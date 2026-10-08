#!/usr/bin/env python3
"""Figure 3 - cross-scale comparison at *matched* training budgets.

Comparing runs at their own final reward would compare different amounts of
experience (5v5 seed 2 stopped at 2.3M steps, 10v10 seed 1 at 1.86M, others
at 6M).  This figure instead compares every run at four fixed budgets
(1M / 2M / 4M / 6M env steps) with one pre-declared robust statistic:

    matched value = data.matched_budget(rows, budget) = mean reward over the
    [budget - 200,000, budget] env-step bracket (data.MATCHED_WINDOW)

- a window mean, never a single-point spike; a run that never reached the
  budget returns ``None`` and is simply absent (no interpolation, no
  extrapolation), and the same bracket means the same amount of experience at
  every team size.

Panels (one PNG + one PDF)
--------------------------
A. matched reward per enemy vs team size N - one polyline per budget.
   Colour = team size (fixed palette, as everywhere else); budget is carried
   by marker shape (o 1M, s 2M, ^ 4M, D 6M) and by a neutral-grey connector,
   so no size colour is ever re-assigned to a budget.  Each point is tagged
   with its seed count ("n=..."), and error bars (+/- 1 sample s.d. across
   seeds) are drawn ONLY where at least 3 seeds exist - points resting on 1-2
   seeds are drawn as bare markers, exactly as the campaign's data demands
   (2v2: 1 seed, 3v3: 2, 5v5: 3 but only 1 at 6M, 10v10: 2 but 1 beyond 1M).
B. matched reward per enemy vs budget - one line per team size, same
   quantity, same y limits as panel A.  Error bars follow the same >= 3 seed
   rule (only 5v5 at 1M and 2M qualifies).

Scope and honesty rules wired into the drawing code
---------------------------------------------------
* Only the NoWeapon *scaling* family (2v2/3v3/5v5/10v10, generated scaling_*
  configs) forms the comparison.  Its reward is the scale-normalisable one:
  the NoWeapon PostureReward accumulates over enemy aircraft, so reward / N is
  the only normalisation that has a chance of being comparable across N.  It
  is still NOT a unified task-success metric - see the caption limitations.
* The official-config 2v2 run (f6m_official_2v2_noweapon_s0) belongs to a
  different experiment family; it appears in panel A only as hollow markers
  flagged as a different family, never merged into the scaling lines.
* The official 1v1 / SingleControl runs are excluded: different tasks whose
  reward scales differ by an order of magnitude (they must not share a y axis
  with the NvN runs in the first place).
* Extrapolated / interpolated data does not exist anywhere in this module.

Products
--------
figures_v2/fig3_matched_budget.png / .pdf

Every colour, line style and font comes from ``style``; every number comes
from metrics/normalized_scaling.csv via ``data``.
"""

from __future__ import annotations

import textwrap
from statistics import mean, stdev

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullLocator

import data
import style

# Fixed budgets (env steps) and the pre-declared bracket for the matched mean.
BUDGETS = (1_000_000, 2_000_000, 4_000_000, 6_000_000)
WINDOW = data.MATCHED_WINDOW                 # 200k env-step bracket

# Panel A: budget -> marker shape (budget identity is shape, never colour).
BUDGET_MARKER = {1_000_000: "o", 2_000_000: "s", 4_000_000: "^", 6_000_000: "D"}

SIZES = (2, 3, 5, 10)
OFFICIAL_2V2 = "f6m_official_2v2_noweapon_s0"

# The normalised quantity lives in normalized_scaling.csv (reward / N).
VALUE_KEY = "reward_per_enemy"
X_KEY = "env_steps"

# shared limits so the two panels (same quantity) can be read against
# each other; the zero line is a neutral reference, not a series
YLIM = (-3.0, 13.5)
_INK = style.CAPTION_COLOR


# --------------------------------------------------------------------------
# data layer (thin - all averaging is data.matched_budget)
# --------------------------------------------------------------------------
def _load(camp=None):
    """{experiment: rows sorted by env_steps} from normalized_scaling.csv."""
    rows = data.load_normalized() if camp is None else data.load_normalized(camp)
    by_exp = {}
    for r in rows:
        exp = r.get("experiment")
        if exp is None or r.get(X_KEY) is None:
            continue
        by_exp.setdefault(exp, []).append(r)
    for run_rows in by_exp.values():
        run_rows.sort(key=lambda r: r[X_KEY])
    return by_exp


def _matched_per_run(by_exp, exp):
    """{budget: matched reward per enemy | None} - None = budget never reached."""
    if exp not in by_exp:
        return {b: None for b in BUDGETS}
    return {b: data.matched_budget(by_exp[exp], b, window=WINDOW,
                                   value_key=VALUE_KEY, x_key=X_KEY)
            for b in BUDGETS}


