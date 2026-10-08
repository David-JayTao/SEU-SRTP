# Formal-6M 自动结果 —— 机器生成的数值记录

> **本文件由机器生成，请勿手改。** 生成于 **2026-10-08 11:58:21 CST** （2026-10-08T11:58:21+08:00），由 `experiments/2026-10-07-08-formal6m/scripts/make_auto_results.py` 生成（repo HEAD `fa4c6e9`，分支 `exp/formal-6m-20261007`）。所有数字均来自机器产物。
>
> 实验批次：`experiments/2026-10-07-08-formal6m`。重新生成：`cd experiments/2026-10-07-08-formal6m && /root/miniconda3/envs/jsbsim/bin/python scripts/make_auto_results.py` （`scripts/freeze.sh` 也会调用它，tmux auto-finalizer 按计划运行 freeze.sh）。
>
> 下方每个数值都读取自 *数据来源与新鲜度* 一节列出的文件；没有任何手工填入的值，除某行明确说明外也不做任何外推。若手写报告最终未能完成，本文档就是完整的数值记录。

## 状态词表与预算规则

状态恰好为六个值之一，由本脚本按以下规则从 watcher 自身的标志（`metrics/status.json`）推导（与监控所用规则一致）：

| 状态 | 含义 |
|---|---|
| `completed_6M` | 跑满 6,000,000 预算。 |
| `completed_at_ceiling` | 到达自身可达上限，该上限低于 6,000,000（仅 3-thread 通道）。 |
| `running` | 仍在写入：日志在 watcher 的 30 分钟停滞阈值内更新。 |
| `time_cutoff` | 未达上限即停止，且无崩溃证据（挂钟时间上限，或日志静默 > 30 分钟）。 |
| `failed` | 观测到 Traceback / NaN / Inf。 |
| `not_applicable` | 该通道未找到任何数据。 |

runner 向下取整 `episodes = num_env_steps // 3000 // n_rollout_threads`（事件 F17），因此通道的可达上限为 `(6e6 // 3000 // threads) * 3000 * threads`。本实验批次实际出现的线程数对应的上限：

| threads | episodes | 可达上限 |
|---|---|---|
| 3 | 666 | 5,994,000 |
| 4 | 500 | 6,000,000 |
| 8 | 250 | 6,000,000 |
| 10 | 200 | 6,000,000 |
| 20 | 100 | 6,000,000 |

`reward_per_enemy`（reward / team_size）**仅**对 NoWeapon 系列是可跨 N 比较的量（PostureReward 对每个 agent 的敌机求和）。此处对 ShootMissile 系列一律不给出。

Pilot（2026-10-04）与 formal（6M）是两条独立序列，绝不合并。

## 数据来源与新鲜度

本文档中的每个数字都在生成时刻从这些机器产物读取。来源文件比表格更新，意味着表格只是快照而非实时状态；实时状态永远是下面的清单表（由 `metrics/status.json` 构建）。

| 来源 | 最近写入 |
|---|---|
| `manifest.csv` | 2026-10-08 09:20:32 |
| `metrics/status.json` | 2026-10-08 10:29:36 |
| `metrics/summary.csv` | 2026-10-08 09:21:31 |
| `metrics/scaling_table.csv` | 2026-10-08 09:21:31 |
| `metrics/critic_scaling.json` | 2026-10-08 09:20:37 |
| `metrics/equal_sample.csv` | 2026-10-08 09:20:39 |
| `metrics/equal_wallclock.csv` | 2026-10-08 09:20:39 |
| `status/incidents.md` | 2026-10-08 11:52:13 |

## 实验清单（所有通道）

来自 `metrics/status.json` 的实时视图（时间戳 2026-10-08 10:29:33；本文件生成前 88.8 分钟）。
**警告**：watcher 快照已过期 89 分钟 —— 下方的存活标志可能已过时。

