# 报告表格快照（自动生成，勿手改）

由 `scripts/make_report_tables.py` 在每次 sweep 时重新生成。

## A. Baseline 复现与缩放实验状态

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 首→末 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `official_1v1_dodge_vsbaseline` | 已结束 (墙钟上限截断) | 1020000/100000000 | 249 | -248.9 → -249.5 | -230.69 | yes |
| `official_1v1_dodgemissile_selfplay` | 已结束 (墙钟上限截断) | 900000/100000000 | 218 | -265.4 → -0.365 | - | yes |
| `official_1v1_hier_dodge_vsbaseline` | 已结束 (墙钟上限截断) | 1140000/100000000 | 277 | -257.5 → -43.22 | -218.88 | yes |
| `official_1v1_hier_selfplay` | 已结束 (墙钟上限截断) | 1140000/100000000 | 276 | -69.37 → 36.77 | - | yes |
| `official_1v1_selfplay` | 已结束 (墙钟上限截断) | 1350000/100000000 | 325 | -156.5 → -91.13 | - | yes |
| `official_1v1_shoot_hier_selfplay` | 已结束 (墙钟上限截断) | 720000/100000000 | 172 | -195.8 → -21.06 | - | yes |
| `official_1v1_shoot_hier_vsbaseline` | **失败 (见 F9)** | / | - | - → - | - | no |
| `official_1v1_shoot_selfplay` | 已结束 (墙钟上限截断) | 660000/100000000 | 160 | -221.2 → -225.7 | - | yes |
| `official_1v1_vsbaseline` | 已结束 (墙钟上限截断) | 1500000/100000000 | 357 | -208.2 → -1.925 | - | yes |
| `official_2v2_noweapon` | 已结束 (墙钟上限截断) | 1476000/100000000 | 208 | -3.525 → 1.204 | 7.9537 | yes |
| `official_2v2_noweapon_s1b` | 已结束 (墙钟上限截断) | 1152000/100000000 | 219 | -3.511 → 8.633 | -162.51 | yes |
| `official_2v2_noweapon_selfplay` | 已结束 (墙钟上限截断) | 816000/100000000 | 154 | 11.16 → -16.14 | 24.192 | yes |
| `official_2v2_shoot` | 已结束 (墙钟上限截断) | 1152000/100000000 | 163 | -36.94 → 9.077 | -9.1317 | yes |
| `official_heading` | 已结束 (墙钟上限截断) | 2460000/100000000 | 590 | -13.98 → 100.6 | - | yes |
| `scaling_10v10_noweapon` | 已结束 (墙钟上限截断) | 648000/900000 | 61 | -17.66 → -16.43 | -4.4321 | yes |
| `scaling_10v10_noweapon_s1` | 已结束 (墙钟上限截断) | 594000/900000 | 57 | -17.66 → -15.28 | -17.556 | yes |
| `scaling_10v10_noweapon_s2` | 已结束 (墙钟上限截断) | 594000/900000 | 57 | -17.68 → -15.89 | -21.814 | yes |
| `scaling_2v2_noweapon` | 已完成 (达到步数预算) | 900000/900000 | 223 | -3.526 → -0.1223 | -48.366 | yes |
| `scaling_2v2_noweapon_s1` | 已完成 (达到步数预算) | 900000/900000 | 186 | -3.532 → 3.739 | -1.6435 | yes |
| `scaling_2v2_noweapon_s2` | 已完成 (达到步数预算) | 900000/900000 | 220 | -3.534 → -1.24 | -2.2117 | yes |
| `scaling_2v2_shoot` | 已结束 (墙钟上限截断) | 624000/900000 | 115 | -37.02 → -12.48 | -42.079 | yes |
| `scaling_3v3_noweapon` | 已结束 (墙钟上限截断) | 864000/900000 | 257 | -5.382 → -1.496 | -6.9778 | yes |
| `scaling_3v3_noweapon_s1` | 已结束 (墙钟上限截断) | 840000/900000 | 159 | -5.435 → 19.54 | 43.627 | yes |
| `scaling_3v3_noweapon_s2` | 已结束 (墙钟上限截断) | 840000/900000 | 160 | -5.233 → -3.435 | -32.77 | yes |
| `scaling_3v3_noweapon_s3` | 已结束 (墙钟上限截断) | 672000/900000 | 126 | -5.429 → -1.46 | -7.6903 | yes |
| `scaling_3v3_shoot` | 已结束 (墙钟上限截断) | 648000/900000 | 90 | -22.29 → -19.01 | -31.709 | yes |
| `scaling_5v5_noweapon` | 已结束 (墙钟上限截断) | 864000/900000 | 154 | -9.083 → -8.669 | -12.092 | yes |
| `scaling_5v5_noweapon_s1` | 已结束 (墙钟上限截断) | 630000/900000 | 92 | -9.054 → 5.042 | 8.471 | yes |
| `scaling_5v5_noweapon_s2` | 已结束 (墙钟上限截断) | 864000/900000 | 156 | -9.008 → -4.015 | -151.49 | yes |
| `scaling_5v5_shoot` | 已结束 (墙钟上限截断) | 384000/900000 | 55 | 10.93 → 11.84 | 0.36383 | yes |

