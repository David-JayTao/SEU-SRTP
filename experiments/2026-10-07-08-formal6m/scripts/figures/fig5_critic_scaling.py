#!/usr/bin/env python3
"""Figure 5 - centralised-critic scalability of the formal 6M campaign (2x2).

Panels
------
A  Observation dimensions vs team size N: the local (per-agent) obs dim and
   the shared (joint) obs dim on two stacked sub-axes.  The shared vector is
   20x the local one at N=10, so a single shared y-axis would flatten the
   local curve to nothing - different magnitudes never share a y-axis.
   Measured markers lie exactly on the closed-form curves obs = 12N+3 and
   share_obs = 24N^2+6N (exact at N=2/3/5/10).
B  Critic parameters vs N with the actor overlay (both are architecture
   counts): the critic closed form 128*(24N^2+6N) + 150,145 is exact at the
   four measured N; the actor grows ~8% over the same range.
C  Critic first-layer MACs (multiply-accumulates) per environment step =
   128 * share_obs * 12N - a hockey stick, asymptotically ~N^3 (log-log
   inset confirms the slope).
D  Distribution of ``critic_grad_norm_per_N`` (= critic_grad_norm / N, per
   team size) grouped by N, as boxplots, from metrics/normalized_scaling.csv
   rows with label 'scaling noweapon' only (the official 2v2 family is not
   mixed in).  Measured N=2/3/5/10 only.

Population / provenance: metrics/critic_scaling.json measured rows only - the
N=20/50/100 extrapolated rows in the same file are never plotted; panel D
reads metrics/normalized_scaling.csv.  Every number comes from disk; there is
no interpolation, no extrapolation and no smoothing (nothing here is a time
series, so the 250,000-env-step window of the curve figures does not apply).
Colour roles use style.PALETTE hues: local/actor quantities are the N=2 blue,
shared/critic quantities the N=10 vermillion, guides and notes grey.

The caption states the diagnostic-not-causal limit: larger dimensions /
parameter counts / MACs are architectural facts and do NOT by themselves
demonstrate critic learning difficulty or a curse of multiagency.

Run via make_all.py (``build(camp, out_dir)``) or directly:
    python3 fig5_critic_scaling.py
"""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter

import style
import data

# --------------------------------------------------------------------------
# layout - fig.add_axes so that every panel keeps its exact position; panel A
# is a pair of stacked sub-axes inside the top-left cell
# --------------------------------------------------------------------------
FIG_SIZE = (12.0, 8.7)
COL_L, COL_R, COL_GAP = 0.062, 0.988, 0.075
ROW1_BOTTOM, ROW1_H = 0.585, 0.345     # panels A / B
# bottom row sits a little higher than in fig4 so the long caption never
# touches its two-line tick labels + xlabel (guarded in build())
ROW2_BOTTOM, ROW2_H = 0.190, 0.270     # panels C / D
CAPTION_FONTSIZE = 7.8                 # long caveat block; style default 8.5

# role colours, taken from style.PALETTE (never invented inside a figure)
C_LOCAL = style.color_for_n(2)                  # local obs / actor  (#0072B2)
C_SHARED = style.color_for_n(10)                # shared obs / critic (#D55E00)
C_NOTE = style.CAPTION_COLOR                    # grey annotations

NS_MEASURED = (2, 3, 5, 10)   # measured rows only in this whole figure

CAPTION = (
    "Panels A-C: critic_scaling.json measured rows only (N=2/3/5/10); the N=20/50/100 extrapolated rows are NOT plotted. Probe: one pass per model "
    "(cuda:0, batch_threads=12, batch_rows=12N); the closed forms are exact at the four measured N. N = agents per team; total agents = 2N. "
    "A: local and shared obs dims on separate y-axes; shared is 20x local at N=10. B: the critic head reads share_obs, the actor reads local obs. "
    "C: first-layer MACs (multiply-accumulates) per env step = 128 x share_obs x 12N, ~N^3 asymptotically (inset: log-log). "
    "D: normalized_scaling.csv rows labelled 'scaling noweapon' only (official 2v2 family excluded, not mixed); y = critic_grad_norm / N (per team size, "
    "not per agent) over 500/500/526/131 episodes pooled across 1/2/3/2 seeds; boxes = per-episode median / IQR / 1.5-IQR whiskers, dots beyond - an "
    "episode distribution, not a confidence interval; N=10 seed 1 and 5v5 seeds 1-2 were still running, so those boxes may shift. No smoothing applies "
    "(no time series). All panels are diagnostic: growth in dims / parameters / MACs is an architectural property and does NOT by itself show critic "
    "learning difficulty or a curse of multiagency; that claim needs controlled critic-variant experiments, not run this round."
)