| 实验 | 场景 | 算法 | 种子 | threads | 可达上限 | 步数 | % 上限 | 状态 | FPS | 挂钟时间 | 标志 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `f6m_2v2_noweapon_s0` | 2v2/scaling_noweapon/HierarchySelfplay | mappo | 0 | 4 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 77 | 21.5 h | — |
| `f6m_3v3_noweapon_s0` | 3v3/scaling_noweapon/HierarchySelfplay | mappo | 0 | 8 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 125 | 13.3 h | — |
| `f6m_3v3_noweapon_s1` | 3v3/scaling_noweapon/HierarchySelfplay | mappo | 1 | 8 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 124 | 13.4 h | — |
| `f6m_5v5_noweapon_s0` | 5v5/scaling_noweapon/HierarchySelfplay | mappo | 0 | 8 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 79 | 20.9 h | — |
| `f6m_5v5_noweapon_s1` | 5v5/scaling_noweapon/HierarchySelfplay | mappo | 1 | 10 | 6,000,000 | 5,820,000 | 97.0% | `running` | 94 | 17.1 h | — |
| `f6m_5v5_noweapon_s2` | 5v5/scaling_noweapon/HierarchySelfplay | mappo | 2 | 8 | 6,000,000 | 2,376,000 | 39.6% | `time_cutoff` | 79 | 8.3 h | 被时间上限停掉（SIGINT 收尾回溯，非崩溃）; Traceback in log |
| `f6m_10v10_noweapon_s0` | 10v10/scaling_noweapon/HierarchySelfplay | mappo | 0 | 20 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 65 | 25.3 h | — |
| `f6m_10v10_noweapon_s1` | 10v10/scaling_noweapon/HierarchySelfplay | mappo | 1 | 20 | 6,000,000 | 1,920,000 | 32.0% | `time_cutoff` | 64 | 8.3 h | 被时间上限停掉（SIGINT 收尾回溯，非崩溃）; Traceback in log |
| `f6m_official_1v1_hier_selfplay_s1` | 1v1/NoWeapon/HierarchySelfplay | ppo | 1 | 3 | 5,994,000 | 5,994,000 | 100.0% | `completed_at_ceiling` | 83 | 20.0 h | — |
| `f6m_official_1v1_selfplay_s1` | 1v1/NoWeapon/Selfplay | ppo | 1 | 3 | 5,994,000 | 5,994,000 | 100.0% | `completed_at_ceiling` | 104 | 15.9 h | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1v1/ShootMissile/HierarchySelfplay | ppo | 1 | 3 | 5,994,000 | 5,994,000 | 100.0% | `completed_at_ceiling` | 61 | 27.0 h | — |
| `f6m_official_1v1_vsbaseline_s1` | 1v1/NoWeapon/vsBaseline | ppo | 1 | 3 | 5,994,000 | 5,994,000 | 100.0% | `completed_at_ceiling` | 122 | 13.6 h | — |
| `f6m_official_2v2_noweapon_s0` | 2v2/NoWeapon/HierarchySelfplay | mappo | 0 | 4 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 75 | 22.0 h | — |
| `f6m_official_heading_s5` | 1/heading | ppo | 5 | 4 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 275 | 6.1 h | — |

共 14 条通道合计：已完成 **76,092,000 env steps / 可达 83,976,000**（快照）；全批次实时聚合吞吐 **1427 env-steps/s**。

### Checkpoint

| 实验 | 最新 checkpoint | 状态 |
|---|---|---|
| `f6m_2v2_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/2v2/scaling_noweapon/HierarchySelfplay/mappo/f6m_2v2_noweapon_s0/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_3v3_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/3v3/scaling_noweapon/HierarchySelfplay/mappo/f6m_3v3_noweapon_s0/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_3v3_noweapon_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/3v3/scaling_noweapon/HierarchySelfplay/mappo/f6m_3v3_noweapon_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_5v5_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/5v5/scaling_noweapon/HierarchySelfplay/mappo/f6m_5v5_noweapon_s0/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_5v5_noweapon_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/5v5/scaling_noweapon/HierarchySelfplay/mappo/f6m_5v5_noweapon_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_5v5_noweapon_s2` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/5v5/scaling_noweapon/HierarchySelfplay/mappo/f6m_5v5_noweapon_s2/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_10v10_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_10v10_noweapon_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_1v1_hier_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/HierarchySelfplay/ppo/f6m_official_1v1_hier_selfplay_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_1v1_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/Selfplay/ppo/f6m_official_1v1_selfplay_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/ShootMissile/HierarchySelfplay/ppo/f6m_official_1v1_shoot_hier_selfplay_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_1v1_vsbaseline_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/vsBaseline/ppo/f6m_official_1v1_vsbaseline_s1/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_2v2_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/2v2/NoWeapon/HierarchySelfplay/mappo/f6m_official_2v2_noweapon_s0/run1/actor_latest.pt` | 已在磁盘上 |
| `f6m_official_heading_s5` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleControl/1/heading/ppo/f6m_official_heading_s5/run1/actor_latest.pt` | 已在磁盘上 |

