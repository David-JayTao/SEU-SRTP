#!/usr/bin/env python
"""Reward-normalised cross-N comparison of the centralised critic diagnostics.

Why this is necessary
---------------------
`PostureReward.get_reward()` accumulates `orientation * range` over **every**
enemy while `PostureReward_scale` is held at 15.0 for every scenario we run, so
the per-step reward magnitude grows linearly with team size N. Raw reward,
value_loss and grad-norm are therefore NOT comparable across N: part of any
increase is just the reward scale, not a learning phenomenon.

The normalisation used here is derived from the reward structure, not fitted:
  * reward          -> reward / N        removes the sum-over-enemies factor
  * value_loss      -> value_loss / N^2  value targets scale like the return,
                                         and a squared loss scales like its square
  * critic_grad_norm-> grad_norm / N     gradient magnitude scales with the target

A quantity that is *purely* reward-scale would come out constant after this
normalisation. Anything that keeps growing is a residual effect worth naming.

Only the hierarchical_noWeapon family is compared: same task class
(`hierarchical_multiplecombat`), same reward config, same action space. The
non-hierarchical `2v2/NoWeapon/Selfplay` uses a different action space (raw
4-dim control) and `1/heading` is a single-agent control task with its own
reward, so both are excluded from the cross-N series.
"""
import csv
import glob
import os
import re

EXP = "/root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night"
CURVES = os.path.join(EXP, "metrics/curves")
OUT = os.path.join(EXP, "metrics/normalized_scaling.csv")

SERIES = [
    # (regex on experiment name, N, label)
    (r"^official_2v2_noweapon$", 2, "2v2 official (hier, 2v2 template)"),
    (r"^scaling_(\d+)v\d+_noweapon(_s\d)?$", None, "scaling noweapon"),
]


def rows_for(path, exp, n, label):
    out = []
    for r in csv.DictReader(open(path)):
        def g(k):
            try:
                return float(r[k])
            except (KeyError, TypeError, ValueError):
                return None
        rw, vl, cg = g("average_episode_rewards"), g("value_loss"), g("critic_grad_norm")
        if rw is None or vl is None:
            continue
        out.append({
            "experiment": exp, "label": label, "team_size": n,
            "total_agents": 2 * n, "episode": int(r["episode"]),
            "env_steps": int(r["total_num_steps"]), "fps": g("fps"),
            "reward": rw, "reward_per_enemy": rw / n,
            "value_loss": vl, "value_loss_per_N2": vl / (n * n),
            "critic_grad_norm": cg,
            "critic_grad_norm_per_N": (cg / n) if cg is not None else None,
            "entropy_loss": g("policy_entropy_loss"),
            "policy_loss": g("policy_loss"),
        })
    return out


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(CURVES, "*.csv"))):
        exp = os.path.basename(path)[:-4]
        if exp == "official_2v2_noweapon":
            rows += rows_for(path, exp, 2, "2v2 official hier")
            continue
        m = re.match(r"^scaling_(\d+)v\d+_noweapon(_s\d)?$", exp)
        if m:
            rows += rows_for(path, exp, int(m.group(1)), "scaling noweapon")

    if not rows:
        print("no data yet")
        return
    rows.sort(key=lambda r: (r["team_size"], r["experiment"], r["episode"]))

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows)\n")

    # matched-stage comparison: episode index equal across scales
    print("=== matched training stage (episode index), hierarchical NoWeapon family ===")
    print(f"{'N':>3} {'ep':>3} {'reward':>9} {'rew/N':>8} {'vl':>9} {'vl/N²':>8} "
          f"{'critic_gn':>10} {'gn/N':>7}  experiment")
    for r in rows:
        if r["episode"] > 4:
            continue
        cg = r["critic_grad_norm"]
        print(f"{r['team_size']:>3} {r['episode']:>3} {r['reward']:>9.2f} "
              f"{r['reward_per_enemy']:>8.2f} {r['value_loss']:>9.3f} "
              f"{r['value_loss_per_N2']:>8.3f} "
              f"{(cg if cg is not None else float('nan')):>10.2f} "
              f"{(r['critic_grad_norm_per_N'] if r['critic_grad_norm_per_N'] is not None else float('nan')):>7.2f}  "
              f"{r['experiment']}")


if __name__ == "__main__":
    main()
