#!/usr/bin/env python
"""
Environment-only throughput benchmark for LAG (no learning).

Measures raw env stepping cost for a given scenario, which is the dominant
cost of this project (JSBSim C++ FDM x N aircraft x 12 substeps per env step).

Usage:
    python env_bench.py --scenario 2v2/NoWeapon/HierarchySelfplay --steps 200 \
        --num-env 12 [--procs N] [--random-action] [--json out.json]
"""
import argparse
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402


def build_env(scenario, env_name):
    if env_name == "MultipleCombat":
        from envs.JSBSim.envs import MultipleCombatEnv
        return MultipleCombatEnv(scenario)
    from envs.JSBSim.envs import SingleCombatEnv, SingleControlEnv
    if env_name == "SingleCombat":
        return SingleCombatEnv(scenario)
    return SingleControlEnv(scenario)


def run_single(scenario, env_name, steps, warmup):
    env = build_env(scenario, env_name)
    n = env.num_agents
    is_multi = env_name == "MultipleCombat"
    t0 = time.time()
    reset_out = env.reset()
    t_reset = time.time() - t0
    obs = reset_out[0] if is_multi else reset_out

    def sample_action():
        # raw env (unwrapped) takes (num_agents, ...) with no leading batch dim
        return np.array([env.action_space.sample() for _ in range(n)])

    for _ in range(warmup):
        env.step(sample_action())

    t0 = time.time()
    for _ in range(steps):
        env.step(sample_action())
    dt = time.time() - t0
    env.close()
    return {
        "num_agents": n,
        "obs_dim": int(np.asarray(obs).shape[-1]),
        "share_obs_dim": int(env.share_observation_space.shape[0]) if is_multi else None,
        "reset_s": t_reset,
        "env_steps_per_s": steps / dt,
        "sim_steps_per_s": steps / dt * 12,
        "sec_per_env_step": dt / steps,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", required=True)
    p.add_argument("--env-name", default="MultipleCombat")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--json", default=None)
    args = p.parse_args()

    res = run_single(args.scenario, args.env_name, args.steps, args.warmup)
    res["scenario"] = args.scenario
    res["env_name"] = args.env_name
    print(json.dumps(res, indent=2))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(res, f, indent=2)


if __name__ == "__main__":
    main()
