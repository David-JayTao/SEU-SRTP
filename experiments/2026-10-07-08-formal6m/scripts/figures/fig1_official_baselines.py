#!/usr/bin/env python3
"""Figure 1 - official repository configs, replicated at a 6M-step budget.

Four *different tasks* are shown as a 2x2 small-multiple grid whose panels have
**independent y axes**.  The task's episode-reward scales differ by roughly an
order of magnitude (SingleControl heading ~ +/-320, 1v1 ~ +/-200, 2v2 ~ +/-40),
so one shared y axis would visually rank *tasks* instead of algorithms: the 2v2
run and the 1v1 degradation would both collapse into thin lines near the
baseline - the failure mode this figure revision exists to fix.  Each panel's
y label therefore states that it carries its own scale and that panels must not
be compared with one another.

Panels
------
A. SingleControl / heading         f6m_official_heading_s5              (1 curve)
B. 1v1 / NoWeapon                  Selfplay, vsBaseline, HierarchySelfplay
                                   - three *scenarios*, not three seeds, so
                                   they share the N=1 colour and differ by
                                   line style; the raw HierarchySelfplay
                                   series is annotated where it destabilises
C. 1v1 / ShootMissile              f6m_official_1v1_shoot_hier_selfplay_s1
D. 2v2 / NoWeapon                  f6m_official_2v2_noweapon_s0

Also writes fig1b_1v1_hier_raw.{png,pdf}: the 1v1 HierarchySelfplay run drawn
as a complete raw series with no rolling mean overlaid, so that the late
negative spikes cannot be mistaken for a smoothing artefact.

Products
--------
figures_v2/fig1_official_baselines.png / .pdf
figures_v2/fig1b_1v1_hier_raw.png / .pdf

Every colour, line width and font comes from ``style``; every number comes from
the curve CSVs via ``data``.  Nothing is interpolated and no run is dropped.
"""

from __future__ import annotations

from statistics import median

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import data
import style

# The one smoothing window, in environment steps - fixed for the whole figure
# set (never re-tuned per panel; see data.smooth_by_steps).
WINDOW = data.DEFAULT_WINDOW
MILLION = 1_000_000

# Shown on every y label: the panels are four tasks, not four variants.
_OWN_SCALE = "Episode reward\n(own scale - not comparable)"

# Colour of the annotation ink / instability band (text + neutral tokens only,
# series identity is never carried by this colour).
_INK = style.CAPTION_COLOR
_BAND_COLOR = style.PALETTE["neutral"]
_BAND_ALPHA = 0.13

# A "late-training instability" band must span at least this many env steps to
# be reported at all (guards against shading noise).
_MIN_BAND_STEPS = 1_000_000


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def _series(rows):
    """[(env_steps, episode_reward)] with incomplete rows dropped."""
    out = []
    for r in rows:
        x, y = r.get("total_num_steps"), r.get("average_episode_rewards")
        if x is None or y is None:
            continue
        out.append((float(x), float(y)))
    out.sort()
    return out


def _instability_span(rows, window=WINDOW, min_len=_MIN_BAND_STEPS):
    """Longest contiguous span whose rolling *median* reward stays negative.

    The rolling median uses the same fixed environment-step window as the
    smoothed curves (``data.DEFAULT_WINDOW``), so the band is defined by the
    same amount of experience at every scale.  Returns ``(x_start, x_end)`` in
    env steps, or ``None`` when no run of at least ``min_len`` steps exists -
    the band is measured from the data, never hard-coded.
    """
    pts = _series(rows)
    if len(pts) < 2:
        return None
    xs_all = [x for x, _ in pts]
    ys_all = [y for _, y in pts]
    xs, meds = [], []
    j = 0
    for i, (x, _) in enumerate(pts):
        lo = x - window
        while xs_all[j] < lo:
            j += 1
        if x - xs_all[0] < window:      # full window not available yet
            continue
        xs.append(x)
        meds.append(median(ys_all[j:i + 1]))
    best = None
    start = None
    for i, m in enumerate(meds):
        if m < 0:
            if start is None:
                start = i
            if best is None or (xs[i] - xs[start]) > (best[1] - best[0]):
                best = (xs[start], xs[i])
        else:
            start = None
    if best is None or best[1] - best[0] < min_len:
        return None
    return best


def _shade_band(ax, span):
    """Light neutral band behind the data (zorder 1, raw curves sit at 2)."""
    if span is None:
        return None
    return ax.axvspan(span[0], span[1], facecolor=_BAND_COLOR,
                      edgecolor="none", alpha=_BAND_ALPHA, zorder=1)


