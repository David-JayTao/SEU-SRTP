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

### 5.3 ⚠️ 官方脚本里的「FSP」并不是 FSP

读 `algorithms/utils/selfplay.py` 发现：

```python
class FSP(SelfplayAlgorithm):
    @staticmethod
    def choose(agents_elo, **kwargs) -> str:
        return np.random.choice(list(agents_elo.keys()))   # 均匀随机，不用 ELO
    @staticmethod
    def update(agents_elo, eval_results, **kwargs) -> None:
        pass                                               # 空函数
```

而 `share_jsbsim_runner.py:356` 给每个新 checkpoint 写的 ELO 都是同一个初值
`init_elo`，第 219 行还留着 `# TODO: use eval results to update elo`。

**后果**：
- `fsp` 实际是**对全部历史 checkpoint 的均匀随机采样**；
- `pfsp` 因 ELO 从不更新，其 meta-solver 概率退化为均匀分布，**同样等价于均匀采样**；
- 只有 `sp`（永远取最新）是真正不同的。

**因此本报告对 self-play 的准确表述改为**：
「MAPPO + **历史 checkpoint 均匀随机采样自博弈**」，
**不能**称其为博弈论意义上的 Fictitious Self-Play，
**也不能**拿它的结果与文献里的 FSP 结果对比。

（我们跑的确实是官方代码——用的就是官方 `--selfplay-algorithm fsp`。
这是对 baseline 的**命名纠正**，不是对代码的改动。）

### 5.4 学习信号（含一次**自我修正**）

> **⚠️ 本文档先前版本曾写「2v2 训练 reward 平坦」。那个判断在
> episode 0–12（≈4.3e5 步）时成立，但在更长预算下被数据推翻，现予更正。**

截至 03:40 的完整轨迹（`metrics/curves/`）：

| 实验 | 步数 | 训练 reward 轨迹 | 结论 |
|---|---|---|---|
| `official_heading` | 2.46e6 | -13.98 → … → **+100.6** | **明确学习** |
| `official_2v2_noweapon`（hier） | 9.7e5 | e0–e21 在 -3.5 ~ -3.2 徘徊，**e24 跳到 +6.67** | **慢，但有学习** |
| `official_2v2_noweapon_selfplay`（非层次化） | 6.7e5 | 11.2 → -12.9 → +18.1（**高度振荡**） | 有变化，噪声大 |
| `scaling_3v3_noweapon_s1` | 6.6e5 | -5.43 → -4.79 → -3.53 → -0.57 → **+4.09** | **稳定上升** |
| `scaling_10v10_noweapon` | 2.2e5 | -17.66, -17.57, -17.56, -17.65（仅 4 个 episode） | **样本不足，无法判断** |

**修正后的结论**：

1. **学习确实在发生**，但**很慢**——`2v2` 直到约 **7.5e5 步之后**
   才出现明显的 reward 抬升；`3v3` 则从较早阶段就开始稳步爬升。
2. 之前基于前 12 个 episode 得出的「平坦」是**过早的结论**。
   保留这条修正记录，是因为它本身就是一个教训：
   **在 4e5 步、约 0.4% 官方预算下不足以判断「学不学得会」。**
3. `10v10` 目前**只有 4 个 episode**（每 episode 约 17 分钟），
   **完全不足以判断**，任何关于 10v10 学习能力的断言都是无根据的。
4. `eval reward` 与 `train reward` 经常给出相反信号
   （如 3v3 的 eval 从 -136 升到 +21.4，而 2v2 的 eval 在
   -28 ~ -280 之间振荡）。结合 §5.1（评估确定性）与
   §5.3（对手是历史 checkpoint 的均匀采样），
   **eval 的波动主要来自对手变化**，不能单独用于判断 ego 策略的进步。

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

### 7.0 有效性验证：生成的 scaling 家族确实锚定在官方 2v2 上

scaling 系列是**我们生成**的配置（§6）。在做跨 N 对比之前必须验证
「生成的 2v2」与「官方 2v2」行为一致，否则整个 scaling 家族就失去了基线锚点。

**验证方法**：比较两者 **episode 0** 的 `average_episode_rewards`
（同一算法、同一奖励配置、同一动作空间；唯一差异是生成编队整体沿经度平移 278 m）。

