#!/usr/bin/env python
"""Measure the *actual* entropy of a saved policy's action distribution.

Why this is needed
------------------
`metrics.jsonl` carries `policy_entropy_loss`, but `ACTLayer.evaluate_actions`
divides the per-dimension entropy by the batch size before summing
(`action_dist.entropy() / action_log_probs[-1].size(0)`, then `.sum(-1)`), so
the logged number is (sum of per-dim entropies) / batch_rows. The batch size
depends on n_rollout_threads, buffer_size, num_mini_batch and data_chunk_length,
so the logged entropy is NOT comparable across runs -- and in particular varies
systematically with team size.

This script bypasses that entirely: it loads the checkpoint, pushes a batch of
observations through the actor, and reports the real mean per-dimension
Categorical entropy plus its fraction of the maximum. That number is directly
comparable across scales.

Usage:
  python policy_entropy_probe.py --run-dir <runN> [--scenario ...] [--env-name ...]
                                 [--batch 4096] [--fresh]
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import torch

REPO = "/root/autodl-tmp/SEU-SRTP"
sys.path.insert(0, REPO)
os.chdir(REPO)

from config import get_config                       # noqa: E402
from gymnasium import spaces                        # noqa: E402
from algorithms.mappo.ppo_policy import PPOPolicy    # noqa: E402
from algorithms.ppo.ppo_policy import PPOPolicy as PPOPolicy1v1  # noqa: E402


def infer_dims(run_dir):
    parts = os.path.normpath(run_dir).split(os.sep)
    idx = parts.index("results")
    env_name = parts[idx + 1]
    scenario = "/".join(parts[idx + 2:-3])
    algo = parts[-2]
    return env_name, scenario, algo


def entropy_of(policy, obs, act_space, device):
    nvec = np.atleast_1d(act_space.nvec if hasattr(act_space, "nvec")
                         else [act_space.n])
    is_multi = hasattr(act_space, "nvec")
    x = torch.as_tensor(obs, dtype=torch.float32, device=device)
    total = 0.0
    max_total = 0.0
    per_dim = []
    with torch.no_grad():
        feats = policy.actor.base(x)
        if policy.actor.use_recurrent_policy:
            rnn = torch.zeros((x.shape[0], policy.actor.recurrent_hidden_layers,
                               policy.actor.recurrent_hidden_size), device=device)
            masks = torch.ones((x.shape[0], 1), device=device)
            feats, _ = policy.actor.rnn(feats, rnn, masks)
        if getattr(policy.actor.act, "_mlp_actlayer", False):
            feats = policy.actor.act.mlp(feats)
        outs = (policy.actor.act.action_outs if (is_multi or
                getattr(policy.actor.act, "_shoot_action", False))
                else [policy.actor.act.action_out])
        for out, n in zip(outs, nvec):
            d = out(feats)
            try:
                h = d.entropy()
            except AttributeError:
                d = d.dist if hasattr(d, "dist") else d
                h = d.entropy()
            h = h.reshape(-1).mean().item()
            per_dim.append({"dim_size": int(n), "entropy": round(h, 4),
                            "max": round(math.log(n), 4),
                            "frac_of_max": round(h / math.log(n), 4)})
            total += h
            max_total += math.log(n)
    return {
        "per_dim": per_dim,
        "total_entropy": round(total, 4),
        "max_total_entropy": round(max_total, 4),
        "fraction_of_max": round(total / max_total, 4) if max_total else None,
        "n_dims": len(nvec),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--scenario", default=None)
    p.add_argument("--env-name", default=None)
    p.add_argument("--batch", type=int, default=4096)
    p.add_argument("--fresh", action="store_true",
                   help="measure an untrained policy instead of the checkpoint")
    p.add_argument("--rollout-steps", type=int, default=200,
                   help="collect real observations for this many env steps; "
                        "random inputs are off-distribution and overstate entropy")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    env_name, scenario, algo = infer_dims(args.run_dir)
    env_name = args.env_name or env_name
    scenario = args.scenario or scenario

    parser = get_config()
    all_args = parser.parse_known_args([])[0]
    all_args.hidden_size = "128 128"
    all_args.act_hidden_size = "128 128"
    all_args.recurrent_hidden_size = 128
    all_args.recurrent_hidden_layers = 1
    all_args.use_recurrent_policy = True
    all_args.gain = 0.01
    all_args.activation_id = 1
    all_args.use_feature_normalization = False

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # Action space + obs dim come from the scenario so the architecture matches.
    is_multi = env_name == "MultipleCombat"
    if is_multi:
        from envs.JSBSim.envs import MultipleCombatEnv
        env = MultipleCombatEnv(scenario)
        obs_space, act_space = env.observation_space, env.action_space
        policy = PPOPolicy(all_args, obs_space, env.share_observation_space,
                           act_space, device=device)
    else:
        from envs.JSBSim.envs import SingleCombatEnv, SingleControlEnv
        env = (SingleCombatEnv(scenario) if env_name == "SingleCombat"
               else SingleControlEnv(scenario))
        obs_space, act_space = env.observation_space, env.action_space
        policy = PPOPolicy1v1(all_args, obs_space, act_space, device=device)

    if not args.fresh:
        ckpt = os.path.join(args.run_dir, "actor_latest.pt")
        policy.actor.load_state_dict(torch.load(ckpt, map_location=device, weights_only=True))
    policy.prep_rollout()

    # Collect observations the policy actually visits. Entropy computed on random
    # Gaussian inputs is off-distribution and overstates how uniform the policy
    # is, which is exactly the wrong direction for this measurement.
    n_agents = env.num_agents
    reset = env.reset()
    obs = reset[0] if is_multi else reset
    rnn = np.zeros((n_agents, 1, 128), dtype=np.float32)
    masks = np.ones((n_agents, 1), dtype=np.float32)
    collected = []
    for step in range(args.rollout_steps):
        collected.append(np.asarray(obs).reshape(n_agents, -1).copy())
        with torch.no_grad():
            a, rnn = policy.act(np.asarray(obs).reshape(n_agents, -1), rnn, masks)
        a = a.cpu().numpy().astype(np.int64)
        if is_multi:
            obs, _s, _r, _d, _i = env.step(a)
        else:
            obs, _r, _d, _i = env.step(a)
    env.close()
    obs = np.concatenate(collected, axis=0)[:args.batch]
    n_obs_samples = obs.shape[0]

    res = entropy_of(policy, obs, act_space, device)
    res["obs_source"] = f"on-policy rollout, {n_obs_samples} agent-steps"
    res.update({"run_dir": args.run_dir, "scenario": scenario, "algo": algo,
                "env_name": env_name, "batch": args.batch,
                "checkpoint": None if args.fresh else os.path.join(args.run_dir, "actor_latest.pt"),
                "note": "entropy measured directly on the policy, NOT normalised by batch size"})
    print(json.dumps(res, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
