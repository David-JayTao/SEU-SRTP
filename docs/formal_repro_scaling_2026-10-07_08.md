# SRTP 6M Formal Reproduction & Scaling Report

负责人：刘酝潇
实验窗口：2026-10-07 02:54 CST → 2026-10-08 10:00 CST
分支：`exp/formal-6m-20261007`
工作区：`experiments/2026-10-07-08-formal6m/`

> **Status: IN PROGRESS.** This document is updated continuously while the runs
> are still training. Numbers marked `TBD` are not yet available. Nothing in
> this report is extrapolated from the §3 pilot runs to stand in for a formal
> number; where a formal number does not exist yet, the cell says so.
>
> Sections §5–§8, §11, §12 and §17 are data-derived and are regenerated in
> place by `experiments/2026-10-07-08-formal6m/scripts/fill_report.py`, which
> rewrites exactly the region between the `<!-- AUTO:sectionN -->` /
> `<!-- /AUTO:sectionN -->` marker pair in each of those sections. Do not hand-
> edit inside a marker pair — edit the generator or the CSVs it reads. The
> remaining sections are written by hand and are never touched by the generator.

---

## 1. 实验目标

本轮的目标不是"把官方实验跑满"，而是在约 **31 小时**的有限 wall-clock 预算内，
最大化 **科研信息量 / 计算成本**，产出一套可复现、口径统一的数据体系：

1. **实验线 A — 官方 baseline 的 6M formal reproduction。**
   对仓库中**真实存在**的官方入口，在保持全部官方超参数不变的前提下，
   把训练预算从 `1e8` 降到 `6e6`，得到一条比 §3 的 ~1M pilot 可信得多的学习曲线。
2. **实验线 B — N-v-N scalability。** 对 N ∈ {2,3,5,10} 的 NoWeapon
   任务，在**同一个 6M environment-step 预算**下训练，得到一条 vanilla
   baseline scaling curve。
3. **关键 second seed**，用于把"单 seed 的趋势"升级为"可分离噪声的观察"。
4. **两条比较轴**：equal-sample（相同 env steps）与 equal-wall-clock（相同小时数）。
   因为 10v10 的计算开销本身就是 scalability 问题的一部分。

**本轮明确不做**：不实现 Graph/Attention/Hypergraph/World-Model/Locality-MAPPO，
不修改 reward / 网络 / 超参数，不做 observation 性能优化（见 §4.4）。

---

## 2. 服务器与软件环境

| 项目 | 值 |
|---|---|
| GPU | 3 × NVIDIA GeForce RTX 4090 D (24 GB each) |
| Driver / CUDA | 595.71.05 / CUDA 13.2 |
| CPU | 48 core quota（cgroup `cpu.max = 4800000 100000`），宿主 192 逻辑核 |
| RAM | 1007 GB total |
| 磁盘 | `/dev/md0` 50 GB，`scripts/results/` 本次实验前占 440 MB |
| conda env | `jsbsim` — Python 3.12.3, torch 2.8.0+cu128 |
| OS | Linux 5.15.0-94-generic |
| 仓库 | `David-JayTao/SEU-SRTP`, branch `exp/formal-6m-20261007` |

**已确认的调度事实**：本机 GPU 显存占用 ~0.5 GB/job、GPU 利用率 0–6%，
**瓶颈完全在 CPU 侧的环境仿真**（与 `docs/night_failures.md` F8 的诊断一致）。
因此本轮的调度目标不是"填满 GPU"，而是
**最大化 aggregate useful env-steps/s**，并把 rollout worker 总量控制在 44–46
（48 核配额中为 OS / learner / logging / 分析保留 2–4 核）。

---

## 3. Previous Pilot Summary

2026-10-04 的一次通宵实验（`experiments/2026-10-04-night/`、
`docs/overnight_repro_scaling_2026-10-04.md`、`docs/night_failures.md`）建立了
本次实验的全部基础设施与大部分诊断，但它**不是**正式的 6M 实验：

| 性质 | 2026-10-04 pilot | 本轮 formal |
|---|---|---|
| 预算 | `1e8` 计划 + 4200–10800 s **wall-clock 上限轮转** | 6e6，跑到预算结束 |
| 实际完成 | 全部 ≤ **1.48M** steps（多为 0.65–0.9M） | target 6M |
| 中断 | 被 `timeout` 主动 SIGINT | 无 wall-clock 上限（仅 108000 s 兜底） |
| 语义 | 可复现，但被截断 | 完整 |

**因此 pilot 的曲线一律不与 formal 曲线混画**（见 §5 图例）。

pilot 已经确立、本轮直接继承的事实：

- **F8 瓶颈定位**：10v10 时 18 个 rollout worker 全部 `state=R` 各 ~0.72 核，
  主进程 `state=S` 仅 0.11 核 —— 瓶颈是 CPU 侧环境仿真，**不是** PPO 更新、
  **不是** GPU、**不是**算法。观测构造 `get_obs()` 对每个 agent 遍历全部
  partner+enemy，`BaseEnv.get_state()` 又对全部 2N 个 agent 各调用一次
  `get_obs`，使每步观测构造为 **O(N²) 且做两遍**。
- **F9**：`1v1/ShootMissile/HierarchyVsBaseline` 是 upstream 真实 bug，
  第一个 env step 即 `TypeError: 'NoneType' object is not subscriptable`，
  **零步完成**。不能用它作为 baseline。
- **F5**：生成的 scaling 配置曾把 shoot 变体覆盖 noweapon 变体，
  已修复为 `scaling_noweapon/` 与 `scaling_shoot/` 分目录。
- **"FSP" 不是 FSP**（`docs/baseline_inventory.md` §1.2b）：
  `algorithms/utils/selfplay.py` 的 `FSP.choose` 是对全部历史 checkpoint 的
  **均匀随机采样**，`update()` 是空函数，ELO 从不更新。
  本报告中一律称 **"MAPPO + uniform-random self-play over checkpoint history"**。
- **吞吐基准**（`metrics/env_bench_scaling.json`，单核，随机动作）：
  2v2 107.8 / 3v3 60.3 / 5v5 25.4 / 10v10 7.8 env-steps/s。

---

## 4. Formal Experiment Protocol

### 4.1 为什么是 6M

- 比 ~1M pilot 深 6 倍，足以观察**较可信的 learning trend**；
- 仍远低于官方 `1e8` full budget，**不能**声称达到官方完整收敛；
- 在本机的实测吞吐下（§5），6M 是唯一能在 31 小时窗口内让
  **四个规模 + 官方 baseline** 同时跑完的量级。

**报告中一律使用 "6M-budget formal reproduction / scaling characterization"，
不使用 "full 100M convergence reproduction"。**

### 4.2 6M 的口径（已用代码核实）

`--num-env-steps 6e6` 指 **vectorised environment steps**，**不乘 agent 数**。
核实方式：runner 自己打印的 `total_num_steps` 每轮增加
`n_rollout_threads × buffer_size`（buffer_size 固定为官方值 3000）。

| 规模 | n_rollout_threads | steps / update | 到 6M 的 updates |
|---|---|---|---|
| 2v2 | 4 | 12,000 | 500 |
| 3v3 | 8 | 24,000 | 250 |
| 5v5 | 8 | 24,000 | 250 |
| 10v10 | 20 | 60,000 | 100 |
| official 2v2 | 4 | 12,000 | 500 |

（实测日志样例：`updates 0/500 episodes, total num timesteps 12000/6000000, FPS 86.`）

### 4.3 运行级参数与算法参数的分离

**保持官方不变**（`experiments/2026-10-07-08-formal6m/scripts/run_train.sh` 逐字复刻
官方 `scripts/*.sh`）：

```
--n-training-threads 1   --num-mini-batch 5   --buffer-size 3000
--lr 3e-4  --gamma 0.99  --ppo-epoch 4  --clip-param 0.2  --max-grad-norm 2
--entropy-coef 1e-3  --hidden-size "128 128"  --act-hidden-size "128 128"
--recurrent-hidden-size 128  --recurrent-hidden-layers 1  --data-chunk-length 8
self-play: --use-selfplay --selfplay-algorithm fsp --n-choose-opponents 1
```