def _wrap(text, fontsize=CAPTION_FONTSIZE, fig_w_in=FIG_SIZE[0]):
    """Hard-wrap the caption to the figure width (mpl never auto-wraps; an
    overlong line silently widens the saved tight bbox).  The 0.62 factor is
    the measured average width of DejaVu Sans at these sizes (0.56 under-
    estimated it and produced a caption taller than the reserved band)."""
    max_chars = max(40, int((fig_w_in - 0.35) * 72.0 / (0.62 * fontsize)))
    return "\n".join(textwrap.wrap(text, max_chars))


# closed forms, annotated in the panels and drawn over N in [2, 10].  They are
# exact at every measured N (verified against critic_scaling.json).
def _local_dim(n):
    return 12.0 * n + 3.0


def _shared_dim(n):
    return 24.0 * n ** 2 + 6.0 * n


def _critic_params(n):
    return 128.0 * _shared_dim(n) + 150_145.0


def _mac_per_step(n):
    return 128.0 * _shared_dim(n) * 12.0 * n   # batch_rows = 12N


def _measured_rows(camp):
    """Sorted measured rows of critic_scaling.json; hard-fails when the file
    does not hold the expected four measured team sizes."""
    rows, _extrapolated = data.load_critic(camp)
    rows = sorted(rows, key=lambda r: int(r["team_size"]))
    ns = [int(r["team_size"]) for r in rows]
    if ns != list(NS_MEASURED):
        raise RuntimeError(
            f"critic_scaling.json measured rows have team sizes {ns}, "
            f"expected {list(NS_MEASURED)} - refusing to plot")
    return rows


def _end_label(ax, x, y, text, color, *, fontsize=9.5, dx=7.0, va="center"):
    """Short direct label pinned to the right of a line's last point."""
    return ax.annotate(text, xy=(x, y), xytext=(dx, 0),
                       textcoords="offset points", ha="left", va=va,
                       fontsize=fontsize, color=color, annotation_clip=False)


def _plain_ticks(ax, ticks):
    """Fixed y ticks with plain (non-scientific, non-offset) labels."""
    ax.set_yticks(ticks)
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.minorticks_off()


def _size_ticks(ax, *, show_labels=True, with_xlabel=False):
    """The shared x convention: team size N at measured 2 / 3 / 5 / 10, with
    two-line labels carrying the NvN short name."""
    ax.set_xlim(1.5, 11.8)
    ax.set_xticks(list(NS_MEASURED))
    if show_labels:
        ax.set_xticklabels([f"{n}\n{n}v{n}" for n in NS_MEASURED])
    else:
        ax.tick_params(labelbottom=False)
    if with_xlabel:
        ax.set_xlabel("team size N (agents per side)")


