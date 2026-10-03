#!/usr/bin/env python
"""Figures for the overnight reproduction + scaling study.

Colour policy (see the dataviz skill):
  * categorical series use the reference palette's fixed slot order, never
    cycled; slots 1-4 in order are the documented-validated set for the
    *adjacent* pairlist, which is the correct pairlist for line charts;
  * identity is never colour-alone: every series also carries a distinct dash
    pattern and a direct end-label;
  * one axis per panel -- FPS / CPU / RAM / VRAM each get their own panel
    rather than a second y-axis;
  * sequential (magnitude) uses the single-hue blue ramp, light->dark.

The skill's `validate_palette.js` could not be executed here (no `node` on this
box), so the palette is taken as documented rather than re-validated.

Everything is driven from metrics/summary.csv and metrics/curves/*.csv, which
collect_metrics.py regenerates from on-disk artefacts, so this is safe to run
while training continues.
"""
import csv
import glob
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

REPO = "/root/autodl-tmp/SEU-SRTP"
EXP = os.path.join(REPO, "experiments/2026-10-04-night")
FIG = os.path.join(EXP, "figures")
CURVES = os.path.join(EXP, "metrics/curves")
METRICS = os.path.join(EXP, "metrics")

os.makedirs(FIG, exist_ok=True)

# reference palette, categorical slots in fixed order
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8983"
GRID = "#e3e2de"
DASH = ["-", "--", ":", "-."]

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
    "axes.titlesize": 12,
    "axes.titleweight": "600",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "figure.dpi": 140,
})


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def label_for(exp):
    """Map an experiment id to a short human label."""
    m = re.search(r"scaling_(\d+v\d+)_noweapon(_s(\d))?", exp)
    if m:
        s = f" (seed {m.group(3)})" if m.group(3) else ""
        return f"{m.group(1)} scaling{s}"
    m = re.search(r"scaling_(\d+v\d+)_shoot", exp)
    if m:
        return f"{m.group(1)} scaling (shoot)"
    if exp.startswith("official_"):
        return "official " + exp[len("official_"):]
    return exp


def load_curves():
    out = {}
    for p in sorted(glob.glob(os.path.join(CURVES, "*.csv"))):
        rows = read_csv(p)
        if not rows:
            continue
        out[os.path.basename(p)[:-4]] = rows
    return out


def curve_xy(rows, xkey):
    xs, ys = [], []
    t0 = fnum(rows[0].get("wall_time")) if rows else None
    for r in rows:
        y = fnum(r.get("average_episode_rewards"))
        if y is None:
            continue
        if xkey == "steps":
            x = fnum(r.get("total_num_steps"))
        else:
            wt = fnum(r.get("wall_time"))
            x = (wt - t0) / 60.0 if (wt is not None and t0 is not None) else None
        if x is None:
            continue
        xs.append(x)
        ys.append(y)
    return xs, ys


