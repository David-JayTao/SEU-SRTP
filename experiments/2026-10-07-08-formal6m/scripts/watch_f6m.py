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
    "f6m_10v10_noweapon_s0": ("10v10", 20),
    "f6m_5v5_noweapon_s0": ("5v5", 8),
    "f6m_3v3_noweapon_s0": ("3v3", 8),
    "f6m_2v2_noweapon_s0": ("2v2", 4),
    "f6m_official_2v2_noweapon_s0": ("official_2v2", 4),
}

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


def system_stats() -> dict:
    load = os.getloadavg()
    vm = sh("vmstat 1 2 | tail -1").split()
    cpu_busy = None
    if len(vm) >= 15:
        try:
            cpu_busy = 100 - int(vm[14])  # id column
        except ValueError:
            pass
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
    return {"load1": round(load[0], 2), "cpu_busy_pct": cpu_busy, "gpu": gpu, "mem": mem}


def tmux_sessions() -> list[str]:
    out = sh("tmux ls")
    return [l.split(":")[0] for l in out.strip().splitlines() if ":" in l]


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
            "stalled": (age_min is not None and age_min > args.stall_min),
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
        if r["stalled"]:
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
    lines.append(f"- load1 **{s['load1']}**  cpu_busy **{s['cpu_busy_pct']}%**  "
                 f"train procs **{p['n_procs']}** using **{p['cpu_pct']}%** CPU, "
                 f"**{p['rss_gb']} GB** RSS")
    lines.append(f"- RAM used {s['mem'].get('used_gb')} GB / {s['mem'].get('total_gb')} GB "
                 f"(avail {s['mem'].get('avail_gb')} GB)")
    for g in s["gpu"]:
        lines.append(f"- GPU{g['index']}: util {g['util']}%, VRAM {g['mem_mib']} MiB")
    lines.append(f"- tmux: {', '.join(state['tmux']) or 'none'}")

    txt = "\n".join(lines)
    (CAMP / "status" / "monitor_latest.md").write_text(txt + "\n")
    print(txt)

    # Append one row per sweep to a CSV history -- this is the throughput-vs-time
    # record used later for the equal-wall-clock analysis.
    hist = CAMP / "metrics" / "throughput_history.csv"
    new = not hist.exists()
    with hist.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp_local", "aggregate_fps", "load1", "cpu_busy_pct",
                        "train_cpu_pct", "rss_gb"]
                       + [f"{r['exp']}_fps" for r in rows]
                       + [f"{r['exp']}_steps" for r in rows])
        w.writerow([state["timestamp_local"], agg_fps, s["load1"], s["cpu_busy_pct"],
                    p["cpu_pct"], p["rss_gb"]]
                   + [(r["fps"] or "") for r in rows]
                   + [r["steps"] for r in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
