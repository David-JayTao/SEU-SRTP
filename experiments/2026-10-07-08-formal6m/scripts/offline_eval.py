#!/usr/bin/env python
"""Low-variance offline evaluation of a saved checkpoint.

Why this exists
---------------
The official scripts evaluate with `--eval-episodes 1`. A combat episode is a
bimodal outcome (win / lose / timeout) and self-play re-draws the opponent each
eval round, so a single episode gives swings of hundreds of reward points on an
unchanged policy. The observed `official_2v2_noweapon` eval series wanders
between -28 and -280 -- that is sampling noise, not learning.

This script re-evaluates a checkpoint over many episodes and reports the mean
with a standard error, so a trend claim can actually be supported. It runs in
its own process and never touches a training run.

Usage:
  python offline_eval.py --run-dir <path to runN> --episodes 32 [--threads 4]
                         [--scenario 2v2/scaling_noweapon/HierarchySelfplay]
                         [--selfplay] [--opponent 0]
"""
import argparse
import json
import os
import statistics
import sys

import numpy as np
import torch

REPO = "/root/autodl-tmp/SEU-SRTP"
sys.path.insert(0, REPO)
os.chdir(REPO)

from config import get_config                       # noqa: E402
from envs.JSBSim.envs import MultipleCombatEnv, SingleCombatEnv  # noqa: E402
from algorithms.mappo.ppo_policy import PPOPolicy    # noqa: E402
from algorithms.ppo.ppo_policy import PPOPolicy as PPOPolicy1v1  # noqa: E402