| 配置 | episode 0 reward | reward/N |
|---|---|---|
| 官方 `2v2/NoWeapon/HierarchySelfplay` | **-3.525** | -1.7625 |
| 生成 `2v2/scaling_noweapon/HierarchySelfplay` | **-3.532** | -1.7658 |
| 差异 | **0.0065（占官方 0.19%）** | — |

> **结论：生成的 scaling 家族与官方 2v2 在数值上几乎完全一致（差 0.19%），
> 因此 2v2 → 3v3 → 5v5 → 10v10 的对比是可信的，
> 差异来自队伍规模而不是配置改动。**（§5.2 提到的唯一系统性差异——
> 正面宽度随 N 线性增长——仍然存在，必须一并声明。）

### 7.0b 头图：归一化后的 scaling 对比

图：`figures/scaling_reward_normalized.png`（左：vs 环境步数；右：vs 墙钟小时）。
纵轴统一为 **reward / N**（理由见 §11.1；仅对 NoWeapon 家族严格成立）。

**关键读数**（截至 05:45）：

| 规模 | 最长运行步数 | 已用墙钟 | reward/N 轨迹 | reward/N 终值 |
|---|---|---|---|---|
| 2v2 | 900k | ~1.3 h | -1.76 → 上升 → **+5.5** | **+1.87** |
| 3v3 | 840k | ~1.4 h | -1.81 → 上升 → **+6.5** | **+6.51** |
| 5v5 | 162k | ~0.5 h | -1.72（刚开始） | -0.91 |
| **10v10** | **648k** | **~2.7 h（最长）** | **-1.77 → 仍然平坦** | **-1.64** |

> **这是今晚关于 scalability 最清晰的一条实测结论**：
> **10v10 跑了全场最长的墙钟时间（约 2.7 小时、64.8 万步），
> 归一化后的奖励仍然没有任何可辨识的改善（-1.77 → -1.64）；
> 而 2v2 与 3v3 在 1.4 小时内就从 -1.8 升到了 +5 ~ +6.5。**
>
> 这**主要**是计算成本的直接后果：10v10 每个 rollout episode 约需 **17 分钟**
> （2v2 约 2.9 分钟），所以同样的墙钟时间买到的步数少得多
> （10v10: 648k / 2.7h ≈ 67k steps/h；2v2: 900k / 1.3h ≈ 692k steps/h，
> **相差 10 倍**）。
>
> **必须同时声明的限制**：
> - 10v10 只有约 **9 个 episode 数据点**，曲线很粗；
> - 各规模目前**都只有 1 个种子**；
> - 10v10 的步数（648k）仍少于 2v2（900k），
>   因此**不能排除「10v10 只是需要更多步」**——
>   只能说「**在同等墙钟预算下没有观察到改善**」。
> - 若最终仍是这个结论，正确的表述是
>   **「10v10 的 wall-clock efficiency 显著下降」**，
>   **不是**「curse of multiagency 被证实」。

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

> ⚠️ **但必须同时说清反面事实（已把 N=20/50 从外推升级为实测）**：
> critic 单次前向的**生产 batch** 耗时从 N=2 到 N=50 几乎**完全恒定**：
> 0.517 / 0.458 / 0.441 / 0.498 / 0.445 / **0.607 ms**。
> 即使 N=50（share_obs 60,300 维），一次完整 critic 前向只要 **0.6 ms**——
> 因为 batch 同步变大，GPU 并行度把它吸收了。实测的**每 agent** critic 前向
> 耗时反而随 N **下降**（0.022 → 0.001 ms）。
>
> **所以「O(N³)」在 N ≤ 50 都不是约束**（外推到 N≈100 才到 19.4 ms/env-step）。
> **真正先撞墙的是内存**：share_obs replay buffer 在 N=10 已 3.3 GB、
> N=20 需 26 GB、N=50 需 404 GB。
> **内存墙（N≈20）比计算墙（N≈100）早到约 5 倍。**
> 工程含义：若要扩到 20v20 以上，第一个要动的不是网络结构，
> 而是 `share_obs` 的稠密存储方式（改成图/实体表示）。

