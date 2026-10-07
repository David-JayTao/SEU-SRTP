#!/usr/bin/env python
"""Generate docs/formal_repro_scaling_auto_results.md -- the unattended safety net.

WHY THIS EXISTS
---------------
The campaign lives in tmux and survives anything; the agent does not. The
hand-written report (docs/formal_repro_scaling_2026-10-07_08.md) has data
sections that only get filled while an agent is awake. This script removes that
dependency: it renders every number that CAN be rendered from the machine
artefacts into one standalone document, so the complete numeric record exists
even if the hand-written report is never finished.

Invoked by scripts/freeze.sh (which the tmux auto-finalizer runs on a schedule),
and safe to run at any time -- including while training is live and while other
scripts are appending to their outputs:

  * every source is read defensively: a missing / partial / half-written file
    degrades to a placeholder in that one section, never a crash;
  * nothing is hand-typed: every value comes from the files listed in the
    "Sources" section of the output, whose mtimes are recorded alongside;
  * it is read-only with respect to everything except its own output document.

Policy rules honoured (status/plan.md, status/incidents.md):
  * reachable budget = (6e6 // 3000 // n_rollout_threads) * 3000 * threads, so
    a 3-thread lane can never pass 5,994,000 (incident F17; not a failure);
  * status vocabulary is exactly one of: completed_6M | completed_at_ceiling |
    running | time_cutoff | failed | not_applicable;
  * reward/team_size is defined only for the NoWeapon family and is withheld
    for ShootMissile (mirrors equal_sample.py:per_enemy);
  * pilot (2026-10-04) and formal (6M) results are never merged.

Usage:
    python scripts/make_auto_results.py [--campaign-root DIR] [--out FILE]
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
from collections import Counter, OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve()
CAMPAIGN_DEFAULT = SCRIPT.parents[1]          # <campaign>/scripts/this.py
REPO_DEFAULT = SCRIPT.parents[3]              # <repo>

TARGET = 6_000_000          # nominal vectorised env-step budget (--num-env-steps 6e6)
BUFFER = 3000               # runner buffer_size, fixed (runner/share_jsbsim_runner.py)
STALL_MIN = 30.0            # watch_f6m.py stall threshold, minutes

STATUS_VOCAB = ["completed_6M", "completed_at_ceiling", "running",
                "time_cutoff", "failed", "not_applicable"]
ENV_PREFIXES = ("SingleCombat/", "MultipleCombat/", "SingleControl/")
UNDEFINED = "UNDEFINED"

# ------------------------------------------------------------------ utilities

def read_csv_rows(path):
    """Tolerant CSV reader: missing file -> [], torn rows are padded, never raises."""
    rows = []
    try:
        with open(path, newline="", errors="replace") as f:
            r = csv.reader(f)
            header = next(r, None)
            if not header:
                return []
            n = len(header)
            for raw in r:
                if not raw:
                    continue
                if len(raw) < n:
                    raw = raw + [""] * (n - len(raw))
                rows.append(dict(zip(header, raw[:n])))
    except Exception:  # noqa: BLE001 -- partial data must not kill the document
        pass
    return rows


def read_json(path, retries=2, pause=0.3):
    """Tolerant JSON reader with a short retry for torn concurrent writes."""
    for attempt in range(retries + 1):
        try:
            with open(path, errors="replace") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            if attempt < retries:
                time.sleep(pause)
    return None


def read_text(path):
    try:
        return Path(path).read_text(errors="replace")
    except Exception:  # noqa: BLE001
        return None


def parse_dt(s):
    """Parse the date formats used by this campaign; return naive LOCAL time."""
    if not s:
        return None
    s = str(s).strip().rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)  # machine-local
            return dt
        except ValueError:
            continue
    return None


LOG_STAMP_RE = re.compile(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.log$")


def start_from_log_name(log_path):
    if not log_path:
        return None
    m = LOG_STAMP_RE.search(str(log_path))
    if not m:
        return None
    try:
        return datetime(*[int(x) for x in m.groups()])
    except ValueError:
        return None


def mtime_str(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return "missing"


def g(row, *keys, default=""):
    """First non-empty value among alternative column names."""
    for k in keys:
        if not row:
            break
        v = row.get(k)
        if v not in (None, "", "None"):
            return v
    return default


def f_int(v):
    try:
        return f"{int(float(v)):,}"
    except (TypeError, ValueError):
        return "—"


def f_num(v, nd=4):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def f_g(v):
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return "—"


def raw(v):
    return "—" if v in (None, "", "None") else str(v)


def cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def ceiling_of(threads):
    """Reachable env-step ceiling for a lane (incident F17 quantisation)."""
    try:
        t = int(float(threads))
    except (TypeError, ValueError):
        return None
    if t <= 0:
        return None
    return (TARGET // BUFFER // t) * BUFFER * t


def strip_env_prefix(s):
    for p in ENV_PREFIXES:
        if s.startswith(p):
            return s[len(p):]
    return s


def scenario_from_run_dir(run_dir):
    """<results>/<env>/<scale>/<variant>/<scenario>/<algo>/<exp>/run<N> -> scenario, algo."""
    try:
        parts = Path(run_dir).parts
        i = parts.index("results")
        seg = list(parts[i + 1:])
        if len(seg) >= 6 and seg[-1].startswith("run"):
            return "/".join(seg[1:4]), seg[4]
    except (ValueError, IndexError):
        pass
    return "", ""


def team_size_of(text):
    m = re.search(r"(\d+)v\d+", str(text))
    return int(m.group(1)) if m else None


def is_shoot(text):
    return "shoot" in str(text).lower()


def git_info(repo):
    out = {}
    try:
        out["head"] = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
        out["branch"] = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        out.setdefault("head", "unknown")
        out.setdefault("branch", "unknown")
    return out


# ------------------------------------------------------------------ inventory

def build_inventory(camp, now):
    """Merge manifest.csv + metrics/summary.csv + metrics/status.json into lanes."""
    man = OrderedDict()
    for r in read_csv_rows(camp / "manifest.csv"):
        e = r.get("experiment_id")
        if e and e not in man:
            man[e] = r
    summ = OrderedDict()
    for r in read_csv_rows(camp / "metrics" / "summary.csv"):
        e = r.get("experiment")
        if e and e not in summ:
            summ[e] = r
    st = read_json(camp / "metrics" / "status.json") or {}
    st_ts = parse_dt(st.get("timestamp_local")) or parse_dt(st.get("timestamp"))
    jobs = OrderedDict()
    for j in st.get("jobs", []) or []:
        if isinstance(j, dict) and j.get("exp"):
            jobs[j["exp"]] = j

    names, seen = [], set()
    for n in list(jobs) + list(man) + list(summ):
        if n not in seen:
            seen.add(n)
            names.append(n)

    lanes = []
    for name in names:
        j, m, s = jobs.get(name), man.get(name), summ.get(name)

        # ---- run dir / scenario / algorithm / seed / threads
        run_dir = (j or {}).get("run_dir") or (s or {}).get("run_dir") or ""
        scr, algo_d = scenario_from_run_dir(run_dir)
        scenario = strip_env_prefix(g(m, "scenario") or g(s, "scenario") or scr)
        algo = g(m, "algorithm") or g(s, "algo") or algo_d or "?"
        seed = g(m, "seed") or g(s, "seed")
        if seed == "":
            mseed = re.search(r"_s(\d+)$", name)
            seed = mseed.group(1) if mseed else ""
        threads = None
        for cand in ((j or {}).get("threads"), g(m, "n_rollout_threads"),
                     g(s, "n_rollout_threads")):
            try:
                threads = int(float(cand))
                break
            except (TypeError, ValueError):
                continue
        ceil = ceiling_of(threads)

        # ---- steps / liveness flags
        steps = None
        for cand in ((j or {}).get("steps"), g(s, "steps_done"),
                     g(m, "num_env_steps_done")):
            try:
                steps = int(float(cand))
                break
            except (TypeError, ValueError):
                continue
        nan = bool((j or {}).get("nan", False))
        inf = bool((j or {}).get("inf", False))
        trace = bool((j or {}).get("traceback", False))
        age = (j or {}).get("age_min")
        if j is not None:
            done = bool(j.get("done"))
            stalled = bool(j.get("stalled"))
        else:
            last = parse_dt(g(s, "last_log_time") or g(m, "end_time"))
            age = round((now - last).total_seconds() / 60.0, 1) if last else None
            done = steps is not None and ceil is not None and steps >= ceil
            stalled = bool(age is not None and age > STALL_MIN and not done)
            trace = trace or str(g(s, "crashed")).strip().lower() == "true"

        if steps is None and not run_dir and s is None and m is None:
            status, flags = "not_applicable", ["no data found for this lane"]
        elif trace or nan or inf:
            if done:
                status = "completed_6M" if (steps is not None and steps >= TARGET) else "completed_at_ceiling"
                flags = ["health flag raised"]
            else:
                status, flags = "failed", ["crash/health evidence in log or metrics"]
        elif done:
            if steps is not None and steps >= TARGET:
                status, flags = "completed_6M", []
            else:
                status, flags = "completed_at_ceiling", []
        elif stalled:
            status = "time_cutoff"
            flags = [f"no log write for {age:.0f} min" if isinstance(age, (int, float)) else "stopped short"]
        else:
            status, flags = "running", []
        if isinstance(age, (int, float)) and age > STALL_MIN and status == "running":
            flags.append(f"quiet {age:.0f} min")
        if nan:
            flags.append("NaN")
        if inf:
            flags.append("Inf")
        if trace and status != "failed":
            flags.append("Traceback in log")
        if ceil is not None and (j or {}).get("achievable") is not None:
            try:
                if int((j or {}).get("achievable")) != ceil:
                    flags.append("ceilings disagree (computed vs watcher)")
            except (TypeError, ValueError):
                pass

        # ---- timestamps / wall clock
        start = (parse_dt(g(m, "start_time")) or start_from_log_name(g(m, "log_path"))
                 or start_from_log_name((j or {}).get("log")) or g(s, "start"))
        if not isinstance(start, datetime):
            start = parse_dt(g(s, "start"))
        last = None
        if j is not None and st_ts is not None and isinstance(age, (int, float)):
            last = st_ts - timedelta(minutes=float(age))
        if last is None:
            last = parse_dt(g(m, "end_time") or g(s, "last_log_time"))
        wall_h = None
        if isinstance(start, datetime) and isinstance(last, datetime):
            delta = (last - start).total_seconds() / 3600.0
            wall_h = delta if delta >= 0 else None

        # ---- fps
        fps = (j or {}).get("fps")
        if fps in (None, ""):
            fps = g(m, "FPS") or g(s, "fps_last")

        # ---- checkpoint
        ckpt, ckpt_state = g(m, "checkpoint_path"), "manifest"
        if run_dir:
            found = None
            for cand in ("actor_latest.pt", "actor_0.pt"):
                p = Path(run_dir) / cand
                if p.exists():
                    found = p
                    break
            if found is not None:
                ckpt, ckpt_state = str(found), "on disk"
            elif ckpt:
                ckpt_state = "manifest path (file not seen on disk)"
            else:
                ckpt = str(Path(run_dir) / "actor_latest.pt")
                ckpt_state = "not yet written"

        lanes.append(dict(
            exp=name, scenario=scenario or "?", algo=algo, seed=seed,
            threads=threads, ceiling=ceil, steps=steps, status=status,
            fps=fps, wall_h=wall_h, start=start, last=last, flags=flags,
            ckpt=ckpt or "—", ckpt_state=ckpt_state, run_dir=run_dir,
            team_size=team_size_of(scenario or name),
            shoot=is_shoot(scenario or name),
        ))

    def key(l):
        return (1 if "official" in l["exp"] else 0,
                l["team_size"] if l["team_size"] is not None else 99,
                str(l["seed"]), l["exp"])

    lanes.sort(key=key)
    return lanes, st, st_ts


def wall_str(l):
    if l["wall_h"] is None:
        return "—"
    if l["wall_h"] < 1.0:
        return f"{l['wall_h'] * 60:.0f} min"
    return f"{l['wall_h']:.1f} h"


# ------------------------------------------------------------------ sections

def sec_conventions(lanes):
    out = ["## Status vocabulary and budget rule", "",
           "Status is exactly one of six values, derived by this script from the "
           "watcher's own flags (`metrics/status.json`) under the rules below "
           "(the same rules the monitor uses):", "",
           "| status | meaning |", "|---|---|",
           "| `completed_6M` | reached the full 6,000,000 budget. |",
           "| `completed_at_ceiling` | reached its own reachable ceiling, which is below 6,000,000 (3-thread lanes only). |",
           "| `running` | still writing: log updated within the watcher's 30 min stall threshold. |",
           "| `time_cutoff` | stopped short of its ceiling without crash evidence (wall-clock cap, or log quiet > 30 min). |",
           "| `failed` | Traceback / NaN / Inf observed. |",
           "| `not_applicable` | no data found for the lane. |", "",
           "The runner floors `episodes = num_env_steps // 3000 // n_rollout_threads` "
           "(incident F17), so a lane's ACHIEVABLE ceiling is "
           "`(6e6 // 3000 // threads) * 3000 * threads`. Ceilings for the thread "
           "counts that actually occur in this campaign:", "",
           "| threads | episodes | achievable ceiling |", "|---|---|---|"]
    seen = sorted({l["threads"] for l in lanes if l["threads"]}, key=int)
    for t in seen:
        c = ceiling_of(t)
        out.append(f"| {t} | {TARGET // BUFFER // int(t)} | {f_int(c)} |")
    out += ["",
            "`reward_per_enemy` (reward / team_size) is a cross-N-comparable quantity "
            "ONLY for the NoWeapon family (PostureReward sums over each agent's "
            "enemies). It is withheld for the ShootMissile family here.", "",
            "Pilot (2026-10-04) and formal (6M) results are separate series and are "
            "never merged.", ""]
    return out


def sec_sources(camp):
    rows = [
        ("manifest.csv", "campaign root"),
        ("metrics/status.json", "live per-lane state (watcher)"),
        ("metrics/summary.csv", "per-experiment record (collect_metrics)"),
        ("metrics/scaling_table.csv", "scaling + computational table"),
        ("metrics/critic_scaling.json", "representation probe (measured/extrapolated)"),
        ("metrics/equal_sample.csv", "equal-sample checkpoints"),
        ("metrics/equal_wallclock.csv", "equal-wall-clock checkpoints"),
        ("status/incidents.md", "failure/incident list"),
    ]
    out = ["## Sources and freshness", "",
           "Every number in this document is read from these machine artefacts at "
           "generation time. A source newer than a table means the table is a "
           "snapshot, not the live state; the live state is always the inventory "
           "table below (built from `metrics/status.json`).", "",
           "| source | last written |", "|---|---|"]
    for rel, _ in rows:
        out.append(f"| `{rel}` | {mtime_str(camp / rel)} |")
    out.append("")
    return out


def sec_inventory(lanes, st, st_ts):
    out = ["## Experiment inventory (every lane)", ""]
    if st_ts is not None:
        age_min = (datetime.now() - st_ts).total_seconds() / 60.0
        out.append(f"Live view from `metrics/status.json` (timestamp {st_ts:%Y-%m-%d %H:%M:%S}; "
                   f"{age_min:.1f} min before this file was generated).")
        if age_min > STALL_MIN:
            out.append(f"**Warning**: the watcher snapshot is {age_min:.0f} min old — "
                       "the liveness flags below may be stale.")
    else:
        out.append("`metrics/status.json` is unavailable — statuses below are derived "
                   "from `metrics/summary.csv` / `manifest.csv` instead.")
    out += ["", "| experiment | scenario | algo | seed | thr | achievable ceiling | steps | % ceiling | status | FPS | wall-clock | flags |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in lanes:
        pct = "—"
        if l["steps"] is not None and l["ceiling"]:
            pct = f"{100.0 * l['steps'] / l['ceiling']:.1f}%"
        out.append("| `{}` | {} | {} | {} | {} | {} | {} | {} | `{}` | {} | {} | {} |".format(
            l["exp"], cell(l["scenario"]), cell(l["algo"]), cell(l["seed"]),
            cell(raw(l["threads"])), f_int(l["ceiling"]), f_int(l["steps"]), pct,
            l["status"], f_g(l["fps"]), wall_str(l),
            cell("; ".join(l["flags"]) if l["flags"] else "—")))
    out.append("")
    total_steps = sum(l["steps"] for l in lanes if l["steps"] is not None)
    total_ceiling = sum(l["ceiling"] for l in lanes if l["ceiling"])
    agg = st.get("aggregate_fps")
    out.append(f"Totals across {len(lanes)} lanes: **{total_steps:,} env steps completed of "
               f"{total_ceiling:,} achievable** (snapshot); aggregate live throughput "
               f"**{raw(agg)} env-steps/s**.")
    out += ["", "### Checkpoints", "", "| experiment | latest checkpoint | state |", "|---|---|---|"]
    for l in lanes:
        out.append(f"| `{l['exp']}` | `{cell(l['ckpt'])}` | {cell(l['ckpt_state'])} |")
    out.append("")
    return out


def sec_scaling(camp):
    rows = read_csv_rows(camp / "metrics" / "scaling_table.csv")
    out = ["## Scaling table (reward and reward-per-enemy)", ""]
    if not rows:
        out += ["_UNAVAILABLE — `metrics/scaling_table.csv` missing or empty._", ""]
        return out
    out.append(f"Snapshot: `metrics/scaling_table.csv` (written {mtime_str(camp / 'metrics' / 'scaling_table.csv')}). "
               "`reward_per_enemy = train_reward_last / team_size`, computed here and "
               "emitted only for the NoWeapon family.")
    out += ["", "| scale | variant | seed | thr | steps (snapshot) | FPS | train reward (last) | reward/enemy | eval reward (last) | tail slope |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        variant = g(r, "variant")
        rw = g(r, "train_reward_last", "reward")
        if "shoot" in variant.lower():
            rpe = "n/a"
        elif rw not in ("", None) and g(r, "team_size"):
            rpe = f_num(float(rw) / int(r["team_size"]))
        else:
            rpe = "—"
        out.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            cell(g(r, "scale")), cell(variant), cell(g(r, "seed")), cell(g(r, "n_rollout_threads")),
            f_int(g(r, "env_steps", "steps_done")), f_g(g(r, "fps")),
            f_num(g(r, "train_reward_last")), rpe, f_num(g(r, "eval_reward_last")),
            raw(g(r, "train_reward_tail_slope"))))
    out += ["",
            "`reward_per_enemy` is shown as `n/a` for any ShootMissile row by policy. "
            "The official-baseline lanes are not part of this table (they are their own "
            "series; see the inventory).", ""]
    return out


BUDGET_MARK = {"interp": "*", "cross": "†", "before-data": "§", "nan-gap": "§"}


def render_budget_tables(camp, fname, title, blurb):
    rows = read_csv_rows(camp / "metrics" / fname)
    out = [f"## {title}", ""]
    if not rows:
        out += [f"_UNAVAILABLE — `metrics/{fname}` missing or empty._", ""]
        return out
    budgets = []
    for col in rows[0].keys():
        m = re.match(r"reward@(.+)$", col)
        if m:
            budgets.append(m.group(1))
    out += [blurb, "",
            f"Snapshot: `metrics/{fname}` (written {mtime_str(camp / 'metrics' / fname)}). "
            "`—` = pending (budget not reached at the snapshot); `*` = interpolated "
            "between bracketing updates; `†` = first crossing; `§` = before-data / "
            "nan-gap. Raw status and bracket per cell: the CSV itself.", ""]

    def table(prefix, label, withhold_shoot):
        out_l = [f"**{label}**", "", "| experiment | seed | " + " | ".join(budgets) + " |",
                 "|---" * (2 + len(budgets)) + "|"]
        any_value = False
        for r in rows:
            cells = []
            shoot = is_shoot(g(r, "scenario") or g(r, "experiment"))
            for b in budgets:
                v = g(r, f"{prefix}@{b}")
                s = g(r, f"status@{b}")
                if withhold_shoot and shoot:
                    cells.append("n/a")
                    continue
                if s == "pending" or v == "":
                    cells.append("—")
                else:
                    any_value = True
                    cells.append(f"{v}{BUDGET_MARK.get(s, '')}")
            out_l.append("| `{}` | {} | {} |".format(
                cell(g(r, "experiment")), cell(g(r, "seed")), " | ".join(cells)))
        out_l.append("")
        if not any_value:
            out_l += ["_No lane has reached any of these budgets at the snapshot; "
                      "every cell is pending and nothing is extrapolated._", ""]
        return out_l

    out += table("reward", "reward", False)
    out += table("reward_per_enemy", "reward per enemy (reward / team_size; NoWeapon family only — "
                 "`n/a` for ShootMissile)", True)
    return out


def sec_representation(camp):
    data = read_json(camp / "metrics" / "critic_scaling.json")
    out = ["## Representation / critic scaling (measured vs extrapolated)", ""]
    if not data:
        out += ["_UNAVAILABLE — `metrics/critic_scaling.json` missing or unreadable._", ""]
        return out
    measured = data.get("measured", []) or []
    extrapolated = data.get("extrapolated", []) or []
    anchored = [e for e in extrapolated if str(e.get("note", "")).strip() == "measured"]
    beyond = [e for e in extrapolated if str(e.get("note", "")).strip() != "measured"]

    out += [f"Source: `metrics/critic_scaling.json` (written "
            f"{mtime_str(camp / 'metrics' / 'critic_scaling.json')}); probe = model "
            "construction on the real networks, no training. Three tables, never "
            "mixed: (1) the four MEASURED points, (2) values derived from those same "
            "measurements, (3) predictions beyond the measured range.", "",
            "### 1. Measured rows (N = 2, 3, 5, 10)", "",
            "| N | agents | obs dim | share obs dim | actor params | critic params | critic 1st layer params | 1st-layer MAC/envstep | fwd ms (batch) | fwd ms (fixed-256) | bwd ms (fixed-256) | fwd µs/sample |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    checks = []
    for m in measured:
        n = m.get("team_size")
        so = m.get("share_obs_dim")
        cp = m.get("critic_params")
        fl = m.get("critic_first_layer_params")
        so_calc = 24 * n * n + 6 * n if isinstance(n, int) else None
        cp_calc = 128 * so_calc + 150145 if so_calc is not None else None
        fl_calc = 128 * (so + 1) if isinstance(so, int) else None
        checks.append((f"N={n} share_obs_dim", so, so_calc))
        checks.append((f"N={n} critic_params", cp, cp_calc))
        checks.append((f"N={n} critic_first_layer", fl, fl_calc))
        out.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            cell(n), cell(m.get("total_agents")), cell(m.get("obs_dim")), cell(so),
            f_int(m.get("actor_params")), f_int(cp), f_int(fl),
            f_int(m.get("critic_first_layer_MAC_per_envstep")),
            f_num(m.get("critic_fwd_ms_batch"), 3), f_num(m.get("critic_fwd_ms_fixed256")),
            f_num(m.get("critic_bwd_ms_fixed256")), f_num(m.get("critic_fwd_us_per_sample_fixed256"))))

    def extra_table(rows, heading, blurb):
        out_l = ["", f"### {heading}", "", blurb, "",
                 "| N | agents | obs dim | share obs dim | critic 1st layer params | 1st-layer MAC/envstep | est. fwd ms/envstep | share-obs buffer GB |",
                 "|---|---|---|---|---|---|---|---|"]
        for e in rows:
            out_l.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                cell(e.get("team_size")), cell(e.get("total_agents")), cell(e.get("obs_dim")),
                cell(e.get("share_obs_dim")), f_int(e.get("critic_first_layer_params")),
                f_int(e.get("critic_first_layer_MAC_per_envstep")),
                f_num(e.get("critic_fwd_ms_per_envstep_est")),
                raw(e.get("share_obs_buffer_GB"))))
        out_l.append("")
        return out_l

    out += extra_table(anchored, "2. Derived from the measured points (not new measurements)",
                       f"Computed from the same N = {', '.join(str(r.get('team_size')) for r in anchored)} "
                       "probe runs; the first-layer values here are identical to table 1 and are "
                       "checked below. Do not treat this table as independent evidence.")
    out += extra_table(beyond, "3. EXTRAPOLATED beyond the measured range (predictions only)",
                       f"N = {', '.join(str(r.get('team_size')) for r in beyond)} were never measured "
                       "(the probe only built the four networks above). These rows are model-based "
                       "predictions and must never be mixed with — or quoted as — measurements.")

    for e in beyond:
        n = e.get("team_size")
        so = e.get("share_obs_dim")
        fl = e.get("critic_first_layer_params")
        so_calc = 24 * n * n + 6 * n if isinstance(n, int) else None
        fl_calc = 128 * (so + 1) if isinstance(so, int) else None
        checks.append((f"N={n} share_obs_dim (extrapolated)", so, so_calc))
        checks.append((f"N={n} critic_first_layer (extrapolated)", fl, fl_calc))

    ok = all(rec in (None, "") or calc is None or abs(float(rec) - float(calc)) < 0.5
             for _, rec, calc in checks)
    out += ["### Closed-form check (computed in this script, not asserted)", "",
            "Per row: `share_obs = 24N² + 6N`, `critic_params = 128·(24N²+6N) + 150145`, "
            "`critic_first_layer_params = 128·(share_obs + 1)`.", "",
            "| quantity | recorded | closed form | match |", "|---|---|---|---|"]
    for name, rec, calc in checks:
        match = "—" if (rec in (None, "") or calc is None) else ("OK" if abs(float(rec) - float(calc)) < 0.5 else "**MISMATCH**")
        out.append(f"| {cell(name)} | {f_int(rec)} | {f_int(calc)} | {match} |")
    out += ["", f"All closed-form checks passed: **{'yes' if ok else 'NO — see MISMATCH rows'}**. "
            f"Probe metadata: device `{raw(data.get('device'))}`, "
            f"effective G-MAC/s {raw(data.get('effective_G_MAC_per_s'))}, "
            f"batch threads {raw(data.get('batch_threads'))}.", ""]
    return out


def sec_computational(camp, st):
    rows = read_csv_rows(camp / "metrics" / "scaling_table.csv")
    out = ["## Computational scalability", ""]
    if not rows:
        out += ["_UNAVAILABLE — `metrics/scaling_table.csv` missing or empty._", ""]
        return out
    out += [f"Snapshot: `metrics/scaling_table.csv` (written "
            f"{mtime_str(camp / 'metrics' / 'scaling_table.csv')}). `FPS` is the runner's "
            "own vectorised env-steps/s; `agent-steps/s = env-steps/s × total agents`.", "",
            "| scale | variant | thr | FPS (env-steps/s) | env-steps/s per thread | agent-steps/s | agent-steps/s per thread | sec / vectorised step | sec / rollout episode (3000 steps) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        fps = g(r, "fps")
        thr = g(r, "n_rollout_threads")
        out.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            cell(g(r, "scale")), cell(g(r, "variant")), cell(thr), f_g(fps),
            f_num(float(fps) / int(float(thr)), 2) if (fps not in ("", None) and thr not in ("", None)) else "—",
            f_g(g(r, "agent_steps_per_s")), f_g(g(r, "agent_steps_per_s_per_thread")),
            raw(g(r, "sec_per_vectorised_step")), raw(g(r, "sec_per_rollout_episode"))))
    agg = st.get("aggregate_fps")
    out += ["", f"Live campaign aggregate throughput at the `metrics/status.json` "
            f"snapshot: **{raw(agg)} env-steps/s** across all live lanes.", ""]
    return out


INC_HEAD = re.compile(r"^#+\s+(F\d+)\s*[—–-]\s*(.+?)\s*$")
INC_ANY_HEAD = re.compile(r"^#{1,3}\s")


def parse_incidents(path):
    text = read_text(path)
    if not text:
        return None
    items, cur = [], None
    for line in text.splitlines():
        m = INC_HEAD.match(line)
        if m:
            if cur:
                items.append(cur)
            cur = {"id": m.group(1), "title": m.group(2), "body": []}
            continue
        if cur is not None and INC_ANY_HEAD.match(line):
            items.append(cur)
            cur = None
            continue
        if cur is not None:
            cur["body"].append(line)
    if cur:
        items.append(cur)

    def field(body, name):
        """Value of `- **<name>**: ...`, including indented continuation lines."""
        pat = re.compile(r"-\s*\*\*(?:" + name + r")\*\*\s*:\s*(.*)")
        for i, ln in enumerate(body):
            m = pat.match(ln)
            if not m:
                continue
            parts = [m.group(1)]
            j = i + 1
            while j < len(body):
                nxt = body[j]
                if not nxt.strip() or nxt.lstrip().startswith("-") or INC_ANY_HEAD.match(nxt):
                    break
                parts.append(nxt.strip())
                j += 1
            return re.sub(r"\s+", " ", " ".join(parts)).strip()
        return ""

    for it in items:
        it["category"] = field(it["body"], "Categor(?:y|ies)").replace("`", "")
        it["detected"] = field(it["body"], "Detected")
        it["symptom"] = field(it["body"], "Symptom[s]?") or field(it["body"], "Cause")
        it.pop("body", None)
    return items


def sec_failures(camp, lanes, st):
    out = ["## Failure list (summarised from `status/incidents.md`)", ""]
    items = parse_incidents(camp / "status" / "incidents.md")
    if not items:
        out += ["_UNAVAILABLE — `status/incidents.md` missing or unreadable._", ""]
    else:
        cats = Counter((it["category"] or "?").split("(")[0].strip() for it in items)
        out += [f"{len(items)} incidents recorded for this campaign "
                f"({', '.join(f'{c}: {n}' for c, n in sorted(cats.items()))}). "
                "F1–F9 live in `docs/night_failures.md` and belong to the 2026-10-04 "
                "pilot; they are not re-listed here.", "",
                "| id | title | category | detected | summary (symptom/cause excerpt) |",
                "|---|---|---|---|---|"]
        for it in items:
            sym = it.get("symptom") or ""
            if len(sym) > 220:
                sym = sym[:217] + "…"
            out.append(f"| {cell(it['id'])} | {cell(it['title'])} | {cell(it['category'])} | "
                       f"{cell(it['detected'])} | {cell(sym)} |")
        out.append("")
    n_nan = sum(1 for l in lanes if "NaN" in l["flags"])
    n_inf = sum(1 for l in lanes if "Inf" in l["flags"])
    n_tb = sum(1 for l in lanes if "Traceback in log" in l["flags"])
    n_failed = sum(1 for l in lanes if l["status"] == "failed")
    out += [f"Live health flags at this snapshot: NaN ×{n_nan}, Inf ×{n_inf}, "
            f"traceback ×{n_tb}; lanes in status `failed`: {n_failed}.", ""]
    return out


def sec_limitations(lanes):
    out = ["## WHAT THIS DOES NOT SHOW", "",
           "Known limitations; read this before quoting any number above.", ""]

    groups = {}
    for l in lanes:
        groups.setdefault(l["scenario"], set()).add(str(l["seed"]))
    multi = sorted(k for k, v in groups.items() if len(v) > 1)
    single = sorted(k for k, v in groups.items() if len(v) <= 1)
    out += ["1. **Single seed at most scales.** Only the scenarios below carry more "
            "than one seed so far; every other scenario is a single-seed result. A "
            "between-scale (or between-seed) difference smaller than the run-to-run "
            "seed spread is not interpretable, and this document performs no such "
            "comparison.",
            f"   - multi-seed so far: {', '.join(f'`{k}`' for k in multi) if multi else 'none'}",
            f"   - single-seed at this generation: {', '.join(f'`{k}`' for k in single) if single else 'none'}", ""]

    thr_groups = {}
    for l in lanes:
        thr_groups.setdefault(l["scenario"], set()).add(l["threads"])
    confound = sorted(k for k, v in thr_groups.items() if len(v) > 1)
    out += ["2. **`n_rollout_threads` is a confound, not a detail.** The thread count "
            "differs across scales (forced by wall-clock: at a constant thread count "
            "10v10 cannot reach 6M inside the window) and the PPO update batch size is "
            "`threads × 3000`, so batch size differs across scales too."]
    thr_line = ", ".join(
        f"`{k}`: {sorted(int(t) for t in v if t)} thr (batch {sorted(int(t) * BUFFER for t in v if t)})"
        for k, v in sorted(thr_groups.items()))
    out += [f"   - threads per scenario at this generation: {thr_line}",
            (f"   - **within-scenario difference across seeds**: "
             f"{', '.join(f'`{k}`' for k in confound)} — the seed comparison there is "
             f"confounded by thread count as well.") if confound else
            "   - no scenario currently mixes thread counts across its seeds.", ""]

    capped = [l for l in lanes if l["ceiling"] and l["ceiling"] < TARGET]
    ceil3 = ceiling_of(3)
    out += ["3. **The 1v1 lanes cannot reach 6,000,000 by construction.** "
            f"A 3-thread lane floors at {TARGET // BUFFER // 3} episodes, i.e. "
            f"{f_int(ceil3)} of the nominal {f_int(TARGET)} (incident F17). Those lanes "
            "are reported as `completed_at_ceiling`, not as censored.",
            (f"   - affected lanes at this generation: "
             f"{', '.join(f'`{l['exp']}`' for l in capped)}") if capped else
            "   - no lane is currently below the nominal budget by construction.", ""]

    shoot_lanes = [l for l in lanes if l["shoot"]]
    sib = [l for l in lanes if l["threads"] == 3 and not l["shoot"] and l["fps"] not in (None, "")]
    fps_line = ""
    if shoot_lanes and sib:
        try:
            sf = max(float(x["fps"]) for x in shoot_lanes if x["fps"] not in (None, ""))
            others = sorted(f"{float(x['fps']):g}" for x in sib if x["fps"] not in (None, ""))
            fps_line = (f"   - current FPS: ShootMissile {sf:g} vs sibling 3-thread 1v1 lanes "
                        f"{', '.join(others)} env-steps/s (see inventory).")
        except (TypeError, ValueError):
            fps_line = ""
    out += ["4. **The 1v1 ShootMissile lane runs with `--use-prior`, which roughly "
            "halves throughput** (incident F14, category `Computational scalability` — "
            "not algorithmic). Its lower FPS is a property of the official code path, "
            "not an algorithmic finding.", fps_line, ""]

    out += ["5. **6M is a budget reduction, not a convergence result.** The official "
            f"configuration trains for 1e8 steps; this campaign runs {f_int(TARGET)} "
            f"({100.0 * TARGET / 1e8:.0f}% of that). Final rewards are an "
            "intermediate-training-state snapshot and must not be presented as "
            "converged performance.", "",
            "Also, by policy:", "",
            "- `reward_per_enemy` is defined only for the NoWeapon family "
            "(PostureReward sums over agents); it is withheld for ShootMissile rows.",
            "- The 2026-10-04 pilot is a separate series and is excluded from this "
            "document.",
            "- Tables built from the analysis CSVs are snapshots of those files "
            "(mtimes above); only the inventory is the live view. Nothing here is "
            "averaged across seeds, fitted, or significance-tested.",
            "- This document is a data record, not an analysis; interpret it with the "
            "hand-written report.", ""]
    return out


def sec_artefacts(camp):
    return ["## Related artefacts (not embedded here)", "",
            "- `metrics/scaling_table.csv` — machine-readable version of the scaling table above, and wider (obs dims, parameter counts, CPU/RAM peaks).",
            "- `metrics/normalized_scaling.csv` — per-episode reward and reward/enemy for the scaling family.",
            "- `metrics/sample_efficiency.csv` — reward / reward-per-enemy at fixed budgets up to 6M.",
            "- `metrics/equal_sample.csv`, `metrics/equal_wallclock.csv` — the raw checkpoint tables with per-cell status and bracket.",
            "- `metrics/resources.csv`, `metrics/throughput_history.csv`, `system/system_samples_v2.csv` — resource/throughput time series (the v1 sampler file is unreliably CPU-scaled; see incident F16).",
            "- `figures/` — plots regenerated by `scripts/make_figures.py`.",
            "- `docs/formal_repro_scaling_2026-10-07_08.md` — the hand-written report this document is the safety net for.",
            ""]


# ------------------------------------------------------------------ main

def generate(camp, out_path, repo):
    now = datetime.now()
    lanes, st, st_ts = build_inventory(camp, now)
    gi = git_info(repo)

    L = []
    L += [f"# Formal-6M auto-results — machine-generated numeric record", "",
          f"> **This file is machine-generated. Do not hand-edit.** Generated "
          f"**{now:%Y-%m-%d %H:%M:%S} {now.astimezone().tzname()}** "
          f"({now.astimezone().isoformat(timespec='seconds')}) "
          f"by `experiments/2026-10-07-08-formal6m/scripts/make_auto_results.py` "
          f"(repo HEAD `{gi['head']}`, branch `{gi['branch']}`). 本文件由脚本自动生成，所有数字均来自机器产物。", ">",
          f"> Campaign: `experiments/2026-10-07-08-formal6m`. Regenerate with: "
          f"`cd experiments/2026-10-07-08-formal6m && /root/miniconda3/envs/jsbsim/bin/python scripts/make_auto_results.py` "
          f"(also invoked by `scripts/freeze.sh`, which the tmux auto-finalizer runs on a schedule).", ">",
          "> Every value below is read from the files listed under *Sources and freshness*; "
          "none is hand-entered, and nothing is extrapolated except where a row explicitly "
          "says so. If the hand-written report never gets finished, this document is the "
          "complete numeric record.", ""]

    sections = [
        ("Conventions", lambda: sec_conventions(lanes)),
        ("Sources", lambda: sec_sources(camp)),
        ("Inventory", lambda: sec_inventory(lanes, st, st_ts)),
        ("Scaling", lambda: sec_scaling(camp)),
        ("EqualSample", lambda: render_budget_tables(
            camp, "equal_sample.csv", "Equal-sample comparison",
            "Reward and reward-per-enemy at fixed vectorised env-step budgets "
            "(1M–6M), from the campaign's own equal-sample generator.")),
        ("EqualWallclock", lambda: render_budget_tables(
            camp, "equal_wallclock.csv", "Equal-wall-clock comparison",
            "Reward and reward-per-enemy at fixed wall-clock budgets (1h–24h), "
            "from the campaign's own equal-wall-clock generator.")),
        ("Representation", lambda: sec_representation(camp)),
        ("Computational", lambda: sec_computational(camp, st)),
        ("Failures", lambda: sec_failures(camp, lanes, st)),
        ("Limitations", lambda: sec_limitations(lanes)),
        ("Artefacts", lambda: sec_artefacts(camp)),
    ]
    for name, fn in sections:
        try:
            L += fn()
        except Exception as exc:  # noqa: BLE001 -- one broken section must not kill the doc
            L += [f"sections/{name}: _UNAVAILABLE — generator error: "
                  f"{type(exc).__name__}: {exc}_", ""]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text("\n".join(L) + "\n")
    os.replace(tmp, out_path)  # atomic: readers never see a half-written doc
    return lanes


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign-root", default=os.environ.get("CAMPAIGN_ROOT"),
                    help=f"campaign dir (default: {CAMPAIGN_DEFAULT})")
    ap.add_argument("--out", default=os.environ.get("OUT"),
                    help="output document (default: <repo>/docs/formal_repro_scaling_auto_results.md)")
    ap.add_argument("--repo", default=None, help="repo root (default: derived from script location)")
    args = ap.parse_args(argv)

    camp = Path(args.campaign_root).expanduser().resolve() if args.campaign_root else CAMPAIGN_DEFAULT
    repo = Path(args.repo).expanduser().resolve() if args.repo else REPO_DEFAULT
    out_path = (Path(args.out).expanduser().resolve() if args.out
                else repo / "docs" / "formal_repro_scaling_auto_results.md")

    lanes = generate(camp, out_path, repo)
    missing = [rel for rel in ("manifest.csv", "metrics/status.json", "metrics/summary.csv",
                               "metrics/scaling_table.csv", "metrics/critic_scaling.json",
                               "metrics/equal_sample.csv", "metrics/equal_wallclock.csv",
                               "status/incidents.md") if not (camp / rel).exists()]
    print(f"campaign root : {camp}")
    print(f"wrote         : {out_path}")
    print(f"lanes         : {len(lanes)} "
          f"({sum(1 for l in lanes if l['status'].startswith('completed'))} completed, "
          f"{sum(1 for l in lanes if l['status'] == 'running')} running)")
    if missing:
        print(f"missing sources (sections degraded to placeholders): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
