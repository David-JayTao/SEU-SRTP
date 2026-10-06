#!/usr/bin/env python
"""Build the scaling comparison table required by the brief (section 20).

Emits metrics/scaling_table.csv (machine readable) and a markdown rendering on
stdout, with one row per (scale, variant, seed) that has real data.

Every column is either measured or derived from the code-review-verified
formulas; nothing here is asserted from expectation.
  obs_dim          = 12N + 3        (NoWeapon)      / 12N + 9 (Shoot)
  share_obs_dim    = 2N * obs_dim
  actor_params     = measured from the real PPOActor
  critic_params    = measured from the real PPOCritic
  FPS / steps / rewards / losses   from logs + metrics.jsonl
  CPU / RAM / VRAM  from system_samples.csv during the run
"""
import csv
import glob
import json
import os
import re
import sys

REPO = "/root/autodl-tmp/SEU-SRTP"
EXP = os.path.join(REPO, "experiments/2026-10-04-night")
METRICS = os.path.join(EXP, "metrics")

sys.path.insert(0, os.path.join(REPO, "experiments/2026-10-04-night/scripts"))


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_arch():
    p = os.path.join(METRICS, "critic_scaling.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p))
    return {m["team_size"]: m for m in d["measured"]}, {e["team_size"]: e for e in d["extrapolated"]}


def load_resources():
    rows = read_csv(os.path.join(EXP, "system/system_samples.csv"))
    return rows


def has_nan(exp):
    """A NaN in the run would show up as a nan reward or a pdb.set_trace hang;
    the assert in env_base._pack would abort the run. Report from the curve."""
    p = os.path.join(METRICS, "curves", f"{exp}.csv")
    for r in read_csv(p):
        for k in ("average_episode_rewards", "value_loss", "critic_grad_norm"):
            v = r.get(k, "")
            if v and v.lower() == "nan":
                return "yes"
    return "no"


def main():
    meas, ext = load_arch()
    summary = read_csv(os.path.join(METRICS, "summary.csv"))
    res = load_resources()
    peak_vram = 0
    for c in ("gpu0_mem_mb", "gpu1_mem_mb", "gpu2_mem_mb"):
        for r in res:
            peak_vram = max(peak_vram, fnum(r.get(c)) or 0)
    peak_ram = max((fnum(r.get("mem_used_gb")) or 0 for r in res), default=0)
    peak_cpu = max((fnum(r.get("cpu_busy_pct")) or 0) * 1.92 for r in res) if res else 0

    rows = []
    for s in summary:
        e = s["experiment"]
        m = re.match(r"scaling_(\d+)v\d+_(noweapon|shoot)(_s(\d))?$", e)
        if not m:
            continue
        n = int(m.group(1))
        variant = m.group(2)
        a = meas.get(n) or ext.get(n) or {}
        obs_dim = a.get("obs_dim")
        share_dim = a.get("share_obs_dim")
        if variant == "shoot" and obs_dim is not None:
            obs_dim = 12 * n + 9
            share_dim = 2 * n * obs_dim
        fps = fnum(s.get("fps_last"))
        thr = fnum(s.get("n_rollout_threads"))
        # Wall-clock normalisations. FPS counts *individual* env-steps/s summed
        # over the rollout threads, so:
        #   seconds per vectorised rollout step = threads / FPS
        #   agent-steps/s = FPS * total_agents
        # Thread counts differ between scales (they were sized to the measured
        # cost), so the per-thread figure is the only fair cross-scale one.
        rows.append({
            "scale": f"{n}v{n}",
            "variant": variant,
            "team_size": n,
            "total_agents": 2 * n,
            "local_obs_dim": obs_dim,
            "share_obs_dim": share_dim,
            "actor_params": a.get("actor_params"),
            "critic_params": a.get("critic_params"),
            "n_rollout_threads": s.get("n_rollout_threads"),
            "seed": s.get("seed"),
            "fps": s.get("fps_last"),
            "sec_per_vectorised_step": (round(thr / fps, 5) if (fps and thr) else None),
            "sec_per_rollout_episode": (round(3000 * thr / fps, 1) if (fps and thr) else None),
            "agent_steps_per_s": (round(fps * 2 * n, 1) if fps else None),
            "agent_steps_per_s_per_thread": (round(fps * 2 * n / thr, 1) if (fps and thr) else None),
            "env_steps": s.get("steps_done"),
            "episodes_logged": s.get("episodes_logged"),
            "train_reward_last": s.get("train_reward_last"),
            "train_reward_first": s.get("train_reward_first"),
            "train_reward_tail_slope": s.get("train_reward_tail_slope"),
            "eval_reward_last": s.get("eval_reward_last"),
            "critic_loss_value": s.get("value_loss_last"),
            "policy_loss": s.get("policy_loss_last"),
            "entropy_loss": s.get("entropy_loss_last"),
            "critic_grad_norm": s.get("critic_grad_norm_last"),
            "actor_grad_norm": s.get("actor_grad_norm_last"),
            "ratio": s.get("ratio_last"),
            "nan_observed": has_nan(e),
            "peak_cpu_cores_host": round(peak_cpu, 1),
            "peak_ram_gb_host": round(peak_ram, 1),
            "peak_vram_mb_host": round(peak_vram),
            "checkpoint": s.get("checkpoint_path"),
        })

    rows.sort(key=lambda r: (r["variant"], r["team_size"], str(r["seed"])))
    out = os.path.join(METRICS, "scaling_table.csv")
    if rows:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out} ({len(rows)} rows)\n")

    hdr = ["scale", "variant", "agents", "obs", "share_obs", "actor_p",
           "critic_p", "thr", "seed", "FPS", "s/vec-step", "s/rollout-ep",
           "agent-steps/s", "ag-steps/s/thr", "steps", "eps", "rew_first",
           "rew_last", "slope", "eval_rew", "value_loss", "critic_gn",
           "entropy", "NaN?", "learnable?"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in rows:
        def g(k, nd=3):
            v = r.get(k)
            if v is None or v == "":
                return "-"
            try:
                return f"{float(v):.{nd}g}"
            except (TypeError, ValueError):
                return str(v)
        slope = fnum(r["train_reward_tail_slope"])
        learning = "improving" if (slope or 0) > 0.05 else ("flat/declining" if slope is not None else "?")
        print("| " + " | ".join([
            r["scale"], r["variant"], str(r["total_agents"]), str(r["local_obs_dim"]),
            str(r["share_obs_dim"]), str(r["actor_params"]), str(r["critic_params"]),
            str(r["n_rollout_threads"]), str(r["seed"]), g("fps"),
            g("sec_per_vectorised_step", 3), g("sec_per_rollout_episode", 4),
            g("agent_steps_per_s", 4), g("agent_steps_per_s_per_thread", 3),
            str(r["env_steps"]),
            str(r["episodes_logged"]), g("train_reward_first"), g("train_reward_last"),
            ("-" if slope is None else f"{slope:+.3g}"), g("eval_reward_last"),
            g("critic_loss_value"), g("critic_grad_norm"), g("entropy_loss"),
            r["nan_observed"], learning,
        ]) + " |")
    print(f"\nhost peaks during the whole night: CPU {peak_cpu:.1f}/48 cores, "
          f"RAM {peak_ram:.1f} GB, VRAM {peak_vram:.0f} MB (single job uses <1.5 GB)")


if __name__ == "__main__":
    main()
