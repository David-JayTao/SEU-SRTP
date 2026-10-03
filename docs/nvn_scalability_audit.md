# LAG 2v2 → N-v-N 可扩展性代码审计

负责人：刘酝潇
日期：2026-10-04
仓库：`David-JayTao/SEU-SRTP` @ `60a3e2d`，实验分支 `exp/repro-scaling-20261004`
审计对象：`envs/JSBSim/**`、`runner/**`、`algorithms/**`

本审计回答两件事：
1. **代码层面**：现有实现能不能跑 N-v-N？哪些地方写死了？
2. **表示/计算层面**：obs / share_obs / critic 规模如何随 N 变化？公式是什么？

> **本审计严格区分「代码可扩展性问题」与「MARL 算法可扩展性问题」。**
> 本文件中发现的绝大部分限制属于前者——它们是工程约束，不是 curse of multiagency 的证据。

---

## 1. 结论速览

| # | 问题 | 结论 |
|---|---|---|
| 1 | agent 数是否硬编码 4？ | ✅ **是**——`MultipleCombatTask.num_agents` 原本 `return 4`。**已修复**为读取配置 |
| 2 | 红蓝是否默认各 2？ | 原本是（由硬编码 4 + `2v2/*.yaml` 共同决定）。现已由 `aircraft_configs` 决定 |
| 3 | team split 如何实现？ | 按 `uid[0]` 首字符分队（`env_base.load_simulator`），与 N 无关 |
| 4 | aircraft config 如何生成？ | 逐条读 YAML `aircraft_configs`，每条建一个 `AircraftSimulator` |
| 5 | observation 如何构造？ | 9 维 ego + 对每个 (partner+enemy) 6 维相对量 |
| 6 | obs 是否随 N 变化？ | ✅ **是，且线性增长**。这是本仓库最关键的扩展性事实之一 |
| 7 | share_obs 如何构造？ | `BaseEnv.get_state()` 对**全部** agent 调用 `get_obs` 再 `hstack`，然后**复制给每个 agent** |
| 8 | centralized critic 输入维度？ | `2N × obs_dim`，即 **O(N²)** |
| 9 | actor 输入是否随 N 变化？ | ✅ **是**——因为 local obs 本身含全局相对信息 |
| 10 | action space 是否随 N 变化？ | ❌ **否**，完全不变（这是 MAPPO factorized actor 的好处） |
| 11 | rollout buffer 是否支持 N？ | ✅ 是，全部 shape 由 `envs.num_agents` 推出 |
| 12 | recurrent hidden state 是否依赖 N？ | ❌ 否，每个 agent 独立 `(1,128)` |
| 13 | runner reshape 是否依赖 4？ | ⚠️ 依赖 `num_agents // 2`——**要求红蓝队伍等大** |
| 14 | reward 是否依赖 2v2？ | ⚠️ **PostureReward 对每个敌机求和 → 奖励幅度 ∝ N**（重要混淆因素） |
| 15 | termination 是否依赖 2v2？ | ❌ 否，`SafeReturn` 检查「所有敌人死亡」，通用 |
| 16 | self-play 是否支持 N-v-N？ | ✅ 是（经 `num_agents//2`），前提是队伍等大 |
| 17 | evaluation 是否支持 N-v-N？ | ✅ 是，同上 |
| 18 | render 是否支持 N-v-N？ | ✅ 是（`tacview` 路径通用；`renders/render_2v2*.py` 是硬编码 2v2 的独立脚本，不在训练路径） |
| 19 | missile 逻辑是否支持 N-v-N？ | ✅ 是（就近选敌），但**观测只编码 1 枚来袭导弹** |
| 20 | target selection 是否支持多敌机？ | ✅ 是：`argmin` 距离就近选目标 |

---

## 2. 唯一的代码硬编码点（已修复）

