# Running jobs — formal 6M campaign (2026-10-07 → 2026-10-08)

Launched **2026-10-07 02:54:31 CST** (wave 1), **03:10:14** (wave 2).
Hard deadline **2026-10-08 10:00 CST**.
Branch: `exp/formal-6m-20261007`.

Budget definition: `--num-env-steps 6e6` = **6,000,000 vectorised environment
steps**, *not* agent-steps. Verified against the runner's own accounting:
`total_num_steps` increments by `n_rollout_threads × buffer_size` (buffer_size is
fixed at the official 3000), e.g. 20 threads → 60,000 per update.
6M is a *formal-budget* reproduction, not the official 100M convergence budget.

**Episode counts are exact, so 6M is reached exactly** — the runner computes
`episodes = num_env_steps // buffer_size // n_rollout_threads`
(`runner/share_jsbsim_runner.py:72`, `runner/jsbsim_runner.py:41`), and
`6e6 / (3000 × threads)` divides evenly for every lane used here:

| scale | threads | steps/update | episodes | exact total |
|---|---|---|---|---|
| 2v2 / official 2v2 | 4 | 12,000 | 500 | 6,000,000 |
| 3v3 / 5v5 | 8 | 24,000 | 250 | 6,000,000 |
| 10v10 | 20 | 60,000 | 100 | 6,000,000 |

(This is *not* automatic: the 2026-10-04 pilot lost 36,000 of its nominal
900,000 steps at 18 threads because `900000 // 54000 = 16` episodes, i.e. 864,000.)

---

## Wave 1 — launched 02:54:31

| tmux | experiment_id | scenario | algo | seed | GPU | thr | target | cap | measured FPS | ETA (from 03:11) |
|---|---|---|---|---|---|---|---|---|---|---|
| `f6m_10v10` | `f6m_10v10_noweapon_s0` | `10v10/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 2 | 20 | 6e6 | 108000 s | **70** | **03:00 Oct 8** |
| `f6m_5v5` | `f6m_5v5_noweapon_s0` | `5v5/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 1 | 8 | 6e6 | 108000 s | **85** | 22:45 Oct 7 |
| `f6m_3v3` | `f6m_3v3_noweapon_s0` | `3v3/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 8 | 6e6 | 108000 s | **133** | 15:40 Oct 7 |
| `f6m_2v2` | `f6m_2v2_noweapon_s0` | `2v2/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 4 | 6e6 | 108000 s | **84** | 23:00 Oct 7 |
| `f6m_off2v2` | `f6m_official_2v2_noweapon_s0` | `2v2/NoWeapon/HierarchySelfplay` *(L1 official)* | mappo | 0 | 1 | 4 | 6e6 | 108000 s | **79** | 00:15 Oct 8 |

**Aggregate throughput at 03:11 = 451 env-steps/s** (sum of the five FPS values).
Each of the five is projected to reach 6M *before* the deadline on current rates.

## Wave 2 — launched 03:10:14 (P1 official SingleCombat family)

Two lanes, 3 rollout threads each, each lane running two baselines sequentially.
Added only after wave 1 was measured to leave CPU headroom (42 of the 48-core
quota busy at 03:11).

| tmux | lane queue | job order | env/scenario | algo | seed | GPU | thr |
|---|---|---|---|---|---|---|---|
| `f6m_1v1sp` | `configs/queue_1v1a.txt` | 1. `f6m_official_1v1_selfplay_s1` 2. `f6m_official_1v1_shoot_hier_selfplay_s1` | `1v1/NoWeapon/Selfplay`, then `1v1/ShootMissile/HierarchySelfplay` *(both L1)* | ppo | 1 | 0 | 3 |
| `f6m_1v1vs` | `configs/queue_1v1b.txt` | 1. `f6m_official_1v1_vsbaseline_s1` 2. `f6m_official_1v1_hier_selfplay_s1` | `1v1/NoWeapon/vsBaseline` *(L1)*, then `1v1/NoWeapon/HierarchySelfplay` *(L2)* | ppo | 1 | 1 | 3 |