**只改动运行级参数**：`num_env_steps` 1e8 → 6e6；`n_rollout_threads` 32 → {4,8,20}；
GPU 分配；logging；checkpoint 间隔（`--save-interval 1` 与官方一致）。

**两个已记录的兼容性偏差**（均不改变算法语义，沿用 pilot 的既有处理）：

1. 去掉 `--use-wandb`（服务器无 W&B 账号/网络）。此时走官方代码里**本就存在**的非
   wandb 分支，checkpoint 落到 `scripts/results/...`。
2. 官方 `.sh` 传 `--clip-params 0.2`（拼写错误，`config.py` 真名是 `--clip-param`），
   `train_jsbsim.py` 用 `parse_known_args` 静默忽略 → 实际生效的是默认值 0.2。
   我们显式传 `--clip-param 0.2`，**数值完全相同**。

### 4.4 不在正式主实验中做的事

- **不改算法**（reward / network / hidden size / lr / gamma / entropy / clip /
  PPO epochs / self-play 算法 / observation 语义 / action 语义）。
- **不做环境性能优化**。`get_state()` 的双遍 O(N²) 观测构造是已知的工程瓶颈
  （pilot F8），但在正式 6M 序列跑完后突然优化会让优化前后的数据无法混在
  同一张正式曲线上。若将来采用，必须开 `engineering_speedup_*` 独立实验并
  逐项验证 obs/reward/done/transition 一致。

### 4.5 必须披露的 confound

**`n_rollout_threads` 在规模之间不同**（2v2=4, 3v3=8, 5v5=8, 10v10=20）。
这是 wall-clock 强制的：若固定线程数，10v10 无法在窗口内到达 6M。
后果是 **PPO update 的 batch 大小随 N 变化**（12k / 24k / 24k / 60k 样本）。
这是一个**真实的跨 N confound**，在 §6 的结论中必须附带此保留。
它**在同一 N 的不同 seed 之间是常数**，所以 seed-variance 与同 N 比较不受影响。

### 4.6 官方 baseline 的 L1 / L2 口径

沿用 `docs/baseline_inventory.md` §0 的三层定义，**严禁把 L3 自造实验包装成官方**：

- **L1**（有官方 `.sh`）：`1/heading`、`1v1/NoWeapon/vsBaseline`、
  `1v1/NoWeapon/Selfplay`、`1v1/ShootMissile/HierarchySelfplay`、
  `2v2/NoWeapon/HierarchySelfplay`。
- **L2**（官方 YAML + 官方 task 分支，但无官方 `.sh`）：
  `1v1/NoWeapon/HierarchySelfplay`、`2v2/ShootMissile/HierarchySelfplay`、
  全部 `DodgeMissile` 变体。
- **L3**（不存在，本轮若跑必须标注为自造）：所有 N≥3 的 `NvN/scaling_*`。

---

## 5. Official Baseline Reproduction

<!-- AUTO:section5 -->
Official baseline lanes of this campaign. `Status` uses the campaign vocabulary (see the notes below); `Wall time` is the run's own start to its last log write (running lanes: to generation time).

| Experiment | Seed | Steps | Wall time | FPS | Initial reward | Final reward | Eval | Status | Checkpoint |
|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 4,608,000 | 15.41 h | 83 | -69.367 | -211.43 | -225.14 | running | actor_latest.pt |
| f6m_official_1v1_selfplay_s1 | 1 | 5,832,000 | 15.54 h | 104 | -156.44 | 33.921 | 37.937 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 3,393,000 | 15.41 h | 61 | -192.88 | -21.311 | -0.21357 | running | actor_latest.pt |
| f6m_official_1v1_vsbaseline_s1 | 1 | 5,994,000 | 13.59 h | 122 | -207.14 | 27.785 | - | completed_at_ceiling | actor_latest.pt |
| f6m_official_2v2_noweapon_s0 | 0 | 4,272,000 | 15.80 h | 75 | -3.5066 | 23.647 | 31.693 | running | actor_latest.pt |
| f6m_official_1v1_shoot_hier_vsbaseline | - | - | - | - | - | - | - | not_applicable | - |

