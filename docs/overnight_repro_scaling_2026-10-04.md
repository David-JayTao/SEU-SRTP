# SRTP Overnight Reproduction and Scaling Report

负责人：刘酝潇
日期：2026-10-04
仓库：`David-JayTao/SEU-SRTP`
实验分支：`exp/repro-scaling-20261004`
基础提交：`60a3e2d`（main）

> **状态说明**：本报告在通宵实验进行中持续更新。
> 标注 `[进行中]` 的章节在实验结束后会补全。
> 所有数字均来自落盘产物（`experiments/2026-10-04-night/`），非估计值，除非明确标注。

---

## 1. Objectives

三条主线：

- **A. 完整复现官方已有实验**——先把仓库里**真实存在**的实验审计清楚，再用**官方超参数**跑，
  不做任何算法改动。
- **B. N-v-N 可扩展性研究**——在不改变 MAPPO 核心算法的前提下，把 2v2 扩展到
  3v3 / 5v5 / 10v10，回答「LAG + MAPPO + self-play 在 agent 数增加后到底发生了什么」。
- **C. 后续可扩展 MARL 方向规划**——结合实测数据、代码结构与老师指定的两篇论文，
  给出候选方向，**不在今晚实现**。

**今晚的原则：数据先于结论。** 不预设答案；A–H 任意一种结论都可以，
但必须由数据决定，且必须把「工程问题」与「算法问题」严格分开。

---

## 2. Hardware and Environment

| 项目 | 值 |
|---|---|
| 机器 | AutoDL 容器 `autodl-container-cedc49a0d5-585eb907` |
| GPU | 3 × NVIDIA GeForce RTX 4090D（24564 MiB 显存/卡），驱动 595.71.05，CUDA 13.2 |
| CPU 配额 | **48 核**（`/sys/fs/cgroup/cpu.max` = `4800000 100000`；`nproc`=48；宿主 192 逻辑核） |
| 内存 | 1007 GB |
| 磁盘 | `/root/autodl-tmp` 50 GB（项目仅 48 MB，空间充足） |
| conda 环境 | `jsbsim`（Python 3.12.3） |
| PyTorch | **2.8.0+cu128**，`torch.cuda.is_available() = True` |
| JSBSim | 1.1.6（pip），气动数据来自 submodule `JSBSim-Team/jsbsim` |
| gymnasium | 1.3.0 |

**环境层面的重要事实**：本机**没有 CJK 字体**，因此所有图表的文字为英文。

---

## 3. Repository State

- 起始提交：`60a3e2d`（`main`），工作区除未跟踪的 `papers/` 外干净
- 实验分支：`exp/repro-scaling-20261004`
- `envs/JSBSim/data` 是 **git submodule**，初始为空（见 `docs/night_failures.md` F1），
  已用 `git submodule update --init --depth 1` 补齐（14 MB）
- 官方参考脚本共 **6 个训练入口** + 2 个非训练脚本（详见 §4）

---

## 4. Official Experiment Inventory

完整清单见 **`docs/baseline_inventory.md`**。核心结论：

「官方实验」分三层，**严禁把 L3 冒充成官方 baseline**：

| 层次 | 含义 | 数量 |
|---|---|---|
| **L1** | 有官方 `.sh` 启动脚本 | 6 个训练 + 2 个非训练 |
| **L2** | 官方 YAML + 官方 task 实现，但**没有官方 `.sh`** | 14 个配置 |
| **L3** | 仓库中不存在 | N≥3 的任何组合、`2v2 vsBaseline`、`MultipleCombat+ppo` 等 |

**L1 六个训练入口**：

| # | Environment | Scenario | Algo | 武器 | Self-play |
|---|---|---|---|---|---|
| 1 | SingleControl | `1/heading` | ppo | 无 | 否 |
| 2 | SingleCombat | `1v1/NoWeapon/vsBaseline` | ppo | 无 | 否（对手=内置 baseline） |
| 3 | SingleCombat | `1v1/NoWeapon/Selfplay` | ppo | 无 | ✅ fsp |
| 4 | SingleCombat | `1v1/ShootMissile/HierarchySelfplay` | ppo | 导弹 | ✅ fsp |
| 5 | MultipleCombat | `2v2/NoWeapon/HierarchySelfplay` | **mappo** | 无 | ✅ fsp |
| 6 | SingleControl | `1/HumanFreeFly`（人在回路） | ppo | 无 | 否 |

**关于「2v2 + ShootMissile」的明确结论**：

