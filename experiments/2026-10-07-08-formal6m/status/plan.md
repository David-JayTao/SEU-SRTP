# Campaign plan and dynamic scheduling decisions

Live state is in `running_jobs.md`; this file records *why* the schedule is what
it is, and the pre-decided rules for what happens as lanes free up.

## Resource model

48-core cgroup quota. GPU is not the constraint (≤2.3 GB VRAM/job, 0–39% util).
Objective: **maximise aggregate useful env-steps/s**, subject to P0 (10v10)
completing 6M.

Measured calibration points (2026-10-07):

| time | lanes | threads | cores busy | aggregate env-steps/s |
|---|---|---|---|---|
| 03:11 | 5 | 44 | 42.0 / 48 | 451 |
| 03:17 | 7 | 50 | 41.0 / 48 | 672 |
| 03:19 | 9 | 56 | 42.2 / 48 | 668 |
| 03:46 | 9 | 56 | 43.0 / 48 | ~810 |

Steady-state per-lane FPS at 9 lanes / 56 threads (03:46), with the CPU cost of
each lane expressed as FPS per rollout thread:

| lane | threads | FPS | FPS/thread | ETA to 6M |
|---|---|---|---|---|
| 10v10 s0 | 20 | 67 cum. (**74 marginal**) | 3.7 | 01:35–03:55 Oct 8 |
| 5v5 s0 | 8 | 81 | 10.1 | 22:50 Oct 7 |
| 3v3 s0 | 8 | 127 | 15.9 | 15:45 Oct 7 |
| 2v2 s0 | 4 | 78 | 19.5 | 23:20 Oct 7 |
| official 2v2 s0 | 4 | 78 | 19.5 | 00:10 Oct 8 |
| 1v1 vsBaseline | 3 | 119 | 39.7 | 17:30 Oct 7 |
| 1v1 Selfplay | 3 | 106 | 35.3 | 18:50 Oct 7 |
| 1v1 HierSelfplay | 3 | 85 | 28.3 | 22:20 Oct 7 |
| 1v1 Shoot HierSelfplay | 3 | 55 | 18.3 | **~09:40 Oct 8 — marginal** |

(FPS/thread varies 21× across lanes, which is the whole reason a flat
thread-per-job allocation is wrong and why the allocation is chosen per lane.)

### 1v1/ShootMissile is structurally ~2× slower — not contention

`--use-prior` (implemented only in `algorithms/ppo/ppo_actor.py`) roughly halves
SingleCombat throughput. Pilot measurement at an identical 10 threads:

| pilot run | threads | FPS |
|---|---|---|
| `official_1v1_selfplay` | 10 | 324 |
| `official_1v1_shoot_hier_selfplay` | 10 | 170 |

This campaign reproduces it at 3 threads (1v1 Selfplay 106 FPS = 35.3/thread,
1v1 Shoot 55 FPS = 18.3/thread — the same ~2:1 ratio). **Consequence: at 3
threads the Shoot baseline needs ~30.3 h, i.e. it lands at roughly 98% of 6M by
the freeze.** It is kept rather than killed+relaunched because a relaunch would
create a second `run<N>/` directory and a restarted partial trajectory is not a
clean formal run. It will be reported as `time_cutoff` with the steps actually
reached, never as `completed_6M`.

Adding the two SingleCombat lanes at 03:10 raised aggregate throughput by **+221
env-steps/s at zero measured cost to the other five lanes** (10v10 held at 70 FPS,
3v3 at 132 vs 133). This is the F8 mechanism in reverse: each rollout worker only
reaches ~0.7 of a core because it blocks on IPC, so the machine has spare
*scheduling* capacity even when `load1` looks saturated (44). **Decision rule:
judge by measured aggregate env-steps/s and by the P0 job's FPS, never by load1
or by idle GPU.**

At 56 threads / 42.2 busy cores the box is now genuinely full; no further
concurrency is added until a lane drains.

## Why this thread allocation

At equal threads the env cost scales roughly as 2v2 : 3v3 : 5v5 : 10v10 =
107.8 : 60.3 : 25.4 : 7.8 (single-core bench, pilot). Equal finish times would
need threads in roughly inverse proportion, i.e. ~2/3 of the budget on 10v10 —
which would starve everything else. The allocation below instead gives 10v10
enough to clear 6M with margin and spends the rest on coverage.

| job | threads | rationale |
|---|---|---|
| 10v10 s0 | 20 | P0. The only job that cannot be re-run in this window. |
| 5v5 s0 | 8 | P2. |
| 3v3 s0 | 8 | P2. |
| 2v2 s0 | 4 | P2. Cheapest scale; reaches 6M at 4 threads in ~20 h. |
| official 2v2 s0 | 4 | P1, L1 official entry point. |
| 4 × official 1v1 | 3 each | P1. SingleCombat is only 2 aircraft, so 3 threads already yields 107–119 FPS. |

## Pre-decided rules as lanes drain

Drain schedule at current rates (all still on track):

| ~time | lane freeing | threads |
|---|---|---|
| 15:40 Oct 7 | 3v3 s0 | 8 |
| 17:15 Oct 7 | 1v1 vsBaseline | 3 |
| 18:45 Oct 7 | 1v1 Selfplay | 3 |
| 22:55 Oct 7 | 5v5 s0 | 8 |
| 23:25 Oct 7 | 2v2 s0 | 4 |
| 00:05 Oct 8 | official 2v2 | 4 |
| 03:00 Oct 8 | 10v10 s0 | 20 |

Rule for each freed lane, in priority order (§14 of the campaign brief):

1. **Second seed where a full 6M still fits.** Check
   `(6e6 - 0) / expected_FPS` against the *remaining* wall-clock, and start only
   if it finishes by 09:00 Oct 8. Feasible candidates and their 8-thread ETAs
   from 15:40: 3v3 s1 ≈ 12.4 h (→ 04:05 ✔), 2v2 s1 ≈ 11.1 h (→ 02:45 ✔),
   5v5 s1 ≈ 19.7 h (→ 11:20 ✘). **5v5 s1 misses by ~2 h at 8 threads; if it is
   chosen it must be given more threads or accepted as time-censored.**
2. **Shoot-family scaling** (P4) if no seed fits: `2v2/scaling_shoot` ≈ 11 h ✔,
   `3v3/scaling_shoot` ≈ 16 h ✔.
3. **Remaining official baselines not yet run** (P3): `1/heading` (ppo,
   SingleControl, seed 5). Cheap (~590 FPS at 10 threads).
4. **Never** start a job that cannot produce a useful partial result before
   10:00 Oct 8.

## Explicitly not done, and why

- **10v10 second seed**: needs ~26 h at the threads available; the earliest a
  lane large enough could free is 03:00 Oct 8, leaving 7 h. Recorded in the
  report as infeasible in this window, not attempted as a token gesture.
- **Official 100M budgets**: ~300–400 h per run on this box. Out of scope by
  construction; 6M is stated as a formal *budget reduction*, never as
  convergence.
- **Algorithm changes / env optimisation**: forbidden for the main line
  (comparability). See report §4.4.
