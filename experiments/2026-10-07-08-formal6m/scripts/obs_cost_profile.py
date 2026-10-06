#!/usr/bin/env python
"""Attribute the env-step cost of LAG to its parts, as a function of team size.

The audit claims the env-step cost is superlinear because
  (a) get_obs() walks every partner+enemy for every agent, and
  (b) BaseEnv.get_state() calls get_obs() for ALL agents *again* and then
      hstacks the result into a (num_agents * obs_dim) vector that is copied
      to every agent.
Rather than assert that, this measures each part separately at each N.

Reported per env step:
  get_obs_all   : sum over agents of task.get_obs(env, agent)
  get_state     : BaseEnv.get_state()  (which internally repeats get_obs_all)
  sim_run       : the JSBSim integration loop only
  full_step     : env.step() end to end (actions + sim + task + obs + reward)

Usage: python obs_cost_profile.py [--out metrics/obs_cost_profile.json]
"""
import argparse
import json
import os
import sys
import time

import numpy as np

REPO = "/root/autodl-tmp/SEU-SRTP"
sys.path.insert(0, REPO)
os.chdir(REPO)

from envs.JSBSim.envs import MultipleCombatEnv  # noqa: E402


def timeit(fn, iters):
    fn()  # warm
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    return (time.perf_counter() - t0) / iters


def profile(n, iters=40):
    env = MultipleCombatEnv(f"{n}v{n}/scaling_noweapon/HierarchySelfplay")
    env.reset()
    na = env.num_agents

    obs_all = timeit(lambda: [env.task.get_obs(env, a) for a in env.agents], iters)
    state = timeit(lambda: env.get_state(), iters)

    def sim_only():
        for _ in range(env.agent_interaction_steps):
            for s in env._jsbsims.values():
                s.run()
            for s in env._tempsims.values():
                s.run()

    sim = timeit(sim_only, max(5, iters // 4))

    def full():
        env.step(np.array([env.action_space.sample() for _ in range(na)]))

    full_t = timeit(full, max(10, iters // 2))

    env.close()
    return {
        "team_size": n,
        "num_agents": na,
        "obs_dim": int(env.observation_space.shape[0]),
        "share_obs_dim": int(env.share_observation_space.shape[0]),
        "get_obs_all_ms": round(obs_all * 1000, 4),
        "get_state_ms": round(state * 1000, 4),
        "sim_run_ms": round(sim * 1000, 4),
        "full_step_ms": round(full_t * 1000, 4),
        "obs_share_of_step_pct": round(100 * (obs_all + state) / full_t, 1),
        "sim_share_of_step_pct": round(100 * sim / full_t, 1),
        "get_state_per_agent_us": round(state / na * 1e6, 2),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--n", type=int, nargs="+", default=[2, 3, 5, 10])
    args = p.parse_args()

    rows = [profile(n) for n in args.n]
    print(f"{'N':>3} {'agents':>7} {'get_obs_all':>12} {'get_state':>10} "
          f"{'sim_run':>9} {'full_step':>10} {'obs%':>6} {'sim%':>6} "
          f"{'us/agent':>9}")
    for r in rows:
        print(f"{r['team_size']:>3} {r['num_agents']:>7} {r['get_obs_all_ms']:>10.3f}ms "
              f"{r['get_state_ms']:>8.3f}ms {r['sim_run_ms']:>7.3f}ms "
              f"{r['full_step_ms']:>8.3f}ms {r['obs_share_of_step_pct']:>5.1f}% "
              f"{r['sim_share_of_step_pct']:>5.1f}% {r['get_state_per_agent_us']:>8.2f}")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