def _aggregate(by_exp, exps):
    """{N: {budget: {"mean", "sd", "n", "vals"}}} over the given runs."""
    per_run = {e: _matched_per_run(by_exp, e) for e in exps}
    table = {}
    for n in SIZES:
        table[n] = {}
        for b in BUDGETS:
            vals = [per_run[e][b] for e in exps
                    if data.RUN_META[e]["n"] == n and per_run[e][b] is not None]
            table[n][b] = {
                "vals": vals,
                "mean": mean(vals) if vals else None,
                # sample s.d.; used for error bars only where n >= 3
                "sd": stdev(vals) if len(vals) >= 2 else None,
                "n": len(vals),
            }
    return table


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _zero_line(ax):
    """Neutral reference at reward = 0 (grey belongs to references, not data)."""
    ax.axhline(0.0, color=style.PALETTE["neutral"], lw=0.9, alpha=0.55,
               zorder=1.2)


def _errorbar_if_supported(ax, x, st, color):
    """mean +/- 1 sample s.d. - drawn ONLY where >= 3 seeds support a spread."""
    if st["n"] >= 3 and st["sd"] is not None:
        ax.errorbar([x], [st["mean"]], yerr=[st["sd"]], fmt="none",
                    ecolor=color, elinewidth=1.4, capsize=3.4, capthick=1.2,
                    zorder=3.4)


def _seed_tags(ax, table, gap_frac=0.032):
    """Annotate every point with its seed count, pushing tags apart vertically.

    Tags are plain counts ('n=2'); their association with a budget is not
    needed here because every budget inside one size column is tagged, and
    the caption still lists the counts per point for the record.
    """
    y0, y1 = ax.get_ylim()
    gap = (y1 - y0) * gap_frac
    for n in SIZES:
        col = [(st["mean"], b) for b in BUDGETS
               if (st := table[n][b])["mean"] is not None]
        col.sort(key=lambda t: -t[0])          # top first
        prev = None
        for y_true, b in col:
            y = y_true
            if prev is not None and prev - y < gap:
                y = prev - gap
            prev = y
            ax.annotate(f"n={table[n][b]['n']}", xy=(n, y), xytext=(-6.5, 0),
                        textcoords="offset points", ha="right", va="center",
                        fontsize=8.5, color=_INK, annotation_clip=False)


def _panel_a(ax, table, official):
    """Matched reward per enemy vs team size; one grey polyline per budget."""
    ax.set_xscale("log", base=2)
    ax.set_xlim(1.5, 13.6)          # room for seed tags (left) + end labels
    ax.set_xticks(list(SIZES))
    ax.set_xticklabels([f"{n}v{n}" for n in SIZES])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_ylim(*YLIM)
    _zero_line(ax)

    for b in BUDGETS:
        # grey connector = the budget's trajectory across team sizes; it is
        # scaffolding, so it stays neutral (colour is reserved for team size)
        seg = [(n, table[n][b]["mean"]) for n in SIZES
               if table[n][b]["mean"] is not None]
        if len(seg) >= 2:
            ax.plot([x for x, _ in seg], [y for _, y in seg],
                    color=style.PALETTE["neutral"], lw=1.3, alpha=0.9,
                    zorder=1.6)
        for n, y in seg:
            color = style.color_for_n(n)
            _errorbar_if_supported(ax, n, table[n][b], color)
            ax.plot([n], [y], ls="none", marker=BUDGET_MARKER[b], ms=6.8,
                    mfc=color, mec="white", mew=0.9, zorder=4.2)

    # official-config 2v2 = a DIFFERENT family: one series of hollow rings at
    # the same four budgets, no line, drawn *under* the filled scaling markers
    # so the pairs stay readable wherever the two families nearly coincide
    c2 = style.color_for_n(2)
    o_pts = [(b, official[b]) for b in BUDGETS if official[b] is not None]
    for b, y in o_pts:
        ax.plot([2], [y], ls="none", marker="o", ms=8.2, mfc="white",
                mec=c2, mew=1.5, zorder=3.8)
    if o_pts:
        b_top, y_top = max(o_pts, key=lambda t: t[1])
        ax.annotate("hollow circles = official 2v2\n(a different family)",
                    xy=(2, y_top), xycoords="data",
                    xytext=(0.02, 0.985), textcoords="axes fraction",
                    ha="left", va="top", fontsize=8.5, color=_INK,
                    arrowprops=dict(arrowstyle="->", color=_INK, lw=0.9,
                                    shrinkA=3, shrinkB=4))

    _seed_tags(ax, table)

    ax.set_xlabel("Team size (agents per side)")
    ax.set_ylabel("Reward per enemy (reward / N)")
    ax.set_title("A. Matched reward per enemy vs team size")
    # direct end labels, placed top-down so the automatic stacking stays tidy
    ends = [(b, table[SIZES[-1]][b]["mean"]) for b in BUDGETS
            if table[SIZES[-1]][b]["mean"] is not None]
    for b, y in sorted(ends, key=lambda t: -t[1]):
        style.add_end_label(ax, SIZES[-1], y, style.fmt_steps(b),
                            style.PALETTE["neutral"])


