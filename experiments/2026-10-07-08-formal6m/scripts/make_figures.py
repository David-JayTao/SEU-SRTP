#!/usr/bin/env python
"""Figures for the formal 6M-step campaign.

This file lives at <campaign>/scripts/make_figures.py and targets *its own*
campaign: the campaign root is derived from this file's location, never
hardcoded, so the copy inside experiments/2026-10-07-08-formal6m/ writes to
that campaign's figures/ while the copy inside experiments/2026-10-04-night/
would keep writing to the pilot's.  Two explicit overrides exist:

    --campaign PATH          /  FIG_CAMPAIGN  (default: this file's parent dir)
    --compare PATH[:LABEL]   /  FIG_COMPARE   (optional second campaign to
                                              overlay; no campaign path is
                                              baked in anywhere)

With --compare the six figures are additionally written with a "_with_<label>"
suffix, so the plain formal-only figures are never polluted by the overlay.
In those overlay figures every compared series is drawn dotted with open
markers and a "[<label>]" legend entry: pilot (~1M, time-capped, idle machine)
and formal (6M, live, saturated machine) series are never one undifferentiated
line.  No comparison is drawn by default - the pilot adds nothing to most of
these six figures.

Required outputs (figures/):
    formal_learning_curves_steps.png       reward vs environment steps
    formal_learning_curves_walltime.png    reward vs wall-clock hours
    formal_scaling_reward_normalized.png   reward per enemy vs steps, wall-clock and N
    formal_throughput_vs_agents.png        FPS / env-steps-per-second vs agents
    formal_resource_scaling.png            CPU / RAM / VRAM vs N
    formal_critic_scaling.png              critic dim / params / grad norm vs N

Data sources
------------
Everything is derived from on-disk artefacts only, so this is safe to run
while training continues, and it renders correctly on partial runs:

  * stdout logs   logs/<exp>_seed<k>_gpu<g>_<stamp>.log : the per-update
                  "updates i/N ... total num timesteps S/T, FPS f." lines and
                  the "average episode rewards is ..." values that follow them;
  * run dirs      <repo>/scripts/results/<env>/<scen>/<algo>/<exp>/run1/
                  metrics.jsonl : wall_time and the training diagnostics
                  (value_loss, critic_grad_norm, ...), unioned by
                  total_num_steps exactly like collect_metrics.py does;
  * metrics/curves/<exp>.csv : used when a log is not on disk (e.g. pruned
                  run dir), and preferred as a wall_time source if metrics.jsonl
                  is missing;
  * metrics/resources.csv : per-experiment CPU / RSS / GPU-memory samples.
                  The file is shared with make_report_tables.py (and matches
                  the pilot's sweep.sh schema); this script appends one light
                  1 s /proc + nvidia-smi sample per run, never touching the
                  training processes;
  * metrics/throughput_history.csv : campaign aggregate FPS over time, written
                  by watch_f6m.py;
  * metrics/critic_scaling.json : optional measured critic probe, used if a
                  sibling script has produced it for this campaign.

Colour policy (see the dataviz skill):
  * categorical series use the reference palette's fixed slot order, never
    cycled; within a panel the slot order follows ascending N (or name);
  * identity is never colour-alone: every line series also carries a distinct
    dash pattern and a direct end-label, and every scatter point is directly
    labelled;
  * scatter panels deliberately carry NO colour identity: the skill's
    validate_palette.py (python port; this box has no node) FAILs the
    all-pairs normal-vision floor on the 4-slot set (#eda100 vs #eb6834,
    OKLab dE 13.7 < 15), which is the pairlist that applies to scatters.  The
    line panels use the adjacent pairlist, where slots 1-4 and 1-6 PASS in
    light mode (CVD worst 9.1, normal-vision worst 19.6; the sub-3:1 contrast
    WARN is relieved by the direct labels every series carries);
  * one axis per panel - FPS / CPU / RAM / VRAM each get their own panel
    rather than a second y-axis;
  * sequential (magnitude) uses the single-hue blue ramp, light->dark.
"""
from __future__ import annotations

import argparse
import csv
import json
import numpy as np
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# --------------------------------------------------------------------------
# Paths.  The campaign root is THIS FILE's grandparent; overridable, but no
# campaign path is ever hardcoded.
# --------------------------------------------------------------------------
HERE = Path(__file__).resolve()
CAMP = HERE.parents[1]

FIG = METRICS = CURVES = LOGS = RESULTS = None  # set by configure()


def configure(camp: Path, repo: Path | None = None) -> None:
    global CAMP, FIG, METRICS, CURVES, LOGS, RESULTS
    CAMP = Path(camp).expanduser().resolve()
    FIG = CAMP / "figures"
    METRICS = CAMP / "metrics"
    CURVES = METRICS / "curves"
    LOGS = CAMP / "logs"
    root = Path(repo).expanduser().resolve() if repo else CAMP.parents[1]
    RESULTS = root / "scripts" / "results"
    FIG.mkdir(parents=True, exist_ok=True)


