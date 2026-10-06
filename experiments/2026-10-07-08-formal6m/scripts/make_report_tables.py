#!/usr/bin/env python
"""Emit paste-ready markdown tables for the report, refreshed each sweep.

Writing these mechanically at the end of the night is how the report gets final
numbers without transcription errors, and it means an interrupted final assembly
still has the tables on disk.

Sections written to <out-dir>/report_tables.md
----------------------------------------------
  A. 运行状态总表              summary.csv (refreshed via collect_metrics.py)
  B. Scaling 对比表            stdout of scripts/scaling_table.py
  C. 归一化后的 critic 对比     stdout of scripts/normalized_scaling.py
  D. 逐实验资源峰值             <out-dir>/resources.csv
  E. OFFICIAL BASELINE TABLE   required by docs/formal_repro_scaling_2026-10-07_08.md
  F. SCALING TABLE             required by the same report

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/make_report_tables.py -> <campaign>), so the copy inside a
campaign always targets that campaign: the copy under
experiments/2026-10-07-08-formal6m/ drives the formal campaign, the copy under
experiments/2026-10-04-night/ drives the pilot. Explicit overrides for
cross-campaign comparisons:

  --campaign-root DIR / --root DIR   campaign the tables report on
                                     (env: CAMPAIGN_ROOT, then LAG_CAMPAIGN_ROOT)
  --out-dir DIR                      where the tables are written
                                     (env: OUT_DIR; default: <campaign>/metrics)

so a foreign campaign (e.g. the 2026-10-04 pilot) is read with --campaign-root
while every write stays under --out-dir.

Status vocabulary (sections E/F; exact tokens)
----------------------------------------------
  completed_6M    target reached (the num_env_steps budget from log/ledger), or
                  the run exhausted its full episode schedule and exited
                  cleanly (rc=0). The runner floors the episode count --
                  episodes = num_env_steps // 3000 // threads -- so e.g. the
                  3-thread 1v1 lanes terminate at 5,994,000/6,000,000 steps by
                  construction: that is completion, not failure.
  running         started and still writing (fresh artefacts, no end marker)
  failed          stopped short of target/episode schedule with an error that
                  is not a clean interrupt, or went silent after real progress
                  without having consumed the whole episode schedule
  time_cutoff     stopped short of target by a clean interrupt (the queue's
                  `timeout -s INT` wall-clock cap raises KeyboardInterrupt)
  early_error     error before the first PPO update completed (e.g. F9)
  not_applicable  known official entry that was never launched (F9 scenario)
Status is derived from the run dir (metrics.jsonl + checkpoints), the stdout log
and the queue ledger (configs/queue_*.txt + status/queue_*.status). A run that
is still writing always reads `running`, never `completed_6M`.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_CAMPAIGN = SCRIPTS_DIR.parent  # <campaign>/scripts/x.py -> <campaign>

# --------------------------------------------------------------- log patterns

STEP_RE = re.compile(
    r"Exp (?P<exp>\S+) updates (?P<ep>\d+)/(?P<eps>\d+) episodes, "
    r"total num timesteps (?P<steps>\d+)/(?P<total>\d+), FPS (?P<fps>[\d.]+)\.")
TRAIN_REW_RE = re.compile(r"average episode rewards is\s*(-?[\d.eE+]+)")
EVAL_REW_RE = re.compile(r"eval average episode rewards:\s*(-?[\d.eE+-]+)")
START_RE = re.compile(r"^start\s+:\s+(\S+)", re.M)
SEED_RE = re.compile(r"^algo\s+:\s+\S+\s+seed=(\d+)", re.M)
THREADS_RE = re.compile(r"^threads\s+:\s+(\d+)", re.M)
EXIT_RE = re.compile(r"^EXPERIMENT (\S+) exited with code (\d+)", re.M)
TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\)")
CLEAN_INT_RE = re.compile(r"^(KeyboardInterrupt|SystemExit)\s*$", re.M)

# Scaling-run names, both campaign generations (mirrors scaling_table.py):
#   pilot  : scaling_<N>v<N>_<variant>[_s<seed>]
#   formal : f6m_<N>v<N>_<variant>_s<seed>
RUN_RE = re.compile(
    r"^(?:scaling_|f6m_)(?P<n>\d+)v\d+_(?P<variant>noweapon|shoot)(?:_s(?P<seed>\d))?$")
GPU_RE = re.compile(r"_gpu(\d+)_")

STATUS_VOCAB = ("completed_6M", "running", "failed", "time_cutoff",
                "early_error", "not_applicable")

STATUS_ZH = {
    "completed_6M": "已完成 (达到步数预算)",
    "running": "运行中 (仍在写入)",
    "failed": "**失败**",
    "time_cutoff": "已结束 (墙钟上限截断)",
    "early_error": "**启动即失败**",
    "not_applicable": "不适用",
}

# Official entries documented as impossible to run (status/running_jobs.md):
# F9 -- 1v1/ShootMissile/HierarchyVsBaseline dies at the first env step with
# `TypeError: 'NoneType' object is not subscriptable`; it is recorded as
# not_applicable, not as a failure of this campaign, and was never launched.
# The experiment id is the one it would have had under this campaign's naming.
# Such ids are specific to a campaign generation, so an entry is emitted only
# when the reported campaign itself uses the same experiment-family prefix
# (f6m_); a foreign-campaign view (--campaign-root) never gains this row.
KNOWN_NOT_APPLICABLE = [{
    "experiment": "f6m_official_1v1_shoot_hier_vsbaseline",
    "scenario": "1v1/ShootMissile/HierarchyVsBaseline",
    "reason": "F9 (docs/night_failures.md): TypeError at first env step; "
              "recorded not_applicable in status/running_jobs.md, not launched",
}]

F9_SCENARIO = "1v1/ShootMissile/HierarchyVsBaseline"


# ----------------------------------------------------------------- utilities

def resolve_campaign(cli=None):
    """CLI (--campaign-root / --root) > env > campaign derived from this file."""
    root = cli or os.environ.get("CAMPAIGN_ROOT") or os.environ.get("LAG_CAMPAIGN_ROOT")
    return Path(root).expanduser().resolve() if root else DEFAULT_CAMPAIGN


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def g(v, nd=4):
    try:
        return f"{float(v):.{nd}g}"
    except (TypeError, ValueError):
        return "-" if v in (None, "") else str(v)


def fmt(v, nd=5):
    if v is None or v == "":
        return "-"
    try:
        return f"{float(v):.{nd}g}"
    except (TypeError, ValueError):
        return str(v)


def fmt_int(v):
    if v is None or v == "":
        return "-"
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return str(v)


def parse_dt(txt):
    """ISO timestamp -> epoch seconds (queue ledger + log header are +08:00)."""
    if not txt:
        return None
    try:
        return datetime.fromisoformat(txt).timestamp()
    except ValueError:
        return None


def parse_steps(v):
    """'6e6' / '6000000' / 6000000 -> int."""
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- data reads

def load_ledger(camp):
    """(planned, state) from configs/queue_*.txt + status/queue_*.status.

    planned: exp -> {threads, steps, tlimit, env, scenario, algo, seed, queue}
    state:   exp -> {start: epoch, end: epoch, rc: str}   (liveness signal)
    """
    planned, state = {}, {}
    for qf in sorted((camp / "configs").glob("queue_*.txt")):
        try:
            text = qf.read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 8:
                continue
            planned[p[0]] = {
                "threads": parse_steps(p[1]), "steps": parse_steps(p[2]),
                "time_limit_s": p[3], "env": p[4], "scenario": p[5],
                "algo": p[6], "seed": p[7], "queue": qf.name,
                "extra": " ".join(p[8:]).strip(),
            }
    for sf in sorted((camp / "status").glob("queue_*.status")):
        try:
            lines = sf.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            m = re.match(r">>> (\S+) start (\S+)", line)
            if m:
                exp, ts = m.groups()
                dt = parse_dt(ts)
                st = state.setdefault(exp, {})
                if dt and (st.get("start") is None or dt < st["start"]):
                    st["start"] = dt
                continue
            m = re.match(r"<<< (\S+) end (\S+) rc=(\d*)", line)
            if m:
                exp, ts, rc = m.groups()
                st = state.setdefault(exp, {})
                dt = parse_dt(ts)
                if dt:
                    st["end"] = dt
                st["rc"] = rc
    return planned, state


def latest_log(camp, exp):
    cands = sorted((camp / "logs").glob(f"{exp}_seed*.log"),
                   key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def parse_log(path):
    txt = path.read_text(errors="replace")
    out = {"start": None, "seed": None, "threads": None, "steps": None,
           "target": None, "fps": None, "rew_first": None, "rew_last": None,
           "evals": [], "traceback": False, "clean_interrupt": False,
           "exit_code": None, "update_last": None, "updates_total": None}
    m = START_RE.search(txt)
    if m:
        out["start"] = parse_dt(m.group(1))
    m = SEED_RE.search(txt)
    if m:
        out["seed"] = int(m.group(1))
    m = THREADS_RE.search(txt)
    if m:
        out["threads"] = int(m.group(1))
    m = EXIT_RE.search(txt)
    if m:
        out["exit_code"] = int(m.group(2))
    for mm in STEP_RE.finditer(txt):
        out["steps"] = int(mm.group("steps"))
        out["target"] = int(mm.group("total"))
        out["fps"] = float(mm.group("fps"))
        # "updates ep/eps" prints the 0-based index of the update just finished,
        # so after the whole (floored) schedule ep == eps - 1.
        out["update_last"] = int(mm.group("ep"))
        out["updates_total"] = int(mm.group("eps"))
    rews = TRAIN_REW_RE.findall(txt)
    if rews:
        out["rew_first"], out["rew_last"] = float(rews[0]), float(rews[-1])
    out["evals"] = [float(x) for x in EVAL_REW_RE.findall(txt)]
    out["traceback"] = bool(TRACEBACK_RE.search(txt))
    # `timeout -s INT` (the queue wall-clock cap) ends in a clean
    # KeyboardInterrupt/SystemExit, not in a crash -- see collect_metrics.py.
    out["clean_interrupt"] = bool(CLEAN_INT_RE.search(txt[-4000:]))
    return out


def find_run_dir(repo, exp):
    """Newest run dir for an experiment (runner nests it by env/scenario/algo)."""
    hits = sorted(repo.glob(f"scripts/results/**/{exp}/run*/metrics.jsonl"))
    return hits[-1].parent if hits else None


def read_metrics(run_dir):
    out = {"steps": None, "rew_first": None, "rew_last": None, "eval_last": None,
           "value_loss": None, "critic_grad": None, "rows": 0}
    if run_dir is None:
        return out
    p = run_dir / "metrics.jsonl"
    if not p.exists():
        return out
    with p.open(errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)   # a torn last line is simply skipped
            except json.JSONDecodeError:
                continue
            out["rows"] += 1
            if "total_num_steps" in r:
                s = int(r["total_num_steps"])
                out["steps"] = s if out["steps"] is None else max(out["steps"], s)
            if "average_episode_rewards" in r:
                if out["rew_first"] is None:
                    out["rew_first"] = r["average_episode_rewards"]
                out["rew_last"] = r["average_episode_rewards"]
            if "eval_average_episode_rewards" in r:
                out["eval_last"] = r["eval_average_episode_rewards"]
            if "value_loss" in r:
                out["value_loss"] = r["value_loss"]
            if "critic_grad_norm" in r:
                out["critic_grad"] = r["critic_grad_norm"]
    return out


def build_record(camp, repo, name, planned, ledger):
    """One row of state for an experiment, from ledger + log + run dir."""
    pl = planned.get(name, {})
    st = ledger.get(name, {})
    rec = {
        "exp": name, "seed": pl.get("seed"), "threads": pl.get("threads"),
        "target": pl.get("steps"), "steps": None, "fps": None,
        "rew_first": None, "rew_last": None, "eval": None,
        "value_loss": None, "critic_grad": None,
        "start": st.get("start"), "end": st.get("end"), "rc": st.get("rc"),
        "log": None, "run_dir": None, "checkpoint": None, "mtime": None,
        "traceback": False, "clean_interrupt": False, "exit_code": None,
        "update_last": None, "updates_total": None,
        "status": None,
    }
    log = latest_log(camp, name)
    if log is not None:
        rec["log"] = log
        lg = parse_log(log)
        if lg["seed"] is not None:
            rec["seed"] = lg["seed"]
        if lg["threads"] is not None:
            rec["threads"] = lg["threads"]
        if lg["start"] is not None:
            rec["start"] = lg["start"]
        if lg["steps"] is not None:
            rec["steps"] = lg["steps"]
        if lg["target"] is not None:
            rec["target"] = lg["target"]
        rec["fps"] = lg["fps"]
        rec["rew_first"], rec["rew_last"] = lg["rew_first"], lg["rew_last"]
        if lg["evals"]:
            rec["eval"] = lg["evals"][-1]
        rec["traceback"] = lg["traceback"]
        rec["clean_interrupt"] = lg["clean_interrupt"]
        rec["exit_code"] = lg["exit_code"]
        rec["update_last"] = lg["update_last"]
        rec["updates_total"] = lg["updates_total"]
        rec["mtime"] = log.stat().st_mtime

    run_dir = find_run_dir(repo, name)
    if run_dir is not None:
        rec["run_dir"] = run_dir
        mj = read_metrics(run_dir)
        if mj["steps"] is not None:
            rec["steps"] = mj["steps"] if rec["steps"] is None else max(rec["steps"], mj["steps"])
        if mj["rew_first"] is not None:
            rec["rew_first"] = mj["rew_first"]
        if mj["rew_last"] is not None:
            rec["rew_last"] = mj["rew_last"]
        if mj["eval_last"] is not None:      # metrics.jsonl beats the log pairing
            rec["eval"] = mj["eval_last"]
        rec["value_loss"], rec["critic_grad"] = mj["value_loss"], mj["critic_grad"]
        ck = run_dir / "actor_latest.pt"
        if ck.exists():
            rec["checkpoint"] = ck.name
        if (run_dir / "metrics.jsonl").exists():
            mt = (run_dir / "metrics.jsonl").stat().st_mtime
            rec["mtime"] = mt if rec["mtime"] is None else max(rec["mtime"], mt)
    return rec


def classify(rec, now, stale_min):
    """One exact status token (see module docstring) for an experiment record."""
    steps, target = rec["steps"], rec["target"]
    threads = rec["threads"] or 1
    started = (rec["start"] is not None or rec["log"] is not None
               or rec["run_dir"] is not None)
    ended = rec["end"] is not None or rec["exit_code"] is not None

    if steps is not None and target and steps >= target:
        return "completed_6M"
    if not started:
        return "not_applicable"

    # Freshness window: never call a run dead while it is merely sitting
    # between PPO updates -- 10v10 needs ~15 min per 60k-step update.
    window = stale_min * 60.0
    if rec["fps"] and rec["threads"]:
        window = max(window, 3.0 * rec["threads"] * 3000.0 / rec["fps"])
    ref = rec["mtime"] if rec["mtime"] is not None else rec["start"]
    fresh = ref is not None and (now - ref) < window

    if not ended and fresh:
        return "running"
    if rec["traceback"]:
        if rec["clean_interrupt"]:
            return "time_cutoff"
        if steps is None or steps < threads * 3000:   # died inside update 0
            return "early_error"
        return "failed"
    # A clean end (rc=0) after the runner consumed its entire floored episode
    # schedule is completion, not failure: episodes = num_env_steps // 3000 //
    # threads floors, so e.g. the 3-thread 1v1 lanes stop short of the 6M
    # budget at 5,994,000 steps BY CONSTRUCTION (666 episodes x 9,000).
    if (ended and rec.get("update_last") is not None
            and rec.get("updates_total")
            and rec["update_last"] >= rec["updates_total"] - 1
            and steps is not None and rec["exit_code"] in (None, 0)):
        return "completed_6M"
    # ended (or silent) without a crash signature and short of target
    return "failed"


def fmt_wall(rec, now):
    start = rec["start"]
    if start is None:
        return "-"
    if rec["status"] == "running":
        end = now
    elif rec["end"] is not None:
        end = rec["end"]
    elif rec["mtime"] is not None:
        end = rec["mtime"]
    else:
        end = now
    if end < start:
        return "-"
    return f"{(end - start) / 3600:.2f} h"


# --------------------------------------------------- resource sampling (light)

def _match_filter(args_txt):
    """Processes worth sampling: the run's own train_jsbsim.py main + workers."""
    for bad in ("run_train.sh", "timeout -k ", "ps -eo", "grep", "nvidia-smi",
                "make_report_tables", "watch_f6m", "os_watchdog"):
        if bad in args_txt:
            return False
    return True


