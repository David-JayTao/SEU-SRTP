# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。
campaign root: `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m`（本文件位置推导；--campaign-root / $CAMPAIGN_ROOT 可覆盖）

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `f6m_official_1v1_hier_selfplay_s1` | 运行中 (仍在写入) | 522000/6000000 | 81 | -69.37 → 10.44 | 31.438 | yes |
| `f6m_official_1v1_selfplay_s1` | 运行中 (仍在写入) | 711000/6000000 | 103 | -156.4 → -79.48 | -278.47 | yes |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 运行中 (仍在写入) | 360000/6000000 | 56 | -192.9 → -21.94 | -434.72 | yes |
| `f6m_official_1v1_vsbaseline_s1` | 运行中 (仍在写入) | 828000/6000000 | 120 | -207.1 → -32.71 | - | yes |
| `f6m_official_2v2_noweapon_s0` | 运行中 (仍在写入) | 588000/6000000 | 76 | -3.507 → 10.99 | 29.017 | yes |
| `f6m_10v10_noweapon_s0` | 运行中 (仍在写入) | 540000/6000000 | 76 | -17.62 → -17.61 | -55.891 | yes |
| `f6m_2v2_noweapon_s0` | 运行中 (仍在写入) | 600000/6000000 | 77 | -3.51 → 20.49 | -0.92842 | yes |
| `f6m_3v3_noweapon_s0` | 运行中 (仍在写入) | 984000/6000000 | 127 | -5.318 → 26.64 | 17.553 | yes |
| `f6m_5v5_noweapon_s0` | 运行中 (仍在写入) | 624000/6000000 | 82 | -9.117 → -6.661 | -12.025 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/scaling_table.csv (4 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 4 | 0 | 77 | 0.052 | 155.8 | 308 | 77 | 600000 | 50 | -3.51 | 20.5 | +0.694 | -0.928 | 0.375 | 10.1 | -0.00131 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 8 | 0 | 127 | 0.063 | 189 | 762 | 95.2 | 984000 | 41 | -5.32 | 26.6 | +0.912 | 17.6 | 0.918 | 11 | -0.000704 | no | improving |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 8 | 0 | 82 | 0.0976 | 292.7 | 820 | 102 | 624000 | 26 | -9.12 | -6.66 | -0.0187 | -12 | 7.26 | 24.2 | -0.000762 | no | flat/declining |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 20 | 0 | 76 | 0.263 | 789.5 | 1520 | 76 | 540000 | 9 | -17.6 | -17.6 | -0.0853 | -55.9 | 70.4 | 47.2 | -0.000315 | no | flat/declining |

campaign peaks so far: CPU peak 46.8 busy cores of the 48-core quota (97.6% of quota; formal-6M sampler (quota-normalised)), RAM 52.6 GB, VRAM 2386 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/normalized_scaling.csv (175 rows)

=== mean over the first 5 episodes per run (hierarchical NoWeapon family) ===
(value_loss/N^2 and grad_norm/N remove the reward-magnitude growth; a purely reward-scale effect would make both constant)

  N  runs  eps  reward/N   vl/N^2    gn/N  sd(vl/N^2)  sd(gn/N)
  2     2   10    -1.638    0.502   3.942      0.0431    0.6387
  3     1    5    -1.735    0.616   3.818      0.0429    0.2219
  5     1    5    -1.808    0.677   4.574      0.0462    0.0517
 10     1    5    -1.755    0.702   4.972      0.0362    0.5015

=== matched training stage (episode index), hierarchical NoWeapon family ===
  N  ep    reward    rew/N        vl    vl/N²  critic_gn    gn/N  experiment
  2   0     -3.51    -1.76     1.814    0.453       6.20    3.10  f6m_2v2_noweapon_s0
  2   1     -3.48    -1.74     2.166    0.541       8.17    4.09  f6m_2v2_noweapon_s0
  2   2     -3.49    -1.74     2.145    0.536       8.01    4.00  f6m_2v2_noweapon_s0
  2   3     -3.44    -1.72     2.089    0.522       7.61    3.80  f6m_2v2_noweapon_s0
  2   4     -2.97    -1.48     2.154    0.538      10.93    5.46  f6m_2v2_noweapon_s0
  2   0     -3.51    -1.75     1.817    0.454       6.22    3.11  f6m_official_2v2_noweapon_s0
  2   1     -2.39    -1.19     1.881    0.470       8.48    4.24  f6m_official_2v2_noweapon_s0
  2   2     -3.53    -1.76     2.132    0.533       7.37    3.68  f6m_official_2v2_noweapon_s0
  2   3     -2.97    -1.48     2.182    0.546       8.49    4.24  f6m_official_2v2_noweapon_s0
  2   4     -3.50    -1.75     1.709    0.427       7.37    3.68  f6m_official_2v2_noweapon_s0
  3   0     -5.32    -1.77     4.862    0.540      10.18    3.39  f6m_3v3_noweapon_s0
  3   1     -5.42    -1.81     5.921    0.658      11.86    3.95  f6m_3v3_noweapon_s0
  3   2     -5.06    -1.69     5.664    0.629      11.61    3.87  f6m_3v3_noweapon_s0
  3   3     -5.08    -1.69     5.399    0.600      11.52    3.84  f6m_3v3_noweapon_s0
  3   4     -5.15    -1.72     5.867    0.652      12.09    4.03  f6m_3v3_noweapon_s0
  5   0     -9.12    -1.82    14.826    0.593      22.61    4.52  f6m_5v5_noweapon_s0
  5   1     -8.98    -1.80    16.723    0.669      22.86    4.57  f6m_5v5_noweapon_s0
  5   2     -9.08    -1.82    18.127    0.725      22.60    4.52  f6m_5v5_noweapon_s0
  5   3     -9.10    -1.82    17.747    0.710      22.98    4.60  f6m_5v5_noweapon_s0
  5   4     -8.94    -1.79    17.257    0.690      23.30    4.66  f6m_5v5_noweapon_s0
 10   0    -17.62    -1.76    63.635    0.636      59.75    5.97  f6m_10v10_noweapon_s0
 10   1    -17.67    -1.77    71.605    0.716      47.05    4.71  f6m_10v10_noweapon_s0
 10   2    -17.68    -1.77    74.679    0.747      47.42    4.74  f6m_10v10_noweapon_s0
 10   3    -17.35    -1.73    70.706    0.707      47.26    4.73  f6m_10v10_noweapon_s0
 10   4    -17.45    -1.74    70.574    0.706      47.13    4.71  f6m_10v10_noweapon_s0

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 22 | 1567% | 15.7 | 15.18 GB | 2 | 1036 MB |
| `f6m_2v2_noweapon_s0` | 6 | 288% | 2.9 | 2.97 GB | 0 | 536 MB |
| `f6m_3v3_noweapon_s0` | 10 | 552% | 5.5 | 4.61 GB | 0 | 650 MB |
| `f6m_5v5_noweapon_s0` | 10 | 603% | 6.0 | 4.85 GB | 1 | 656 MB |
| `f6m_official_1v1_hier_selfplay_s1` | 5 | 195% | 1.9 | 2.59 GB | 0 | 534 MB |
| `f6m_official_1v1_selfplay_s1` | 5 | 170% | 1.7 | 2.51 GB | 0 | 640 MB |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 5 | 220% | 2.2 | 2.62 GB | 2 | 620 MB |
| `f6m_official_1v1_vsbaseline_s1` | 5 | 204% | 2.0 | 2.69 GB | 1 | 654 MB |
| `f6m_official_2v2_noweapon_s0` | 6 | 291% | 2.9 | 2.97 GB | 1 | 536 MB |

## E. OFFICIAL BASELINE TABLE

| Experiment | Seed | Steps | Wall time | FPS | Initial reward | Final reward | Eval | Status | Checkpoint |
|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 522,000 | 1.80 h | 81 | -69.367 | 10.441 | 31.438 | running | actor_latest.pt |
| f6m_official_1v1_selfplay_s1 | 1 | 711,000 | 1.92 h | 103 | -156.44 | -79.477 | -278.47 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 360,000 | 1.80 h | 56 | -192.88 | -21.936 | -434.72 | running | actor_latest.pt |
| f6m_official_1v1_vsbaseline_s1 | 1 | 828,000 | 1.92 h | 120 | -207.14 | -32.71 | - | running | actor_latest.pt |
| f6m_official_2v2_noweapon_s0 | 0 | 588,000 | 2.18 h | 76 | -3.5066 | 10.988 | 29.017 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_vsbaseline | - | - | - | - | - | - | - | not_applicable | - |

_Status ∈ {completed_6M, running, failed, time_cutoff, early_error, not_applicable}；Steps 为目标 6,000,000 vectorised env steps 的已完成量；running 行的 Steps/FPS/Wall time/reward 为生成时刻的实时值（Wall time = 队列启动至今）。3-thread 的 1v1 lane 因 runner 取整（6e6 // 3000 // 3 = 666 episodes）在 5,994,000 步即自然结束，计为 completed_6M（不是 failed）。_

_F9: `1v1/ShootMissile/HierarchyVsBaseline` 是官方入口但在首个 env step 即报错（TypeError），本轮未启动，按 `status/running_jobs.md` 记为 not_applicable。_

## F. SCALING TABLE

| Scale | Agents | Seed | Steps | FPS | Wall time | Reward raw | Reward normalized | Value loss | Critic grad | CPU | RAM | VRAM | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | 4 | 0 | 600,000 | 77 | 2.18 h | 20.485 | 10.243 | 0.37464 | 10.067 | 2.9 | 2.97 GB | 536 MB | running |
| 3v3 | 6 | 0 | 984,000 | 127 | 2.18 h | 26.641 | 8.8802 | 0.91838 | 10.953 | 5.5 | 4.61 GB | 650 MB | running |
| 5v5 | 10 | 0 | 624,000 | 82 | 2.18 h | -6.6609 | -1.3322 | 7.2553 | 24.165 | 6.0 | 4.85 GB | 656 MB | running |
| 10v10 | 20 | 0 | 540,000 | 76 | 2.19 h | -17.613 | -1.7613 | 70.401 | 47.242 | 15.7 | 15.18 GB | 1036 MB | running |

_Reward normalized = 末次训练 reward / N（NoWeapon 家族 PostureReward 对每个 enemy 求和，故除以 team size N；ShootMissile 家族不适用该归一化）。CPU/RAM/VRAM 为该实验进程的实测峰值（ps + nvidia-smi --query-compute-apps，随本脚本每次运行累积进 metrics/resources.csv；'-' 表示尚无采样）。_