# reference palette, categorical slots in fixed order (see module docstring for
# the validation status of each pairlist actually used here)
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8983"
GRID = "#e3e2de"
DASH = ["-", "--", ":", "-."]
MARK = ["o", "s", "^", "D", "v", "P"]
# style used for every compared (e.g. pilot) series: dotted + x markers + muted
# ink, so a comparison can never read as part of a formal series
CMP_COLOUR = MUTED
CMP_LS = (0, (1.6, 1.6))
CMP_MARK = "x"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "600",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "figure.dpi": 140,
})


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def read_csv(path):
    try:
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def fnum(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # drop NaN, keep inf


def to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def fmt_steps(v):
    v = fnum(v)
    if v is None:
        return "?"
    if v >= 1e6:
        return f"{v / 1e6:.1f}M"
    if v >= 1e3:
        return f"{v / 1e3:.0f}k"
    return f"{v:.0f}"


def fmt_num(y):
    if y is None:
        return ""
    if abs(y) >= 100:
        return f"{y:,.0f}"
    if abs(y) >= 1:
        return f"{y:.2f}".rstrip("0").rstrip(".")
    return f"{y:.3g}"


def core_name(exp):
    """Strip the campaign-generation prefixes so the pilot names
    (scaling_2v2_noweapon_s1) and the formal names (f6m_2v2_noweapon_s0)
    classify identically."""
    for pref in ("f6m_", "scaling_"):
        if exp.startswith(pref):
            return exp[len(pref):]
    return exp


def seed_of(exp):
    m = re.search(r"_s(\d+[a-z]?)$", exp)
    return m.group(1) if m else "0"


def team_size_of(exp):
    m = re.search(r"(\d+)v(\d+)", exp)
    return int(m.group(1)) if m else None


def family_of(exp):
    """-> (family, weapon); family in {scaling, official, other}."""
    core = core_name(exp)
    weapon = "shoot" if ("shoot" in core.lower() or "missile" in core.lower()) else "noweapon"
    if re.match(r"^\d+v\d+_(noweapon|shoot)", core):
        return "scaling", weapon
    if core.startswith("official_"):
        return "official", weapon
    return "other", weapon


def variant_of(exp):
    """Family identity without the seed: the key used to pair a formal run with
    its pilot counterpart (2v2_noweapon, official_1v1_selfplay, ...)."""
    return re.sub(r"_s\d+[a-z]?$", "", core_name(exp))


def label_for(exp):
    core = core_name(exp)
    m = re.match(r"^(\d+v\d+)_(noweapon|shoot)(?:_s(\d+))?$", core)
    if m:
        seed = f" (seed {m.group(3)})" if m.group(3) is not None else ""
        shoot = "" if m.group(2) == "noweapon" else " shoot"
        return f"{m.group(1)}{shoot}{seed}"
    if core.startswith("official_"):
        tail = core[len("official_"):]
        seed = ""
        ms = re.search(r"_s(\d+[a-z]?)$", tail)
        if ms:
            seed = f" (seed {ms.group(1)})"
            tail = tail[: ms.start()]
        return "official " + tail.replace("_", " ") + seed
    return core


def short_label(exp):
    core = core_name(exp)
    m = re.match(r"^(\d+v\d+)_(noweapon|shoot)", core)
    if m:
        return m.group(1) + ("" if m.group(2) == "noweapon" else " shoot")
    if core.startswith("official_"):
        return "off " + re.sub(r"_s\d+[a-z]?$", "", core[len("official_"):]).replace("_", " ")
    return core


def series_style(i):
    return CAT[i % len(CAT)], DASH[i % len(DASH)], MARK[i % len(MARK)]


# --------------------------------------------------------------------------
# log + run loading (works on partial runs; tolerant of a run writing now)
# --------------------------------------------------------------------------
EP_RE = re.compile(
    r"updates (?P<ep>\d+)/(?P<episodes>\d+) episodes, "
    r"total num timesteps (?P<steps>\d+)/(?P<total>\d+), FPS (?P<fps>[\d.]+)\."
)
TRAIN_REW_RE = re.compile(r"average episode rewards is (?P<v>-?[\d.eE+]+)")
EVAL_REW_RE = re.compile(r"eval average episode rewards: (?P<v>-?[\d.eE+-]+)")
HDR_RES = {
    "exp": re.compile(r"^EXPERIMENT\s*:\s*(?P<v>\S+)", re.M),
    "scen": re.compile(r"^env/scen\s*:\s*(?P<env>\S+)\s*/\s*(?P<scen>.+)", re.M),
    "algo": re.compile(r"^algo\s*:\s*(?P<v>\S+)", re.M),
    "seed": re.compile(r"^algo\s*:\s*\S+\s+seed=(?P<v>\d+)", re.M),
    "threads": re.compile(r"^threads\s*:\s*(?P<v>\d+)", re.M),
    "start": re.compile(r"^start\s*:\s*(?P<v>\S+)", re.M),
}
DIAG_KEYS = ("wall_time", "value_loss", "policy_loss", "policy_entropy_loss",
             "actor_grad_norm", "critic_grad_norm", "ratio")


def parse_log(path: Path):
    """Parse one stdout log -> (meta, rows, evals).

    rows: per PPO update {episode, total_num_steps, fps,
    average_episode_rewards}; evals: eval rewards in file order (used only as a
    fallback when metrics.jsonl is unavailable).
    """
    txt = path.read_text(encoding="utf-8", errors="replace")
    meta, target = {}, None
    for key, rgx in HDR_RES.items():
        m = rgx.search(txt)
        if not m:
            continue
        if key == "scen":
            meta["env"] = m.group("env")
            meta["scenario"] = m.group("scen").strip()
        else:
            meta[key] = m.group("v")
    rows = []
    for m in EP_RE.finditer(txt):
        rows.append({
            "episode": int(m.group("ep")),
            "total_num_steps": int(m.group("steps")),
            "fps": float(m.group("fps")),
        })
        target = int(m.group("total"))
    rewards = [float(x) for x in TRAIN_REW_RE.findall(txt)]
    for i, r in enumerate(rewards):
        if i < len(rows):
            rows[i]["average_episode_rewards"] = r
    meta["target_steps"] = target
    evals = [float(x) for x in EVAL_REW_RE.findall(txt)]
    return meta, rows, evals


def load_jsonl(path: Path | None):
    rows = []
    if path is None or not path.exists():
        return rows
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:  # torn last line while a run writes
                continue
    return rows


def find_run_dir(exp, meta):
    env, scen, algo = meta.get("env"), meta.get("scenario"), meta.get("algo")
    if env and scen and algo:
        cand = RESULTS / env / scen / algo / exp / "run1"
        if cand.is_dir():
            return cand
    hits = sorted(RESULTS.glob(f"**/{exp}/run1"))  # few tens of dirs: cheap
    return hits[0] if hits else None


def merge_jsonl(rows, run_dir):
    """Union metrics.jsonl into the log rows by total_num_steps.

    A single step can carry two records (training diagnostics + eval), so they
    are unioned, not overwritten.  Returns {steps: eval_reward}.
    """
    evals = {}
    if not run_dir:
        return evals
    by_step = {}
    for rec in load_jsonl(Path(run_dir) / "metrics.jsonl"):
        step = rec.get("total_num_steps")
        if step is None:
            continue
        by_step.setdefault(int(step), {}).update(rec)
        if "eval_average_episode_rewards" in rec:
            evals[int(step)] = rec["eval_average_episode_rewards"]
    for row in rows:
        rec = by_step.get(row["total_num_steps"], {})
        for k in DIAG_KEYS:
            if k in rec:
                row[k] = rec[k]
        if "average_episode_rewards" in rec:
            row["average_episode_rewards"] = rec["average_episode_rewards"]
    return evals


def fill_missing_from_curves(rows, curve_path: Path):
    """Last-resort backfill (wall_time and diagnostics) from collect_metrics'
    curve CSV when the run dir is not on disk.  Never overwrites log values."""
    if not curve_path.exists():
        return
    by_step = {}
    for r in read_csv(curve_path):
        s = fnum(r.get("total_num_steps"))
        if s is None:
            continue
        by_step[int(s)] = {k: fnum(r.get(k)) for k in DIAG_KEYS}
    for row in rows:
        rec = by_step.get(row["total_num_steps"], {})
        for k, v in rec.items():
            if v is not None and row.get(k) is None:
                row[k] = v


def queue_meta(camp: Path):
    """exp -> queue definition (threads, target, env, scenario, algo, seed)
    from configs/queue_*.txt; also the campaign's *planned* experiment set."""
    out = {}
    for qf in sorted((camp / "configs").glob("queue_*.txt")):
        try:
            lines = qf.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split("|")
            if len(p) < 8:
                continue
            out[p[0]] = {"threads": p[1], "target": p[2], "env": p[4],
                         "scenario": p[5], "algo": p[6], "seed": p[7]}
    return out


def _make_run(exp, rows, meta, evals, tag, source="", run_dir=None, qmeta=None):
    q = (qmeta or {}).get(exp, {})
    walls = [r["wall_time"] for r in rows if r.get("wall_time") is not None]
    return {
        "exp": exp, "tag": tag, "source": source,
        "dir": str(run_dir) if run_dir else None,
        "label": label_for(exp), "short": short_label(exp),
        "n": team_size_of(exp), "seed": meta.get("seed") or seed_of(exp),
        "threads": to_int(meta.get("threads")) or to_int(q.get("threads")),
        "env": meta.get("env") or q.get("env"),
        "scenario": meta.get("scenario") or q.get("scenario"),
        "algo": meta.get("algo") or q.get("algo"),
        "target": meta.get("target_steps") or to_int(q.get("target")),
        "start": meta.get("start"),
        "rows": rows, "evals": evals,
        "t0": min(walls) if walls else None,
        "last_steps": rows[-1]["total_num_steps"] if rows else None,
    }


def load_campaign(camp: Path, tag: str):
    """exp -> run dict, from logs (+metrics.jsonl) where available, else from
    metrics/curves/*.csv.  Logs win: they are fresher than the CSVs."""
    camp = Path(camp).expanduser().resolve()
    runs = {}
    qmeta = queue_meta(camp)
    curve_dir, log_dir = camp / "metrics" / "curves", camp / "logs"

    for p in sorted(curve_dir.glob("*.csv")):
        exp = p.stem
        if exp.startswith(("SMOKE", "METRICS_TEST")):
            continue
        rows = []
        for r in read_csv(p):
            step = fnum(r.get("total_num_steps"))
            if step is None:
                continue
            row = {"episode": fnum(r.get("episode")),
                   "total_num_steps": int(step),
                   "fps": fnum(r.get("fps")),
                   "average_episode_rewards": fnum(r.get("average_episode_rewards"))}
            for k in DIAG_KEYS:
                row[k] = fnum(r.get(k))
            rows.append(row)
        if rows:
            runs[exp] = _make_run(exp, rows, {}, {}, tag, source=f"curves/{p.name}",
                                  qmeta=qmeta)

    best_log = {}
    for lp in sorted(log_dir.glob("*.log")):
        meta, rows, evals = parse_log(lp)
        exp = meta.get("exp") or lp.name.split("_seed")[0]
        if exp.startswith(("SMOKE", "METRICS_TEST")) or not rows:
            continue
        key = (rows[-1]["total_num_steps"], lp.stat().st_mtime)
        cur = best_log.get(exp)
        if cur is None or key > cur[0]:
            best_log[exp] = (key, lp, meta, rows, evals)
    for exp, (_, lp, meta, rows, evals) in best_log.items():
        run_dir = find_run_dir(exp, meta)
        ev = merge_jsonl(rows, run_dir)
        if run_dir is None:
            fill_missing_from_curves(rows, curve_dir / f"{exp}.csv")
        runs[exp] = _make_run(exp, rows, meta, ev, tag, source=lp.name,
                              run_dir=run_dir, qmeta=qmeta)
    return runs


# --------------------------------------------------------------------------
# per-experiment resource sampling (/proc + nvidia-smi; ported from the
# pilot's sweep.sh).  Light: one 1 s window, never touches the runs.
# --------------------------------------------------------------------------
def _proc_snapshot(known):
    pat_exp = re.compile(r"--experiment-name (\S+)")
    pat_title = re.compile(r"^(?:ppo|mappo)-[^-]+-(.+)@[^@]*$")
    page = os.sysconf("SC_PAGE_SIZE")
    agg, pid_exp = defaultdict(lambda: [0, 0, 0]), {}
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            cmd = (Path(f"/proc/{pid}/cmdline").read_bytes()
                   .replace(b"\0", b" ").decode("utf-8", "replace"))
            m = pat_exp.search(cmd) or pat_title.match(cmd.strip())
            if not m:
                continue
            exp = m.group(1)
            if known and exp not in known:
                continue
            st = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            rec = agg[exp]
            rec[0] += 1
            rec[1] += int(st[11]) + int(st[12])          # utime + stime ticks
            rec[2] += int(st[21]) * page                 # RSS bytes
            pid_exp[pid] = exp
        except (OSError, IndexError, ValueError, UnicodeDecodeError):
            continue
    return agg, pid_exp


def _gpu_info():
    """(index -> util %) and (pid -> MiB) from two light nvidia-smi queries."""
    utils, pid_mem = {}, {}
    if not shutil.which("nvidia-smi"):
        return utils, pid_mem
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) == 2:
                utils[int(p[0])] = float(p[1])
    except Exception:  # noqa: BLE001 - nvidia-smi must never break a figure
        pass
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) >= 2:
                try:
                    pid_mem[int(p[0])] = float(p[1])
                except ValueError:
                    continue
    except Exception:  # noqa: BLE001
        pass
    return utils, pid_mem