## B. Scaling 对比表（含 wall-clock 归一化）

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/scaling_table.csv (16 rows)

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | s/vec-step | s/rollout-ep | agent-steps/s | ag-steps/s/thr | steps | eps | rew_first | rew_last | slope | eval_rew | value_loss | critic_gn | entropy | NaN? | learnable? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 12 | 0 | 223 | 0.0538 | 161.4 | 892 | 74.3 | 900000 | 25 | -3.53 | -0.122 | +0.359 | -48.4 | 0.297 | 11.4 | -0.000505 | no | improving |
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 10 | 1 | 186 | 0.0538 | 161.3 | 744 | 74.4 | 900000 | 30 | -3.53 | 3.74 | +0.55 | -1.64 | 0.381 | 6.59 | -0.000603 | no | improving |
| 2v2 | noweapon | 4 | 27 | 108 | 154891 | 163969 | 12 | 2 | 220 | 0.0546 | 163.6 | 880 | 73.3 | 900000 | 25 | -3.53 | -1.24 | +0.307 | -2.21 | 0.211 | 5.47 | -0.000516 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 18 | 0 | 257 | 0.07 | 210.1 | 1542 | 85.7 | 864000 | 16 | -5.38 | -1.5 | +0.585 | -6.98 | 2.62 | 10.1 | -0.000347 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 10 | 1 | 159 | 0.0629 | 188.7 | 954 | 95.4 | 840000 | 28 | -5.43 | 19.5 | +2.15 | 43.6 | 1.3 | 27.5 | -0.000596 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 10 | 2 | 160 | 0.0625 | 187.5 | 960 | 96 | 840000 | 28 | -5.23 | -3.44 | +0.0715 | -32.8 | 0.958 | 14.4 | -0.000605 | no | improving |
| 3v3 | noweapon | 6 | 39 | 234 | 156427 | 180097 | 8 | 3 | 126 | 0.0635 | 190.5 | 756 | 94.5 | 672000 | 28 | -5.43 | -1.46 | -1.16 | -7.69 | 0.942 | 9.4 | -0.000752 | no | flat/declining |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 18 | 0 | 154 | 0.117 | 350.6 | 1540 | 85.6 | 864000 | 16 | -9.08 | -8.67 | +0.0784 | -12.1 | 10.7 | 24.8 | -0.000341 | no | improving |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 10 | 1 | 92 | 0.109 | 326.1 | 920 | 92 | 630000 | 21 | -9.05 | 5.04 | +1.61 | 8.47 | 6.98 | 33.4 | -0.000612 | no | improving |
| 5v5 | noweapon | 10 | 63 | 630 | 159499 | 230785 | 18 | 2 | 156 | 0.115 | 346.2 | 1560 | 86.7 | 864000 | 16 | -9.01 | -4.01 | +0.521 | -151 | 11.5 | 29.2 | -0.000346 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 0 | 61 | 0.295 | 885.2 | 1220 | 67.8 | 648000 | 12 | -17.7 | -16.4 | +0.0915 | -4.43 | 62.1 | 47.7 | -0.000343 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 1 | 57 | 0.316 | 947.4 | 1140 | 63.3 | 594000 | 11 | -17.7 | -15.3 | +0.557 | -17.6 | 64.9 | 49.6 | -0.000346 | no | improving |
| 10v10 | noweapon | 20 | 123 | 2460 | 167179 | 465025 | 18 | 2 | 57 | 0.316 | 947.4 | 1140 | 63.3 | 594000 | 11 | -17.7 | -15.9 | +0.0057 | -21.8 | 67.5 | 47.6 | -0.000349 | no | flat/declining |
| 2v2 | shoot | 4 | 33 | 132 | 154891 | 163969 | 8 | 0 | 115 | 0.0696 | 208.7 | 460 | 57.5 | 624000 | 26 | -37 | -12.5 | +1.95 | -42.1 | 30.5 | 49.2 | -0.000898 | no | improving |
| 3v3 | shoot | 6 | 45 | 270 | 156427 | 180097 | 8 | 0 | 90 | 0.0889 | 266.7 | 540 | 67.5 | 648000 | 27 | -22.3 | -19 | -0.177 | -31.7 | 23.6 | 102 | -0.0009 | no | flat/declining |
| 5v5 | shoot | 10 | 69 | 690 | 159499 | 230785 | 8 | 0 | 55 | 0.145 | 436.4 | 550 | 68.8 | 384000 | 16 | 10.9 | 11.8 | +0.676 | 0.364 | 13.9 | 135 | -0.000919 | no | improving |