```python
# envs/JSBSim/tasks/multiplecombat_task.py  (原始)
class MultipleCombatTask(SingleCombatTask):
    @property
    def num_agents(self) -> int:
        return 4          # <-- 只支持 2v2
```

由于 `num_agents` 是**整条流水线唯一的规模来源**：

```
envs/JSBSim/envs/env_base.py :: BaseEnv.num_agents  ->  self.task.num_agents
envs/env_wrappers.py        :: ShareSubprocVecEnv.num_agents  ->  envs[0].num_agents
runner/share_jsbsim_runner.py :: self.num_agents = self.envs.num_agents
algorithms/utils/buffer.py  :: SharedReplayBuffer(..., num_agents, ...)
runner/share_jsbsim_runner.py :: buffer = SharedReplayBuffer(..., self.num_agents // 2, ...)
```

因此**只要放开这一个属性，buffer / runner / vec-env / 策略网络全部自动适配**。
这是本次改造只需要改一处代码的原因。

修复后：

```python
def __init__(self, config):
    self._num_agents_override = getattr(config, 'num_agents', None)
    super().__init__(config)

@property
def num_agents(self) -> int:
    if self._num_agents_override is not None:
        return self._num_agents_override
    return len(self.config.aircraft_configs)
```

注意 `_num_agents_override` 必须在 `super().__init__()` **之前**赋值，因为
`BaseTask.__init__` 会调用 `load_observation_space()`，而后者需要 `num_agents`。

---

## 3. 观测与集中式 critic 的维度公式（严格由代码推导）

### 3.1 局部观测

**NoWeapon**（`MultipleCombatTask.load_observation_space`）：
```python
self.obs_length = 9 + (self.num_agents - 1) * 6
```
`get_obs()` 中 `offset` 从 8 开始，对 `partners + enemies`（共 `num_agents-1` 个）
每个写 6 维：`[Δv_body_x, Δaltitude, AO, TA, R, side_flag]`。

$$\text{obs\_dim}_{\text{NoWeapon}}(N) = 9 + (2N-1)\cdot 6 = 12N + 3$$

**ShootMissile**（`HierarchicalMultipleCombatShootTask.load_observation_space`）：
```python
self.obs_length = 9 + self.num_agents * 6
```
多出的 6 维是**一枚**来袭导弹的相对信息（`check_missile_warning()` 只返回第一枚存活导弹）。

$$\text{obs\_dim}_{\text{Shoot}}(N) = 9 + 2N\cdot 6 = 12N + 9$$

### 3.2 share_obs（集中式 critic 输入）

```python
# envs/JSBSim/envs/env_base.py
def get_state(self):
    state = np.hstack([self.task.get_obs(self, agent_id) for agent_id in self.agents.keys()])
    return dict([(agent_id, state.copy()) for agent_id in self.agents.keys()])
```

两点关键：
1. 它是**所有 agent 局部观测的拼接** → 维度 = `num_agents × obs_dim`
2. 它**复制给每一个 agent**，即所有 agent 拿到完全相同的全局状态

$$\text{share\_obs\_dim}_{\text{NoWeapon}}(N) = 2N(12N+3) = 24N^2 + 6N$$
$$\text{share\_obs\_dim}_{\text{Shoot}}(N) = 2N(12N+9) = 24N^2 + 18N$$

### 3.3 维度表

| N | 总机数 | obs (NoWeapon) | share_obs (NoWeapon) | obs (Shoot) | share_obs (Shoot) | critic 首层参数 |
|---|---|---|---|---|---|---|
| 1 | 2 | 15 | 30 | 21 | 42 | 3,968 |
| 2 | 4 | **27** | **108** | 33 | 132 | 13,952 |
| 3 | 6 | **39** | **234** | 45 | 270 | 30,080 |
| 5 | 10 | **63** | **630** | 69 | 690 | 80,768 |
| 10 | 20 | **123** | **2460** | 129 | 2580 | 315,008 |
| 20 | 40 | 243 | 9,720 | 249 | 10,020 | 1,244,288 |
| 50 | 100 | 603 | 60,300 | 609 | 61,200 | 7,718,528 |
| 100 | 200 | 1203 | 240,600 | 1209 | 241,800 | 30,796,928 |

