"""Shared style / palette foundation for the f6m figure pipeline (fig1..fig5).

This module owns every hard-coded visual rule so that all figures read as one
system.  Figure modules import it, they never re-define colours or styles.

House rules (binding for every figure)
--------------------------------------
* Okabe-Ito colour-blind-safe palette, **fixed per team size** and never
  re-assigned between figures:

      N=1  (1v1)          #56B4E9  sky blue
      N=2  (2v2)          #0072B2  blue
      N=3  (3v3)          #009E73  green
      N=5  (5v5)          #E69F00  orange
      N=10 (10v10)        #D55E00  vermillion
      SingleControl       #CC79A7  magenta
      neutral / reference #999999  grey

  The palette was validated with the dataviz skill's checker
  (``validate_palette.py``): lightness band, chroma floor, CVD separation and
  the normal-vision floor all PASS.  It emits one WARN: the sky blue / orange /
  magenta sit below 3:1 contrast on a white surface, so identity must never be
  colour-alone - every series carries a legend entry and/or a direct end label.
  That relief is already required by the house rules below.

* Several seeds of the *same* size share colour and are separated by line
  style (solid / dashed / dash-dot, see ``linestyle_for_seed``), never by
  alpha.  Alpha is reserved for the raw curves.
* Raw curve   : lw=0.7, alpha=0.15, same colour as its size.
  Smoothed curve: lw=2.2, alpha=1.0, same colour and line style.
* White background, light grey grid (#DDDDDD, lw 0.6, alpha 0.7, behind data),
  no top/right spines, DejaVu Sans, title 13 / axis label 11 / ticks 9.5 /
  legend 9.5.  Figure text is always English (no CJK font is installed on this
  machine; Chinese text renders as boxes).
* Every figure is exported as PNG (dpi=300) *and* PDF (vector) into
  ``figures_v2/``; ``save()`` refuses to report success for a blank figure.

Typical figure-module usage::

    import style, data
    style.apply_style()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    rows = curves["f6m_3v3_noweapon_s0"]
    style.plot_curve(ax, rows, style.color_for_n(3), "-")
    style.add_end_label(ax, xs[-1], ys[-1], "3v3 seed 0", style.color_for_n(3))
    style.caption(fig, "Rolling mean over 250,000 env steps (raw curve beneath).")
    style.save(fig, "fig1_reward_by_scale")
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
# this file lives at <campaign>/scripts/figures/style.py
HERE = Path(__file__).resolve()
HERE_DIR = HERE.parent                     # <campaign>/scripts/figures
CAMPAIGN = HERE.parents[2]                 # experiments/2026-10-07-08-formal6m
OUT_DIR = CAMPAIGN / "figures_v2"          # every fig1..fig5 product lands here

# make the sibling modules (data.py) and the fig modules importable even when
# this file is executed directly or loaded by path via importlib
if str(HERE_DIR) not in sys.path:
    sys.path.insert(0, str(HERE_DIR))

# --------------------------------------------------------------------------
# palette - the single source of truth for colour
# --------------------------------------------------------------------------
PALETTE = {
    1: "#56B4E9",              # 1v1
    2: "#0072B2",              # 2v2
    3: "#009E73",              # 3v3
    5: "#E69F00",              # 5v5
    10: "#D55E00",             # 10v10
    "single_control": "#CC79A7",   # SingleControl / heading
    "neutral": "#999999",          # reference lines, annotations, "other"
}

# step sizes the campaign actually contains; colour_for_n refuses anything else
# instead of silently inventing a colour (colour stability is a requirement)
KNOWN_SIZES = (1, 2, 3, 5, 10)

_FAMILY_ALIASES = {
    "singlecontrol": "single_control",
    "single_control": "single_control",
    "single": "single_control",
    "control": "single_control",
    "heading": "single_control",
    "ref": "neutral",
    "reference": "neutral",
    "baseline": "neutral",
    "grid": "neutral",
    "gray": "neutral",
    "grey": "neutral",
}

# line styles that separate seeds of the SAME size (same colour); index by seed
SEED_LINESTYLES = ("-", "--", "-.")
SEED_LABEL_SUFFIX = ("", " dashed", " dash-dot")

# mark specs, fixed by the house rules
RAW_LW = 0.7
RAW_ALPHA = 0.15
SMOOTH_LW = 2.2
SMOOTH_ALPHA = 1.0

GRID_COLOR = "#DDDDDD"
GRID_LW = 0.6
GRID_ALPHA = 0.7
CAPTION_COLOR = "#555555"

__all__ = [
    "CAMPAIGN", "OUT_DIR", "PALETTE", "KNOWN_SIZES", "SEED_LINESTYLES",
    "RAW_LW", "RAW_ALPHA", "SMOOTH_LW", "SMOOTH_ALPHA", "GRID_COLOR",
    "apply_style", "color_for_n", "color_for_family", "linestyle_for_seed",
    "save", "add_end_label", "caption", "plot_raw", "plot_smoothed",
    "plot_curve", "fmt_steps", "fmt_num",
]


def _normalise_size(key):
    """'2v2' / 'N=10' / 'n2' / 5 -> int team size; None when not a size."""
    if isinstance(key, bool):
        return None
    if isinstance(key, int):
        return int(key)
    s = str(key).strip().lower().replace(" ", "")
    for pref in ("n=", "n", "team=", "size="):
        if s.startswith(pref) and s[len(pref):len(pref) + 1].isdigit():
            s = s[len(pref):]
            break
    if "v" in s:
        left, _, right = s.partition("v")
        if left.isdigit() and right.isdigit():
            if left != right:
                raise ValueError(f"asymmetric size not supported: {key!r}")
            return int(left)
        return None
    return int(s) if s.isdigit() else None


def color_for_n(n):
    """Fixed colour for a team size.  Accepts 3, '3', '3v3', 'N=3'.

    Raises KeyError for a size without a fixed colour: add it to PALETTE (and
    to the guide) instead of picking a new colour inside one figure - the whole
    point of the palette is that a size keeps its colour across figures.
    """
    size = _normalise_size(n)
    if size in PALETTE:
        return PALETTE[size]
    raise KeyError(
        f"no fixed colour for N={n!r} (known sizes: {KNOWN_SIZES}); "
        "extend PALETTE in style.py rather than inventing a colour"
    )


def color_for_family(key):
    """Fixed colour for a non-size series key.  Accepts 'single_control',
    'heading', 'neutral'/'reference', or anything color_for_n accepts."""
    if key in PALETTE:
        return PALETTE[key]
    s = str(key).strip().lower().replace(" ", "_").replace("-", "_")
    if s in _FAMILY_ALIASES:
        return PALETTE[_FAMILY_ALIASES[s]]
    size = _normalise_size(key)
    if size is not None:
        return color_for_n(size)
    raise KeyError(
        f"unknown series key {key!r}; use a team size, 'single_control' or "
        "'neutral'"
    )


def linestyle_for_seed(seed):
    """Seed -> line style.  Same size => same colour, seeds differ by style."""
    try:
        i = int(seed) % len(SEED_LINESTYLES)
    except (TypeError, ValueError):
        i = 0
    return SEED_LINESTYLES[i]


# --------------------------------------------------------------------------
# rcParams
# --------------------------------------------------------------------------
def apply_style():
    """Install the house rcParams.  Call once per process, before plotting."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID_COLOR,
        "grid.linewidth": GRID_LW,
        "grid.alpha": GRID_ALPHA,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9.5,
        "font.size": 10,
        "legend.frameon": False,
        "lines.solid_capstyle": "round",
        "figure.dpi": 120,
        "savefig.dpi": 300,
    })