> 官方**没有** `.sh` 脚本（不是 L1）。但**也不是我们凭空造的**：
> `envs/JSBSim/configs/2v2/ShootMissile/HierarchySelfplay.yaml` 是仓库正式提交的配置，
> `MultipleCombatEnv.load_task()` 有 `hierarchical_multiplecombat_shoot` 分支，
> `HierarchicalMultipleCombatShootTask` 也完整实现。
> 正确表述：**官方配置 + 官方任务实现，缺官方标准脚本（L2）**。

**官方脚本的两个缺陷**（复现必须记录）：

1. 六个 `.sh` 全传 `--clip-params`，而真名是 `--clip-param`。
   因为 `train_jsbsim.py` 用 `parse_known_args()`，**未知参数被静默忽略**，
   实际生效的是默认值 0.2。我们的启动器显式传 `--clip-param 0.2`，
   **语义完全不变**。
2. `--use-wandb` 需要外部账号；且 `use_wandb=True` 时 `save_dir` 被指向
   `wandb.run.dir`。我们的启动器去掉该参数，走官方代码里本就存在的非 wandb 分支。

---

## 5. Baseline Reproduction

> `[进行中]` 下表在实验结束后填最终值。实时状态见
> `experiments/2026-10-04-night/status/running_jobs.md` 与 `manifest.csv`。

**所有官方入口一律用官方超参数启动**（`num_env_steps=1e8`、`buffer_size=3000`、
`lr=3e-4`、`ppo_epoch=4`、`hidden="128 128"`、`data_chunk_length=8` …），
**没有偷偷调小步数**。因为实测吞吐远不足以在 11 小时内跑完 1e8 步，
每个作业有**墙钟上限**，记录 `planned / completed / 趋势 / 预计剩余`。

| 实验 | 状态 | steps 完成/计划 | FPS | 训练 reward 趋势 | eval reward | checkpoint |
|---|---|---|---|---|---|---|
| `official_heading` | 进行中 | 510000 / 1e8 | 569 | **明显上升**（-14.0 → +0.8） | - | ✅ |
| `official_2v2_noweapon` | 进行中 | 180000 / 1e8 | 218 | 平坦（-3.5 附近） | -290 → -99（**上升**） | ✅ |
| `official_2v2_noweapon_selfplay` | 进行中 | 96000 / 1e8 | 155 | +11.2 → +9.9 | 29.7 → 15.0 | ✅ |
| `official_1v1_vsbaseline` | 排队中 | - | - | - | - | - |
| `official_1v1_selfplay` | 排队中 | - | - | - | - | - |
| `official_1v1_hier_selfplay` | 排队中 | - | - | - | - | - |
| `official_1v1_shoot_hier_selfplay` | 排队中 | - | - | - | - | - |
| `official_1v1_dodgemissile_selfplay` | 排队中 | - | - | - | - | - |
| `official_1v1_shoot_hier_vsbaseline` | 排队中 | - | - | - | - | - |

### 5.1 一个重要的方法学发现：MultipleCombat 的评估是确定性的

我最初怀疑官方 `--eval-episodes 1` 的评估太噪声（eval 序列在 -28 → -280 之间大幅摆动）。
为此写了离线评估器 `scripts/offline_eval.py`，对**同一个 checkpoint** 重复评估 8 个 episode：

```
mean_return = -191.5615   std_return = 0.0   mean_episode_length = 724
per_episode_returns = [-191.561, -191.561, -191.561, -191.561, ...]   # 8 个完全相同
```

**std = 0.0**，即 **MultipleCombat 的评估在固定 checkpoint 下是完全确定性的**。
原因在代码里：

- `MultipleCombatEnv.reset_simulators()` 只调用 `sim.reload()`（无新初始状态），
  **不做任何随机化**；对比 `SingleCombatEnv.reset_simulators()` 里有
  `self.np_random.shuffle(init_states)`
- 评估时策略是 `deterministic=True`

**因此结论要修正**：官方的 `--eval-episodes 1` 对 MultipleCombat **不是统计噪声问题**。
eval 曲线的大幅摆动是**策略与对手真实变化**的结果（FSP 的循环/振荡特性），
这一点本身值得在论文里讨论，而不是当作噪声忽略。

（补充：同一 checkpoint 在不同时间点评估会得到不同数值——因为训练**已经更新了 checkpoint**，
不是评估本身有随机性。已用两次运行 -191.6 / -139.9 的差异验证。）

> **对后续实验的建议**：由于评估是确定性的，"评估 1 个 episode" 等于评估
> **一个固定的确定性交战场景**。真正需要的不是更多 episode，而是
> **多个不同的初始条件**（例如随机化初始态势），否则评估无法代表策略的一般水平。
> 这是一个可以立即改进的点：给 `MultipleCombatEnv` 的 reset 加入初始状态随机化，
> 与 `SingleCombatEnv` 保持一致。