# --------------------------------------------------------------------------
# panels
# --------------------------------------------------------------------------
def _panel_a(fig, cell, rows):
    """Local vs shared observation dim - two stacked sub-axes (never one
    shared y-axis: the shared vector is 20x the local one at N=10)."""
    x0, y0, w, h = cell
    gap = 0.034
    top_h = 0.152
    bot_h = h - top_h - gap
    ax_top = fig.add_axes([x0, y0 + bot_h + gap, w, top_h])
    ax_bot = fig.add_axes([x0, y0, w, bot_h])

    ns = np.array([r["team_size"] for r in rows], dtype=float)
    local = np.array([r["obs_dim"] for r in rows], dtype=float)
    shared = np.array([r["share_obs_dim"] for r in rows], dtype=float)
    nline = np.linspace(NS_MEASURED[0], NS_MEASURED[-1], 200)

    ax_top.plot(nline, _local_dim(nline), color=C_LOCAL, lw=1.8, zorder=3)
    ax_top.plot(ns, local, "o", ms=6.5, mfc=C_LOCAL, mec="white", mew=0.9,
                zorder=4)
    _end_label(ax_top, float(ns[-1]), float(local[-1]), "12N+3", C_LOCAL)
    ax_top.set_ylim(0, 148)
    _plain_ticks(ax_top, [0, 30, 60, 90, 120])
    ax_top.set_ylabel("local obs dim (per agent)")
    _size_ticks(ax_top, show_labels=False)
    ax_top.set_title("A. Observation dimensions vs team size", loc="left")
    ratio = float(shared[-1] / local[-1])
    ax_top.text(0.035, 0.97,
                f"shared joint obs (panel below) = {ratio:.0f}x local at N=10",
                transform=ax_top.transAxes, ha="left", va="top",
                fontsize=8.5, color=C_NOTE)

    ax_bot.plot(nline, _shared_dim(nline), color=C_SHARED, lw=1.8, zorder=3)
    ax_bot.plot(ns, shared, "o", ms=6.5, mfc=C_SHARED, mec="white", mew=0.9,
                zorder=4)
    _end_label(ax_bot, float(ns[-1]), float(shared[-1]), "24N²+6N", C_SHARED)
    ax_bot.set_ylim(0, 2850)
    _plain_ticks(ax_bot, [0, 500, 1000, 1500, 2000, 2500])
    ax_bot.set_ylabel("shared obs dim (joint)")
    _size_ticks(ax_bot, show_labels=True)
    return ax_top, ax_bot


def _panel_b(ax, rows):
    """Critic parameters vs N, actor params overlaid (both in thousands)."""
    ns = np.array([r["team_size"] for r in rows], dtype=float)
    critic = np.array([r["critic_params"] for r in rows], dtype=float) / 1e3
    actor = np.array([r["actor_params"] for r in rows], dtype=float) / 1e3
    nline = np.linspace(NS_MEASURED[0], NS_MEASURED[-1], 200)

    ax.plot(nline, _critic_params(nline) / 1e3, color=C_SHARED, lw=1.8,
            zorder=3)
    ax.plot(ns, critic, "o", ms=6.5, mfc=C_SHARED, mec="white", mew=0.9,
            zorder=4)
    ax.plot(ns, actor, ls="--", lw=1.6, color=C_LOCAL, marker="s", ms=6.0,
            mfc=C_LOCAL, mec="white", mew=0.9, zorder=4)
    _end_label(ax, float(ns[-1]), float(critic[-1]), "critic", C_SHARED)
    _end_label(ax, float(ns[-1]), float(actor[-1]), "actor", C_LOCAL)

    ax.set_ylim(133, 505)
    _plain_ticks(ax, [150, 200, 250, 300, 350, 400, 450, 500])
    ax.set_ylabel("parameters (thousands)")
    _size_ticks(ax, show_labels=True)
    ax.set_title("B. Critic and actor parameters vs team size", loc="left")
    ax.text(0.035, 0.97,
            "critic = 128·(24N²+6N) + 150,145\nexact at the 4 measured N",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5,
            color=C_NOTE)
    growth = float(actor[-1] / actor[0] - 1.0)
    ax.text(0.44, 0.20,
            f"actor: local obs input only, ~+{growth * 100:.0f}% over N=2-10",
            transform=ax.transAxes, ha="left", va="center", fontsize=8.2,
            color=C_NOTE)


