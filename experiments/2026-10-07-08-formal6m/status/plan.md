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

### Drain-time arithmetic (why late lanes can only take short jobs)

A lane freeing at time *t* can host a job only if
`6e6 / expected_FPS_at_those_threads <= (09:00 Oct 8 - t)`. Using the measured
per-thread rates (2v2 ≈ 19.5, 3v3 ≈ 16, 5v5 ≈ 10, 10v10 ≈ 3.7 env-steps/s/thread):

| lane frees | threads | window left | 6M at 8 threads needs | fits? |
|---|---|---|---|---|
| 3v3 @15:40 | 8 | 17.3 h | 3v3 (10.4 h) ✔, 2v2 (10.4 h) ✔, 5v5 (20.8 h) ✘ | yes (small scales) |
| 5v5 @22:50 | 8 | 10.2 h | 2v2 (10.4 h) ~, 3v3 (10.4 h) ~, anything bigger ✘ | marginal |
| 2v2 @23:20 | 4 | 9.7 h | 2v2 at 4 thr (20 h) ✘ | no |
| off2v2 @00:10 | 4 | 8.8 h | ✘ for 6M; fine for 1/heading (2.8 h) | short jobs only |
| 10v10 @~01:30 | 20 | 7.5 h | 2v2 seed at 20 thr (4.3 h) ✔, 3v3 seed (5.2 h) ✔, 5v5 (8.3 h) ✘ | generous |

**Consequence: the only genuinely useful 6M-capable slot after ~23:00 is the
10v10 lane's 20 threads when it completes at ~01:30 Oct 8.** That is the slot to
hold for a second seed at 2v2 or 3v3. Everything freeing between 22:50 and 00:10
can only take `1/heading` (SingleControl, ~590 FPS at 10 threads, ~2.8 h) or a
partial Shoot-scaling run.

**No lane can host 5v5 seed 1 at 6M.** Starting it at 15:40 on the 3v3 lane gets
it to roughly 5.0M by the freeze (5v5 needs ~20.8 h at 8 threads against a 17.3 h
window). If it is started anyway it must be reported as `time_cutoff` with the
steps actually reached — which is still a usable variance sample over 0–5M, but
is a weaker deliverable than a complete 3v3 seed 1. **Decision deferred to
15:40 with live numbers in hand.**

## Final-phase tasks (do at ~09:00 Oct 8, once training stops competing for CPU)

These are cheap, single-core, inference-only probes that need a QUIET machine or
trained checkpoints, so they are deliberately deferred to the freeze window.

1. **`offline_eval.py` on every final f6m checkpoint** (`--run-dir <...>/run1
   --episodes 8`). Yields for each lane a low-variance `mean_return`,
   `std_return` and, critically, **`mean_episode_length`**.
   *Why this matters:* `average_episode_rewards` is computed as
   `buffer.rewards.sum() / (buffer.masks == False).sum()`
   (`runner/share_jsbsim_runner.py:112`) — i.e. a **per-agent-episode** mean over
   the learner's `num_agents // 2` team. Because `PostureReward` sums over an
   agent's enemies, that quantity scales with N, which is why `reward/N` is the
   right normalisation. **But it is still confounded if the mean episode LENGTH
   differs across N** (reward accumulates per step, so shorter episodes give
   smaller-magnitude per-episode rewards regardless of skill). The probe
   measures the length directly instead of assuming it away.
2. **`critic_scaling_probe.py`** on a quiet box — fills the representation
   columns (local obs dim, share_obs dim, actor/critic param counts vs N).
3. **`env_bench.py`** quiet-mode re-measurement for the computational-scaling
   figure; the pilot's `quiet`/`loaded` pair is the precedent for reporting both.
4. **`obs_cost_profile.py`** to re-confirm the O(N²) observation-construction
   attribution (pilot F8) under this campaign's configuration.

## Two eval-measurement facts inherited from the pilot (do not re-derive)

- **MultipleCombat evaluation is deterministic.** Re-evaluating one checkpoint 8
  times gave `std_return = 0.0` (`docs/overnight_repro_scaling_2026-10-04.md`
  §5.1). So the `--eval-episodes 1` series wobbling between −28 and −280 across
  training is **not** eval sampling noise; it is the policy *and the re-drawn
  self-play opponent* changing. Per-checkpoint the estimator has zero variance
  and unknown (potentially large) bias — so eval curves are suggestive only, and
  no conclusion in this report rests on a single eval point.