def _panel_b(ax, table):
    """Same matched values, now as one line per team size over the budgets."""
    ax.set_xscale("log", base=2)
    ax.set_xlim(0.92e6, 7.4e6)      # room for end labels right of 6M
    ax.set_xticks(list(BUDGETS))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: style.fmt_steps(v)))
    ax.set_ylim(*YLIM)
    _zero_line(ax)

    for n in SIZES:
        color = style.color_for_n(n)
        xs = [b for b in BUDGETS if table[n][b]["mean"] is not None]
        ys = [table[n][b]["mean"] for b in xs]
        ax.plot(xs, ys, color=color, lw=style.SMOOTH_LW, alpha=1.0,
                marker="o", ms=6.2, mfc=color, mec="white", mew=0.9, zorder=4)
        for b in xs:
            _errorbar_if_supported(ax, b, table[n][b], color)
        if xs:
            style.add_end_label(ax, xs[-1], ys[-1], f"{n}v{n}", color)

    ax.set_xlabel("Training budget (environment steps)")
    ax.set_ylabel("Reward per enemy (reward / N)")
    ax.set_title("B. Matched reward per enemy vs budget")


# --------------------------------------------------------------------------
# caption + figure
# --------------------------------------------------------------------------
# One paragraph per statement; textwrap fits them into the figure width so a
# long limitations note can never stretch the tight bbox (the caption must
# stay inside the same 13.4in canvas as the axes).
CAPTION_PARAGRAPHS = (
    "Matched value = mean reward per enemy over the fixed "
    "[budget - 200k, budget] env-step bracket (data.MATCHED_WINDOW) of "
    "metrics/normalized_scaling.csv; a budget a run never reached is omitted "
    "- nothing is interpolated.",
    "Seeds per point at 1M/2M/4M/6M: 2v2 1/1/1/1, 3v3 2/2/2/2, "
    "5v5 3/3/2/1, 10v10 2/1/1/1. Error bars = +/-1 sample s.d. across seeds, "
    "drawn only where >= 3 seeds exist; points on 1-2 seeds carry no interval.",
    "Panel A: shape = budget (o 1M, s 2M, ^ 4M, D 6M), colour = team size, "
    "grey line = the budget's trajectory across team sizes. Hollow circles = "
    "the official-config 2v2 run (a different config family, 1 seed) at the "
    "same four budgets, shown for reference only; the official 1v1 / "
    "SingleControl runs are excluded (different tasks, reward scales an "
    "order of magnitude apart).",
    "LIMITS: reward/N normalisation is only meaningful inside the NoWeapon "
    "family (its PostureReward accumulates over enemy aircraft) and is not a "
    "unified task-success metric; different N are different tasks (scale, "
    "reward make-up and difficulty all differ), so more reward per enemy does "
    "not mean a higher win rate. No reliable win-rate or common evaluation "
    "metric exists for these runs - this is an exploratory comparison of "
    "training reward.",
    "Lines join the means over the seeds available at each budget, so a "
    "point's seed set can shrink at later budgets; no run or seed is dropped "
    "or filled in.",
)
_CAPTION_WIDTH = 200          # chars per line at 8.5pt on a 13.4in figure


def _caption_text():
    lines = []
    for para in CAPTION_PARAGRAPHS:
        lines.extend(textwrap.wrap(para, width=_CAPTION_WIDTH) or [""])
    return "\n".join(lines)


def build(camp=None, out_dir=None):
    """Build fig3 (two panels, one PNG + one PDF); returns (png, pdf)."""
    style.apply_style()

    by_exp = _load(camp)
    scaling_runs = data.runs_of(family="scaling")
    table = _aggregate(by_exp, scaling_runs)
    official = _matched_per_run(by_exp, OFFICIAL_2V2)

    # Manual axes (not plt.subplots): style.save() re-runs fig.tight_layout(),
    # which would silently expand subplot axes over the caption.  The bottom
    # margin is measured from the *rendered* caption height instead of guessed.
    width_in, height_in = 13.4, 7.8
    fig = plt.figure(figsize=(width_in, height_in))
    cap = style.caption(fig, _caption_text())
    fig.canvas.draw()
    cap_top_in = cap.get_window_extent(fig.canvas.get_renderer()).y1 / fig.dpi

    bottom = (cap_top_in + 0.45) / height_in    # caption + tick labels + xlabel
    top = 0.90
    ax_a = fig.add_axes([0.055, bottom, 0.400, top - bottom])
    ax_b = fig.add_axes([0.545, bottom, 0.400, top - bottom])

    _panel_a(ax_a, table, official)
    _panel_b(ax_b, table)

    fig.suptitle("Equal-budget cross-scale comparison: matched reward per "
                 "enemy (NoWeapon scaling family)", fontsize=13, y=0.975)

    return style.save(fig, "fig3_matched_budget", out_dir=out_dir)


if __name__ == "__main__":
    png, pdf = build()
    print(f"{png}\n{pdf}")
    for name in (png, pdf):
        print(f"  {name.name}: {name.stat().st_size / 1024:.1f} KB")
