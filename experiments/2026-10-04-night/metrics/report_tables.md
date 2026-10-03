# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `official_2v2_noweapon` | running (time-capped) | 540000/100000000 | 211 | -3.525 → -3.498 | -40.158 | yes |
| `official_2v2_noweapon_selfplay` | running (time-capped) | 360000/100000000 | 154 | 11.16 → 14.48 | 15.313 | yes |
| `official_heading` | running (time-capped) | 1500000/100000000 | 585 | -13.98 → 29.2 | - | yes |
| `scaling_10v10_noweapon` | running (time-capped) | 108000/900000 | 53 | -17.66 → -17.57 | -279.43 | yes |
| `scaling_3v3_noweapon_s1` | running (time-capped) | 330000/900000 | 155 | -5.435 → -0.5674 | -136.23 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/scaling_table.csv (2 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 10 | 1 | 155 | 0.0645 | 193.5 | 930 | 93 | 330000 | 11 | -5.43 | -0.567 | +1.48 | -136 | 3.39 | 13.1 | -0.00062 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 0 | 53 | 0.34 | 1019 | 1060 | 58.9 | 108000 | 2 | -17.7 | -17.6 | - | -279 | 72.4 | 46.9 | -0.000352 | no | ? |

host peaks during the whole night: CPU 48.0/48 cores, RAM 60.1 GB, VRAM 1842 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/normalized_scaling.csv (28 rows)

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

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `official_2v2_noweapon` | 14 | 663% | 6.6 | 5.80 GB | 1 | 1405 MB |
| `official_2v2_noweapon_selfplay` | 10 | 408% | 4.1 | 4.20 GB | 0 | 1359 MB |
| `official_heading` | 12 | 323% | 3.2 | 4.75 GB | 0 | 1359 MB |
| `scaling_10v10_noweapon` | 20 | 1218% | 12.2 | 13.83 GB | 2 | 994 MB |
| `scaling_3v3_noweapon_s1` | 12 | 612% | 6.1 | 5.21 GB | 1 | 1405 MB |