_3-thread lanes (`f6m_official_1v1_*`) stop at **5,994,000** of the 6,000,000-step target: the runner floors `episodes = 6e6//3000//threads` = 666, and 666 x 9,000 = 5,994,000. That is `completed_at_ceiling` (completion at the lane's own reachable budget), never a cutoff — see §17._

_`f6m_official_1v1_shoot_hier_vsbaseline` is the F9 entry: it dies at the first env step upstream and was deliberately never launched._
<!-- /AUTO:section5 -->

## 6. N-v-N Formal Scaling

<!-- AUTO:section6 -->
N-v-N formal scaling table, one row per (scale, seed). `Reward normalized` = final training reward / N — valid for the NoWeapon family only (PostureReward sums over the N enemies), never for ShootMissile.

| Scale | Agents | Seed | Steps | FPS | Wall time | Reward raw | Reward normalized | Value loss | Critic grad | CPU | RAM | VRAM | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | 4 | 0 | 4,392,000 | 77 | 15.80 h | 22.687 | 11.344 | 0.35289 | 5.3512 | 2.9 | 2.97 GB | 536 MB | running |
| 3v3 | 6 | 0 | 6,000,000 | 125 | 13.29 h | 35.932 | 11.977 | 0.17833 | 7.3129 | 5.5 | 4.61 GB | 650 MB | completed_6M |
| 3v3 | 6 | 1 | 504,000 | 116 | 1.29 h | 0.27721 | 0.092404 | 4.332 | 11.065 | 5.3 | 4.48 GB | 650 MB | running |
| 5v5 | 10 | 0 | 4,536,000 | 80 | 15.80 h | -37.881 | -7.5761 | 4.3817 | 59.158 | 6.1 | 4.85 GB | 658 MB | running |
| 5v5 | 10 | 1 | 360,000 | 82 | 1.37 h | -7.5252 | -1.505 | 16.565 | 22.266 | 6.8 | 5.59 GB | 712 MB | running |
| 10v10 | 20 | 0 | 3,780,000 | 67 | 15.80 h | 1.3063 | 0.13063 | 16.302 | 42.851 | 16.0 | 15.19 GB | 1036 MB | running |

_Wall time = run start to last log write (running rows: to generation time); Steps/FPS/rewards of a `running` row are live values at generation time. CPU/RAM/VRAM are this run's own process peaks from `metrics/resources.csv`; a cell marked `deg` fell back to the campaign-wide peak from `scaling_table.csv` because no per-lane sample exists yet. `n_rollout_threads` differs between scales (§4.5), so FPS is not cross-N comparable; `Reward normalized` and the per-agent view in §7/§11 are._
<!-- /AUTO:section6 -->

## 7. Equal-Sample Comparison

<!-- AUTO:section7 -->
Equal-sample comparison: mean training reward of each lane at matched vectorised-env-step budgets (1M..6M).

| Experiment | N | Seed | Threads | Steps reached | State | 1M | 2M | 3M | 4M | 5M | 6M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 1 | 3 | 4,347,000 | active | 20.875* | 33.131* | -104.04* | -8.0676* | pending | pending |
| f6m_official_1v1_selfplay_s1 | 1 | 1 | 3 | 5,517,000 | active | -64.908* | 4.9369* | 25.578* | 13.116* | 30.325* | pending |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 1 | 3 | 3,213,000 | active | -17.923* | -68.911* | -29.384* | pending | pending | pending |
| f6m_official_1v1_vsbaseline_s1 | 1 | 1 | 3 | 5,994,000 | idle | 11.295* | 12.07* | 23.519* | 26.451* | 29.823* | pending |
| f6m_2v2_noweapon_s0 | 2 | 0 | 4 | 4,164,000 | active | 23.755 (11.877)* | 24.393 (12.197)* | 16.315 (8.1576) | 19.93 (9.9648)* | pending | pending |
| f6m_official_2v2_noweapon_s0 | 2 | 0 | 4 | 4,056,000 | active | 15.143 (7.5713)* | 21.623 (10.812)* | 23.131 (11.566) | 22.421 (11.211)* | pending | pending |
| f6m_3v3_noweapon_s0 | 3 | 0 | 8 | 6,000,000 | complete | 31.799 (10.6)* | 35.312 (11.771)* | 36.062 (12.021) | 35.791 (11.93)* | 36.074 (12.025)* | 35.932 (11.977) |
| f6m_3v3_noweapon_s1 | 3 | 1 | 8 | 168,000 | active | pending | pending | pending | pending | pending | pending |
| f6m_5v5_noweapon_s0 | 5 | 0 | 8 | 4,320,000 | active | -1.6399 (-0.328)* | 48.802 (9.7603)* | 50.304 (10.061) | 23.136 (4.6272)* | pending | pending |
| f6m_5v5_noweapon_s1 | 5 | 1 | 10 | 150,000 | active | pending | pending | pending | pending | pending | pending |
| f6m_10v10_noweapon_s0 | 10 | 0 | 20 | 3,660,000 | active | -17.266 (-1.7266)* | -11.699 (-1.1699)* | -10.626 (-1.0626) | pending | pending | pending |

_Cells: `reward (reward per enemy)` for NoWeapon lanes; `*` = value interpolated between the two bracketing PPO updates; `pending` = the lane has not reached that budget yet (nothing is extrapolated); `before-data`/`nan-gap` are the raw provenance tokens. Raw per-cell brackets are in `metrics/equal_sample.csv`. Per-enemy values are only shown for NoWeapon; a ShootMissile reward is not a team sum._
<!-- /AUTO:section7 -->

## 8. Equal-Wall-Clock Comparison

<!-- AUTO:section8 -->
Equal-wall-clock comparison: mean training reward of each lane at matched elapsed-time budgets (1h..24h of its own run time).

| Experiment | N | Seed | Threads | Steps reached | State | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 1 | 3 | 4,347,000 | active | 23.597* | 32.666* | 18.727* | -10.517* | pending |
| f6m_official_1v1_selfplay_s1 | 1 | 1 | 3 | 5,517,000 | active | -156.74* | -20.315* | 36.362* | 29.107* | pending |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 1 | 3 | 3,213,000 | active | -18.116* | -26.653* | -60.931* | -12.236* | pending |
| f6m_official_1v1_vsbaseline_s1 | 1 | 1 | 3 | 5,994,000 | idle | -8.6019* | 6.8271* | 12.368* | 29.232* | pending |
| f6m_2v2_noweapon_s0 | 2 | 0 | 4 | 4,164,000 | active | 4.319 (2.1595)* | 22.78 (11.39)* | 21.227 (10.613)* | 11.739 (5.8694)* | pending |
| f6m_official_2v2_noweapon_s0 | 2 | 0 | 4 | 4,056,000 | active | -0.5935 (-0.2967)* | 18.718 (9.359)* | 20.998 (10.499)* | 17.13 (8.5647)* | pending |
| f6m_3v3_noweapon_s0 | 3 | 0 | 8 | 6,000,000 | complete | -1.2008 (-0.4003)* | 35.439 (11.813)* | 35.566 (11.855)* | 35.846 (11.949)* | pending |
| f6m_3v3_noweapon_s1 | 3 | 1 | 8 | 168,000 | active | pending | pending | pending | pending | pending |
| f6m_5v5_noweapon_s0 | 5 | 0 | 8 | 4,320,000 | active | -7.7217 (-1.5443)* | -4.2391 (-0.8478)* | -4.0284 (-0.8057)* | 27.242 (5.4484)* | pending |
| f6m_5v5_noweapon_s1 | 5 | 1 | 10 | 150,000 | active | pending | pending | pending | pending | pending |
| f6m_10v10_noweapon_s0 | 10 | 0 | 20 | 3,660,000 | active | -17.48 (-1.7479)* | -17.234 (-1.7234)* | -16.764 (-1.6764)* | -2.6125 (-0.2613)* | pending |

_Cells: `reward (reward per enemy)` for NoWeapon lanes; `*` = interpolated between bracketing updates; `pending` = not reached yet. Elapsed time is the lane's own `wall_time` minus its first logged timestamp, so it excludes queueing/startup. Scales use different `n_rollout_threads` (§4.5), so wall-clock reflects both learning speed and the scheduling choice. Raw brackets: `metrics/equal_wallclock.csv`._
<!-- /AUTO:section8 -->

<!--
Figure embedding convention for this report (brief §27: figures must be embedded,
not merely listed). All figures live in experiments/2026-10-07-08-formal6m/figures/
and are regenerated by scripts/make_figures.py, which is re-run by scripts/freeze.sh.
Paths below are relative to this file's location (docs/).

Pilot and formal series must never be drawn as one undifferentiated line; the
"*_with_pilot" variants are the only ones that mix them, and there the distinction
is carried by linestyle and by an explicit legend entry.
-->

### Figures

**§6 — N-v-N formal scaling, learning curves**

![Formal learning curves vs environment steps](../experiments/2026-10-07-08-formal6m/figures/formal_learning_curves_steps.png)

![Formal learning curves vs wall-clock](../experiments/2026-10-07-08-formal6m/figures/formal_learning_curves_walltime.png)

**§7 — reward normalised by team size (the only cross-N-comparable quantity for NoWeapon)**

![Reward per enemy vs steps, vs wall-clock, and vs N](../experiments/2026-10-07-08-formal6m/figures/formal_scaling_reward_normalized.png)

**§9 — computational scalability and campaign throughput**

![Throughput vs number of agents](../experiments/2026-10-07-08-formal6m/figures/formal_throughput_vs_agents.png)

![Resource scaling vs N](../experiments/2026-10-07-08-formal6m/figures/formal_resource_scaling.png)

**§10 — representation / centralised-critic scaling**

![Critic and actor scaling vs N](../experiments/2026-10-07-08-formal6m/figures/formal_critic_scaling.png)

**Pilot-vs-formal comparison figures** (`*_with_pilot`) overlay the 2026-10-04
pilot in a distinct linestyle so the two campaigns are never confusable.

## 9. Computational Scalability

### 9.1 The intrinsic cost of one environment step

From the pilot's environment-only benchmark (`metrics/env_bench_scaling.json`,
`scripts/env_bench.py`, random actions, no learning), re-fitted here:

| condition | cost per env step vs N | R² | cost per aircraft vs N | R² |
|---|---|---|---|---|
| **quiet** (machine otherwise idle) | **N^1.64** | 0.9989 | N^0.64 | 0.9927 |
| loaded (5 concurrent queues) | N^1.44 | 0.9937 | N^0.44 | 0.9369 |

Per-aircraft cost rises from 2.32 ms (N=2) to 6.39 ms (N=10) on a quiet machine —
i.e. **the environment does not merely have more aircraft to simulate; each
aircraft gets more expensive.** That is the signature of an N-dependent per-step
term, and it is exactly the O(N²) observation construction diagnosed as F8:
`MultipleCombatTask.get_obs()` walks every partner and enemy for every agent, and
`BaseEnv.get_state()` then calls `get_obs` again for all 2N agents and hstacks the
result — two O(N²) passes per step. Amortised over N aircraft this gives the
measured N^0.64. Note the exponent being *lower* under load (1.44) is not a
speedup: contention adds a roughly constant overhead per step, which flattens a
power law. Both are reported, per the pilot's F7 discipline.

### 9.2 What training actually achieves

`FPS` is the runner's own accounting (wall-clock, and it includes eval). Divided
by the rollout threads allocated, and compared against the single-core intrinsic
rate:

| N | threads | FPS | steps/s per thread | intrinsic single-core | achieved fraction |
|---|---|---|---|---|---|
| 2 | 4 | 77 | 19.2 | 107.8 | **17.9%** |
| 3 | 8 | 126 | 15.8 | 60.3 | **26.1%** |
| 5 | 8 | 82 | 10.2 | 25.4 | **40.4%** |
| 10 | 20 | 76 | 3.8 | 7.8 | **48.6%** |