def _point_at(ax, x, y, text, *, dx_frac=0.045, dy_frac=0.10, ha="left"):
    """Grey annotation with an arrow from open space to (x, y).

    The text is parked in the lower-left corner of the axes (measured in axes
    fractions after all limit changes), which is empty in every panel here -
    the annotation never sits on top of a curve.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.annotate(text, xy=(x, y),
                xytext=(x0 + dx_frac * (x1 - x0), y0 + dy_frac * (y1 - y0)),
                ha=ha, va="center", fontsize=9.5, color=_INK,
                arrowprops=dict(arrowstyle="->", color=_INK, lw=0.9,
                                shrinkA=3, shrinkB=2))


def _set_limits(ax, series_list, pad_frac=0.10):
    """Explicit independent limits: y from this panel's data only, x from 0."""
    ys = [y for pts in series_list for _, y in pts]
    xs = [x for pts in series_list for x, _ in pts]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    ax.set_ylim(lo - pad_frac * span, hi + pad_frac * span)
    ax.set_xlim(0.0, max(xs) * 1.01)


def _draw_entry(ax, entry):
    """raw + smoothed curve, then the direct end label on the smoothed line."""
    res = style.plot_curve(ax, entry["rows"], entry["color"], entry["linestyle"],
                           window=WINDOW)
    if res["xs"]:
        x_end, y_end = res["xs"][-1], res["ys"][-1]
    else:                               # shorter than one window: raw only
        x_end, y_end = _series(entry["rows"])[-1]
    style.add_end_label(ax, x_end, y_end, entry["label"], entry["color"])
    return res


def _millions(v, _pos=None):
    """Env-step tick -> million (the x unit used on every panel)."""
    return f"{v / MILLION:g}"


def _finish_axes(ax):
    ax.xaxis.set_major_formatter(FuncFormatter(_millions))


def _caption_strip(fig, gs, row, text):
    """Bottom small-print block, rendered inside its own grid cell.

    ``style.caption`` pins the text to the figure bottom with ``fig.text``, but
    ``Figure.tight_layout()`` - which ``style.save`` calls - does not reserve
    room for figure-level text, so a multi-line caption ends up drawn over the
    bottom row's x tick labels (measured, not assumed).  Hosting the same text
    in a decor-less axes makes the layout engine see it and reserve the space.
    Font size, colour, alignment and corner stay identical to style.caption.
    """
    cap = fig.add_subplot(gs[row, :])
    cap.set_axis_off()
    return cap.text(0.004, 0.05, text, transform=cap.transAxes, ha="left",
                    va="bottom", fontsize=8.5, color=style.CAPTION_COLOR,
                    linespacing=1.45)


# --------------------------------------------------------------------------
# panels
# --------------------------------------------------------------------------
def _entry(curves, exp, label, family_key, linestyle="-"):
    return {"rows": curves[exp], "label": label, "linestyle": linestyle,
            "color": style.color_for_family(family_key)}


def _build_main(camp=None, out_dir=None):
    curves = data.load_curves() if camp is None else data.load_curves(camp)

    # Stable order, fixed colours: N=1 sky blue, N=2 blue, SingleControl magenta.
    # The three 1v1 scenarios share the N=1 colour and differ by line style.
    ls_a, ls_b, ls_c = style.SEED_LINESTYLES   # '-', '--', '-.'

    panel_a = [_entry(curves, "f6m_official_heading_s5", "SingleControl", "single_control")]
    panel_b = [
        _entry(curves, "f6m_official_1v1_selfplay_s1", "Selfplay", 1, ls_a),
        _entry(curves, "f6m_official_1v1_vsbaseline_s1", "vsBaseline", 1, ls_b),
        _entry(curves, "f6m_official_1v1_hier_selfplay_s1", "HierSelfplay", 1, ls_c),
    ]
    panel_c = [_entry(curves, "f6m_official_1v1_shoot_hier_selfplay_s1",
                      "ShootHier", 1)]
    panel_d = [_entry(curves, "f6m_official_2v2_noweapon_s0", "2v2 official", 2)]

    fig = plt.figure(figsize=(13.4, 10.8))
    # No hspace/wspace/left/right here on purpose: passing them marks the
    # GridSpec as "locally modified" and tight_layout then refuses to lay the
    # figure out at all (it warns and returns without touching anything).
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.38])
    # four separate axes: sharey is deliberately OFF (four different tasks)
    ax_a, ax_b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    ax_c, ax_d = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])

    panels = (
        (ax_a, panel_a, "A. SingleControl - heading control (single agent)"),
        (ax_b, panel_b, "B. 1v1 NoWeapon - three training scenarios"),
        (ax_c, panel_c, "C. 1v1 ShootMissile - hierarchy self-play"),
        (ax_d, panel_d, "D. 2v2 MultipleCombat - NoWeapon"),
    )

    # Panel B carries the late destabilisation of the hierarchy run: measure the
    # band once, shade it behind the curves, annotate the worst measured spike.
    hier_rows = curves["f6m_official_1v1_hier_selfplay_s1"]
    hier_span = _instability_span(hier_rows)

    for ax, entries, title in panels:
        series_list = [_series(e["rows"]) for e in entries]
        _set_limits(ax, series_list)        # before plotting: locks scale
        _finish_axes(ax)
        if ax is ax_b:
            _shade_band(ax, hier_span)
        for entry in entries:
            _draw_entry(ax, entry)
        ax.set_title(title)
        ax.set_ylabel(_OWN_SCALE)
        ax.set_xlabel("Environment steps (millions)")

    if hier_span is not None:
        y_min, x_min = min((y, x) for x, y in _series(hier_rows)
                           if hier_span[0] <= x <= hier_span[1])
        _point_at(ax_b, x_min, y_min, "late-training instability")

    band_txt = (f"{hier_span[0] / MILLION:.1f}M-{hier_span[1] / MILLION:.1f}M"
                if hier_span is not None else "none")
    _caption_strip(fig, gs, 2, "\n".join([
        "Official repo configs (SingleControl / 1v1 / 2v2) replicated at a reduced "
        "6M-step budget per run; official runs use 1e8 steps, so this is a budget "
        "cut, not full convergence.",
        "Panels carry independent y axes: task reward scales differ by an order of "
        "magnitude (heading ~+/-320, 1v1 ~+/-200, 2v2 ~+/-40, measured here), so "
        "panel levels must not be compared.",
        "Panel B shows three 1v1 scenarios (Selfplay / vsBaseline / "
        "HierarchySelfplay), not three seeds: same colour, line style separates "
        "them.",
        f"The shaded band is the longest span whose 250k-step rolling median reward "
        f"stays negative ({band_txt} steps); the arrow marks its lowest episode.",
        "Raw episode reward (lw 0.7, alpha 0.15) plus a rolling mean over a fixed "
        "250,000-env-step window (data.DEFAULT_WINDOW).",
        "Runs end at 5,994,000 steps (1v1, 3 threads, time cap) or 6,000,000 "
        "(heading and 2v2, 4 threads).",
    ]))

    fig.suptitle("Official baselines: four tasks, four independent reward scales",
                 fontsize=13)

    return style.save(fig, "fig1_official_baselines", out_dir=out_dir)