---

## 10. Sample Efficiency Scalability

> `[进行中]` 数字随实验推进自动刷新。
> 工具：`scripts/sample_efficiency.py` → `metrics/sample_efficiency.csv`。
> 归一化说明见 §11.1（NoWeapon 家族奖励幅度严格 ∝ N，必须归一化）。

### 10.1 方法说明（为什么不用「达到阈值所需步数」）

本应做的对比是「达到同等 reward 需要多少环境步」。但**目前没有任何一个规模收敛**，
因此任何阈值都是**事后挑的**，会系统性地偏向刚好越过它的那个运行。
所以本报告改成报告**在匹配步数处的 reward**，并同时给出种子间的分散度。

### 10.2 匹配步数处的 reward

（`( )` 内为 reward/敌机数；`-` 表示该运行尚未到达该步数；
`~` 表示该列最近一次测量低于请求步数的 75%，**不能当作在该步数处有测量**）

| N | seed | eps | max_steps | 150k | 300k | 600k |
|---|---|---|---|---|---|---|
| 3 | 1 | 23 | 690000 | -5.37 (-1.79) | -0.82 (-0.27) | 2.38 (0.79) |
| 10 | 0 | 5 | 270000 | -17.57 (-1.76)~ | -17.46 (-1.75) | -17.46 (-1.75)~ |

### 10.3 目前能说与不能说的

- **能说**：`3v3` 在 30 万步后出现明确上升（reward/敌机 -1.79 → -0.27）；
  `10v10` 到 27 万步仍**完全没有移动**（-1.75 → -1.75，5 个 episode）。
- **不能说**：由于 (a) 每个规模**种子数不足**（3v3 目前 1 个、10v10 1 个），
  (b) 10v10 只有 5 个 episode（每个约 17 分钟），
  (c) 3v3 与 10v10 的**步数区间不重叠**（10v10 最多 27 万步，3v3 已到 69 万步），
  **当前数据不足以得出任何「sample efficiency 随 N 下降」的结论。**
  要得到该结论，至少需要各规模在**同一批步数节点**（如 300k / 600k / 900k）
  上都有多种子测量。
- 队列里已经在跑 3v3 的 s2/s3、5v5 的 s1/s2、10v10 的 s1/s2，正是为了补足这一点。

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

### 11.1b ⚠️ 一个必须先排除的混淆：策略几乎还是均匀随机

**这是本晚最重要的单点发现之一，也是解释「战斗任务 reward 平坦」的关键。**

#### (a) `metrics.jsonl` 里的熵列不可直接用

`algorithms/utils/act.py :: ACTLayer.evaluate_actions` 对 MultiDiscrete 动作空间做的是：

```python
dist_entropy.append(action_dist.entropy() / action_log_probs[-1].size(0))   # ← 除以 batch 行数
...
dist_entropy = torch.cat(dist_entropy, dim=-1).sum(dim=-1, keepdim=True)
```

所以被 log 的 `policy_entropy_loss` 实际是 **(各维熵之和) / batch 行数**。
而 batch 行数

```
data_chunks     = n_rollout_threads * buffer_size // data_chunk_length
mini_batch_size = data_chunks // num_mini_batch
batch_rows      = data_chunk_length * mini_batch_size
```

**随 `n_rollout_threads` 变化，因此随 N 变化** —— 直接拿这列跨 N 比较是**错的**。
（例：2v2 的只读因子是 7200，10v10 是 10800。）

已在 `collect_metrics.py` 中还原：`policy_entropy_true_sum = -policy_entropy_loss × batch_rows`。

#### (b) 两种独立方法测出的真实熵（互相印证）

| 运行 | 训练步数 | 还原后的熵（终端值/最大） | **直接测量**（加载 checkpoint 前向） |
|---|---|---|---|
| 未训练 2v2 | 0 | — | **1.000** |
| `official_heading` | 1.17e6 | 13.91 / 14.54 = **0.957** | **0.949** |
| `official_2v2_noweapon` | 4.3e5 | 3.724 / 3.807 = **0.978** | **0.973** |
| `scaling_3v3_noweapon_s1` | 2.4e5 | 3.741 / 3.807 = **0.983** | — |
| `scaling_10v10_noweapon` | 1.1e5 | 3.798 / 3.807 = **0.998** | **0.998** |