def build_run_dir_args(run_dir):
    """Reconstruct the args needed to rebuild the policy architecture."""
    cfg = os.path.normpath(run_dir).split(os.sep)
    # .../results/<env>/<scenario...>/<algo>/<exp>/runN
    var = os.path.basename(cfg[-1])
    if not var.startswith("run"):
        raise SystemExit("--run-dir must point at a runN directory")
    algo = cfg[-3]
    idx = cfg.index("results")
    env_name = cfg[idx + 1]
    scenario = "/".join(cfg[idx + 2:-3])
    return env_name, scenario, algo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--episodes", type=int, default=32)
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--scenario", default=None, help="override scenario")
    p.add_argument("--env-name", default=None)
    p.add_argument("--selfplay", action="store_true",
                   help="mirror the ego/opponent split; opponent is the checkpoint too")
    p.add_argument("--max-steps", type=int, default=None)
    p.add_argument("--coordination", action="store_true",
                   help="also record per-step team-coordination proxies")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    env_name, scenario, algo = build_run_dir_args(args.run_dir)
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

    is_multi = env_name == "MultipleCombat"
    env = (MultipleCombatEnv(scenario) if is_multi else SingleCombatEnv(scenario))
    n_agents = env.num_agents

    obs_space = env.observation_space
    act_space = env.action_space
    if is_multi:
        share_space = env.share_observation_space
        policy = PPOPolicy(all_args, obs_space, share_space, act_space, device=device)
    else:
        policy = PPOPolicy1v1(all_args, obs_space, act_space, device=device)

    ckpt = os.path.join(args.run_dir, "actor_latest.pt")
    policy.actor.load_state_dict(torch.load(ckpt, map_location=device, weights_only=True))
    policy.prep_rollout()

    n_ego = n_agents // 2 if (is_multi and args.selfplay) else n_agents
    returns, lengths = [], []

    def coordination_metrics(env, n_ego):
        """Cheap, geometry-based coordination proxies for the ego team.

        We do not have an explicit target assignment in the NoWeapon task, so we
        use the nearest-enemy as the de-facto target:
          n_distinct_targets  how many different enemies the team is oriented to
          collision_rate      fraction of ego agents whose nearest enemy is also
                              some teammate's nearest enemy (everyone piling on
                              the same aircraft)
          team_spread_m       mean pairwise distance inside the ego team
          nearest_enemy_m     mean distance from each ego agent to its target
        All are proxies; the formation width is deliberately scaled with N, so
        absolute values are not comparable across N -- only the trends, and only
        at comparable policy quality.
        """
        ids = list(env.agents.keys())[:n_ego]
        enm = list(env.agents[ids[0]].enemies)
        pos = np.array([env.agents[i].get_position() for i in ids], dtype=float)
        epos = np.array([e.get_position() for e in enm], dtype=float)
        d = np.linalg.norm(pos[:, None, :] - epos[None, :, :], axis=-1)  # (n_ego, n_enm)
        tgt = d.argmin(axis=1)
        counts = np.bincount(tgt, minlength=len(enm))
        collision = float(np.mean([counts[t] > 1 for t in tgt]))
        pd = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
        iu = np.triu_indices(len(ids), k=1)
        return {
            "n_distinct_targets": int((counts > 0).sum()),
            "collision_rate": collision,
            "team_spread_m": float(pd[iu].mean()) if len(iu[0]) else 0.0,
            "nearest_enemy_m": float(d.min(axis=1).mean()),
        }

    coord = []

    for ep in range(args.episodes):
        reset = env.reset()
        obs = reset[0] if is_multi else reset
        if is_multi and args.selfplay:
            obs_ego = obs[:n_ego]
        else:
            obs_ego = obs
        rnn = np.zeros((n_ego, 1, 128), dtype=np.float32)
        masks = np.ones((n_ego, 1), dtype=np.float32)
        ep_ret = np.zeros(n_ego, dtype=np.float64)
        step = 0
        while True:
            step += 1
            if args.coordination and is_multi and step % 5 == 1:
                coord.append(coordination_metrics(env, n_ego))
            with torch.no_grad():
                actions, rnn = policy.act(obs_ego.reshape(n_ego, -1), rnn, masks, deterministic=True)
            actions = actions.cpu().numpy().astype(np.int64)
            full = np.zeros((n_agents, *actions.shape[1:]), dtype=actions.dtype)
            full[:n_ego] = actions
            if is_multi and args.selfplay:
                full[n_ego:] = actions            # opponent mirrors the same checkpoint
            elif n_ego < n_agents:
                # DEFAULT (no --selfplay): the opponent emits action 0, i.e. it never
                # manoeuvres and never fires. This is a NULL opponent, not an
                # evaluation. Returns and episode lengths measured in this mode say
                # nothing about policy strength -- in particular an episode that runs
                # to max_steps here only reflects that a null opponent cannot end it.
                # Use --selfplay for any measurement that is meant to mean anything.
                full[n_ego:] = 0
            if is_multi:
                obs, _share, rew, dones, _info = env.step(full)
                ep_ret += rew[:n_ego, 0]
                done = bool(np.all(dones))
                obs_ego = obs[:n_ego]
            else:
                obs, rew, dones, _info = env.step(full)
                ep_ret += rew[:n_ego, 0]
                done = bool(np.all(dones))
                obs_ego = obs[:n_ego]
            if done or step >= (args.max_steps or 10 ** 9):
                break
        returns.append(float(ep_ret.mean()))
        lengths.append(step)
    env.close()

    mean = statistics.mean(returns)
    sd = statistics.pstdev(returns) if len(returns) > 1 else 0.0
    se = sd / max(1, len(returns)) ** 0.5
    res = {
        "run_dir": args.run_dir, "checkpoint": ckpt, "scenario": scenario,
        "algo": algo, "episodes": args.episodes, "n_agents": n_agents,
        "selfplay_mirror": bool(args.selfplay),
        "mean_return": round(mean, 4),
        "std_return": round(sd, 4),
        "stderr": round(se, 4),
        "mean_episode_length": round(statistics.mean(lengths), 2),
        "per_episode_returns": [round(r, 3) for r in returns],
    }
    if coord:
        keys = list(coord[0].keys())
        res["coordination"] = {
            k: round(float(np.mean([c[k] for c in coord])), 4) for k in keys
        }
        res["coordination_samples"] = len(coord)
        res["coordination_note"] = (
            "proxies only; formation width is deliberately scaled with N, so "
            "absolute values are not comparable across N")
    print(json.dumps(res, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