`1v1/ShootMissile/HierarchySelfplay` is launched with `--use-prior`, matching the
official `scripts/train_selfplay_shoot.sh`. `--use-prior` exists only in
`algorithms/ppo/ppo_actor.py` (5 occurrences); it has no meaning for mappo, which
is why no MultipleCombat job passes it.

**Explicitly NOT run**: `1v1/ShootMissile/HierarchyVsBaseline` — it is the one
officially-configured scenario that cannot run at all (pilot failure F9: dies at
the first env step with `TypeError: 'NoneType' object is not subscriptable` at
`envs/JSBSim/tasks/singlecombat_with_missle_task.py:226`). It is recorded as
`not_applicable`, not as a failure of this campaign.

## Total thread budget

| lane | threads |
|---|---|
| `f6m_10v10` | 20 |
| `f6m_5v5` | 8 |
| `f6m_3v3` | 8 |
| `f6m_2v2` | 4 |
| `f6m_off2v2` | 4 |
| `f6m_1v1sp` | 3 |
| `f6m_1v1vs` | 3 |
| **total** | **50** |

Measured occupancy at 03:11: **42.0 of the 48-core cgroup quota (88%)**.
GPU assignment is arbitrary — VRAM use is ~1.2 GB per GPU and GPU utilisation is
0–12%; **CPU is the binding constraint**, so the scheduling objective is
aggregate useful env-steps/s, not GPU fill.

## Launch command

```bash
cd experiments/2026-10-07-08-formal6m
tmux new-session -d -s <lane> "bash scripts/run_queue_lane.sh <gpu_id> configs/<queue>.txt; exec bash"
```

Wave 1 used `scripts/run_queue.sh`, which derives its status ledger from
`gpu_id` alone — so the two GPU0 lanes (3v3, 2v2) and the two GPU1 lanes (5v5,
off2v2) share one ledger file. Wave 2 uses `scripts/run_queue_lane.sh`, a copy
that keys the ledger on the queue-file name instead. The original was left
untouched because a running bash script must not be edited in place.

`run_train.sh` reproduces the official `scripts/*.sh` hyper-parameters verbatim
(lr 3e-4, gamma 0.99, ppo-epoch 4, clip 0.2, max-grad-norm 2, entropy 1e-3,
hidden 128×128, act-hidden 128×128, recurrent 128×1, data-chunk 8,
num-mini-batch 5, buffer-size 3000), with the two documented compatibility
deviations (no wandb; `--clip-param` passed explicitly at its default value).
Run-level deviations from official: `num_env_steps` 1e8→6e6 and
`n_rollout_threads` 32→{3,4,8,20}. Nothing else.

## Known instrumentation caveats

- **`rc` is meaningless.** `run_train.sh:102-104` captures `$?` from a
  `python … | tee` pipeline without `pipefail`, so every job records
  `exited with code 0` — including crashes and SIGINT timeouts. Failure must be
  detected from the log body (TypeError / EOFError / stalled steps), which is
  what `scripts/watch_f6m.py` and `scripts/os_watchdog.sh` do.
- **Nothing auto-restarts.** `scripts/train/train_jsbsim.py:107-133` always
  allocates the next free `run<N>` directory and no launcher exposes
  `--model-dir`, so a relaunch would silently start a *fresh* run in `run2/`
  and a spliced trajectory would be uninterpretable. Restarts are therefore a
  deliberate decision, logged in `status/incidents.md`.

## Deviations to disclose in the report

1. **`n_rollout_threads` differs across scale** (2v2=4, 3v3=8, 5v5=8, 10v10=20).
   Forced by wall-clock: at a constant thread count 10v10 cannot reach 6M inside
   the window. Consequence: the PPO update batch is
   `n_rollout_threads × 3000`, i.e. 12k / 24k / 24k / 60k samples for
   N=2/3/5/10. **This is a genuine confound on the cross-N comparison and is
   recorded as such.** It is constant across seeds, so seed-variance and same-N
   comparisons stay clean.
2. Official baselines keep the official `--eval-interval 1`; the generated
   scaling configs use `--eval-interval 2` (as in the 2026-10-04 pilot) to cut
   eval overhead. Eval runs in separate envs and does not affect training.
3. `2v2/NoWeapon/HierarchySelfplay` (official) vs `2v2/scaling_noweapon/`
   (generated) differ only in a 0.005° longitude formation shift; both are run
   so the official baseline is uncontaminated and the scaling series is
   internally consistent.