### 5.2 训练本身也没有场景随机化

由 §5.1 的代码事实直接推出一个更值得注意的结论：
`MultipleCombatEnv.reset_simulators()` 每次都把飞机 reload 回**同一组初始状态**，
因此**全部 12（或 18）个 rollout 线程、每一个 episode，都从完全相同的初始态势开始**。

- 训练时的随机性只来自**策略采样的动作**，不来自初始条件
- 也就是说，agent 是在**单一初始态势**上训练的，没有任何 domain randomization

这对结果的解读有直接影响：跨 N 的对比是在「同一个确定性初始交战」上做的，
因此**泛化性（不同初始态势下的表现）在本次实验中完全没有被测量**。
这也是「下一步实验」里优先要补的一项。

**已可确认**：
- `SingleControl/1/heading` 的 PPO **确实在学**：reward 从 -14 稳步升到 +0.8
  （510k 环境步，约 15 分钟）。这条最基础的通路是通的。
- `2v2/NoWeapon/HierarchySelfplay`（MAPPO + FSP）**能在本机跑起来并保存 checkpoint**，
  eval reward 从 -290 提升到 -99，**有学习趋势但很慢**。
- 1e8 步在本服务器需要**数百小时**，因此「完整跑完官方 1e8」在今晚不可能；
  本报告如实记录 planned vs completed，而不是伪造完成。

---

## 6. N-v-N Generalization

完整审计见 **`docs/nvn_scalability_audit.md`**。关键点：

**唯一的代码硬编码**：`MultipleCombatTask.num_agents` 原本 `return 4`。
因为整条流水线（vec-env → buffer → runner → 策略）都从 `envs.num_agents` 推导，
**放开这一个属性即可支持任意 N**。已改为读取场景自身的 `aircraft_configs`
（并保留显式 `num_agents` 覆盖键）。

**未改动**：MAPPO 算法、PPO 更新、GAE、网络结构、自博弈（FSP）、缓冲、
奖励函数、终止条件。满足「不改变 MAPPO 核心算法」的要求。

**新增**（生成，**非官方**）：7 个场景配置
`{2,3,5,10}v{N}/scaling_noweapon/HierarchySelfplay.yaml` 与
`{2,3,5}v{N}/scaling_shoot/HierarchySelfplay.yaml`。
生成器：`experiments/2026-10-04-night/scripts/gen_nvn_configs.py`。
reward / termination / simulation 参数**逐字继承**官方 2v2 模板，
只替换 `aircraft_configs`。

**队形设计**：一字排开、等间距 0.01°经度（≈556 m @60°N）、以战场经度为中心；
红队纬度 60.0 航向 0，蓝队纬度 60.1 航向 180，两队列相距 ≈11.1 km。
**副作用（必须声明）**：正面宽度随 N 线性增长（2v2: 0.56 km → 10v10: 5.0 km），
即**交战空间随 N 变大**。这是为保持机间几何不变所做的取舍。

---

## 7. Scaling Experiments

> `[进行中]`

**实测 scaling 表**（由 `scripts/scaling_table.py` 生成，
数据源 `experiments/2026-10-04-night/metrics/scaling_table.csv`）：

| scale | variant | agents | obs | share_obs | actor_p | critic_p | thr | seed | FPS | steps | 训练 reward(首→末) | value_loss | critic_grad_norm | NaN? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 27 | 108 | 154,891 | 163,969 | 12 | 0 | 218 | 180000 | -3.52 → -3.42 | 1.71 | 6.90 | no |
| 3v3 | noweapon | 6 | 39 | 234 | 156,427 | 180,097 | 10 | 1 | 155 | 60000 | -5.43 → -5.17 | 5.19 | 12.76 | no |
| 10v10 | noweapon | 20 | 123 | 2460 | 167,179 | 465,025 | 18 | 0 | 60 | 54000 | -17.66 | 63.84 | 61.57 | no |
| 5v5 | noweapon | 10 | 63 | 630 | 159,499 | 230,785 | - | - | - | 排队中 | - | - | - | - |
| 2v2 | shoot | 4 | 33 | 132 | - | - | - | - | - | 排队中 | - | - | - | - |
| 3v3 | shoot | 6 | 45 | 270 | - | - | - | - | - | 排队中 | - | - | - | - |

**当前可直接回答的问题**（用户 §1 主线 B 的 10 问）：

