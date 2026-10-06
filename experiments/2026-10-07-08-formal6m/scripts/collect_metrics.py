#!/usr/bin/env python
"""Collect every experiment's stdout log + metrics.jsonl into analysis-ready CSVs.

Produces (all under <campaign>/metrics/ by default):
  summary.csv          one row per experiment (status, steps, FPS, wall time,
                       final train/eval reward, checkpoint path, ...)
  curves/<exp>.csv     per-episode learning curves

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/collect_metrics.py -> <campaign>) so this same script works
for any campaign without edits. Overrides, for cross-campaign comparisons
(pair --campaign-root on the foreign campaign with --out-dir back home so the
foreign campaign stays read-only):

  --campaign-root / $CAMPAIGN_ROOT   campaign dir (logs/, configs/, status/, metrics/)
  --results-root  / $RESULTS_ROOT    results tree holding <env>/<scen>/<algo>/<exp>/run*/
                                     (default: derived from the campaign root as
                                     <repo>/scripts/results)
  --out-dir       / $OUT_DIR         where summary.csv + curves/ are written
                                     (default: <campaign-root>/metrics)

Everything is derived from artefacts on disk (the tee'd stdout logs and the
per-run metrics.jsonl), so it can be re-run at any time without touching the
training processes -- important because the runs are still going. Partial runs
are handled deliberately: a run may be a few percent in, have a one-line
metrics.jsonl and hold only actor_0.pt and no actor_latest.pt yet.
"""
import argparse
import csv
import glob
import json
import os
import re
from datetime import datetime
from pathlib import Path

DEFAULT_CAMPAIGN = Path(__file__).resolve().parents[1]

# Legacy 2026-10-04 queue filenames whose GPU is not encoded in the name.
LEGACY_GPU_QUEUES = {"queue_extra.txt": "0", "queue_seeds.txt": "1"}

EP_RE = re.compile(
    r"Scenario (?P<scenario>\S+) Algo (?P<algo>\S+) Exp (?P<exp>\S+) "
    r"updates (?P<ep>\d+)/(?P<episodes>\d+) episodes, "
    r"total num timesteps (?P<steps>\d+)/(?P<total>\d+), "
    # FPS is normally printed with a trailing period ("FPS 133."), but accept a
    # missing one too: `[\d.]+\.` would silently truncate "12.5" to "12" (the
    # group backtracks to "12" so the literal "." can match the decimal point).
    r"FPS (?P<fps>\d+(?:\.\d+)?)\.?")
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


def resolve_paths(argv=None):
    """Resolve (campaign_dir, results_dir, out_dir) from CLI/env/defaults."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign-root", default=os.environ.get("CAMPAIGN_ROOT"),
                    help="campaign directory; default: derived from this script's "
                         f"location ({DEFAULT_CAMPAIGN})")
    ap.add_argument("--results-root", default=os.environ.get("RESULTS_ROOT"),
                    help="root of the raw results tree; default: "
                         "<campaign-root>/../../scripts/results")
    ap.add_argument("--out-dir", default=os.environ.get("OUT_DIR"),
                    help="output dir for summary.csv/curves; default: "
                         "<campaign-root>/metrics")
    args = ap.parse_args(argv)

    campaign = (Path(args.campaign_root).expanduser().resolve()
                if args.campaign_root else DEFAULT_CAMPAIGN)
    # Campaigns live at <repo>/experiments/<name>, so the repo -- and with it
    # the shared scripts/results tree -- is derivable from the campaign root.
    repo = campaign.parents[1] if len(campaign.parents) > 1 else campaign
    results = (Path(args.results_root).expanduser().resolve()
               if args.results_root else repo / "scripts" / "results")
    out = (Path(args.out_dir).expanduser().resolve()
           if args.out_dir else campaign / "metrics")
    return campaign, results, out


def status_ledgers(campaign):
    """All queue status ledgers, both naming schemes, deduped and sorted.

    wave 1 (run_queue.sh):       status/queue_gpu<N>.status
    wave 2 (run_queue_lane.sh):  status/queue_<queuefile-stem>.status
                                 e.g. configs/queue_1v1a.txt ->
                                      status/queue_queue_1v1a.status
    """
    status_dir = Path(campaign) / "status"
    files = set()
    for pat in ("queue_gpu*.status", "queue_queue_*.status"):
        files.update(glob.glob(str(status_dir / pat)))
    return sorted(files)


def status_ledger_gpu(campaign):
    """experiment -> gpu, read from the ledgers' '>>> name start ... gpu=N' lines."""
    gpu = {}
    for f in status_ledgers(campaign):
        for line in open(f, encoding="utf-8", errors="replace"):
            m = re.match(r">>> (\S+) start\b.*\bgpu=(\d+)", line)
            if m:
                gpu.setdefault(m.group(1), m.group(2))
    return gpu