两种方法（日志还原 vs 直接前向）在三个可比的运行上**吻合到 1% 以内**，
说明这个测量是可信的。

> **结论：训练了数十万步之后，策略的动作分布仍然停留在最大熵的
> 95%–99.8%——也就是几乎还是均匀随机。**
> 未训练策略是 100.0%，训练后只降到 94.9%（heading）到 99.8%（10v10）。

#### (c) 这意味着什么（以及不能意味着什么）

- **能解释**：战斗任务的训练 reward 为何**上升得如此慢**——策略的绝大多数
  概率质量还压在接近均匀的分布上，只有很小一部分在向更好的动作移动，
  所以每单位步数产生的行为改变很小。
  **注意（修正）**：这解释的是「慢」，**不是「不学」**。
  §5.4 的更长轨迹显示 reward 确实在上升，只是要 7e5 步量级才看得出来。
  **不能**用熵高来断言「学不会」。
- **不能说明**：不能说「10v10 比 2v2 更难学」。上表中熵与**训练步数**高度混淆
  （10v10 只有 2.2e5 步，不到 2v2 的四分之一），**必须先控制步数才能比较熵**。
  目前**不足以**得出「N 越大熵越高」的结论。
- **也不能说明**：不能用熵高推断「没在学」——见 §5.4 的修正，
  reward 确实在上升。熵只反映**动作分布**移动得慢，不反映价值/策略是否在改进。
- **归因**：这是**优化/超参数层面的现象**（`entropy_coef=1e-3` 很小、
  策略梯度在这两个任务上推进很慢），**不是 MARL 算法可扩展性问题**。
  按用户 §16 的分类，它属于 **Algorithmic/Learning**，但成因是超参数与任务难度，
  与 agent 数量无关。

**实际影响**：在策略仍接近随机的阶段比较 2v2 / 3v3 / 5v5 / 10v10 的
`reward vs steps`，比较的其实是「随机策略在几何规模不同的场景下拿到多少 shaping reward」，
而不是「哪个规模更容易学」。**这一点必须在结论与答辩中明确说明**，
否则会把环境几何差异误读成算法可扩展性差异。

#### (d) 是「学得慢」还是「学坏了」？——逐项诊断

这是必须区分的问题。看四个关键量的演化：

| 运行 | 步数 | `value_loss` | `policy_loss` | `actor_grad_norm` | **`ratio`** |
|---|---|---|---|---|---|
| `official_heading` | 30k → 1.29e6 | 3.99 → **0.66** | -0.0117 → -0.0119 | 0.27 → 0.49 | 1.0018 → 0.9995 |
| `official_2v2_noweapon` | 36k → 468k | 1.79 → **0.71** | -0.0020 → -0.0073 | 0.58 → 0.64 | 1.0003 → 1.0000 |
| `scaling_3v3_noweapon_s1` | 30k → 270k | 4.24 → **3.61** | -0.014 → +0.006 | 0.63 → 0.71 | 0.9995 → 0.9996 |
| `scaling_10v10_noweapon` | 54k → 108k | 63.8 → 72.4 | -0.0046 → -0.0054 | 0.50 → 0.49 | 0.9999 → 0.9999 |

**读法**：

1. **critic 确实在学**：`value_loss` 在 2v2 上从 1.79 降到 0.71，
   heading 从 3.99 降到 0.66。**价值拟合是有效的、在收敛的。**
2. **actor 几乎没有更新**：`ratio = exp(logπ_new − logπ_old) ≈ 1.0000`
   在**全部**运行、**全部**时刻都是这个值——意味着 PPO 每次更新后
   动作概率的变化只有约 1e-4 量级。
3. 两者结合 → **不是「学习坏了」，而是「actor 更新极慢」**。
   这排除了「梯度算错 / advantage 算错 / mask 处理错」这类 bug 假设
   （若是 bug，critic 不会稳定收敛、ratio 也不会稳定在 1 附近而是会发散或 NaN）。