| # | 问题 | 目前答案 |
|---|---|---|
| 1 | 能不能正常运行？ | ✅ 2v2/3v3/10v10 全部正常运行，无 NaN、无崩溃 |
| 2 | 能不能开始学习？ | ✅ 全部在跑；`heading` 学习最明显；combat 任务学习慢 |
| 3 | 学习速度是否显著下降？ | `[进行中]` 需要等各规模积累足够 episode |
| 4 | sample efficiency 是否下降？ | `[进行中]` |
| 5 | wall-clock efficiency 是否下降？ | ✅ **显著下降**：FPS 218(2v2) → 155(3v3) → 60(10v10) |
| 6 | centralized critic 是否更难拟合？ | ⚠️ **有证据**：归一化后 value_loss/N² 上升 42%，grad_norm/N 上升 2.3× |
| 7 | observation / share_obs 是否膨胀？ | ✅ **是**：obs 27→123 线性；share_obs 108→2460 **二次** |
| 8 | coordination difficulty 是否增加？ | `[进行中]` |
| 9 | 是否出现 critic instability？ | ⚠️ critic_grad_norm 随 N 大幅上升（6.9→61.6），尚未观察到发散/NaN |
| 10 | 是否真正观察到算法 scalability degradation？ | ⚠️ **尚不能断言**，见 §13 |

---

## 8. Computational Scalability

### 8.1 环境步进的**内在**成本（机器空闲时测得）

`scripts/env_bench.py`，随机动作，单进程单核：

| 规模 | 飞机数 | steps/s | ms/env-step | 每架飞机 ms | 相对 2v2 |
|---|---|---|---|---|---|
| 2v2 | 4 | 107.8 | 9.27 | 2.32 | 1.00× |
| 3v3 | 6 | 60.3 | 16.59 | 2.76 | 1.79× |
| 5v5 | 10 | 25.4 | 39.37 | 3.94 | 4.25× |
| 10v10 | 20 | 7.82 | 127.85 | 6.39 | 13.79× |

**每架飞机本身的成本在增长**（2.32 → 6.39 ms），所以总成本**超线性**，
拟合约 **O(N^1.7)**。可精确定位到代码：

- `MultipleCombatTask.get_obs()` 对**每个 agent** 遍历其**全部** `partners+enemies`
  （每个都做 `LLA2NEU` + `get_AO_TA_R`）→ 每步 O(N²)
- `BaseEnv.get_state()` 又对**全部 2N 个 agent** 各调用一次 `get_obs`，
  再做 `hstack` 构造 `24N²+6N` 维向量 → **同一份 O(N²) 每步做了两遍**

### 8.2 训练时的实际吞吐（受争用影响）

5 条队列并发（约 40 个 rollout 进程 / 48 核）时：

| 规模 | 孤立基准 steps/s/进程（并发下） | 训练实测 steps/s/线程 | 达成率 |
|---|---|---|---|
| 2v2（12 线程） | 67.2 | 18.3 | **27%** |
| 3v3（10 线程） | 34.2 | 16.1 | **47%** |
| 10v10（18 线程） | 6.58 | 3.33 | **51%** |

10v10 完成 episode 0（3000 向量化步）约需 **15 分钟**，稳态 FPS 60。

### 8.2b 逐项拆分：到底是「物理」还是「观测工程」？（决定性证据）

`scripts/obs_cost_profile.py` 把每个 env step 拆成 4 部分分别计时：

| N | 机数 | `get_obs` 全部 agent | `get_state` | **JSBSim 物理** | `env.step` 总计 | 观测占比 | 物理占比 |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 1.98 ms | **2.02 ms** | 3.66 ms | 14.50 ms | 27.6% | 25.3% |
| 3 | 6 | 4.87 ms | 4.56 ms | 5.55 ms | 27.17 ms | 34.7% | 20.4% |
| 5 | 10 | 13.26 ms | 13.37 ms | 10.63 ms | 58.23 ms | 45.7% | 18.3% |
| 10 | 20 | 37.18 ms | **36.95 ms** | 15.63 ms | 183.88 ms | **40.3%** | **8.5%** |

**三个可以直接下结论的事实**：

1. **`get_state` 的耗时 ≈ 「对全部 agent 再跑一遍 `get_obs`」的耗时**
   （1.98 vs 2.02；37.18 vs 36.95 ms）。这直接证实 `get_state()` 内部
   **重复了整份观测构造** —— 每个 env step 做了**两遍完全相同的 O(N²) 工作**。
2. **JSBSim 物理本身是线性的**：0.91 ms/机（N=2）→ 0.78 ms/机（N=10）。
   二次增长**不是**物理仿真造成的。
3. 到 N=10，**观测构造占整个 step 的 40%，物理仿真只占 8.5%**。

> 这是本报告中最强的一条归因结论：
> **LAG 在 N-v-N 上的超线性成本主要是「观测/全局状态构造的工程实现」造成的，
> 而不是 JSBSim 物理仿真，更不是 MARL 算法。**