## scaling 表（reward 与每敌机 reward）

快照：`metrics/scaling_table.csv`（写入于 2026-10-08 09:21:31）。`reward_per_enemy = train_reward_last / team_size`，在本脚本内计算，仅对 NoWeapon 系列输出。

| 规模 | 变体 | 种子 | thr | 步数（快照） | FPS | 训练 reward（最后） | 每敌机 reward | eval reward（最后） | 尾段斜率 |
|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 0 | 4 | 6,000,000 | 77 | 21.9924 | 10.9962 | -99.0258 | 0.0479 |
| 3v3 | noweapon | 0 | 8 | 6,000,000 | 125 | 35.9318 | 11.9773 | 47.8388 | 0.0089 |
| 3v3 | noweapon | 1 | 8 | 6,000,000 | 124 | 34.4728 | 11.4909 | 47.6476 | -0.0105 |
| 5v5 | noweapon | 0 | 8 | 6,000,000 | 79 | 39.7857 | 7.9571 | -222.7146 | 0.3652 |
| 5v5 | noweapon | 1 | 10 | 5,400,000 | 93 | 34.0185 | 6.8037 | -2.8143 | -0.4046 |
| 5v5 | noweapon | 2 | 8 | 2,304,000 | 79 | 7.9511 | 1.5902 | -58.1626 | 0.1439 |
| 10v10 | noweapon | 0 | 20 | 6,000,000 | 65 | 0.3918 | 0.0392 | -87.8638 | 0.3908 |
| 10v10 | noweapon | 1 | 20 | 1,860,000 | 64 | 3.2868 | 0.3287 | -30.8630 | 2.0756 |

按既定口径，任何 ShootMissile 行的 `reward_per_enemy` 一律显示为 `n/a`。官方基线通道不属于本表（它们是独立序列；见清单）。

## 等样本对比

固定 vectorised env-step 预算（1M–6M）下的 reward 与每敌机 reward，来自本批次自带的等样本生成器。

快照：`metrics/equal_sample.csv`（写入于 2026-10-08 09:20:39）。`—` = pending（该快照时尚未达到该预算）；`*` = 在相邻 update 之间插值；`†` = 首次跨过；`§` = before-data / nan-gap。逐格原始状态与区间见 CSV 本身。

**reward**

| 实验 | 种子 | 1M | 2M | 3M | 4M | 5M | 6M |
|---|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -17.2663* | -11.6991* | -10.6261 | -4.7305* | -0.5542* | 0.3918 |
| `f6m_10v10_noweapon_s1` | 1 | -11.6634* | — | — | — | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 23.7545* | 24.3933* | 16.3153 | 19.9296* | 15.8947* | 21.9924 |
| `f6m_3v3_noweapon_s0` | 0 | 31.7989* | 35.3119* | 36.0622 | 35.7911* | 36.0737* | 35.9318 |
| `f6m_3v3_noweapon_s1` | 1 | 25.9371* | 32.5543* | 35.0528 | 36.899* | 36.7437* | 34.4728 |
| `f6m_5v5_noweapon_s0` | 0 | -1.6399* | 48.8016* | 50.3039 | 23.136* | 24.4286* | 39.7857 |
| `f6m_5v5_noweapon_s1` | 1 | 4.4416* | 16.2785* | 55.8344 | 14.0141* | 51.7336* | — |
| `f6m_5v5_noweapon_s2` | 2 | -5.9702* | 9.0304* | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 20.8747* | 33.1314* | -104.0363* | -8.0676* | -73.7012* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -64.9082* | 4.9369* | 25.578* | 13.1161* | 30.3252* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | -17.9232* | -68.9111* | -29.3841* | -18.6212* | -14.153* | — |
| `f6m_official_1v1_vsbaseline_s1` | 1 | 11.2948* | 12.0699* | 23.5194* | 26.4511* | 29.8232* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | 15.1427* | 21.6233* | 23.1315 | 22.4214* | 21.308* | 23.1285 |

**每敌机 reward（reward / team_size；仅 NoWeapon 系列 —— ShootMissile 为 `n/a`）**