4. 与 §11.1b 的熵测量一致：actor 慢 → 策略停在近均匀 → reward 平坦。

**为什么 heading 能学而战斗任务近乎不动**：heading 的动作空间是**原始舵面控制**，
奖励是低方差的稠密跟踪奖励；而战斗任务（层次化）的高层策略只有 3 维离散动作
（Δ高度 / Δ航向 / Δ速度），必须通过一个**冻结的预训练底层控制器**施加影响——
credit assignment 链更长、奖励更稀疏且对抗性更强。
**这是任务难度与层次化结构的问题，不是 agent 数量的问题。**

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

### 12.1 实测协调代理量（`scripts/offline_eval.py --coordination`）

NoWeapon 任务没有显式的目标分配，所以用「最近敌机」作为事实上的目标，
测量四个几何代理量（对已训练的 checkpoint 做**确定性** rollout）：

| 规模 | 检查点 | 不同目标数 | 目标碰撞率 | 队内平均间距 | 到最近敌机距离 | 平均 episode 长度 |
|---|---|---|---|---|---|---|
| 2v2 | `official_2v2_noweapon`（1.0e6 步） | **1.50 / 2** | 0.497 | 4461 m | 4235 m | 935 |
| 3v3 | `scaling_3v3_noweapon_s1`（6.9e5 步） | **2.02 / 3** | 0.597 | 3266 m | 2411 m | 1000 |

其中：
- **不同目标数**：队内有多少架敌机被至少一个己方 agent 当作最近目标
- **目标碰撞率**：有多少比例的 agent 与队友共享同一个最近敌机（"一窝蜂" 程度）

**读法（必须极度谨慎）**：

- 「目标覆盖比例」两会话接近（2v2 = 75%，3v3 = 67%），**没有观察到协调明显恶化**。
- 碰撞率 3v3 更高（0.60 vs 0.50），**但这很可能只是几何效应**：
  敌方数量从 2 增加到 3、而己方队形按固定间距展宽，
  最近敌机的分布本身就会更集中。
- **因此不能**由这两个数字得出「agent 变多导致协调变差」。

> **本测量有三个已知缺陷，必须在引用时一并说明**：
> 1. **只有 1 个种子**，且两个规模的步数不同（1.0e6 vs 6.9e5）；
> 2. **代理量受队形几何混淆**——生成配置刻意保持机间间距恒定，
>    正面宽度随 N 线性增长，这会独立于协调质量地移动这些数值；
> 3. 「最近敌机」只是目标的**代理**，LAG 的 NoWeapon 任务里
>    并没有真正的目标分配机制。

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
   不是算法。实测环境成本 **∝ N^1.64（R²=0.999）**（§8.1），
   buffer 内存 ∝ N³（N=20 需 26 GB，§9）。
   **而且是观测构造而不是物理仿真在驱动超线性**（§8.2b：物理是 N^0.90 的线性项）。
3. **表示层面**：share_obs 维度 O(N²)、critic 计算 O(N³)——
   但**实测 N 到 50，critic 单次前向仍是 0.6 ms**，GPU 利用率 0–11%，
   **完全没有成为约束**（§9）。
4. **学习层面**：归一化后 critic 的 `value_loss/N²`（0.448→0.638）与
   `grad_norm/N`（2.68→6.16）**确实在随 N 上升**（§11.2），
   这是目前唯一指向「表示/优化层面可扩展性」的实证信号。
   **但它有三个必须在答辩中同时说明的限制**：
   (a) 每个规模只有 1 个种子；
   (b) 只在 early-training（episode 0）取点；
   (c) 同一批运行的 `ratio ≈ 1.0000`、策略熵仍占最大熵的 97%–99.8%（§11.1b），
   即 **actor 本身几乎没动**，所以这个"critic 更难拟合"的信号
   也可能部分来自「critic 在追一个几乎不动的目标」这一平凡情形。
   **因此它仍是被标注为待确认的假设，不是结论。**
5. **协调层面**：team-mean 奖励使个体贡献按 1/N 衰减（设计问题，非 bug，§12）。
   实测代理量（§12.1）**没有观察到协调明显恶化**，但该测量有 3 个已知缺陷。