def sample_resources(camp, out_dir, names):
    """One-shot ps + nvidia-smi snapshot appended to <out-dir>/resources.csv.

    Pilot-compatible schema: timestamp,experiment,n_procs,cpu_pct,rss_gb,
    gpu_id,gpu_util,gpu_vram_mb.  Deliberately cheap (a single ps and two
    nvidia-smi queries); best-effort -- any failure just leaves the tables'
    CPU/RAM/VRAM cells empty, it never breaks the report.
    """
    try:
        ps_out = subprocess.run(["ps", "-eo", "pid,rss,pcpu,args", "--no-headers"],
                                capture_output=True, text=True, timeout=20).stdout
    except Exception:                                        # noqa: BLE001
        return
    gpu_util, vram_by_pid = {}, {}
    try:
        q = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20).stdout
        for line in q.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) == 2:
                gpu_util[int(p[0])] = float(p[1])
    except Exception:                                        # noqa: BLE001
        pass
    try:
        q = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_gpu_memory",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20).stdout
        for line in q.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) == 2:
                try:
                    vram_by_pid[int(p[0])] = float(p[1])
                except ValueError:
                    continue
    except Exception:                                        # noqa: BLE001
        pass

    ordered = sorted(names, key=len, reverse=True)   # longest name first
    agg = {}
    for line in ps_out.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) < 4:
            continue
        pid_s, rss_s, cpu_s, args_txt = parts
        if not _match_filter(args_txt):
            continue
        for name in ordered:
            if name in args_txt:
                try:
                    pid = int(pid_s)
                except ValueError:
                    continue
                a = agg.setdefault(name, {"n": 0, "cpu": 0.0, "rss": 0.0, "vram": 0.0})
                a["n"] += 1
                a["cpu"] += float(cpu_s or 0)
                a["rss"] += float(rss_s or 0) / 1024 / 1024
                a["vram"] += vram_by_pid.get(pid, 0.0)
                break
    if not agg:
        return
    res_path = Path(out_dir) / "resources.csv"
    res_path.parent.mkdir(parents=True, exist_ok=True)
    new = not res_path.exists()
    ts = datetime.now().isoformat(timespec="seconds")
    with res_path.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "experiment", "n_procs", "cpu_pct", "rss_gb",
                        "gpu_id", "gpu_util", "gpu_vram_mb"])
        for name, a in sorted(agg.items()):
            log = latest_log(camp, name)
            gpu_id = ""
            if log is not None:
                m = GPU_RE.search(log.name)
                if m:
                    gpu_id = int(m.group(1))
            w.writerow([ts, name, a["n"], round(a["cpu"], 1), round(a["rss"], 2),
                        gpu_id if gpu_id != "" else "",
                        (gpu_util.get(gpu_id, "") if gpu_id != "" else ""),
                        round(a["vram"])])