| 实验 | 种子 | 1M | 2M | 3M | 4M | 5M | 6M |
|---|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -1.7266* | -1.1699* | -1.0626 | -0.4731* | -0.0554* | 0.0392 |
| `f6m_10v10_noweapon_s1` | 1 | -1.1663* | — | — | — | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 11.8772* | 12.1967* | 8.1576 | 9.9648* | 7.9474* | 10.9962 |
| `f6m_3v3_noweapon_s0` | 0 | 10.5996* | 11.7706* | 12.0207 | 11.9304* | 12.0246* | 11.9773 |
| `f6m_3v3_noweapon_s1` | 1 | 8.6457* | 10.8514* | 11.6843 | 12.2997* | 12.2479* | 11.4909 |
| `f6m_5v5_noweapon_s0` | 0 | -0.328* | 9.7603* | 10.0608 | 4.6272* | 4.8857* | 7.9571 |
| `f6m_5v5_noweapon_s1` | 1 | 0.8883* | 3.2557* | 11.1669 | 2.8028* | 10.3467* | — |
| `f6m_5v5_noweapon_s2` | 2 | -1.194* | 1.8061* | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 20.8747* | 33.1314* | -104.0363* | -8.0676* | -73.7012* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -64.9082* | 4.9369* | 25.578* | 13.1161* | 30.3252* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | n/a | n/a | n/a | n/a | n/a | n/a |
| `f6m_official_1v1_vsbaseline_s1` | 1 | 11.2948* | 12.0699* | 23.5194* | 26.4511* | 29.8232* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | 7.5713* | 10.8116* | 11.5658 | 11.2107* | 10.654* | 11.5642 |

## 等挂钟时间对比

固定挂钟时间预算（1h–24h）下的 reward 与每敌机 reward，来自本批次自带的等挂钟时间生成器。

快照：`metrics/equal_wallclock.csv`（写入于 2026-10-08 09:20:39）。`—` = pending（该快照时尚未达到该预算）；`*` = 在相邻 update 之间插值；`†` = 首次跨过；`§` = before-data / nan-gap。逐格原始状态与区间见 CSV 本身。

**reward**

| 实验 | 种子 | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -17.4795* | -17.2337* | -16.7635* | -2.6125* | 17.2993* |
| `f6m_10v10_noweapon_s1` | 1 | -17.7188* | -15.8033* | -6.0021* | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 4.319* | 22.78* | 21.2265* | 11.7387* | — |
| `f6m_3v3_noweapon_s0` | 0 | -1.2008* | 35.4391* | 35.5665* | 35.8465* | — |
| `f6m_3v3_noweapon_s1` | 1 | -0.0385* | 36.2703* | 34.0847* | 29.6497* | — |
| `f6m_5v5_noweapon_s0` | 0 | -7.7217* | -4.2391* | -4.0284* | 27.2418* | — |
| `f6m_5v5_noweapon_s1` | 1 | -5.6468* | 0.1679* | 16.3989* | 14.7439* | — |
| `f6m_5v5_noweapon_s2` | 2 | -8.717* | -3.4745* | 1.7509* | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 23.5967* | 32.6657* | 18.727* | -10.5172* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -156.7427* | -20.3149* | 36.3616* | 29.1071* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | -18.116* | -26.653* | -60.9307* | -12.2356* | -5.509* |
| `f6m_official_1v1_vsbaseline_s1` | 1 | -8.6019* | 6.8271* | 12.3685* | 29.2324* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | -0.5935* | 18.718* | 20.9977* | 17.1295* | — |

**每敌机 reward（reward / team_size；仅 NoWeapon 系列 —— ShootMissile 为 `n/a`）**

| 实验 | 种子 | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -1.7479* | -1.7234* | -1.6764* | -0.2613* | 1.7299* |
| `f6m_10v10_noweapon_s1` | 1 | -1.7719* | -1.5803* | -0.6002* | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 2.1595* | 11.39* | 10.6132* | 5.8694* | — |
| `f6m_3v3_noweapon_s0` | 0 | -0.4003* | 11.813* | 11.8555* | 11.9488* | — |
| `f6m_3v3_noweapon_s1` | 1 | -0.0128* | 12.0901* | 11.3616* | 9.8832* | — |
| `f6m_5v5_noweapon_s0` | 0 | -1.5443* | -0.8478* | -0.8057* | 5.4484* | — |
| `f6m_5v5_noweapon_s1` | 1 | -1.1294* | 0.0336* | 3.2798* | 2.9488* | — |
| `f6m_5v5_noweapon_s2` | 2 | -1.7434* | -0.6949* | 0.3502* | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 23.5967* | 32.6657* | 18.727* | -10.5172* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -156.7427* | -20.3149* | 36.3616* | 29.1071* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | n/a | n/a | n/a | n/a | n/a |
| `f6m_official_1v1_vsbaseline_s1` | 1 | -8.6019* | 6.8271* | 12.3685* | 29.2324* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | -0.2967* | 9.359* | 10.4988* | 8.5647* | — |

