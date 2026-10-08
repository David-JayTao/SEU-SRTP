#!/usr/bin/env python
"""Self-filling report: regenerate the AUTO sections of the formal-6M report.

The report `docs/formal_repro_scaling_2026-10-07_08.md` marks the sections whose
content is PURELY DERIVED DATA with an explicit pair of markers:

    <!-- AUTO:section5 -->
    ...generated content...
    <!-- /AUTO:section5 -->

and this script rewrites exactly the region between each pair, in place, from
the campaign's own artefacts.  It exists so that the report no longer depends
on a live Claude session: the tmux auto-finalizer (scripts/auto_finalize.sh)
runs scripts/freeze.sh on a schedule, and freeze.sh runs this script after the
analysis sweep, so every snapshot snapshot carries up-to-date numbers.

Guarantees
----------
* **Idempotent** -- each marker pair is matched as a pair and its whole body is
  replaced; markers are never nested, duplicated or re-emitted.  Running the
  script twice on the same data snapshot writes the same bytes (it still
  rewrites atomically, so mtime changes, content does not).  The only cells
  that can differ between two such runs are the wall-clock-derived ones
  (elapsed hours, "last write N min ago"), which re-render from the current
  time by design.
* **Partial-data safe** -- a lane at 60 %, or at its first update, renders;
  missing files, missing columns and missing markers degrade to `-`, to an
  explicit note, or to an inserted block -- never to a traceback.
* **Read-only w.r.t. everything else** -- it only reads campaign artefacts and
  writes the report file (atomically).  It never touches `scripts/results/`,
  the logs, or any input CSV.

Sources (all under `metrics/` unless stated)
--------------------------------------------
  summary.csv           one row per experiment: steps, FPS, rewards, slope,
                        checkpoint, crashed flag               (§5 §6 §11 §12 §17)
  scaling_table.csv     per-scale N-v-N table + arch dims      (§6 §11)
  normalized_scaling.csv  per-update normalised critic trace   (§11 context)
  equal_sample.csv      reward at 1M..6M steps per run         (§7)
  equal_wallclock.csv   reward at 1h/3h/6h/12h/24h per run      (§8)
  sample_efficiency.csv reward at matched sample budgets, no interpolation (§11)
  report_tables.md      sections E/F, used as a fallback when a CSV lacks a
                        lane, and for the per-lane CPU/RAM/VRAM reference (§6)
  status.json           live per-lane state (steps / achievable / done) written
                        by scripts/watch_f6m.py, which freeze.sh runs first   (§17)
  resources.csv         per-experiment peak CPU/RAM/VRAM samples               (§6)
  ../manifest.csv       planned lanes, threads, seeds                           (§17)
  ../configs/queue_*.txt, ../status/queue_*.status   planned threads + exit     (§17)

Status vocabulary (exactly one token, from the campaign brief)
--------------------------------------------------------------
  completed_6M          reached 6,000,000 steps
  completed_at_ceiling  reached its own, smaller ceiling by construction: the
                        runner floors episodes = num_env_steps//3000//threads,
                        so a 3-thread lane stops at 5,994,000 and can NEVER
                        reach 6,000,000.  That is completion, not a cutoff.
  running               still writing at generation time
  time_cutoff           stopped short of its own ceiling without a crash
                        signature (wall-clock cap / campaign end)
  failed                crash signature (traceback that is not a clean
                        KeyboardInterrupt -- the crashed flag of collect_metrics)
  not_applicable        the F9 official entry that cannot run at all

Exit codes and tracebacks are deliberately NOT used as success evidence:
run_train.sh captures `$?` from a pipeline without pipefail, and every queued
job is capped with `timeout -s INT` (a Traceback + KeyboardInterrupt by design)
-- see report §13.4.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_CAMPAIGN = SCRIPTS_DIR.parent                  # <campaign>/scripts/x.py
DEFAULT_REPO = DEFAULT_CAMPAIGN.parents[1]             # <repo>/experiments/<name>
DEFAULT_REPORT = DEFAULT_REPO / "docs" / "formal_repro_scaling_2026-10-07_08.md"

TARGET_STEPS = 6_000_000     # --num-env-steps 6e6, VECTORISED env steps
BUFFER_SIZE = 3000           # official buffer-size; one PPO update = threads * 3000
FRESH_FLOOR_S = 45 * 60      # freshness floor in seconds (mirrors make_report_tables.py)

SCALING_EXP_RE = re.compile(r"^f6m_(?P<n>\d+)v\d+_(?P<variant>noweapon|shoot)_s(?P<seed>\d+)$")

STATUS_VOCAB = ("completed_6M", "completed_at_ceiling", "running",
                "time_cutoff", "failed", "not_applicable")

# The F9 official entry: 1v1/ShootMissile/HierarchyVsBaseline dies at the first
# env step (`TypeError: 'NoneType' object is not subscriptable`) and was never
# launched; it is not_applicable, not a failure of this campaign.  Same id and
# rationale as scripts/make_report_tables.py.
NOT_APPLICABLE = [{
    "exp": "f6m_official_1v1_shoot_hier_vsbaseline",
    "scenario": "1v1/ShootMissile/HierarchyVsBaseline",
    "note": "not_applicable：F9 上游 bug（第一个 env step 即 TypeError）；"
            "该官方条目无法运行，从未启动",
}]

# Marker pair.  `(?P=sid)` keeps opener and closer bound to each other, so a
# missing closer can never swallow a foreign block.
AUTO_RE = re.compile(
    r"<!-- AUTO:(?P<sid>section\d+) -->[ \t]*\n?(?P<body>.*?)\n?[ \t]*"
    r"<!-- /AUTO:(?P=sid) -->",
    re.S)

SECTION_HEADINGS = {
    "section5": "## 5. ",
    "section6": "## 6. ",
    "section7": "## 7. ",
    "section8": "## 8. ",
    "section11": "## 11. ",
    "section12": "## 12. ",
    "section17": "## 17. ",
}


# --------------------------------------------------------------------- utils

def read_csv_rows(path):
    """CSV -> list[dict]; empty list on any failure (partial-data safe)."""
    try:
        with open(path, newline="") as fh:
            return list(csv.DictReader(fh))
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fint(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def first_not_none(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None


def max_int(*vals):
    xs = [fint(v) for v in vals]
    xs = [x for x in xs if x is not None]
    return max(xs) if xs else None


def fmt(v, nd=5):
    x = fnum(v)
    return "-" if x is None else f"{x:.{nd}g}"


def fmt_int(v):
    x = fint(v)
    return "-" if x is None else f"{x:,}"


def fmt_slope(v):
    x = fnum(v)
    return "-" if x is None else f"{x:+.3g}"


def parse_dt(txt):
    """ISO timestamp -> aware datetime (None on failure)."""
    if not txt:
        return None
    try:
        return datetime.fromisoformat(str(txt).strip())
    except ValueError:
        return None


def epoch(dt):
    return None if dt is None else dt.timestamp()


def age_min_str(seconds):
    if seconds is None:
        return "写入时间未知"
    m = seconds / 60.0
    return f"最近写入 {m:.0f} 分钟前" if m >= 2 else "最近写入 <2 分钟前"


def ceiling_steps(threads):
    """The reachable step budget at this thread count (F17).

    Runner: episodes = num_env_steps // 3000 // threads, then steps =
    episodes * threads * 3000.  So 3 threads -> 5,994,000; 4/8/10/20 -> exact.
    """
    t = fint(threads)
    if not t or t <= 0:
        return None
    return (TARGET_STEPS // BUFFER_SIZE // t) * t * BUFFER_SIZE


def scaling_exp_name(scale, variant, seed):
    s = f"f6m_{scale}_{variant}_s{seed}" if scale and variant else None
    return s


def exp_from_checkpoint(path):
    m = re.search(r"/(f6m_[^/]+)/run\d+", str(path or ""))
    return m.group(1) if m else None


def team_size_of(exp):
    m = re.search(r"(\d+)v\d+", exp or "")
    return int(m.group(1)) if m else None


def variant_of(exp):
    if "_noweapon" in (exp or ""):
        return "noweapon"
    if "_shoot" in (exp or ""):
        return "shoot"
    return None


def is_scaling(exp):
    return bool(SCALING_EXP_RE.match(exp or ""))


def is_official(exp):
    return (exp or "").startswith("f6m_official")


# ----------------------------------------------------------------- data load

def parse_report_tables(path):
    """Sections E (official) and F (scaling) of report_tables.md as fallbacks.

    Returns {"official": {exp: row}, "scaling": {(scale, seed): row}}.  Every
    parse step is defensive: on any surprise the result is simply empty and the
    primary CSVs carry the section.
    """
    out = {"official": {}, "scaling": {}}
    try:
        text = Path(path).read_text(errors="replace")
    except OSError:
        return out

    def rows_after(marker):
        idx = text.find(marker)
        if idx < 0:
            return []
        rows = []
        for line in text[idx:].splitlines():
            s = line.strip()
            if s.startswith("|") and s.endswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if cells and not set("".join(cells)) <= set("-: "):
                    rows.append(cells)
            elif rows and not s:
                break
        return rows

    e_rows = rows_after("## E. OFFICIAL BASELINE TABLE")
    hdr = e_rows[0] if e_rows else []
    if hdr and hdr[0] == "Experiment":
        keys = ["exp", "seed", "steps", "wall", "fps", "rew_first", "rew_last",
                "eval", "rt_status", "checkpoint"]
        for cells in e_rows[1:]:
            if len(cells) == len(keys):
                d = dict(zip(keys, cells))
                if d.get("exp"):
                    out["official"][d["exp"]] = d

    f_rows = rows_after("## F. SCALING TABLE")
    hdr = f_rows[0] if f_rows else []
    if hdr and hdr[0] == "Scale":
        keys = ["scale", "agents", "seed", "steps", "fps", "wall", "rew_raw",
                "rew_norm", "value_loss", "critic_grad", "cpu", "ram", "vram",
                "rt_status"]
        for cells in f_rows[1:]:
            if len(cells) == len(keys):
                d = dict(zip(keys, cells))
                seed = fint(d.get("seed"))
                out["scaling"][(d.get("scale"), seed)] = d
    return out


def resource_peaks(path):
    """exp -> {cpu_cores, ram_gb, vram_mb} over all samples in resources.csv."""
    peaks = {}
    for r in read_csv_rows(path):
        e = r.get("experiment")
        if not e:
            continue
        p = peaks.setdefault(e, {"cpu_cores": 0.0, "ram_gb": 0.0, "vram_mb": 0.0})
        cpu = fnum(r.get("cpu_pct"))
        ram = fnum(r.get("rss_gb"))
        vram = fnum(r.get("gpu_vram_mb"))
        if cpu is not None:
            p["cpu_cores"] = max(p["cpu_cores"], cpu / 100.0)
        if ram is not None:
            p["ram_gb"] = max(p["ram_gb"], ram)
        if vram is not None:
            p["vram_mb"] = max(p["vram_mb"], vram)
    return peaks


def load_queue_ledger(camp):
    """planned: exp -> {threads, steps, seed}; state: exp -> {end, rc}."""
    planned, state = {}, {}
    for qf in sorted((camp / "configs").glob("queue_*.txt")):
        try:
            lines = qf.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            p = [x.strip() for x in line.split("|")]
            if len(p) < 8 or line.strip().startswith("#"):
                continue
            planned[p[0]] = {"threads": fint(p[1]), "steps": fint(p[2]),
                             "seed": fint(p[7])}
    for sf in sorted((camp / "status").glob("queue_*.status")):
        try:
            lines = sf.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            m = re.match(r">>> (\S+) start (\S+)", line)
            if m:
                st = state.setdefault(m.group(1), {})
                t = parse_dt(m.group(2))
                if t is not None:
                    st["start"] = min(filter(None, [st.get("start"), epoch(t)]))
                continue
            m = re.match(r"<<< (\S+) end (\S+) rc=(\d*)", line)
            if m:
                st = state.setdefault(m.group(1), {})
                t = parse_dt(m.group(2))
                if t is not None:
                    st["end"] = epoch(t)
                st["rc"] = m.group(3)
    return planned, state


# -------------------------------------------------------------------- lanes

def build_lanes(camp, now):
    """One merged record per experiment from every available source."""
    mdir = camp / "metrics"
    status = load_json(mdir / "status.json")
    json_epoch = None
    if isinstance(status, dict):
        json_epoch = epoch(parse_dt(status.get("timestamp")))

    summary = {}
    for r in read_csv_rows(mdir / "summary.csv"):
        if r.get("experiment"):
            summary[r["experiment"]] = r

    scaling = {}
    for r in read_csv_rows(mdir / "scaling_table.csv"):
        exp = first_not_none(exp_from_checkpoint(r.get("checkpoint")),
                             scaling_exp_name(r.get("scale"), r.get("variant"), fint(r.get("seed"))))
        if exp:
            scaling[exp] = r

    resources = resource_peaks(mdir / "resources.csv")
    rt = parse_report_tables(mdir / "report_tables.md")

    manifest = {}
    for r in read_csv_rows(camp / "manifest.csv"):
        if r.get("experiment_id"):
            manifest[r["experiment_id"]] = r

    sjobs = {}
    if isinstance(status, dict) and isinstance(status.get("jobs"), list):
        for j in status["jobs"]:
            if isinstance(j, dict) and j.get("exp"):
                sjobs[j["exp"]] = j

    planned, ledger = load_queue_ledger(camp)

    names = set(summary) | set(scaling) | set(sjobs) | set(planned)
    for e, m in manifest.items():
        if m.get("start_time") or fint(m.get("num_env_steps_done")) is not None:
            names.add(e)

    lanes = {}
    for exp in sorted(names):
        s = summary.get(exp, {})
        j = sjobs.get(exp, {})
        m = manifest.get(exp, {})
        sc = scaling.get(exp, {})
        pl = planned.get(exp, {})
        led = ledger.get(exp, {})

        threads = first_not_none(fint(s.get("n_rollout_threads")), fint(j.get("threads")),
                                 fint(m.get("n_rollout_threads")), pl.get("threads"))
        seed = first_not_none(fint(s.get("seed")), fint(m.get("seed")), pl.get("seed"))
        if seed is None:
            mm = SCALING_EXP_RE.match(exp)
            if mm:
                seed = fint(mm.group("seed"))

        steps = max_int(s.get("steps_done"), j.get("steps"), m.get("num_env_steps_done"))
        ceil = ceiling_steps(threads) or fint(j.get("achievable"))
        target = first_not_none(fint(s.get("steps_target")), fint(j.get("target")),
                                fint(m.get("num_env_steps_planned")))

        start = epoch(parse_dt(s.get("start")))
        if start is None:
            start = first_not_none(led.get("start"), epoch(parse_dt(m.get("start_time"))))
        if start is None:
            # the log header is authoritative; a log file mtime is not a start,
            # so only fall back to the queue's start marker, handled above.
            start = first_not_none(led.get("start"))

        last_write = epoch(parse_dt(s.get("last_log_time")))
        if j.get("age_min") is not None and json_epoch is not None:
            last_write = max(filter(None, [last_write,
                                           json_epoch - float(j["age_min"]) * 60]),
                             default=None)
        # the log's mtime is cheap to read and immune to status.json being stale
        lp = s.get("log_path")
        if lp:
            try:
                last_write = max(filter(None, [last_write, os.path.getmtime(lp)]),
                                 default=None)
            except OSError:
                pass

        fps = first_not_none(fnum(s.get("fps_last")), fnum(j.get("fps")), fnum(sc.get("fps")))
        window = FRESH_FLOOR_S
        if fps and threads:
            window = max(window, 3.0 * threads * BUFFER_SIZE / fps)
        fresh = last_write is not None and (now - last_write) <= window

        crashed = str(s.get("crashed", "")).strip().lower() == "true"

        # status.json is rewritten by watch_f6m.py at the START of a freeze,
        # before collect_metrics/make_manifest rewrite the CSVs -- so it can be
        # one update BEHIND them.  Prefer its live reward/eval/FPS only when it
        # is at least as advanced as the freshest step count in this lane
        # record; otherwise the row would combine a newer step count with an
        # older reward (seen for f6m_5v5_noweapon_s0 in the 17:40 freeze:
        # steps 4,296,000 from summary.csv with the -4.3517 reward that
        # actually belongs to step 4,272,000).
        json_fresh = json_epoch is not None and (now - json_epoch) <= 1800
        j_steps = fint(j.get("steps"))
        json_ahead = j_steps is not None and (steps is None or j_steps >= steps)
        live = ((lambda k: fnum(j.get(k)))
                if (json_fresh and json_ahead) else (lambda k: None))

        pe = resources.get(exp, {})
        lane = {
            "exp": exp, "seed": seed, "threads": threads, "steps": steps,
            "target": target, "ceiling": ceil,
            "fps": first_not_none(live("fps"), fnum(s.get("fps_last")),
                                  fnum(j.get("fps")), fnum(sc.get("fps"))),
            "rew_first": first_not_none(fnum(s.get("train_reward_first")),
                                        fnum(sc.get("train_reward_first"))),
            "rew_last": first_not_none(live("reward"),
                                       fnum(s.get("train_reward_last")),
                                       fnum(sc.get("train_reward_last")),
                                       fnum(j.get("reward"))),
            "slope": first_not_none(fnum(s.get("train_reward_tail_slope")),
                                    fnum(sc.get("train_reward_tail_slope"))),
            "eval": first_not_none(live("eval_reward"),
                                   fnum(s.get("eval_reward_last")),
                                   fnum(sc.get("eval_reward_last")),
                                   fnum(j.get("eval_reward"))),
            "value_loss": first_not_none(fnum(sc.get("critic_loss_value")),
                                         fnum(s.get("value_loss_last"))),
            "critic_grad": first_not_none(fnum(sc.get("critic_grad_norm")),
                                          fnum(s.get("critic_grad_norm_last"))),
            "start": start, "last_write": last_write, "fresh": fresh,
            "crashed": crashed,
            "episodes": first_not_none(fint(s.get("episodes_logged")), fint(sc.get("episodes_logged"))),
            "episodes_target": fint(s.get("episodes_target")),
            "checkpoint": first_not_none(s.get("checkpoint_path"), sc.get("checkpoint")),
            "scenario": first_not_none(s.get("scenario"), m.get("scenario")),
            "n": team_size_of(exp), "variant": variant_of(exp),
            "family": "official" if is_official(exp) else ("scaling" if is_scaling(exp) else "other"),
            "scale": first_not_none(j.get("scale"), scaling.get(exp, {}).get("scale")),
            "end": led.get("end"), "rc": led.get("rc"),
            "manifest_status": m.get("status"),
            "manifest_notes": m.get("notes"),
            "resources": pe,
            "rt_official": rt["official"].get(exp),
        }
        lanes[exp] = lane
    return lanes


def classify(lane):
    """Exactly one status token (see module docstring)."""
    steps, ceil = lane["steps"], lane["ceiling"]
    if steps is not None and ceil:
        if steps >= ceil:
            return "completed_6M" if ceil >= TARGET_STEPS else "completed_at_ceiling"
    elif steps is not None and steps >= TARGET_STEPS:
        return "completed_6M"
    if lane["crashed"]:
        return "failed"
    if lane["fresh"]:
        return "running"
    if steps is None and lane["last_write"] is None and lane["start"] is None:
        return "not_applicable"          # nothing ever ran under this id
    return "time_cutoff"


def wall_seconds(lane, status, now):
    start = lane["start"]
    if start is None:
        return None
    end = now if status == "running" else (lane["last_write"] or now)
    return max(0.0, end - start)


# --------------------------------------------------------------- render bits

def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c) for c in r) + " |")
    return "\n".join(out)


def cell_value(reward, per_enemy, status, variant):
    """One equal-sample / equal-wall-clock cell: value (per-enemy)* or token."""
    if status in ("pending", "before-data", "nan-gap") or reward in (None, ""):
        return status if status else "pending"
    txt = fmt(reward, 5)
    # Same gate as equal_sample.py / equal_wallclock.py: a per-enemy figure
    # exists only for NoWeapon-family rows (the CSVs leave it blank elsewhere).
    if per_enemy not in (None, "") and "noweapon" in (variant or ""):
        txt += f" ({fmt(per_enemy, 5)})"
    if status in ("interp", "cross"):
        txt += "*"
    return txt


def lane_status_note(lane, status, now):
    """Human-readable reason/state line for §17."""
    s, c, t = lane["steps"], lane["ceiling"], lane["threads"]
    if status == "completed_6M":
        return "已达到 6,000,000 步目标"
    if status == "completed_at_ceiling":
        eps = (TARGET_STEPS // BUFFER_SIZE // t) if t else None
        return (f"按其构造只能到达自身上限 {fmt_int(c)} < 6,000,000"
                f"（F17：runner 向下取整 episodes = 6e6//3000//{t} = {eps}；"
                f"{t}-thread 通道永远到不了 6M）。这不是缺口。")
    if status == "running":
        rem = (c - s) if (c is not None and s is not None) else None
        rem_txt = f"本快照时距其上限还差 {fmt_int(rem)} 步" if rem is not None else "低于其上限"
        return f"仍在写入（{age_min_str(now - lane['last_write'] if lane['last_write'] else None)}）；{rem_txt}"
    if status == "time_cutoff":
        short = (c - s) if (c is not None and s is not None) else None
        short_txt = f"低于其上限 {fmt_int(short)}" if short is not None else "未达其上限"
        return (f"停在 {fmt_int(s)}（{short_txt}）；无崩溃特征 —— "
                f"挂钟时间/批次截止（time_cutoff）。退出码不是证据（§13.4）。")
    if status == "failed":
        return "崩溃特征（不是干净 KeyboardInterrupt 的 traceback）；见其日志"
    if status == "not_applicable":
        return next((na["note"] for na in NOT_APPLICABLE if na["exp"] == lane["exp"]),
                    "不适用")
    return "-"


# ----------------------------------------------------------------- sections

def render_section5(lanes, now):
    official = sorted((l for l in lanes.values() if l["family"] == "official"),
                      key=lambda l: l["exp"])
    for l in official:
        l["status"] = classify(l)
    rows = []
    for l in official:
        wall = wall_seconds(l, l["status"], now)
        ck = os.path.basename(str(l["checkpoint"])) if l["checkpoint"] else "-"
        rows.append([l["exp"],
                     fmt_int(l["seed"]) if l["seed"] is not None else "-",
                     fmt_int(l["steps"]),
                     (f"{wall / 3600:.2f} h" if wall is not None else "-"),
                     fmt(l["fps"], 4), fmt(l["rew_first"]), fmt(l["rew_last"]),
                     fmt(l["eval"]), l["status"], ck])
    have = {l["exp"] for l in official}
    for na in NOT_APPLICABLE:
        if na["exp"] not in have:
            rows.append([na["exp"], "-", "-", "-", "-", "-", "-", "-",
                         "not_applicable", "-"])
    body = [
        "本实验批次的官方基线通道。`Status` 使用本批次的既定状态词表"
        "（见下方说明）；`Wall time`（挂钟时间）为该次运行自身开始到"
        "最后一次日志写入（`running` 通道：到本区块生成时刻）。",
        "",
        md_table(["实验", "种子", "步数", "挂钟时间", "FPS",
                  "初始 reward", "最终 reward", "Eval", "状态", "Checkpoint"],
                 rows),
        "",
        "_3-thread 通道（`f6m_official_1v1_*`）停在 6,000,000 步目标的 "
        "**5,994,000** 处：runner 向下取整 `episodes = 6e6//3000//threads` "
        "= 666，而 666 x 9,000 = 5,994,000。这属于 `completed_at_ceiling`"
        "（在通道自身可达预算处完成），绝不是被截断 —— 见 §17。_",
        "",
        "_`f6m_official_1v1_shoot_hier_vsbaseline` 是 F9 条目：它在 upstream "
        "第一个 env step 就崩溃，从未被启动。_",
    ]
    if not official:
        body.append("")
        body.append("_尚无官方基线通道留下产物（summary.csv 为空）。"
                    "下一次 freeze 时该表会被填充。_")
    return "\n".join(body)


def render_section6(lanes, camp_peaks, now):
    scaling = sorted((l for l in lanes.values() if l["family"] == "scaling"),
                     key=lambda l: (l["n"] or 0, l["seed"] if l["seed"] is not None else 0))
    for l in scaling:
        l["status"] = classify(l)
    rows = []
    for l in scaling:
        n = l["n"]
        raw = l["rew_last"]
        norm = (raw / n) if (raw is not None and n and l["variant"] == "noweapon") else None
        wall = wall_seconds(l, l["status"], now)
        pe = l["resources"] or {}
        if pe.get("cpu_cores"):
            cpu = f"{pe['cpu_cores']:.1f}"
        elif camp_peaks.get("cpu_cores"):
            cpu = f"{camp_peaks['cpu_cores']:.1f} deg"   # deg = campaign-wide peak
        else:
            cpu = "-"
        ram = (f"{pe['ram_gb']:.2f} GB" if pe.get("ram_gb")
               else (f"{camp_peaks['ram_gb']:.1f} GB deg" if camp_peaks.get("ram_gb") else "-"))
        vram = (f"{pe['vram_mb']:.0f} MB" if pe.get("vram_mb")
                else (f"{camp_peaks['vram_mb']:.0f} MB deg" if camp_peaks.get("vram_mb") else "-"))
        rows.append([f"{n}v{n}" if n else l["exp"], str(2 * n) if n else "-",
                     fmt_int(l["seed"]) if l["seed"] is not None else "-",
                     fmt_int(l["steps"]), fmt(l["fps"], 4),
                     f"{wall / 3600:.2f} h" if wall is not None else "-",
                     fmt(raw), fmt(norm), fmt(l["value_loss"]), fmt(l["critic_grad"]),
                     cpu, ram, vram, l["status"]])
    body = [
        "N-v-N 正式 scaling 表，每行一个 (规模, 种子)。`Reward normalized` "
        "= 最终训练 reward / N —— 仅对 NoWeapon 系列有效"
        "（PostureReward 对 N 个敌机求和），ShootMissile 一律不适用。",
        "",
        md_table(["规模", "Agent 数", "种子", "步数", "FPS", "挂钟时间",
                  "Reward 原始值", "Reward 归一化", "Value loss", "Critic grad",
                  "CPU", "RAM", "VRAM", "状态"], rows),
        "",
        "_挂钟时间 = 运行开始到最后一次日志写入（`running` 行：到生成时刻）；"
        "`running` 行的步数/FPS/reward 均为生成时刻的实时值。"
        "CPU/RAM/VRAM 取自该次运行自身进程在 `metrics/resources.csv` 中的峰值；"
        "标 `deg` 的单元格因尚无逐通道样本而退回使用 `scaling_table.csv` 的"
        "全批次峰值。`n_rollout_threads` 在各规模间不同（§4.5），"
        "因此 FPS 不可跨 N 比较；`Reward normalized` 与 §7/§11 的"
        "逐 agent 视角可以。_",
    ]
    if not scaling:
        body.append("")
        body.append("_尚无 N-v-N scaling 通道留下产物。_")
    return "\n".join(body)


def render_equal_section(rows, budgets, labels, kind):
    """§7 (steps) and §8 (hours) share this renderer.

    budgets: list of raw ints; labels: display strings.
    """
    if not rows:
        return (f"_`metrics/{kind}.csv` 为空或缺失 —— 暂无可渲染内容"
                f"（需先运行其 freeze 步骤）。_")
    rrows = []
    for r in sorted(rows, key=lambda r: (fint(r.get("team_size")) or 0,
                                         fint(r.get("seed")) or 0, r.get("experiment", ""))):
        variant = r.get("variant", "")
        cells = []
        for b, lab in zip(budgets, labels):
            st = r.get(f"status@{lab}", "")
            rw = r.get(f"reward@{lab}", "")
            pe = r.get(f"reward_per_enemy@{lab}", "")
            cells.append(cell_value(rw, pe, st, variant))
        rrows.append([r.get("experiment", "-"), str(r.get("team_size", "-")),
                      str(r.get("seed", "-")), str(r.get("n_rollout_threads", "-")),
                      fmt_int(r.get("max_steps")), r.get("run_state", "-")] + cells)
    header = (["实验", "N", "种子", "Rollout 线程", "已到步数", "状态"]
              + labels)
    if kind == "equal_sample":
        lead = ("等样本对比：各通道在相同 vectorised-env-step 预算（1M..6M）"
                "下的平均训练 reward。")
        foot = ("_单元格：NoWeapon 通道为 `reward（每敌机 reward）`；"
                "`*` = 在相邻两个 PPO update 之间插值；`pending` = 该通道尚未"
                "达到该预算（绝不做任何外推）；`before-data`/`nan-gap` 为原始"
                "来源标记。逐格原始区间见 `metrics/equal_sample.csv`。"
                "每敌机数值仅对 NoWeapon 显示；ShootMissile 的 reward 不是"
                "队伍求和。_")
    else:
        lead = ("等挂钟时间对比：各通道在相同已流逝时间预算（自身运行时间的 "
                "1h..24h）下的平均训练 reward。")
        foot = ("_单元格：NoWeapon 通道为 `reward（每敌机 reward）`；"
                "`*` = 在相邻 update 之间插值；`pending` = 尚未达到。"
                "已流逝时间 = 通道自身的 `wall_time` 减去其首个日志时间戳，"
                "因此不含排队/启动时间。各规模使用不同的 `n_rollout_threads`"
                "（§4.5），所以挂钟时间同时反映学习速度与调度选择。"
                "原始区间：`metrics/equal_wallclock.csv`。_")
    return "\n".join([lead, "", md_table(header, rrows), "", foot])


def improving_verdict(slope):
    x = fnum(slope)
    if x is None:
        return "-"
    if x > 0.05:
        return f"上升（{x:+.3g}/update）"
    if x < -0.05:
        return f"下降（{x:+.3g}/update）"
    return f"持平（{x:+.3g}/update）"


def matched_stage_rows(norm_rows, first_k=5):
    """Per-N means over the first `first_k` logged updates (normalized_scaling.csv).

    value_loss/N^2 and critic_grad_norm/N remove the *reward-magnitude* growth
    with N; if the N-dependence were a pure reward-scale effect both would be
    roughly constant.  Small-k means are noisy; the point is only that they are
    computed on matched training stages, and k is stated.
    """
    per_n = {}
    seen = {}
    for r in norm_rows:
        n = fint(r.get("team_size"))
        if n is None:
            continue
        ep = fint(r.get("episode"))
        if ep is None or ep >= first_k:
            continue
        if r.get("experiment") in seen and ep in seen[r["experiment"]]:
            continue
        seen.setdefault(r.get("experiment", ""), set()).add(ep)
        d = per_n.setdefault(n, {"rw": [], "vl": [], "gn": [], "runs": set()})
        d["runs"].add(r.get("experiment"))
        for key, col in (("rw", "reward_per_enemy"), ("vl", "value_loss_per_N2"),
                         ("gn", "critic_grad_norm_per_N")):
            x = fnum(r.get(col))
            if x is not None:
                d[key].append(x)
    rows = []
    for n in sorted(per_n):
        d = per_n[n]
        mean = lambda xs: (sum(xs) / len(xs)) if xs else None   # noqa: E731
        rows.append([f"{n}v{n}", str(len(d["runs"])),
                     str(max(len(d["rw"]), len(d["vl"]), len(d["gn"]))),
                     fmt(mean(d["rw"]), 4), fmt(mean(d["vl"]), 4), fmt(mean(d["gn"]), 4)])
    return rows


def render_section11(lanes, sample_rows, norm_rows):
    scaling = sorted((l for l in lanes.values() if l["family"] == "scaling"),
                     key=lambda l: (l["n"] or 0, l["seed"] if l["seed"] is not None else 0))
    for l in scaling:
        l["status"] = classify(l)
    rows = []
    for l in scaling:
        n = l["n"]
        # per-enemy reward is a NoWeapon-only normalisation (PostureReward sums
        # over enemies); never divide a ShootMissile reward by N.
        pe = ((l["rew_last"] / n) if (l["rew_last"] is not None and n
                                      and l["variant"] == "noweapon") else None)
        frac = (100.0 * l["steps"] / l["ceiling"]) if (l["steps"] and l["ceiling"]) else None
        frac_txt = f"{frac:.1f}%" if frac is not None else "-"
        rows.append([f"{n}v{n}" if n else l["exp"],
                     fmt_int(l["seed"]) if l["seed"] is not None else "-",
                     f"{fmt_int(l['steps'])} ({frac_txt})", l["status"],
                     fmt(l["rew_first"]), fmt(l["rew_last"]), fmt(pe),
                     fmt_slope(l["slope"]), improving_verdict(l["slope"]),
                     fmt(l["eval"])])
    body = [
        "N-v-N 各通道的逐规模 reward 轨迹汇总，数据来自 "
        "`metrics/summary.csv`。`Tail slope` 是最后三分之一已记录 update 中 "
        "`average_episode_rewards` 每次 PPO update 的平均变化量；仅当斜率超过 "
        "+0.05/update 时才判定为上升（与 `scaling_table.py` 同阈值），"
        "在 ±0.05 内为持平，低于 -0.05 为下降。",
        "",
        md_table(["规模", "种子", "已到步数（占上限 %）", "状态",
                  "首个 reward", "最后 reward", "每敌机 reward",
                  "尾段斜率", "最后一条已记录 update 时仍在上升？",
                  "Eval 最后值"], rows),
        "",
        "_`每敌机 reward` 除以 N，是 NoWeapon 系列唯一可跨 N 比较的 reward"
        "（PostureReward 对敌机求和；见 §4）。`running` 通道的判定说的是其"
        "在生成时刻最后一条已记录 update 的状态，而非最终走向；处于 "
        "`completed_*` 的通道已冻结在其最终值。有两个种子的规模按种子分别"
        "给出；§12 量化其离散度。_",
    ]
    # matched-sample table from sample_efficiency.csv (never interpolated)
    if sample_rows:
        labels = ["150k", "300k", "450k", "600k"]
        keys = ["150000", "300000", "450000", "600000"]
        rows2 = []
        if all(f"reward@{k}" in sample_rows[0] for k in keys):
            for r in sorted(sample_rows, key=lambda r: (fint(r.get("team_size")) or 0,
                                                        fint(r.get("seed")) or 0)):
                cells = []
                for k in keys:
                    rw, pe = fnum(r.get(f"reward@{k}")), fnum(r.get(f"reward_per_enemy@{k}"))
                    actual = fint(r.get(f"actual_step@{k}"))
                    if rw is None:
                        cells.append("未达到")
                        continue
                    txt = f"{rw:.2f}" + (f" ({pe:.2f})" if pe is not None else "")
                    if actual is not None and actual < 0.75 * int(k):
                        txt += "~"
                    cells.append(txt)
                rows2.append([f"{r.get('team_size')}v{r.get('team_size')}",
                              str(r.get("seed", "-")), fmt_int(r.get("max_steps"))] + cells)
            body += [
                "",
                "来自 `metrics/sample_efficiency.csv` 的等样本预算"
                "（每个预算取 ≤ 该预算的最新真实测量值 —— 不做插值；"
                "`~` 表示最近的测量值低于所请求预算的 75%，即不要把该列"
                "读成该通道曾在该预算处被测量）：",
                "",
                md_table(["规模", "种子", "最大步数", "150k", "300k", "450k", "600k"], rows2),
                "",
                "_`reward（每敌机 reward）`；仅 NoWeapon 系列。_",
            ]
    # matched early-training stage from normalized_scaling.csv
    ms_rows = matched_stage_rows(norm_rows) if norm_rows else []
    if ms_rows:
        body += [
            "",
            "匹配的早期训练阶段（每次运行前 5 条已记录 update 的均值，"
            "来自 `metrics/normalized_scaling.csv`）。把 critic 的 value loss "
            "除以 N^2、梯度范数除以 N，可消去随 N 增长的 reward 量级；"
            "若 N 依赖纯粹来自 reward 尺度效应，两者都应大致恒定 —— "
            "剩下的漂移就是同一训练阶段下的跨 N 逐 update 差异：",
            "",
            md_table(["规模", "运行数", "Updates", "每敌机 reward",
                      "Value loss / N^2", "Critic grad / N"], ms_rows),
            "",
            "_前 5 条 update 的均值天然噪声很大；这是同阶段对比，不是收敛值。"
            "完整逐 update 轨迹见 `metrics/normalized_scaling.csv`。_",
        ]
    return "\n".join(body)


def render_section12(lanes):
    scaling = [l for l in lanes.values() if l["family"] == "scaling" and l["steps"] is not None]
    for l in scaling:
        l["status"] = classify(l)
    by_n = {}
    for l in scaling:
        by_n.setdefault(l["n"], []).append(l)
    out = [
        "N-v-N 通道的种子离散度。仅当同一规模存在至少两个种子时才计算离散"
        "范围；单次运行无法给出方差，也绝不凭单次运行编造。",
        "",
    ]
    if not by_n:
        out.append("_尚无任何 scaling 通道记录数据。_")
        return "\n".join(out)
    for n in sorted(by_n):
        group = sorted(by_n[n], key=lambda l: (l["seed"] if l["seed"] is not None else -1))
        out.append(f"**{n}v{n}** —— 有数据的通道数：{len(group)}。")
        out.append("")
        rows = []
        for l in group:
            # NoWeapon-only normalisation, as in §6/§11 -- see cell_value().
            pe = ((l["rew_last"] / n) if (l["rew_last"] is not None
                                          and l["variant"] == "noweapon") else None)
            rows.append([fmt_int(l["seed"]), l["status"], fmt_int(l["threads"]),
                         fmt_int(l["steps"]), fmt_int(l["ceiling"]),
                         fmt(l["rew_last"]), fmt(pe)])
        out.append(md_table(["种子", "状态", "Rollout 线程", "已到步数", "上限",
                             "最后记录的 reward", "每敌机 reward"], rows))
        out.append("")
        thr = sorted({l["threads"] for l in group if l["threads"] is not None})
        if len(group) >= 2 and len(thr) > 1:
            detail = ", ".join(f"种子 {l['seed']}: {l['threads']}" for l in group)
            out.append(f"**线程混淆因素（§4.5）：** {n}v{n} 的各种子并不共享 "
                       f"`n_rollout_threads`（{detail}），因此该对比同时混入"
                       f"了 batch 大小差异。")
            out.append("")
        if len(group) < 2:
            out.append(f"_本次实验批次中 {n}v{n} 只有一个种子，因此**不计算"
                       f"离散范围**（至少要两次运行才能给出）。"
                       f"单种子趋势见 §11。_")
        else:
            raws = [l["rew_last"] for l in group if l["rew_last"] is not None]
            pes = [l["rew_last"] / n for l in group if l["rew_last"] is not None]
            if len(raws) >= 2:
                spread_raw = max(raws) - min(raws)
                spread_pe = max(pes) - min(pes)
                out.append(f"_生成时刻最终已记录训练 reward 的离散范围：原始值 "
                           f"**{spread_raw:.3g}**（每敌机 **{spread_pe:.3g}**），"
                           f"即 {len(raws)} 个种子的 max - min。_")
            else:
                out.append("_记录到 reward 的种子不足两个 —— 暂不计算离散范围。_")
            incomplete = [l for l in group if l["status"] == "running"]
            if incomplete:
                names = ", ".join(f"种子 {l['seed']} 处于 {fmt_int(l['steps'])} 步"
                                  for l in incomplete)
                out.append("")
                out.append(f"**暂定：** {names} —— 该离散范围比较的是不同训练"
                           f"阶段的种子，会随未完成通道继续训练而收缩或移动。"
                           f"请把它当作当前差异的上界，而不是方差估计。")
        out.append("")
    out.append("_本次实验批次在 3v3 与 5v5 各有两个种子（种子 0 与种子 1）。"
               "2v2 与 10v10 的 scaling 系列各只有一个种子；官方 2v2 通道"
               "走的是另一条场景路径，不计作 scaling 通道的第二个种子。"
               "表中给出每条通道的线程数与步数；若同一规模的两个种子在 "
               "`n_rollout_threads` 上不同，该对比还混入 §4.5 的 batch 大小混淆"
               "因素，上面已对该组做出标注。_")
    return "\n".join(out)


def render_section17(lanes, now):
    items = [l for l in lanes.values()
             if not (l["steps"] is None and l["last_write"] is None and l["start"] is None)]
    items = sorted(items, key=lambda l: (l["n"] or 0, l["exp"]))
    for l in items:
        l["status"] = classify(l)
    rows = []
    for l in items:
        rows.append([l["exp"],
                     first_not_none(l["scale"], f"{l['n']}v{l['n']}" if l["n"] else "-"),
                     fmt_int(l["threads"]), fmt_int(l["steps"]), fmt_int(l["ceiling"]),
                     l["status"], lane_status_note(l, l["status"], now)])
    for na in NOT_APPLICABLE:
        if na["exp"] not in lanes:
            rows.append([na["exp"], "1v1", "3", "-", "-", "not_applicable", na["note"]])
    body = [
        "本实验批次全部通道在生成本区块时的状态、已到步数，以及任何缺口的"
        "原因。`Status` 恰好取以下之一：completed_6M | completed_at_ceiling | "
        "running | time_cutoff | failed | not_applicable。仍在写入的通道为 "
        "`running`；未达自身上限但无崩溃特征的通道按实际步数记为 "
        "`time_cutoff`；退出码不作为成功证据（§13.4）。",
        "",
        md_table(["实验", "规模", "Rollout 线程", "已到步数", "上限",
                  "状态", "说明"], rows),
        "",
        "_上限即通道自身的可达预算：runner 向下取整 "
        "`episodes = 6e6//3000//threads`，因此 3-thread 通道封顶 5,994,000"
        "（F17），4/8/10/20-thread 通道恰好到达 6,000,000。`running` 通道的"
        "「已到步数」为实时值；之后的 freeze 会覆盖本表，auto-finalizer 每次"
        "快照都会写入一份（`status/final_state_history.md`）。_",
    ]
    if len(items) == 0:
        body.append("")
        body.append("_完全没有找到通道产物 —— 本实验批次的 status.json、"
                    "summary.csv 与队列台账均为空。_")
    return "\n".join(body)


# --------------------------------------------------------------------- apply

def apply_sections(text, rendered):
    """Replace each marker-pair body; insert the pair if it is missing.

    rendered: list of (sid, body).  Returns (new_text, messages).
    """
    messages = []
    rendered_map = dict(rendered)

    for sid, body in rendered:
        opener, closer = f"<!-- AUTO:{sid} -->", f"<!-- /AUTO:{sid} -->"
        no, nc = text.count(opener), text.count(closer)
        if no != nc or no > 1:
            return None, [f"{sid}: found {no} opener(s) / {nc} closer(s) -- "
                          f"refusing to rewrite an ambiguous region"]

    def _sub(m):
        body = rendered_map.get(m.group("sid"))
        if body is None:
            return m.group(0)
        return f"<!-- AUTO:{m.group('sid')} -->\n{body}\n<!-- /AUTO:{m.group('sid')} -->"

    text = AUTO_RE.sub(_sub, text)

    for sid, body in rendered:
        if f"<!-- AUTO:{sid} -->" in text:
            continue
        # Safety net: the marker pair is absent (e.g. someone removed it).
        # Insert it directly after the section heading; any old body text below
        # is left where it is and flagged, so nothing is silently destroyed.
        prefix = SECTION_HEADINGS.get(sid, "")
        lines = text.splitlines(keepends=True)
        idx = next((i for i, ln in enumerate(lines) if ln.startswith(prefix)), None)
        if idx is None:
            messages.append(f"{sid}: no marker pair and no heading starting "
                            f"with {prefix!r} -- skipped")
            continue
        block = ["\n", f"<!-- AUTO:{sid} -->\n", body + "\n", f"<!-- /AUTO:{sid} -->\n"]
        lines[idx + 1:idx + 1] = block
        text = "".join(lines)
        messages.append(f"{sid}: marker pair was missing -- inserted after the heading "
                        f"(check that no stale hand-written body remains below it)")
    return text, messages


def atomic_write(path, text):
    tmp = path.with_name(path.name + ".fill_report.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


# ---------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign-root", default=None,
                    help="campaign that is read (default: derived from this file's location)")
    ap.add_argument("--report", default=None,
                    help="report file to rewrite in place (default: <repo>/docs/"
                         "formal_repro_scaling_2026-10-07_08.md)")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the report differs from what would be generated")
    args = ap.parse_args(argv)

    camp = (Path(args.campaign_root).expanduser().resolve()
            if args.campaign_root else DEFAULT_CAMPAIGN)
    report = (Path(args.report).expanduser().resolve()
              if args.report else DEFAULT_REPORT)

    now = time.time()
    mdir = camp / "metrics"

    lanes = build_lanes(camp, now)

    # campaign-wide resource peaks from scaling_table.csv (fallback labels).
    # The CPU column name carries the quota it was measured against
    # (peak_busy_cores_of_48_quota), so it is matched by prefix, not by name.
    camp_peaks = {"cpu_cores": None, "ram_gb": None, "vram_mb": None}
    for r in read_csv_rows(mdir / "scaling_table.csv"):
        for k, v in r.items():
            if k.startswith("peak_busy_cores"):
                x = fnum(v)
                if x is not None:
                    camp_peaks["cpu_cores"] = max(camp_peaks["cpu_cores"] or 0, x)
            elif k == "peak_ram_gb_host":
                x = fnum(v)
                if x is not None:
                    camp_peaks["ram_gb"] = max(camp_peaks["ram_gb"] or 0, x)
            elif k == "peak_vram_mb_host":
                x = fnum(v)
                if x is not None:
                    camp_peaks["vram_mb"] = max(camp_peaks["vram_mb"] or 0, x)

    equal_sample_rows = read_csv_rows(mdir / "equal_sample.csv")
    equal_wall_rows = read_csv_rows(mdir / "equal_wallclock.csv")
    sample_rows = read_csv_rows(mdir / "sample_efficiency.csv")
    norm_rows = read_csv_rows(mdir / "normalized_scaling.csv")

    sections = [
        ("section5", render_section5(lanes, now)),
        ("section6", render_section6(lanes, camp_peaks, now)),
        ("section7", render_equal_section(
            equal_sample_rows, [1_000_000, 2_000_000, 3_000_000, 4_000_000,
                                5_000_000, 6_000_000],
            ["1M", "2M", "3M", "4M", "5M", "6M"], "equal_sample")),
        ("section8", render_equal_section(
            equal_wall_rows, [1, 3, 6, 12, 24],
            ["1h", "3h", "6h", "12h", "24h"], "equal_wallclock")),
        ("section11", render_section11(lanes, sample_rows, norm_rows)),
        ("section12", render_section12(lanes)),
        ("section17", render_section17(lanes, now)),
    ]

    try:
        original = report.read_text()
    except OSError as e:
        print(f"fill_report: cannot read report {report}: {e}", file=sys.stderr)
        return 2

    new_text, messages = apply_sections(original, sections)
    if new_text is None:
        for m in messages:
            print(f"fill_report: ERROR {m}", file=sys.stderr)
        return 2

    print(f"fill_report: campaign={camp}")
    print(f"fill_report: report  ={report}")
    for sid, body in sections:
        print(f"  {sid:9s}: {len(body.splitlines())} lines")
    for m in messages:
        print(f"  note: {m}")

    if new_text == original:
        print("fill_report: report already up to date (no content change)")
    if args.check:
        print("fill_report: --check: " + ("IN SYNC" if new_text == original else "OUT OF SYNC"))
        return 0 if new_text == original else 1
    atomic_write(report, new_text)
    print(f"fill_report: wrote {report} ({len(new_text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