def fig_learning_curves(curves, xkey, fname, xlabel, title):
    """One panel per family, no dual axis. Series = team size."""
    families = {
        "NoWeapon (generated scaling family)": [
            e for e in curves if re.search(r"scaling_\d+v\d+_noweapon$", e)],
        "ShootMissile (generated scaling family)": [
            e for e in curves if re.search(r"scaling_\d+v\d+_shoot$", e)],
        "Official baselines": [
            e for e in curves if e.startswith("official_")],
    }
    def sort_key(s):
        m = re.search(r"(\d+)v\d+", s)
        return (0, int(m.group(1))) if m else (1, 0)

    have = {k: sorted(v, key=sort_key) for k, v in families.items() if v}
    if not have:
        return
    n = len(have)
    fig, axes = plt.subplots(1, n, figsize=(5.6 * n, 4.1), squeeze=False)
    for ax, (name, exps) in zip(axes[0], have.items()):
        handles = []
        for i, e in enumerate(exps):
            xs, ys = curve_xy(curves[e], xkey)
            if not xs:
                continue
            c = CAT[i % 4]
            ax.plot(xs, ys, color=c, lw=2, ls=DASH[i % 4], label=label_for(e),
                    marker="o", ms=3.5, markevery=max(1, len(xs) // 14))
            handles.append(Line2D([], [], color=c, lw=2, ls=DASH[i % 4], label=label_for(e)))
        ax.set_xlabel(xlabel)
        ax.set_ylabel("average episode reward")
        ax.set_title(name)
        if handles:
            ax.legend(handles=handles, loc="best", fontsize=8)
    fig.suptitle(title, fontsize=13, fontweight="600", y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(FIG, fname), bbox_inches="tight")
    plt.close(fig)
    print("wrote", fname)


def _fmt_num(y):
    if y is None:
        return ""
    if abs(y) >= 10000:
        return f"{y:,.0f}"
    if abs(y) >= 100:
        return f"{y:,.0f}"
    if abs(y) >= 1:
        return f"{y:.2f}".rstrip("0").rstrip(".")
    return f"{y:.3g}"


def _panel(ax, xs, ys, xlabel, ylabel, title, color=None, annotate=True, series=None):
    if series is None:
        ax.plot(xs, ys, color=color or CAT[0], lw=2, marker="o", ms=6)
    else:
        for i, (lbl, yy) in enumerate(series):
            ax.plot(xs, yy, color=CAT[i % 4], lw=2, ls=DASH[i % 4], marker="o", ms=6, label=lbl)
        ax.legend(fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(xs)
    if annotate:
        # stagger the labels so adjacent points with close values do not collide
        ymax = max(v for v in ys if v is not None)
        ax.margins(y=0.18)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if y is None:
                continue
            dy = 9 if i % 2 == 0 else -16
            ax.annotate(_fmt_num(y), (x, y), textcoords="offset points",
                        xytext=(0, dy), ha="center", fontsize=8, color=INK2,
                        va="bottom" if dy > 0 else "top")


def fig_scaling_dashboards():
    """Analytic dimension + measured compute scaling. One axis per panel."""
    probe_path = os.path.join(METRICS, "critic_scaling.json")
    bench_path = os.path.join(METRICS, "env_bench_scaling.json")
    if not os.path.exists(probe_path):
        return
    probe = json.load(open(probe_path))
    ex = {e["team_size"]: e for e in probe["extrapolated"]}

    N = [2, 3, 5, 10]
    obs = [ex[n]["obs_dim"] for n in N]
    share = [ex[n]["share_obs_dim"] for n in N]
    cparam = [ex[n]["critic_first_layer_params"] for n in N]
    macs = [ex[n]["critic_first_layer_MAC_per_envstep"] for n in N]
    buf = [ex[n]["share_obs_buffer_GB"] for n in N]

    bench = {}
    if os.path.exists(bench_path):
        b = json.load(open(bench_path))
        bench = {"quiet": {r["team_size"]: r for r in b.get("quiet", [])},
                 "loaded": {r["team_size"]: r for r in b.get("loaded", [])}}

    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.2))
    axes = axes.ravel()

    _panel(axes[0], N, obs, "team size N", "dimension",
           "Local observation dim  = 12N + 3")
    _panel(axes[1], N, share, "team size N", "dimension",
           "Centralised critic input dim  = 24N$^2$ + 6N")
    _panel(axes[2], N, cparam, "team size N", "parameters",
           "Critic first-layer parameters  = O(N$^2$)")
    _panel(axes[3], N, macs, "team size N", "MACs per env step",
           "Critic first-layer compute per env step  = O(N$^3$)")
    _panel(axes[4], N, buf, "team size N", "GB (buffer_size=3000, T=12)",
           "share_obs replay buffer  = O(N$^3$)")

    ax = axes[5]
    if bench.get("quiet"):
        xs = sorted(bench["quiet"])
        q = [bench["quiet"][n]["sec_per_env_step"] * 1000 for n in xs]
        ax.plot(xs, q, color=CAT[0], lw=2, marker="o", ms=6,
                label="idle machine (intrinsic)")
        ref = [q[0] * (n / xs[0]) ** 1.7 for n in xs]
        ax.plot(xs, ref, color=CAT[2], lw=2, ls=":", label=r"$O(N^{1.7})$ reference")
        if bench.get("loaded"):
            l = [bench["loaded"][n]["sec_per_env_step"] * 1000 for n in xs]
            ax.plot(xs, l, color=CAT[1], lw=2, ls="--", marker="s", ms=5,
                    label="under 5 concurrent queues")
        ax.set_xlabel("team size N")
        ax.set_ylabel("ms per env step (single core)")
        ax.set_title("JSBSim env-step cost")
        ax.set_xticks(xs)
        ax.legend(fontsize=8)
    else:
        ax.axis("off")

    fig.suptitle("Representation and compute scaling of LAG 2v2 -> 10v10 "
                 "(measured N<=10, extrapolated beyond)",
                 fontsize=13, fontweight="600", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(FIG, "scaling_dimensions.png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote scaling_dimensions.png")


def fig_resources():
    """FPS / CPU / RAM / VRAM vs team size, measured. One axis per panel."""
    rows = []
    if os.path.exists(os.path.join(METRICS, "summary.csv")):
        rows = read_csv(os.path.join(METRICS, "summary.csv"))
    res = {}
    for r in rows:
        m = re.search(r"scaling_(\d+)v\d+_noweapon$", r["experiment"])
        if not m:
            continue
        n = int(m.group(1))
        fps = fnum(r.get("fps_last"))
        if fps:
            res.setdefault(n, []).append(fps)
    if not res:
        return
    N = sorted(res)
    fps = [sum(res[n]) / len(res[n]) for n in N]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1))
    _panel(axes[0], N, fps, "team size N", "training FPS (env-steps/s)",
           "Throughput per job (measured)")
    # throughput normalised per aircraft -- shows the superlinear cost
    ax = axes[1]
    ys = [f / (2 * n) for f, n in zip(fps, N)]
    ax.plot(N, ys, color=CAT[1], lw=2, marker="o", ms=6)
    ax.set_xlabel("team size N")
    ax.set_ylabel("env-steps/s per aircraft")
    ax.set_title("Throughput per aircraft (cost of scaling)")
    ax.set_xticks(N)
    for x, y in zip(N, ys):
        ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                    xytext=(0, 7), ha="center", fontsize=8, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "throughput_vs_agents.png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote throughput_vs_agents.png")


