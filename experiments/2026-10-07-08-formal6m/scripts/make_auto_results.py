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

# 收尾型回溯（不是崩溃）。run_train.sh 用 `timeout -k 60 -s INT` 包住训练进程，
# 到点发 SIGINT，于是日志里必然留下 KeyboardInterrupt 回溯；主进程随后在
# envs.close() 里再抛 EOFError（与 F9 同型的连带异常）。
# 这两者都是**正常收尾**的签名，必须与真正的崩溃区分，否则一个跑到预算上限
# 才被时间上限停掉的通道会被误标成 `failed`。
TEARDOWN_EXC = ("KeyboardInterrupt", "EOFError")
# 出现其中任何一个都说明是真崩溃，而非收尾
REAL_CRASH_HINTS = ("TypeError", "AttributeError", "ValueError", "RuntimeError",
                    "KeyError", "IndexError", "AssertionError", "MemoryError",
                    "CUDA error", "out of memory", "NotImplementedError")


def teardown_only_traceback(log_path):
    """日志里的回溯是否**全部**是 SIGINT 收尾签名（无真崩溃迹象）。

    返回 True 表示"有回溯，但那是被时间上限停掉的正常收尾"，调用方应记为
    time_cutoff；返回 False 表示无法排除真崩溃，调用方应记为 failed。
    """
    if not log_path or not os.path.exists(log_path):
        return False
    try:
        txt = read_text(log_path)
    except OSError:
        return False
    if "Traceback (most recent call last)" not in txt:
        return False
    if any(h in txt for h in REAL_CRASH_HINTS):
        return False
    return any(e in txt for e in TEARDOWN_EXC)

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
        return "缺失"


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
            status, flags = "not_applicable", ["该通道未找到任何数据"]
        elif trace and not nan and not inf and teardown_only_traceback(g(s, "log_path")):
            # 有回溯，但只是 `timeout -s INT` 的收尾签名：按 time_cutoff 记，
            # 不按 failed 记（否则被时间上限停掉的通道会被误报成崩溃）。
            status = "time_cutoff" if not done else (
                "completed_6M" if (steps is not None and steps >= TARGET) else "completed_at_ceiling")
            flags = ["被时间上限停掉（SIGINT 收尾回溯，非崩溃）"]
        elif trace or nan or inf:
            if done:
                status = "completed_6M" if (steps is not None and steps >= TARGET) else "completed_at_ceiling"
                flags = ["健康标志被触发"]
            else:
                status, flags = "failed", ["日志或指标中有崩溃/健康证据"]
        elif done:
            if steps is not None and steps >= TARGET:
                status, flags = "completed_6M", []
            else:
                status, flags = "completed_at_ceiling", []
        elif stalled:
            status = "time_cutoff"
            flags = [f"{age:.0f} 分钟无日志写入" if isinstance(age, (int, float)) else "中途停止"]
        else:
            status, flags = "running", []
        if isinstance(age, (int, float)) and age > STALL_MIN and status == "running":
            flags.append(f"静默 {age:.0f} 分钟")
        if nan:
            flags.append("NaN")
        if inf:
            flags.append("Inf")
        if trace and status != "failed":
            flags.append("Traceback in log")
        if ceil is not None and (j or {}).get("achievable") is not None:
            try:
                if int((j or {}).get("achievable")) != ceil:
                    flags.append("上限不一致（计算值 vs watcher）")
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
        ckpt, ckpt_state = g(m, "checkpoint_path"), "manifest 记录"
        if run_dir:
            found = None
            for cand in ("actor_latest.pt", "actor_0.pt"):
                p = Path(run_dir) / cand
                if p.exists():
                    found = p
                    break
            if found is not None:
                ckpt, ckpt_state = str(found), "已在磁盘上"
            elif ckpt:
                ckpt_state = "manifest 路径（磁盘上未见该文件）"
            else:
                ckpt = str(Path(run_dir) / "actor_latest.pt")
                ckpt_state = "尚未写入"

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
    out = ["## 状态词表与预算规则", "",
           "状态恰好为六个值之一，由本脚本按以下规则从 watcher 自身的标志"
           "（`metrics/status.json`）推导（与监控所用规则一致）：", "",
           "| 状态 | 含义 |", "|---|---|",
           "| `completed_6M` | 跑满 6,000,000 预算。 |",
           "| `completed_at_ceiling` | 到达自身可达上限，该上限低于 6,000,000（仅 3-thread 通道）。 |",
           "| `running` | 仍在写入：日志在 watcher 的 30 分钟停滞阈值内更新。 |",
           "| `time_cutoff` | 未达上限即停止，且无崩溃证据（挂钟时间上限，或日志静默 > 30 分钟）。 |",
           "| `failed` | 观测到 Traceback / NaN / Inf。 |",
           "| `not_applicable` | 该通道未找到任何数据。 |", "",
           "runner 向下取整 `episodes = num_env_steps // 3000 // n_rollout_threads`"
           "（事件 F17），因此通道的可达上限为 "
           "`(6e6 // 3000 // threads) * 3000 * threads`。本实验批次实际出现的"
           "线程数对应的上限：", "",
           "| threads | episodes | 可达上限 |", "|---|---|---|"]
    seen = sorted({l["threads"] for l in lanes if l["threads"]}, key=int)
    for t in seen:
        c = ceiling_of(t)
        out.append(f"| {t} | {TARGET // BUFFER // int(t)} | {f_int(c)} |")
    out += ["",
            "`reward_per_enemy`（reward / team_size）**仅**对 NoWeapon 系列是"
            "可跨 N 比较的量（PostureReward 对每个 agent 的敌机求和）。"
            "此处对 ShootMissile 系列一律不给出。", "",
            "Pilot（2026-10-04）与 formal（6M）是两条独立序列，绝不合并。", ""]
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
    out = ["## 数据来源与新鲜度", "",
           "本文档中的每个数字都在生成时刻从这些机器产物读取。来源文件比表格"
           "更新，意味着表格只是快照而非实时状态；实时状态永远是下面的清单表"
           "（由 `metrics/status.json` 构建）。", "",
           "| 来源 | 最近写入 |", "|---|---|"]
    for rel, _ in rows:
        out.append(f"| `{rel}` | {mtime_str(camp / rel)} |")
    out.append("")
    return out


