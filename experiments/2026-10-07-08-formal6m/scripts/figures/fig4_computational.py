#!/usr/bin/env python3
"""Figure 4 - computational scalability of the formal 6M campaign (2x2 panel).

Panels
------
A  Training throughput: per-run median of the curves-CSV ``fps`` column vs
   total agents.  Every point is labelled with its rollout thread count, and
   the pilot idle-machine single-environment benchmark (quiet group of
   env_bench_scaling.json, 2026-10-04-night) x that run's rollout threads is
   drawn as a grey no-contention ceiling.  The per-env benchmark is converted
   to run level (x threads) because a training fps counts env steps across all
   rollout threads - the raw per-env number would not be comparable and would
   visually cross the run points at some sizes.
B  Wall-clock hours to the first logged episode at/above 1,000,000 env steps:
   curves-CSV ``wall_time`` of that row minus the first row's ``wall_time``.
C  Peak CPU% / RSS / VRAM per run from metrics/resources.csv, as three stacked
   sub-axes - the three quantities have different units and never share a
   y-axis.  ``cpu_pct`` comes from the sampler whose host-wide /proc/stat
   reading was falsified (F16): unreliable, relative context only.
D  Per-step cost decomposition (simulation / observation construction / state
   construction / other residual) per team size from the pilot's
   obs_cost_profile.json - an independent profiling measurement, not sampled
   during training.

Population: the eight scaling runs plus the official single-agent heading
control (N=1).  The four official 1v1 combat runs (3 rollout threads, a
different experiment family) are deliberately not mixed into this panel; the
caption says so.  Colour is team size everywhere (style.PALETTE, via
style.color_for_n); every number is read from disk - no interpolation, no
extrapolation, no smoothing (nothing here is a time series).

Smoothing note: this figure contains no learning curves, so the 250,000-env-step
rolling window of the curve figures does not apply here.

Run via make_all.py (``build(camp, out_dir)``) or directly:
    python3 fig4_computational.py
"""

from __future__ import annotations

import statistics as st
import textwrap
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

import style
import data

# --------------------------------------------------------------------------
# layout - delivered through fig.add_axes so save()'s tight_layout() never
# reflows the custom stacked panels (nested gridspecs are not handled by it)
# --------------------------------------------------------------------------
FIG_SIZE = (12.4, 8.6)
COL_L, COL_R, COL_GAP = 0.062, 0.988, 0.075
ROW1_BOTTOM, ROW1_H = 0.585, 0.345     # panels A / B
ROW2_BOTTOM, ROW2_H = 0.170, 0.290     # panels C / D
CAPTION_FONTSIZE = 8.0                 # long caveat block; style default is 8.5
CAPTION = (
    "Panels A-C: the 8 scaling runs + the official single-agent heading control (N=1); the four official 1v1 combat runs (3 threads, a separate "
    "experiment family) are omitted. Rollout threads differ per run (4 / 8 / 8-10 / 20) and the campaign shared one 48-core box (~5 concurrent queues), "
    "so points are not an equal-compute comparison; point labels give seed and rollout threads. Three of the nine runs are partial "
    "(5.4M / 2.3M / 1.86M steps), the rest reached 6M. A: per-run median of the fps column (log scale); grey = pilot idle-machine single-env benchmark x "
    "that run's threads (a no-contention ceiling, not a training run; measured under 5-queue load the benchmark drops to 57-84% of idle). B: wall_time of "
    "the first episode at/above 1M steps minus the first logged row (undercounts by up to one episode). C: peaks over 4-32 samples per run; cpu_pct comes "
    "from the host-wide /proc/stat sampler (F16) - relative only, not container-accurate. D: independent pilot profiling, not sampled during training; "
    "'other' is the unaccounted residual (full_step_ms minus sim + obs + state); share labels above bars = (get_obs + get_state)/full_step."
)


