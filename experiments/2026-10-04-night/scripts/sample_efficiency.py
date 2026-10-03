#!/usr/bin/env python
"""Matched-step sample-efficiency comparison across N.

"Steps to reach threshold X" is not usable here: no scale has converged, so any
threshold would be picked to flatter whichever run happened to clear it. Instead
this reports reward AT matched step counts, plus the spread across seeds, and
states explicitly where a scale has too few episodes to say anything.

Two normalisations are given because the raw numbers are not comparable:
  reward / N        removes the PostureReward sum-over-enemies factor
                    (exact for the NoWeapon family; see nvn_scalability_audit.md)
  step-matched     all scales sampled at the same total_num_steps

Usage: python sample_efficiency.py [--steps 300000 600000 900000]
"""
import argparse
import csv
import glob
import os
import re
import statistics

EXP = "/root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night"
CURVES = os.path.join(EXP, "metrics/curves")
OUT = os.path.join(EXP, "metrics/sample_efficiency.csv")

MIN_EPISODES_FOR_CLAIM = 4


def load():
    """experiment -> (N, seed, [(steps, reward, eval_reward)])"""
    runs = {}
    for path in sorted(glob.glob(os.path.join(CURVES, "*.csv"))):
        e = os.path.basename(path)[:-4]
        m = re.match(r"scaling_(\d+)v\d+_noweapon(?:_s(\d))?$", e)
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, nargs="+",
                   default=[150000, 300000, 450000, 600000, 750000, 900000])
    args = p.parse_args()

    runs = load()
    if not runs:
        print("no scaling runs with data yet")
        return

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

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} runs)\n")

    print("=== reward at matched environment steps (NoWeapon family) ===")
    print("(reward per enemy in brackets; '-' = not reached; '~' = nearest")
    print(" measurement is below 75% of the requested step, i.e. do not read that")
    print(" column as if the run had a measurement there)\n")
    hdr = ["N", "seed"] + [f"{s//1000}k" for s in args.steps] + ["eps", "max_steps"]
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

    print("\n=== per-scale summary at the last common step ===")
    print("| N | runs | mean reward/N | spread (min..max) | enough episodes? |")
    print("|---|---|---|---|---|")
    by_n = {}
    for r in rows:
        by_n.setdefault(r["team_size"], []).append(r)
    for n in sorted(by_n):
        vals, ok = [], []
        for r in by_n[n]:
            v = r[f"reward_per_enemy@{args.steps[-1]}"]
            if v is None:
                v = r[f"reward_per_enemy@{max(args.steps[0], r['max_steps'])}"]
            if v is not None:
                vals.append(v)
            ok.append(r["episodes"] >= MIN_EPISODES_FOR_CLAIM)
        if not vals:
            continue
        spread = f"{min(vals):.2f} .. {max(vals):.2f}"
        enough = "yes" if all(ok) else "NO (too few episodes)"
        print(f"| {n}v{n} | {len(vals)} | {statistics.mean(vals):+.2f} | {spread} | {enough} |")


if __name__ == "__main__":
    main()