def queue_gpu_hint(queue_file):
    """GPU id encoded in a wave-1 queue filename (queue_gpu0.txt, queue_gpu1b.txt)."""
    m = re.match(r"queue_gpu(\d+)[a-z]*\.txt$", os.path.basename(queue_file))
    return m.group(1) if m else None


def queue_metadata(campaign):
    """experiment -> {env_name, scenario, algo, seed, gpu, n_threads}.

    Fallback for jobs launched before run_train.sh started writing its header
    into the log file: the queue definitions still carry the same information.
    Reads every configs/queue_*.txt (both waves); the GPU comes from the
    filename when it encodes one, otherwise from the status ledgers.
    """
    meta = {}
    ledger_gpu = status_ledger_gpu(campaign)
    for qf in sorted(glob.glob(str(Path(campaign) / "configs" / "queue_*.txt"))):
        gpu = queue_gpu_hint(qf) or LEGACY_GPU_QUEUES.get(os.path.basename(qf), "")
        for line in open(qf, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split("|")
            if len(p) < 8:
                continue
            meta[p[0]] = {"env_name": p[4], "scenario": p[5], "algo": p[6],
                          "seed": p[7], "gpu": gpu or ledger_gpu.get(p[0], ""),
                          "n_threads": p[1]}
    return meta


def find_checkpoint(run_dir):
    """Newest actor checkpoint, preferring actor_latest.pt.

    Safe on partial runs: a run holding only actor_0.pt so far (actor_latest.pt
    is written on the next checkpoint cycle) reports actor_0.pt, not nothing.
    """
    if not run_dir:
        return None
    latest = os.path.join(run_dir, "actor_latest.pt")
    if os.path.exists(latest):
        return latest

    def episode(path):
        m = re.match(r"actor_(\d+)\.pt$", os.path.basename(path))
        return int(m.group(1)) if m else -1

    numbered = [p for p in glob.glob(os.path.join(run_dir, "actor_*.pt"))
                if episode(p) >= 0]
    return max(numbered, key=episode) if numbered else None


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


def main(argv=None):
    campaign, results_dir, out_dir = resolve_paths(argv)
    log_dir = campaign / "logs"

    os.makedirs(os.path.join(out_dir, "curves"), exist_ok=True)
    summary = []
    qmeta = queue_metadata(campaign)

    for logpath in sorted(glob.glob(str(log_dir / "*.log"))):
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
            pattern = os.path.join(str(results_dir), meta["env_name"], meta["scenario"],
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
        ckpt = find_checkpoint(run_dir)

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
            "checkpoint_path": ckpt,
            "log_path": logpath,
        })

        curve_path = os.path.join(str(out_dir), "curves", f"{exp}.csv")
        keys = ["episode", "total_num_steps", "fps", "average_episode_rewards",
                "value_loss", "policy_loss", "policy_entropy_loss",
                "policy_entropy_true_sum",
                "actor_grad_norm", "critic_grad_norm", "ratio", "wall_time"]
        with open(curve_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for e in eps:
                w.writerow(e)

    summary_path = os.path.join(str(out_dir), "summary.csv")
    if summary:
        keys = list(summary[0].keys())
        with open(summary_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(summary)

    print(f"campaign root : {campaign}")
    print(f"results root  : {results_dir}")
    print(f"wrote {summary_path}  ({len(summary)} experiments)")
    print(f"wrote {out_dir}/curves/*.csv")
    for s in summary:
        print(f"  {s['experiment']:38s} steps={str(s['steps_done']):>10s} "
              f"fps={str(s['fps_last']):>7s} rew={str(s['train_reward_last'])[:9]:>9s} "
              f"eval={str(s['eval_reward_last'])[:9]:>9s} ckpt={str(s['checkpoint_path']).rsplit('/', 1)[-1]!r:>18s} crashed={s['crashed']}")


if __name__ == "__main__":
    main()