**OBSERVATION.** Achieved thread efficiency *rises* with N. This is the
counter-intuitive part, and it is explained by the same mechanism: at N=2 a
vectorised step takes ~9 ms, so the per-step fixed costs (IPC to the learner,
action dispatch, Python overhead) are a large fraction of it; at N=10 a step
takes ~128 ms and the same fixed costs amortise. So each worker approaches its
intrinsic rate precisely *because* the task got slow.

**FACT.** Consequently the wall-clock to a fixed step budget grows much faster
than the intrinsic N^1.64, because at small N the parallel efficiency is worse.
At the thread allocation used here, 6M steps cost roughly:

| N | threads | hours to 6M |
|---|---|---|
| 2 | 4 | ~21.7 |
| 3 | 8 | ~13.2 |
| 5 | 8 | ~20.3 |
| 10 | 20 | ~21.9 |

which is why the thread allocation is per-lane rather than flat (§4.5, and
`status/plan.md` for the full derivation). Note that at *equal threads* 10v10
would need ~52 h — 2.4× the wall-clock of 2v2 — for the same 6M env steps. The
`n_rollout_threads` confound in §4.5 is the price of removing that.

### 9.3 Aggregate scheduling throughput

The binding resource is CPU, not GPU (GPU utilisation stayed 0–45% and VRAM
≤ 2.4 GB/job across nine concurrent lanes). The campaign was therefore scheduled
against **aggregate useful env-steps/s**:

| time | lanes | rollout threads | CPU used (of 48 quota) | aggregate env-steps/s |
|---|---|---|---|---|
| 03:11 | 5 | 44 | — | 451 |
| 03:17 | 7 | 50 | — | 672 |
| ~05:00 | 9 | 56 | ~35–39 | ~798 |
| 17:30 | 9 (+2 seeds) | 66 | 38–42 | ~800 |

**FACT.** Adding two 3-thread SingleCombat lanes at 03:10 raised aggregate
throughput from 451 to ~670 env-steps/s, and later additions took the campaign to
~800 env-steps/s while remaining inside the CPU quota.

**FACT (a measurement error, corrected — incident F16).** Every CPU figure in
earlier drafts of this section was wrong. They came from `/proc/stat`, which in
this container reports the **host's** 192 logical CPUs and returns deltas
alternating between 0 and ~200 cores between consecutive 5-second samples while
the container is demonstrably busy. The authoritative source is the container's
own cgroup accounting, and by that measure the campaign used **~38–42 of its 48
cores (≈80–87%), with `nr_throttled` at 0.02–0.04% of periods** — i.e. the quota
was never actually binding.

**OBSERVATION (revised in light of the above).** `f6m_10v10_noweapon_s0`'s
*cumulative* FPS fell from 70 to 64 across the two updates following the 03:10
additions, then recovered to 74–76. Cumulative FPS is an average since run start,
so a dip is the arithmetic consequence of any slower interval and is not by
itself evidence of sustained contention. Since the quota turns out never to have
been saturated, **the honest reading is that the added lanes cost 10v10 little or
nothing measurable**, and the initial dip should not be cited as a scheduling
cost. What *is* solid: the 10v10 lane finished with margin.

**OBSERVATION.** `load1` reached 74 at 17:23 while the container was using 38 of
48 cores. Load average counts runnable-and-blocked tasks across the host and is a
poor scheduler signal here; GPU idleness is a useless one (the GPU sat at 0–45%
for the entire campaign). The decisions were made on measured aggregate
env-steps/s, on the container's own cgroup CPU accounting, and on the P0 lane's
own FPS.

**CATEGORISATION.** Everything in this section is `Computational scalability`.
None of it is evidence about the learning algorithm, and it must not be read as
such — a slow environment is not a MARL failure.

## 10. Representation / Critic Scalability

**This section is complete and does not depend on the training runs finishing.**
It is a pure model-construction measurement (`scripts/critic_scaling_probe.py`,
output `metrics/critic_scaling.json`), it takes ~7 s, and the values it produces
for N = 2/3/5/10 are **bit-identical to the ones the 2026-10-04 pilot measured
independently** — which is the reproducibility evidence for this section.

### 10.1 Measured dimensions and parameter counts

| N | total agents | local obs dim | share_obs dim | actor params | critic params | critic 1st-layer params | critic 1st-layer MAC / env step |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 154,891 | 163,969 | 13,952 | 331,776 |
| 3 | 6 | 39 | 234 | 156,427 | 180,097 | 30,080 | 1,078,272 |
| 5 | 10 | 63 | 630 | 159,499 | 230,785 | 80,768 | 4,838,400 |
| 10 | 20 | 123 | 2,460 | 167,179 | 465,025 | 315,008 | 37,785,600 |
| **N=2 → N=10 growth** | 4→20 | **4.56×** | **22.78×** | **1.08×** | **2.84×** | **22.58×** | **113.9×** |

### 10.2 Exact closed forms (stronger than a fitted exponent)

Fitting exponents was unnecessary: the dependence is exactly determined by the
architecture, and the closed forms below reproduce **all four measured points
exactly**, with no free parameters.

| quantity | closed form | N=2 | N=3 | N=5 | N=10 | exact? |
|---|---|---|---|---|---|---|
| local obs dim | `12N + 3` | 27 | 39 | 63 | 123 | ✔ |
| **share_obs dim** | **`2N·(12N + 3) = 24N² + 6N`** | 108 | 234 | 630 | 2,460 | ✔ |
| actor params | `128·(12N+3) + 151,435` | 154,891 | 156,427 | 159,499 | 167,179 | ✔ |
| **critic params** | **`128·(24N²+6N) + 150,145`** | 163,969 | 180,097 | 230,785 | 465,025 | ✔ |

Why these hold, straight off the code:

- An agent's own observation is `12N + 3`-dimensional: a fixed 3-dimensional
  self-state plus **12 features for each of the N enemies** (heading, relative
  position, velocity, …). The agent's view of its own team-mates enters through
  the shared state, not its local observation.
- `share_obs` is the concatenation of the observations of **all 2N agents**
  (`envs/JSBSim/envs/env_base.py::get_state` hstacks `get_obs` over every agent).
  So `share_obs_dim = 2N × obs_dim = 2N(12N+3)`, and the N² term is structural:
  one factor of N from "more agents" times a second factor of N from "each agent
  observes more enemies".
- Both networks are MLPs whose first layer is `share_or_obs_dim × 128`; the
  remaining `151,435` / `150,145` parameters (recurrent core + heads) are
  **constants independent of N**.

**Consequences, read directly off the closed forms:**

| quantity | N=2 → N=10 growth | asymptotic |
|---|---|---|
| local obs dim | 4.56× | Θ(N) |
| **share_obs dim** | **22.78×** | **Θ(N²)** |
| actor params | **1.08×** | Θ(1) |
| **critic params** | 2.84× | Θ(N²) |
| critic first-layer params | 22.58× | Θ(N²) |
| critic first-layer MAC / env step | 113.9× | Θ(N³) |

The `Θ(N³)` in the last row is worth stating plainly: the critic's first layer
does `O(N²)`-wide work for `O(N)` agents, hence **cubic** total work per
environment step. For comparison the *environment* was measured at N^1.64
(§9.1) — so the centralised critic is, asymptotically, the more aggressive
scaling term of the two.

### 10.3 What this does and does not establish

**FACT.** In this codebase the centralised critic is the only learned component
whose *representation* grows super-linearly in team size, and it grows as
exactly N². The policy is essentially scale-invariant in parameter count.

**OBSERVATION.** The same O(N²) structure — the fully concatenated global state —
is simultaneously the cause of the environment-side bottleneck diagnosed as F8 in
`docs/night_failures.md` (`get_state()` calling `get_obs` over all 2N agents,
twice per step). One architectural choice produces both a computational and a
representational N² term. Notably, the measured `critic 1st-layer MAC/env step`
grows **113.9×** for a 5× growth in N.

**HYPOTHESIS (not established here).** An O(N²)-sized critic input is a plausible
contributor to a *learning* scalability gap, but this campaign has not isolated
it: we have not run a critic with a sub-quadratic input (attention, factorised,
or local critic) on the same task. Any such claim needs that controlled
comparison, which is explicitly out of scope this round (§4.4).