# --------------------------------------------------------------------------
# number formatting (kept here so every figure labels axes identically)
# --------------------------------------------------------------------------
def fmt_steps(v):
    """Environment steps -> compact axis label ('1.5M', '750k', '0')."""
    if v is None:
        return "?"
    if abs(v) >= 1_000_000:
        return f"{v / 1e6:g}M" if v % 1e6 else f"{v / 1e6:.0f}M"
    if abs(v) >= 1_000:
        return f"{v / 1e3:g}k" if v % 1e3 else f"{v / 1e3:.0f}k"
    return f"{v:g}"


def fmt_num(v, digits=1):
    """Generic compact number for end labels / annotations."""
    if v is None:
        return ""
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 10:
        return f"{v:.0f}" if digits == 1 else f"{v:.{digits}f}"
    return f"{v:.{max(digits, 1)}f}"


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------
def save(fig, name, *, out_dir=None, close=True):
    """Write ``name`` as PNG (dpi=300) and PDF (vector) into figures_v2/.

    ``name`` may carry a .png/.pdf suffix and may contain a sub-directory;
    it is normalised to one stem and both formats are written.  Returns
    ``(png_path, pdf_path)`` as ``pathlib.Path``.  Asserts that neither file
    is a blank figure (PNG > 20 KB; PDF > 4 KB - a truly empty matplotlib PDF
    is ~1.2 KB, a minimal real plot ~7 KB, so 4 KB catches blankness without
    ever failing a real figure).
    """
    out = Path(out_dir) if out_dir else OUT_DIR
    rel = Path(str(name))
    if rel.suffix.lower() in (".png", ".pdf"):
        rel = rel.with_suffix("")
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"refusing to save outside the figure directory: {name!r}")
    png = out / rel.with_suffix(".png")
    pdf = out / rel.with_suffix(".pdf")
    png.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.tight_layout()
    except Exception:  # exotic layouts (add_axes, inset) may refuse; not fatal
        pass
    # After tight_layout: shift the axes up if the caption would collide with
    # them, and keep the caption in the saved area.
    cap = _caption_collision_guard(fig)
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.12,
                bbox_extra_artists=[cap] if cap is not None else None)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.12,
                bbox_extra_artists=[cap] if cap is not None else None)
    if close:
        plt.close(fig)
    png_kb = png.stat().st_size / 1024
    pdf_kb = pdf.stat().st_size / 1024
    assert png.stat().st_size > 20_000, (
        f"blank figure? {png} is only {png_kb:.1f} KB (expected > 20 KB at "
        "dpi=300)"
    )
    assert pdf.stat().st_size > 4_000, (
        f"blank figure? {pdf} is only {pdf_kb:.1f} KB"
    )
    return png, pdf