def reads_peaks(out_dir):
    """exp -> {cpu_cores, ram_gb, vram_mb} peak over all recorded samples."""
    peak = {}
    for r in read_csv(Path(out_dir) / "resources.csv"):
        e = r.get("experiment")
        if not e:
            continue
        p = peak.setdefault(e, {"cpu": 0.0, "ram": 0.0, "vram": 0.0})
        for key, col in (("cpu", "cpu_pct"), ("ram", "rss_gb"), ("vram", "gpu_vram_mb")):
            try:
                p[key] = max(p[key], float(r.get(col) or 0))
            except ValueError:
                pass
    return {e: {"cpu_cores": p["cpu"] / 100.0, "ram_gb": p["ram"],
                "vram_mb": p["vram"]} for e, p in peak.items()}


# ------------------------------------------------------------- markdown bits

def baseline_table(out_dir, by_exp):
    rows = [r for r in read_csv(Path(out_dir) / "summary.csv")
            if r["experiment"].startswith(("official_", "scaling_", "f6m_"))]
    # one row per experiment, newest log wins
    seen = {}
    for r in rows:
        seen[r["experiment"]] = r
    order = sorted(seen, key=lambda e: (not e.startswith(("official_", "f6m_official")), e))
    out = ["| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |",
           "|---|---|---|---|---|---|---|"]
    for e in order:
        r = seen[e]
        rec = by_exp.get(e)
        if rec is not None:
            status = STATUS_ZH.get(rec["status"], rec["status"])
        else:                       # summary row with no artefact record (rare)
            try:
                done, tgt = int(r["steps_done"]), int(r["steps_target"])
                status = "已完成 (达到步数预算)" if done >= tgt else "运行中 (仍在写入)"
            except (TypeError, ValueError):
                status = "未启动"
        if r.get("crashed") == "True":
            status = "**失败 (见 F9)**"
        ck = "yes" if r.get("checkpoint_path") else "no"
        out.append(f"| `{e}` | {status} | {r.get('steps_done','-')}/{r.get('steps_target','-')} "
                   f"| {g(r.get('fps_last'),5)} | {g(r.get('train_reward_first'),4)} → {g(r.get('train_reward_last'),4)} "
                   f"| {g(r.get('eval_reward_last'),5)} | {ck} |")
    return "\n".join(out)


