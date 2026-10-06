#!/usr/bin/env python
"""Build <campaign>/manifest.csv (campaign root derived from this file's location).

Joins three sources so every experiment has a complete record even while it is
still running:
  * configs/queue_*.txt      -> what was planned (command, threads, budget, gpu)
  * metrics/summary.csv      -> what actually happened (steps, FPS, rewards, ckpt)
  * logs/*.log + status/     -> start/end wall-clock, checkpoint locations, liveness

BOTH queue-status ledger naming schemes are understood:
  wave 1 (run_queue.sh):       status/queue_gpu<N>.status
  wave 2 (run_queue_lane.sh):  status/queue_<queuefile-stem>.status
                               e.g. configs/queue_1v1a.txt ->
                                    status/queue_queue_1v1a.status
The '>>> name start ... gpu=N' lines give each experiment's GPU; the
'queue started gpu=N' line gives a lane's GPU so jobs defined but not yet
started in that lane can still be placed on it. Ledgers are authoritative for
liveness: a job that has started but not yet logged its first rollout episode
has no 'updates' line in its log at all (and often no summary row yet), so
log-parsing alone would misreport it as 'queued'.

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/make_manifest.py -> <campaign>) so the same script works
for any campaign without edits. Overrides, for cross-campaign comparisons
(pair --campaign-root on the foreign campaign with --out-dir back home so the
foreign campaign stays read-only):

  --campaign-root / $CAMPAIGN_ROOT   campaign dir (configs/, metrics/, logs/, status/)
  --out-dir       / $OUT_DIR         where manifest.csv is written
                                     (default: <campaign-root>)
"""
import argparse
import csv
import glob
import os
import re
from pathlib import Path

DEFAULT_CAMPAIGN = Path(__file__).resolve().parents[1]

# Legacy 2026-10-04 queue filenames whose GPU is not encoded in the name.
LEGACY_GPU_QUEUES = {"queue_extra.txt": "0", "queue_seeds.txt": "1"}

COLUMNS = ["experiment_id", "description", "git_commit", "scenario", "algorithm",
           "command", "seed", "gpu_id", "n_rollout_threads", "start_time",
           "end_time", "wall_time", "num_env_steps_planned", "num_env_steps_done",
           "FPS", "final_train_reward", "final_eval_reward", "VRAM_MB", "RAM_GB",
           "CPU_cores", "checkpoint_path", "log_path", "status", "notes"]


