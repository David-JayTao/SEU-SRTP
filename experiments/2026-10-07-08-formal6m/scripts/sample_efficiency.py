#!/usr/bin/env python
"""Matched-step sample-efficiency comparison across N.

"Steps to reach threshold X" is not usable here: no scale has converged, so any
threshold would be picked to flatter whichever run happened to clear it. Instead
this reports reward AT matched step counts, plus the spread across seeds, and
states explicitly where a scale has too few episodes to say anything.

Two normalisations are given because the raw numbers are not comparable:
  reward / N        removes the PostureReward sum-over-enemies factor
                    (exact for the NoWeapon family ONLY -- see
                    normalized_scaling.py; never apply to ShootMissile)
  step-matched     all scales sampled at the same total_num_steps

Size env-steps means VECTORISED steps (n_rollout_threads * 3000 per update), the
runner's own `total_num_steps` accounting.

Default budget grid covers both campaigns:
  150k..900k   the 2026-10-04 pilot grid, kept so the two campaigns compare
  1M..6M       the formal 6M campaign grid (matched budgets at the new budget)

Partial runs are handled explicitly: a budget the run has not reached reports
its latest real measurement and the actual step, flagged "~" when that step is
below 75% of the requested budget.

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/sample_efficiency.py -> parents[1] = <campaign>), so the
same script targets whichever campaign it is copied into. Explicit overrides
for cross-campaign comparisons (point the READS at the foreign campaign and the
writes back home, so the foreign campaign stays untouched):
    --campaign-root DIR / CAMPAIGN_ROOT   campaign that is read
    --out-dir DIR       / OUT_DIR         where sample_efficiency.csv goes
                                          (default: <campaign-root>/metrics)

Usage: python sample_efficiency.py [--campaign-root DIR] [--out-dir DIR]
                                   [--steps 150000 ...]
"""
import argparse
import csv
import glob
import os
import re
import statistics
from pathlib import Path

DEFAULT_CAMPAIGN = Path(__file__).resolve().parents[1]

DEFAULT_STEPS = [150000, 300000, 450000, 600000, 750000, 900000,
                 1000000, 2000000, 3000000, 4000000, 5000000, 6000000]

# Scaling-run names, both campaign generations (same rule as scaling_table.py):
#   pilot 2026-10-04 night : scaling_<N>v<N>_noweapon[_s<seed>]
#   formal 6M campaign     : f6m_<N>v<N>_noweapon_s<seed>
SCALING_RE = re.compile(r"^(?:scaling_|f6m_)(\d+)v\d+_noweapon(?:_s(\d))?$")

MIN_EPISODES_FOR_CLAIM = 4


def load(curves_dir):
    """experiment -> (N, seed, [(steps, reward), ...]) sorted by step."""
    runs = {}
    for path in sorted(glob.glob(os.path.join(curves_dir, "*.csv"))):
        e = os.path.basename(path)[:-4]
        m = SCALING_RE.match(e)
        if not m:
            continue
        n = int(m.group(1))
        seed = m.group(2) or "0"
        pts = []
        for r in csv.DictReader(open(path)):
            try:
                pts.append((int(r["total_num_steps"]),
                            float(r["average_episode_rewards"])))
            except (KeyError, TypeError, ValueError):
                continue
        pts.sort()
        if pts:
            runs[e] = (n, seed, pts)
    return runs


def reward_at(pts, step):
    """Latest (step, reward) at or before `step`; reward is noisy, never interpolated.

    Returns the ACTUAL step alongside the value so a sparse run cannot look like
    a dense one: a scale with 5 episodes would otherwise print the same number
    in every column and read as a measured plateau.
    """
    best = None
    for s, r in pts:
        if s <= step:
            best = (s, r)
        else:
            break
    return best