def resources_table(out_dir):
    rows = read_csv(Path(out_dir) / "resources.csv")
    if not rows:
        return "_(no resource samples yet)_"
    peak = {}
    for r in rows:
        e = r["experiment"]
        cur = peak.setdefault(e, {"n": 0, "cpu": 0.0, "rss": 0.0, "vram": 0.0, "gpu": ""})
        cur["n"] = max(cur["n"], int(r["n_procs"] or 0))
        cur["cpu"] = max(cur["cpu"], float(r["cpu_pct"] or 0))
        cur["rss"] = max(cur["rss"] or 0, float(r["rss_gb"] or 0))
        cur["vram"] = max(cur["vram"], float(r["gpu_vram_mb"] or 0))
        cur["gpu"] = r.get("gpu_id", "")
    out = ["| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |",
           "|---|---|---|---|---|---|---|"]
    for e in sorted(peak):
        p = peak[e]
        out.append(f"| `{e}` | {p['n']} | {p['cpu']:.0f}% | {p['cpu']/100:.1f} | "
                   f"{p['rss']:.2f} GB | {p['gpu']} | {p['vram']:.0f} MB |")
    return "\n".join(out)


OFFICIAL_HDR = ["Experiment", "Seed", "Steps", "Wall time", "FPS",
                "Initial reward", "Final reward", "Eval", "Status", "Checkpoint"]
