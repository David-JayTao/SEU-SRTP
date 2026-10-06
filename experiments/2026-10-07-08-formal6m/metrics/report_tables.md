# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。
campaign root: `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m`（本文件位置推导；--campaign-root / $CAMPAIGN_ROOT 可覆盖）

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `f6m_official_1v1_hier_selfplay_s1` | 运行中 (仍在写入) | 135000/6000000 | 85 | -69.37 → -39.51 | - | yes |
| `f6m_official_1v1_selfplay_s1` | 运行中 (仍在写入) | 216000/6000000 | 106 | -156.4 → -154.1 | - | yes |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 运行中 (仍在写入) | 81000/6000000 | 55 | -192.9 → -101.7 | - | yes |
| `f6m_official_1v1_vsbaseline_s1` | 运行中 (仍在写入) | 243000/6000000 | 119 | -207.1 → -222.9 | - | yes |
| `f6m_official_2v2_noweapon_s0` | 运行中 (仍在写入) | 228000/6000000 | 78 | -3.507 → -1.873 | -121.41 | yes |
| `f6m_10v10_noweapon_s0` | 运行中 (仍在写入) | 180000/6000000 | 67 | -17.62 → -17.68 | -93.849 | yes |
| `f6m_2v2_noweapon_s0` | 运行中 (仍在写入) | 228000/6000000 | 79 | -3.51 → -1.732 | -4.5171 | yes |
| `f6m_3v3_noweapon_s0` | 运行中 (仍在写入) | 384000/6000000 | 127 | -5.318 → -0.03177 | -5.3127 | yes |
| `f6m_5v5_noweapon_s0` | 运行中 (仍在写入) | 240000/6000000 | 81 | -9.117 → -8.697 | -11.185 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/scaling_table.csv (4 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | None | None | None | None | 4 | 0 | 79 | 0.0506 | 151.9 | 316 | 79 | 228000 | 19 | -3.51 | -1.73 | +0.086 | -4.52 | 0.529 | 10.2 | -0.00153 | no | improving |
| 3v3 | noweapon | 6 | None | None | None | None | 8 | 0 | 127 | 0.063 | 189 | 762 | 95.2 | 384000 | 16 | -5.32 | -0.0318 | +1.09 | -5.31 | 2.92 | 17.4 | -0.000777 | no | improving |
| 5v5 | noweapon | 10 | None | None | None | None | 8 | 0 | 81 | 0.0988 | 296.3 | 810 | 101 | 240000 | 10 | -9.12 | -8.7 | -1.54 | -11.2 | 13.3 | 22.7 | -0.000781 | no | flat/declining |
| 10v10 | noweapon | 20 | None | None | None | None | 20 | 0 | 67 | 0.299 | 895.5 | 1340 | 67 | 180000 | 3 | -17.6 | -17.7 | - | -93.8 | 74.7 | 47.4 | -0.000316 | no | ? |

host peaks over the campaign so far: CPU 175.9/48 cores, RAM 52.6 GB, VRAM 2358 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/normalized_scaling.csv (67 rows)

=== mean over the first 5 episodes per run (hierarchical NoWeapon family) ===
(value_loss/N^2 and grad_norm/N remove the reward-magnitude growth; a purely reward-scale effect would make both constant)

  N  runs  eps  reward/N   vl/N^2    gn/N  sd(vl/N^2)  sd(gn/N)
  2     2   10    -1.638    0.502   3.942      0.0431    0.6387
  3     1    5    -1.735    0.616   3.818      0.0429    0.2219
  5     1    5    -1.808    0.677   4.574      0.0462    0.0517
 10     1    3    -1.766    0.700   5.141      0.0465    0.5901

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

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 22 | 1401% | 14.0 | 15.17 GB | 2 | 1036 MB |
| `f6m_2v2_noweapon_s0` | 6 | 286% | 2.9 | 2.97 GB | 0 | 534 MB |
| `f6m_3v3_noweapon_s0` | 10 | 550% | 5.5 | 4.48 GB | 0 | 650 MB |
| `f6m_5v5_noweapon_s0` | 10 | 598% | 6.0 | 4.85 GB | 1 | 656 MB |
| `f6m_official_1v1_hier_selfplay_s1` | 5 | 195% | 1.9 | 2.59 GB | 0 | 534 MB |
| `f6m_official_1v1_selfplay_s1` | 5 | 170% | 1.7 | 2.50 GB | 0 | 614 MB |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 5 | 218% | 2.2 | 2.62 GB | 2 | 568 MB |
| `f6m_official_1v1_vsbaseline_s1` | 5 | 203% | 2.0 | 2.64 GB | 1 | 600 MB |
| `f6m_official_2v2_noweapon_s0` | 6 | 291% | 2.9 | 2.97 GB | 1 | 534 MB |

## E. OFFICIAL BASELINE TABLE

| Experiment | Seed | Steps | Wall time | FPS | Initial reward | Final reward | Eval | Status | Checkpoint |
|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 135,000 | 0.45 h | 85 | -69.367 | -39.511 | -378.97 | running | actor_latest.pt |
| f6m_official_1v1_selfplay_s1 | 1 | 216,000 | 0.58 h | 106 | -156.44 | -154.07 | -105.75 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 81,000 | 0.45 h | 55 | -192.88 | -101.68 | -434.71 | running | actor_latest.pt |
| f6m_official_1v1_vsbaseline_s1 | 1 | 243,000 | 0.58 h | 119 | -207.14 | -222.86 | - | running | actor_latest.pt |
| f6m_official_2v2_noweapon_s0 | 0 | 228,000 | 0.84 h | 78 | -3.5066 | -1.8733 | -121.41 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_vsbaseline | - | - | - | - | - | - | - | not_applicable | - |

_Status ∈ {completed_6M, running, failed, time_cutoff, early_error, not_applicable}；Steps 为目标 6,000,000 vectorised env steps 的已完成量；running 行的 Steps/FPS/Wall time/reward 为生成时刻的实时值（Wall time = 队列启动至今）。3-thread 的 1v1 lane 因 runner 取整（6e6 // 3000 // 3 = 666 episodes）在 5,994,000 步即自然结束，计为 completed_6M（不是 failed）。_

_F9: `1v1/ShootMissile/HierarchyVsBaseline` 是官方入口但在首个 env step 即报错（TypeError），本轮未启动，按 `status/running_jobs.md` 记为 not_applicable。_

## F. SCALING TABLE

| Scale | Agents | Seed | Steps | FPS | Wall time | Reward raw | Reward normalized | Value loss | Critic grad | CPU | RAM | VRAM | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | 4 | 0 | 228,000 | 79 | 0.84 h | -1.7322 | -0.86608 | 0.52859 | 10.25 | 2.9 | 2.97 GB | 534 MB | running |
| 3v3 | 6 | 0 | 384,000 | 127 | 0.84 h | -0.031766 | -0.010589 | 2.9171 | 17.353 | 5.5 | 4.48 GB | 650 MB | running |
| 5v5 | 10 | 0 | 240,000 | 81 | 0.84 h | -8.6972 | -1.7394 | 13.343 | 22.663 | 6.0 | 4.85 GB | 656 MB | running |
| 10v10 | 20 | 0 | 180,000 | 67 | 0.84 h | -17.68 | -1.768 | 74.679 | 47.418 | 14.0 | 15.17 GB | 1036 MB | running |

_Reward normalized = 末次训练 reward / N（NoWeapon 家族 PostureReward 对每个 enemy 求和，故除以 team size N；ShootMissile 家族不适用该归一化）。CPU/RAM/VRAM 为该实验进程的实测峰值（ps + nvidia-smi --query-compute-apps，随本脚本每次运行累积进 metrics/resources.csv；'-' 表示尚无采样）。_