def budget_label(s):
    return f"{s // 1000000}M" if s % 1000000 == 0 else f"{s // 1000}k"


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--campaign-root", default=os.environ.get("CAMPAIGN_ROOT"),
                   help="campaign that is read; default: derived from this "
                        f"script's location ({DEFAULT_CAMPAIGN})")
    p.add_argument("--out-dir", default=os.environ.get("OUT_DIR"),
                   help="where sample_efficiency.csv is written; default: "
                        "<campaign-root>/metrics (set this to keep a foreign "
                        "campaign untouched when comparing across campaigns)")
    p.add_argument("--steps", type=int, nargs="+", default=DEFAULT_STEPS,
                   help="matched budgets in vectorised env steps "
                        "(default: pilot 150k..900k + formal 1M..6M)")
    args = p.parse_args(argv)

    campaign = (Path(args.campaign_root).expanduser().resolve()
                if args.campaign_root else DEFAULT_CAMPAIGN)
    out_dir = (Path(args.out_dir).expanduser().resolve()
               if args.out_dir else campaign / "metrics")

    runs = load(campaign / "metrics" / "curves")
    if not runs:
        print("no scaling runs with data yet")
        return
    out_path = out_dir / "sample_efficiency.csv"

    rows = []
    for e, (n, seed, pts) in sorted(runs.items()):
        rec = {"experiment": e, "team_size": n, "seed": seed,
               "episodes": len(pts), "max_steps": pts[-1][0]}
        for s in args.steps:
            got = reward_at(pts, s)
            rec[f"reward@{s}"] = None if got is None else round(got[1], 4)
            rec[f"actual_step@{s}"] = None if got is None else got[0]
            rec[f"reward_per_enemy@{s}"] = None if got is None else round(got[1] / n, 4)
        rows.append(rec)

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} runs)\n")

    print("=== reward at matched environment steps (NoWeapon family) ===")
    print("(reward per enemy in brackets; '-' = not reached; '~' = nearest")
    print(" measurement is below 75% of the requested step, i.e. do not read that")
    print(" column as if the run had a measurement there)\n")
    hdr = ["N", "seed"] + [budget_label(s) for s in args.steps] + ["eps", "max_steps"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in sorted(rows, key=lambda x: (x["team_size"], str(x["seed"]))):
        cells = [str(r["team_size"]), str(r["seed"])]
        for s in args.steps:
            v, pv = r[f"reward@{s}"], r[f"reward_per_enemy@{s}"]
            av = r[f"actual_step@{s}"]
            # flag when the nearest measurement is far from the requested step
            tag = "" if (av is None or av >= 0.75 * s) else "~"
            cells.append("-" if v is None else f"{v:.2f} ({pv:.2f}){tag}")
        cells += [str(r["episodes"]), str(r["max_steps"])]
        print("| " + " | ".join(cells) + " |")

    print("\n=== per-scale summary at the last requested budget ===")
    print("| N | runs | mean reward/N | spread (min..max) | enough episodes? |")
    print("|---|---|---|---|---|")
    by_n = {}
    for r in rows:
        by_n.setdefault(r["team_size"], []).append(r)
    fell_back = []
    for n in sorted(by_n):
        vals, ok = [], []
        for r in by_n[n]:
            v = r[f"reward_per_enemy@{args.steps[-1]}"]
            if v is None:
                # No measurement at or below the final budget for this run (only
                # possible with custom --steps): use its latest real
                # measurement -- never an interpolation -- and say so below.
                n_, seed_, pts = runs[r["experiment"]]
                v = pts[-1][1] / n_
                fell_back.append(f"{r['experiment']}@{pts[-1][0]}")
            if v is not None:
                vals.append(v)
            ok.append(r["episodes"] >= MIN_EPISODES_FOR_CLAIM)
        if not vals:
            continue
        spread = f"{min(vals):.2f} .. {max(vals):.2f}"
        enough = "yes" if all(ok) else "NO (too few episodes)"
        print(f"| {n}v{n} | {len(vals)} | {statistics.mean(vals):+.2f} | {spread} | {enough} |")
    if fell_back:
        print(f"\nnote: no measurement at/below the last budget for: "
              f"{', '.join(fell_back)} -- latest real measurement used instead")


if __name__ == "__main__":
    main()