> **本报告明确不断言「10v10 学不会 = 证明了 curse of multiagency」。**
> 事实上本次实测显示 **10v10 到 27 万步确实还没有移动，但这不足以说明任何问题**
> （5 个 episode，每个约 17 分钟）。
> 目前能说的最严谨表述是：
> 「在固定的墙钟预算与 48 核约束下，**环境与内存成本先于算法成为瓶颈**
> （环境 ∝N^1.64 且由观测工程而非物理驱动；buffer 内存 ∝N³）；
> 在扣除奖励尺度后 centralized critic 的相对拟合误差随 N 上升，
> 但因 actor 本身移动极小、且每种规模只有单种子，**尚不能归因于算法层面的可扩展性失效**。」

---

## 14. Paper A Analysis

**完整精读见 `docs/scalable_marl_papers.md` §1、§3、§4。**
该文档由一个 17 agent 的工作流产出（每篇 5 个分页抽取 → 每篇合成 → 两篇对比 →
3 个对抗验证 agent（分别核查 A 的事实地基、B 的样本复杂度精确性、
概念正确性与完整性）→ 最终写作者），共提出 13 个问题，**3 个严重问题已修正并入正文**。

**论文 A**：Ma, Li, Du, Dong & Yang, *Efficient and scalable reinforcement learning
for large-scale network control*, **Nature Machine Intelligence 6** (2024),
doi:10.1038/s42256-024-00879-7。

核心（**它攻击的是"全局信息 / 中心化"，全文不用 "curse" 一词，用词是 scalability**）：

- **形式化**：networked MDP；agent $i$ 的 $\kappa$-hop 邻域 $N^\kappa_i$
  （图距离 ≤ κ 的节点，含自身）；**localized policy** $\pi_i(\cdot\mid s_{N^\kappa_i})$
  只依赖邻域与自身状态；**extended value** $V_i(s^{N^\kappa_i})$。
- **Theorem 3**（eq. 15, p.12）：$|V_i(s)-V_i(s^{N^\kappa_i})|\le \frac{r_{max}}{1-\gamma}\gamma^\kappa$
  —— 近似误差随 κ **指数衰减**。
- **Theorem 4**（eq. 17, p.12）：policy gradient 版本，
  误差 $\le \frac{\gamma^{\kappa-1}}{1-\gamma}\left[1-(1-\gamma^2)\frac{|N^\kappa_i|}{n}\right]r_{max}g_{max}$。
  **邻域占比是乘性因子，不是指数**（验证器据 SI §4.6 的推导确认了这一读法）。
- **方法**：localized model + extended value + **branched rollout**（Thm 2 把模型误差系数
  从 $\le\gamma/(1-\gamma)$ 降到 $\le\gamma(1-\gamma^T)/(1-\gamma)$）。
- **实验规模**：真实系统数百个 agent。
- **⚠️ 量级现实检验（对我们很重要）**：$\gamma^\kappa$ 在 $\gamma=0.99$ 时，
  要让误差降到 $0.1\,r_{max}$ 需要 **$\kappa\approx700$**。
  **"小的 κ 就够"绝不能当定理使用**，必须经验验证。

## 15. Paper B Analysis

**论文 B**：Shi, Gai, Mazumdar, Chi & Wierman,
*Breaking the Curse of Multiagency in Robust Multi-Agent Reinforcement Learning*,
arXiv:2409.20067v3（Caltech / PKU / CMU）。

核心（**它攻击的是"联合动作空间"的统计瓶颈**）：

- **curse of multiagency 的精确含义**：sample complexity 经联合动作空间
  $\prod_i|A_i|$ **随 agent 数指数增长**。
  ⚠️ **术语出处**：B **不是**这个术语的首创者（应归 Wang et al. 2023 COLT）。
- **设定**：distributionally robust Markov games；
  提出 **fictitious uncertainty set**（每个 agent 的不确定性集同时由环境和
  其他 agent 的**整体行为**决定），并证明 robust NE 与 robust CCE 的存在性。
- **算法**：**Robust-Q-FTRL** + adaptive sampling；其 robust Q 只定义在 $(s,a_i)$ 上，
  不确定性集把其他 agent 的行为**积分掉**。