（这些绝对值是在并发负载下测得，故高于 §8.1 的静默基准；成立的是**比例**与**增长阶数**。）

### 8.3 瓶颈归因（逐进程采样，非推测）

对 `scaling_10v10_noweapon` 采样 `/proc`：

| 组件 | 状态 | CPU 占用 |
|---|---|---|
| 18 个 rollout worker | 全部 `state=R` | 各 ~0.72 核，合计 **13.2 核** |
| **主进程（PPO learner）** | **`state=S`（等待）** | **0.11 核** |
| GPU | 空闲 | 利用率 **0–1%**，显存 464 MB |

> **结论：瓶颈完全在 CPU 侧的环境仿真（JSBSim），既不是 PPO 更新，也不是 GPU。**
> 这是 `Computational scalability`，**不能**拿来当作 MARL 算法可扩展性的证据。

### 8.4 硬件利用率

- 实测峰值 CPU：**42.2 / 48 核**（约 88%）
- 峰值内存：**60.1 GB / 1007 GB**
- 峰值显存：**1564 MB / 24564 MB**（单作业 <1.5 GB —— **GPU 完全不是瓶颈**）
- 3 张卡的用途：**并行跑不同实验**，而不是多卡训练一个小网络

**一个重要的资源结论**：MPPO 的 actor/critic 只有 ~16 万参数，
每步 GPU 前向实测约 0.5 ms（且随 N 几乎不变，因为 batch 同步变大）。
**在 2v2–10v10 规模上，GPU 利用率 0–11%，网络远未成为约束。**
本项目的真实货币是 **CPU 核 × 时间**。

---

## 9. Representation Scalability

由代码严格推导（详见 `docs/nvn_scalability_audit.md` §3）：

$$\text{obs\_dim}_{\text{NoWeapon}}(N) = 12N+3 \qquad
\text{obs\_dim}_{\text{Shoot}}(N) = 12N+9$$
$$\text{share\_obs\_dim}(N) = 2N\cdot\text{obs\_dim} = 24N^2+6N \;\;(\text{NoWeapon})$$

| N | 总机数 | obs | share_obs | actor 参数 | critic 参数 | critic 首层参数 | share_obs buffer |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 154,891 | 163,969 | 13,952 | 0.03 GB |
| 3 | 6 | 39 | 234 | 156,427 | 180,097 | 30,080 | 0.09 GB |
| 5 | 10 | 63 | 630 | 159,499 | 230,785 | 80,768 | 0.42 GB |
| 10 | 20 | 123 | 2460 | 167,179 | 465,025 | 315,008 | **3.30 GB** |
| 20 | 40 | 243 | 9,720 | - | - | 1,244,288 | **26.1 GB** |
| 50 | 100 | 603 | 60,300 | - | - | 7,718,528 | **404 GB** |
| 100 | 200 | 1203 | 240,600 | - | - | 30,796,928 | **3,228 GB** |

（N≤10 为实测；N>10 为外推）

**关键点**：

1. **局部观测本身就随 N 线性增长**（因为 `get_obs` 把全部队友+敌机的相对量都塞进去了）。
   严格说这不是「局部」观测——**它已经是一个稠密的全局交互描述**。
2. **share_obs 是全部 agent 观测的拼接**，且**复制给每一个 agent**，
   因此维度 O(N²)。
3. **critic 每步计算量 O(N³)**：`(T·N) 行 × share_obs_dim(24N²)` × 128。
   实测 MAC/step：331,776 (N=2) → 37,785,600 (N=10)，**114×**。
4. **share_obs replay buffer 内存 O(N³)**：`(buffer_size+1) × T × N × share_dim × 4B`。
   N=10 已需 3.3 GB/进程；N=20 需 26 GB；N=50 需 404 GB。

> ⚠️ **但必须同时说清反面事实**：在 N ≤ 10 的**实测**区间，
> critic 单次前向耗时几乎**恒定**（0.45–0.53 ms），因为 batch 同步变大，
> GPU 并行度把它吸收了；实测的**每 agent** critic 前向耗时反而随 N **下降**
> （0.0199 → 0.0038 ms）。
> **所以「O(N³)」在 N≤10 还不是约束，真正的墙是内存**：
> N≈20 时 replay buffer 就要 26 GB。

---

## 10. Sample Efficiency Scalability

> `[进行中]` 需要等各规模积累到可比步数后填。
> 归一化方法见 §11 开头说明（奖励幅度 ∝ N，必须归一化）。

---

## 11. Learning Scalability

### 11.1 为什么必须归一化

`PostureReward.get_reward()` 对**每个敌机**累加 `orientation × range`：

