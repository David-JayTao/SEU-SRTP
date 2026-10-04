#!/usr/bin/env python
"""Emit paste-ready markdown tables for the report, refreshed each sweep.

Writing these mechanically at the end of the night is how the report gets final
numbers without transcription errors, and it means an interrupted final assembly
still has the tables on disk.
"""
import csv
import os
import re
import subprocess
import sys

EXP = "/root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night"
METRICS = os.path.join(EXP, "metrics")
OUT = os.path.join(METRICS, "report_tables.md")


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def g(v, nd=4):
    try:
        return f"{float(v):.{nd}g}"
    except (TypeError, ValueError):
        return "-" if v in (None, "") else str(v)


def baseline_table():
    rows = [r for r in read_csv(os.path.join(METRICS, "summary.csv"))
            if r["experiment"].startswith(("official_", "scaling_"))]
    # one row per experiment, newest log wins
    seen = {}
    for r in rows:
        seen[r["experiment"]] = r
    order = sorted(seen, key=lambda e: (not e.startswith("official_"), e))
    out = ["| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |",
           "|---|---|---|---|---|---|---|"]
    for e in order:
        r = seen[e]
        try:
            done, tgt = int(r["steps_done"]), int(r["steps_target"])
            # A run that fell short of its target did so because its wall-clock
            # cap expired, not because it is still going -- all queues have
            # drained. Say that rather than "running".
            status = "已完成 (达到步数预算)" if done >= tgt else "已结束 (墙钟上限截断)"
        except (TypeError, ValueError):
            status = "未启动"
        if r.get("crashed") == "True":
            status = "**失败 (见 F9)**"
        ck = "yes" if r.get("checkpoint_path") else "no"
        out.append(f"| `{e}` | {status} | {r.get('steps_done','-')}/{r.get('steps_target','-')} "
                   f"| {g(r.get('fps_last'),5)} | {g(r.get('train_reward_first'),4)} → {g(r.get('train_reward_last'),4)} "
                   f"| {g(r.get('eval_reward_last'),5)} | {ck} |")
    return "\n".join(out)


def resources_table():
    rows = read_csv(os.path.join(METRICS, "resources.csv"))
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


def main():
    try:
        scaling = subprocess.run(
            [sys.executable, os.path.join(EXP, "scripts/scaling_table.py")],
            capture_output=True, text=True, cwd="/root/autodl-tmp/SEU-SRTP").stdout
    except Exception as e:
        scaling = f"(scaling_table failed: {e})"

    try:
        norm = subprocess.run(
            [sys.executable, os.path.join(EXP, "scripts/normalized_scaling.py")],
            capture_output=True, text=True, cwd="/root/autodl-tmp/SEU-SRTP").stdout
    except Exception as e:
        norm = f"(normalized_scaling failed: {e})"

    parts = [
        "# 报告表格快照（自动生成，勿手改）",
        "",
        "由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。",
        "",
        "## A. Baseline 复现与缩放实验状态",
        "",
        baseline_table(),
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
        resources_table(),
        "",
    ]
    with open(OUT, "w") as f:
        f.write("\n".join(parts) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
