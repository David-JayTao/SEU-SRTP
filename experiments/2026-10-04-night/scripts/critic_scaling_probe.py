#!/usr/bin/env python
"""Representation-scalability probe for the LAG MAPPO actor / centralised critic.

Answers, with *measured* numbers rather than hand-waving:
  - local obs dim, share_obs dim, actor input dim as a function of team size N
  - actor / critic parameter counts
  - per-agent critic forward and backward wall time
  - the resulting critic compute per env step at each N
and extrapolates to scales we cannot afford to run (20v20 / 50v50 / 100v100).

It builds the *real* PPOActor/PPOCritic classes from the repo, so the numbers
track the actual code rather than a re-derivation.

Usage: python critic_scaling_probe.py [--out results.json]
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

REPO = "/root/autodl-tmp/SEU-SRTP"
sys.path.insert(0, REPO)
os.chdir(REPO)

from algorithms.mappo.ppo_actor import PPOActor          # noqa: E402
from algorithms.mappo.ppo_critic import PPOCritic        # noqa: E402
from gymnasium import spaces                             # noqa: E402


class Args:
    """Mirrors the official scripts' network config exactly."""
    gain = 0.01
    hidden_size = "128 128"
    act_hidden_size = "128 128"
    activation_id = 1
    use_feature_normalization = False
    use_recurrent_policy = True
    recurrent_hidden_size = 128
    recurrent_hidden_layers = 1


def dims_noweapon(n):
    """obs_length = 9 + (num_agents-1)*6 ; share = num_agents * obs_length"""
    num_agents = 2 * n
    obs = 9 + (num_agents - 1) * 6
    return obs, num_agents * obs


def dims_shoot(n):
    """obs_length = 9 + num_agents*6 ; share = num_agents * obs_length"""
    num_agents = 2 * n
    obs = 9 + num_agents * 6
    return obs, num_agents * obs


def n_params(module):
    return sum(p.numel() for p in module.parameters())


