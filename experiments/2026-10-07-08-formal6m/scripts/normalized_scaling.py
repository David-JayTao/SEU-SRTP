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

IMPORTANT: the reward/N convention ("reward per enemy") is exact ONLY for the
**NoWeapon** family, whose per-step reward literally sums over enemies
(`for enm in env.agents[agent_id].enemies` in PostureReward.get_reward). It must
NOT be applied to the **ShootMissile** family: those scenarios add
MissilePostureReward (a missile-relative term, not a per-enemy sum) and their
EventDrivenReward hit/kill events do not aggregate per enemy, so dividing by N
has no derivation there. (The value_loss/N^2 and grad_norm/N columns inherit
the same restriction, since they follow from the reward scaling.)

A quantity that is *purely* reward-scale would come out constant after this
normalisation. Anything that keeps growing is a residual effect worth naming.

Only the hierarchical_noWeapon family is compared: same task class
(`hierarchical_multiplecombat`), same reward config, same action space. The
non-hierarchical `2v2/NoWeapon/Selfplay` uses a different action space (raw
4-dim control) and `1/heading` is a single-agent control task with its own
reward, so both are excluded from the cross-N series.

Partial runs are fine: a run with only a few logged episodes contributes those
episodes; rows missing value_loss are skipped.

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/normalized_scaling.py -> parents[1] = <campaign>), so the
same script targets whichever campaign it is copied into. Explicit overrides
for cross-campaign comparisons (point the READS at the foreign campaign and the
writes back home, so the foreign campaign stays untouched):
    --campaign-root DIR / CAMPAIGN_ROOT   campaign that is read
    --out-dir DIR       / OUT_DIR         where normalized_scaling.csv goes
                                          (default: <campaign-root>/metrics)
"""
import argparse
import csv
import glob
import os
import re
from pathlib import Path

DEFAULT_CAMPAIGN = Path(__file__).resolve().parents[1]

# Cross-N series, both campaign generations:
#   pilot 2026-10-04 night : official_2v2_noweapon / scaling_<N>v<N>_noweapon[_s<k>]
#   formal 6M campaign     : f6m_official_2v2_noweapon_s0 / f6m_<N>v<N>_noweapon_s0
OFFICIAL_2V2_RE = re.compile(r"^(?:f6m_)?official_2v2_noweapon(?:_s\d)?$")
SCALING_NOWEAPON_RE = re.compile(r"^(?:scaling_|f6m_)(\d+)v\d+_noweapon(?:_s\d)?$")


def resolve_paths(argv=None):
    """(campaign read, metrics dir written).

    --campaign-root / $CAMPAIGN_ROOT selects the campaign that is read;
    --out-dir / $OUT_DIR selects where outputs go (default: that campaign's
    metrics/). Splitting the two is what lets a cross-campaign comparison read
    a foreign campaign without writing anything into it.
    """
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--campaign-root", default=None)
    ap.add_argument("--out-dir", default=None)
    ns, _ = ap.parse_known_args(argv)
    root = ns.campaign_root or os.environ.get("CAMPAIGN_ROOT")
    campaign = Path(root).expanduser().resolve() if root else DEFAULT_CAMPAIGN
    out = ns.out_dir or os.environ.get("OUT_DIR")
    out_dir = Path(out).expanduser().resolve() if out else campaign / "metrics"
    return campaign, out_dir


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
            # reward_per_enemy = reward / N. Exact only for the NoWeapon family
            # (PostureReward sums over enemies); NEVER apply to ShootMissile.
            "reward": rw, "reward_per_enemy": rw / n,
            "value_loss": vl, "value_loss_per_N2": vl / (n * n),
            "critic_grad_norm": cg,
            "critic_grad_norm_per_N": (cg / n) if cg is not None else None,
            "entropy_loss": g("policy_entropy_loss"),
            "policy_loss": g("policy_loss"),
        })
    return out


def main(argv=None):
    campaign, out_dir = resolve_paths(argv)
    curves = campaign / "metrics" / "curves"
    out_path = out_dir / "normalized_scaling.csv"

    rows = []
    for path in sorted(glob.glob(os.path.join(curves, "*.csv"))):
        exp = os.path.basename(path)[:-4]
        if OFFICIAL_2V2_RE.match(exp):
            rows += rows_for(path, exp, 2, "2v2 official hier")
            continue
        m = SCALING_NOWEAPON_RE.match(exp)
        if m:
            rows += rows_for(path, exp, int(m.group(1)), "scaling noweapon")

    if not rows:
        print("no data yet")
        return
    rows.sort(key=lambda r: (r["team_size"], r["experiment"], r["episode"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} rows)\n")

    # Mean over the first K episodes. Episode 0 alone is a single point; this is
    # the version that should be quoted, with its episode count attached.
    K = 5
    print(f"=== mean over the first {K} episodes per run (hierarchical NoWeapon family) ===")
    print("(value_loss/N^2 and grad_norm/N remove the reward-magnitude growth; "
          "a purely reward-scale effect would make both constant)")
    print(f"\n{'N':>3} {'runs':>5} {'eps':>4} {'reward/N':>9} {'vl/N^2':>8} "
          f"{'gn/N':>7}  sd(vl/N^2)  sd(gn/N)")
    by_n = {}
    for r in rows:
        if r["episode"] < K:
            by_n.setdefault(r["team_size"], []).append(r)
    import statistics as _st
    for n in sorted(by_n):
        rs = by_n[n]
        rw = [r["reward_per_enemy"] for r in rs]
        vl = [r["value_loss_per_N2"] for r in rs]
        gn = [r["critic_grad_norm_per_N"] for r in rs if r["critic_grad_norm_per_N"] is not None]
        exps = {r["experiment"] for r in rs}
        print(f"{n:>3} {len(exps):>5} {len(rs):>4} {_st.mean(rw):>9.3f} "
              f"{_st.mean(vl):>8.3f} {_st.mean(gn) if gn else float('nan'):>7.3f}  "
              f"{( _st.pstdev(vl) if len(vl) > 1 else 0):>10.4f}  "
              f"{(_st.pstdev(gn) if len(gn) > 1 else 0):>8.4f}")

    # matched-stage comparison: episode index equal across scales
    print("\n=== matched training stage (episode index), hierarchical NoWeapon family ===")
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
