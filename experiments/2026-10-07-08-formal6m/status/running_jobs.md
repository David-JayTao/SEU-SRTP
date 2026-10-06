# Running jobs — formal 6M campaign (2026-10-07 → 2026-10-08)

Launched **2026-10-07 02:54:31 CST**. Hard deadline **2026-10-08 10:00 CST**.
Branch: `exp/formal-6m-20261007` @ `d133be6`.

Budget definition: `--num-env-steps 6e6` = **6,000,000 vectorised environment
steps**, *not* agent-steps. Verified against the runner's own accounting:
`total_num_steps` increments by `n_rollout_threads × buffer_size` (buffer_size is
fixed at the official 3000), e.g. 20 threads → 60,000 per update.
6M is a *formal-budget* reproduction, not the official 100M convergence budget.

## Wave 1 — all launched 02:54:31

| tmux session | experiment_id | scenario | algo | seed | GPU | threads | target | wall cap | log |
|---|---|---|---|---|---|---|---|---|---|
| `f6m_10v10` | `f6m_10v10_noweapon_s0` | `10v10/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 2 | 20 | 6e6 | 108000 s | `logs/f6m_10v10_noweapon_s0_seed0_gpu2_20261007_025431.log` |
| `f6m_5v5` | `f6m_5v5_noweapon_s0` | `5v5/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 1 | 8 | 6e6 | 108000 s | `logs/f6m_5v5_noweapon_s0_seed0_gpu1_20261007_025433.log` |
| `f6m_3v3` | `f6m_3v3_noweapon_s0` | `3v3/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 8 | 6e6 | 108000 s | `logs/f6m_3v3_noweapon_s0_seed0_gpu0_20261007_025433.log` |
| `f6m_2v2` | `f6m_2v2_noweapon_s0` | `2v2/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 4 | 6e6 | 108000 s | `logs/f6m_2v2_noweapon_s0_seed0_gpu0_20261007_025433.log` |
| `f6m_off2v2` | `f6m_official_2v2_noweapon_s0` | `2v2/NoWeapon/HierarchySelfplay` | mappo | 0 | 1 | 4 | 6e6 | 108000 s | `logs/f6m_official_2v2_noweapon_s0_seed0_gpu1_20261007_025433.log` |

Total rollout threads: **44** (4 cores left for OS / learner / logging / analysis).
GPU assignment is arbitrary — VRAM use is <1 GB per job and GPU utilisation is
0–6%; **CPU is the binding constraint**.

Queue files: `configs/queue_gpu2.txt` (lane A), `queue_gpu1.txt` (B),
`queue_gpu0.txt` (C), `queue_gpu0b.txt` (D), `queue_gpu1b.txt` (E).

## Launch command

```bash
cd experiments/2026-10-07-08-formal6m
bash scripts/run_queue.sh <gpu_id> configs/<queue>.txt
```

`run_train.sh` reproduces the official `scripts/*.sh` hyper-parameters verbatim
(lr 3e-4, gamma 0.99, ppo-epoch 4, clip 0.2, max-grad-norm 2, entropy 1e-3,
hidden 128×128, act-hidden 128×128, recurrent 128×1, data-chunk 8,
num-mini-batch 5, buffer-size 3000), with the two documented compatibility
deviations (no wandb; `--clip-param` passed explicitly at its default value).
Run-level deviations from official: `num_env_steps` 1e8→6e6 and
`n_rollout_threads` 32→{4,8,20}. Nothing else.

## Deviations to disclose in the report

1. **`n_rollout_threads` differs across scale** (2v2=4, 3v3=8, 5v5=8, 10v10=20).
   This is forced by wall-clock: at a constant thread count 10v10 cannot reach
   6M inside the window. Consequence: the PPO update batch is
   `n_rollout_threads × 3000`, so it is 12k / 24k / 24k / 60k samples for
   N=2/3/5/10. **This is a genuine confound on the cross-N comparison and is
   recorded as such.** It is constant across seeds, so seed-variance and
   same-N comparisons stay clean.
2. Official baselines keep the official `--eval-interval 1`; the generated
   scaling configs use `--eval-interval 2` (as in the 2026-10-04 pilot) to
   cut eval overhead. Eval runs in separate envs and does not affect training.
3. `2v2/NoWeapon/HierarchySelfplay` (official) vs `2v2/scaling_noweapon/`
   (generated) differ only in a 0.005° longitude formation shift; both are run
   so the official baseline is uncontaminated and the scaling series is
   internally consistent.

## Superseded by Wave 1

The 2026-10-04 campaign runs are **pilot / exploratory** (all ≤1.48M steps, all
time-capped, several interrupted). They are retained as pilot curves and are
plotted separately from the 6M formal runs. None is being extended into a
formal 6M run (see `docs/formal_repro_scaling_2026-10-07_08.md` §3/§4).

## Monitoring

```bash
python experiments/2026-10-07-08-formal6m/scripts/watch_f6m.py
```

Writes `metrics/status.json`, `status/monitor_latest.md`, and appends to
`metrics/throughput_history.csv`.