```python
new_reward = 0
for enm in env.agents[agent_id].enemies:      # 对每个敌机求和
    AO, TA, R = get_AO_TA_R(ego_feature, enm_feature)
    new_reward += self.orientation_fn(AO, TA) * self.range_fn(R / 1000)
```

而 `PostureReward_scale` 在**所有** 2v2 与 N-v-N 配置里都是 **15.0**。
于是每步奖励幅度 **∝ N**。

**实测验证**：episode 0 的 `reward / N`：
**-1.76 (2v2) / -1.81 (3v3) / -1.77 (10v10)** —— 几乎恒定，
**直接证明奖励幅度确实 ∝ N**，也验证了归一化方式的正确性。

因此跨 N 比较必须用：
`reward/N`、`value_loss/N²`（平方损失随收益尺度的平方缩放）、`grad_norm/N`。

（顺带说明：官方自己也没有统一奖励尺度——`1v1/NoWeapon` 用 scale=100，
`1v1/Shoot`、`1v1/Dodge`、`2v2` 用 scale=15。说明这个尺度是逐场景手工调的，
**从来没有人针对 N>2 调过**。）

### 11.2 归一化后的 matched-stage 结果（同一 task 类、同一奖励配置、同一动作空间）

数据源 `metrics/normalized_scaling.csv`：

| N | episode | reward | reward/N | value_loss | **value_loss/N²** | critic_grad_norm | **grad_norm/N** |
|---|---|---|---|---|---|---|---|
| 2 | 0 | -3.52 | -1.76 | 1.791 | **0.448** | 5.35 | **2.68** |
| 2 | 4 | -3.42 | -1.71 | 1.708 | 0.427 | 6.90 | 3.45 |
| 3 | 0 | -5.43 | -1.81 | 4.239 | **0.471** | 11.28 | **3.76** |
| 10 | 0 | -17.66 | -1.77 | 63.838 | **0.638** | 61.57 | **6.16** |

**扣除奖励尺度后仍然残留的信号**：

- `value_loss/N²`：0.448 → 0.471 → **0.638**（2v2 → 10v10 **上升 42%**）
- `grad_norm/N`：2.68 → 3.76 → **6.16**（**上升 2.3×**）

> **解释（谨慎）**：在把「奖励尺度随 N 线性增长」这一平凡效应除掉之后，
> centralized critic 的**相对拟合误差与梯度幅度仍在随 N 增长**。
> 这与「集中式价值函数的表示/优化随 N 变难」的假设一致。
>
> **但这是假设，不是结论**：目前每个规模只有 1 个种子、且只到 early-training。
> 需要用 `queue_seeds` 的种子重复实验确认，并观察 trend 而非单点。

---

## 12. Coordination Scalability

> `[进行中]`

**已经识别出的、属于真正的协调/信用分配层面的可扩展性问题**（来自代码审计）：

```python
# envs/JSBSim/envs/multiplecombat_env.py
ego_reward = np.mean([rewards[ego_id] for ego_id in self.ego_ids])
for ego_id in self.ego_ids:
    rewards[ego_id] = [ego_reward]
```

每个 agent 拿到的是**全队均值奖励**。N 增大时，单个 agent 的行为对 team-mean 的
影响按 **1/N** 衰减 —— 这与代码 bug 无关，是**设计层面的信用分配问题**，
是本次实验中**少数几个可以正当地与 MARL 可扩展性挂钩的现象之一**。

另一个设计限制：`check_missile_warning()` 只返回**第一枚**存活来袭导弹，
观测里也只有一个 6 维导弹槽位。N 增大后来袭导弹数增加，
agent **无法感知同时来袭的多枚导弹**。这是 shoot 变体在 N 上的表示瓶颈。

---

## 13. Curse of Multiagency Discussion

**必须先说清楚理论**：不能说「联合动作空间指数增长，所以 MAPPO 训练不了」。

设 agent $i$ 的动作空间为 $A_i$，联合动作空间
$|A_{joint}| = \prod_i |A_i|$ 确实随 agent 数指数增长。

**但是** MAPPO 的 actor 是 **factorized** 的：

$$\pi(a\mid o) = \prod_i \pi_i(a_i \mid o_i)$$

MAPPO **不会显式枚举所有联合动作**。因此联合动作空间的指数增长主要体现为：

- exploration 困难
- sample complexity
- coordination
- non-stationarity
- credit assignment
- optimization complexity

而**不一定**体现为网络前向计算量指数增长。

**本次实验对这条链的实证贡献**：

1. **工程层面**：LAG 原本只支持 2v2（`num_agents` 硬编码 4），
   这是纯代码问题，已修复（F1/审计文档）。
2. **计算层面**：随 N 增长，**真正先爆掉的是环境仿真（CPU）与 replay buffer（内存）**，
   不是算法。O(N^1.7) 的环境成本，O(N³) 的 buffer 内存。