def fig_normalized_critic():
    """Reward-scale normalisation, and the residual critic effect it exposes.

    Three panels, one axis each: reward/N (should be flat if the normalisation
    is right), value_loss/N^2 and grad_norm/N (what is left after removing the
    trivial reward-scale growth).
    """
    path = os.path.join(METRICS, "normalized_scaling.csv")
    if not os.path.exists(path):
        return
    rows = read_csv(path)
    if not rows:
        return
    by_n = {}
    for r in rows:
        by_n.setdefault(int(r["team_size"]), []).append(r)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    panels = [
        ("reward_per_enemy", "reward / N", "Reward per enemy (flat => scale is exactly O(N))"),
        ("value_loss_per_N2", "value loss / N$^2$", "Critic loss, reward-scale removed"),
        ("critic_grad_norm_per_N", "critic grad norm / N", "Critic gradient, reward-scale removed"),
    ]
    Ns = sorted(by_n)
    for ax, (key, ylab, title) in zip(axes, panels):
        for i, n in enumerate(Ns):
            rs = sorted(by_n[n], key=lambda r: int(r["episode"]))
            xs = [int(r["episode"]) for r in rs]
            ys = [fnum(r[key]) for r in rs]
            if any(y is None for y in ys):
                continue
            ax.plot(xs, ys, color=CAT[i % 4], lw=2, ls=DASH[i % 4], marker="o", ms=6,
                    label=f"{n}v{n}")
        ax.set_xlabel("PPO episode (matched training stage)")
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.set_xticks(sorted({int(r["episode"]) for r in rows}))
    fig.suptitle("Centralised critic scaling after removing the reward-magnitude confound "
                 "(hierarchical NoWeapon family only)",
                 fontsize=13, fontweight="600", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(FIG, "critic_normalized_scaling.png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote critic_normalized_scaling.png")


def fig_resource_scaling():
    """Per-experiment CPU cores and RSS vs team size, plus per-rollout-thread cost.

    Sourced from metrics/resources.csv, which sweep.sh samples from /proc while
    the runs are live. Values are peaks over the observed samples, so they
    describe what the run actually demanded, not a synthetic benchmark.
    """
    path = os.path.join(METRICS, "resources.csv")
    if not os.path.exists(path):
        return
    rows = read_csv(path)
    peak = {}
    for r in rows:
        e = r["experiment"]
        m = re.search(r"scaling_(\d+)v\d+_noweapon", e)
        if not m:
            continue
        n = int(m.group(1))
        cpu = fnum(r["cpu_pct"])
        rss = fnum(r["rss_gb"])
        if cpu is None:
            continue
        cur = peak.setdefault(n, [0.0, 0.0, 0.0])
        cur[0] = max(cur[0], cpu / 100.0)      # cores
        cur[1] = max(cur[1], rss or 0.0)       # GB
    if not peak:
        return
    Ns = sorted(peak)
    cores = [peak[n][0] for n in Ns]
    rss = [peak[n][1] for n in Ns]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    _panel(axes[0], Ns, cores, "team size N", "CPU cores (of 48)",
           "CPU demand per job (measured peaks)")
    _panel(axes[1], Ns, rss, "team size N", "RSS (GB)",
           "Process RSS per job (measured peaks)")
    # VRAM is flat across N -- show it so the flatness is on the record
    vram = {}
    for r in rows:
        m = re.search(r"scaling_(\d+)v\d+_noweapon", r["experiment"])
        if not m:
            continue
        v = fnum(r["gpu_vram_mb"])
        if v is not None:
            vram[int(m.group(1))] = max(vram.get(int(m.group(1)), 0.0), v)
    if vram:
        vs = sorted(vram)
        _panel(axes[2], vs, [vram[n] for n in vs], "team size N", "GPU VRAM (MB)",
               "Peak VRAM on the run's GPU (shared)")
    else:
        axes[2].axis("off")
    fig.suptitle("Per-job resource demand vs team size (peaks over live samples)",
                 fontsize=13, fontweight="600", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(os.path.join(FIG, "resource_scaling.png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote resource_scaling.png")


def main():
    curves = load_curves()
    # exclude smoke / metrics-test runs from the figures
    curves = {k: v for k, v in curves.items()
              if not k.startswith(("SMOKE", "METRICS_TEST"))}
    if curves:
        fig_learning_curves(curves, "steps", "learning_curves_steps.png",
                            "environment steps (vectorised)", "Learning curves: reward vs environment steps")
        fig_learning_curves(curves, "time", "learning_curves_walltime.png",
                            "wall-clock (minutes)", "Learning curves: reward vs wall-clock (compute-normalised view)")
    fig_scaling_dashboards()
    fig_normalized_critic()
    fig_resource_scaling()
    fig_resources()
    print(f"\nfigures in {FIG}")


if __name__ == "__main__":
    main()
