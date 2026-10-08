#!/usr/bin/env python3
"""fig2 - N-v-N scaling learning curves (the panel figure of the campaign).

Four panels - 2v2 / 3v3 / 5v5 / 10v10 - each carrying *that size's* seeds of
the ``scaling`` family (generated ``scaling_*`` configs, NoWeapon).  Every run
is drawn as a raw underlay (lw 0.7, alpha 0.15) plus the rolling mean over a
fixed ``data.DEFAULT_WINDOW`` = 250,000 **environment steps** - never an
episode-indexed window, because a 2v2 episode is 12k steps while a 10v10
episode is 60k, so only an env-step window means the same amount of experience
at every scale.

Two products come out of this module
------------------------------------
1. ``fig2_scaling_curves`` - the primary figure.  Each panel gets its **own**
   y-scale so that size's own trend stays readable, and the per-panel reward
   magnitude is written into that panel's y-axis label.  Absolute heights are
   therefore *not* comparable between panels and the caption says so.
2. ``fig2b_scaling_shared_axis`` - the illustration companion: all eight
   scaling runs on ONE shared y-axis.  That is exactly the plot shape in which
   10v10 was invisible in the old figures (its reward lives around -18..+17
   while 2v2/3v3/5v5 climb to +22..+53).  Deliberately marked as an
   illustration of the artefact, not as a fair comparison.

Unfinished runs - 5v5 seed 1 (stops at 5.4M), 5v5 seed 2 (2.3M), 10v10 seed 1
(1.86M) - are drawn up to their last logged step and annotated
``(censored at ...)``.  Nothing is interpolated, extended or dropped, and the
smoothed line never crosses the last real sample (``data.smooth_by_steps``).

Colours are fixed per size by ``style.color_for_n``; seeds of one size share
the colour and differ by line style (``style.linestyle_for_seed``).  Curves
are labelled directly at their ends, so there is no legend.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.transforms import Bbox

import data
import style

# the single smoothing window, taken from its owner (never re-defined here)
WINDOW = data.DEFAULT_WINDOW

# all four panels span the same environment-step range
X_MIN, X_MAX = 0, 6_000_000

# y padding above / below the smoothed data range of a panel
PAD_FRAC = 0.08

PANEL_SIZES = (2, 3, 5, 10)          # reading order: top-left -> bottom-right
FIG2_NAME = "fig2_scaling_curves"
FIG2B_NAME = "fig2b_scaling_shared_axis"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _load(camp):
    curves = data.load_curves() if camp is None else data.load_curves(camp)
    missing = [exp for n in PANEL_SIZES
               for exp in data.runs_of("scaling", n=n) if not curves.get(exp)]
    if missing:
        raise RuntimeError(
            "fig2 needs the scaling curve CSVs, missing: " + ", ".join(missing))
    return curves


def _padded(lo, hi, frac=PAD_FRAC):
    """Symmetrically pad a data range; guards against a degenerate span."""
    span = hi - lo
    if span <= 0:
        span = max(abs(lo), 1.0)
    return lo - frac * span, hi + frac * span


def _draw_size(ax, curves, n):
    """Draw one size's seeds onto ``ax``.

    Returns ``(color, drawn, (lo, hi))`` where ``drawn`` is a list of
    ``(exp, meta, curve_info)`` in the deterministic ``data.runs_of`` order and
    ``(lo, hi)`` is the range of the *smoothed* series (the series the reader
    is asked to read), falling back to the raw values for a run shorter than
    one window.
    """
    color = style.color_for_n(n)
    drawn = []
    lo = hi = None
    for exp in data.runs_of("scaling", n=n):
        meta = data.RUN_META[exp]
        info = style.plot_curve(ax, curves[exp], color,
                                style.linestyle_for_seed(meta["seed"]),
                                window=WINDOW)
        drawn.append((exp, meta, info))
        if info["ys"]:
            vlo, vhi = min(info["ys"]), max(info["ys"])
        else:                                   # shorter than one window
            vals = [float(r["average_episode_rewards"]) for r in curves[exp]
                    if r.get("average_episode_rewards") is not None]
            vlo, vhi = min(vals), max(vals)
        lo = vlo if lo is None else min(lo, vlo)
        hi = vhi if hi is None else max(hi, vhi)
    return color, drawn, (lo, hi)


def _decorate(ax, ylim, *, title, ylabel):
    """Axis furniture shared by every axes: range, ticks, title, y-label."""
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(*ylim)
    ax.xaxis.set_major_locator(MultipleLocator(1_000_000))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda v, _pos: style.fmt_steps(v)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
    ax.axhline(0.0, color=style.color_for_family("neutral"), lw=0.8,
               alpha=0.55, zorder=1)            # reward baseline
    if title:
        ax.set_title(title)
    ax.set_ylabel(ylabel)


def _end_labels(ax, curves, drawn, *, qualify=False):
    """Label every curve's end (no legend); return the censored-run entries.

    The anchor is the last *smoothed* point, i.e. the end of the thick line -
    which by construction never extends past the last real sample.  ``qualify``
    prefixes the label with the team size (needed when several sizes share one
    axes, as in fig2b).  The entries returned are handed to
    ``_place_censor_notes`` once the final layout is known.
    """
    ends = []
    for exp, meta, info in drawn:
        if info["xs"]:
            x, y = info["xs"][-1], info["ys"][-1]
        else:
            row = curves[exp][-1]
            x, y = row["total_num_steps"], row["average_episode_rewards"]
        name = f"{meta['n']}v{meta['n']} seed {meta['seed']}" if qualify \
            else f"seed {meta['seed']}"
        ends.append((y, x, meta, name))
    # highest curve first: style.add_end_label only pushes labels *downwards*,
    # so placing the topmost anchor first keeps it on its own curve end and
    # makes the crowded stack (four curves ending at 6M in fig2b) descend in
    # the same order as the data
    labels, censored = [], []
    for y, x, meta, name in sorted(ends, key=lambda e: (-e[0], e[1])):
        ann = style.add_end_label(ax, x, y, name, style.color_for_n(meta["n"]))
        labels.append(ann)
        if not meta["complete"]:
            censored.append((ann, f"(censored at {style.fmt_steps(x)})",
                             style.color_for_n(meta["n"])))
    return labels, censored


def _place_censor_notes(ax, labels, entries):
    """Small "(censored at ...)" notes, tucked against their own end labels.

    ``style.add_end_label`` de-collides *labels* with a data-space gap; the
    notes are placed against the actually rendered text boxes instead, because
    a label that has been pushed around can pass the data-space gap test yet
    still overlap a neighbouring note on screen.  Each note is tried just below
    its own label first and just above it second; the candidate that needs the
    smaller displacement while overlapping nothing (labels and already placed
    notes) wins, so a crowded area pushes the note to the free side.
    """
    if not entries:
        return
    fig = ax.figure
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    px_pt = ren.points_to_pixels(1.0)
    gap = ren.points_to_pixels(3.5)
    step = ren.points_to_pixels(3.0)
    occupied = [a.get_window_extent(ren) for a in labels]
    for ann, text, color in entries:
        label_box = ann.get_window_extent(ren)
        anchor_y = ax.transData.transform(ann.xy)[1]
        # throw-away probe: the note's rendered width/height at this font size
        probe = ax.annotate(text, xy=ann.xy, xytext=(6.0, 0.0),
                            textcoords="offset points", ha="left", va="center",
                            fontsize=8.0, color=color, alpha=0.9,
                            annotation_clip=False)
        fig.canvas.draw()
        pb = probe.get_window_extent(ren)
        probe.remove()
        x0, x1, half = pb.x0, pb.x1, (pb.y1 - pb.y0) / 2.0

        choices = []
        for direction in (-1.0, 1.0):        # below the label, then above it
            y = (label_box.y0 - gap - half) if direction < 0 \
                else (label_box.y1 + gap + half)
            start = y
            for _ in range(30):
                if y - half < ax.bbox.y0 + 1.0 or y + half > ax.bbox.y1 - 1.0:
                    y = None                 # ran out of panel
                    break
                box = Bbox.from_extents(x0, y - half, x1, y + half)
                if not any(box.overlaps(other) for other in occupied):
                    break
                y += direction * step
            else:
                y = None
            if y is not None:
                choices.append((abs(y - start), y))
        if choices:
            y = min(choices)[1]
        else:                                # nothing fits: keep it readable
            y = min(max(label_box.y0 - gap - half, ax.bbox.y0 + half),
                    ax.bbox.y1 - half)
        note = ax.annotate(text, xy=ann.xy,
                           xytext=(6.0, (y - anchor_y) / px_pt),
                           textcoords="offset points", ha="left", va="center",
                           fontsize=8.0, color=color, alpha=0.9,
                           annotation_clip=False)
        fig.canvas.draw()
        occupied.append(note.get_window_extent(ren))


def _unify_x(axes):
    """Give every panel the identical x-limit; ``style.add_end_label`` widens
    the axes to make room for the label at x_end + 0.13 * span, and since every
    panel contains a run that ends at 6M they all land on the same widened
    range (ticks stop at 6M; the extra strip is label room only)."""
    xmax = max(ax.get_xlim()[1] for ax in axes)
    for ax in axes:
        ax.set_xlim(X_MIN, xmax)


def _finish(fig, pending, caption_text):
    """Final layout pass: end-label notes, then the caption under the axes.

    ``fig.tight_layout()`` is computed once here; ``style.save`` repeats the
    same call, so the geometry the notes were measured against is the geometry
    that gets written out.  ``pending`` is a list of ``(ax, labels, entries)``.
    """
    fig.tight_layout()
    for ax, labels, entries in pending:
        _place_censor_notes(ax, labels, entries)
    return _caption_below(fig, caption_text)


def _caption_below(fig, text):
    """House caption anchored just below the lowest axes decoration.

    ``savefig(bbox_inches="tight")`` grows the canvas around it, so the caption
    can never land on the bottom row's tick labels - the 2x2 tight_layout
    margin is ~30 pt, less than a four-line caption needs.  The Text itself
    still comes from ``style.caption``; only its anchor is moved.
    """
    cap = style.caption(fig, text)
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    ymin = min(ax.get_tightbbox(ren).y0 for ax in fig.axes if ax.get_visible())
    cap.set_position((0.012,
                      (ymin - ren.points_to_pixels(5.0)) / fig.bbox.height))
    cap.set_va("top")
    cap.set_in_layout(True)
    return cap


# --------------------------------------------------------------------------
# fig2 - four panels, four y-scales
# --------------------------------------------------------------------------
def _build_panels(curves, out_dir):
    fig, grid = plt.subplots(2, 2, figsize=(11.6, 8.0))
    axes = list(grid.ravel())

    pending, ranges = [], {}
    for ax, n in zip(axes, PANEL_SIZES):
        _color, drawn, (lo, hi) = _draw_size(ax, curves, n)
        ranges[n] = (lo, hi)
        _decorate(ax, _padded(lo, hi),
                  title=f"{n}v{n}  (N={n})",
                  # the magnitude note lives in the axis label on purpose: the
                  # reader must see, per panel, which reward scale it is on
                  ylabel=f"Episode reward ({n}v{n} scale: {lo:.0f} to {hi:.0f})")
        labels, censored = _end_labels(ax, curves, drawn)
        pending.append((ax, labels, censored))

    for ax in grid[1]:
        ax.set_xlabel("Environment steps (M)")

    _unify_x(axes)
    fig.suptitle("N-v-N scaling: episode reward vs environment steps, one panel "
                 "per team size (each panel on its own y-scale)", fontsize=13)
    _finish(fig, pending, "\n".join([
        "NoWeapon HierarchySelfplay; 6M env steps target, 5 of 8 runs reached "
        "it - the rest stop at their last logged step (see end labels). "
        "Seeds per panel: 2v2=1, 3v3=2, 5v5=3, 10v10=2.",
        "Rolling mean over a fixed 250,000-env-step window (raw curves beneath: "
        "lw 0.7, alpha 0.15). Line style = seed (solid 0, dashed 1, dash-dot 2).",
        "n_rollout_threads differ by size (2v2=4, 3v3=8, 5v5=8 for seeds 0/2 and "
        "10 for seed 1, 10v10=20), so cross-size gaps mix batch size with scale.",
        "Each panel has its own y-scale: heights are NOT comparable across panels "
        f"(2v2 spans {ranges[2][0]:.0f}..{ranges[2][1]:+.0f}, 10v10 "
        f"{ranges[10][0]:.0f}..{ranges[10][1]:+.0f}; the tasks' reward definitions "
        "differ); rare raw spikes are clipped by the panel limits.",
    ]))
    return list(style.save(fig, FIG2_NAME, out_dir=out_dir))


# --------------------------------------------------------------------------
# fig2b - the same runs on ONE shared y-axis (illustration of the artefact)
# --------------------------------------------------------------------------
def _span_of(drawn, n):
    """Span of the smoothed series of one size inside ``drawn`` (no padding)."""
    ys = [y for _exp, meta, info in drawn if meta["n"] == n
          for y in info["ys"]]
    return max(ys) - min(ys)


def _build_shared(curves, out_dir):
    fig, ax = plt.subplots(figsize=(10.8, 5.8))

    drawn = []
    lo = hi = None
    ranges = {}
    for n in PANEL_SIZES:
        _color, got, (rlo, rhi) = _draw_size(ax, curves, n)
        drawn += got
        ranges[n] = (rlo, rhi)
        lo = rlo if lo is None else min(lo, rlo)
        hi = rhi if hi is None else max(hi, rhi)

    _decorate(ax, _padded(lo, hi), title=None,
              ylabel="Episode reward (one shared y-scale for all four sizes)")
    ax.set_xlabel("Environment steps (M)")
    labels, censored = _end_labels(ax, curves, drawn, qualify=True)

    # explain, inside the plot, why the 10v10 curves look almost flat here
    ax.text(0.42, 0.05,
            f"10v10 spans {_span_of(drawn, 10):.0f} of the {hi - lo:.0f} reward "
            "units on this axis\n(it only looks flat because the shared scale "
            "is set by 5v5)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5,
            color=style.color_for_family("neutral"))

    _unify_x([ax])
    fig.suptitle("SHARED y-axis version of fig2 (illustration, not a fair "
                 "comparison): all four scales on one axis", fontsize=13)
    _finish(fig, [(ax, labels, censored)], "\n".join([
        "Same eight scaling runs and the same fixed 250,000-env-step rolling mean "
        "as fig2 (raw curves beneath). Seeds: 2v2=1, 3v3=2, 5v5=3, 10v10=2.",
        "Line style = seed (solid 0, dashed 1, dash-dot 2). This is the plot shape "
        f"that hid 10v10 before: its {ranges[10][0]:.0f}..{ranges[10][1]:+.0f} "
        f"range is compressed by the 5v5 scale ({ranges[5][0]:.0f}.."
        f"{ranges[5][1]:+.0f}).",
        "n_rollout_threads 4 / 8 / 8-10 / 20; 3 of 8 runs censored early "
        "(see labels).",
        "Read trends in fig2 (per-panel y-scales); a taller curve here does NOT "
        "mean a better policy - each task defines its reward differently.",
    ]))
    return list(style.save(fig, FIG2B_NAME, out_dir=out_dir))


def build(camp=None, out_dir=None):
    """Write fig2 and fig2b (PNG + PDF each); returns the four paths."""
    style.apply_style()
    curves = _load(camp)
    out = []
    out += _build_panels(curves, out_dir)
    out += _build_shared(curves, out_dir)
    return out


if __name__ == "__main__":
    for path in build():
        print(path)