> 注：1v1（`SingleCombatTask`）的 obs 固定 15 维、**不随任何东西变化**，
> 因为它写死了 `enemies[0]` 和 `partners`（1v1 无队友）。这与 N-v-N 是两套不同的观测构造。

---

## 4. 计算与内存的可扩展性（实测量化）

### 4.1 环境步进成本（实测，单核，`env_bench.py`）

| 规模 | 飞机数 | sec/env-step | 每架飞机 | 相对 2v2 |
|---|---|---|---|---|
| 2v2 | 4 | 9.27 ms | 2.32 ms | 1.00× |
| 3v3 | 6 | 16.59 ms | 2.76 ms | 1.79× |
| 5v5 | 10 | 39.37 ms | 3.94 ms | 4.25× |
| 10v10 | 20 | 127.85 ms | 6.39 ms | 13.79× |

**每架飞机的成本本身在增长**（2.32 → 6.39 ms），说明总体成本**超线性**。
拟合：`(N/2)^1.6 ~ N^1.7`。原因明确且可定位：

- `MultipleCombatTask.get_obs()` 对**每个 agent** 遍历其**全部** `partners + enemies`（O(N) 次 `LLA2NEU` + `get_AO_TA_R`）
- `BaseEnv.get_state()` 对**全部 2N 个 agent** 各调用一次 `get_obs`（每步又来一次 O(N²)）
- `get_state()` 还要做一次 `hstack` 构造 `24N²+6N` 维向量，并**复制 2N 份**

所以在**任何一个 N**，每步的观测构造都是 O(N²)，而 `get_state` 使其在 step 中做了 **2 遍**。

### 4.1.1 逐项实测拆分（决定性证据）

`experiments/2026-10-04-night/scripts/obs_cost_profile.py` 把每个 env step 拆开测量：

| N | 机数 | `get_obs` 全部 agent | `get_state` | **JSBSim 物理仿真** | `env.step` 总计 | 观测占比 | 物理占比 | `get_state` 每 agent |
|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 1.98 ms | **2.02 ms** | 3.66 ms | 14.50 ms | 27.6% | 25.3% | 504 µs |
| 3 | 6 | 4.87 ms | 4.56 ms | 5.55 ms | 27.17 ms | 34.7% | 20.4% | 760 µs |
| 5 | 10 | 13.26 ms | 13.37 ms | 10.63 ms | 58.23 ms | 45.7% | 18.3% | 1336 µs |
| 10 | 20 | 37.18 ms | **36.95 ms** | 15.63 ms | 183.88 ms | **40.3%** | **8.5%** | 1847 µs |

三个可以直接下结论的事实：

1. **`get_state` 与「对全部 agent 再跑一遍 `get_obs`」耗时几乎相等**
   （1.98 vs 2.02；37.18 vs 36.95 ms）。这**证实**了 `get_state()` 内部确实
   重复了整份观测构造 —— 也就是说每步做了 **两遍完全相同的 O(N²) 工作**，
   第二遍是 100% 冗余的。
2. **物理仿真本身是线性的**：3.66 ms / 4 机 = 0.91 ms/机；
   15.63 ms / 20 机 = 0.78 ms/机。JSBSim 的积分成本随飞机数近似线性，
   **二次增长完全来自观测构造，不是物理**。
3. 到 N=10 时，**观测构造占整个 env step 的 40%，而物理仿真只占 8.5%**。