def _wrap(text, fontsize=CAPTION_FONTSIZE, fig_w_in=FIG_SIZE[0]):
    """Hard-wrap the caption to the figure width (text does not auto-wrap in
    matplotlib; an overlong line silently widens the saved tight bbox)."""
    max_chars = max(40, int((fig_w_in - 0.35) * 72.0 / (0.56 * fontsize)))
    return "\n".join(textwrap.wrap(text, max_chars))

# run labels ("s0" = seed 0, "(Nt)" = rollout threads); never the full ids
def _short_label(exp):
    meta = data.RUN_META[exp]
    if meta["env"] == "SingleControl":
        return f"Heading ({meta['threads']}t)"
    return f"s{meta['seed']} ({meta['threads']}t)"


def _ordered_runs():
    """Scaling runs + the heading control, sorted by (team size, seed)."""
    exps = list(data.runs_of("scaling")) + ["f6m_official_heading_s5"]
    return sorted(exps, key=lambda e: (data.RUN_META[e]["n"], data.RUN_META[e]["seed"]))


def _dodge(exps):
    """x-offset per run so equal-N points do not sit exactly on top of each
    other (x keeps its meaning: total agents, 2N)."""
    by_n = {}
    for exp in exps:
        by_n.setdefault(data.RUN_META[exp]["n"], []).append(exp)
    off = {}
    for n, group in by_n.items():
        group = sorted(group, key=lambda e: data.RUN_META[e]["seed"])
        for i, exp in enumerate(group):
            off[exp] = (i - (len(group) - 1) / 2.0) * 0.62
    return off


def _color(exp):
    meta = data.RUN_META[exp]
    if meta["env"] == "SingleControl":
        return style.color_for_family("single_control")
    return style.color_for_n(meta["n"])


def _point_label(ax, x, y, text, color, *, side="right", fontsize=8.5,
                 dx_pt=6.0, leader_lw=0.8):
    """Direct-label a scatter point, the scatter analogue of
    style.add_end_label: the text sits beside (x, y) and is pushed *down in
    axes-fraction steps* (correct on log axes too) until it clears every label
    already placed on this axes; a hairline leader is drawn whenever it had to
    move, so the label never detaches from its point.  Placement history lives
    on the axes (``_ptlabel_boxes``)."""
    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    bb = ax.get_window_extent(rend)
    px_per_pt = fig.dpi / 72.0
    w_pt, h_pt = bb.width / px_per_pt, bb.height / px_per_pt
    x0d, x1d = ax.get_xlim()
    x_per_pt = (x1d - x0d) / w_pt
    y_frac = ax.transAxes.inverted().transform(
        ax.transData.transform((x, y)))[1]
    gap = fontsize * 1.55 / h_pt            # min vertical separation
    est_w = 0.56 * fontsize * len(text) * x_per_pt
    if side == "right":
        xa, xb, dx = x + dx_pt * x_per_pt, x + dx_pt * x_per_pt + est_w, dx_pt
    else:
        xa, xb, dx = x - dx_pt * x_per_pt - est_w, x - dx_pt * x_per_pt, -dx_pt
    placed = ax.__dict__.setdefault("_ptlabel_boxes", [])
    yy = y_frac
    for _ in range(200):
        if not any(xa < b and a < xb and abs(yy - p) < gap
                   for a, b, p in placed):
            break
        yy -= gap
    if yy < 0.015:
        yy = 0.015
    placed.append((xa, xb, yy))
    dy_pt = (yy - y_frac) * h_pt
    moved = abs(dy_pt) > 3.0
    return ax.annotate(
        text, xy=(x, y), xytext=(dx, dy_pt), textcoords="offset points",
        ha="left" if side == "right" else "right", va="center",
        fontsize=fontsize, color=color, annotation_clip=False,
        arrowprops=(dict(arrowstyle="-", color=color, lw=leader_lw,
                         shrinkA=1.5, shrinkB=3.5) if moved else None))


def _size_ticks(ax, *, labels=True):
    """Shared x ticks for panels A-C: total agents, annotated with the task."""
    ax.set_xticks([2, 4, 6, 10, 20])
    if labels:
        ax.set_xticklabels(["2\n1v1", "4\n2v2", "6\n3v3", "10\n5v5",
                            "20\n10v10"])
    else:
        ax.set_xticklabels(["2", "4", "6", "10", "20"])