def sec_inventory(lanes, st, st_ts):
    out = ["## 实验清单（所有通道）", ""]
    if st_ts is not None:
        age_min = (datetime.now() - st_ts).total_seconds() / 60.0
        out.append(f"来自 `metrics/status.json` 的实时视图（时间戳 {st_ts:%Y-%m-%d %H:%M:%S}；"
                   f"本文件生成前 {age_min:.1f} 分钟）。")
        if age_min > STALL_MIN:
            out.append(f"**警告**：watcher 快照已过期 {age_min:.0f} 分钟 —— "
                       "下方的存活标志可能已过时。")
    else:
        out.append("`metrics/status.json` 不可用 —— 下方状态改由 "
                   "`metrics/summary.csv` / `manifest.csv` 推导。")
    out += ["", "| 实验 | 场景 | 算法 | 种子 | threads | 可达上限 | 步数 | % 上限 | 状态 | FPS | 挂钟时间 | 标志 |",
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
    out.append(f"共 {len(lanes)} 条通道合计：已完成 **{total_steps:,} env steps / "
               f"可达 {total_ceiling:,}**（快照）；全批次实时聚合吞吐 "
               f"**{raw(agg)} env-steps/s**。")
    out += ["", "### Checkpoint", "", "| 实验 | 最新 checkpoint | 状态 |", "|---|---|---|"]
    for l in lanes:
        out.append(f"| `{l['exp']}` | `{cell(l['ckpt'])}` | {cell(l['ckpt_state'])} |")
    out.append("")
    return out


def sec_scaling(camp):
    rows = read_csv_rows(camp / "metrics" / "scaling_table.csv")
    out = ["## scaling 表（reward 与每敌机 reward）", ""]
    if not rows:
        out += ["_不可用 —— `metrics/scaling_table.csv` 缺失或为空。_", ""]
        return out
    out.append(f"快照：`metrics/scaling_table.csv`（写入于 {mtime_str(camp / 'metrics' / 'scaling_table.csv')}）。"
               "`reward_per_enemy = train_reward_last / team_size`，在本脚本内计算，"
               "仅对 NoWeapon 系列输出。")
    out += ["", "| 规模 | 变体 | 种子 | thr | 步数（快照） | FPS | 训练 reward（最后） | 每敌机 reward | eval reward（最后） | 尾段斜率 |",
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
            "按既定口径，任何 ShootMissile 行的 `reward_per_enemy` 一律显示为 `n/a`。"
            "官方基线通道不属于本表（它们是独立序列；见清单）。", ""]
    return out


BUDGET_MARK = {"interp": "*", "cross": "†", "before-data": "§", "nan-gap": "§"}


def render_budget_tables(camp, fname, title, blurb):
    rows = read_csv_rows(camp / "metrics" / fname)
    out = [f"## {title}", ""]
    if not rows:
        out += [f"_不可用 —— `metrics/{fname}` 缺失或为空。_", ""]
        return out
    budgets = []
    for col in rows[0].keys():
        m = re.match(r"reward@(.+)$", col)
        if m:
            budgets.append(m.group(1))
    out += [blurb, "",
            f"快照：`metrics/{fname}`（写入于 {mtime_str(camp / 'metrics' / fname)}）。"
            "`—` = pending（该快照时尚未达到该预算）；`*` = 在相邻 update 之间"
            "插值；`†` = 首次跨过；`§` = before-data / nan-gap。"
            "逐格原始状态与区间见 CSV 本身。", ""]

    def table(prefix, label, withhold_shoot):
        out_l = [f"**{label}**", "", "| 实验 | 种子 | " + " | ".join(budgets) + " |",
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
            out_l += ["_该快照时没有任何通道达到这些预算；所有单元格均为 pending，"
                      "未做任何外推。_", ""]
        return out_l

    out += table("reward", "reward", False)
    out += table("reward_per_enemy", "每敌机 reward（reward / team_size；仅 NoWeapon 系列 —— "
                 "ShootMissile 为 `n/a`）", True)
    return out


def sec_representation(camp):
    data = read_json(camp / "metrics" / "critic_scaling.json")
    out = ["## 表征 / critic scaling（实测 vs 外推）", ""]
    if not data:
        out += ["_不可用 —— `metrics/critic_scaling.json` 缺失或无法读取。_", ""]
        return out
    measured = data.get("measured", []) or []
    extrapolated = data.get("extrapolated", []) or []
    anchored = [e for e in extrapolated if str(e.get("note", "")).strip() == "measured"]
    beyond = [e for e in extrapolated if str(e.get("note", "")).strip() != "measured"]

    out += [f"来源：`metrics/critic_scaling.json`（写入于 "
            f"{mtime_str(camp / 'metrics' / 'critic_scaling.json')}）；probe = 在真实网络"
            "上构建模型，不做训练。三张表绝不混用：(1) 四个实测点，"
            "(2) 由这些实测值推导的量，(3) 超出实测范围的预测。", "",
            "### 1. 实测行（N = 2, 3, 5, 10）", "",
            "| N | agents | obs 维度 | share obs 维度 | actor 参数量 | critic 参数量 | critic 首层参数量 | 首层 MAC/envstep | fwd ms（batch） | fwd ms（固定 256） | bwd ms（固定 256） | fwd µs/样本 |",
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
                 "| N | agents | obs 维度 | share obs 维度 | critic 首层参数量 | 首层 MAC/envstep | 估计 fwd ms/envstep | share-obs 缓冲区 GB |",
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

    out += extra_table(anchored, "2. 由实测点推导（不是新的测量）",
                       f"由同样的 N = {', '.join(str(r.get('team_size')) for r in anchored)} "
                       "的 probe 运行计算得到；此处的首层数值与表 1 完全相同，"
                       "并在下方核对。不要把这本表当作独立证据。")
    out += extra_table(beyond, "3. 超出实测范围的外推（仅为预测）",
                       f"N = {', '.join(str(r.get('team_size')) for r in beyond)} 从未被实测"
                       "（probe 只构建了上面四个网络）。这些行是基于模型的预测，"
                       "绝不能与实测混用 —— 也不能当作实测引用。")

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
    out += ["### 解析式核对（在本脚本中计算，非断言）", "",
            "每行：`share_obs = 24N² + 6N`，`critic_params = 128·(24N²+6N) + 150145`，"
            "`critic_first_layer_params = 128·(share_obs + 1)`。", "",
            "| 量 | 记录值 | 解析式 | 是否一致 |", "|---|---|---|---|"]
    for name, rec, calc in checks:
        match = "—" if (rec in (None, "") or calc is None) else ("一致" if abs(float(rec) - float(calc)) < 0.5 else "**不一致**")
        out.append(f"| {cell(name)} | {f_int(rec)} | {f_int(calc)} | {match} |")
    out += ["", f"全部解析式核对通过：**{'是' if ok else '否 —— 见不一致的行'}**。"
            f"Probe 元数据：device `{raw(data.get('device'))}`，"
            f"effective G-MAC/s {raw(data.get('effective_G_MAC_per_s'))}，"
            f"batch threads {raw(data.get('batch_threads'))}。", ""]
    return out


def sec_computational(camp, st):
    rows = read_csv_rows(camp / "metrics" / "scaling_table.csv")
    out = ["## 计算可扩展性", ""]
    if not rows:
        out += ["_不可用 —— `metrics/scaling_table.csv` 缺失或为空。_", ""]
        return out
    out += [f"快照：`metrics/scaling_table.csv`（写入于 "
            f"{mtime_str(camp / 'metrics' / 'scaling_table.csv')}）。`FPS` 为 runner 自身的 "
            "vectorised env-steps/s；`agent-steps/s = env-steps/s × 总 agent 数`。", "",
            "| 规模 | 变体 | thr | FPS（env-steps/s） | 每线程 env-steps/s | agent-steps/s | 每线程 agent-steps/s | 秒 / vectorised step | 秒 / rollout episode（3000 步） |",
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
    out += ["", f"`metrics/status.json` 快照时全批次实时聚合吞吐："
            f"全部活跃通道合计 **{raw(agg)} env-steps/s**。", ""]
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
    out = ["## 失败清单（摘自 `status/incidents.md`）", ""]
    items = parse_incidents(camp / "status" / "incidents.md")
    if not items:
        out += ["_不可用 —— `status/incidents.md` 缺失或无法读取。_", ""]
    else:
        cats = Counter((it["category"] or "?").split("(")[0].strip() for it in items)
        out += [f"本实验批次共记录 {len(items)} 起事件 "
                f"（{', '.join(f'{c}: {n}' for c, n in sorted(cats.items()))}）。"
                "F1–F9 位于 `docs/night_failures.md`，属于 2026-10-04 pilot；"
                "此处不再重复列出。", "",
                "| id | 标题 | 类别 | 发现时间 | 摘要（症状/原因节选） |",
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
    out += [f"本快照的实时健康标志：NaN ×{n_nan}，Inf ×{n_inf}，"
            f"traceback ×{n_tb}；状态为 `failed` 的通道：{n_failed} 条。", ""]
    return out


def sec_limitations(lanes):
    out = ["## 本文档不展示的内容", "",
           "已知局限；引用上面任何数字之前请先阅读本节。", ""]

    groups = {}
    for l in lanes:
        groups.setdefault(l["scenario"], set()).add(str(l["seed"]))
    multi = sorted(k for k, v in groups.items() if len(v) > 1)
    single = sorted(k for k, v in groups.items() if len(v) <= 1)
    out += ["1. **大多数规模只有一个种子。** 目前只有下列场景拥有多于一个种子；"
            "其余场景均为单种子结果。小于运行间种子离散度的跨规模（或跨种子）"
            "差异不可解释，本文档也不做这类比较。",
            f"   - 目前多种子：{', '.join(f'`{k}`' for k in multi) if multi else '无'}",
            f"   - 本次生成时为单种子：{', '.join(f'`{k}`' for k in single) if single else '无'}", ""]

    thr_groups = {}
    for l in lanes:
        thr_groups.setdefault(l["scenario"], set()).add(l["threads"])
    confound = sorted(k for k, v in thr_groups.items() if len(v) > 1)
    out += ["2. **`n_rollout_threads` 是混淆因素，不是细节。** 线程数在各规模间"
            "不同（受挂钟时间所迫：固定线程数时 10v10 无法在窗口内到达 6M），"
            "且 PPO update 的 batch 大小为 `threads × 3000`，因此 batch 大小"
            "也随规模不同。"]
    thr_line = ", ".join(
        f"`{k}`: {sorted(int(t) for t in v if t)} thr（batch {sorted(int(t) * BUFFER for t in v if t)}）"
        for k, v in sorted(thr_groups.items()))
    out += [f"   - 本次生成时各场景的线程数：{thr_line}",
            (f"   - **同场景内跨种子的差异**："
             f"{', '.join(f'`{k}`' for k in confound)} —— 该处的种子比较同样"
             f"被线程数混淆。") if confound else
            "   - 目前没有场景在其种子之间混用不同线程数。", ""]

    capped = [l for l in lanes if l["ceiling"] and l["ceiling"] < TARGET]
    ceil3 = ceiling_of(3)
    out += ["3. **1v1 通道按构造无法到达 6,000,000。** "
            f"3-thread 通道向下取整到 {TARGET // BUFFER // 3} 个 episode，即名义 "
            f"{f_int(TARGET)} 中的 {f_int(ceil3)}（事件 F17）。这些通道记为 "
            "`completed_at_ceiling`，而不是被截断。",
            (f"   - 本次生成时受影响的通道："
             f"{', '.join(f'`{l['exp']}`' for l in capped)}") if capped else
            "   - 目前没有通道因构造原因低于名义预算。", ""]

    shoot_lanes = [l for l in lanes if l["shoot"]]
    sib = [l for l in lanes if l["threads"] == 3 and not l["shoot"] and l["fps"] not in (None, "")]
    fps_line = ""
    if shoot_lanes and sib:
        try:
            sf = max(float(x["fps"]) for x in shoot_lanes if x["fps"] not in (None, ""))
            others = sorted(f"{float(x['fps']):g}" for x in sib if x["fps"] not in (None, ""))
            fps_line = (f"   - 当前 FPS：ShootMissile {sf:g}，同类 3-thread 1v1 通道为 "
                        f"{', '.join(others)} env-steps/s（见清单）。")
        except (TypeError, ValueError):
            fps_line = ""
    out += ["4. **1v1 ShootMissile 通道带 `--use-prior` 运行，吞吐约减半**"
            "（事件 F14，类别 `Computational scalability` —— 不是算法问题）。"
            "其较低的 FPS 是官方代码路径的性质，不是算法发现。", fps_line, ""]

    out += ["5. **6M 是预算缩减，不是收敛结果。** 官方配置训练 1e8 步；"
            f"本批次只跑 {f_int(TARGET)}（为其 {100.0 * TARGET / 1e8:.0f}%）。"
            "最终 reward 是训练中途状态的快照，绝不能当作已收敛的性能来呈现。", "",
            "另外，按既定口径：", "",
            "- `reward_per_enemy` 只对 NoWeapon 系列有定义"
            "（PostureReward 对 agent 求和）；ShootMissile 行一律不给出。",
            "- 2026-10-04 pilot 是独立序列，不包含在本文档中。",
            "- 由分析 CSV 构建的表格只是那些文件的快照（mtime 见上）；"
            "只有清单是实时视图。本文档不做跨种子平均、拟合或显著性检验。",
            "- 本文档是数据记录，不是分析；请结合手写报告解读。", ""]
    return out


def sec_artefacts(camp):
    return ["## 相关产物（未内嵌到本文档）", "",
            "- `metrics/scaling_table.csv` —— 上表 scaling 表的机器可读版本，列更全（obs 维度、参数量、CPU/RAM 峰值）。",
            "- `metrics/normalized_scaling.csv` —— scaling 系列的逐 episode reward 与每敌机 reward。",
            "- `metrics/sample_efficiency.csv` —— 至 6M 各固定预算下的 reward / 每敌机 reward。",
            "- `metrics/equal_sample.csv`、`metrics/equal_wallclock.csv` —— 带逐格状态与区间的原始 checkpoint 表。",
            "- `metrics/resources.csv`、`metrics/throughput_history.csv`、`system/system_samples_v2.csv` —— 资源/吞吐时间序列（v1 采样文件的 CPU 换算不可靠；见事件 F16）。",
            "- `figures/` —— 由 `scripts/make_figures.py` 重新生成的图。",
            "- `docs/formal_repro_scaling_2026-10-07_08.md` —— 本文档作为其安全网的手写报告。",
            ""]


# ------------------------------------------------------------------ main

def generate(camp, out_path, repo):
    now = datetime.now()
    lanes, st, st_ts = build_inventory(camp, now)
    gi = git_info(repo)

    L = []
    L += [f"# Formal-6M 自动结果 —— 机器生成的数值记录", "",
          f"> **本文件由机器生成，请勿手改。** 生成于 "
          f"**{now:%Y-%m-%d %H:%M:%S} {now.astimezone().tzname()}** "
          f"（{now.astimezone().isoformat(timespec='seconds')}），"
          f"由 `experiments/2026-10-07-08-formal6m/scripts/make_auto_results.py` "
          f"生成（repo HEAD `{gi['head']}`，分支 `{gi['branch']}`）。所有数字均来自机器产物。", ">",
          f"> 实验批次：`experiments/2026-10-07-08-formal6m`。重新生成："
          f"`cd experiments/2026-10-07-08-formal6m && /root/miniconda3/envs/jsbsim/bin/python scripts/make_auto_results.py` "
          f"（`scripts/freeze.sh` 也会调用它，tmux auto-finalizer 按计划运行 freeze.sh）。", ">",
          "> 下方每个数值都读取自 *数据来源与新鲜度* 一节列出的文件；没有任何手工"
          "填入的值，除某行明确说明外也不做任何外推。若手写报告最终未能完成，"
          "本文档就是完整的数值记录。", ""]

    sections = [
        ("Conventions", lambda: sec_conventions(lanes)),
        ("Sources", lambda: sec_sources(camp)),
        ("Inventory", lambda: sec_inventory(lanes, st, st_ts)),
        ("Scaling", lambda: sec_scaling(camp)),
        ("EqualSample", lambda: render_budget_tables(
            camp, "equal_sample.csv", "等样本对比",
            "固定 vectorised env-step 预算（1M–6M）下的 reward 与每敌机 reward，"
            "来自本批次自带的等样本生成器。")),
        ("EqualWallclock", lambda: render_budget_tables(
            camp, "equal_wallclock.csv", "等挂钟时间对比",
            "固定挂钟时间预算（1h–24h）下的 reward 与每敌机 reward，"
            "来自本批次自带的等挂钟时间生成器。")),
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
            L += [f"sections/{name}: _不可用 —— 生成器错误："
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