> **结论（可以写进论文的强表述）**：
> 「LAG 在 N-v-N 上的超线性成本，主要不是 JSBSim 物理仿真造成的，
> 而是观测/全局状态构造的工程实现造成的 —— 每步做了两遍 O(N²) 的冗余工作。
> 这是 `Computational / Representation scalability`，与 MARL 算法无关。」
>
> 对应的**纯工程优化**（本次未实施，保持官方实现以便公平复现）：
> 在同一步内缓存 `get_obs` 的结果并让 `get_state` 复用，
> 可把每步的观测构造成本直接减半；在 10v10 上约等于整体提速 20%。
> **若将来采用，必须声明它改变了基线实现，不得与算法改进混为一谈。**

> ⚠️ 注意这些绝对值是在机器**处于并发负载**时测量的，故高于 §4.1 的静默基准；
> 这里成立的结论是**各部分之间的比例**与**增长阶数**，不是绝对秒数。

### 4.2 centralized critic 的计算（实测 + FLOP 外推）

用真实 `PPOActor`/`PPOCritic` 类在 RTX 4090D 上实测（`critic_scaling_probe.py`）。

自博弈 ego 队每步的行数 = `n_rollout_threads × N`，因此 critic 首层
（`share_dim → 128`）的乘加次数：

$$\text{MAC/step}(N) = (T\cdot N)\cdot(24N^2+6N)\cdot 128 = O(N^3)$$

| N | 总机数 | share_obs | critic 首层参数 | 首层 MAC/env-step | 相对 N=2 | critic 前向/env-step（外推） | share_obs buffer |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 108 | 13,952 | 331,776 | 1× | 0.002 ms | 0.03 GB |
| 3 | 6 | 234 | 30,080 | 1,078,272 | 3.3× | 0.008 ms | 0.09 GB |
| 5 | 10 | 630 | 80,768 | 4,838,400 | 14.6× | 0.034 ms | 0.42 GB |
| 10 | 20 | 2460 | 315,008 | 37,785,600 | 113.9× | 0.265 ms | **3.30 GB** |
| 20 | 40 | 9,720 | 1,244,288 | 298,598,400 | 900× | 2.1 ms | **26.1 GB** |
| 50 | 100 | 60,300 | 7,718,528 | 4.63e9 | 13,956× | 32.5 ms | **404 GB** |
| 100 | 200 | 240,600 | 30,796,928 | 3.70e10 | 111,390× | 259 ms | **3,228 GB** |

buffer 计算：`(buffer_size+1) × n_rollout_threads × N × share_dim × 4 bytes`。
注意这里 `O(N^3)` 有两个来源相乘：**每行变宽 O(N²)** × **行数变多 O(N)**。

**但必须说清楚一个反面事实**：在 N ≤ 10 的实测区间，critic 单次前向耗时几乎恒定
（0.45–0.53 ms），因为 batch 也在同步变大，GPU 的并行度把它吸收掉了。
实测的**每 agent** critic 前向耗时反而随 N **下降**（0.0199 → 0.0038 ms）。
也就是说：

> **在当前 2v2–10v10 规模上，GPU 侧不是瓶颈，甚至远未饱和（利用率 0–11%）。
> critic 的 O(N³) 计算要在 N ≈ 20–50 才可能成为约束。**

真正的墙比计算来得更早：**share_obs replay buffer 的内存**。
N=10 已是 3.3 GB/进程，N=20 需要 26 GB，N=50 需要 404 GB。
（本机 1 TB 内存，所以 N=20 尚可，N=50 已不可能。）

### 4.3 actor 侧

actor 输入是**局部** obs，但本仓库的局部 obs 本身就含全部队友+敌机的相对量，
所以 actor 也无法免俗：

$$\text{actor 首层 MAC/step}(N) = (T\cdot N)\cdot(12N+3)\cdot 128 = O(N^2)$$

actor 参数量：`128 × obs_dim + 常数`，N=2/3/5/10 分别为
154,891 / 156,427 / 159,499 / 167,179（**增长很慢，因为只有第一层变宽**）。
critic 参数量：163,969 / 180,097 / 230,785 / 465,025（增长快得多）。