## 表征 / critic scaling（实测 vs 外推）

来源：`metrics/critic_scaling.json`（写入于 2026-10-08 09:20:37）；probe = 在真实网络上构建模型，不做训练。三张表绝不混用：(1) 四个实测点，(2) 由这些实测值推导的量，(3) 超出实测范围的预测。

### 1. 实测行（N = 2, 3, 5, 10）

| N | agents | obs 维度 | share obs 维度 | actor 参数量 | critic 参数量 | critic 首层参数量 | 首层 MAC/envstep | fwd ms（batch） | fwd ms（固定 256） | bwd ms（固定 256） | fwd µs/样本 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 154,891 | 163,969 | 13,952 | 331,776 | 0.328 | 0.3396 | 6.1962 | 1.3260 |
| 3 | 6 | 39 | 234 | 156,427 | 180,097 | 30,080 | 1,078,272 | 0.572 | 0.9866 | 6.1374 | 3.8540 |
| 5 | 10 | 63 | 630 | 159,499 | 230,785 | 80,768 | 4,838,400 | 0.456 | 0.9931 | 6.3363 | 3.8790 |
| 10 | 20 | 123 | 2460 | 167,179 | 465,025 | 315,008 | 37,785,600 | 0.454 | 0.9697 | 6.1432 | 3.7880 |

### 2. 由实测点推导（不是新的测量）

由同样的 N = 2, 3, 5, 10 的 probe 运行计算得到；此处的首层数值与表 1 完全相同，并在下方核对。不要把这本表当作独立证据。

| N | agents | obs 维度 | share obs 维度 | critic 首层参数量 | 首层 MAC/envstep | 估计 fwd ms/envstep | share-obs 缓冲区 GB |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 13,952 | 331,776 | 0.0040 | 0.029 |
| 3 | 6 | 39 | 234 | 30,080 | 1,078,272 | 0.0130 | 0.094 |
| 5 | 10 | 63 | 630 | 80,768 | 4,838,400 | 0.0582 | 0.423 |
| 10 | 20 | 123 | 2460 | 315,008 | 37,785,600 | 0.4545 | 3.3 |


### 3. 超出实测范围的外推（仅为预测）

N = 20, 50, 100 从未被实测（probe 只构建了上面四个网络）。这些行是基于模型的预测，绝不能与实测混用 —— 也不能当作实测引用。

| N | agents | obs 维度 | share obs 维度 | critic 首层参数量 | 首层 MAC/envstep | 估计 fwd ms/envstep | share-obs 缓冲区 GB |
|---|---|---|---|---|---|---|---|
| 20 | 40 | 243 | 9720 | 1,244,288 | 298,598,400 | 3.5920 | 26.08 |
| 50 | 100 | 603 | 60300 | 7,718,528 | 4,631,040,000 | 55.7097 | 404.478 |
| 100 | 200 | 1203 | 240600 | 30,796,928 | 36,956,160,000 | 444.5690 | 3227.773 |

### 解析式核对（在本脚本中计算，非断言）

每行：`share_obs = 24N² + 6N`，`critic_params = 128·(24N²+6N) + 150145`，`critic_first_layer_params = 128·(share_obs + 1)`。

