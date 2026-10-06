#!/usr/bin/env python
"""Build experiments/2026-10-04-night/manifest.csv.

Joins three sources so every experiment has a complete record even while it is
still running:
  * configs/queue_*.txt      -> what was planned (command, threads, budget, gpu)
  * metrics/summary.csv      -> what actually happened (steps, FPS, rewards, ckpt)
  * logs/*.log               -> start/end wall-clock and checkpoint locations
"""
import csv
import glob
import os
import re

REPO = "/root/autodl-tmp/SEU-SRTP"
EXP = os.path.join(REPO, "experiments/2026-10-04-night")
OUT = os.path.join(EXP, "manifest.csv")

GPUS = {"queue_gpu0.txt": 0, "queue_extra.txt": 0, "queue_gpu1.txt": 1,
        "queue_seeds.txt": 1, "queue_gpu2.txt": 2}

COLUMNS = ["experiment_id", "description", "git_commit", "scenario", "algorithm",
           "command", "seed", "gpu_id", "n_rollout_threads", "start_time",
           "end_time", "wall_time", "num_env_steps_planned", "num_env_steps_done",
           "FPS", "final_train_reward", "final_eval_reward", "VRAM_MB", "RAM_GB",
           "CPU_cores", "checkpoint_path", "log_path", "status", "notes"]

FIELDS = ["run_dir", "wall_time", "wall_time_hours", "steps_done", "steps_target",
          "fps_last", "train_reward_first", "train_reward_last",
          "train_reward_tail_slope", "eval_reward_last", "episodes_logged",
          "episodes_target", "value_loss_last", "critic_grad_norm_last",
          "entropy_loss_last", "ratio_last", "crashed", "checkpoint_path",
          "log_path", "seed", "gpu", "n_rollout_threads", "algo", "scenario",
          "env", "git_commit"]


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def planned_jobs():
    jobs = []
    for qf, gpu in GPUS.items():
        path = os.path.join(EXP, "configs", qf)
        if not os.path.exists(path):
            continue
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 8:
                continue
            name, threads, steps, tlimit, env, scen, algo, seed = parts[:8]
            extra = "|".join(parts[8:]).strip()
            cmd = (f"bash scripts/run_train.sh {gpu} {env} '{scen}' {algo} {name} "
                   f"{seed} {threads} {steps} {extra}").strip()
            jobs.append({
                "experiment_id": name, "gpu_id": gpu, "n_rollout_threads": threads,
                "num_env_steps_planned": steps, "scenario": f"{env}/{scen}",
                "algorithm": algo, "seed": seed, "command": cmd,
                "time_limit_s": tlimit, "source_queue": qf,
            })
    return jobs


def resource_peaks():
    """Peak VRAM / RAM / cores observed while the monitor was sampling."""
    path = os.path.join(EXP, "system/system_samples.csv")
    rows = read_csv(path)
    if not rows:
        return None
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
            cpu = max(cpu, float(r["cpu_busy_pct"]) * 1.92)
            ram = max(ram, float(r["mem_used_gb"]))
        except (ValueError, KeyError):
            pass
    return {"vram_mb": round(vram), "ram_gb": round(ram, 1), "cpu_cores": round(cpu, 1)}


def queue_lifecycle():
    """experiment -> 'running' | 'finished' from the queue status ledgers.

    A job that has started but not yet finished its first rollout episode has no
    'updates' line in its log at all, so log-parsing alone would misreport it as
    'queued'. The queue ledger is the authoritative liveness signal.
    """
    state = {}
    for f in glob.glob(os.path.join(EXP, "status/queue_*.status")):
        for line in open(f):
            m = re.match(r">>> (\S+) start", line)
            if m:
                state[m.group(1)] = "running"
                continue
            m = re.match(r"<<< (\S+) end rc=(\d+)", line)
            if m:
                state[m.group(1)] = "finished" if m.group(2) == "0" else f"exited rc={m.group(2)}"
    return state


def main():
    summary = {r["experiment"]: r for r in read_csv(os.path.join(EXP, "metrics/summary.csv"))}
    jobs = planned_jobs()
    res = resource_peaks() or {}
    live = queue_lifecycle()

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
        if s and s.get("steps_target"):
            try:
                done, target = int(s["steps_done"]), int(s["steps_target"])
                status = "completed" if done >= target else "running (truncated by time cap)"
            except (TypeError, ValueError):
                status = "running"
        elif s:
            status = "running"
        else:
            status = live.get(e, "queued (not started)")
            if status == "running":
                status = "running (first episode in progress)"
        if s and s.get("crashed") == "True":
            status = "CRASHED"

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

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT}  ({len(out)} rows)")
    for r in out:
        print(f"  {r['experiment_id']:38s} {r['status']:22s} "
              f"steps {str(r['num_env_steps_done']):>9s}/{str(r['num_env_steps_planned']):>10s} "
              f"fps={str(r['FPS']):>7s}")


if __name__ == "__main__":
    main()