def _build_hier_raw(camp=None, out_dir=None):
    """fig1b: the full raw HierarchySelfplay series, no rolling mean.

    This is the one place the raw alpha is raised: the house rule's alpha=0.15
    exists so a raw curve can sit *under* a smoothed one, but here the raw line
    is the only series, and at 0.15 the late spikes this figure exists to show
    would be invisible in print.
    """
    exp = "f6m_official_1v1_hier_selfplay_s1"
    curves = data.load_curves() if camp is None else data.load_curves(camp)
    rows = curves[exp]
    pts = _series(rows)
    color = style.color_for_family(1)

    fig = plt.figure(figsize=(12.6, 6.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 0.24])   # no local params
    ax = fig.add_subplot(gs[0, 0])
    _set_limits(ax, [pts])

    span = _instability_span(rows)
    _shade_band(ax, span)

    line = style.plot_raw(ax, [x for x, _ in pts], [y for _, y in pts], color)
    line.set_alpha(0.85)                    # documented deviation (see docstring)
    style.add_end_label(ax, pts[-1][0], pts[-1][1], "HierSelfplay", color)

    if span is not None:
        y_min, x_min = min((y, x) for x, y in pts if span[0] <= x <= span[1])
        _point_at(ax, x_min, y_min, "late-training instability")

    _finish_axes(ax)
    ax.set_title("1v1 NoWeapon / HierarchySelfplay - raw episode reward, no smoothing")
    ax.set_xlabel("Environment steps (millions)")
    ax.set_ylabel("Episode reward (raw)")

    med_all = median(y for _, y in pts)
    med_band = median(y for x, y in pts if span[0] <= x <= span[1]) if span else med_all
    band_txt = (f"{span[0] / MILLION:.1f}M-{span[1] / MILLION:.1f}M" if span
                else "none")
    _caption_strip(fig, gs, 1, "\n".join([
        f"f6m_official_1v1_hier_selfplay_s1: all {len(pts)} logged episodes "
        f"({data.RUN_META[exp]['threads']} threads x 3000 env steps = "
        f"{data.steps_per_episode(exp):,} steps each), ending at "
        f"{int(pts[-1][0]):,} steps (~6M budget, time cap).",
        f"No rolling mean is overlaid, so every late negative spike is a measured "
        f"value: median episode reward {med_all:.1f} overall, {med_band:.1f} inside "
        f"the band, {pts[-1][1]:.1f} at the end.",
        f"Band = longest span whose {WINDOW // 1000}k-step rolling median stays "
        f"negative ({band_txt} steps); raw line at alpha 0.85 instead of the usual "
        f"0.15 underlay because it is the only series here.",
    ]))

    return style.save(fig, "fig1b_1v1_hier_raw", out_dir=out_dir)


def build(camp=None, out_dir=None):
    """Build both figure 1 products; returns their (png, pdf) path tuples."""
    style.apply_style()
    return [_build_main(camp=camp, out_dir=out_dir),
            _build_hier_raw(camp=camp, out_dir=out_dir)]


if __name__ == "__main__":
    for png, pdf in build():
        print(f"{png}\n{pdf}")