host peaks during the whole night: CPU 65.3/48 cores, RAM 132.8 GB, VRAM 1842 MB (single job uses <1.5 GB)

## C. 归一化后的 critic 对比

wrote /root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/metrics/normalized_scaling.csv (308 rows)

=== mean over the first 5 episodes per run (hierarchical NoWeapon family) ===
(value_loss/N^2 and grad_norm/N remove the reward-magnitude growth; a purely reward-scale effect would make both constant)

  N  runs  eps  reward/N   vl/N^2    gn/N  sd(vl/N^2)  sd(gn/N)
  2     4   20    -1.748    0.479   3.420      0.0348    0.4374
  3     4   20    -1.762    0.584   3.891      0.0588    0.2857
  5     3   15    -1.775    0.643   4.458      0.0512    0.1764
 10     3   15    -1.739    0.704   5.201      0.0337    0.7730

=== matched training stage (episode index), hierarchical NoWeapon family ===
  N  ep    reward    rew/N        vl    vl/N²  critic_gn    gn/N  experiment
  2   0     -3.52    -1.76     1.791    0.448       5.35    2.68  official_2v2_noweapon
  2   1     -3.34    -1.67     2.055    0.514       6.90    3.45  official_2v2_noweapon
  2   2     -3.48    -1.74     2.057    0.514       7.39    3.70  official_2v2_noweapon
  2   3     -3.53    -1.77     1.883    0.471       6.48    3.24  official_2v2_noweapon
  2   4     -3.42    -1.71     1.708    0.427       6.90    3.45  official_2v2_noweapon
  2   0     -3.53    -1.76     1.793    0.448       5.34    2.67  scaling_2v2_noweapon
  2   1     -3.52    -1.76     2.132    0.533       7.32    3.66  scaling_2v2_noweapon
  2   2     -3.50    -1.75     2.104    0.526       7.59    3.79  scaling_2v2_noweapon
  2   3     -3.33    -1.67     1.865    0.466       7.39    3.69  scaling_2v2_noweapon
  2   4     -3.48    -1.74     1.773    0.443       7.84    3.92  scaling_2v2_noweapon
  2   0     -3.53    -1.77     1.803    0.451       5.51    2.76  scaling_2v2_noweapon_s1
  2   1     -3.51    -1.75     1.942    0.486       6.53    3.27  scaling_2v2_noweapon_s1
  2   2     -3.54    -1.77     2.026    0.507       6.66    3.33  scaling_2v2_noweapon_s1
  2   3     -3.54    -1.77     1.982    0.496       7.67    3.84  scaling_2v2_noweapon_s1
  2   4     -3.53    -1.77     1.829    0.457       7.48    3.74  scaling_2v2_noweapon_s1
  2   0     -3.53    -1.77     1.883    0.471       5.20    2.60  scaling_2v2_noweapon_s2
  2   1     -3.53    -1.76     1.986    0.496       6.83    3.42  scaling_2v2_noweapon_s2
  2   2     -3.52    -1.76     2.170    0.543       7.85    3.93  scaling_2v2_noweapon_s2
  2   3     -3.50    -1.75     1.879    0.470       6.50    3.25  scaling_2v2_noweapon_s2
  2   4     -3.53    -1.77     1.676    0.419       8.06    4.03  scaling_2v2_noweapon_s2
  3   0     -5.38    -1.79     4.763    0.529       9.71    3.24  scaling_3v3_noweapon
  3   1     -5.30    -1.77     6.061    0.673      11.46    3.82  scaling_3v3_noweapon
  3   2     -5.39    -1.80     5.923    0.658      11.34    3.78  scaling_3v3_noweapon
  3   3     -5.41    -1.80     5.655    0.628      11.26    3.75  scaling_3v3_noweapon
  3   4     -5.31    -1.77     5.352    0.595      12.01    4.00  scaling_3v3_noweapon
  3   0     -5.43    -1.81     4.239    0.471      11.28    3.76  scaling_3v3_noweapon_s1
  3   1     -5.17    -1.72     5.193    0.577      12.76    4.25  scaling_3v3_noweapon_s1
  3   2     -5.27    -1.76     5.727    0.636      11.46    3.82  scaling_3v3_noweapon_s1
  3   3     -5.35    -1.78     5.358    0.595      12.42    4.14  scaling_3v3_noweapon_s1
  3   4     -5.37    -1.79     4.645    0.516      11.46    3.82  scaling_3v3_noweapon_s1
  3   0     -5.23    -1.74     4.322    0.480      10.11    3.37  scaling_3v3_noweapon_s2
  3   1     -5.40    -1.80     5.573    0.619      12.62    4.21  scaling_3v3_noweapon_s2
  3   2     -5.23    -1.74     5.748    0.639      12.66    4.22  scaling_3v3_noweapon_s2
  3   3     -5.23    -1.74     5.410    0.601      11.49    3.83  scaling_3v3_noweapon_s2
  3   4     -5.36    -1.79     5.206    0.578      13.22    4.41  scaling_3v3_noweapon_s2
  3   0     -5.43    -1.81     4.250    0.472      10.60    3.53  scaling_3v3_noweapon_s3
  3   1     -5.42    -1.81     5.629    0.625      11.67    3.89  scaling_3v3_noweapon_s3
  3   2     -4.93    -1.64     5.474    0.608      11.56    3.85  scaling_3v3_noweapon_s3
  3   3     -4.98    -1.66     5.186    0.576      12.15    4.05  scaling_3v3_noweapon_s3
  3   4     -5.09    -1.70     5.335    0.593      12.21    4.07  scaling_3v3_noweapon_s3
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
  5   0     -9.01    -1.80    13.832    0.553      22.89    4.58  scaling_5v5_noweapon_s2
  5   1     -8.96    -1.79    16.788    0.672      22.72    4.54  scaling_5v5_noweapon_s2
  5   2     -8.88    -1.78    17.515    0.701      21.48    4.30  scaling_5v5_noweapon_s2
  5   3     -8.58    -1.72    17.144    0.686      21.25    4.25  scaling_5v5_noweapon_s2
  5   4     -8.60    -1.72    16.692    0.668      21.23    4.25  scaling_5v5_noweapon_s2
 10   0    -17.66    -1.77    63.838    0.638      61.57    6.16  scaling_10v10_noweapon
 10   1    -17.57    -1.76    72.391    0.724      46.94    4.69  scaling_10v10_noweapon
 10   2    -17.56    -1.76    73.277    0.733      46.92    4.69  scaling_10v10_noweapon
 10   3    -17.65    -1.76    70.535    0.705      47.18    4.72  scaling_10v10_noweapon
 10   4    -17.46    -1.75    69.102    0.691      47.23    4.72  scaling_10v10_noweapon
 10   0    -17.66    -1.77    65.518    0.655      67.87    6.79  scaling_10v10_noweapon_s1
 10   1    -17.80    -1.78    71.550    0.716      50.11    5.01  scaling_10v10_noweapon_s1
 10   2    -17.44    -1.74    71.266    0.713      49.21    4.92  scaling_10v10_noweapon_s1
 10   3    -17.80    -1.78    72.294    0.723      48.84    4.88  scaling_10v10_noweapon_s1
 10   4    -17.77    -1.78    71.622    0.716      50.05    5.00  scaling_10v10_noweapon_s1
 10   0    -17.68    -1.77    63.552    0.636      71.31    7.13  scaling_10v10_noweapon_s2
 10   1    -17.16    -1.72    70.073    0.701      49.05    4.90  scaling_10v10_noweapon_s2
 10   2    -16.98    -1.70    73.966    0.740      48.02    4.80  scaling_10v10_noweapon_s2
 10   3    -16.37    -1.64    74.678    0.747      47.93    4.79  scaling_10v10_noweapon_s2
 10   4    -16.25    -1.63    72.412    0.724      47.95    4.80  scaling_10v10_noweapon_s2