def _rows_for(curves, exp):
    return curves[exp]


# --------------------------------------------------------------------------
# panels
# --------------------------------------------------------------------------
def _panel_a(ax, curves, exps, off):
    """A. median fps per run vs total agents, with the idle-machine ceiling."""
    bench = {int(r["team_size"]): float(r["env_steps_per_s"])
             for r in data.load_env_bench()["quiet"]}
    meta = data.RUN_META

    # grey ceiling line through the seed-0 run of every size that has a bench
    ceil_line = [(2 * meta[e]["n"], bench[meta[e]["n"]] * meta[e]["threads"])
                 for e in exps
                 if meta[e]["n"] in bench and meta[e]["seed"] == 0]
    ceil_line.sort()
    neutral = style.color_for_family("neutral")
    ax.plot([p[0] for p in ceil_line], [p[1] for p in ceil_line],
            color=neutral, lw=style.SMOOTH_LW, zorder=2,
            label="idle-machine ceiling (bench x threads)")
    seen = set()
    for e in exps:                    # one square per (N, threads) - deduped
        n, threads = meta[e]["n"], meta[e]["threads"]
        if n in bench:
            seen.add((2 * n, bench[n] * threads))
    for x, yv in sorted(seen):
        ax.plot([x], [yv], marker="s", ms=5.5, mfc="none", mec=neutral,
                mew=1.3, ls="none", zorder=3)

    # coloured run points + per-point labels (seed, threads)
    pts = []
    for e in exps:
        fps = [r["fps"] for r in curves[e] if r.get("fps") is not None]
        pts.append((2 * meta[e]["n"] + off[e], st.median(fps), e))
    for x, y, e in pts:
        ax.plot([x], [y], marker="o", ms=6.0, mfc=_color(e), mec="white",
                mew=0.9, ls="none", zorder=4)
    ax.set_xlim(0.4, 21.6)
    ax.set_yscale("log")
    ax.set_ylim(48, 640)
    ax.set_yticks([60, 80, 100, 150, 200, 300, 400, 600])
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    ax.set_ylabel("env steps / s  (whole run, log scale)")
    _size_ticks(ax)
    for x, y, e in sorted(pts, key=lambda p: -p[1]):    # top-down placement
        side = "left" if meta[e]["n"] == 10 else "right"
        _point_label(ax, x, y, _short_label(e), _color(e), side=side)
    ax.legend(loc="upper right", frameon=False)
    ax.set_title("A. Training throughput vs team size", loc="left")


def _panel_b(ax, curves, exps, off):
    """B. wall-clock hours to the first logged episode at/above 1M steps."""
    meta = data.RUN_META
    pts = []
    for e in exps:
        rows = _rows_for(curves, e)
        t0 = rows[0]["wall_time"]
        hit = next((r for r in rows if r["total_num_steps"] >= 1_000_000),
                   None)
        if hit is None:
            continue                     # never reached 1M - plot nothing
        pts.append((2 * meta[e]["n"] + off[e], (hit["wall_time"] - t0) / 3600.0,
                    e))
    for x, y, e in pts:
        ax.plot([x], [y], marker="o", ms=6.0, mfc=_color(e), mec="white",
                mew=0.9, ls="none", zorder=4)
    ax.set_xlim(0.4, 21.6)
    ax.set_ylim(0.75, 5.25)
    ax.set_ylabel("wall-clock hours to 1M env steps")
    ax.set_xlabel("total agents (2N)")
    _size_ticks(ax)
    for x, y, e in sorted(pts, key=lambda p: -p[1]):
        side = "left" if meta[e]["n"] == 10 else "right"
        _point_label(ax, x, y, _short_label(e), _color(e), side=side)
    ax.set_title("B. Time to first 1M env steps", loc="left")
    ax.text(0.985, 0.05, "x at the first logged episode >= 1M (1.008-1.02M)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5,
            color=style.CAPTION_COLOR)