---

## 5. 其它需要记录的问题

### 5.1 奖励幅度随 N 线性增长（重要混淆因素）

```python
# reward_functions/posture_reward.py
new_reward = 0
for enm in env.agents[agent_id].enemies:          # <-- 对每个敌机求和
    AO, TA, R = get_AO_TA_R(ego_feature, enm_feature)
    new_reward += self.orientation_fn(AO, TA) * self.range_fn(R / 1000)
```

而所有 `2v2/*` 与 `NvN/scaling_*` 配置里 `PostureReward_scale` 都是 **15.0**。
于是：

- 2v2：对 2 个敌机求和 → 幅度 ~2×
- 5v5：对 5 个敌机求和 → 幅度 ~5×
- 10v10：对 10 个敌机求和 → 幅度 ~10×

**后果**：跨 N 的 reward 曲线**不可直接比较**。reward 的绝对值随 N 增长，
`value_loss` 的目标尺度也随之变化（实测 2v2 首次 `value_loss=1.74`）。
这不是算法变差，而是奖励设计没有做 N 归一化。

**处理**：报告中同时给出 reward 与 **reward/敌机数** 两条曲线，并明确声明这一点。
（官方自己也没有统一：1v1 NoWeapon 用 scale=100，1v1 Shoot/Dodge 和 2v2 用 scale=15，
说明这个尺度是逐场景手工调的，从未有人为 N>2 调过。）

### 5.2 团队奖励平均化（credit assignment 随 N 变难）

```python
# envs/JSBSim/envs/multiplecombat_env.py
ego_reward = np.mean([rewards[ego_id] for ego_id in self.ego_ids])
for ego_id in self.ego_ids:
    rewards[ego_id] = [ego_reward]
```

每个 agent 拿到的是**全队均值**。N 增大时，单个 agent 的行为对 team-mean 的
影响按 1/N 衰减——这是**真正的 coordination / credit-assignment 层面的扩展性问题**
（与代码 bug 无关），值得在报告里单独讨论。

### 5.3 导弹预警观测只有 1 个槽位

`check_missile_warning()` 返回**第一枚**存活的来袭导弹，`obs_length` 也只预留 6 维。
N 增大后来袭导弹数量增加，agent **无法感知同时来袭的多枚导弹**。
这是 shoot 变体在 N 上的**表示瓶颈**，且是设计层面的（不是 bug）。

### 5.4 `num_agents // 2` 假设队伍等大

`share_jsbsim_runner.py` 用 `obs[:, self.num_agents//2:, ...]` 切分 ego/opponent，
`warmup/insert/collect/eval/render` 全部如此。因此：

- ✅ 对称 N-v-N 可用
- ❌ **非对称（如 2v4）会静默错位**——不会报错，但会把不同队的 agent 混在一起
- 建议：若将来要做非对称，应改为按 `env.ego_ids` 长度切分，而不是 `num_agents//2`

### 5.5 其它小问题（不影响本次实验，但应记录）

| 位置 | 问题 | 影响 |
|---|---|---|
| `algorithms/mappo/ppo_policy.py :: copy()` | `PPOPolicy(self.args, self.obs_space, self.act_space, self.device)` 参数个数错误（缺 `cent_obs_space`），且方法从未被调用 | 潜在 bug，当前无影响 |
| `reward_functions/posture_reward.py` 顶部 | `from wandb import agent`——一个未被使用的误导入。若卸载 wandb 会导致 reward 模块导入失败 | 意外硬依赖 |
| `multiplecombat_task.py` 的 `torch.load(...)` | 未传 `weights_only=True`（`singlecombat_task.py` 传了）。torch≥2.6 默认 `weights_only=True`，行为依赖版本 | 版本敏感 |
| `test_env.py:43` | `assert envs.num_agents == 4` | 该测试对 N≠2 会失败（不影响训练路径） |
| `scripts/*.sh` | `--clip-params` 拼写错误，因 `parse_known_args` 被静默忽略 | 实际值与默认一致（0.2），无语义影响 |