- **`--eval-interval 2` means eval every 2 PPO updates**, and at 10v10 an eval
  costs ~140–156 s (`metrics.jsonl` `wall_time` deltas). At 100 updates that is
  ~2 h of the 10v10 lane's wall-clock — already inside the reported FPS, which is
  a wall-clock average, not a pure step rate.

## Explicitly not done, and why

- **10v10 second seed**: needs ~26 h at the threads available; the earliest a
  lane large enough could free is 03:00 Oct 8, leaving 7 h. Recorded in the
  report as infeasible in this window, not attempted as a token gesture.
- **Official 100M budgets**: ~300–400 h per run on this box. Out of scope by
  construction; 6M is stated as a formal *budget reduction*, never as
  convergence.
- **Algorithm changes / env optimisation**: forbidden for the main line
  (comparability). See report §4.4.

---

## Revised drain plan (2026-10-07 17:45), after the CPU correction (F16)

The earlier drain table assumed 43–47 of 48 cores were busy, i.e. no headroom.
The cgroup measurement shows **~38–42 of 48** with no meaningful throttling, so
two second seeds were launched immediately (5v5 s1 @10 thr, 3v3 s1 @8 thr) rather
than waiting for lanes to drain.

Projected drain times at current rates:

| ~time (Oct 7/8) | lane freeing | threads |
|---|---|---|
| 19:20 | 1v1 Selfplay | 3 |
| 23:30 | 1v1 HierSelfplay | 3 |
| 23:50 | 5v5 s0 | 8 |
| 00:45 | 2v2 s0 | 4 |
| 01:15 | official 2v2 s0 | 4 |
| 03:25 | 10v10 s0 | 20 |
| ~06:00 | 1v1 Shoot | 3 |

**Feasibility of a third seed.** A lane only helps if
`6e6 / FPS_at_that_thread_count <= 09:20 Oct 8 - t`. From ~23:30 there are
~9.8 h left, so a second seed needs ≥170 FPS. `2v2` reaches ~19.5 env-steps/s per
thread, so **2v2 seed 1 at 10 threads (~195 FPS, ~8.5 h) fits** and is the next
item in the brief's ranking (第三：2v2 / 3v3 seed 2). 3v3 seed 1 is already
running at 8 threads.

**Reminder on divisibility (F17).** Choose thread counts that divide 2000:
4, 5, 8, 10, 16, 20, 25 … **not** 3, 6, 7, 9, 11. A lane launched at 11 threads
would silently finish 1.8% short.

**Reserve.** The 10v10 lane's 20 threads free at ~03:25 with only ~5.5 h left —
too little for any 6M run, so that capacity should go to (`1/heading`, ~2.8 h) or
a partial Shoot-scaling run, or simply be left unused rather than started and
abandoned.

### Decision 17:30 — do NOT add a fourth seed yet

After launching 5v5 s1 and 3v3 s1, measured container CPU rose to **41.6–43.6 of
48 cores (87–91%)** with throttling still negligible (0.047%). That is close
enough to the quota that adding another 10-thread lane would risk real
throttling, which would fall hardest on the *tightest* lane — `f6m_5v5_noweapon_s1`
at 95 FPS (nominal ETA ~10:50, i.e. already past the freeze).

So the next seed waits for a lane to drain rather than being squeezed in. Note
that `f6m_5v5_noweapon_s1` is **not necessarily lost**: its nominal ETA assumes
today's contention. By 01:15 Oct 8 roughly 22 rollout threads will have freed, so
if its marginal rate rises from 95 to ~120 FPS it reaches 6M around 07:30–08:00.
Its progress is therefore tracked explicitly rather than assumed censored.

### 18:45 — CPU is at the quota edge; the remaining official L1 entry gets the next free lane

Container CPU is **42–43 of 48 cores (87–90%)** and `nr_throttled` has risen from
0.078% to **1.28% of periods** and is still creeping (~+0.035%/2 min). Small
enough that aggregate throughput is unaffected (991 env-steps/s, unchanged since
the second seeds started), and the two second seeds are worth far more than the
~1.3% they cost — but the box is now genuinely at its ceiling, so no further
concurrency without a corresponding free-up.

**Plan: at ~19:05 `f6m_official_1v1_selfplay_s1` completes and frees 3 threads.**
Rather than leave them idle, add the one official L1 training entry not yet run:

| job | scenario | algo | seed | threads | why |
|---|---|---|---|---|---|
| `f6m_official_heading_s5` | `SingleControl 1/heading` | ppo | 5 | **4** | the last unrun official L1 entry (brief P3); ~236 FPS at 4 threads → 6M in ~7 h, done ~02:10 |