def _panel_c(fig, cell, exps, off):
    """C. peak CPU% / RSS / VRAM - three stacked sub-axes, own y each."""
    x0, y0, w, h = cell
    meta = data.RUN_META
    res = data.load_resources()
    peaks = {}                             # exp -> (cpu, rss, vram)
    for e in exps:
        rows = [r for r in res if r["experiment"] == e]
        peaks[e] = (
            max((r["cpu_pct"] for r in rows if r.get("cpu_pct") is not None),
                default=None),
            max((r["rss_gb"] for r in rows if r.get("rss_gb") is not None),
                default=None),
            max((r["gpu_vram_mb"] for r in rows
                 if r.get("gpu_vram_mb") is not None), default=None),
        )

    gap = 0.018
    hs = (h - 2 * gap) / 3.0
    axes = []
    for i, key in enumerate(("cpu", "rss", "vram")):
        ax = fig.add_axes([x0, y0 + (2 - i) * (hs + gap), w, hs])
        axes.append(ax)
    specs = [
        ("cpu", "CPU %",
         "unreliable: sampler read host-wide /proc/stat (F16) - relative only"),
        ("rss", "RSS (GB)", None),
        ("vram", "VRAM (MB)", None),
    ]
    for ax, (key, ylab, note) in zip(axes, specs):
        for e in exps:
            val = peaks[e][{"cpu": 0, "rss": 1, "vram": 2}[key]]
            if val is None:
                continue
            ax.plot([2 * meta[e]["n"] + off[e]], [val], marker="o", ms=5.5,
                    mfc=_color(e), mec="white", mew=0.8, ls="none", zorder=3)
        ax.set_ylabel(ylab, fontsize=10)
        ax.set_xlim(0.4, 21.6)
        ax.set_xticks([2, 4, 6, 10, 20])
        ax.tick_params(labelbottom=False)      # only the bottom axis shows x
        if note:
            ax.text(0.015, 0.88, note, transform=ax.transAxes, ha="left",
                    va="top", fontsize=7.6,
                    color=style.color_for_family("neutral"))
    axes[0].set_yticks([0, 600, 1200, 1800])
    axes[1].set_yticks([0, 5, 10, 15])
    axes[2].set_yticks([0, 400, 800, 1200])
    axes[0].set_title("C. Peak resource use per run (sampled)", loc="left")
    axes[0].text(0.985, 0.04, "peak over 4-32 samples/run",
                 transform=axes[0].transAxes, ha="right", va="bottom",
                 fontsize=8.5, color=style.CAPTION_COLOR)
    axes[-1].tick_params(labelbottom=True)
    axes[-1].set_xticklabels(["2\n1v1", "4\n2v2", "6\n3v3", "10\n5v5",
                              "20\n10v10"])
    axes[-1].set_xlabel("total agents (2N)", fontsize=10)
    return axes