**CANNOT CONCLUDE.** These are *parameter and FLOP* counts. They say nothing on
their own about achievable reward. A large critic input is not by itself a defect
— it is the definition of a centralised critic. The measurement bounds the size
of the problem; it does not demonstrate that the size is what limits learning.

### 10.4 Projection: where the centralised critic stops fitting

`metrics/critic_scaling.json` also carries an `extrapolated` block. **These are
projections, not measurements** — they extend the exact dimension formulas above
beyond the four N we can actually construct. They are reported here only because
they are computed from a *measured* calibration on this GPU (68.9 G-MAC/s,
fixed batch 256) and because they answer "what breaks first?".

| N | total agents | share_obs dim | critic 1st-layer params | analyst buffer for `share_obs` | est. critic fwd / env step | source |
|---|---|---|---|---|---|---|
| 2 | 4 | 108 | 13,952 | 0.03 GB | 0.005 ms | measured |
| 3 | 6 | 234 | 30,080 | 0.09 GB | 0.016 ms | measured |
| 5 | 10 | 630 | 80,768 | 0.42 GB | 0.070 ms | measured |
| 10 | 20 | 2,460 | 315,008 | 3.30 GB | 0.548 ms | measured |
| 20 | 40 | 9,720 | 1,244,288 | **26.1 GB** | 4.3 ms | *projected* |
| 50 | 100 | 60,300 | 7,718,528 | **404 GB** | 67 ms | *projected* |
| 100 | 200 | 240,600 | 30,796,928 | **3,228 GB** | 536 ms | *projected* |