**4 threads, not 3**, because the thread count must divide 2000 (F17) or the lane
silently caps at 5,994,000. SingleControl is 1 aircraft and CPU-cheap, so 4
threads plus the freed 3 keeps us inside the quota.

**Note the honest framing of this lane**: `1/heading` is SingleControl, i.e. *not*
a multi-agent task. It completes the official inventory and is reported as a
single-agent control, **not** as evidence about multi-agent scaling.

### 19:07 — the real concurrency limit: bursty throttling, not average CPU

A 90-second window measurement separates two things the instantaneous samples
conflated:

| quantity | value |
|---|---|
| CPU consumed, 90 s average | **35.3 of 48 cores (74% of quota)** |
| throttled periods, same window | **5.22%** |
| throttled periods, campaign lifetime | 1.49% |

Average utilisation is only 74%, yet 5% of scheduling periods are throttled. That
is the signature of **bursty oversubscription**: cgroup-v2 throttling fires when
the container exceeds its 100 ms-period quota, and with 70+ worker processes a
synchronised moment (several lanes beginning a rollout or ending an episode at
once) can exceed it even though the long-run average sits well below the cap.

**Consequence for scheduling.** The usable capacity is not "48 minus average
usage". It is 48 cores of *smooth* capacity, and a workload that is bursty loses
a few percent of it to throttling. So the earlier reasoning — "average is 74%, so
there are ~13 cores spare" — was wrong, and no further lanes are added. Twelve is
the ceiling for this campaign.

**Cost check.** Aggregate throughput is 992 env-steps/s, unchanged since the
second seeds were added, so the throttling cost is small relative to what those
lanes contribute (~190 env-steps/s). Kept, not rolled back — but the box is done.

---

# 2026-10-08 01:14 — wave 6: second seeds into recovered capacity

By 01:12 eight lanes had completed (5v5 s0, 3v3 s0, 2v2 s0, official 2v2 and
heading all at exactly 6,000,000; the three 3-thread 1v1 lanes at their
5,994,000 ceiling). Only 4 lanes were still running and container CPU had fallen
to **30.8 of 48 cores**, freeing **29 rollout threads**.

## What was launched, and why in that order

| job | threads | rationale |
|---|---|---|
| `f6m_10v10_noweapon_s1` | **20** | The brief's #1 second seed, and it tests the campaign's **headline** result. |
| `f6m_5v5_noweapon_s2` | **8** | A clean second comparison at the most volatile mid scale. |

**Thread count is not a free parameter here.** For a *seed* comparison everything
except `--seed` must match the seed-0 lane or the comparison additionally
crosses the §4.5 batch-size confound. So 10v10 seed 1 runs at 20 threads
(seed 0's value) and 5v5 seed 2 at 8 (seed 0's value) — **not** at the largest
number the box could take. This deliberately trades coverage for comparability;
the opposite trade would have produced two fast, uninterpretable runs.

**Why 10v10 seed 1 matters most.** The scaling curve's striking feature is that
10v10 sits at ≈0 reward (≈+0.06 per enemy) while 2v2/3v3/5v5 are all strongly
positive (+8 to +12 per enemy). That is the headline, and it currently rests on
**one trajectory**. A second 10v10 seed is the only available test of whether the
result replicates. At 20 threads it reaches roughly **2.3M of 6M (≈38%)** by the
freeze, so it will be `time_cutoff` — accepted deliberately, because a partial
second trajectory at the headline scale is worth more than a complete run at a
scale that is already well covered.

**What was deliberately not run.** 2v2 seed 1: it would need 4 threads to match
seed 0, buying only ~28% coverage at the scale with the *smoothest* seed-0 curve
and therefore the least variance to resolve. The brief's #3 item
(2v2 **or** 3v3 second seed) is already satisfied by `f6m_3v3_noweapon_s1`, which
projects to complete.

## Next free-up: 10v10 seed 0 at ~04:00 (20 threads, 5 h window)

5 h is too short for any 6M run at N≥3 at the thread counts that keep a
comparison clean. The best available use is a **new family** at small scale:
`2v2/scaling_shoot` at 20 threads ≈ 390 FPS → 6M in ≈4.3 h, which fits. That adds
an armed-combat point at a scale where the unarmed baseline is already complete,
i.e. a matched armed-vs-unarmed comparison. Decided at 04:00 with live numbers.