| 量 | 记录值 | 解析式 | 是否一致 |
|---|---|---|---|
| N=2 share_obs_dim | 108 | 108 | 一致 |
| N=2 critic_params | 163,969 | 163,969 | 一致 |
| N=2 critic_first_layer | 13,952 | 13,952 | 一致 |
| N=3 share_obs_dim | 234 | 234 | 一致 |
| N=3 critic_params | 180,097 | 180,097 | 一致 |
| N=3 critic_first_layer | 30,080 | 30,080 | 一致 |
| N=5 share_obs_dim | 630 | 630 | 一致 |
| N=5 critic_params | 230,785 | 230,785 | 一致 |
| N=5 critic_first_layer | 80,768 | 80,768 | 一致 |
| N=10 share_obs_dim | 2,460 | 2,460 | 一致 |
| N=10 critic_params | 465,025 | 465,025 | 一致 |
| N=10 critic_first_layer | 315,008 | 315,008 | 一致 |
| N=20 share_obs_dim (extrapolated) | 9,720 | 9,720 | 一致 |
| N=20 critic_first_layer (extrapolated) | 1,244,288 | 1,244,288 | 一致 |
| N=50 share_obs_dim (extrapolated) | 60,300 | 60,300 | 一致 |
| N=50 critic_first_layer (extrapolated) | 7,718,528 | 7,718,528 | 一致 |
| N=100 share_obs_dim (extrapolated) | 240,600 | 240,600 | 一致 |
| N=100 critic_first_layer (extrapolated) | 30,796,928 | 30,796,928 | 一致 |

全部解析式核对通过：**是**。Probe 元数据：device `cuda:0`，effective G-MAC/s 83.13，batch threads 12。

## 计算可扩展性

快照：`metrics/scaling_table.csv`（写入于 2026-10-08 09:21:31）。`FPS` 为 runner 自身的 vectorised env-steps/s；`agent-steps/s = env-steps/s × 总 agent 数`。

| 规模 | 变体 | thr | FPS（env-steps/s） | 每线程 env-steps/s | agent-steps/s | 每线程 agent-steps/s | 秒 / vectorised step | 秒 / rollout episode（3000 步） |
|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 77 | 19.25 | 308 | 77 | 0.05195 | 155.8 |
| 3v3 | noweapon | 8 | 125 | 15.62 | 750 | 93.8 | 0.064 | 192.0 |
| 3v3 | noweapon | 8 | 124 | 15.50 | 744 | 93 | 0.06452 | 193.5 |
| 5v5 | noweapon | 8 | 79 | 9.88 | 790 | 98.8 | 0.10127 | 303.8 |
| 5v5 | noweapon | 10 | 93 | 9.30 | 930 | 93 | 0.10753 | 322.6 |
| 5v5 | noweapon | 8 | 79 | 9.88 | 790 | 98.8 | 0.10127 | 303.8 |
| 10v10 | noweapon | 20 | 65 | 3.25 | 1300 | 65 | 0.30769 | 923.1 |
| 10v10 | noweapon | 20 | 64 | 3.20 | 1280 | 64 | 0.3125 | 937.5 |

`metrics/status.json` 快照时全批次实时聚合吞吐：全部活跃通道合计 **1427 env-steps/s**。

## 失败清单（摘自 `status/incidents.md`）

本实验批次共记录 9 起事件 （?: 9）。F1–F9 位于 `docs/night_failures.md`，属于 2026-10-04 pilot；此处不再重复列出。

| id | 标题 | 类别 | 发现时间 | 摘要（症状/原因节选） |
|---|---|---|---|---|
| F10 | CPU 核数列报告了一个物理上不可能的值 |  |  |  |
| F11 | 表示可扩展性（Representational-scalability）的各列静默为空 |  |  |  |
| F12 | 已完成的通道被报告为仍在运行 |  |  |  |
| F13 | 分析脚本硬编码了 pilot 的实验路径 |  |  |  |
| F17 | 可达到的步数预算被线程数量化 |  |  |  |
| F16 | `/proc/stat` 在这个容器里不可用；由它推导的每一个 CPU 数字都是错的 |  |  |  |
| F15 | 探针的 `--out` 相对仓库根目录解析，而不是调用时的 cwd |  |  |  |
| F14 | `1v1` ShootMissile 通道在结构上慢约 2×，并且将错过 6M |  |  |  |
| F18 | `offline_eval.py` 的默认对手是 NULL 策略，所以它的默认数字毫无意义 |  |  |  |

本快照的实时健康标志：NaN ×0，Inf ×0，traceback ×2；状态为 `failed` 的通道：0 条。

## 本文档不展示的内容

已知局限；引用上面任何数字之前请先阅读本节。