## Superseded by Wave 1

The 2026-10-04 campaign runs are **pilot / exploratory** (all ≤1.48M steps; 23 of
29 finished runs were killed by a wall-clock cap, 6 exited cleanly early, 1
crashed in 5 s). They are retained as pilot curves and are plotted separately
from the 6M formal runs. None was extended into a formal 6M run.

## Monitoring

```bash
python experiments/2026-10-07-08-formal6m/scripts/watch_f6m.py
```

Writes `metrics/status.json`, `status/monitor_latest.md`, and appends to
`metrics/throughput_history.csv`. `tmux f6m_watch` additionally runs
`scripts/os_watchdog.sh 600`, which appends to `system/system_samples.csv` and
`system/events.log` and survives a dead Claude/VS Code session.

---

# Status at 2026-10-07 17:35 (14.7 h elapsed)

## Completed (reached the full budget)

| experiment | steps | target | FPS | lane freed |
|---|---|---|---|---|
| `f6m_3v3_noweapon_s0` | **6,000,000** | 6,000,000 | 125 | 16:12 (8 thr) |
| `f6m_official_1v1_vsbaseline_s1` | **5,994,000** | 6,000,000 | 122 | 16:45 (3 thr) |

Both exited cleanly (no leaked workers; queue ledgers show `queue drained`).

**The 1v1 lanes cannot reach 6,000,000** — see "Granularity" below. 5,994,000 is
their maximum achievable value, i.e. 99.9% of the nominal budget, and is
`completed` rather than `time_cutoff`.

## Wave 4 — second seeds, launched 17:20 and 17:27

| tmux | experiment | scenario | seed | GPU | thr | launched | projected |
|---|---|---|---|---|---|---|---|
| `f6m_5v5s1` | `f6m_5v5_noweapon_s1` | `5v5/scaling_noweapon/HierarchySelfplay` | 1 | 2 | 10 | 17:20 | ~09:30–10:00 → likely `time_cutoff` near 5.9M |
| `f6m_3v3s1` | `f6m_3v3_noweapon_s1` | `3v3/scaling_noweapon/HierarchySelfplay` | 1 | 0 | 8 | 17:27 | ~06:50 → should complete |

Priority order followed (§14 of the brief): 5v5 second seed first (highest-ranked
scale still feasible), then 3v3 — chosen over 2v2 because the pilot measured its
**largest** seed spread at N=3 (7.66 reward/N, exceeding every between-scale gap),
making it the most informative variance point available.

Both use the identical config, algorithm and hyperparameters as seed 0; **only
`--seed` differs**.

## Granularity: the achievable step budget is quantised by thread count

The runner computes `episodes = num_env_steps // buffer_size // n_rollout_threads`
(`runner/share_jsbsim_runner.py:72`), so the reached total is
`episodes × 3000 × threads`:

| threads | episodes | steps reached | vs 6M |
|---|---|---|---|
| 3 | 666 | **5,994,000** | 99.9% |
| 4 | 500 | 6,000,000 | 100% |
| 8 | 250 | 6,000,000 | 100% |
| 10 | 200 | 6,000,000 | 100% |
| 20 | 100 | 6,000,000 | 100% |

**Lesson**: a thread count must divide `6e6 / 3000 = 2000` evenly or the nominal
budget is unreachable by construction — silently, with no error. The 3-thread 1v1
lanes are the only affected ones (4 threads would have reached 6M exactly). Recorded
as F17; not "fixed", because changing it would mean relaunching into a `run2/`.

## CPU measurement corrected (F16)

All CPU figures before 17:23 came from `/proc/stat`, which in this container
reports the **host's** 192 CPUs and returns deltas alternating between 0 and ~200
cores. They are **wrong** and must not be used. The authoritative measure is the
container's cgroup `cpu.stat`:

- campaign CPU: **~38–42 of the 48-core quota (~80–87%)**
- `nr_throttled`: **0.02–0.04% of periods** — the quota was **never binding**

So the earlier "we are at 48/48, no headroom" conclusion was an artifact, and the
headroom is partly what the two second seeds above were launched into.