def _gpu_id_for(exp):
    """GPU index from the experiment's newest log filename (as the campaign's
    other sampler does)."""
    try:
        logs = sorted((LOGS or Path(".")).glob(f"{exp}_seed*.log"),
                      key=lambda p: p.stat().st_mtime)
    except OSError:
        return None
    if not logs:
        return None
    m = re.search(r"gpu(\d+)", logs[-1].name)
    return int(m.group(1)) if m else None


def sample_resources(camp: Path, known):
    """Append one per-experiment sample to metrics/resources.csv.

    Same schema as this campaign's make_report_tables.py sampler (and the
    pilot's sweep.sh), so every row joins cleanly with the rows those tools
    write: timestamp, experiment, n_procs, cpu_pct, rss_gb, gpu_id, gpu_util,
    gpu_vram_mb.  cpu_pct is summed %CPU with 100 = one core.  One 1 s /proc
    window plus two nvidia-smi queries: light, and it never touches the runs.
    """
    a, _ = _proc_snapshot(known)
    t0 = time.time()
    time.sleep(1.0)                       # measure CPU over a window, not a point
    b, pid_exp = _proc_snapshot(known)
    dt = max(time.time() - t0, 1e-6)
    utils, pid_mem = _gpu_info()
    vram = defaultdict(float)
    for pid, exp in pid_exp.items():
        mb = pid_mem.get(int(pid))
        if mb:
            vram[exp] += mb
    path = camp / "metrics" / "resources.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    ts = datetime.now().isoformat(timespec="seconds")
    n = 0
    with path.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "experiment", "n_procs", "cpu_pct",
                        "rss_gb", "gpu_id", "gpu_util", "gpu_vram_mb"])
        for exp in sorted(set(a) | set(b)):
            na, nb = a.get(exp, [0, 0, 0]), b.get(exp, [0, 0, 0])
            cores = max(0.0, (nb[1] - na[1]) / os.sysconf("SC_CLK_TCK") / dt)
            rss = max(na[2], nb[2]) / 1024 ** 3
            gid = _gpu_id_for(exp)
            w.writerow([ts, exp, nb[0] or na[0], round(cores * 100, 1),
                        round(rss, 2),
                        gid if gid is not None else "",
                        utils.get(gid, "") if gid is not None else "",
                        round(vram.get(exp, 0.0))])
            n += 1
    return path, n


def resource_peaks(camp: Path):
    """exp -> {cpu_cores, rss, vram, k} peak over every recorded sample.

    Understands both the request-free 6-column schema this script would create
    on its own and the sweep.sh-style schema (cpu_pct, gpu_vram_mb) used by
    the pilot and by make_report_tables.py.
    """
    peaks = {}
    for r in read_csv(Path(camp) / "metrics" / "resources.csv"):
        exp = r.get("experiment")
        if not exp:
            continue
        if r.get("cpu_cores") is not None:
            cpu = fnum(r.get("cpu_cores"))
            vram = fnum(r.get("vram_mb"))
        else:
            c = fnum(r.get("cpu_pct"))
            cpu = c / 100.0 if c is not None else None
            vram = fnum(r.get("gpu_vram_mb"))
        rss = fnum(r.get("rss_gb"))
        cur = peaks.setdefault(exp, {"cpu": None, "rss": None, "vram": None, "k": 0})
        for key, val in (("cpu", cpu), ("rss", rss), ("vram", vram)):
            if val is not None:
                cur[key] = val if cur[key] is None else max(cur[key], val)
        cur["k"] += 1
    return peaks