def _panel_c(ax, rows):
    """Critic first-layer MACs per env step (hockey stick) + log-log inset."""
    ns = np.array([r["team_size"] for r in rows], dtype=float)
    mac = np.array([r["critic_first_layer_MAC_per_envstep"] for r in rows],
                   dtype=float) / 1e6
    nline = np.linspace(NS_MEASURED[0], NS_MEASURED[-1], 200)

    ax.plot(nline, _mac_per_step(nline) / 1e6, color=C_SHARED, lw=1.8,
            zorder=3)
    ax.plot(ns, mac, "o", ms=6.5, mfc=C_SHARED, mec="white", mew=0.9,
            zorder=4)
    ax.set_ylim(0, 43.5)
    _plain_ticks(ax, [0, 10, 20, 30, 40])
    ax.set_ylabel("first-layer MACs per env step (M)")
    _size_ticks(ax, show_labels=True, with_xlabel=True)
    ax.set_title("C. Critic first-layer MACs per env step", loc="left")
    ax.text(0.03, 0.96,
            "first-layer MACs = 128 x share_obs x 12N\n"
            "share_obs = 24N² + 6N  =>  ~N³",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5,
            color=C_NOTE)
    ax.annotate(f"{mac[0]:.2f}M", xy=(float(ns[0]), float(mac[0])),
                xytext=(0, 7), textcoords="offset points", ha="center",
                va="bottom", fontsize=8.5, color=C_NOTE)
    ax.annotate(f"{mac[-1]:.1f}M", xy=(float(ns[-1]), float(mac[-1])),
                xytext=(8, 0), textcoords="offset points", ha="left",
                va="center", fontsize=8.5, color=C_NOTE)

    axins = ax.inset_axes([0.735, 0.07, 0.245, 0.50])
    axins.plot(nline, _mac_per_step(nline) / 1e6, color=C_SHARED, lw=1.4,
               zorder=3)
    axins.plot(ns, mac, "o", ms=4.5, mfc=C_SHARED, mec="white", mew=0.7,
               zorder=4)
    axins.set_xscale("log")
    axins.set_yscale("log")
    axins.set_xlim(1.7, 13.0)
    axins.set_ylim(0.25, 60.0)
    axins.set_xticks([2, 3, 5, 10])
    axins.set_xticklabels(["2", "3", "5", "10"])
    axins.set_yticks([0.3, 1, 3, 10, 30])
    axins.set_yticklabels(["0.3", "1", "3", "10", "30"])
    axins.minorticks_off()
    axins.tick_params(labelsize=8, length=2.5, pad=1.5)
    axins.set_xlabel("N", fontsize=8.5, labelpad=1)
    axins.set_ylabel("MACs (M)", fontsize=8.5, labelpad=1)
    axins.text(0.03, 0.05, "log-log; slope ~3", transform=axins.transAxes,
               ha="left", va="bottom", fontsize=7.5, color=C_NOTE)


def _panel_d(ax, grad_rows):
    """Boxplots of critic_grad_norm_per_N by team size (measured N only)."""
    groups, counts, seeds = [], [], []
    for n in NS_MEASURED:
        sub = [r for r in grad_rows if int(r["team_size"]) == n]
        vals = [float(r["critic_grad_norm_per_N"]) for r in sub
                if r.get("critic_grad_norm_per_N") is not None]
        if not vals:
            raise RuntimeError(
                f"no critic_grad_norm_per_N rows for N={n} in "
                "normalized_scaling.csv (label 'scaling noweapon')")
        groups.append(vals)
        counts.append(len(vals))
        seeds.append(len({r["experiment"] for r in sub}))

    bp = ax.boxplot(groups, positions=range(len(NS_MEASURED)), widths=0.55,
                    patch_artist=True, whis=1.5, showfliers=True)
    for i, n in enumerate(NS_MEASURED):
        c = style.color_for_n(n)
        box = bp["boxes"][i]
        box.set_facecolor(c)
        box.set_edgecolor(c)
        box.set_linewidth(1.0)
        for w in bp["whiskers"][2 * i:2 * i + 2]:
            w.set_color(c)
            w.set_linewidth(1.0)
        for cap in bp["caps"][2 * i:2 * i + 2]:
            cap.set_color(c)
            cap.set_linewidth(1.0)
        fl = bp["fliers"][i]
        fl.set_marker("o")
        fl.set_markersize(2.6)
        fl.set_markerfacecolor(c)
        fl.set_markeredgecolor("white")
        fl.set_markeredgewidth(0.4)
        fl.set_linestyle("none")
    for med in bp["medians"]:
        med.set_color("#2B2B2B")
        med.set_linewidth(1.7)

    ax.set_yscale("log")
    ax.set_ylim(0.85, 320)
    _plain_ticks(ax, [1, 2, 5, 10, 20, 50, 100, 200])
    ax.set_ylabel("critic_grad_norm / N (log scale)")
    ax.set_xlim(-0.6, len(NS_MEASURED) - 0.4)
    ax.set_xticks(range(len(NS_MEASURED)))
    ax.set_xticklabels([f"{n}\n{n}v{n}" for n in NS_MEASURED])
    ax.set_xlabel("team size N (agents per side)")
    ax.set_title("D. Critic gradient norm per N, by team size", loc="left")

    # sparsity: which (run) series in this family were still running
    maxstep = {}
    for r in grad_rows:
        exp = r.get("experiment") or ""
        key = (int(r["team_size"]), exp)
        maxstep[key] = max(maxstep.get(key, 0), r.get("env_steps") or 0)
    running = [f"{n}v{n} s{exp.rsplit('_s', 1)[-1]} {st / 1e6:.1f}M"
               for (n, exp), st in sorted(maxstep.items()) if st < 5.99e6]
    ax.text(0.98, 0.97,
            "logged episodes per box: " + " / ".join(map(str, counts)) + "\n"
            "seeds pooled: " + " / ".join(map(str, seeds)) + "\n"
            "still running: " + ", ".join(running) + "\n"
            "per-episode distribution, not a CI",
            transform=ax.transAxes, ha="right", va="top", fontsize=8.2,
            color=C_NOTE)


