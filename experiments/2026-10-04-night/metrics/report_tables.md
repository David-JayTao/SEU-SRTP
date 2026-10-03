# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `official_1v1_vsbaseline` | running (time-capped) | 150000/100000000 | 348 | -208.2 → -211.9 | - | yes |
| `official_2v2_noweapon` | running (time-capped) | 972000/100000000 | 209 | -3.525 → -0.2723 | -74.851 | yes |
| `official_2v2_noweapon_selfplay` | running (time-capped) | 672000/100000000 | 153 | 11.16 → 18.13 | -6.5831 | yes |
| `official_heading` | **CRASHED** | 2460000/100000000 | 590 | -13.98 → 100.6 | - | yes |
| `scaling_10v10_noweapon` | running (time-capped) | 216000/900000 | 55 | -17.66 → -17.65 | -129.76 | yes |
| `scaling_3v3_noweapon_s1` | running (time-capped) | 660000/900000 | 159 | -5.435 → -1.108 | 21.429 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/scaling_table.csv (2 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 10 | 1 | 159 | 0.0629 | 188.7 | 954 | 95.4 | 660000 | 22 | -5.43 | -1.11 | -0.0564 | 21.4 | 1.21 | 15.5 | -0.000606 | no | flat/declining |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 0 | 55 | 0.327 | 981.8 | 1100 | 61.1 | 216000 | 4 | -17.7 | -17.6 | - | -130 | 70.5 | 47.2 | -0.000351 | no | ? |

host peaks during the whole night: CPU 48.0/48 cores, RAM 60.1 GB, VRAM 1842 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/normalized_scaling.csv (53 rows)

=== matched training stage (episode index), hierarchical NoWeapon family ===
  N  ep    reward    rew/N        vl    vl/N²  critic_gn    gn/N  experiment
  2   0     -3.52    -1.76     1.791    0.448       5.35    2.68  official_2v2_noweapon
  2   1     -3.34    -1.67     2.055    0.514       6.90    3.45  official_2v2_noweapon
  2   2     -3.48    -1.74     2.057    0.514       7.39    3.70  official_2v2_noweapon
  2   3     -3.53    -1.77     1.883    0.471       6.48    3.24  official_2v2_noweapon
  2   4     -3.42    -1.71     1.708    0.427       6.90    3.45  official_2v2_noweapon
  3   0     -5.43    -1.81     4.239    0.471      11.28    3.76  scaling_3v3_noweapon_s1
  3   1     -5.17    -1.72     5.193    0.577      12.76    4.25  scaling_3v3_noweapon_s1
  3   2     -5.27    -1.76     5.727    0.636      11.46    3.82  scaling_3v3_noweapon_s1
  3   3     -5.35    -1.78     5.358    0.595      12.42    4.14  scaling_3v3_noweapon_s1
  3   4     -5.37    -1.79     4.645    0.516      11.46    3.82  scaling_3v3_noweapon_s1
 10   0    -17.66    -1.77    63.838    0.638      61.57    6.16  scaling_10v10_noweapon
 10   1    -17.57    -1.76    72.391    0.724      46.94    4.69  scaling_10v10_noweapon
 10   2    -17.56    -1.76    73.277    0.733      46.92    4.69  scaling_10v10_noweapon
 10   3    -17.65    -1.76    70.535    0.705      47.18    4.72  scaling_10v10_noweapon

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `official_1v1_vsbaseline` | 12 | 472% | 4.7 | 5.13 GB | 0 | 1315 MB |
| `official_2v2_noweapon` | 14 | 668% | 6.7 | 5.83 GB | 1 | 1405 MB |
| `official_2v2_noweapon_selfplay` | 10 | 414% | 4.1 | 4.20 GB | 0 | 1559 MB |
| `official_heading` | 12 | 326% | 3.3 | 4.75 GB | 0 | 1559 MB |
| `scaling_10v10_noweapon` | 20 | 1218% | 12.2 | 13.83 GB | 2 | 994 MB |
| `scaling_3v3_noweapon_s1` | 12 | 620% | 6.2 | 5.21 GB | 1 | 1405 MB |

