#!/usr/bin/env python
"""Watchdog + aggregate-throughput monitor for the formal-6M campaign.

Design notes
------------
The scarce resource on this box is CPU, not GPU: measured GPU utilisation is
0-6% while 44 rollout workers saturate the 48 cores. So the quantity worth
watching is *aggregate useful environment steps per second*, not per-GPU
utilisation. This script therefore reports, every sweep:

  * per-job: current env steps, instantaneous FPS (from the run's own FPS
    line), steps/iteration, ETA to the 6M target, and the most recent
    value_loss / critic_grad_norm / entropy proxy
  * campaign-level: sum of FPS across jobs == aggregate env-steps/s
  * system-level: load average, CPU busy, per-core occupancy, RAM, per-GPU
    utilisation and VRAM
  * health: NaN/Inf detection, stall detection (no new episode within a
    threshold), and Traceback detection in the stdout log

It writes machine-readable state to metrics/status.json and a human-readable
snapshot to status/monitor_latest.md so a later reader can reconstruct exactly
what was running and how fast.

Usage: python watch_f6m.py [--stall-min 30] [--json]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/root/autodl-tmp/SEU-SRTP")
CAMP = REPO / "experiments" / "2026-10-07-08-formal6m"
RESULTS = REPO / "scripts" / "results"

TARGET_STEPS = 6_000_000

# Experiment name -> (scale label, n_rollout_threads). Kept explicit rather than
# inferred, so the monitor keeps working even if a process is mid-restart.
JOBS = {
    # Experiment line B -- N-v-N NoWeapon scaling, generated configs (L3).
    "f6m_10v10_noweapon_s0": ("10v10", 20),
    "f6m_5v5_noweapon_s0": ("5v5", 8),
    "f6m_3v3_noweapon_s0": ("3v3", 8),
    "f6m_2v2_noweapon_s0": ("2v2", 4),
    # Experiment line A -- official baselines. L1 unless noted.
    "f6m_official_2v2_noweapon_s0": ("official_2v2", 4),          # L1 official .sh entry
    "f6m_official_1v1_selfplay_s1": ("o_1v1_selfplay", 3),        # L1
    "f6m_official_1v1_vsbaseline_s1": ("o_1v1_vsbaseline", 3),    # L1
    "f6m_official_1v1_shoot_hier_selfplay_s1": ("o_1v1_shoot", 3),  # L1, --use-prior
    "f6m_official_1v1_hier_selfplay_s1": ("o_1v1_hier", 3),       # L2 official YAML, no .sh
    # Wave 4 -- second seeds (only --seed differs from the seed-0 lane).
    "f6m_5v5_noweapon_s1": ("5v5 s1", 10),
    "f6m_3v3_noweapon_s1": ("3v3 s1", 8),
}

# Every experiment name the campaign may launch, including queued ones. Used to
# detect an accidental DUPLICATE run (two training processes writing the same
# experiment name into sibling run1/run2 dirs).
ALL_EXPERIMENTS = list(JOBS) + [
    "f6m_2v2_noweapon_s1",
    "f6m_5v5_noweapon_s0",
    "f6m_10v10_noweapon_s1",
]

FPS_RE = re.compile(r"updates (\d+)/(\d+) episodes, total num timesteps (\d+)/(\d+), FPS (\d+)")
EVAL_RE = re.compile(r"eval average episode rewards: (-?[\d.eE+-]+)")


def sh(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout
    except Exception as exc:  # noqa: BLE001
        return f"<error: {exc}>"


def find_run_dir(exp: str) -> Path | None:
    """Locate the run dir for an experiment name (the runner nests by env/scenario/algo)."""
    hits = list(RESULTS.glob(f"**/{exp}/run1"))
    return hits[0] if hits else None


def find_duplicate_runs() -> list[str]:
    """Detect two run dirs for one experiment name.

    train_jsbsim.py always allocates the next free run<N>, so if the same
    experiment name is ever launched twice it silently creates run2/ beside
    run1/ and the two trajectories must not be spliced together. Flag it loudly.
    """
    dups = []
    for exp in ALL_EXPERIMENTS:
        dirs = sorted(RESULTS.glob(f"**/{exp}"))
        for d in dirs:
            runs = sorted(p.name for p in d.glob("run*") if p.is_dir())
            if len(runs) > 1:
                dups.append(f"{exp}: {runs} under {d}")
    return dups


def read_metrics(run_dir: Path | None) -> dict:
    out = {
        "steps": 0, "fps": None, "updates": None, "total_updates": None,
        "reward": None, "eval_reward": None, "value_loss": None,
        "critic_grad_norm": None, "actor_grad_norm": None,
        "policy_entropy_loss": None, "n_lines": 0, "last_mtime": None,
        "nan": False, "inf": False,
    }
    if run_dir is None:
        return out
    mj = run_dir / "metrics.jsonl"
    if not mj.exists():
        return out
    out["last_mtime"] = mj.stat().st_mtime
    with mj.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            out["n_lines"] += 1
            if "total_num_steps" in rec:
                out["steps"] = rec["total_num_steps"]
            if "average_episode_rewards" in rec:
                out["reward"] = rec["average_episode_rewards"]
            if "eval_average_episode_rewards" in rec:
                out["eval_reward"] = rec["eval_average_episode_rewards"]
            for k in ("value_loss", "critic_grad_norm", "actor_grad_norm", "policy_entropy_loss"):
                if k in rec:
                    out[k] = rec[k]
                    v = rec[k]
                    if isinstance(v, (int, float)):
                        if v != v:
                            out["nan"] = True
                        elif v in (float("inf"), float("-inf")):
                            out["inf"] = True
    return out


def read_log(exp: str, run_dir: Path | None) -> dict:
    """Parse the stdout log for the latest FPS line and any traceback."""
    out = {"fps": None, "updates": None, "total_updates": None, "traceback": False,
           "log_path": None, "last_fps_mtime": None}
    # logs are named <exp>_seed<k>_gpu<g>_<stamp>.log; take the newest
    cands = sorted(CAMP.glob(f"logs/{exp}_seed*.log"), key=lambda p: p.stat().st_mtime)
    if not cands:
        return out
    log = cands[-1]
    out["log_path"] = str(log)
    txt = log.read_text(errors="replace")
    out["traceback"] = ("Traceback (most recent call last)" in txt)
    for m in FPS_RE.finditer(txt):
        out["updates"] = int(m.group(1))
        out["total_updates"] = int(m.group(2))
        out["fps"] = int(m.group(5))
        out["last_fps_mtime"] = log.stat().st_mtime
    return out


def proc_stats() -> dict:
    """Sum of RSS and CPU% over all training processes (matches setproctitle names)."""
    out = subprocess.run(
        "ps -eo rss,pcpu,args --no-headers", shell=True, capture_output=True, text=True
    ).stdout
    total_rss = 0
    total_cpu = 0.0
    n = 0
    for line in out.splitlines():
        if "-MultipleCombat-" not in line and "train_jsbsim.py" not in line:
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            total_rss += int(parts[0])
            total_cpu += float(parts[1])
        except ValueError:
            continue
        n += 1
    return {"n_procs": n, "rss_gb": round(total_rss / 1024 / 1024, 2), "cpu_pct": round(total_cpu, 1)}


def quota_cpu() -> dict:
    """CPU actually consumed by this container, from its own cgroup accounting.

    Do NOT use /proc/stat or vmstat here (incident F16): in this container
    /proc/stat reports the HOST's 192 logical CPUs and returns deltas that
    alternate between 0 and ~200 cores between consecutive 5-second samples while
    the container is demonstrably busy, so any "N of 48 cores" figure derived
    from it is meaningless. `cpu.stat usage_usec` is the container's own
    accounting and is stable; `cpu.max` is the quota.
    """
    out = {"cores": None, "quota": None, "pct_of_quota": None, "throttled_pct": None}
    try:
        quota_raw = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        quota = float(quota_raw[0]) / float(quota_raw[1])
        a = None
        for line in Path("/sys/fs/cgroup/cpu.stat").read_text().splitlines():
            if line.startswith("usage_usec"):
                a = float(line.split()[1])
        time.sleep(2)
        b = None
        for line in Path("/sys/fs/cgroup/cpu.stat").read_text().splitlines():
            if line.startswith("usage_usec"):
                b = float(line.split()[1])
        if a is not None and b is not None:
            cores = (b - a) / 1e6 / 2.0
            out.update(cores=round(cores, 2), quota=quota,
                       pct_of_quota=round(100 * cores / quota, 1))
        periods = throttled = None
        for line in Path("/sys/fs/cgroup/cpu.stat").read_text().splitlines():
            if line.startswith("nr_periods"):
                periods = float(line.split()[1])
            elif line.startswith("nr_throttled"):
                throttled = float(line.split()[1])
        if periods:
            out["throttled_pct"] = round(100 * throttled / periods, 4)
    except Exception:  # noqa: BLE001
        pass
    return out


def system_stats() -> dict:
    load = os.getloadavg()
    cpu_busy = quota_cpu()
    gpu = []
    q = sh("nvidia-smi --query-gpu=index,utilization.gpu,memory.used "
           "--format=csv,noheader,nounits")
    for line in q.strip().splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) == 3:
            gpu.append({"index": int(p[0]), "util": int(p[1]), "mem_mib": int(p[2])})
    mem = {}
    for line in sh("free -m").splitlines():
        if line.startswith("Mem:"):
            f = line.split()
            mem = {"total_gb": round(int(f[1]) / 1024, 1),
                   "used_gb": round(int(f[2]) / 1024, 1),
                   "avail_gb": round(int(f[6]) / 1024, 1)}
    return {"load1": round(load[0], 2), "cpu_busy": cpu_busy, "gpu": gpu, "mem": mem}


def tmux_sessions() -> list[str]:
    out = sh("tmux ls")
    return [l.split(":")[0] for l in out.strip().splitlines() if ":" in l]


def sync_history_schema(hist: Path, header: list) -> None:
    """Make sure `hist`'s stored header is exactly `header`.

    The per-job column set follows JOBS, which grew from 5 to 9 experiments
    mid-campaign. The original implementation wrote the header only when the
    file did not exist, so the extra columns stayed unnamed and every named
    *_steps column silently held a shifted FPS value (repaired 2026-10-07).
    Re-sync whenever the header no longer matches: legacy-width rows
    are migrated by column NAME; rows already as wide as the new header are
    kept verbatim (their leading fields must not be re-interpreted through
    the stale old header). Normal sweeps -- header matches -- stay a plain
    append and never rewrite the file.
    """
    if not hist.exists():
        hist.parent.mkdir(parents=True, exist_ok=True)
        with hist.open("w", newline="") as fh:
            csv.writer(fh).writerow(header)
        return
    with hist.open(newline="") as fh:
        table = list(csv.reader(fh))
    if not table:
        with hist.open("w", newline="") as fh:
            csv.writer(fh).writerow(header)
        return
    old_header, body = table[0], table[1:]
    if old_header == header:
        return
    fixed = []
    for row in body:
        if len(row) == len(old_header):
            by_name = dict(zip(old_header, row))
            fixed.append([by_name.get(c, "") for c in header])
        elif len(row) == len(header):
            fixed.append(row)
        else:  # last resort: pad short rows / truncate over-long ones
            fixed.append((row + [""] * len(header))[: len(header)])
    with hist.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(fixed)
    print(f"throughput_history.csv: header updated to {len(header)} fields, "
          f"{len(fixed)} rows migrated")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stall-min", type=float, default=30.0,
                    help="flag a job with no new episode in this many minutes")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    now = time.time()
    rows = []
    for exp, (scale, threads) in JOBS.items():
        run_dir = find_run_dir(exp)
        m = read_metrics(run_dir)
        lg = read_log(exp, run_dir)
        # prefer the log's own FPS (it is the runner's own accounting)
        fps = lg["fps"] if lg["fps"] is not None else m["fps"]
        steps = m["steps"]
        age_min = None
        if m["last_mtime"]:
            age_min = round((now - m["last_mtime"]) / 60.0, 1)
        eta_h = None
        if fps and fps > 0 and steps < TARGET_STEPS:
            eta_h = round((TARGET_STEPS - steps) / fps / 3600.0, 2)
        rows.append({
            "exp": exp, "scale": scale, "threads": threads,
            "steps": steps, "target": TARGET_STEPS,
            "pct": round(100 * steps / TARGET_STEPS, 1),
            "fps": fps, "eta_h": eta_h,
            "updates": lg["updates"], "total_updates": lg["total_updates"],
            "reward": m["reward"], "eval_reward": m["eval_reward"],
            "value_loss": m["value_loss"], "critic_grad_norm": m["critic_grad_norm"],
            "actor_grad_norm": m["actor_grad_norm"],
            "nan": m["nan"], "inf": m["inf"], "traceback": lg["traceback"],
            # The reachable budget is quantised by thread count (incident F17):
            # the runner floors num_env_steps // 3000 // threads, so a 3-thread
            # lane caps at 5,994,000 and can never equal TARGET_STEPS. Compare
            # against its own achievable maximum, or a lane that finished
            # perfectly is misreported as stalled forever.
            "achievable": (TARGET_STEPS // 3000 // threads) * 3000 * threads,
            "done": steps >= (TARGET_STEPS // 3000 // threads) * 3000 * threads,
            "stalled": (age_min is not None and age_min > args.stall_min
                        and steps < (TARGET_STEPS // 3000 // threads) * 3000 * threads),
            "age_min": age_min,
            "run_dir": str(run_dir) if run_dir else None,
            "log": lg["log_path"],
        })

    agg_fps = sum(r["fps"] or 0 for r in rows)
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "aggregate_fps": agg_fps,
        "jobs": rows,
        "duplicate_runs": find_duplicate_runs(),
        "system": system_stats(),
        "procs": proc_stats(),
        "tmux": tmux_sessions(),
    }

    (CAMP / "metrics").mkdir(parents=True, exist_ok=True)
    (CAMP / "status").mkdir(parents=True, exist_ok=True)
    (CAMP / "metrics" / "status.json").write_text(json.dumps(state, indent=2, default=str))

    if args.json:
        print(json.dumps(state, indent=2, default=str))
        return 0

    lines = []
    lines.append(f"# Formal-6M monitor  {state['timestamp_local']}")
    lines.append("")
    lines.append(f"**Aggregate throughput: {agg_fps} env-steps/s** across {len(rows)} jobs"
                 f" ({sum(r['threads'] for r in rows)} rollout threads)")
    lines.append("")
    lines.append("| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        flags = []
        if r["nan"]:
            flags.append("**NaN**")
        if r["inf"]:
            flags.append("**Inf**")
        if r["traceback"]:
            flags.append("**Traceback**")
        if r["done"]:
            flags.append("**complete**" if r["steps"] == r["target"]
                         else f"**complete {r['steps']:,} of {r['target']:,}**")
        elif r["stalled"]:
            flags.append(f"**STALL {r['age_min']}m**")
        if not flags:
            flags.append("ok")
        def fmt(v, n=3):
            return "—" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))
        lines.append(
            f"| {r['exp']} | {r['scale']} | {r['threads']} | {r['steps']:,} | {r['pct']}% | "
            f"{r['fps'] or '—'} | {r['eta_h'] if r['eta_h'] is not None else '—'} | "
            f"{fmt(r['reward'])} | {fmt(r['eval_reward'])} | {fmt(r['value_loss'])} | "
            f"{fmt(r['critic_grad_norm'],2)} | {' '.join(flags)} |"
        )
    s = state["system"]
    p = state["procs"]
    lines.append("")
    cb = s["cpu_busy"]
    lines.append(f"- load1 **{s['load1']}**  container CPU **{cb.get('cores')} / {cb.get('quota')} cores** "
                 f"({cb.get('pct_of_quota')}% of quota, throttled {cb.get('throttled_pct')}% of periods)  "
                 f"train procs **{p['n_procs']}**, **{p['rss_gb']} GB** RSS")
    lines.append(f"- RAM used {s['mem'].get('used_gb')} GB / {s['mem'].get('total_gb')} GB "
                 f"(avail {s['mem'].get('avail_gb')} GB)")
    for g in s["gpu"]:
        lines.append(f"- GPU{g['index']}: util {g['util']}%, VRAM {g['mem_mib']} MiB")
    lines.append(f"- tmux: {', '.join(state['tmux']) or 'none'}")
    if state["duplicate_runs"]:
        lines.append("")
        lines.append("**DUPLICATE RUN DIRS DETECTED (do not splice these trajectories):**")
        for d in state["duplicate_runs"]:
            lines.append(f"- {d}")

    txt = "\n".join(lines)
    (CAMP / "status" / "monitor_latest.md").write_text(txt + "\n")
    print(txt)

    # Append one row per sweep to a CSV history -- this is the throughput-vs-time
    # record used later for the equal-wall-clock analysis. The column set
    # follows JOBS, so sync_history_schema() first guarantees the stored header
    # still describes the rows being appended (it silently lagged when the job
    # list grew from 5 to 9 on 2026-10-07 03:19).
    hist = CAMP / "metrics" / "throughput_history.csv"
    header = (["timestamp_local", "aggregate_fps", "load1", "cpu_cores_of_quota", "cpu_pct_of_quota",
               "train_cpu_pct", "rss_gb"]
              + [f"{r['exp']}_fps" for r in rows]
              + [f"{r['exp']}_steps" for r in rows])
    sync_history_schema(hist, header)
    with hist.open("a", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([state["timestamp_local"], agg_fps, s["load1"],
                    (s["cpu_busy"] or {}).get("cores"), (s["cpu_busy"] or {}).get("pct_of_quota"),
                    p["cpu_pct"], p["rss_gb"]]
                   + [(r["fps"] or "") for r in rows]
                   + [r["steps"] for r in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