# --------------------------------------------------------------------------
# plotting helpers
# --------------------------------------------------------------------------
def save(fig, fname):
    path = FIG / fname
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path.name}  ({path.stat().st_size / 1024:.0f} KB)")


def placeholder(fname, title, msg):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.58, title, ha="center", va="center", fontsize=13,
            fontweight="600", color=INK)
    ax.text(0.5, 0.40, msg, ha="center", va="center", fontsize=10, color=INK2,
            wrap=True)
    save(fig, fname)


def add_end_labels(ax, items, pad_frac=0.055):
    """Direct end-labels at the last point of each series, staggered so nearby
    values do not collide.  (Identity is never colour-alone.)"""
    items = [(x, y, t, c) for (x, y, t, c) in items if x is not None and y is not None]
    if not items:
        return
    ax.margins(x=0.14)
    fig = ax.figure
    fig.canvas.draw()           # realise limits before placing labels
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    dx, gap = (xmax - xmin) * 0.015, (ymax - ymin) * pad_frac
    placed = []
    for x, y, t, c in sorted(items, key=lambda it: -it[1]):
        yy = y
        while any(abs(yy - p) < gap for p in placed):
            yy -= gap
        placed.append(yy)
        ax.text(x + dx, yy, t, fontsize=7.5, color=c, va="center", ha="left",
                clip_on=False)


def label_points(ax, pts, dy_frac=0.035):
    """Direct labels for scatter points: pts = [(x, y, text, colour)].

    Labels sit just above their point, staggered downward when several land at
    the same value; near the left/right edge they grow inward, so a point on
    the axis never clips its own label.
    """
    pts = [(x, y, t, c) for (x, y, t, c) in pts if x is not None and y is not None]
    if not pts:
        return
    fig = ax.figure
    fig.canvas.draw()
    ymin, ymax = ax.get_ylim()
    xmin, xmax = ax.get_xlim()
    gap = (ymax - ymin) * dy_frac
    placed = []
    for x, y, t, c in sorted(pts, key=lambda it: -it[1]):
        yy = y + gap * 0.6
        while any(abs(yy - p) < gap for p in placed):
            yy -= gap
        placed.append(yy)
        ann = ax.annotate(t, xy=(x, y), xytext=(x, yy), textcoords="data",
                          fontsize=7.5, color=c, ha="center", va="bottom")
        # nudge horizontally until the label is inside the axes box
        fig.canvas.draw()
        bb = ann.get_window_extent()
        (bx0, _), (bx1, _) = ax.transData.inverted().transform(
            [(bb.x0, bb.y0), (bb.x1, bb.y1)])
        nudge = xmin - bx0 if bx0 < xmin else (xmax - bx1 if bx1 > xmax else 0.0)
        if nudge:
            ann.set_position((x + nudge, yy))


def _line_display_points(ax):
    out = []
    for ln in ax.get_lines():
        xd = np.asarray(ln.get_xdata(), dtype=float)
        yd = np.asarray(ln.get_ydata(), dtype=float)
        if xd.size == 0 or xd.size != yd.size:
            continue
        out.append(ax.transData.transform(np.column_stack([xd, yd])))
    return out


def smart_legend(ax, handles=None, fontsize=7.5,
                 candidates=("upper right", "upper left", "lower right",
                             "lower left", "center right", "center left")):
    """Place the legend in the candidate corner with the least ink under it.

    Ink = curve samples inside the legend box plus direct labels it would
    cover.  matplotlib's "best" ignores text artists, which is how a legend
    ends up sitting on an end-label it duplicates; this measures both and
    keeps the plot readable without hand-tuning per panel.
    """
    if handles is None:
        handles = ax.get_legend_handles_labels()[0]
    if not handles:
        return None
    try:
        ax.figure.canvas.draw()
    except Exception:  # noqa: BLE001 - never let legend placement fail a figure
        pass
    lines = _line_display_points(ax)
    texts = list(ax.texts)
    best = None
    for loc in candidates:
        leg = ax.legend(handles=handles, loc=loc, fontsize=fontsize)
        try:
            ax.figure.canvas.draw()
            bb = leg.get_window_extent()
            penalty = 0
            for disp in lines:
                inside = ((disp[:, 0] >= bb.x0) & (disp[:, 0] <= bb.x1)
                          & (disp[:, 1] >= bb.y0) & (disp[:, 1] <= bb.y1))
                penalty += int(inside.sum())
            for t in texts:
                try:
                    tb = t.get_window_extent()
                except Exception:  # noqa: BLE001
                    continue
                if bb.overlaps(tb):
                    penalty += 30
            if best is None or penalty < best[0]:
                best = (penalty, loc)
        finally:
            leg.remove()
        if best[0] == 0:
            break
    return ax.legend(handles=handles, loc=best[1], fontsize=fontsize)


def title_with_note(fig, title, note, rect_top=0.93):
    """Big title plus a small data-freshness note under it.

    Spacing is computed in inches above the figure box so the two lines never
    collide no matter how tall the figure is (short single-row figures used to
    overlap when the offsets were fractions).
    """
    h = fig.get_figheight()
    fig.suptitle(title, fontsize=13, fontweight="600", y=1.0 + 0.34 / h)
    if note:
        fig.text(0.5, 1.0 + 0.10 / h, note, ha="center", fontsize=8.5,
                 color=INK2)
    fig.tight_layout(rect=[0, 0, 1, rect_top])


def xfmt(ax, xkey):
    if xkey == "steps":
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_steps(v)))
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


def curve_xy(run, xkey, ykey="average_episode_rewards", scale=1.0):
    xs, ys = [], []
    t0 = run.get("t0")
    for r in run["rows"]:
        y = fnum(r.get(ykey))
        if y is None:
            continue
        if xkey == "steps":
            x = fnum(r.get("total_num_steps"))
        else:
            wt = fnum(r.get("wall_time"))
            x = (wt - t0) / 3600.0 if (wt is not None and t0 is not None) else None
        if x is None:
            continue
        xs.append(x)
        ys.append(y * scale)
    return xs, ys


def early_mean(run, key, k=5):
    vals = [fnum(r.get(key)) for r in run["rows"]]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, 0
    tail = vals[:k]
    return statistics.mean(tail), len(tail)


def latest_fps(run, k=5):
    vals = [fnum(r.get("fps")) for r in run["rows"]]
    vals = [v for v in vals if v is not None and v > 0]
    if not vals:
        return None, 0
    tail = vals[-k:]
    return statistics.median(tail), len(tail)


def progress_str(run):
    last, tgt = run.get("last_steps"), run.get("target")
    if last is None:
        return "no data"
    if tgt:
        return f"{fmt_steps(last)}/{fmt_steps(tgt)} ({100.0 * last / tgt:.0f}%)"
    return f"{fmt_steps(last)} steps"