SCALING_HDR = ["Scale", "Agents", "Seed", "Steps", "FPS", "Wall time",
               "Reward raw", "Reward normalized", "Value loss", "Critic grad",
               "CPU", "RAM", "VRAM", "Status"]


def campaign_owns(na_exp, records):
    """True iff the reported campaign uses the same experiment-family prefix
    (everything up to the first '_') as a KNOWN_NOT_APPLICABLE id. Keeps this
    campaign's documented-anchor rows out of foreign-campaign views."""
    prefix = na_exp.split("_", 1)[0] + "_"
    return any(r["exp"].startswith(prefix) for r in records)


def official_table(records, now):
    """Section E -- one row per official baseline run (see report §5)."""
    sel = sorted((r for r in records
                  if r["exp"].startswith(("f6m_official", "official_"))),
                 key=lambda r: r["exp"])
    out = ["| " + " | ".join(OFFICIAL_HDR) + " |", "|" + "---|" * len(OFFICIAL_HDR)]
    for r in sel:
        out.append("| " + " | ".join([
            r["exp"],
            str(int(r["seed"])) if r.get("seed") not in (None, "") else "-",
            fmt_int(r["steps"]), fmt_wall(r, now), fmt(r["fps"]),
            fmt(r["rew_first"]), fmt(r["rew_last"]), fmt(r["eval"]),
            r["status"], r["checkpoint"] or "-",
        ]) + " |")
    for na in KNOWN_NOT_APPLICABLE:
        if not campaign_owns(na["experiment"], records):
            continue
        if any(r["exp"] == na["experiment"] for r in sel):
            continue
        out.append("| " + " | ".join([
            na["experiment"], "-", "-", "-", "-", "-", "-", "-",
            "not_applicable", "-"]) + " |")
    return "\n".join(out), sel