3. **表示层面**：share_obs 维度 O(N²)，critic 计算 O(N³) —
   但实测 N≤10 时 GPU 只用到 0–11%，**还没成为约束**。
4. **学习层面**：归一化后 critic 的 value_loss/N² 与 grad_norm/N **确实在增长**，
   这是目前唯一指向「算法/表示层面可扩展性」的实证信号，
   但**样本量不足**（每规模 1 个种子），**必须在报告与答辩中标注为待确认**。
5. **协调层面**：team-mean 奖励使个体贡献按 1/N 衰减（设计问题，非 bug）。

> **本报告明确不断言「10v10 学不会 = 证明了 curse of multiagency」。**
> 到 12:00 为止能说的最严谨表述是：
> 「在固定的墙钟预算与 48 核约束下，10v10 的**环境与内存成本**先于算法成为瓶颈；
> 在扣除奖励尺度后，centralized critic 的拟合难度随 N 上升，但没有观察到发散或 NaN。」

---

## 14. Paper A Analysis

> `[进行中]` 由后台工作流产出，见 `docs/scalable_marl_papers.md`。

---

## 15. Paper B Analysis

> `[进行中]` 同上。

---

## 16. Connection to LAG

> `[进行中]`

---

## 17. Candidate Scalable MARL Directions

完整分析见 **`docs/scalable_marl_candidates.md`**（12 个候选 + 客观对照表）。
**今晚只做分析，不实现任何新算法。**

先把靶子定清楚——当晚实测**确认**的失效：

| 编号 | 失效 | 证据强度 |
|---|---|---|
| **P1** | 观测构造 O(N²) 且**每步做两遍**（10v10 时占整个 env step 的 **40%**） | **强（实测）** |
| **P2** | 局部观测不是局部的：`obs_dim = 12N+3` 含全部其他飞机 | 强 |
| **P3** | `share_obs = 24N²+6N`，复制给每个 agent | 强 |
| **P4** | share_obs buffer **O(N³) 字节**（N=10 已 3.3 GB，N=20 需 26 GB） | 强 |
| **P5** | 归一化后 critic 仍在变难（`value_loss/N²` 0.448→0.638，`grad_norm/N` 2.68→6.16） | 中（单种子） |
| **P6** | team-mean 奖励使个体贡献按 **1/N** 衰减 | 仅代码推论，**未测量** |
| **P7** | 导弹观测只有 1 个槽位 | 强（代码） |
| **P8** | 训练无场景随机化、评估确定性 | 强（实测 std=0.0） |

候选方向（按「证据强度 × 与实测失效的对应度」排序，**不是我替项目组选的方向**）：

| Candidate | 靶子 | 改动量 | 难度 | 与 Paper A | 与 Paper B |
|---|---|---|---|---|---|
| **L. 修复观测构造冗余** | **P1** | 极小 | 低 | — | — |
| **A. Local / sparse critic（κ-sweep）** | P2,P3,P5 | 中 | 中 | **主对应** | 弱 |
| **B. Dynamic interaction graph** | P2,P3 | 中高 | 中高 | 强 | 弱 |
| **I. Curriculum scaling** | P9 | 小 | 低—中 | 弱 | 弱 |
| **J. Adaptive sampling** | 样本效率 | 小 | 低 | 弱 | **主对应** |
| **E. Graph critic** | P4,P5,P7 | 中高 | 中高 | 强 | 弱 |
| **D. Attention / sparse attention** | P2,P3,P7 | 中 | 中 | 中 | 弱 |
| **G. Mean-field** | P2,P3,P4,P7 | 中 | 中 | 中 | 弱 |
| **F. Value decomposition** | P5,P6 | 中/高 | 中/高 | 弱 | 弱 |
| **K. Model-based MARL** | 样本效率 | 高 | 高 | **主对应** | 弱 |
| **C. Dynamic grouping** | P6 | 高 | 高 | 弱 | 弱 |
| **H. Role embedding** | P6 | 中 | 中 | 弱 | 弱 |

**三条必须先讲清楚的纪律**：

1. **P1 是工程冗余，不是算法问题。** 在修复它之前，任何「新方法更快」的结论
   都会被这个工程 bug 污染。实测：`get_state` 与「对全部 agent 再跑一遍
   `get_obs`」耗时**相等**（37.18 vs 36.95 ms @10v10），即每步有一整份 O(N²)
   工作是纯冗余的。
2. **Paper B 不能用来在 LAG 上实现算法**（tabular + generative model +
   robust CCE），只能借「adaptive sampling / agent-wise treatment /
   避免显式联合动作估计」的**思想**。