def campaign_stamp(runs):
    """One string describing how partial the data is, for the suptitles."""
    steps = max((r.get("last_steps") or 0) for r in runs.values()) if runs else 0
    tgt = max((r.get("target") or 0) for r in runs.values()) if runs else 0
    walls = [row.get("wall_time") for r in runs.values() for row in r["rows"]
             if row.get("wall_time")]
    when = (datetime.fromtimestamp(max(walls)).strftime("%Y-%m-%d %H:%M")
            if walls else "n/a")
    if tgt:
        return (f"partial data: longest run at {fmt_steps(steps)} of "
                f"{fmt_steps(tgt)} steps ({100.0 * steps / tgt:.1f}%), "
                f"data through {when}")
    return f"data through {when}"


def panel_groups(runs):
    """Split runs into the per-family panels used by the learning curves."""
    titles = {
        ("scaling", "noweapon", "multi"): "Scaling family - NoWeapon N-v-N (generated configs)",
        ("scaling", "shoot", "multi"): "Scaling family - ShootMissile N-v-N",
        ("official", "noweapon", "1v1"): "Official 1v1 - NoWeapon",
        ("official", "shoot", "1v1"): "Official 1v1 - ShootMissile",
        ("official", "noweapon", "multi"): "Official baselines - MultipleCombat NoWeapon",
        ("official", "shoot", "multi"): "Official baselines - MultipleCombat ShootMissile",
    }
    order = list(titles) + [("other", "", "")]
    groups = {}
    for r in runs.values():
        fam, weapon = family_of(r["exp"])
        if fam == "other":
            groups.setdefault(("other", "", ""), []).append(r)
        else:
            size = "1v1" if r.get("n") == 1 else "multi"
            groups.setdefault((fam, weapon, size), []).append(r)
    out = []
    for key in order:
        if key in groups:
            series = sorted(groups[key], key=lambda r: (r.get("n") or 99, r["exp"]))
            out.append((titles.get(key, "Other experiments"), series))
    return out


def compare_matches(cruns, formal_series, max_per_variant=2):
    """Compare-campaign runs that pair with any formal series (same family
    identity, seed ignored), capped per variant so a multi-seed compare
    campaign does not bury the formal curves, sorted for stable legends."""
    wanted = {variant_of(r["exp"]) for r in formal_series}
    out, seen = [], defaultdict(int)
    for r in sorted(cruns.values(), key=lambda r: r["exp"]):
        v = variant_of(r["exp"])
        if v not in wanted:
            continue
        seen[v] += 1
        if seen[v] <= max_per_variant:
            out.append(r)
    return out