# --------------------------------------------------------------------------
# plotting helpers - the only sanctioned way to draw a curve
# --------------------------------------------------------------------------
def plot_raw(ax, xs, ys, color, ls="-", *, label=None, **kw):
    """The thin raw curve (lw=0.7, alpha=0.15, colour of its size)."""
    kw.setdefault("zorder", 2)
    (line,) = ax.plot(xs, ys, color=color, ls=ls, lw=RAW_LW, alpha=RAW_ALPHA,
                      label=label, **kw)
    return line


def plot_smoothed(ax, xs, ys, color, ls="-", *, label=None, **kw):
    """The solid smoothed curve (lw=2.2, alpha=1.0, same colour / style)."""
    kw.setdefault("zorder", 3)
    (line,) = ax.plot(xs, ys, color=color, ls=ls, lw=SMOOTH_LW,
                      alpha=SMOOTH_ALPHA, label=label, **kw)
    return line


def plot_curve(ax, rows, color, ls="-", *, window=None,
               value_key="average_episode_rewards", x_key="total_num_steps",
               label=None, draw_raw=True):
    """Draw one run: raw underlay + environment-step-windowed rolling mean.

    The window is fixed in *environment steps* (``data.DEFAULT_WINDOW`` =
    250,000), never in episode indices - a 10v10 episode is 60k steps while a
    2v2 episode is 12k, so an episode-indexed window would not be equivalent
    across scales.  Returns ``{"raw": Line2D|None, "smooth": Line2D|None,
    "xs": [...], "ys": [...]}`` where xs/ys are the *smoothed* points; when the
    run is shorter than one window only the raw line is drawn (never a
    partially-windowed or extrapolated smooth line).
    """
    import data as _data  # sibling module; style stays importable stand-alone

    if window is None:
        window = _data.DEFAULT_WINDOW
    pts = [(r.get(x_key), r.get(value_key)) for r in rows]
    pts = [(x, y) for x, y in pts if x is not None and y is not None]
    xs_raw = [p[0] for p in pts]
    ys_raw = [p[1] for p in pts]
    raw = plot_raw(ax, xs_raw, ys_raw, color, ls, label=label) if draw_raw else None
    xs, ys = _data.smooth_by_steps(rows, window, value_key=value_key, x_key=x_key)
    smooth = plot_smoothed(ax, xs, ys, color, ls) if xs else None
    return {"raw": raw, "smooth": smooth, "xs": xs, "ys": ys}