# --------------------------------------------------------------------------
# entry point (contract for make_all.py)
# --------------------------------------------------------------------------
def build(camp=None, out_dir=None):
    camp = Path(camp) if camp else data.CAMPAIGN
    style.apply_style()

    rows = _measured_rows(camp)
    grad_rows = [r for r in data.load_normalized(camp)
                 if r.get("label") == "scaling noweapon"
                 and r.get("critic_grad_norm_per_N") is not None]
    if not grad_rows:
        raise RuntimeError(
            "normalized_scaling.csv has no rows with label 'scaling "
            "noweapon' - panel D has no data")

    w = (COL_R - COL_L - COL_GAP) / 2.0
    col = [(COL_L, w), (COL_L + w + COL_GAP, w)]
    fig = plt.figure(figsize=FIG_SIZE)

    _panel_a(fig, (col[0][0], ROW1_BOTTOM, col[0][1], ROW1_H), rows)
    ax_b = fig.add_axes([col[1][0], ROW1_BOTTOM, col[1][1], ROW1_H])
    _panel_b(ax_b, rows)
    ax_c = fig.add_axes([col[0][0], ROW2_BOTTOM, col[0][1], ROW2_H])
    _panel_c(ax_c, rows)
    ax_d = fig.add_axes([col[1][0], ROW2_BOTTOM, col[1][1], ROW2_H])
    _panel_d(ax_d, grad_rows)

    cap = style.caption(fig, _wrap(CAPTION), fontsize=CAPTION_FONTSIZE)
    # guard: matplotlib never wraps text, and an over-wide caption silently
    # widens the saved tight bbox - fail loudly instead of shipping that
    fig.canvas.draw()
    cap_ext = cap.get_window_extent(fig.canvas.get_renderer())
    cap_w_in = cap_ext.width / fig.dpi
    cap_top_in = cap_ext.y1 / fig.dpi
    assert cap_w_in <= FIG_SIZE[0] - 0.1, (
        f"caption is {cap_w_in:.2f} in wide, figure is {FIG_SIZE[0]} in - "
        "wrap it shorter (see _wrap)")
    # 0.60 in below the bottom-row axes is reserved for their two-line tick
    # labels + xlabel; the caption must not reach into that band
    band_in = ROW2_BOTTOM * FIG_SIZE[1] - 0.60
    assert cap_top_in <= band_in, (
        f"caption top is {cap_top_in:.2f} in up, bottom-row labels reach "
        f"down to {band_in:.2f} in - trim the caption")
    # every axes here is placed with add_axes, so style.save()'s tight_layout()
    # is a no-op for them; silence the "not compatible with tight_layout"
    # warning it would otherwise emit for manually positioned axes
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*not compatible with "
                                                 "tight_layout.*")
        return [style.save(fig, "fig5_critic_scaling", out_dir=out_dir)]


if __name__ == "__main__":
    for p in build():
        print(p)