def scaling_table(records, peaks, now):
    """Section F -- one row per N-v-N scaling run (see report §6/§7)."""
    sel = []
    for r in records:
        m = RUN_RE.match(r["exp"])
        if m:
            sel.append((int(m.group("n")), r))
    sel.sort(key=lambda t: (t[0], t[1]["exp"]))
    out = ["| " + " | ".join(SCALING_HDR) + " |", "|" + "---|" * len(SCALING_HDR)]
    for n, r in sel:
        p = peaks.get(r["exp"], {})
        rw = r["rew_last"]
        rw_norm = "-"
        if rw is not None:
            try:
                rw_norm = fmt(float(rw) / n)
            except (TypeError, ValueError):
                rw_norm = "-"
        cpu = f"{p['cpu_cores']:.1f}" if p.get("cpu_cores") else "-"
        ram = f"{p['ram_gb']:.2f} GB" if p.get("ram_gb") else "-"
        vram = f"{p['vram_mb']:.0f} MB" if p.get("vram_mb") else "-"
        out.append("| " + " | ".join([
            f"{n}v{n}", str(2 * n),
            str(int(r["seed"])) if r.get("seed") not in (None, "") else "-",
            fmt_int(r["steps"]), fmt(r["fps"]), fmt_wall(r, now),
            fmt(rw), rw_norm, fmt(r["value_loss"]), fmt(r["critic_grad"]),
            cpu, ram, vram, r["status"],
        ]) + " |")
    return "\n".join(out), sel