## D. 逐实验资源占用（峰值）

| 实验 | 进程数 | 峰值 CPU% | 峰值 CPU 核 | 峰值 RSS | GPU | 该 GPU 峰值显存 |
|---|---|---|---|---|---|---|
| `official_1v1_dodgemissile_selfplay` | 12 | 498% | 5.0 | 5.02 GB | 0 | 1371 MB |
| `official_1v1_hier_selfplay` | 12 | 459% | 4.6 | 5.02 GB | 0 | 1241 MB |
| `official_1v1_selfplay` | 12 | 346% | 3.5 | 4.77 GB | 0 | 1281 MB |
| `official_1v1_shoot_hier_selfplay` | 12 | 570% | 5.7 | 5.05 GB | 0 | 1513 MB |
| `official_1v1_vsbaseline` | 12 | 481% | 4.8 | 5.39 GB | 0 | 1433 MB |
| `official_2v2_noweapon` | 14 | 672% | 6.7 | 5.83 GB | 1 | 1405 MB |
| `official_2v2_noweapon_s1b` | 14 | 706% | 7.1 | 5.85 GB | 1 | 1749 MB |
| `official_2v2_noweapon_selfplay` | 10 | 416% | 4.2 | 4.20 GB | 0 | 1559 MB |
| `official_2v2_shoot` | 14 | 688% | 6.9 | 5.78 GB | 1 | 1343 MB |
| `official_heading` | 12 | 326% | 3.3 | 4.75 GB | 0 | 1559 MB |
| `scaling_10v10_noweapon` | 20 | 1218% | 12.2 | 13.83 GB | 2 | 994 MB |
| `scaling_10v10_noweapon_s1` | 20 | 1277% | 12.8 | 13.81 GB | 1 | 1749 MB |
| `scaling_2v2_noweapon` | 14 | 708% | 7.1 | 5.82 GB | 1 | 1477 MB |
| `scaling_2v2_noweapon_s1` | 12 | 594% | 5.9 | 5.11 GB | 1 | 1405 MB |
| `scaling_2v2_shoot` | 10 | 493% | 4.9 | 4.45 GB | 0 | 1433 MB |
| `scaling_3v3_noweapon` | 20 | 1025% | 10.2 | 8.12 GB | 2 | 900 MB |
| `scaling_3v3_noweapon_s1` | 12 | 620% | 6.2 | 5.21 GB | 1 | 1405 MB |
| `scaling_3v3_shoot` | 10 | 513% | 5.1 | 4.49 GB | 0 | 1267 MB |
| `scaling_5v5_noweapon` | 20 | 1192% | 11.9 | 8.81 GB | 2 | 902 MB |
| `scaling_5v5_noweapon_s1` | 12 | 661% | 6.6 | 5.60 GB | 1 | 1477 MB |
| `scaling_5v5_noweapon_s2` | 20 | 1074% | 10.7 | 8.81 GB | 2 | 902 MB |
| `scaling_5v5_shoot` | 10 | 558% | 5.6 | 4.84 GB | 0 | 1513 MB |

