# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。
campaign root: `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m`（本文件位置推导；--campaign-root / $CAMPAIGN_ROOT 可覆盖）

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `f6m_official_1v1_hier_selfplay_s1` | 运行中 (仍在写入) | 5310000/6000000 | 83 | -69.37 → -59.15 | -401.63 | yes |
| `f6m_official_1v1_selfplay_s1` | 已完成 (达到步数预算) | 5994000/6000000 | 104 | -156.4 → 26.93 | 36.368 | yes |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 运行中 (仍在写入) | 3924000/6000000 | 61 | -192.9 → -54.21 | 0.13253 | yes |
| `f6m_official_1v1_vsbaseline_s1` | 已完成 (达到步数预算) | 5994000/6000000 | 122 | -207.1 → 27.78 | - | yes |
| `f6m_official_2v2_noweapon_s0` | 运行中 (仍在写入) | 4920000/6000000 | 75 | -3.507 → 19.59 | 7.4297 | yes |
| `f6m_official_heading_s5` | 运行中 (仍在写入) | 1980000/6000000 | 272 | -14.82 → 168.3 | - | yes |
| `f6m_10v10_noweapon_s0` | 运行中 (仍在写入) | 4320000/6000000 | 66 | -17.62 → -0.1503 | -34.074 | yes |
| `f6m_2v2_noweapon_s0` | 运行中 (仍在写入) | 5052000/6000000 | 77 | -3.51 → 24.69 | -12.768 | yes |
| `f6m_3v3_noweapon_s0` | 已完成 (达到步数预算) | 6000000/6000000 | 125 | -5.318 → 35.93 | 47.839 | yes |
| `f6m_3v3_noweapon_s1` | 运行中 (仍在写入) | 1512000/6000000 | 118 | -5.436 → 4.315 | 46.352 | yes |
| `f6m_5v5_noweapon_s0` | 运行中 (仍在写入) | 5184000/6000000 | 79 | -9.117 → 30.46 | -61.483 | yes |
| `f6m_5v5_noweapon_s1` | 运行中 (仍在写入) | 1170000/6000000 | 89 | -9.054 → 6.211 | 42.159 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/scaling_table.csv (6 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 4 | 0 | 77 | 0.052 | 155.8 | 308 | 77 | 5052000 | 421 | -3.51 | 24.7 | +0.299 | -12.8 | 0.114 | 4.9 | -0.000524 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 8 | 0 | 125 | 0.064 | 192 | 750 | 93.8 | 6000000 | 250 | -5.32 | 35.9 | +0.0089 | 47.8 | 0.178 | 7.31 | -0.000331 | no | flat/declining |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 8 | 1 | 118 | 0.0678 | 203.4 | 708 | 88.5 | 1512000 | 63 | -5.44 | 4.31 | -1.47 | 46.4 | 0.436 | 10.7 | -0.000708 | no | flat/declining |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 8 | 0 | 79 | 0.101 | 303.8 | 790 | 98.8 | 5184000 | 216 | -9.12 | 30.5 | -0.097 | -61.5 | 0.758 | 11.6 | -0.000552 | no | flat/declining |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 10 | 1 | 89 | 0.112 | 337.1 | 890 | 89 | 1170000 | 39 | -9.05 | 6.21 | +0.208 | 42.2 | 2.31 | 25.9 | -0.000584 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 20 | 0 | 66 | 0.303 | 909.1 | 1320 | 66 | 4320000 | 72 | -17.6 | -0.15 | +0.685 | -34.1 | 6.23 | 44.2 | -0.000284 | no | improving |

campaign peaks so far: CPU peak 44.3 busy cores of the 48-core quota (92.4% of quota; cgroup cpu.stat (authoritative)), RAM 87.1 GB, VRAM 3310 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/metrics/normalized_scaling.csv (1471 rows)

=== mean over the first 5 episodes per run (hierarchical NoWeapon family) ===
(value_loss/N^2 and grad_norm/N remove the reward-magnitude growth; a purely reward-scale effect would make both constant)

  N  runs  eps  reward/N   vl/N^2    gn/N  sd(vl/N^2)  sd(gn/N)
  2     2   10    -1.638    0.502   3.942      0.0431    0.6387
  3     2   10    -1.748    0.586   3.892      0.0552    0.2053
  5     2   10    -1.781    0.654   4.573      0.0558    0.1239
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
  3   0     -5.44    -1.81     4.247    0.472      11.80    3.93  f6m_3v3_noweapon_s1
  3   1     -5.40    -1.80     5.082    0.565      12.69    4.23  f6m_3v3_noweapon_s1
  3   2     -5.13    -1.71     5.616    0.624      11.44    3.81  f6m_3v3_noweapon_s1
  3   3     -5.40    -1.80     5.223    0.580      12.09    4.03  f6m_3v3_noweapon_s1
  3   4     -5.05    -1.68     4.886    0.543      11.46    3.82  f6m_3v3_noweapon_s1
  5   0     -9.12    -1.82    14.826    0.593      22.61    4.52  f6m_5v5_noweapon_s0
  5   1     -8.98    -1.80    16.723    0.669      22.86    4.57  f6m_5v5_noweapon_s0
  5   2     -9.08    -1.82    18.127    0.725      22.60    4.52  f6m_5v5_noweapon_s0
  5   3     -9.10    -1.82    17.747    0.710      22.98    4.60  f6m_5v5_noweapon_s0
  5   4     -8.94    -1.79    17.257    0.690      23.30    4.66  f6m_5v5_noweapon_s0
  5   0     -9.05    -1.81    13.079    0.523      22.93    4.59  f6m_5v5_noweapon_s1
  5   1     -9.11    -1.82    15.902    0.636      24.39    4.88  f6m_5v5_noweapon_s1
  5   2     -8.85    -1.77    16.619    0.665      22.76    4.55  f6m_5v5_noweapon_s1
  5   3     -8.55    -1.71    16.539    0.662      21.96    4.39  f6m_5v5_noweapon_s1
  5   4     -8.30    -1.66    16.565    0.663      22.27    4.45  f6m_5v5_noweapon_s1
 10   0    -17.62    -1.76    63.635    0.636      59.75    5.97  f6m_10v10_noweapon_s0
 10   1    -17.67    -1.77    71.605    0.716      47.05    4.71  f6m_10v10_noweapon_s0
 10   2    -17.68    -1.77    74.679    0.747      47.42    4.74  f6m_10v10_noweapon_s0
 10   3    -17.35    -1.73    70.706    0.707      47.26    4.73  f6m_10v10_noweapon_s0
 10   4    -17.45    -1.74    70.574    0.706      47.13    4.71  f6m_10v10_noweapon_s0

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 22 | 1603% | 16.0 | 15.19 GB | 2 | 1036 MB |
| `f6m_2v2_noweapon_s0` | 6 | 288% | 2.9 | 2.97 GB | 0 | 536 MB |
| `f6m_3v3_noweapon_s0` | 10 | 552% | 5.5 | 4.61 GB | 0 | 650 MB |
| `f6m_3v3_noweapon_s1` | 10 | 559% | 5.6 | 4.48 GB | 0 | 650 MB |
| `f6m_5v5_noweapon_s0` | 10 | 625% | 6.2 | 4.85 GB | 1 | 660 MB |
| `f6m_5v5_noweapon_s1` | 12 | 735% | 7.4 | 5.59 GB | 2 | 712 MB |
| `f6m_official_1v1_hier_selfplay_s1` | 5 | 195% | 1.9 | 2.59 GB | 0 | 538 MB |
| `f6m_official_1v1_selfplay_s1` | 5 | 170% | 1.7 | 2.51 GB | 0 | 670 MB |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 5 | 220% | 2.2 | 2.62 GB | 2 | 620 MB |
| `f6m_official_1v1_vsbaseline_s1` | 5 | 204% | 2.0 | 2.69 GB | 1 | 654 MB |
| `f6m_official_2v2_noweapon_s0` | 6 | 291% | 2.9 | 2.97 GB | 1 | 536 MB |
| `f6m_official_heading_s5` | 6 | 175% | 1.8 | 2.82 GB | 0 | 676 MB |

## E. OFFICIAL BASELINE TABLE

| Experiment | Seed | Steps | Wall time | FPS | Initial reward | Final reward | Eval | Status | Checkpoint |
|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 5,310,000 | 17.73 h | 83 | -69.367 | -59.148 | -401.63 | running | actor_latest.pt |
| f6m_official_1v1_selfplay_s1 | 1 | 5,994,000 | 15.90 h | 104 | -156.44 | 26.933 | 36.368 | completed_6M | actor_latest.pt |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 3,924,000 | 17.73 h | 61 | -192.88 | -54.206 | 0.13253 | running | actor_latest.pt |
| f6m_official_1v1_vsbaseline_s1 | 1 | 5,994,000 | 13.59 h | 122 | -207.14 | 27.785 | - | completed_6M | actor_latest.pt |
| f6m_official_2v2_noweapon_s0 | 0 | 4,920,000 | 18.12 h | 75 | -3.5066 | 19.587 | 7.4297 | running | actor_latest.pt |
| f6m_official_heading_s5 | 5 | 1,980,000 | 2.02 h | 272 | -14.825 | 168.26 | - | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_vsbaseline | - | - | - | - | - | - | - | not_applicable | - |

_Status ∈ {completed_6M, running, failed, time_cutoff, early_error, not_applicable}；Steps 为目标 6,000,000 vectorised env steps 的已完成量；running 行的 Steps/FPS/Wall time/reward 为生成时刻的实时值（Wall time = 队列启动至今）。3-thread 的 1v1 lane 因 runner 取整（6e6 // 3000 // 3 = 666 episodes）在 5,994,000 步即自然结束，计为 completed_6M（不是 failed）。_

_F9: `1v1/ShootMissile/HierarchyVsBaseline` 是官方入口但在首个 env step 即报错（TypeError），本轮未启动，按 `status/running_jobs.md` 记为 not_applicable。_

## F. SCALING TABLE

| Scale | Agents | Seed | Steps | FPS | Wall time | Reward raw | Reward normalized | Value loss | Critic grad | CPU | RAM | VRAM | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | 4 | 0 | 5,052,000 | 77 | 18.12 h | 24.692 | 12.346 | 0.1139 | 4.8956 | 2.9 | 2.97 GB | 536 MB | running |
| 3v3 | 6 | 0 | 6,000,000 | 125 | 13.29 h | 35.932 | 11.977 | 0.17833 | 7.3129 | 5.5 | 4.61 GB | 650 MB | completed_6M |
| 3v3 | 6 | 1 | 1,512,000 | 118 | 3.61 h | 4.3149 | 1.4383 | 0.43618 | 10.678 | 5.6 | 4.48 GB | 650 MB | running |
| 5v5 | 10 | 0 | 5,184,000 | 79 | 18.12 h | 30.456 | 6.0912 | 0.7578 | 11.637 | 6.2 | 4.85 GB | 660 MB | running |
| 5v5 | 10 | 1 | 1,170,000 | 89 | 3.69 h | 6.2114 | 1.2423 | 2.3144 | 25.935 | 7.4 | 5.59 GB | 712 MB | running |
| 10v10 | 20 | 0 | 4,320,000 | 66 | 18.12 h | -0.15033 | -0.015033 | 6.2294 | 44.173 | 16.0 | 15.19 GB | 1036 MB | running |

_Reward normalized = 末次训练 reward / N（NoWeapon 家族 PostureReward 对每个 enemy 求和，故除以 team size N；ShootMissile 家族不适用该归一化）。CPU/RAM/VRAM 为该实验进程的实测峰值（ps + nvidia-smi --query-compute-apps，随本脚本每次运行累积进 metrics/resources.csv；'-' 表示尚无采样）。_