def time_forward_backward(module, x, rnn_states, masks, device, iters=30, is_critic=True):
    """Wall-clock forward (and backward for the critic) per call, per agent."""
    module.train()
    opt = torch.optim.Adam(module.parameters(), lr=1e-6)

    def fwd():
        out = module(x, rnn_states, masks)
        return out

    # warmup
    for _ in range(5):
        out = fwd()
        val = out[0] if is_critic else out[0]

    torch.cuda.synchronize() if device.type == "cuda" else None
    t0 = time.perf_counter()
    for _ in range(iters):
        fwd()
    torch.cuda.synchronize() if device.type == "cuda" else None
    fwd_ms = (time.perf_counter() - t0) / iters * 1000

    if is_critic:
        for _ in range(5):
            out = fwd()
            loss = out[0].pow(2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
        torch.cuda.synchronize() if device.type == "cuda" else None
        t0 = time.perf_counter()
        for _ in range(iters):
            out = fwd()
            loss = out[0].pow(2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
        torch.cuda.synchronize() if device.type == "cuda" else None
        bwd_ms = (time.perf_counter() - t0) / iters * 1000
    else:
        bwd_ms = None
    return fwd_ms, bwd_ms


def probe(n, variant, device, batch_threads, fixed_batch=256):
    obs_dim, share_dim = (dims_noweapon if variant == "noweapon" else dims_shoot)(n)
    obs_space = spaces.Box(low=-10, high=10.0, shape=(obs_dim,))
    share_space = spaces.Box(low=-10, high=10.0, shape=(share_dim,))
    act_space = spaces.MultiDiscrete([3, 5, 3])

    args = Args()
    actor = PPOActor(args, obs_space, act_space, device=device)
    critic = PPOCritic(args, share_space, device=device)

    # (a) "production" batch: one rollout step across `batch_threads` envs.
    #     self-play means the ego team only -> n rows per env.
    n_row = batch_threads * n
    rnn = torch.zeros((n_row, args.recurrent_hidden_layers, args.recurrent_hidden_size), device=device)
    masks = torch.ones((n_row, 1), device=device)
    a_fwd, _ = time_forward_backward(
        actor, torch.zeros((n_row, obs_dim), device=device), rnn, masks, device, is_critic=False)
    c_fwd, c_bwd = time_forward_backward(
        critic, torch.zeros((n_row, share_dim), device=device), rnn, masks, device, is_critic=True)

    # (b) fixed-size batch: isolates the per-sample cost so that the growth in
    #     share_dim is not masked by the GPU's parallelism (at small N the
    #     production batch is latency-bound and hiding the scaling entirely).
    fb = fixed_batch
    rnn_f = torch.zeros((fb, args.recurrent_hidden_layers, args.recurrent_hidden_size), device=device)
    masks_f = torch.ones((fb, 1), device=device)
    c_fwd_fixed, c_bwd_fixed = time_forward_backward(
        critic, torch.zeros((fb, share_dim), device=device), rnn_f, masks_f, device, is_critic=True)

    # first-layer multiply-accumulates for the whole ego-team rollout step
    mac_first_layer_per_step = n_row * share_dim * int(args.hidden_size.split()[0])

    return {
        "team_size": n,
        "variant": variant,
        "total_agents": 2 * n,
        "obs_dim": obs_dim,
        "share_obs_dim": share_dim,
        "actor_params": n_params(actor),
        "critic_params": n_params(critic),
        "critic_first_layer_params": share_dim * 128 + 128,
        "batch_rows": n_row,
        "actor_fwd_ms_batch": round(a_fwd, 3),
        "critic_fwd_ms_batch": round(c_fwd, 3),
        "critic_bwd_ms_batch": round(c_bwd, 3),
        "critic_fwd_ms_per_agent": round(c_fwd / n_row, 4),
        "critic_fwd_ms_fixed256": round(c_fwd_fixed, 4),
        "critic_bwd_ms_fixed256": round(c_bwd_fixed, 4),
        "critic_fwd_us_per_sample_fixed256": round(c_fwd_fixed / fb * 1000, 3),
        "critic_first_layer_MAC_per_envstep": mac_first_layer_per_step,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--batch-threads", type=int, default=12)
    p.add_argument("--n", type=int, nargs="+", default=[2, 3, 5, 10])
    p.add_argument("--variant", default="noweapon", choices=["noweapon", "shoot"])
    p.add_argument("--cuda", action="store_true", default=True)
    p.add_argument("--cpu", dest="cuda", action="store_false")
    args = p.parse_args()

    device = torch.device("cuda:0") if (args.cuda and torch.cuda.is_available()) else torch.device("cpu")
    print(f"device={device} batch_threads={args.batch_threads}")

    rows = []
    for n in args.n:
        r = probe(n, args.variant, device, args.batch_threads)
        rows.append(r)
        print(json.dumps(r))

    # Extrapolation. The honest model is FLOP-based, not time-based:
    #   critic first-layer work per env step  = (rows) * share_dim * 128
    #                                        = (T*N) * (24N^2+6N) * 128
    #                                        = O(N^3)
    # We convert MACs -> seconds with an effective throughput calibrated from
    # the *fixed-batch* measurement, which is the compute-bound regime.
    # (Using the production batch would be misleading: at small N it is
    # launch-latency-bound and the measured per-agent cost actually FALLS with
    # N, which says nothing about asymptotic scaling.)
    base = max(rows, key=lambda r: r["team_size"])
    mac_per_sample_base = base["share_obs_dim"] * 128
    sec_per_mac = (base["critic_fwd_ms_fixed256"] / 1000) / (256 * mac_per_sample_base)
    eff_gmacs = 1.0 / sec_per_mac / 1e9
    measured_n = {r["team_size"] for r in rows}

    extrap = []
    for n in sorted(measured_n | {2, 3, 5, 10, 20, 50, 100}):
        obs_dim, share_dim = dims_noweapon(n)
        rows_per_step = args.batch_threads * n          # ego team only
        mac_per_step = rows_per_step * share_dim * 128
        # shared replay buffer for share_obs: (buffer_size+1, T, N, share_dim) fp32
        buf_bytes = (3000 + 1) * args.batch_threads * n * share_dim * 4
        extrap.append({
            "team_size": n,
            "total_agents": 2 * n,
            "obs_dim": obs_dim,
            "share_obs_dim": share_dim,
            "critic_first_layer_params": share_dim * 128 + 128,
            "critic_first_layer_MAC_per_envstep": mac_per_step,
            "critic_fwd_ms_per_envstep_est": round(mac_per_step * sec_per_mac * 1000, 4),
            "share_obs_buffer_GB": round(buf_bytes / 1024 ** 3, 3),
            "note": "measured" if n in measured_n else "extrapolated",
        })

    out = {"measured": rows, "extrapolated": extrap, "device": str(device),
           "effective_G_MAC_per_s": round(eff_gmacs, 2), "batch_threads": args.batch_threads}
    print(f"\ncalibrated effective throughput: {eff_gmacs:.1f} G-MAC/s (fixed batch 256)")
    print("\n=== scaling table ===")
    print(f"{'N':>4} {'agents':>7} {'obs':>6} {'share':>8} {'criticL1param':>14} "
          f"{'MAC/step':>12} {'criticfwd/step':>15} {'sharebuf':>10}  src")
    for e in extrap:
        print(f"{e['team_size']:>4} {e['total_agents']:>7} {e['obs_dim']:>6} {e['share_obs_dim']:>8} "
              f"{e['critic_first_layer_params']:>14} {e['critic_first_layer_MAC_per_envstep']:>12} "
              f"{e['critic_fwd_ms_per_envstep_est']:>13.3f}ms {e['share_obs_buffer_GB']:>8.2f}GB  [{e['note']}]")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