def add_compare_series(ax, handles, cruns, formal_series, xkey, scale=1.0):
    for cr in compare_matches(cruns, formal_series):
        xs, ys = curve_xy(cr, xkey, scale=scale)
        if not xs:
            continue
        ax.plot(xs, ys, color=CMP_COLOUR, lw=1.4, ls=CMP_LS, marker=CMP_MARK,
                ms=4, alpha=0.9, markevery=max(1, len(xs) // 12))
        handles.append(Line2D([], [], color=CMP_COLOUR, lw=1.4, ls=CMP_LS,
                              marker=CMP_MARK, ms=4,
                              label=f"[{cr['tag']}] {cr['label']}"))


# --------------------------------------------------------------------------
# figure 1 + 2: learning curves vs env steps / wall-clock hours
# --------------------------------------------------------------------------
def fig_learning_curves(runs, compare, xkey, fname, xlabel, title):
    groups = panel_groups(runs)
    if not groups:
        placeholder(fname, title, "no PPO update has been logged yet")
        return
    n = len(groups)
    cols = min(3, n)
    rows_n = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows_n, cols, figsize=(5.9 * cols, 4.3 * rows_n),
                             squeeze=False)
    for ax, (gtitle, series) in zip(axes.ravel(), groups):
        handles, ends = [], []
        for i, run in enumerate(series[:6]):
            xs, ys = curve_xy(run, xkey)
            if not xs:
                continue
            c, ls, mk = series_style(i)
            ax.plot(xs, ys, color=c, lw=2, ls=ls, marker=mk, ms=4,
                    markevery=max(1, len(xs) // 12))
            handles.append(Line2D([], [], color=c, lw=2, ls=ls, marker=mk,
                                  ms=4, label=f"{run['label']} - {progress_str(run)}"))
            ends.append((xs[-1], ys[-1], run["short"], c))
        if len(series) > 6:
            ax.text(0.02, 0.02, f"+{len(series) - 6} more series not shown",
                    transform=ax.transAxes, fontsize=7.5, color=INK2)
        for label, cruns in compare:
            add_compare_series(ax, handles, cruns, series, xkey)
        ax.set_title(gtitle, fontsize=10.5)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("average episode reward")
        xfmt(ax, xkey)
        add_end_labels(ax, ends)
        if handles:
            smart_legend(ax, handles)
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    note = campaign_stamp(runs)
    if compare:
        note += ("   |   overlays dotted = " +
                 ", ".join(f"[{lab}]" for lab, _ in compare))
    title_with_note(fig, title, note, rect_top=0.94)
    save(fig, fname)


# --------------------------------------------------------------------------
# figure 3: reward per enemy vs steps / wall-clock / N
# --------------------------------------------------------------------------
def fig_scaling_reward_normalized(runs, compare, suffix=""):
    fname = f"formal_scaling_reward_normalized{suffix}.png"
    family = [r for r in runs.values()
              if family_of(r["exp"]) == ("scaling", "noweapon")]
    if len(family) < 2:  # fall back to every MultipleCombat N-v-N run
        family = [r for r in runs.values()
                  if family_of(r["exp"])[0] in ("scaling", "official") and (r.get("n") or 0) >= 2]
    if not family:
        placeholder(fname, "Reward per enemy (N-normalised)",
                    "no MultipleCombat N-v-N run has logged an update yet")
        return
    family.sort(key=lambda r: (r["n"] or 99, r["exp"]))

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    ax = axes[0]
    handles, ends = [], []
    for i, run in enumerate(family[:6]):
        xs, ys = curve_xy(run, "steps", scale=1.0 / run["n"])
        if not xs:
            continue
        c, ls, mk = series_style(i)
        ax.plot(xs, ys, color=c, lw=2, ls=ls, marker=mk, ms=4,
                markevery=max(1, len(xs) // 12))
        handles.append(Line2D([], [], color=c, lw=2, ls=ls, marker=mk, ms=4,
                              label=f"{run['label']} - {progress_str(run)}"))
        ends.append((xs[-1], ys[-1], run["short"], c))
    for label, cruns in compare:
        for cr in compare_matches(cruns, family):
            xs, ys = curve_xy(cr, "steps", scale=1.0 / cr["n"])
            if not xs:
                continue
            ax.plot(xs, ys, color=CMP_COLOUR, lw=1.4, ls=CMP_LS, marker=CMP_MARK,
                    ms=4, alpha=0.9, markevery=max(1, len(xs) // 12))
            handles.append(Line2D([], [], color=CMP_COLOUR, lw=1.4, ls=CMP_LS,
                                  marker=CMP_MARK, ms=4,
                                  label=f"[{cr['tag']}] {cr['label']}"))
    ax.axhline(0, color=MUTED, lw=1, ls=":")
    ax.set_xlabel("environment steps (vectorised)")
    ax.set_ylabel("average episode reward / N")
    ax.set_title("Reward per enemy vs steps", fontsize=10.5)
    xfmt(ax, "steps")
    add_end_labels(ax, ends)
    if handles:
        smart_legend(ax, handles)

    ax = axes[1]
    handles, ends = [], []
    for i, run in enumerate(family[:6]):
        xs, ys = curve_xy(run, "hours", scale=1.0 / run["n"])
        if not xs:
            continue
        c, ls, mk = series_style(i)
        ax.plot(xs, ys, color=c, lw=2, ls=ls, marker=mk, ms=4,
                markevery=max(1, len(xs) // 12))
        handles.append(Line2D([], [], color=c, lw=2, ls=ls, marker=mk, ms=4,
                              label=run["label"]))
        ends.append((xs[-1], ys[-1], run["short"], c))
    for label, cruns in compare:
        for cr in compare_matches(cruns, family):
            xs, ys = curve_xy(cr, "hours", scale=1.0 / cr["n"])
            if not xs:
                continue
            ax.plot(xs, ys, color=CMP_COLOUR, lw=1.4, ls=CMP_LS, marker=CMP_MARK,
                    ms=4, alpha=0.9, markevery=max(1, len(xs) // 12))
            handles.append(Line2D([], [], color=CMP_COLOUR, lw=1.4, ls=CMP_LS,
                                  marker=CMP_MARK, ms=4,
                                  label=f"[{cr['tag']}] {cr['label']}"))
    ax.axhline(0, color=MUTED, lw=1, ls=":")
    ax.set_xlabel("wall-clock since each run's start (hours)")
    ax.set_ylabel("average episode reward / N")
    ax.set_title("Same data vs wall-clock (compute-normalised)", fontsize=10.5)
    xfmt(ax, "hours")
    add_end_labels(ax, ends)
    if handles:
        smart_legend(ax, handles)

    # cross-section: reward per enemy against N at the latest common step.
    # Matched, never interpolated: each point shows the running step it was
    # actually measured at (partial runs have very different lengths).
    ax = axes[2]
    common = min(r["last_steps"] for r in family if r.get("last_steps"))
    pts, ends = [], []
    dupe = defaultdict(int)
    for i, run in enumerate(family[:6]):
        best = None
        for row in run["rows"]:
            if row["total_num_steps"] <= common and row.get("average_episode_rewards") is not None:
                best = row
        if best is None or not run["n"]:
            continue
        k = dupe[run["n"]]
        dupe[run["n"]] += 1
        x = run["n"] + (k - 0.5) * 0.10
        y = best["average_episode_rewards"] / run["n"]
        c = CAT[family.index(run) % len(CAT)] if i < 6 else INK2
        ax.plot([x], [y], marker="o", ms=7, color=c, ls="none")
        pts.append((x, y, f"{run['short']}\n@{fmt_steps(best['total_num_steps'])}", c))
    for label, cruns in compare:
        cxs, cys = [], []
        for cr in compare_matches(cruns, family):
            if not cr.get("n"):
                continue
            best = None
            for row in cr["rows"]:
                if row["total_num_steps"] <= common and row.get("average_episode_rewards") is not None:
                    best = row
            if best is None:
                continue
            cxs.append(cr["n"])
            cys.append(best["average_episode_rewards"] / cr["n"])
        if cxs:
            ax.plot(cxs, cys, marker=CMP_MARK, ms=7, color=CMP_COLOUR, ls="none")
            ax.plot([], [], ls="none", marker=CMP_MARK, ms=7, color=CMP_COLOUR,
                    label=f"[{label}] matched points")
    ax.axhline(0, color=MUTED, lw=1, ls=":")
    ax.set_xlabel("team size N")
    ax.set_ylabel("average episode reward / N")
    ax.set_title(f"Reward per enemy vs N (matched at <= {fmt_steps(common)} steps)", fontsize=10.5)
    ax.set_xticks(sorted({r["n"] for r in family if r.get("n")}))
    label_points(ax, pts)
    if compare:
        smart_legend(ax)
    title_with_note(fig, "N-v-N scaling, reward normalised by team size "
                    "(formal 6M campaign, NoWeapon family)",
                    campaign_stamp(runs), rect_top=0.92)
    save(fig, fname)


# --------------------------------------------------------------------------
# figure 4: throughput vs number of agents
# --------------------------------------------------------------------------
def load_throughput_history(camp: Path):
    out = []
    for r in read_csv(camp / "metrics" / "throughput_history.csv"):
        ts = " ".join((r.get("timestamp_local") or "").split()[:2])
        try:
            t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        out.append((t, fnum(r.get("aggregate_fps"))))
    return out


def fig_throughput(runs, compare, camp, suffix=""):
    fname = f"formal_throughput_vs_agents{suffix}.png"
    pts = []
    for r in runs.values():
        fps, k = latest_fps(r)
        if fps is None or not r.get("n"):
            continue
        pts.append((r, fps, k))
    if not pts:
        placeholder(fname, "Throughput vs team size",
                    "no FPS line has been logged yet")
        return
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.4))
    plans = [
        (axes[0][0], lambda r, f: f, "env-steps/s (as reported by the run)",
         "Throughput per job vs team size"),
        (axes[0][1], lambda r, f: (f / r["threads"]) if r.get("threads") else None,
         "env-steps/s per rollout thread",
         "Per-thread throughput (threads were sized to cost)"),
        (axes[1][0], lambda r, f: f / (2 * r["n"]), "env-steps/s per aircraft",
         "Per-aircraft throughput (cost of scaling)"),
    ]
    for ax, fn, ylab, title in plans:
        pts_xy = [(r, fn(r, f)) for r, f, _ in pts]
        pts_xy = [(r, y) for r, y in pts_xy if y is not None]
        ax.plot([2 * r["n"] for r, _ in pts_xy], [y for _, y in pts_xy],
                ls="none", marker="o", ms=7, color=CAT[0])
        handles = []
        for label, cruns in compare:
            cxs, cys = [], []
            for r in cruns.values():
                fps, _ = latest_fps(r)
                if fps is None or not r.get("n"):
                    continue
                y = fn(r, fps)
                if y is None:
                    continue
                cxs.append(2 * r["n"])
                cys.append(y)
            if cxs:
                ax.plot(cxs, cys, ls="none", marker=CMP_MARK, ms=7,
                        color=CMP_COLOUR)
                handles.append(Line2D([], [], ls="none", marker=CMP_MARK, ms=7,
                                      color=CMP_COLOUR, label=f"[{label}]"))
        ax.set_xlabel("total agents (2N)")
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=10.5)
        ax.set_xticks(sorted({2 * r["n"] for r, _ in pts_xy}))
        label_points(ax, [(2 * r["n"], y, r["short"], INK2) for r, y in pts_xy])
        if handles:
            handles = [Line2D([], [], ls="none", marker="o", ms=7,
                              color=CAT[0], label="formal (live)")] + handles
            smart_legend(ax, handles, fontsize=8)

    ax = axes[1][1]
    hist = load_throughput_history(camp)
    if hist:
        # numeric x (hours since the first sample) with hand-formatted clock
        # labels: datetime x-axes go through matplotlib's timezone machinery,
        # which this box shifts by +8 h, leaving the ticks off the data
        t0 = hist[0][0]
        xs = [(t - t0).total_seconds() / 3600.0 for t, _ in hist]
        ys = [v for _, v in hist]
        fmt = "%m-%d %H:%M" if (xs and xs[-1] > 20) else "%H:%M"
        ax.plot(xs, ys, color=CAT[0], lw=2, marker="o", ms=5)
        ax.set_xlabel("hours since watch start (labels = local clock)")
        ax.set_ylabel("aggregate env-steps/s across live jobs")
        ax.set_title("Campaign aggregate throughput (watch_f6m.py history)",
                     fontsize=10.5)
        ax.xaxis.set_major_formatter(FuncFormatter(
            lambda v, _: (t0 + timedelta(hours=v)).strftime(fmt)))
    else:
        # fallback: per-run FPS against hours since each run started
        for i, r in enumerate(sorted(runs.values(), key=lambda x: (x.get("n") or 99))):
            xs, ys = curve_xy(r, "hours", ykey="fps")
            if not xs:
                continue
            c, ls, mk = series_style(i)
            ax.plot(xs, ys, color=c, lw=1.6, ls=ls, marker=mk, ms=4,
                    label=r["short"])
        ax.set_xlabel("wall-clock since run start (hours)")
        ax.set_ylabel("env-steps/s")
        ax.set_title("Per-run throughput over wall-clock", fontsize=10.5)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=7.5, loc="best")
    note = ("FPS = median of each run's last <=5 reported FPS lines; "
            "one FPS line = one PPO update.  " + campaign_stamp(runs))
    title_with_note(fig, "Throughput vs number of agents (formal 6M campaign)",
                    note, rect_top=0.94)
    save(fig, fname)


# --------------------------------------------------------------------------
# figure 5: CPU / RAM / VRAM vs N
# --------------------------------------------------------------------------
def fig_resource_scaling(runs, compare, camp, suffix=""):
    fname = f"formal_resource_scaling{suffix}.png"
    peaks = resource_peaks(camp)
    pts = []
    for exp, p in sorted(peaks.items()):
        n = team_size_of(exp)
        if n is None or (p["cpu"] is None and p["rss"] is None and p["vram"] is None):
            continue
        pts.append((n, p, exp))
    if not pts:
        placeholder(fname, "Resource demand vs team size",
                    "no per-experiment resource sample recorded yet "
                    "(re-run without --no-sample to take one)")
        return
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
    panels = [("cpu", "CPU cores per job", "CPU demand vs team size"),
              ("rss", "process RSS (GB)", "RAM demand vs team size"),
              ("vram", "GPU memory per job (MB)", "VRAM demand vs team size")]
    for ax, (key, ylab, title) in zip(axes, panels):
        by_n = defaultdict(list)
        for n, p, exp in pts:
            v = p.get(key)
            if v is not None:
                by_n[n].append((v, exp, p))
        pos = []
        for n in sorted(by_n):
            group = sorted(by_n[n], key=lambda t: (-t[0], t[1]))
            m = len(group)
            for i, (v, exp, p) in enumerate(group):
                pos.append((n + (i - (m - 1) / 2.0) * 0.10, n, v, exp, m))
        for x, n, v, exp, m in pos:
            ax.plot([x], [v], marker="o", ms=7, color=CAT[0], ls="none")
        # selective direct labels: single/pair runs keep their names, larger
        # same-N clusters (e.g. the five official 1v1 jobs) get one label
        label_pts, cluster = [], {}
        for x, n, v, exp, m in pos:
            if m <= 2:
                label_pts.append((x, v, short_label(exp), INK2))
            elif n not in cluster or v > cluster[n][1]:
                cluster[n] = (x, v, f"{m} jobs at N={n}")
        label_pts += [(x, v, t, INK2) for x, v, t in cluster.values()]
        for label, c_runs in compare:
            cpts = []
            for exp, p in resource_peaks(compare_dir(label)).items():
                n = team_size_of(exp)
                v = p.get(key)
                if n is None or v is None:
                    continue
                cpts.append((n, v))
            for n, v in cpts:
                ax.plot([n], [v], marker=CMP_MARK, ms=7, color=CMP_COLOUR, ls="none")
            if cpts:
                ax.plot([], [], ls="none", marker=CMP_MARK, ms=7,
                        color=CMP_COLOUR, label=f"[{label}]")
        if key == "cpu":
            ax.text(0.02, 0.97, f"host: {os.cpu_count()} logical CPUs",
                    transform=ax.transAxes, fontsize=7.5, color=INK2,
                    ha="left", va="top")
        ax.set_xlabel("team size N")
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=10.5)
        ax.set_xticks(sorted({n for n, _, _ in pts}))
        label_points(ax, label_pts)
        if compare:
            smart_legend(ax, fontsize=8)
    note = ("peaks over every recorded /proc + nvidia-smi sample (VRAM = sum "
            "of each job's processes' GPU memory); low-N clusters are "
            "labelled once.  " + campaign_stamp(runs))
    title_with_note(fig, "Per-job resource demand vs team size (formal 6M campaign)",
                    note, rect_top=0.92)
    save(fig, fname)


def compare_dir(label):
    """Filled in by main() so figure 5 can reach the compared campaign's
    metrics dir without hardcoding any path."""
    return COMPARE_DIRS.get(label, Path("/nonexistent"))


COMPARE_DIRS = {}


# --------------------------------------------------------------------------
# figure 6: critic scaling
# --------------------------------------------------------------------------
def critic_param_count(share_dim):
    """Total PPOCritic parameters as a function of the centralised input dim.

    Closed form = 128 * share_dim + 150145, verified against a live build of
    algorithms/mappo/PPOCritic on this box at share_dim in {108, 234, 630, 2460}
    (and against the pilot's measured critic_scaling.json probe, to the unit).
    The 128 * D term is the first Linear layer; the constant is the rest of the
    MLP + GRU + LayerNorms + value head.
    """
    return 128 * share_dim + 150145


def fig_critic_scaling(runs, compare, camp, suffix=""):
    fname = f"formal_critic_scaling{suffix}.png"
    fam = [r for r in runs.values()
           if family_of(r["exp"])[0] in ("scaling", "official") and (r.get("n") or 0) >= 2]
    if not fam:
        placeholder(fname, "Critic scaling",
                    "no MultipleCombat run with an N-v-N name yet")
        return
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.2))
    ns = sorted({r["n"] for r in fam})
    share = [24 * n * n + 6 * n for n in ns]

    ax = axes[0][0]
    ax.plot(ns, share, color=CAT[0], lw=2, marker="o", ms=6)
    label_points(ax, [(n, s, fmt_num(s), INK2) for n, s in zip(ns, share)])
    ax.set_xlabel("team size N")
    ax.set_ylabel("dimension")
    ax.set_title("Centralised critic input dim = 24N$^2$ + 6N", fontsize=10.5)
    ax.set_xticks(ns)

    ax = axes[0][1]
    params = [critic_param_count(s) for s in share]
    ax.plot(ns, params, color=CAT[0], lw=2, marker="o", ms=6)
    label_points(ax, [(n, p, fmt_num(p), INK2) for n, p in zip(ns, params)])
    probes = []
    for src_camp in [camp] + [compare_dir(lab) for lab, _ in compare]:
        p = Path(src_camp) / "metrics" / "critic_scaling.json"
        if p.exists():
            try:
                with p.open() as fh:
                    probes += json.load(fh).get("measured", [])
            except (OSError, ValueError, AttributeError):
                pass
    probes = [m for m in probes
              if isinstance(m, dict) and "team_size" in m and "critic_params" in m]
    if probes:
        xs = sorted({m["team_size"] for m in probes if m["team_size"] in ns})
        ys = [next(m["critic_params"] for m in probes if m["team_size"] == n) for n in xs]
        ax.plot(xs, ys, ls="none", marker=CMP_MARK, ms=8, color=CAT[1],
                label="measured probe")
        smart_legend(ax, fontsize=8)
    ax.set_xlabel("team size N")
    ax.set_ylabel("parameters")
    ax.set_title("Critic parameters (measured build: 128D + 150145)", fontsize=10.5)
    ax.set_xticks(ns)

    for ax, scale, title in ((axes[1][0], 1.0, "Critic grad norm vs N (first 5 updates)"),
                             (axes[1][1], None, "Critic grad norm / N vs N (reward-scale removed)")):
        pts = []
        dupe = defaultdict(int)
        for r in sorted(fam, key=lambda x: (x["n"], x["exp"])):
            mean, k = early_mean(r, "critic_grad_norm", k=5)
            if mean is None:
                continue
            y = mean if scale == 1.0 else mean / r["n"]
            i = dupe[r["n"]]
            dupe[r["n"]] += 1
            x = r["n"] + (i - 0.5) * 0.10
            ax.plot([x], [y], marker="o", ms=7, color=CAT[0], ls="none")
            pts.append((x, y, f"{r['short']} (k={k})", INK2))
        for label, cruns in compare:
            cpts = []
            for r in cruns.values():
                if family_of(r["exp"])[0] not in ("scaling", "official") or (r.get("n") or 0) < 2:
                    continue
                mean, k = early_mean(r, "critic_grad_norm", k=5)
                if mean is None:
                    continue
                cpts.append((r["n"], mean if scale == 1.0 else mean / r["n"]))
            for x, y in cpts:
                ax.plot([x], [y], marker=CMP_MARK, ms=7, color=CMP_COLOUR, ls="none")
            if cpts:
                ax.plot([], [], ls="none", marker=CMP_MARK, ms=7,
                        color=CMP_COLOUR, label=f"[{label}]")
        ax.set_xlabel("team size N")
        ax.set_ylabel("critic grad norm" if scale == 1.0 else "critic grad norm / N")
        ax.set_title(title, fontsize=10.5)
        ax.set_xticks(ns)
        label_points(ax, pts)
        if compare:
            smart_legend(ax, fontsize=8)

    title_with_note(fig, "Centralised critic scaling with team size "
                    "(formal 6M campaign, MultipleCombat NoWeapon family)",
                    "grad norms are means over the first 5 logged updates per "
                    "run (k annotated).  " + campaign_stamp(runs), rect_top=0.94)
    save(fig, fname)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--campaign", default=os.environ.get("FIG_CAMPAIGN", str(CAMP)),
                    help="campaign root (default: this file's parent dir)")
    ap.add_argument("--repo", default=os.environ.get("FIG_REPO", ""),
                    help="repo root holding scripts/results (default: campaign/../..)")
    ap.add_argument("--compare", action="append", default=None, metavar="PATH[:LABEL]",
                    help="second campaign to overlay (repeatable; env: FIG_COMPARE)")
    ap.add_argument("--suffix", default=None,
                    help="filename suffix (default: empty, or _with_<label>)")
    ap.add_argument("--no-sample", action="store_true",
                    help="skip the 1 s per-experiment resource sample")
    args = ap.parse_args(argv)

    compares = args.compare
    if compares is None:
        env = os.environ.get("FIG_COMPARE")
        compares = [env] if env else []
    configure(Path(args.campaign), Path(args.repo) if args.repo else None)

    print(f"campaign : {CAMP}")
    print(f"repo     : {CAMP.parents[1] if not args.repo else args.repo}")
    runs = load_campaign(CAMP, tag=CAMP.name)
    print(f"loaded {len(runs)} experiments with at least one logged update")
    for r in sorted(runs.values(), key=lambda x: (x.get("n") or 99, x["exp"])):
        print(f"  {r['exp']:42s} N={str(r['n']):>3s} seed={r['seed']:<3s} "
              f"steps={fmt_steps(r['last_steps']):>6s} fps={fmt_num(latest_fps(r)[0]):>6s} "
              f"threads={r['threads']} source={r['source']}")

    cmp_runs = []
    for spec in compares:
        if ":" in spec:
            path, label = spec.rsplit(":", 1)
        else:
            path, label = spec, None
        cpath = Path(path).expanduser().resolve()
        label = label or cpath.name
        cruns = load_campaign(cpath, tag=label)
        cmp_runs.append((label, cruns))
        COMPARE_DIRS[label] = cpath
        print(f"compare  : {cpath}  ({len(cruns)} experiments, label '{label}')")

    suffix = args.suffix if args.suffix is not None else (
        "_with_" + "_".join(lab for lab, _ in cmp_runs) if cmp_runs else "")

    if not args.no_sample:
        known = set(runs) | set(queue_meta(CAMP))
        path, n = sample_resources(CAMP, known)
        print(f"resource sample: {n} experiments -> {path}")

    jobs = [
        ("learning curves vs steps",
         lambda: fig_learning_curves(runs, cmp_runs, "steps",
                                     f"formal_learning_curves_steps{suffix}.png",
                                     "environment steps (vectorised)",
                                     "Learning curves: reward vs environment steps")),
        ("learning curves vs wall-clock",
         lambda: fig_learning_curves(runs, cmp_runs, "hours",
                                     f"formal_learning_curves_walltime{suffix}.png",
                                     "wall-clock since each run's start (hours)",
                                     "Learning curves: reward vs wall-clock (compute-normalised view)")),
        ("normalised reward scaling",
         lambda: fig_scaling_reward_normalized(runs, cmp_runs, suffix)),
        ("throughput vs agents",
         lambda: fig_throughput(runs, cmp_runs, CAMP, suffix)),
        ("resource scaling",
         lambda: fig_resource_scaling(runs, cmp_runs, CAMP, suffix)),
        ("critic scaling",
         lambda: fig_critic_scaling(runs, cmp_runs, CAMP, suffix)),
    ]
    for name, job in jobs:
        try:
            job()
        except Exception:  # noqa: BLE001 - one broken figure must not stop the rest
            traceback.print_exc()
            fname = {
                "learning curves vs steps": f"formal_learning_curves_steps{suffix}.png",
                "learning curves vs wall-clock": f"formal_learning_curves_walltime{suffix}.png",
                "normalised reward scaling": f"formal_scaling_reward_normalized{suffix}.png",
                "throughput vs agents": f"formal_throughput_vs_agents{suffix}.png",
                "resource scaling": f"formal_resource_scaling{suffix}.png",
                "critic scaling": f"formal_critic_scaling{suffix}.png",
            }[name]
            placeholder(fname, f"{name}: render error",
                        "see the traceback on stdout; the figure will reappear "
                        "once the underlying data issue is fixed")
    print(f"\nfigures in {FIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