1. **大多数规模只有一个种子。** 目前只有下列场景拥有多于一个种子；其余场景均为单种子结果。小于运行间种子离散度的跨规模（或跨种子）差异不可解释，本文档也不做这类比较。
   - 目前多种子：`10v10/scaling_noweapon/HierarchySelfplay`, `3v3/scaling_noweapon/HierarchySelfplay`, `5v5/scaling_noweapon/HierarchySelfplay`
   - 本次生成时为单种子：`1/heading`, `1v1/NoWeapon/HierarchySelfplay`, `1v1/NoWeapon/Selfplay`, `1v1/NoWeapon/vsBaseline`, `1v1/ShootMissile/HierarchySelfplay`, `2v2/NoWeapon/HierarchySelfplay`, `2v2/scaling_noweapon/HierarchySelfplay`

2. **`n_rollout_threads` 是混淆因素，不是细节。** 线程数在各规模间不同（受挂钟时间所迫：固定线程数时 10v10 无法在窗口内到达 6M），且 PPO update 的 batch 大小为 `threads × 3000`，因此 batch 大小也随规模不同。
   - 本次生成时各场景的线程数：`1/heading`: [4] thr（batch [12000]）, `10v10/scaling_noweapon/HierarchySelfplay`: [20] thr（batch [60000]）, `1v1/NoWeapon/HierarchySelfplay`: [3] thr（batch [9000]）, `1v1/NoWeapon/Selfplay`: [3] thr（batch [9000]）, `1v1/NoWeapon/vsBaseline`: [3] thr（batch [9000]）, `1v1/ShootMissile/HierarchySelfplay`: [3] thr（batch [9000]）, `2v2/NoWeapon/HierarchySelfplay`: [4] thr（batch [12000]）, `2v2/scaling_noweapon/HierarchySelfplay`: [4] thr（batch [12000]）, `3v3/scaling_noweapon/HierarchySelfplay`: [8] thr（batch [24000]）, `5v5/scaling_noweapon/HierarchySelfplay`: [8, 10] thr（batch [24000, 30000]）
   - **同场景内跨种子的差异**：`5v5/scaling_noweapon/HierarchySelfplay` —— 该处的种子比较同样被线程数混淆。

3. **1v1 通道按构造无法到达 6,000,000。** 3-thread 通道向下取整到 666 个 episode，即名义 6,000,000 中的 5,994,000（事件 F17）。这些通道记为 `completed_at_ceiling`，而不是被截断。
   - 本次生成时受影响的通道：`f6m_official_1v1_hier_selfplay_s1`, `f6m_official_1v1_selfplay_s1`, `f6m_official_1v1_shoot_hier_selfplay_s1`, `f6m_official_1v1_vsbaseline_s1`

4. **1v1 ShootMissile 通道带 `--use-prior` 运行，吞吐约减半**（事件 F14，类别 `Computational scalability` —— 不是算法问题）。其较低的 FPS 是官方代码路径的性质，不是算法发现。
   - 当前 FPS：ShootMissile 61，同类 3-thread 1v1 通道为 104, 122, 83 env-steps/s（见清单）。

5. **6M 是预算缩减，不是收敛结果。** 官方配置训练 1e8 步；本批次只跑 6,000,000（为其 6%）。最终 reward 是训练中途状态的快照，绝不能当作已收敛的性能来呈现。

另外，按既定口径：

- `reward_per_enemy` 只对 NoWeapon 系列有定义（PostureReward 对 agent 求和）；ShootMissile 行一律不给出。
- 2026-10-04 pilot 是独立序列，不包含在本文档中。
- 由分析 CSV 构建的表格只是那些文件的快照（mtime 见上）；只有清单是实时视图。本文档不做跨种子平均、拟合或显著性检验。
- 本文档是数据记录，不是分析；请结合手写报告解读。

## 相关产物（未内嵌到本文档）

- `metrics/scaling_table.csv` —— 上表 scaling 表的机器可读版本，列更全（obs 维度、参数量、CPU/RAM 峰值）。
- `metrics/normalized_scaling.csv` —— scaling 系列的逐 episode reward 与每敌机 reward。
- `metrics/sample_efficiency.csv` —— 至 6M 各固定预算下的 reward / 每敌机 reward。
- `metrics/equal_sample.csv`、`metrics/equal_wallclock.csv` —— 带逐格状态与区间的原始 checkpoint 表。
- `metrics/resources.csv`、`metrics/throughput_history.csv`、`system/system_samples_v2.csv` —— 资源/吞吐时间序列（v1 采样文件的 CPU 换算不可靠；见事件 F16）。
- `figures/` —— 由 `scripts/make_figures.py` 重新生成的图。
- `docs/formal_repro_scaling_2026-10-07_08.md` —— 本文档作为其安全网的手写报告。