**Buffer assumption matters and is stated:** the projection uses
`n_rollout_threads = 12` (the probe's default), i.e.
`(3001 × 12 × N × share_dim × 4)` bytes. This campaign runs 10v10 at
`n_rollout_threads = 20`, for which the same formula gives **5.9 GB**, not 3.3 GB.
The scaling in N is what matters and is independent of that constant; the absolute
GB figures are not — always read them with the thread count attached.

**FACT.** The `share_obs` replay buffer is O(N²) in memory. Under this campaign's
own configuration the 10v10 buffer is ~5.9 GB, and it grows ~4× per doubling of N
because both the agent count and each agent's observation length grow.

**OBSERVATION.** On a 1 TB box, the projected N=50 (100-agent) `share_obs` buffer
alone is ~0.4 TB at 12 threads, and N=100 is ~3.2 TB. So for this architecture the
**memory wall arrives before the compute wall** — and long before any question
about whether the learning algorithm scales.

**HYPOTHESIS.** This is a strong candidate for why "just use a global critic" does
not extend to large N: the bottleneck is a *representation* choice (concatenating
every agent's observation) rather than the critic's capacity or the optimiser.
Any sub-quadratic critic (attention / factorised / locality-restricted) removes
this term by construction — but that is a claim about memory, and **whether it
also improves learning is exactly what this campaign did not test** (§4.4).

**CANNOT CONCLUDE.** These projections assume the environment itself scales
harmlessly to 40/100/200 aircraft. It does not follow that the *task* is even
well-posed at those sizes, and none of it was run.

> **Only the four `measured` entries are evidence.** Everywhere else in this
> report, `metrics/critic_scaling.json`'s `extrapolated` block is ignored.

## 11. Sample / Learning Scalability

<!-- AUTO:section11 -->
Per-scale reward-trajectory summary for the N-v-N lanes, from `metrics/summary.csv`. `Tail slope` is the mean change of `average_episode_rewards` per PPO update over the last third of the logged updates; the verdict calls it improving only when the slope exceeds +0.05/update (same threshold as `scaling_table.py`), flat within +-0.05, declining below -0.05.

| Scale | Seed | Steps reached (% of ceiling) | Status | First reward | Last reward | Reward / enemy | Tail slope | Still improving at final logged update? | Eval last |
|---|---|---|---|---|---|---|---|---|---|
| 2v2 | 0 | 4,392,000 (73.2%) | running | -3.5101 | 22.687 | 11.344 | +0.0492 | flat (+0.0492/update) | 31.179 |
| 3v3 | 0 | 6,000,000 (100.0%) | completed_6M | -5.3185 | 35.932 | 11.977 | +0.0089 | flat (+0.0089/update) | 47.839 |
| 3v3 | 1 | 504,000 (8.4%) | running | -5.436 | 0.27721 | 0.092404 | -0.3 | declining (-0.3/update) | -4.2488 |
| 5v5 | 0 | 4,536,000 (75.6%) | running | -9.117 | -37.881 | -7.5761 | -1.87 | declining (-1.87/update) | -139.87 |
| 5v5 | 1 | 360,000 (6.0%) | running | -9.0539 | -7.5252 | -1.505 | - | - | -2.6338 |
| 10v10 | 0 | 3,780,000 (63.0%) | running | -17.621 | 1.3063 | 0.13063 | +0.0083 | flat (+0.0083/update) | -182.42 |

_`Reward / enemy` divides by N and is the only cross-N-comparable reward for the NoWeapon family (PostureReward sums over enemies; see §4). A `running` lane's verdict is a statement about its final logged update at generation time, not about where it will end; a lane at `completed_*` is frozen at its final value. Values for scales with two seeds are per seed; §12 quantifies the spread._

Matched-sample budgets from `metrics/sample_efficiency.csv` (latest real measurement at or below each budget — no interpolation; `~` marks a nearest measurement below 75% of the requested budget, i.e. do not read that column as if the lane had been measured there):

| Scale | Seed | Max steps | 150k | 300k | 450k | 600k |
|---|---|---|---|---|---|---|
| 2v2 | 0 | 4,164,000 | -0.61 (-0.31) | 4.32 (2.16) | 21.05 (10.53) | 20.49 (10.24) |
| 3v3 | 0 | 6,000,000 | -4.78 (-1.59) | -4.40 (-1.47) | -2.64 (-0.88) | 1.22 (0.41) |
| 3v3 | 1 | 168,000 | -5.02 (-1.67) | -5.32 (-1.77)~ | -5.32 (-1.77)~ | -5.32 (-1.77)~ |
| 5v5 | 0 | 4,320,000 | -8.87 (-1.77) | -8.29 (-1.66) | -6.30 (-1.26) | -5.74 (-1.15) |
| 5v5 | 1 | 120,000 | -8.55 (-1.71) | -8.55 (-1.71)~ | -8.55 (-1.71)~ | -8.55 (-1.71)~ |
| 10v10 | 0 | 3,660,000 | -17.67 (-1.77) | -17.45 (-1.74) | -17.44 (-1.74) | -17.45 (-1.75) |

_`reward (reward/enemy)`; NoWeapon family only._

Matched early training stage (mean over the first 5 logged updates per run, from `metrics/normalized_scaling.csv`). Dividing the critic's value loss by N^2 and its grad norm by N removes the reward-magnitude growth with N; a pure reward-scale effect would leave both roughly constant — the drift that remains is the cross-N, per-update difference at an identical stage of training:

| Scale | Runs | Updates | Reward / enemy | Value loss / N^2 | Critic grad / N |
|---|---|---|---|---|---|
| 2v2 | 2 | 10 | -1.638 | 0.5022 | 3.942 |
| 3v3 | 2 | 10 | -1.748 | 0.5863 | 3.892 |
| 5v5 | 2 | 10 | -1.781 | 0.6535 | 4.573 |
| 10v10 | 1 | 5 | -1.755 | 0.7024 | 4.972 |

_First-5-update means are noisy by construction; they are a matched-stage comparison, not a converged one. The full per-update trace is in `metrics/normalized_scaling.csv`._
<!-- /AUTO:section11 -->

### 11.1 A degradation, not noise: `1v1/NoWeapon/HierarchySelfplay` gets worse in its second half

Reported separately from the generated tables above because it is an
*observation about one lane's learning path*, not a scaling result.

At 4.39M of 6M steps, `f6m_official_1v1_hier_selfplay_s1` showed
`critic_grad_norm = 1274` and reward `−333`. The immediate question is whether
that single point is a divergence or an extreme draw, so the whole run was split
into quarters:

| quarter | critic_grad_norm median | reward median | reward mean |
|---|---|---|---|
| 1 | 108 | +24.1 | +2.3 |
| 2 | 112 | +22.4 | +13.2 |
| 3 | 266 | −17.2 | −23.8 |
| 4 | **473** | **−89.7** | **−100.1** |

The gradient quartiles barely overlap (last quarter p25 = 317 vs first quarter
p75 = 154), so **this is a monotone trend, not variance** — the lane is getting
*worse* while its critic gradient grows. The last point is simply the extreme of
a real trend, not a one-off.

**OBSERVATION.** Critically, the sibling lane does not do this:
`f6m_official_1v1_selfplay_s1` — the same environment, scenario family, seed and
hyperparameters, differing only in that it is the **non-hierarchical** task — has
a *falling* critic gradient and a rising reward over the same window. So the
degradation is specific to the hierarchical task variant, not to 1v1 NoWeapon,
not to seed 1, and not to the self-play mechanism in general.

**HYPOTHESIS (not tested here).** The hierarchical variant learns a 3-dimensional
high-level action on top of a fixed `BaselineActor` low-level controller, so its
effective action space is far smaller and its reward is dominated by the
low-level controller's behaviour. Under self-play the opponent set is resampled
uniformly from checkpoint history, so the value target is non-stationary; a
critic on a low-dimensional state may be less able to absorb that. This is
consistent with the data but **the campaign contains no experiment that isolates
it** — no fixed-opponent control, no second hierarchical seed.

**Cannot conclude.** One lane, one seed. This is a lead for the next round (§16),
not a result. In particular it is **not** evidence of a curse of multiagency: the
scale here is N=1 per side, the smallest in the campaign.

**No action taken.** This is a legitimate training outcome, not an engineering
fault, so nothing was restarted, clipped or "rescued" (§16 of the brief). The
lane is allowed to finish and is reported at whatever it reaches.

### 11.2 Episode length: measured, found NOT to be an N-dependent confound — and a correction that was tested and then withdrawn

`average_episode_rewards` is a per-episode **sum** of per-step rewards
(`runner/share_jsbsim_runner.py:112`). If mean episode length differed
systematically with N, then per-episode reward would be deflated at larger N for
purely mechanical reasons, and every cross-N conclusion would be suspect. So the
length was measured directly rather than assumed.

**Measurement** (`offline_eval.py --selfplay`, deterministic mirror match, 8
episodes, the scenario's fixed initial condition, final checkpoint of each seed-0
lane; episode length in env steps, `max_steps = 1000`):

| lane | N | mean_episode_length | return |
|---|---|---|---|
| `f6m_2v2_noweapon_s0` | 2 | 1000 (capped) | −212.50 |
| `f6m_3v3_noweapon_s0` | 3 | 1000 (capped) | +47.38 |
| `f6m_5v5_noweapon_s0` | 5 | **547** | −36.44 |
| `f6m_10v10_noweapon_s0` | 10 | 1000 (capped) | +98.62 |
| `f6m_3v3_noweapon_s0` @ 120k steps (control) | 3 | 1000 (capped) | −7.16 |

**Two hypotheses were tested and both were refuted by the data above.**

1. *"Episodes get shorter as N grows, because an episode ends when every agent is
   done and a larger team has more chances to lose someone."* **Refuted**: N=10
   runs the full 1000 steps. The N trend is absent; 5v5 is a lone outlier.
2. *"Short episodes are a consequence of a poor policy crashing, so length is an
   outcome of learning rather than a confound."* **Refuted**: a deliberately
   weak control — the same 3v3 lane at 120k steps (`actor_5.pt`), the worst
   policy in the campaign — also runs the full 1000 steps.

**Therefore the correction I was about to apply was withdrawn.** For a while the
plan was to report `reward_per_enemy / mean_episode_length` as a
length-corrected cross-N metric. On the N=5 numbers it looked like it mattered a
great deal: at the matched 4M budget it moved 5v5 from `+4.63` to `+8.46` per
enemy, i.e. it shrank the apparent 5v5-vs-2v2 gap from 54% to 15%, and at 2M/3M
it made 5v5 look *better* than every smaller scale. That result was **an artifact
of dividing by a lane-specific quantity**: length is 1000 for N=2, 3, 10 and for
a weak 3v3 policy, so it is not a function of N and not a function of policy
quality either. Dividing by it would have injected noise in the guise of removing
bias.

**What actually holds:**

- **FACT.** Episode length is lane-specific and non-stationary. It is *not*
  explained by N (2, 3, 10 all capped; 5 is not) and *not* explained by policy
  quality (a weak 3v3 policy is capped, a strong 10v10 policy is capped).
- **OBSERVATION.** There is therefore no *systematic, directional* N-dependent
  bias from episode length. The naive per-episode cross-N comparison is not
  uniformly corrupted the way §15.5 warned it might be.
- **OBSERVATION.** It *can* mislead for an individual lane. If the 5v5 policy
  genuinely spends 45% less time alive per episode, then ~half its apparent
  reward deficit against the smaller scales is "died sooner" rather than "scored
  worse per unit time" — and there is no way to tell those apart from the
  per-episode number alone.
- **CANNOT CONCLUDE.** Whether the 5v5 result at 547 reflects a real behavioural
  difference (a crash-prone policy), a transient phase of that one run, or an
  artifact of the single deterministic rollout. One sample per lane, one seed,
  and the metric is deterministic so there is no error bar to consult.
- **CONSEQUENCE FOR READING §6/§7.** The N=5 row carries more uncertainty than
  the others, for a reason that has nothing to do with coordination and nothing
  to do with scale. It is flagged, not silently normalised away.

This episode is worth recording as a methodological result in its own right: a
plausible, data-supported correction was proposed, a control was run to test it,
the control refuted it, and the correction was withdrawn before it reached a
conclusion. That is the same discipline the pilot applied in F7 (reporting
measurements under both quiet and loaded conditions rather than picking the one
that suited the narrative).

> Note on the mirror-match returns in the table above: they are **not** a measure
> of policy strength and must not be reported as evaluation performance. Both
> sides run the same checkpoint from a geometrically asymmetric start, so the
> return measures "who wins this fixed deterministic asymmetric engagement under
> identical policies". Only `std_return` (a determinism check) and
> `mean_episode_length` are structurally meaningful. See §13, F18.

## 12. Seed Variance

<!-- AUTO:section12 -->
Seed variance for the N-v-N lanes. A spread is only computed where at least two seeds of the same scale exist; a single run cannot produce a variance, and none is fabricated from one.

**2v2** — 1 lane with data.

| Seed | Status | Threads | Steps reached | Ceiling | Final logged reward | Reward / enemy |
|---|---|---|---|---|---|---|
| 0 | running | 4 | 4,392,000 | 6,000,000 | 22.687 | 11.344 |

_Only one seed exists for 2v2 in this campaign, so **no spread is computed** (a spread needs at least two runs). The single-seed trend is in §11._

**3v3** — 2 lanes with data.

| Seed | Status | Threads | Steps reached | Ceiling | Final logged reward | Reward / enemy |
|---|---|---|---|---|---|---|
| 0 | completed_6M | 8 | 6,000,000 | 6,000,000 | 35.932 | 11.977 |
| 1 | running | 8 | 504,000 | 6,000,000 | 0.27721 | 0.092404 |

_Spread over the final logged training reward at generation time: **35.7** raw (**11.9** per enemy), i.e. max - min over the 2 seeds._

**Provisional:** seed 1 at 504,000 steps — the spread compares seeds at different training stages and will shrink or move as the incomplete lanes train. Treat it as an upper bound on the current difference, not a variance estimate.

**5v5** — 2 lanes with data.

| Seed | Status | Threads | Steps reached | Ceiling | Final logged reward | Reward / enemy |
|---|---|---|---|---|---|---|
| 0 | running | 8 | 4,536,000 | 6,000,000 | -37.881 | -7.5761 |
| 1 | running | 10 | 360,000 | 6,000,000 | -7.5252 | -1.505 |

**Thread confound (§4.5):** the seeds of 5v5 do not share `n_rollout_threads` (seed 0: 8, seed 1: 10), so this comparison crosses batch-size differences as well as seeds.

_Spread over the final logged training reward at generation time: **30.4** raw (**6.07** per enemy), i.e. max - min over the 2 seeds._

**Provisional:** seed 0 at 4,536,000 steps, seed 1 at 360,000 steps — the spread compares seeds at different training stages and will shrink or move as the incomplete lanes train. Treat it as an upper bound on the current difference, not a variance estimate.

**10v10** — 1 lane with data.

| Seed | Status | Threads | Steps reached | Ceiling | Final logged reward | Reward / enemy |
|---|---|---|---|---|---|---|
| 0 | running | 20 | 3,780,000 | 6,000,000 | 1.3063 | 0.13063 |

_Only one seed exists for 10v10 in this campaign, so **no spread is computed** (a spread needs at least two runs). The single-seed trend is in §11._

_This campaign holds two seeds for 3v3 and for 5v5 (seed 0 and seed 1). 2v2 and 10v10 have a single scaling seed each; the official 2v2 lane is a different scenario path and is not counted as a second seed of the scaling lane. The table states each lane's thread count and steps; where the two seeds of a scale differ in `n_rollout_threads` the comparison also crosses the §4.5 batch-size confound, and the group is flagged above._
<!-- /AUTO:section12 -->

## 13. Failures and Fixes

Full detail in `experiments/2026-10-07-08-formal6m/status/incidents.md`
(F-numbers), continuing the `docs/night_failures.md` F1–F9 series.

### 13.1 Inherited from the pilot (not re-run, not re-derived)

| id | what | status this round |
|---|---|---|
| F1 | JSBSim `data` submodule missing → env cannot initialise | already fixed; not seen |
| F2 | `gym` missing | irrelevant (one render script); not on the training path |
| F3 | non-wandb branch dropped all PPO diagnostics | already fixed (`metrics.jsonl`); this campaign depends on it |
| F4 | official scripts' `--clip-params` typo + hard wandb dependency | worked around in the launcher, values unchanged |
| F5 | generated scaling configs overwrote the NoWeapon variants | already fixed; configs verified: 10v10/scaling_noweapon is `hierarchical_multiplecombat` with 20 aircraft |
| F6 | status snapshot mis-parsed setproctitle'd workers | already fixed |
| F7 | env benchmark measured under load, not intrinsically | addressed by reporting quiet **and** loaded |
| **F8** | **env throughput is CPU-bound, main process idle** | **confirmed as the binding constraint this round; see §9** |
| **F9** | **`1v1/ShootMissile/HierarchyVsBaseline` cannot run at all** | **confirmed; deliberately excluded, recorded `not_applicable`** |

### 13.2 New this round

| id | what | category |
|---|---|---|
| **F10** | `scaling_table.py` emitted `peak_cpu_cores_host = 175.9` for a 48-core box | `Other` (measurement bug) |
| **F11** | representation columns (obs dims, param counts) were empty because `critic_scaling_probe.py` was never invoked | `Other` (missing instrumentation) |
| **F12** | `make_manifest.py`'s end-of-job regex never matched the real ledger line, so **finished lanes were silently reported as running** | `Other` (instrumentation bug, inherited from the pilot) |
| **F13** | analysis scripts hardcoded the pilot's campaign path | `Other` (portability) |

**F10** — the sampler (`os_watchdog.sh`) writes `cpu_busy_pct` already normalised
to the 48-core cgroup quota, but `scaling_table.py` multiplied it by the
host-denominator constant 192/100. The result was a physically impossible 175.9
cores. Fixed by deriving the multiplier from `/sys/fs/cgroup/cpu.max` at runtime
and **renaming the column to `peak_busy_cores_of_48_quota`** so the ambiguity
cannot recur; the legacy pilot schema is still reconstructed correctly (it
reproduces the pilot's historical 65.3). This is a pure instrumentation fix — no
training behaviour was touched.

**F11** — fixed by wiring the existing probe into `scaling_table.py` (cached, ~7 s).
The probe had to be *run*, not written: the method existed but nothing called it,
so the Representational-Scalability section (§10) would have had no data at all.

**Why these matter for the report.** F10–F13 are all `Other` — instrumentation
and measurement defects. None of them is evidence about the algorithm, and per
the pilot's own discipline (`docs/night_failures.md` §判定纪律) **none of them may
be cited as support for a curse-of-multiagency claim.** F10 in particular is a
good example of the failure mode the pilot warned about: a number that looked
like a scaling result (175.9 "cores" at N=10) and was actually a unit error.

### 13.3 Not run, and honestly labelled

- `1v1/ShootMissile/HierarchyVsBaseline` — `not_applicable` (F9, upstream bug, 0 steps).
- `1v1/DodgeMissile/*` family — out of scope this round; the pilot covered them.
- `1/heading` (SingleControl) — an L1 official entry that is not a multi-agent
  task. Deferred to a spare lane; if it does not run, it is `not_started`, not
  `failed`.

### 13.4 One process-level caveat about this codebase

`run_train.sh` captures `$?` from a `python … | tee` pipeline **without
`pipefail`** (lines 102–104), so every job records `exited with code 0` —
including crashes and SIGINT timeouts. Additionally
`scripts/train/train_jsbsim.py:107-133` always allocates the next free `run<N>`
directory and no launcher exposes `--model-dir`, so **a relaunch silently starts
a fresh run in `run2/` rather than resuming**. Both facts mean: exit codes are
not evidence of success, and no job is auto-restarted. Success is judged only
from step progress in `metrics.jsonl` plus the absence of `Traceback`.

## 14. What We Can Conclude

TBD

## 15. What We Cannot Conclude

This section is deliberately written to be readable *before* the final numbers
are in, because none of it depends on them. Every item below is a structural
limit of the design, not a caveat about a particular value.

**1. We cannot claim any kind of convergence result.** 6M is a **budget
reduction** from the official 1e8, adopted because 1e8 needs several hundred
hours per run here (§2, §4.1). A run at 6M may be mid-improvement, at a plateau,
or past a degradation; this report says which, per lane, and never says
"converged" without the evidence for that specific lane.

**2. We cannot claim a curse of multiagency.** The phrase describes a
*difficulty that grows with the number of agents*. To support it we would need
(a) more than one seed per scale, (b) the agent-count effect separated from the
compute effect, and (c) at least one controlled mechanism comparison. This
campaign has one of the three: one seed per scale for the scaling family (the
second seeds for 3v3 and 5v5 were launched late and may be time-censored). A
difference in reward-per-enemy between N=2 and N=10 at 6M is an **observation of
a difference**, and §14 will report it as exactly that.

**3. We cannot attribute any observed N-dependence to a mechanism.** The
centralised critic's representation is provably O(N²) (§10) and the environment
cost is measurably N^1.64 (§9.1) — but this campaign ran **no controlled critic
variant** (no attention, factorised, local or graph critic). Establishing that
the O(N²) *input* is what limits *learning* requires running a sub-quadratic
critic on the same task with everything else fixed. That is a next-round
experiment (§16), not a result.

**4. We cannot separate computational scalability from learning scalability.**
`n_rollout_threads` differs across scale (4/8/8/20 for N=2/3/5/10 — §4.5), so the
PPO update batch differs too. Every cross-N reward difference therefore carries
an unresolved batch-size contribution. This is the single largest confound in
the campaign and it is stated up front rather than buried; it does **not** affect
same-N comparisons (seeds) or any within-lane trajectory.

**5. We cannot compare raw per-episode reward across N without care.**
`PostureReward` sums over an agent's enemies, so raw reward scales with N by
construction; `reward/N` is the normalisation used throughout, and it is valid
**only for the NoWeapon family** (§4, §24 of the brief). Per-episode reward is
additionally confounded by episode length, so that was measured rather than
assumed: §11.2 finds lengths of 1000 (capped) at N = 2, 3 and 10, and 547 at
N = 5. **There is no systematic N-dependent length bias** — the confound is
lane-specific, not scale-systematic — so the cross-N comparison is not uniformly
corrupted. It can still mislead for the N=5 row specifically, which §11.2 flags
rather than silently normalising away. A length-corrected metric was built and
then withdrawn: see §11.2 for why dividing by a non-systematic, policy-entangled
quantity injects noise in the guise of removing bias.

**6. We cannot make a statistical statement about seed variance.** At most two
scales get a second seed, and those may be at different training stages when the
window closes. §12 refuses to compute a spread from one run, by design.

**7. We cannot bound 10v10's variance at all.** The highest-priority second seed
in the brief (10v10) is infeasible in this window: it needs ~20 threads for
~20 h, and no lane large enough frees before ~03:25 Oct 8. Its absence is a
recorded gap, not an oversight (§14 of the brief, `status/plan.md`).

**8. We cannot generalise beyond this environment and this configuration.**
`envs/JSBSim` implementing LAG with a 12-feature-per-enemy observation, a fixed
128×128 MLP actor and a concatenation-based centralised critic, at
`buffer_size=3000`, `lr=3e-4`, `gamma=0.99`. Statements here are about *this*
system.

**9. We cannot read anything into the eval curves beyond direction.** Per-checkpoint
MultipleCombat evaluation is deterministic (pilot §5.1, std = 0 over 8 repeats),
so the eval series' wobble is the *policy and the redrawn self-play opponent*
changing — not sampling noise, and not a calibrated estimate either. It is a
single deterministic episode per evaluation point.

**10. Eval/diagnostic quantities are read at different updates.** The `Eval`
column can lag the `Steps` column by one or two updates because eval rows are
sparser than training rows, and figures refresh only at each freeze (§13,
generator notes). No cell is fabricated; but a reader comparing across columns
should know they are not always the same update.

---

## 16. Next Experiments

Ranked by **which measured uncertainty the experiment would remove**, not by
ease. Each entry names the specific limitation from §15 it addresses.

### Tier 1 — would change a conclusion

**N1. 10v10 second seed (removes §15.7).** ~20 h at 20 threads. Without it the
headline scale has a single trajectory and its variance is unknown. This is the
first thing to spend the next window on, and the reason the brief ranks it above
everything else.

**N2. Controlled critic-variant comparison (removes §15.3).** The *only* way to
test the curse-of-multiagency hypothesis rather than describe a difference. Hold
the environment, policy, seed, step budget and thread count fixed; vary **only**
the critic's input structure:
  - `concat` (current baseline, O(N²) input)
  - `attention` over per-agent embeddings (O(N²) compute, O(N) parameters-per-agent)
  - `factorised` / mean-field (O(N) input)
  - `local` critic (O(1) input, no centralisation)
The prediction from §10 is that the concat critic is the first to hit a wall —
but the *learning* consequence is the open question. Run at N ∈ {2, 5, 10}, 2 seeds.

**N3. Fixed-opponent control for the §11.1 degradation (removes §15.2's weakest
point).** `1v1/NoWeapon/HierarchySelfplay` degrades over its second half while
the non-hierarchical sibling improves. Re-run both against a *frozen* opponent to
separate "self-play non-stationarity" from "hierarchical task is harder". Cheap:
1v1 at 3 threads is ~100 FPS.

### Tier 2 — would sharpen a conclusion

**N4. Episode-length normalisation (removes §15.5).** `offline_eval.py` already
reports `mean_episode_length` per checkpoint; run it across N at freeze and
report reward *per step* alongside reward per episode. Without this, cross-N
reward comparisons rest on an unverified assumption.

**N5. Constant-thread scaling re-run (removes §15.4).** Re-run N ∈ {2,3,5} at a
single `n_rollout_threads` (8 divides 2000 exactly, so the budget stays exact) to
get a batch-size-clean sub-curve. 10v10 cannot join at 8 threads in a 31 h
window; the clean sub-curve plus a flagged 10v10 point is still far better than
four confounded points. **Alternatively** hold `n_rollout_threads × buffer_size`
constant by trading threads for buffer size.

**N6. Extend the key lanes to 10M/30M (addresses §15.1 for the important lanes).**
Only where the curve is still clearly improving at 6M. Candidates by current
evidence: `3v3` and `2v2` (both still rising at their latest logged step),
`10v10` if it is still improving. Do **not** extend lanes that have plateaued —
that is budget burned for nothing (§14 of the brief).

### Tier 3 — engineering, must be a separate experiment

**N7. Observation-construction cost (does not address a §15 limit — it buys
wall-clock).** `get_state()` calls `get_obs()` for all 2N agents *in addition to*
the per-agent `get_obs()`, doing the O(N²) work twice per step (pilot F8, §9.1).
A single-pass implementation should recover most of the measured 18–49% achieved
fraction (§9.2). **This must be run as its own A/B**
(`engineering_speedup_old` vs `engineering_speedup_cached`) verifying identical
obs / reward / done / transitions, and the result may **not** be folded into the
formal scaling curves (§17 of the brief). It is included here because it is the
cheapest available speedup for *every* future scaling experiment.

### Explicitly not next

Implementing Graph-MAPPO / Attention-MAPPO / Hypergraph / World-Model as a
contribution. N2 is the *measurement* that would justify one of them; writing the
method first would be choosing the answer before asking the question (§31 of the
brief).

## 17. Running / Time-Censored Jobs

<!-- AUTO:section17 -->
Every lane of this campaign with status, steps reached and the reason for any shortfall, as of the moment this section was generated. `Status` uses exactly one of: completed_6M | completed_at_ceiling | running | time_cutoff | failed | not_applicable. A lane that is still writing is `running`; a lane that stopped short of its own ceiling without a crash signature is `time_cutoff` at its actual step count; exit codes are not evidence of success (§13.4).

| Experiment | Scale | Threads | Steps reached | Ceiling | Status | Note |
|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,608,000 | 5,994,000 | running | still writing (last write <2 min ago); 1,386,000 steps short of its ceiling at this snapshot |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,832,000 | 5,994,000 | running | still writing (last write <2 min ago); 162,000 steps short of its ceiling at this snapshot |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,393,000 | 5,994,000 | running | still writing (last write <2 min ago); 2,601,000 steps short of its ceiling at this snapshot |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 5,994,000 | completed_at_ceiling | reached its own ceiling 5,994,000 < 6,000,000 by construction (F17: runner floors episodes = 6e6//3000//3 = 666; a 3-thread lane can never reach 6M). Not a shortfall. |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,392,000 | 6,000,000 | running | still writing (last write <2 min ago); 1,608,000 steps short of its ceiling at this snapshot |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,272,000 | 6,000,000 | running | still writing (last write <2 min ago); 1,728,000 steps short of its ceiling at this snapshot |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 6,000,000 | completed_6M | reached the 6,000,000-step target |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 504,000 | 6,000,000 | running | still writing (last write <2 min ago); 5,496,000 steps short of its ceiling at this snapshot |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,536,000 | 6,000,000 | running | still writing (last write 3 min ago); 1,464,000 steps short of its ceiling at this snapshot |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 360,000 | 6,000,000 | running | still writing (last write <2 min ago); 5,640,000 steps short of its ceiling at this snapshot |
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,780,000 | 6,000,000 | running | still writing (last write 15 min ago); 2,220,000 steps short of its ceiling at this snapshot |
| f6m_official_1v1_shoot_hier_vsbaseline | 1v1 | 3 | - | - | not_applicable | not_applicable: F9 upstream bug (TypeError at the first env step); the official entry cannot run and was never launched |

_Ceiling is the lane's own reachable budget: runner floors `episodes = 6e6//3000//threads`, so 3-thread lanes cap at 5,994,000 (F17) and 4/8/10/20-thread lanes reach 6,000,000 exactly. `Steps reached` is live for `running` lanes; a later freeze supersedes this table, and the auto-finalizer writes one at every snapshot (`status/final_state_history.md`)._
<!-- /AUTO:section17 -->

## 18. Git Commits

TBD