3. **Paper A 的定理在空战里没有前提保证**（图结构、可分解动力学、局部模型
   都不存在），但它的 **κ 局部化框架可以直接设计成实验**（Candidate A），
   且是与实测失效 P2/P3/P5 最直接对应的方向。

**一个结构性发现**：`obs_dim = 12N+3` 随 N 变化，导致**不同 N 的 actor
权重无法互相加载**。因此 **「与 N 无关的观测表示」是课程学习（Candidate I）、
迁移学习、以及跨规模实验的共同前提**——这使 Candidate A/B/D/E 从「可选优化」
变成了「其他方向的前置条件」。

> **仍未确认**：P5 目前只有单种子、early-training 的一个数据点，需要
> `queue_seeds` 的种子重复实验确认；P6 只有代码推论，本晚**没有测量**
> 协调指标（重复攻击、目标分配冲突等）。「算法层面的 scalability 失效」
> 本晚证据**不支持**——瓶颈在 CPU 环境与内存，主进程在等待、GPU 空闲。

---

## 18. Failures and Fixes

完整记录见 **`docs/night_failures.md`**（F1–F8，含 Symptoms / Cause /
Code location / Fix / Verification / Category）。

摘要：

| ID | 一句话 | Category |
|---|---|---|
| F1 | JSBSim 气动数据 submodule 未初始化 | Other（环境） |
| F2 | `gym` 缺失（仅影响一个未使用的 render 脚本） | Other |
| F3 | 关掉 wandb 后 PPO 诊断量被静默丢弃（已修） | Other（方法学，**很关键**） |
| F4 | 官方脚本 `--clip-params` 拼写错误 + wandb 硬依赖 | Other |
| F5 | 我们自己的配置生成器变体覆盖 bug（已修） | Other |
| F6 | 状态快照脚本两处 bug（已修） | Other |
| F7 | 环境基准被并发负载污染（两种条件都保留） | Computational |
| F8 | 训练吞吐仅为孤立基准的 27–51%，瓶颈定位到环境侧 | Computational |

**判定纪律**：F1–F8 **没有一条**可以支撑 curse of multiagency 的结论。

---

## 19. Git Commits

> `[进行中]` 每次阶段性提交后更新。实时：`git log --oneline exp/repro-scaling-20261004`

| commit | message |
|---|---|
| `d0d9bd0` | chore: add overnight experiment infrastructure for repro + N-v-N scaling |
| `e6dc095` | docs: official baseline inventory + N-v-N scalability audit |
| `353ea10` | feat: metrics collection, figures and live status tooling |
| `088c6bd` | fix: capture experiment metadata in the log, and union per-step metrics records |
| `02c5935` | feat: reward-normalised cross-N critic analysis + scaling comparison table |

---

## 20. Running Jobs

> `[进行中]` 实时快照见 `experiments/2026-10-04-night/status/running_jobs.md`

5 条 tmux 队列：

| session | GPU | 内容 | 时间上限/作业 |
|---|---|---|---|
| `q_gpu0` | 0 | 官方 SingleControl + 1v1 全家（7 个） | 70 min |
| `q_extra` | 0 | 2v2 非层次化 selfplay + shoot scaling 2v2/3v3 | 90 min |
| `q_gpu1` | 1 | 官方 2v2 noweapon + 官方 2v2 shoot + scaling 2v2 | 2 h |
| `q_seeds` | 1 | 3v3/2v2/5v5 scaling 的**第二种子** | 1.5–2 h |
| `q_gpu2` | 2 | **10v10** → 5v5 → 3v3 scaling | 1.5–3 h |

队列采用**墙钟上限**而非杀任务：超时后用 `timeout -s INT` 结束，
**下一个作业自动开始**；因为每 episode 都存 checkpoint，最多只损失在飞的那个 episode。
**不会为了出报告而杀掉正在跑的实验。**

---

## 21. Recommended Next Experiments

> `[进行中]`

初步（待结合实测与论文分析细化）：

1. **在安静机器上重做环境吞吐基准**，把 §8.1 的内在成本与争用成本彻底分离。
2. **给 5v5/10v10 补种子**，把 §11.2 的单点信号变成趋势。
3. **奖励归一化消融**：把 `PostureReward_scale` 设为 `15/N`，
   验证 §11 的结论是否由奖励尺度残留造成。
4. **观测构造优化作为独立消融**：在 `get_state()` 中复用同一步的 `get_obs`，
   把每步 O(N²) 从两遍降到一遍。这是工程优化，必须与算法改进分开报告。
5. **把「局部观测」真正变局部**：当前 obs 含全部 agent 的相对量，
   可测试只保留 k 近邻，用于直接检验老师 Paper A 的 κ-hop 思想。
