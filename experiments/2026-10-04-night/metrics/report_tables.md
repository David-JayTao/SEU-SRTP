# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `official_1v1_hier_selfplay` | running (time-capped) | 330000/100000000 | 278 | -69.37 → -42.75 | - | yes |
| `official_1v1_selfplay` | **CRASHED** | 1350000/100000000 | 325 | -156.5 → -91.13 | - | yes |
| `official_1v1_vsbaseline` | **CRASHED** | 1500000/100000000 | 357 | -208.2 → -1.925 | - | yes |
| `official_2v2_noweapon` | **CRASHED** | 1476000/100000000 | 208 | -3.525 → 1.204 | 7.9537 | yes |
| `official_2v2_noweapon_selfplay` | **CRASHED** | 816000/100000000 | 154 | 11.16 → -16.14 | 24.192 | yes |
| `official_2v2_shoot` | running (time-capped) | 1080000/100000000 | 162 | -36.94 → -2.126 | -1.9939 | yes |
| `official_heading` | **CRASHED** | 2460000/100000000 | 590 | -13.98 → 100.6 | - | yes |
| `scaling_10v10_noweapon` | **CRASHED** | 648000/900000 | 61 | -17.66 → -16.43 | -4.4321 | yes |
| `scaling_2v2_noweapon_s1` | completed | 900000/900000 | 186 | -3.532 → 3.739 | -1.6435 | yes |
| `scaling_2v2_shoot` | **CRASHED** | 624000/900000 | 115 | -37.02 → -12.48 | -42.079 | yes |
| `scaling_3v3_noweapon_s1` | **CRASHED** | 840000/900000 | 159 | -5.435 → 19.54 | 43.627 | yes |
| `scaling_3v3_shoot` | running (time-capped) | 240000/900000 | 89 | -22.29 → -19.57 | -26.883 | yes |
| `scaling_5v5_noweapon` | running (time-capped) | 432000/900000 | 150 | -9.083 → -8.987 | -11.902 | yes |
| `scaling_5v5_noweapon_s1` | running (time-capped) | 270000/900000 | 90 | -9.054 → -7.389 | 39.515 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/scaling_table.csv (7 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 10 | 1 | 186 | 0.0538 | 161.3 | 744 | 74.4 | 900000 | 30 | -3.53 | 3.74 | +0.55 | -1.64 | 0.381 | 6.59 | -0.000603 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 10 | 1 | 159 | 0.0629 | 188.7 | 954 | 95.4 | 840000 | 28 | -5.43 | 19.5 | +2.15 | 43.6 | 1.3 | 27.5 | -0.000596 | no | improving |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 18 | 0 | 150 | 0.12 | 360 | 1500 | 83.3 | 432000 | 8 | -9.08 | -8.99 | +0.0475 | -11.9 | 13.5 | 20.8 | -0.000348 | no | flat/declining |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 10 | 1 | 90 | 0.111 | 333.3 | 900 | 90 | 270000 | 9 | -9.05 | -7.39 | +0.186 | 39.5 | 14.3 | 25.4 | -0.000625 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 0 | 61 | 0.295 | 885.2 | 1220 | 67.8 | 648000 | 12 | -17.7 | -16.4 | +0.0915 | -4.43 | 62.1 | 47.7 | -0.000343 | no | improving |
| 2v2 | shoot | 4 | 33 | 132 | 154891 | 163969 | 8 | 0 | 115 | 0.0696 | 208.7 | 460 | 57.5 | 624000 | 26 | -37 | -12.5 | +1.95 | -42.1 | 30.5 | 49.2 | -0.000898 | no | improving |
| 3v3 | shoot | 6 | 45 | 270 | 156427 | 180097 | 8 | 0 | 89 | 0.0899 | 269.7 | 534 | 66.8 | 240000 | 10 | -22.3 | -19.6 | -0.0246 | -26.9 | 34.8 | 126 | -0.000924 | no | flat/declining |

host peaks during the whole night: CPU 53.8/48 cores, RAM 62.8 GB, VRAM 1842 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/normalized_scaling.csv (128 rows)

=== matched training stage (episode index), hierarchical NoWeapon family ===
  N  ep    reward    rew/N        vl    vl/N²  critic_gn    gn/N  experiment
  2   0     -3.52    -1.76     1.791    0.448       5.35    2.68  official_2v2_noweapon
  2   1     -3.34    -1.67     2.055    0.514       6.90    3.45  official_2v2_noweapon
  2   2     -3.48    -1.74     2.057    0.514       7.39    3.70  official_2v2_noweapon
  2   3     -3.53    -1.77     1.883    0.471       6.48    3.24  official_2v2_noweapon
  2   4     -3.42    -1.71     1.708    0.427       6.90    3.45  official_2v2_noweapon
  2   0     -3.53    -1.77     1.803    0.451       5.51    2.76  scaling_2v2_noweapon_s1
  2   1     -3.51    -1.75     1.942    0.486       6.53    3.27  scaling_2v2_noweapon_s1
  2   2     -3.54    -1.77     2.026    0.507       6.66    3.33  scaling_2v2_noweapon_s1
  2   3     -3.54    -1.77     1.982    0.496       7.67    3.84  scaling_2v2_noweapon_s1
  2   4     -3.53    -1.77     1.829    0.457       7.48    3.74  scaling_2v2_noweapon_s1
  3   0     -5.43    -1.81     4.239    0.471      11.28    3.76  scaling_3v3_noweapon_s1
  3   1     -5.17    -1.72     5.193    0.577      12.76    4.25  scaling_3v3_noweapon_s1
  3   2     -5.27    -1.76     5.727    0.636      11.46    3.82  scaling_3v3_noweapon_s1
  3   3     -5.35    -1.78     5.358    0.595      12.42    4.14  scaling_3v3_noweapon_s1
  3   4     -5.37    -1.79     4.645    0.516      11.46    3.82  scaling_3v3_noweapon_s1
  5   0     -9.08    -1.82    14.721    0.589      21.40    4.28  scaling_5v5_noweapon
  5   1     -8.89    -1.78    17.597    0.704      21.92    4.38  scaling_5v5_noweapon
  5   2     -9.09    -1.82    16.448    0.658      22.03    4.41  scaling_5v5_noweapon
  5   3     -9.08    -1.82    16.743    0.670      23.57    4.71  scaling_5v5_noweapon
  5   4     -9.12    -1.82    15.117    0.605      21.59    4.32  scaling_5v5_noweapon
  5   0     -9.05    -1.81    13.079    0.523      22.93    4.59  scaling_5v5_noweapon_s1
  5   1     -9.11    -1.82    15.902    0.636      24.39    4.88  scaling_5v5_noweapon_s1
  5   2     -8.85    -1.77    16.619    0.665      22.76    4.55  scaling_5v5_noweapon_s1
  5   3     -8.55    -1.71    16.539    0.662      21.96    4.39  scaling_5v5_noweapon_s1
  5   4     -8.30    -1.66    16.565    0.663      22.27    4.45  scaling_5v5_noweapon_s1
 10   0    -17.66    -1.77    63.838    0.638      61.57    6.16  scaling_10v10_noweapon
 10   1    -17.57    -1.76    72.391    0.724      46.94    4.69  scaling_10v10_noweapon
 10   2    -17.56    -1.76    73.277    0.733      46.92    4.69  scaling_10v10_noweapon
 10   3    -17.65    -1.76    70.535    0.705      47.18    4.72  scaling_10v10_noweapon
 10   4    -17.46    -1.75    69.102    0.691      47.23    4.72  scaling_10v10_noweapon

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `official_1v1_hier_selfplay` | 12 | 459% | 4.6 | 5.02 GB | 0 | 1241 MB |
| `official_1v1_selfplay` | 12 | 346% | 3.5 | 4.77 GB | 0 | 1281 MB |
| `official_1v1_vsbaseline` | 12 | 481% | 4.8 | 5.39 GB | 0 | 1433 MB |
| `official_2v2_noweapon` | 14 | 672% | 6.7 | 5.83 GB | 1 | 1405 MB |
| `official_2v2_noweapon_selfplay` | 10 | 416% | 4.2 | 4.20 GB | 0 | 1559 MB |
| `official_2v2_shoot` | 14 | 688% | 6.9 | 5.78 GB | 1 | 1343 MB |
| `official_heading` | 12 | 326% | 3.3 | 4.75 GB | 0 | 1559 MB |
| `scaling_10v10_noweapon` | 20 | 1218% | 12.2 | 13.83 GB | 2 | 994 MB |
| `scaling_2v2_noweapon_s1` | 12 | 594% | 5.9 | 5.11 GB | 1 | 1405 MB |
| `scaling_2v2_shoot` | 10 | 493% | 4.9 | 4.45 GB | 0 | 1433 MB |
| `scaling_3v3_noweapon_s1` | 12 | 620% | 6.2 | 5.21 GB | 1 | 1405 MB |
| `scaling_3v3_shoot` | 10 | 513% | 5.1 | 4.48 GB | 0 | 1267 MB |
| `scaling_5v5_noweapon` | 20 | 1192% | 11.9 | 8.81 GB | 2 | 902 MB |
| `scaling_5v5_noweapon_s1` | 12 | 661% | 6.6 | 5.60 GB | 1 | 1343 MB |