def add_end_label(ax, x, y, text, color, *, fontsize=9.5, dx_pt=6.0,
                  pad_frac=0.022):
    """Label a curve directly at its last point (x, y) - no legend hopping.

    The label is drawn in the series colour at a fixed 6 pt to the right of
    (x, y).  Repeated calls on the same axes push colliding labels downwards in
    value space, and the first call reserves a little room on the right so the
    text stays inside the axes.  Keep labels short ('2v2 seed 0'), never the
    full experiment id.  Returns the matplotlib ``Annotation``.
    """
    fig = ax.figure
    fig.canvas.draw()  # realise the current limits before placing anything
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    span = getattr(ax, "_endlabel_span", None)
    if span is None or not span > 0:
        span = xmax - xmin
        ax._endlabel_span = span
    need = x + 0.13 * span
    if need > xmax:
        ax.set_xlim(xmin, need)
    gap = (ymax - ymin) * pad_frac
    placed = getattr(ax, "_endlabel_ys", None)
    if placed is None:
        placed = []
        ax._endlabel_ys = placed
    yy = y
    for _ in range(60):  # push downwards while colliding with a placed label
        if not any(abs(yy - p) < gap for p in placed):
            break
        yy -= gap
    if yy < ymin + 0.5 * gap:  # keep the label on-canvas
        yy = ymin + 0.5 * gap
    placed.append(yy)
    return ax.annotate(text, xy=(x, yy), xytext=(dx_pt, 0),
                       textcoords="offset points", ha="left", va="center",
                       fontsize=fontsize, color=color, annotation_clip=False)


def caption(fig, text, *, fontsize=8.5, color=CAPTION_COLOR):
    """One small line of context pinned near the bottom of the figure.

    Draws immediately and returns the ``Text`` so callers can re-anchor it --
    several figure modules do exactly that, measuring the lowest axes with
    ``get_tightbbox()`` and placing the caption just beneath it, which is the
    robust way to do it and is why those figures never collided.

    Callers that do NOT re-anchor are handled by ``save()``, which runs a
    collision guard after ``tight_layout()``: ``tight_layout`` ignores
    ``fig.text`` entirely, so a caption left at its default y lands on top of
    the bottom row's x-axis labels whenever the panels are tall enough to reach
    down there.  That is exactly what happened on fig1.

    Must carry what the title does not: smoothing window, seed count, thread
    count, completion state, statistic definition.  Keep it English.
    """
    artist = fig.text(0.012, 0.006, text, ha="left", va="bottom",
                      fontsize=fontsize, color=color)
    fig._srtp_caption = artist
    return artist


def _caption_collision_guard(fig):
    """Re-anchor the caption just below the lowest axes decoration.

    Runs after ``tight_layout()``.  Moving the *caption* rather than the axes
    is what the figure modules do by hand, and it is the better of the two:
    ``savefig(bbox_inches="tight")`` then grows the canvas to include the
    caption, so nothing overlaps and no empty band is left between the panels
    and the text.  (An earlier version shifted the axes upward instead, which
    also removed the overlap but left a conspicuous gap -- the "excessive
    whitespace" failure mode.)

    Returns the caption artist so ``save()`` can pass it to
    ``bbox_extra_artists``, or ``None`` if the figure has no caption.
    """
    cap = getattr(fig, "_srtp_caption", None)
    if cap is None:
        return None
    try:
        fig.canvas.draw()
        ren = fig.canvas.get_renderer()
        visible = [ax for ax in fig.axes if ax.get_visible()]
        if not visible:
            return cap
        lowest = min(ax.get_tightbbox(ren).y0 for ax in visible)
        pad = ren.points_to_pixels(5.0)
        cap.set_position((0.012, (lowest - pad) / fig.bbox.height))
        cap.set_va("top")
        cap.set_in_layout(True)
    except Exception:  # measurement can fail on exotic layouts; not fatal
        pass
    return cap