def resolve_paths(argv=None):
    """Resolve (campaign_dir, manifest_path) from CLI/env/defaults."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign-root", default=os.environ.get("CAMPAIGN_ROOT"),
                    help="campaign directory; default: derived from this script's "
                         f"location ({DEFAULT_CAMPAIGN})")
    ap.add_argument("--out-dir", default=os.environ.get("OUT_DIR"),
                    help="directory manifest.csv is written into; default: "
                         "<campaign-root>")
    args = ap.parse_args(argv)

    campaign = (Path(args.campaign_root).expanduser().resolve()
                if args.campaign_root else DEFAULT_CAMPAIGN)
    out_dir = (Path(args.out_dir).expanduser().resolve()
               if args.out_dir else campaign)
    return campaign, out_dir / "manifest.csv"


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def status_ledgers(campaign):
    """All queue status ledgers, both naming schemes, deduped and sorted."""
    status_dir = Path(campaign) / "status"
    files = set()
    for pat in ("queue_gpu*.status",              # wave 1: run_queue.sh
                "queue_queue_*.status"):          # wave 2: run_queue_lane.sh
        files.update(glob.glob(str(status_dir / pat)))
    return sorted(files)


def queue_gpu_hint(queue_file):
    """GPU id encoded in a wave-1 queue filename (queue_gpu0.txt, queue_gpu1b.txt)."""
    m = re.match(r"queue_gpu(\d+)[a-z]*\.txt$", os.path.basename(queue_file))
    return m.group(1) if m else None


def queue_lifecycle(campaign):
    """Read both ledger schemes.

    Returns (lifecycle, gpu_by_exp, gpu_by_file):
      lifecycle   : experiment -> 'running' | 'finished' | 'exited rc=N'
      gpu_by_exp  : experiment -> gpu, from its '>>> <name> start ... gpu=N' line
      gpu_by_file : queue-file stem -> gpu, from the lane's 'queue started
                    gpu=N' line (wave-2 ledgers only; wave-1 GPU comes from the
                    config filename)
    """
    state, gpu_by_exp, gpu_by_file = {}, {}, {}
    for f in status_ledgers(campaign):
        base = os.path.basename(f)[:-len(".status")]
        stem = base[len("queue_"):] if base.startswith("queue_") else base
        file_gpu = None
        for line in open(f, encoding="utf-8", errors="replace"):
            m = re.match(r">>> (\S+) start\b", line)
            if m:
                state[m.group(1)] = "running"
                g = re.search(r"\bgpu=(\d+)", line)
                if g:
                    gpu_by_exp[m.group(1)] = g.group(1)
                continue
            # line format: `<<< <name> end <ISO timestamp> rc=<n>`
            m = re.match(r"<<< (\S+) end\b.*?\brc=(-?\d+)", line)
            if m:
                state[m.group(1)] = ("finished" if m.group(2) == "0"
                                     else f"exited rc={m.group(2)}")
                continue
            m = re.match(r"queue started gpu=(\d+)", line)
            if m:
                file_gpu = m.group(1)
        if file_gpu and not re.fullmatch(r"gpu\d+[a-z]*", stem):
            # wave-2 ledger `queue_<queuefile-stem>` -> configs/<stem>.txt
            gpu_by_file.setdefault(stem, file_gpu)
    return state, gpu_by_exp, gpu_by_file


def planned_jobs(campaign, gpu_by_exp, gpu_by_file):
    """One dict per queued job, from every configs/queue_*.txt (both waves)."""
    jobs = []
    for qf in sorted(glob.glob(str(Path(campaign) / "configs" / "queue_*.txt"))):
        base = os.path.basename(qf)
        hint = queue_gpu_hint(qf) or LEGACY_GPU_QUEUES.get(base, "")
        stem = base[:-len(".txt")]
        for line in open(qf, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 8:
                continue
            name, threads, steps, tlimit, env, scen, algo, seed = parts[:8]
            extra = "|".join(parts[8:]).strip()
            # wave-1: gpu from the config filename; wave-2: from the lane's
            # ledger (per-experiment start line, else the lane's gpu).
            gpu = (hint or gpu_by_exp.get(name, "") or gpu_by_file.get(stem, ""))
            cmd = (f"bash scripts/run_train.sh {gpu} {env} '{scen}' {algo} {name} "
                   f"{seed} {threads} {steps} {extra}").strip()
            jobs.append({
                "experiment_id": name, "gpu_id": gpu, "n_rollout_threads": threads,
                "num_env_steps_planned": steps, "scenario": f"{env}/{scen}",
                "algorithm": algo, "seed": seed, "command": cmd,
                "time_limit_s": tlimit, "source_queue": base,
            })
    return jobs


def cgroup_cpu_quota():
    """CPUs granted by the cgroup CPU bandwidth limit (CFS quota), or None."""
    try:  # cgroup v2
        quota, period = open("/sys/fs/cgroup/cpu.max").read().split()
        if quota != "max":
            return float(quota) / float(period)
    except (OSError, ValueError):
        pass
    try:  # cgroup v1
        quota = float(open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read())
        period = float(open("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read())
        if quota > 0:
            return quota / period
    except (OSError, ValueError):
        pass
    return None


def cpu_busy_scale(fieldnames):
    """Multiplier turning system_samples.csv `cpu_busy_pct` into busy cores.

    The two samplers define cpu_busy_pct differently, and the schemas tell them
    apart:
      * 2026-10-04 monitor.sh (no train_cpu_pct column): percent of the host's
        logical CPUs -> pct/100 * os.cpu_count()  (on the 192-thread pilot host
        this is the 1.92 constant the pilot copy hardcodes);
      * formal6m os_watchdog.sh (schema superset incl. train_cpu_pct): percent
        already normalised to the cgroup CPU quota -> pct/100 * quota.
    """
    names = set(fieldnames or ())
    if "train_cpu_pct" in names:
        cpus = cgroup_cpu_quota()
        if cpus is None:
            cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
        if cpus is None:
            cpus = os.cpu_count() or 48.0
    else:
        cpus = os.cpu_count() or 192.0
    return float(cpus) / 100.0


def resource_peaks(campaign):
    """Peak VRAM / RAM / cores observed while the monitor was sampling."""
    path = str(Path(campaign) / "system" / "system_samples.csv")
    rows = read_csv(path)
    if not rows:
        return None
    scale = cpu_busy_scale(rows[0].keys())
    gpu_cols = [c for c in rows[0] if re.match(r"gpu\d_mem_mb", c)]
    vram = 0
    for c in gpu_cols:
        for r in rows:
            try:
                vram = max(vram, float(r[c] or 0))
            except ValueError:
                pass
    cpu = 0.0
    ram = 0.0
    for r in rows:
        try:
            cpu = max(cpu, float(r["cpu_busy_pct"]) * scale)
            ram = max(ram, float(r["mem_used_gb"]))
        except (ValueError, KeyError):
            pass
    return {"vram_mb": round(vram), "ram_gb": round(ram, 1), "cpu_cores": round(cpu, 1)}


def main(argv=None):
    campaign, manifest_path = resolve_paths(argv)

    summary = {r["experiment"]: r for r in read_csv(str(campaign / "metrics" / "summary.csv"))}
    res = resource_peaks(campaign) or {}
    live, gpu_by_exp, gpu_by_file = queue_lifecycle(campaign)
    planned = planned_jobs(campaign, gpu_by_exp, gpu_by_file)

    # One row per experiment: a name can appear in several queue files (the
    # wave-2 1v1 lanes overlap). Keep the definition that knows its GPU (the
    # lane that has actually launched) and note the other sources.
    jobs, dup_sources = [], {}
    by_exp = {}
    for j in planned:
        e = j["experiment_id"]
        prev = by_exp.get(e)
        if prev is None:
            by_exp[e] = j
            continue
        keep, drop = prev, j
        if not str(prev.get("gpu_id", "")).strip() and str(j.get("gpu_id", "")).strip():
            keep, drop = j, prev
        seen = dup_sources.setdefault(e, [keep["source_queue"]])
        if drop["source_queue"] not in seen:
            seen.append(drop["source_queue"])
        by_exp[e] = keep
    jobs = list(by_exp.values())

    # experiments present on disk but never in a queue (smoke tests)
    for e in summary:
        if not any(j["experiment_id"] == e for j in jobs):
            jobs.append({"experiment_id": e, "gpu_id": "", "n_rollout_threads": "",
                         "num_env_steps_planned": "", "scenario": summary[e].get("scenario", ""),
                         "algorithm": summary[e].get("algo", ""), "seed": summary[e].get("seed", ""),
                         "command": "(ad-hoc smoke / plumbing test)", "time_limit_s": "",
                         "source_queue": "-"})

    out = []
    for j in jobs:
        e = j["experiment_id"]
        s = summary.get(e)
        ledger = live.get(e)

        if s and s.get("crashed") == "True":
            status = "CRASHED"
        elif ledger == "running":
            # live right now: the ledger is authoritative even between the
            # first '>>>' and the first logged episode
            status = "running" if s else "running (first episode in progress)"
        elif s and s.get("steps_target"):
            try:
                done, target = int(s["steps_done"]), int(s["steps_target"])
                status = "completed" if done >= target else "running (truncated by time cap)"
            except (TypeError, ValueError):
                status = "running"
        elif s:
            status = "running"
        elif ledger:
            status = ledger
        else:
            status = "queued (not started)"

        notes = []
        if j.get("time_limit_s"):
            notes.append(f"time cap {j['time_limit_s']}s")
        if s and s.get("train_reward_tail_slope") not in (None, "", "None"):
            notes.append(f"tail slope {s['train_reward_tail_slope']}")
        if s and s.get("steps_target"):
            try:
                if int(s["steps_target"]) >= 100_000_000:
                    notes.append("official 1e8 budget; truncated by the wall-clock cap "
                                 "-- planned vs done recorded, budget NOT silently reduced")
            except (TypeError, ValueError):
                pass
        if dup_sources.get(e):
            notes.append("also queued in " + ", ".join(sorted(dup_sources[e])))
        if s and s.get("checkpoint_path"):
            notes.append("KEEP")

        out.append({
            "experiment_id": e,
            "description": f"{j['scenario']} / {j['algorithm']}",
            "git_commit": (s or {}).get("git_commit", ""),
            "scenario": j["scenario"],
            "algorithm": j["algorithm"],
            "command": j["command"],
            "seed": j["seed"],
            "gpu_id": j["gpu_id"],
            "n_rollout_threads": j["n_rollout_threads"],
            "start_time": (s or {}).get("start", ""),
            "end_time": (s or {}).get("last_log_time", ""),
            "wall_time": (s or {}).get("wall_time", ""),
            "num_env_steps_planned": j["num_env_steps_planned"],
            "num_env_steps_done": (s or {}).get("steps_done", ""),
            "FPS": (s or {}).get("fps_last", ""),
            "final_train_reward": (s or {}).get("train_reward_last", ""),
            "final_eval_reward": (s or {}).get("eval_reward_last", ""),
            "VRAM_MB": res.get("vram_mb", ""),
            "RAM_GB": res.get("ram_gb", ""),
            "CPU_cores": res.get("cpu_cores", ""),
            "checkpoint_path": (s or {}).get("checkpoint_path", ""),
            "log_path": (s or {}).get("log_path", ""),
            "status": status,
            "notes": "; ".join(notes),
        })

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"campaign root : {campaign}")
    print(f"wrote {manifest_path}  ({len(out)} rows)")
    print(f"resources     : {res}")
    for r in out:
        print(f"  {r['experiment_id']:38s} {r['status']:22s} gpu={str(r['gpu_id']):>2s} "
              f"steps {str(r['num_env_steps_done']):>9s}/{str(r['num_env_steps_planned']):>10s} "
              f"fps={str(r['FPS']):>7s}")


if __name__ == "__main__":
    main()