- **Theorem 2**（p.12, eq. 26/30）：总样本数
  $\tilde O\!\left(\frac{S H^6 \sum_{i=1}^n A_i}{\epsilon^4}\cdot\min\{H,\;1/\min_i\sigma_i\}\right)$
  —— 对动作空间是 **$\sum_i A_i$ 线性，不是 $\prod_i A_i$**。
- **⚠️ 两点必须与结论一起引用**：
  1. 该 $\prod\to\sum$ 结果**只在其自己新引入的 RMG 类内成立**，
     B 在 p.4 footnote 1 **明确声明不可与先前工作直接对比**；
     标准 MG 的 $\sum$ 界早于 B（Li et al. 2023）。
  2. 依赖**生成模型（generative model）+ tabular + finite horizon + robust CCE**。
- **无实验、无代码**；常数 $C_1/C_2$ 未给数值。

## 16. Connection to LAG

**完整分析见 `docs/scalable_marl_papers.md` §5、§6。**

### 16.1 一句话结论

> **Paper A 管"信息"，Paper B 管"统计"——两者正交。**
> 而 **LAG 在 N-v-N 上实测到的所有超线性增长，全部落在 Paper A 的坐标系里，
> 没有一条落在 Paper B 的坐标系里。**

逐条对应（都是本机实测）：

| LAG 的增长点 | 阶数 | Paper A 的轴 | Paper B 的轴 |
|---|---|---|---|
| `obs_dim = 12N+3` | O(N) | ✅ | ❌ |
| `share_obs_dim = 24N²+6N` | **O(N²)** | ✅ | ❌ |
| critic 首层 MAC/env-step | **O(N³)** | ✅ | ❌ |
| share_obs replay buffer 字节 | **O(N³)** | ⚠️ 间接 | ❌ |
| JSBSim 物理仿真 | **O(N) 线性** | ❌ | ❌ |
| 观测构造（工程实现） | **O(N²)，每步两遍** | ⚠️ | ❌ |
| 联合动作空间 | 理论 $\prod\|A_i\|$，**MAPPO 未显式枚举** | ❌ | ⚠️ 概念相关但不可套用 |

### 16.2 最有价值的一条连接：**当前 LAG 的 κ = ∞**

Paper A 的局部性参数是 κ。把它套到 LAG 上：

> **`MultipleCombatTask.get_obs()` 对每个 agent 遍历 `partners + enemies`——
> 即全部其他飞机，与图距离无关。**

因此 LAG 现在实现的**不是**「局部观测 + 集中式 critic」，
而是 **「全局观测 + 全局 critic」**：每个 agent 拿到的是
一个含全部 N 个 agent 交互信息的稠密向量（`12N+3` 维），
而 critic 拿到的是 `24N²+6N` 维并**复制给每个 agent**。

这直接给出一个**可执行、可度量、且与 Thm 3 的形式一一对应**的实验
（见 §17 与 `docs/scalable_marl_candidates.md` 的 Candidate A），
但**今晚不实现**（用户 §29：不急于创新）。
**同时必须声明**：A 的定理前提（图结构已知、动力学可分解、局部模型）
在空战里都不成立，**不能声称有任何理论保证**。

### 16.3 为什么 Paper B 的方法不能拿来改 LAG

- MAPPO 的 actor 是 **factorized** 的：$\pi(a\mid o)=\prod_i\pi_i(a_i\mid o_i)$，
  **不显式枚举联合动作**，所以 $\prod|A_i|$ 不进入网络前向。
- LAG 里确实继承指数的组件是**集中式 critic 的输入维度**，
  但那是**状态空间**的拼接（O(N²)），属于 Paper A 的轴。
- B 的算法需要 **tabular + generative model + robust CCE**，
  与 LAG（连续高维状态、神经网络策略、self-play、非平稳对手）
  之间存在**不可跨越的差距**。

> **因此本报告明确声明：本晚的实验没有、也不可能验证 Paper B 的任何定理。
> B 对我们的价值是术语与诊断工具（∏ vs Σ 的分类学），不是可实现的算法。**
> 「我们用 LAG 验证了 Paper B」这类说法必须禁止。

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

