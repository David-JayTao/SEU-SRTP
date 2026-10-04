#!/usr/bin/env python
"""Collect every experiment's stdout log + metrics.jsonl into analysis-ready CSVs.

Produces
--------
metrics/summary.csv          one row per experiment (status, steps, FPS, wall
                             time, final train/eval reward, checkpoint path, ...)
metrics/curves/<exp>.csv     per-episode learning curves

Everything is derived from artefacts on disk (the tee'd stdout logs and the
per-run metrics.jsonl), so it can be re-run at any time without touching the
training processes -- important because the runs are still going.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime

REPO = "/root/autodl-tmp/SEU-SRTP"
EXP_DIR = os.path.join(REPO, "experiments/2026-10-04-night")
LOG_DIR = os.path.join(EXP_DIR, "logs")
OUT_DIR = os.path.join(EXP_DIR, "metrics")
RESULTS_DIR = os.path.join(REPO, "scripts/results")

EP_RE = re.compile(
    r"Scenario (?P<scenario>\S+) Algo (?P<algo>\S+) Exp (?P<exp>\S+) "
    r"updates (?P<ep>\d+)/(?P<episodes>\d+) episodes, "
    r"total num timesteps (?P<steps>\d+)/(?P<total>\d+), FPS (?P<fps>[\d.]+)\.")
TRAIN_REW_RE = re.compile(r"average episode rewards is (?P<v>-?[\d.eE+]+)")
EVAL_REW_RE = re.compile(r"eval average episode rewards: (?P<v>-?[\d.eE+]+)")
RENDER_REW_RE = re.compile(r"render episode reward of agent: (?P<v>-?[\d.eE+-]+)")
START_RE = re.compile(r"^start\s+:\s+(?P<t>\S+)", re.M)
GIT_RE = re.compile(r"^git commit : (?P<h>\w+)", re.M)
THREADS_RE = re.compile(r"^threads\s+:\s+(?P<n>\d+)", re.M)
SCEN_RE = re.compile(r"^env/scen\s+:\s+(?P<e>\S+) / (?P<s>.+)", re.M)
ALGO_RE = re.compile(r"^algo\s+:\s+(?P<a>\S+)", re.M)
SEED_RE = re.compile(r"^algo\s+:\s+\S+\s+seed=(?P<n>\d+)", re.M)
GPU_RE = re.compile(r"^gpu\s+:\s+(?P<g>\d+)", re.M)


def queue_metadata():
    """experiment -> {env_name, scenario, algo, seed, gpu, n_threads}.

    Fallback for jobs launched before run_train.sh started writing its header
    into the log file: the queue definitions still carry the same information.
    """
    meta = {}
    for qf in glob.glob(os.path.join(EXP_DIR, "configs", "queue_*.txt")):
        gpu_map = {"queue_gpu0.txt": 0, "queue_extra.txt": 0, "queue_gpu1.txt": 1,
                   "queue_seeds.txt": 1, "queue_gpu2.txt": 2}
        gpu = gpu_map.get(os.path.basename(qf), "")
        for line in open(qf):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split("|")
            if len(p) < 8:
                continue
            meta[p[0]] = {"env_name": p[4], "scenario": p[5], "algo": p[6],
                          "seed": p[7], "gpu": gpu, "n_threads": p[1]}
    return meta


def parse_log(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    eps = []
    for m in EP_RE.finditer(txt):
        eps.append({
            "episode": int(m.group("ep")),
            "episodes_total": int(m.group("episodes")),
            "total_num_steps": int(m.group("steps")),
            "num_env_steps_target": int(m.group("total")),
            "fps": float(m.group("fps")),
        })
    # rewards appear after each FPS line; pair them positionally
    rewards = TRAIN_REW_RE.findall(txt)
    evals = [float(x) for x in EVAL_REW_RE.findall(txt)]
    for i, r in enumerate(rewards):
        if i < len(eps):
            eps[i]["average_episode_rewards"] = float(r)

    meta = {}
    for key, rgx in (("start", START_RE), ("git_commit", GIT_RE), ("n_threads", THREADS_RE),
                     ("algo", ALGO_RE), ("seed", SEED_RE), ("gpu", GPU_RE)):
        m = rgx.search(txt)
        meta[key] = m.group(1 if key != "start" else "t") if m else None
    m = SCEN_RE.search(txt)
    meta["env_name"] = m.group("e") if m else None
    meta["scenario"] = m.group("s").strip() if m else None

    # A traceback is NOT a crash here: every queued job is capped with
    # `timeout -s INT`, so a job that ran to its wall-clock limit ends in
    # KeyboardInterrupt by design. Only count tracebacks that are not a clean
    # interrupt, otherwise every time-capped run is misreported as crashed.
    has_tb = bool(re.search(r"Traceback \(most recent call last\)", txt))
    tail = txt[-4000:]
    clean_interrupt = bool(re.search(r"^(KeyboardInterrupt|SystemExit)\s*$", tail, re.M))
    meta["crashed"] = has_tb and not clean_interrupt
    meta["time_capped"] = has_tb and clean_interrupt
    meta["n_fps_lines"] = len(eps)
    meta["eval_rewards"] = evals
    meta["last_eval_reward"] = evals[-1] if evals else None
    return meta, eps


def entropy_batch_rows(n_rollout_threads, buffer_size=3000, num_mini_batch=5,
                       data_chunk_length=8):
    """Rows per PPO minibatch -- the divisor ACTLayer applies to the entropy.

    ACTLayer.evaluate_actions computes `action_dist.entropy() / log_probs.size(0)`
    per action dimension and then sums, so the logged `policy_entropy_loss` is
    (sum of per-dim entropies) / batch_rows. That divisor depends on
    n_rollout_threads and therefore varies with team size, which makes the raw
    column non-comparable across runs. SharedReplayBuffer.recurrent_generator:
        data_chunks     = n_rollout_threads * buffer_size // data_chunk_length
        mini_batch_size = data_chunks // num_mini_batch
        batch_rows      = data_chunk_length * mini_batch_size
    Multiplying the logged value back by batch_rows recovers the true summed
    entropy, which IS comparable across runs and across N.
    """
    try:
        t = int(n_rollout_threads)
    except (TypeError, ValueError):
        return None
    data_chunks = t * buffer_size // data_chunk_length
    mini_batch_size = data_chunks // num_mini_batch
    return data_chunk_length * mini_batch_size


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main():
    os.makedirs(os.path.join(OUT_DIR, "curves"), exist_ok=True)
    summary = []
    qmeta = queue_metadata()

    for logpath in sorted(glob.glob(os.path.join(LOG_DIR, "*.log"))):
        meta, eps = parse_log(logpath)
        exp = os.path.basename(logpath).split("_seed")[0]
        if not eps and not meta.get("crashed"):
            continue

        # fall back to the queue definition when the log has no header
        q = qmeta.get(exp, {})
        for k in ("env_name", "scenario", "algo", "seed", "gpu", "n_threads"):
            if not meta.get(k) and q.get(k) is not None:
                meta[k] = q[k]

        # locate the run dir (metrics.jsonl lives next to the checkpoints)
        run_dir = None
        if meta.get("env_name") and meta.get("scenario") and meta.get("algo"):
            pattern = os.path.join(RESULTS_DIR, meta["env_name"], meta["scenario"],
                                   meta["algo"], exp, "run*", "metrics.jsonl")
            cands = sorted(glob.glob(pattern))
            if cands:
                run_dir = os.path.dirname(cands[-1])
        jrows = load_jsonl(os.path.join(run_dir, "metrics.jsonl")) if run_dir else []

        # Merge metrics.jsonl by total_num_steps. A single step can carry more
        # than one record (the training diagnostics and, when eval is on, the
        # eval infos), so records for the same step must be unioned -- a plain
        # dict assignment would let the eval record shadow value_loss/entropy.
        by_step = {}
        for r in jrows:
            by_step.setdefault(r["total_num_steps"], {}).update(r)

        # undo the batch-size normalisation that ACTLayer applies to entropy
        ent_rows = entropy_batch_rows(meta.get("n_threads"))
        for rec in by_step.values():
            ev = rec.get("policy_entropy_loss")
            if ev is not None and ent_rows:
                rec["policy_entropy_true_sum"] = -float(ev) * ent_rows
        if ent_rows:
            for e in eps:
                if "policy_entropy_loss" in e:
                    e["policy_entropy_true_sum"] = -float(e["policy_entropy_loss"]) * ent_rows
        for e in eps:
            e.update({k: v for k, v in by_step.get(e["total_num_steps"], {}).items()
                      if k != "total_num_steps"})

        mtime = datetime.fromtimestamp(os.path.getmtime(logpath)).isoformat()
        ckpt = os.path.join(run_dir, "actor_latest.pt") if run_dir else None
        ckpt_ok = bool(ckpt and os.path.exists(ckpt))

        last = eps[-1] if eps else {}
        first = eps[0] if eps else {}
        # slope of average_episode_rewards over the last third of the run
        slope = None
        rewards = [e.get("average_episode_rewards") for e in eps
                   if e.get("average_episode_rewards") is not None]
        if len(rewards) >= 4:
            k = max(1, len(rewards) // 3)
            tail = rewards[-k:]
            if len(tail) >= 2:
                slope = (tail[-1] - tail[0]) / max(1, len(tail) - 1)

        summary.append({
            "experiment": exp,
            "env": meta.get("env_name"),
            "scenario": meta.get("scenario"),
            "algo": meta.get("algo"),
            "seed": meta.get("seed"),
            "gpu": meta.get("gpu"),
            "n_rollout_threads": meta.get("n_threads"),
            "git_commit": meta.get("git_commit"),
            "start": meta.get("start"),
            "last_log_time": mtime,
            "episodes_logged": len(eps),
            "episodes_target": last.get("episodes_total"),
            "steps_done": last.get("total_num_steps"),
            "steps_target": last.get("num_env_steps_target"),
            "fps_first": first.get("fps"),
            "fps_last": last.get("fps"),
            "train_reward_first": rewards[0] if rewards else None,
            "train_reward_last": rewards[-1] if rewards else None,
            "train_reward_tail_slope": round(slope, 4) if slope is not None else None,
            "eval_reward_last": meta.get("last_eval_reward"),
            "value_loss_last": last.get("value_loss"),
            "policy_loss_last": last.get("policy_loss"),
            "entropy_loss_last": last.get("policy_entropy_loss"),
            "critic_grad_norm_last": last.get("critic_grad_norm"),
            "actor_grad_norm_last": last.get("actor_grad_norm"),
            "ratio_last": last.get("ratio"),
            "crashed": meta.get("crashed"),
            "run_dir": run_dir,
            "checkpoint_path": ckpt if ckpt_ok else None,
            "log_path": logpath,
        })

        curve_path = os.path.join(OUT_DIR, "curves", f"{exp}.csv")
        keys = ["episode", "total_num_steps", "fps", "average_episode_rewards",
                "value_loss", "policy_loss", "policy_entropy_loss",
                "policy_entropy_true_sum",
                "actor_grad_norm", "critic_grad_norm", "ratio", "wall_time"]
        with open(curve_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for e in eps:
                w.writerow(e)

    summary_path = os.path.join(OUT_DIR, "summary.csv")
    if summary:
        keys = list(summary[0].keys())
        with open(summary_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(summary)

    print(f"wrote {summary_path}  ({len(summary)} experiments)")
    print(f"wrote {OUT_DIR}/curves/*.csv")
    for s in summary:
        print(f"  {s['experiment']:38s} steps={str(s['steps_done']):>10s} "
              f"fps={str(s['fps_last']):>7s} rew={str(s['train_reward_last'])[:9]:>9s} "
              f"eval={str(s['eval_reward_last'])[:9]:>9s} crashed={s['crashed']}")


if __name__ == "__main__":
    main()