def _panel_d(ax):
    """D. per-step cost decomposition from the pilot's obs_cost_profile.

    ``data.load_obs_cost`` keeps its default campaign (2026-10-04-night): the
    profiling was measured there, not in this campaign, so a ``--camp``
    override must not redirect it.
    """
    prof = sorted(data.load_obs_cost(), key=lambda r: int(r["team_size"]))
    if not prof:
        raise RuntimeError(
            "obs_cost_profile.json not found under the pilot campaign - "
            "panel D has no data (see data.PILOT_CAMPAIGN)")
    ns = [int(r["team_size"]) for r in prof]
    sim = [float(r["sim_run_ms"]) for r in prof]
    obs = [float(r["get_obs_all_ms"]) for r in prof]
    stt = [float(r["get_state_ms"]) for r in prof]
    full = [float(r["full_step_ms"]) for r in prof]
    other = [f - a - b - c for f, a, b, c in zip(full, sim, obs, stt)]
    share = [float(r["obs_share_of_step_pct"]) for r in prof]
    colors = [style.color_for_n(n) for n in ns]
    xs = list(range(len(prof)))
    segs = [
        (sim, "", "simulation"),
        (obs, "///", "observation construction"),
        (stt, "\\\\", "state construction"),
        (other, "..", "other (unaccounted)"),
    ]
    bottom = [0.0] * len(prof)
    for vals, hatch, label in segs:
        ax.bar(xs, vals, 0.62, bottom=bottom, color=colors, hatch=hatch,
               edgecolor=colors, lw=0.9, zorder=3)
        bottom = [b + v for b, v in zip(bottom, vals)]
    for x, tot, sh in zip(xs, bottom, share):
        ax.text(x, tot + 4.5, f"{sh:.1f}%", ha="center", va="bottom",
                fontsize=9.5, color="#333333")
    ax.set_ylim(0, 212)
    ax.set_xlim(-0.55, len(prof) - 0.45)
    ax.set_xticks(xs)
    ax.set_xticklabels(["2v2\n(4)", "3v3\n(6)", "5v5\n(10)", "10v10\n(20)"])
    ax.set_ylabel("ms per environment step")
    ax.set_xlabel("team size (total agents)")
    patches = [plt.Rectangle((0, 0), 1, 1, facecolor=style.color_for_family(
        "neutral"), edgecolor=style.color_for_family("neutral"), lw=0.9,
        hatch=hatch) for _v, hatch, _l in segs]
    ax.legend(patches, [l for _v, _h, l in segs], loc="upper left",
              frameon=False, handlelength=1.7, borderaxespad=0.5,
              title="segments (hatch)", title_fontsize=9.5)
    ax.text(0.42, 0.74, "bar colour = team size\n"
                        "labels above bars = obs-path share\n"
                        "of full step (obs + state)",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.2,
            color=style.CAPTION_COLOR)
    ax.set_title("D. Per-step cost breakdown (pilot profiling)", loc="left")


# --------------------------------------------------------------------------
# entry point (contract for make_all.py)
# --------------------------------------------------------------------------
def build(camp=None, out_dir=None):
    camp = Path(camp) if camp else data.CAMPAIGN
    style.apply_style()
    plt.rcParams["hatch.linewidth"] = 0.7

    curves = data.load_curves(camp)
    exps = _ordered_runs()
    off = _dodge(exps)

    w = (COL_R - COL_L - COL_GAP) / 2.0
    col = [(COL_L, w), (COL_L + w + COL_GAP, w)]
    fig = plt.figure(figsize=FIG_SIZE)

    ax_a = fig.add_axes([col[0][0], ROW1_BOTTOM, col[0][1], ROW1_H])
    ax_b = fig.add_axes([col[1][0], ROW1_BOTTOM, col[1][1], ROW1_H])
    _panel_a(ax_a, curves, exps, off)
    _panel_b(ax_b, curves, exps, off)
    _panel_c(fig, (col[0][0], ROW2_BOTTOM, col[0][1], ROW2_H), exps, off)
    ax_d = fig.add_axes([col[1][0], ROW2_BOTTOM, col[1][1], ROW2_H])
    _panel_d(ax_d)

    cap = style.caption(fig, _wrap(CAPTION), fontsize=CAPTION_FONTSIZE)
    # guard: matplotlib never wraps text, and an over-wide caption silently
    # widens the saved tight bbox (the first render of this figure was 18.1 in
    # wide because of it) - fail loudly instead of shipping that
    fig.canvas.draw()
    cap_w_in = cap.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi
    assert cap_w_in <= FIG_SIZE[0] - 0.1, (
        f"caption is {cap_w_in:.2f} in wide, figure is {FIG_SIZE[0]} in - "
        "wrap it shorter (see _wrap)")
    # every axes here is placed with add_axes, so style.save()'s tight_layout()
    # is a no-op for them; silence the "not compatible with tight_layout"
    # warning it would otherwise emit for manually positioned axes
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*not compatible with "
                                                 "tight_layout.*")
        return [style.save(fig, "fig4_computational", out_dir=out_dir)]


if __name__ == "__main__":
    for p in build():
        print(p)
