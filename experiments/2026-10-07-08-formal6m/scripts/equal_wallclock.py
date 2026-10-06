#!/usr/bin/env python
"""Equal-wall-clock comparison across team scales (N in {2,3,5,10}).

For every discovered campaign run this reports the training episode reward at
the shared wall-clock budgets 1h/3h/6h/12h/24h, so scales can be compared at
equal real time (the resource the whole campaign competes for) instead of at
equal sample counts. Elapsed time comes from each run's own `wall_time` field
(absolute epoch float) minus that run's FIRST timestamp; the first timestamp is
the minimum wall_time over all rows of its metrics.jsonl.

Cells a run has not reached yet are marked `pending` -- nothing is extrapolated
or copied from the last known point. The campaign runs live for ~24h, so re-run
this script at any time and the pending cells fill in as training progresses.

Method
------
* x-axis: elapsed hours = (wall_time - run's first wall_time) / 3600, from the
  per-run metrics.jsonl TRAINING rows (`average_episode_rewards`).
* value at budget T: linear interpolation between the two update measurements
  that bracket T (`--method first-crossing` uses the first measurement at/after
  T instead). The bracket (in elapsed hours) is recorded in `bracket@T`.
* `status@T` records what produced each number:
  exact | interp | cross | pending | before-data | nan-gap.
  `pending` = no measurement at/after T exists yet in metrics.jsonl.
* reward_per_enemy = reward / N, which removes the PostureReward
  sum-over-enemies factor (exact for the NoWeapon family).
* per-scale means aggregate runs (seeds) sharing the same variant and N that
  have a value at that budget; the number of contributing runs is shown.
* Cross-scale caveat: each scale runs with a different n_rollout_threads (the
  campaign sized them to the measured cost), so the wall-clock axis embeds that
  scheduling choice -- compare it side by side with equal_sample.py.

Discovery is data-driven: runs are found via this campaign's logs (one entry
per experiment, newest log wins) plus the configs/queue_*.txt files, so
queued-but-not-started runs appear as pending rows instead of silently
vanishing. Run outputs are located under <repo>/scripts/results/<...>/<exp>/run1.

Campaign root is derived from THIS file's location (`parents[1]`), so the copy
inside a campaign's scripts/ always targets that campaign. For cross-campaign
comparison pass `--root <other campaign dir>` or set LAG_CAMPAIGN_ROOT; outputs
are still written under THIS campaign's metrics/ (or --out-dir), never under
the override root, so a comparison run cannot write into another campaign.

Usage
-----
  python equal_wallclock.py                       # 1h..24h budgets, live data
  python equal_wallclock.py --hours 0.1 0.25 0.5  # tighter budgets
  python equal_wallclock.py --method first-crossing
  python equal_wallclock.py --root ../../2026-10-04-night   # pilot reference
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# campaign root: derived from this file, never hardcoded
CAMP = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = CAMP / "metrics"

DEFAULT_HOURS = [1.0, 3.0, 6.0, 12.0, 24.0]
ACTIVE_MIN = 15.0  # metrics.jsonl touched within N minutes => run still writing
OK_STATUS = {"exact", "interp", "cross"}  # statuses that carry a real value
PRIMARY_VARIANTS = {"noweapon", "scaling_noweapon"}  # the N-scaling family

X_MODE = "hours"

LOG_RE = re.compile(r"^(?P<exp>.+)_seed(?P<seed>\d+)_gpu(?P<gpu>\d+)_\d{8}_\d{6}\.log$")
SCALE_RE = re.compile(r"(\d+)v\d+")
SEED_RE = re.compile(r"(?:_s\d+[a-z]?|_seed\d+)$")

HEADER_PATTERNS = {
    "env_scen": re.compile(r"^env/scen\s*:\s*(?P<env>\S+)\s*/\s*(?P<scen>.+?)\s*$", re.M),
    "algo": re.compile(r"^algo\s*:\s*(?P<algo>\S+)\s+seed=(?P<seed>\d+)", re.M),
    "gpu": re.compile(r"^gpu\s*:\s*(?P<gpu>\d+)", re.M),
    "threads": re.compile(
        r"^threads\s*:\s*(?P<thr>\d+)\s+num_env_steps=(?P<steps>[\d.eE+]+)", re.M
    ),
    "start": re.compile(r"^start\s*:\s*(?P<t>\S+)", re.M),
}


def fmt_x(x: float) -> str:
    """Format an x-axis value for the bracket column (elapsed hours here)."""
    return f"{x:.3f}"


def budget_label(budget: float) -> str:
    return f"{budget:g}h"


def classify(exp: str):
    """Experiment name -> (team size N, variant key).  '10v10' -> 10.

    The variant key is the name with the scale token and any seed suffix
    removed: f6m_10v10_noweapon_s0 -> 'noweapon';
    f6m_official_2v2_noweapon_s0 -> 'official_noweapon'.  Runs sharing a
    variant + N are the ones whose per-seed rewards may be averaged.
    """
    m = SCALE_RE.search(exp)
    if not m:
        return None, exp
    n = int(m.group(1))
    v = exp[: m.start()] + "_" + exp[m.end():]
    v = SEED_RE.sub("", v)
    if v.startswith("f6m_"):
        v = v[len("f6m_"):]
    v = re.sub(r"_+", "_", v).strip("_")
    return n, v


def discover_logs(root: Path) -> dict:
    """experiment -> newest stdout log under <root>/logs (logs bind runs to a campaign)."""
    logs = {}
    logdir = root / "logs"
    if not logdir.is_dir():
        return logs
    for p in sorted(logdir.glob("*.log")):
        m = LOG_RE.match(p.name)
        if not m:
            continue
        exp = m.group("exp")
        prev = logs.get(exp)
        if prev is None or p.stat().st_mtime >= prev.stat().st_mtime:
            logs[exp] = p
    return logs


def log_header(path: Path) -> dict:
    """Parse the run_train.sh header block (env/scen, algo, seed, threads...)."""
    out = {}
    if path is None:
        return out
    with path.open(errors="replace") as fh:
        head = fh.read(8192)  # header is at the top; logs can be huge
    m = HEADER_PATTERNS["env_scen"].search(head)
    if m:
        out["env"], out["scenario"] = m.group("env"), m.group("scen")
    m = HEADER_PATTERNS["algo"].search(head)
    if m:
        out["algo"], out["seed"] = m.group("algo"), int(m.group("seed"))
    m = HEADER_PATTERNS["gpu"].search(head)
    if m:
        out["gpu"] = int(m.group("gpu"))
    m = HEADER_PATTERNS["threads"].search(head)
    if m:
        out["threads"] = int(m.group("thr"))
        try:
            out["steps_target"] = int(float(m.group("steps")))
        except ValueError:
            pass
    m = HEADER_PATTERNS["start"].search(head)
    if m:
        out["start"] = m.group("t")
    return out


def read_queues(root: Path) -> dict:
    """configs/queue_*.txt -> {name: {...}} for queued-but-not-started runs.

    Queue line format: name|n_threads|num_env_steps|time_limit|env|scenario|algo|seed|extra
    """
    planned = {}
    cfg = root / "configs"
    if not cfg.is_dir():
        return planned
    for p in sorted(cfg.glob("queue_*.txt")):
        for line in p.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            f = [x.strip() for x in line.split("|")]
            if len(f) < 8 or not f[0]:
                continue

            def as_int(i):
                try:
                    return int(float(f[i]))
                except (ValueError, IndexError):
                    return None

            planned.setdefault(f[0], {
                "threads": as_int(1), "steps_target": as_int(2),
                "env": f[4] or None, "scenario": f[5] or None,
                "algo": f[6] or None, "seed": as_int(7),
            })
    return planned


def results_root(root: Path) -> Path:
    """<repo>/scripts/results -- where the runner writes run outputs."""
    env = os.environ.get("LAG_RESULTS_DIR")
    if env and Path(env).is_dir():
        return Path(env).resolve()
    for base in (root, CAMP):
        for anc in base.parents:
            if anc.name == "experiments":
                p = anc.parent / "scripts" / "results"
                if p.is_dir():
                    return p
    return root.parents[1] / "scripts" / "results"


def find_run1(results: Path, exp: str):
    hits = sorted(results.glob(f"**/{exp}/run1"))
    for h in hits:
        if (h / "metrics.jsonl").exists():
            return h
    return hits[0] if hits else None


def parse_metrics(run1: Path) -> list:
    rows = []
    with (run1 / "metrics.jsonl").open(errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # live file: the last line may be mid-write
    return rows


def build_curve(rows: list) -> dict:
    """-> {points: [(x, reward)], nan_xs, t0, t1, n_train, max_steps}.

    x is vectorised env steps (X_MODE=steps) or elapsed hours since the run's
    FIRST timestamp (X_MODE=hours).  Eval rows carry no train reward and are
    used only for the wall-clock origin (t0 is min over ALL rows).
    """
    ws = [r["wall_time"] for r in rows if isinstance(r.get("wall_time"), (int, float))]
    t0 = min(ws) if ws else None
    t1 = max(ws) if ws else None
    pts, nan_xs, n_train, max_steps = {}, [], 0, None
    for r in rows:
        if "average_episode_rewards" not in r or "total_num_steps" not in r:
            continue
        y, s, w = r.get("average_episode_rewards"), r.get("total_num_steps"), r.get("wall_time")
        if not isinstance(y, (int, float)) or not isinstance(s, (int, float)):
            continue
        n_train += 1
        max_steps = s if max_steps is None else max(max_steps, s)
        if X_MODE == "steps":
            x = float(s)
        else:
            if t0 is None or not isinstance(w, (int, float)):
                continue
            x = max(0.0, (w - t0) / 3600.0)
        if not math.isfinite(y):
            nan_xs.append(x)
            continue
        pts[x] = float(y)  # later duplicate wins (file is append-only)
    return {"points": sorted(pts.items()), "nan_xs": sorted(nan_xs),
            "t0": t0, "t1": t1, "n_train": n_train, "max_steps": max_steps}


def value_at(points: list, nan_xs: list, xb: float, method: str):
    """(reward, status, bracket) at budget xb. Never extrapolates."""
    if not points:
        return None, "pending", None
    if any(abs(xn - xb) <= 1e-12 for xn in nan_xs):
        return None, "nan-gap", fmt_x(xb)
    if xb < points[0][0] - 1e-12:
        return None, "before-data", None
    for x, y in points:
        if abs(x - xb) <= 1e-12:
            return y, "exact", fmt_x(x)
    lo = hi = None
    for x, y in points:
        if x <= xb:
            lo = (x, y)
        else:
            hi = (x, y)
            break
    if lo is None:
        return None, "before-data", None
    if hi is None:
        return None, "pending", None  # budget not reached yet -- do not fabricate
    if any(lo[0] < xn < hi[0] for xn in nan_xs):
        return None, "nan-gap", f"{fmt_x(lo[0])}..{fmt_x(hi[0])}"
    if method == "first-crossing":
        return hi[1], "cross", fmt_x(hi[0])
    x0, y0 = lo
    x1, y1 = hi
    if x1 == x0:
        return y1, "exact", fmt_x(x0)
    y = y0 + (y1 - y0) * (xb - x0) / (x1 - x0)
    return y, "interp", f"{fmt_x(x0)}..{fmt_x(x1)}"


def iso(ts):
    return None if ts is None else datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def elapsed_h(curve: dict):
    if curve["t0"] is None or curve["t1"] is None:
        return None
    return round((curve["t1"] - curve["t0"]) / 3600.0, 3)


def collect(root: Path, results: Path) -> tuple:
    """Return (records, skipped_names). One record per discovered run."""
    logs = discover_logs(root)
    planned = read_queues(root)
    recs, skipped = [], []
    now = time.time()
    for exp in sorted(set(logs) | set(planned)):
        n, variant = classify(exp)
        if n is None:
            skipped.append(exp)
            continue
        hdr = log_header(logs.get(exp))
        plan = planned.get(exp, {})
        run1 = find_run1(results, exp)
        curve = {"points": [], "nan_xs": [], "t0": None, "t1": None,
                 "n_train": 0, "max_steps": None}
        age, state = None, "not-started"
        if run1 is not None and (run1 / "metrics.jsonl").exists():
            curve = build_curve(parse_metrics(run1))
            age = (now - (run1 / "metrics.jsonl").stat().st_mtime) / 60.0
            target = hdr.get("steps_target", plan.get("steps_target"))
            if curve["max_steps"] is not None and target and curve["max_steps"] >= target:
                state = "complete"
            elif age <= ACTIVE_MIN:
                state = "active"
            else:
                state = "idle"
        elif exp in logs:
            state = "starting"
        rec = {
            "experiment": exp, "variant": variant, "team_size": n,
            "scale": f"{n}v{n}",
            "seed": hdr.get("seed", plan.get("seed")),
            "algo": hdr.get("algo") or plan.get("algo"),
            "env": hdr.get("env") or plan.get("env"),
            "scenario": hdr.get("scenario") or plan.get("scenario"),
            "n_rollout_threads": hdr.get("threads", plan.get("threads")),
            "steps_target": hdr.get("steps_target", plan.get("steps_target")),
            "run_state": state, "data_age_min": None if age is None else round(age, 1),
            "curve": curve, "run1": str(run1) if run1 else None,
        }
        recs.append(rec)
    return recs, skipped


def fill_cells(recs: list, budgets: list, method: str) -> None:
    for rec in recs:
        cells = {}
        for b in budgets:
            lab = budget_label(b)
            v, st, br = value_at(rec["curve"]["points"], rec["curve"]["nan_xs"], b, method)
            pv = None if v is None else v / rec["team_size"]
            cells[lab] = (v, pv, st, br)
        rec["cells"] = cells


def write_csv(path: Path, recs: list, budgets: list) -> None:
    labels = [budget_label(b) for b in budgets]
    meta = ["experiment", "variant", "scale", "team_size", "seed", "algo", "env",
            "scenario", "n_rollout_threads", "steps_target", "run_state",
            "data_age_min", "train_rows", "max_steps", "elapsed_h",
            "first_ts", "last_ts"]
    cols = meta + [c for lab in labels for c in
                   (f"reward@{lab}", f"reward_per_enemy@{lab}",
                    f"status@{lab}", f"bracket@{lab}")]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for rec in recs:
            c = rec["curve"]
            row = {
                "experiment": rec["experiment"], "variant": rec["variant"],
                "scale": rec["scale"], "team_size": rec["team_size"],
                "seed": rec["seed"], "algo": rec["algo"], "env": rec["env"],
                "scenario": rec["scenario"],
                "n_rollout_threads": rec["n_rollout_threads"],
                "steps_target": rec["steps_target"], "run_state": rec["run_state"],
                "data_age_min": rec["data_age_min"], "train_rows": c["n_train"],
                "max_steps": c["max_steps"], "elapsed_h": elapsed_h(c),
                "first_ts": iso(c["t0"]), "last_ts": iso(c["t1"]),
            }
            for lab in labels:
                v, pv, st, br = rec["cells"][lab]
                row[f"reward@{lab}"] = None if v is None else round(v, 4)
                row[f"reward_per_enemy@{lab}"] = None if pv is None else round(pv, 4)
                row[f"status@{lab}"] = st
                row[f"bracket@{lab}"] = br
            w.writerow(row)


def fmt_cell(v, pv, star=""):
    return f"{v:+.2f} ({pv:+.2f}){star}"


def render_md(root: Path, results: Path, recs: list, skipped: list, budgets: list,
              method: str) -> str:
    labels = [budget_label(b) for b in budgets]
    lines = []
    lines.append(f"# Equal-wall-clock comparison -- {root.name}")
    lines.append("")
    lines.append(f"- generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- source campaign: `{root}`")
    lines.append(f"- run outputs: `{results}`")
    lines.append(f"- budgets: {', '.join(labels)} of elapsed run time "
                 "(wall_time minus the run's FIRST timestamp)")
    lines.append(f"- value at budget: {'bracketing linear interpolation' if method == 'interp' else 'first measurement at/after the budget'}"
                 "; `pending` = not reached yet, nothing extrapolated")
    lines.append("")

    groups = {}
    for rec in recs:
        groups.setdefault((rec["variant"], rec["team_size"]), []).append(rec)

    def gkey(k):
        v, n = k
        return (0 if v in PRIMARY_VARIANTS else 1, n, v)

    lines.append("## Mean episode reward at equal wall-clock budgets")
    lines.append("")
    lines.append("cells: mean reward (mean reward per enemy) [runs contributing]; "
                 "* = at least one run interpolated between bracketing updates; "
                 "`pending` = no run has reached the budget yet")
    lines.append("")
    hdr = ["variant", "N", "runs", "furthest h"] + labels
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for key in sorted(groups, key=gkey):
        v, n = key
        rs = groups[key]
        n_data = sum(1 for r in rs if r["curve"]["n_train"] > 0)
        furthest = max((elapsed_h(r["curve"]) or 0) for r in rs)
        cells = []
        for lab in labels:
            vals = [r["cells"][lab] for r in rs if r["cells"][lab][0] is not None]
            if not vals:
                cells.append("pending")
            else:
                mv = sum(x[0] for x in vals) / len(vals)
                mp = sum(x[1] for x in vals) / len(vals)
                star = "*" if any(x[2] in ("interp", "cross") for x in vals) else ""
                cells.append(fmt_cell(mv, mp, star) + f" [{len(vals)}]")
        lines.append("| " + " | ".join(
            [v, str(n), f"{n_data}/{len(rs)}",
             f"{furthest:.2f}" if furthest else "-"] + cells) + " |")

    lines.append("")
    lines.append("## Per-run detail")
    lines.append("")
    hdr = ["experiment", "N", "seed", "thr", "rows", "elapsed h", "max steps", "state"] + labels
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for rec in sorted(recs, key=lambda r: (r["team_size"], r["variant"],
                                           str(r["seed"]), r["experiment"])):
        c = rec["curve"]
        cells = []
        for lab in labels:
            v, pv, st, _ = rec["cells"][lab]
            if v is None:
                cells.append(st)
            else:
                cells.append(fmt_cell(v, pv, "*" if st in ("interp", "cross") else ""))
        eh = elapsed_h(c)
        lines.append("| " + " | ".join([
            rec["experiment"], str(rec["team_size"]),
            "-" if rec["seed"] is None else str(rec["seed"]),
            "-" if rec["n_rollout_threads"] is None else str(rec["n_rollout_threads"]),
            str(c["n_train"]),
            "-" if eh is None else f"{eh:.2f}",
            "-" if c["max_steps"] is None else str(c["max_steps"]),
            rec["run_state"],
        ] + cells) + " |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `reward` is `average_episode_rewards` from the metrics.jsonl training rows; "
                 "elapsed time is `wall_time - min(wall_time)`, both from the run's own file, "
                 "so it excludes queueing/startup before the first logged update.")
    lines.append("- A run contributes to a group mean at a budget only once its metrics.jsonl "
                 "reaches that budget; the [k] suffix counts contributing runs.")
    lines.append("- Scales use different n_rollout_threads (sized to measured cost), so "
                 "wall-clock reflects both learning speed and the scheduling choice.")
    lines.append("- Cross-campaign reference: `--root <campaign dir>` (or LAG_CAMPAIGN_ROOT); "
                 "outputs always land in this campaign's metrics/.")
    lines.append("- Raw per-cell statuses/brackets: metrics/equal_wallclock.csv.")
    if skipped:
        lines.append(f"- skipped (no NvN scale token in name): {', '.join(skipped)}")
    not_started = [r["experiment"] for r in recs if r["run_state"] == "not-started"]
    if not_started:
        lines.append(f"- queued, not started yet (all cells pending): {', '.join(not_started)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="campaign dir containing logs/ and configs/ (default: this "
                         "script's campaign, derived from __file__; env: LAG_CAMPAIGN_ROOT)")
    ap.add_argument("--out-dir", default=None, help="output dir (default: <campaign>/metrics)")
    ap.add_argument("--hours", type=float, nargs="+", default=DEFAULT_HOURS,
                    help="budgets in elapsed hours")
    ap.add_argument("--method", choices=["interp", "first-crossing"], default="interp",
                    help="how to take the value at a budget that falls between measurements")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(
        os.environ.get("LAG_CAMPAIGN_ROOT", str(CAMP))).resolve()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    results = results_root(root)

    recs, skipped = collect(root, results)
    if not recs:
        print(f"no campaign runs discovered under {root}")
        return 1
    fill_cells(recs, args.hours, args.method)

    csv_path = out_dir / "equal_wallclock.csv"
    md_path = out_dir / "equal_wallclock.md"
    write_csv(csv_path, recs, args.hours)
    md = render_md(root, results, recs, skipped, args.hours, args.method)
    md_path.write_text(md + "\n")

    n_data = sum(1 for r in recs if r["curve"]["n_train"] > 0)
    print(f"source campaign : {root}")
    print(f"results root    : {results}")
    print(f"runs discovered : {len(recs)} ({n_data} with metrics.jsonl data)")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    print()
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