按「应当先做什么」排序（**这一节是建议，不是今晚已做的事**）。
每条都注明它针对哪个已被实测确认的失效。

### P0 — 必须先做的三件事

1. **把预算提到可判断的量级。**
   实测：`2v2` 到约 **7.5e5 步**才出现明显 reward 抬升，
   而官方预算是 `1e8`。本次通宵每个作业只跑到 1e6 量级（**约 1%**）。
   → 在任何「学不学得会 / 哪个规模更好学」的结论之前，
   **先让每个规模至少跑到 5e6–1e7 步**。
   对应失效：§11.1b 的近均匀策略、§5.4 的自我修正。

2. **给每个规模至少 3 个种子。**
   当前 2v2 官方 1 个、3v3 1–3 个、5v5 0 个、10v10 1 个。
   实测 `official_2v2_noweapon_selfplay` 的 reward 在
   `+11.2 → -12.9 → +18.1` 之间摆动，说明单种子的跨 N 对比**毫无意义**。
   对应失效：§10.3、§11.2 的单点信号。

3. **修正评估协议：随机化初始态势。**
   实测 `MultipleCombatEnv.reset_simulators()` 不做任何随机化，
   因此**训练与评估都只在同一组初始条件下进行**（离线评估 std = 0.0）。
   注意正确的做法**不是**增加 eval episodes（那是同一个确定性交战），
   而是随机化初始状态——这也让 `MultipleCombat` 与原本就会 shuffle 的
   `SingleCombatEnv` 保持一致。
   对应失效：§5.1、§5.2。

### P1 — 拿到可信基线后立刻做

4. **观测构造去冗余（Candidate L）。**
   `get_state()` 每步把 `get_obs` 对全部 agent 重跑一遍
   （实测耗时相等：37.18 vs 36.95 ms @10v10，占整个 step 的 40%）。
   在同一步内缓存复用即可把观测开销减半。
   **这是工程修复，必须单独报告，绝不可与算法改进混算。**

5. **奖励归一化消融。**
   把 `PostureReward_scale` 从 15 改为 `15/N`（NoWeapon 家族），
   验证 §11.2 中 `value_loss/N²` 与 `grad_norm/N` 的残余上升
   是否由奖励尺度造成。**这是对现有结论最直接的证伪实验。**
   注意：这会改变基线配置，必须作为**消融**而非 baseline 报告。

6. **κ-局部化 sweep（Candidate A，直接检验 Paper A）。**
   把 `get_obs` 的邻居集合从「全部」改为「k 近邻 / 威胁邻域」，
   在 2v2/3v3/5v5/10v10 上扫 k。
   这是与老师 Paper A 对应最直接、且与实测失效 P2/P3/P5 最贴合的实验。
   **务必同时报告现实检验**：$\gamma=0.99$ 时 Thm 3 要求 $\kappa\approx700$
   才能把误差压到 $0.1\,r_{max}$，所以「小 κ 就够」是待验证的经验问题。

### P2 — 有价值但优先级较低

7. **在安静机器上重做环境吞吐基准**，彻底分离内在成本与争用成本
   （本次已记录 `quiet` 与 `loaded` 两组，但 `loaded` 组只有一次采样）。
8. **补 shoot 家族的 scaling**（2v2/3v3/5v5 已排队，需扩到 10v10）。
   注意保留 §16 的警告：`reward/N` 归一化对 shoot 家族**只是近似**。
9. **升级自博弈**：当前 `fsp`/`pfsp` 因 ELO 从不更新而都退化为
   **历史 checkpoint 均匀采样**（见 §5.3）。若要做真正的 FSP/PFSP，
   需要实现 `SelfplayAlgorithm.update()` 并用评估结果驱动 ELO。
10. **实现真正的目标分配观测**，替代当前以「最近敌机」作代理的协调度量
    （§12 的三个测量缺陷）。

### 不建议现在做的

- **不要把 Paper B 的 Robust-Q-FTRL 搬到 LAG**：设定差距不可跨越（§16.3）。
- **不要在观测还是 O(N²) 全局拼接的情况下先上 attention / graph**：
  先做 P0-4（去冗余）与 P1-6（κ 局部化），否则无法归因收益来自哪里。