---

## 6. 为 N-v-N 所做的全部改动

| 文件 | 改动 | 类型 |
|---|---|---|
| `envs/JSBSim/tasks/multiplecombat_task.py` | `num_agents` 由硬编码 4 改为读配置 | **必需**，唯一的功能性改动 |
| `envs/JSBSim/configs/{2,3,5,10}v{2,3,5,10}/scaling_{noweapon,shoot}/HierarchySelfplay.yaml` | 新增 7 个场景配置 | 新增数据，不改代码 |
| `runner/base_runner.py` | `log_info` 增加 `metrics.jsonl` 落盘 | **仅日志**，不碰任何算法量 |
| `experiments/.../scripts/run_train.sh` | 复现官方超参数的统一启动器 | 实验基础设施 |

**未改动**：MAPPO 算法、PPO 更新、GAE、网络结构、自博弈（FSP）、缓冲、奖励函数、终止条件。
因此 2v2 → 3v3 → 5v5 → 10v10 的对比是**同一套算法在同一个 pipeline 上跑不同规模**，
满足「不改变 MAPPO 核心算法」的要求。

---

## 7. 生成配置的公平性说明

`experiments/2026-10-04-night/scripts/gen_nvn_configs.py` 生成的 N-v-N 配置：

- reward / termination / simulation 参数**逐字继承**官方 `2v2/*/HierarchySelfplay.yaml`
- 只替换 `aircraft_configs`（并按 N 增加 `num_agents` 与 `team_size` 两个显式键）
- 队形：一字排开，间距恒为 0.01°经度（≈556 m @60°N），以战场经度 120.0 为中心
  - 红队纬度 60.0，航向 0（向北）；蓝队纬度 60.1，航向 180（向南）
  - 两队列间距恒为 0.1°纬度 ≈ 11.1 km
- **副作用**：正面宽度随 N 线性增长（2v2: 0.56 km；10v10: 5.0 km），
  即交战空间随 N 变大。这是为了保持**机间几何不变**而做的取舍，必须声明。

与官方 2v2 的差异：生成的 2v2 编队整体沿经度平移 0.005°（约 278 m），间距相同。
官方 2v2 基线仍使用**原版** YAML，不受影响。

---

## 8. 明确区分：哪些是代码问题，哪些不是

| 现象 | 归因 | 是不是 MARL 算法可扩展性问题？ |
|---|---|---|
| `num_agents` 写死 4 | **代码可扩展性** | ❌ 纯工程问题，已修复 |
| `num_agents // 2` 假设队伍等大 | **代码可扩展性** | ❌ 工程约束 |
| 观测构造 O(N²) | **计算/表示可扩展性** | ❌ 与算法无关 |
| share_obs 维度 O(N²)、buffer 内存 O(N³) | **表示可扩展性** | ⚠️ 是「集中式 critic」这一**设计选择**带来的，但不特定于 MAPPO |
| 每架飞机仿真成本随 N 增长 | **计算可扩展性**（JSBSim 模拟） | ❌ 仿真瓶颈，不是算法 |
| 奖励幅度 ∝ N | **实验设计问题** | ❌ 归一化问题 |
| team-mean 奖励稀释个体贡献 | **算法/信用分配** | ✅ **是**真正的协调可扩展性问题 |
| 导弹观测只有 1 槽 | **表示可扩展性**（设计限制） | ⚠️ 部分属于 |
| critic 拟合变难（若观测到） | **算法/学习可扩展性** | ✅ 才是 curse 相关 |

**只有最后两行的现象才可以在论文中与 curse of multiagency 挂钩。**
其余任何现象都必须先排除掉。