def run_child(script, args, repo):
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo),
                             timeout=300)
        if res.returncode != 0:
            return f"({script} exited {res.returncode})\n{res.stdout.strip()}\n{res.stderr.strip()}"
        return res.stdout
    except Exception as e:                                   # noqa: BLE001
        return f"({script} failed: {e})"


# ------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Emit report_tables.md for a campaign (campaign root derived "
                    "from this file's location unless overridden).")
    ap.add_argument("--campaign-root", "--root", dest="campaign_root", default=None,
                    help="campaign the tables report on (default: derived from "
                         "this script's location; env CAMPAIGN_ROOT / LAG_CAMPAIGN_ROOT)")
    ap.add_argument("--out-dir", default=None,
                    help="where the tables + refreshed summary/resources go "
                         "(default: <campaign-root>/metrics; env OUT_DIR)")
    ap.add_argument("--stale-min", type=float, default=45.0,
                    help="no new artefact for this many minutes means the run is "
                         "not 'running' (auto-extended to 3x its update cadence)")
    ap.add_argument("--no-refresh", action="store_true",
                    help="skip re-running collect_metrics.py first")
    ap.add_argument("--no-sample", action="store_true",
                    help="skip the one-shot ps/nvidia-smi resource snapshot")
    args = ap.parse_args(argv)

    camp = resolve_campaign(args.campaign_root)
    repo = camp.parents[1] if len(camp.parents) > 1 else camp
    out_dir = (Path(args.out_dir).expanduser().resolve() if args.out_dir
               else Path(os.environ.get("OUT_DIR", str(camp / "metrics"))).expanduser().resolve())
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "report_tables.md"

    # Refresh the CSVs sections A/B/C read (summary.csv + curves/*.csv). The
    # children take --campaign-root so a foreign campaign is read, while every
    # write stays under out_dir.
    if not args.no_refresh:
        run_child("collect_metrics.py",
                  ["--campaign-root", str(camp), "--out-dir", str(out_dir)], repo)

    scaling = run_child("scaling_table.py",
                        ["--campaign-root", str(camp), "--out-dir", str(out_dir)], repo)
    norm = run_child("normalized_scaling.py",
                     ["--campaign-root", str(camp), "--out-dir", str(out_dir)], repo)

    planned, ledger = load_ledger(camp)
    names = sorted(set(planned)
                   | {p.name.split("_seed")[0] for p in (camp / "logs").glob("*.log")})

    if not args.no_sample:
        sample_resources(camp, out_dir, names)

    now = time.time()
    records = [build_record(camp, repo, name, planned, ledger) for name in names]
    for rec in records:
        rec["status"] = classify(rec, now, args.stale_min)
    by_exp = {r["exp"]: r for r in records}
    peaks = reads_peaks(out_dir)

    official_md, _ = official_table(records, now)
    scaling_md, _ = scaling_table(records, peaks, now)

    queued = sorted(r["exp"] for r in records
                    if r["status"] == "not_applicable" and r["exp"] in planned
                    and r["exp"] not in {na["experiment"] for na in KNOWN_NOT_APPLICABLE})

    parts = [
        "# 报告表格快照（自动生成，勿手改）",
        "",
        "由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。",
        f"campaign root: `{camp}`（本文件位置推导；--campaign-root / $CAMPAIGN_ROOT 可覆盖）",
        "",
        "## A. Baseline 复现与缩放实验状态",
        "",
        baseline_table(out_dir, by_exp),
        "",
        "## B. Scaling 对比表（含 wall-clock 归一化）",
        "",
        scaling.strip(),
        "",
        "## C. 归一化后的 critic 对比",
        "",
        norm.strip(),
        "",
        "## D. 逐实验资源占用（峰值）",
        "",
        resources_table(out_dir),
        "",
        "## E. OFFICIAL BASELINE TABLE",
        "",
        official_md,
        "",
        f"_Status ∈ {{{', '.join(STATUS_VOCAB)}}}；Steps 为目标 6,000,000 vectorised env steps 的已完成量；"
        "running 行的 Steps/FPS/Wall time/reward 为生成时刻的实时值（Wall time = 队列启动至今）。"
        "3-thread 的 1v1 lane 因 runner 取整（6e6 // 3000 // 3 = 666 episodes）在 5,994,000 步即自然结束，"
        "计为 completed_6M（不是 failed）。_",
        "",
        f"_F9: `{F9_SCENARIO}` 是官方入口但在首个 env step 即报错（TypeError），本轮未启动，"
        "按 `status/running_jobs.md` 记为 not_applicable。_",
        "",
    ]
    if queued:
        parts += [f"_队列中尚未启动（无任何 artefacts）：{', '.join('`'+q+'`' for q in queued)}。_", ""]
    parts += [
        "## F. SCALING TABLE",
        "",
        scaling_md,
        "",
        "_Reward normalized = 末次训练 reward / N（NoWeapon 家族 PostureReward 对每个 enemy 求和，故除以 team size N；"
        "ShootMissile 家族不适用该归一化）。CPU/RAM/VRAM 为该实验进程的实测峰值"
        "（ps + nvidia-smi --query-compute-apps，随本脚本每次运行累积进 metrics/resources.csv；"
        "'-' 表示尚无采样）。_",
        "",
    ]
    out_path.write_text("\n".join(parts) + "\n")
    print(f"wrote {out_path}")
    print()
    print("=== E. OFFICIAL BASELINE TABLE ===")
    print(official_md)
    print()
    print("=== F. SCALING TABLE ===")
    print(scaling_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
