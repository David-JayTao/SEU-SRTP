# LAG 官方实验清单（Baseline Inventory）

负责人：刘酝潇
日期：2026-10-04
仓库：`David-JayTao/SEU-SRTP` @ `60a3e2d`（实验分支 `exp/repro-scaling-20261004`）
审计方法：逐个阅读 `scripts/*.sh`、`envs/JSBSim/configs/**/*.yaml`、`scripts/train/train_jsbsim.py`、
`runner/*.py`、`envs/JSBSim/envs/*.py`、`envs/JSBSim/tasks/*.py`，**全部结论以代码为准，不按名字猜测**。

---

## 0. 判定口径（很重要）

本项目中「官方实验」有三个层次，必须区分：

| 层次 | 定义 | 证据 |
|---|---|---|
| **L1 官方标准入口** | 仓库里存在可直接运行的 `scripts/*.sh` 启动脚本 | `scripts/` 下的 shell 文件 |
| **L2 官方配置，但无官方脚本** | `envs/JSBSim/configs/` 里有正式 YAML，任务类也存在，但仓库没有对应的 `.sh` | YAML + `load_task()` 分支 |
| **L3 不存在** | 代码里没有对应 task 分支或没有对应 YAML，必须自己构造 | — |

**本文档严禁把 L3 自我构造的实验包装成官方 baseline。**

---

## 1. 官方标准入口（L1）——共 6 个训练脚本 + 2 个非训练脚本

| # | Script | Environment | Scenario | Algorithm | Weapon | Self-play? | Eval? | 官方? |
|---|---|---|---|---|---|---|---|---|
| 1 | `scripts/train_heading.sh` | SingleControl | `1/heading` | ppo | 无 | 否 | 否 | ✅ L1 |
| 2 | `scripts/train_vsbaseline.sh` | SingleCombat | `1v1/NoWeapon/vsBaseline` | ppo | 无 | 否（对手是内置 baseline） | 否 | ✅ L1 |
| 3 | `scripts/train_selfplay.sh` | SingleCombat | `1v1/NoWeapon/Selfplay` | ppo | 无 | ✅ fsp | ✅ 1 局/轮 | ✅ L1 |
| 4 | `scripts/train_selfplay_shoot.sh` | SingleCombat | `1v1/ShootMissile/HierarchySelfplay` | ppo | **导弹** | ✅ fsp | ✅ | ✅ L1 |
| 5 | `scripts/train_share_selfplay.sh` | MultipleCombat | `2v2/NoWeapon/HierarchySelfplay` | **mappo** | 无 | ✅ fsp | ✅ | ✅ L1 |
| 6 | `scripts/render_heading.sh` | SingleControl | `1/heading` | ppo | 无 | 否 | 渲染 | ✅ L1（非训练） |
| 7 | `scripts/human_free_fly.sh` | SingleControl | `1/HumanFreeFly` | ppo | 无 | 否 | 人在回路 | ✅ L1（非训练） |
| 8 | `scripts/render_heading.sh` 引用的 `scripts/render/render_jsbsim.py` | — | — | — | — | — | 渲染 | ✅ L1（非训练） |

### 1.1 六个入口共用的超参数（逐字核对）

`train_heading.sh` / `train_vsbaseline.sh` / `train_selfplay.sh` / `train_selfplay_shoot.sh` /
`train_share_selfplay.sh` 的超参数完全一致：

```
--n-training-threads 1      --n-rollout-threads 32     --cuda
--log-interval 1            --save-interval 1
--num-mini-batch 5          --buffer-size 3000         --num-env-steps 1e8
--lr 3e-4  --gamma 0.99  --ppo-epoch 4  --max-grad-norm 2  --entropy-coef 1e-3
--hidden-size "128 128"     --act-hidden-size "128 128"
--recurrent-hidden-size 128 --recurrent-hidden-layers 1 --data-chunk-length 8
```

self-play 任务额外带：
`--use-selfplay --selfplay-algorithm fsp --n-choose-opponents 1 --use-eval --n-eval-rollout-threads 1 --eval-interval 1 --eval-episodes 1`

`train_selfplay_shoot.sh` 额外带 `--use-prior`（只有 `algorithms/ppo/ppo_actor.py` 实现了 prior，
**`algorithms/mappo/` 没有实现**，所以 prior 只能用于 1v1 的 ppo 路径）。

种子：heading=5，1v1 全部=1，2v2=0。

### 1.2b ⚠️ 「FSP」实际不是 FSP（**影响 baseline 的正确命名**）

官方脚本用的是 `--selfplay-algorithm fsp`。但读 `algorithms/utils/selfplay.py` 会发现：

```python
class FSP(SelfplayAlgorithm):
    @staticmethod
    def choose(agents_elo, **kwargs) -> str:
        return np.random.choice(list(agents_elo.keys()))      # 均匀随机，完全不用 ELO
    @staticmethod
    def update(agents_elo, eval_results, **kwargs) -> None:
        pass                                                  # 空函数
```

而且 `share_jsbsim_runner.py:356` 每次存 checkpoint 时写的是
`self.policy_pool[str(episode)] = self.all_args.init_elo` —— **所有历史策略的 ELO
都是同一个初值**，第 219 行还留着 `# TODO: use eval results to update elo`。

**结论**：

1. `FSP` 的 `choose` 是**对全部历史 checkpoint 的均匀随机采样**，
   与 ELO、与「最优反应」都无关。
2. `PFSP` 虽然公式里用了 ELO，但因为 ELO 从不更新，所有值相同，
   于是 `meta_solver_probs` 退化为均匀分布 —— **PFSP 也等价于均匀采样**。
3. 只有 `SP`（永远取最新策略）是真正不同的。

**因此本次实验对 self-play 的准确表述应当是**：

> 「MAPPO + **对历史 checkpoint 的均匀随机采样自博弈**」，
> 而不是「MAPPO + FSP」。

这不改变我们跑的是官方代码这一事实（我们用的就是官方 `--selfplay-algorithm fsp`），
但它改变了**我们如何描述这个 baseline**，也提醒我们：
仓库里名字叫 FSP 的东西**不是**博弈论意义上的 Fictitious Self-Play，
**不能拿它去和文献里的 FSP 结果做对比**。

### 1.2 ⚠️ 官方脚本中的两个缺陷（复现时必须记录）

| 缺陷 | 位置 | 后果 | 处理 |
|---|---|---|---|
| `--clip-params` 拼写错误 | 全部 6 个 `.sh` | `config.py` 里真名是 `--clip-param`；`train_jsbsim.py` 用 `parse_known_args`，未知参数被**静默忽略**，实际生效的是默认值 0.2 | 与默认值相同，**语义无变化**。我们的启动器显式传 `--clip-param 0.2` |
| `--use-wandb` 需要外部账号 | `train_selfplay.sh`、`train_selfplay_shoot.sh`、`train_share_selfplay.sh`、`train_vsbaseline.sh` | 服务器无 W&B 账号/网络时 `wandb.init` 会失败或挂起；且 `base_runner.py` 在 `use_wandb=True` 时把 `save_dir` 指向 `wandb.run.dir` | 我们的启动器**去掉 `--use-wandb`**。此时代码走官方非 wandb 分支，checkpoint 落到 `scripts/results/...`，与官方行为一致 |

---

## 2. 官方配置但无官方脚本（L2）

这些 YAML 是仓库正式提供的、`load_task()` 里有对应分支，但**没有官方 `.sh`**。
可以合法运行，但报告中必须注明「官方配置、非官方脚本」。

| # | Scenario | task | 飞机数 | 武器 | 说明 |
|---|---|---|---|---|---|
| 1 | `1v1/NoWeapon/HierarchySelfplay.yaml` | `hierarchical_singlecombat` | 2 | 无 | NoWeapon 的层次化版本（高层决策 + 底层 BaselineActor） |
| 2 | `1v1/NoWeapon/test/opposite.yaml` | `singlecombat` | 2 | 无 | 测试用 |
| 3 | `1v1/DodgeMissile/Selfplay.yaml` | `singlecombat_dodge_missile` | 2 | 导弹 | 只学躲弹，发射由规则控制 |
| 4 | `1v1/DodgeMissile/HierarchySelfplay.yaml` | `hierarchical_singlecombat_dodge_missile` | 2 | 导弹 | |
| 5 | `1v1/DodgeMissile/vsBaseline.yaml` | `singlecombat_dodge_missile` | 2 | 导弹 | `use_baseline=True` |
| 6 | `1v1/DodgeMissile/HierarchyVsBaseline.yaml` | `hierarchical_singlecombat_dodge_missile` | 2 | 导弹 | |
| 7 | `1v1/DodgeMissile/test/opposite.yaml`、`test/pursue.yaml` | 同上 | 2 | — | 测试用 |
| 8 | `1v1/ShootMissile/Selfplay.yaml` | `singlecombat_shoot` | 2 | 导弹 | 原始（非层次化）射弹 |
| 9 | `1v1/ShootMissile/HierarchyVsBaseline.yaml` | `hierarchical_singlecombat_shoot` | 2 | 导弹 | |
| 10 | `1v1/ShootMissile/HierarchySelfplay_nolimit.yaml` | 同上 | 2 | 导弹 | 「nolimit」= 放宽发射条件 |
| 11 | `1v1/ShootMissile/HierarchyVsBaseline_nolimit.yaml` | 同上 | 2 | 导弹 | |
| 12 | **`2v2/NoWeapon/Selfplay.yaml`** | `multiplecombat` | 4 | 无 | **2v2 非层次化版本**（动作空间是原始 4 维连续舵面，不是高层 3 维） |
| 13 | **`2v2/ShootMissile/HierarchySelfplay.yaml`** | `hierarchical_multiplecombat_shoot` | 4 | **导弹** | **2v2 + 导弹，task 分支存在、YAML 存在** |
| 14 | `1/HumanFreeFly.yaml`、`1v1/NoWeapon/HumanSingleCombat.yaml` | `HumanFreeFly` / `HumanSingleCombat` | — | — | 人在回路 |

### 2.1 关于「2v2 + ShootMissile」的明确结论

> **官方仓库没有提供 2v2 + ShootMissile 的官方启动脚本（无 L1 入口）。**
> 但是，它**不是我们凭空构造的**：`envs/JSBSim/configs/2v2/ShootMissile/HierarchySelfplay.yaml`
> 是仓库正式提交的配置，`MultipleCombatEnv.load_task()` 中有
> `taskname == 'hierarchical_multiplecombat_shoot'` 分支，任务类
> `HierarchicalMultipleCombatShootTask` 也完整实现。
> 因此正确表述是：**「官方配置 + 官方任务实现，但缺少官方标准脚本」**，
> 本次实验中我们用它跑，并标注为 L2。

---

## 3. 明确不存在的组合（L3）

以下组合**在官方仓库中没有任何入口**，本次实验**不**将其冒充为官方 baseline：

| 组合 | 结论 | 证据 |
|---|---|---|
| `2v2 + ShootMissile` 的 `.sh` 脚本 | ❌ 无官方脚本（但配置/任务存在，见 §2.1） | `ls scripts/` 仅 6 个 sh |
| 任意 `NvN`（N≥3） | ❌ 完全不存在 | `configs/` 只有 `1`、`1v1`、`2v2` 三个目录 |
| `MultipleCombat` + **ppo** | ❌ 不支持 | `share_jsbsim_runner.load()` 里 `if algorithm_name == "mappo" ... else raise NotImplementedError` |
| `SingleControl` / `SingleCombat` + **mappo** | ❌ 不支持 | `jsbsim_runner.load()` 同理只支持 ppo |
| 2v2 的 `vsBaseline` | ❌ 不存在 | 无 `2v2/*/vsBaseline.yaml`；`use_baseline` 只在 1v1 配置里出现 |
| 2v2 的 `MAPPO + PFSP` | ⚠️ 脚本只提供 `fsp` | `--selfplay-algorithm` 可选 `sp/fsp/pfsp`，但官方脚本只用 `fsp` |
| MultipleCombat + **DodgeMissile** | ❌ 不存在 | `MultipleCombatEnv.load_task()` 只有 3 个 task 分支 |

### 3.1 本次 N-v-N 扩展的定性（避免自欺）

本次新增的 `{2,3,5,10}v{N}/scaling_{noweapon,shoot}/HierarchySelfplay.yaml`
**是我们生成的**（见 `experiments/2026-10-04-night/scripts/gen_nvn_configs.py`），
**不是官方实验**。它们：

- 继承官方 2v2 模板的**全部** reward / termination / simulation 参数（逐字复制）
- 只改动 `aircraft_configs` 与新增 `num_agents` 键
- 采用「等间距一字排开、以战场经度为中心」的队形，间距恒为 0.01°（约 556 m @60°N）

因此任何跨 N 的差异来自**队伍规模**，而不是来自配置改动。
这一点必须在论文/答辩中明确声明。

> 注：为保持 2v2 的官方基线纯净，`official_2v2_noweapon` 使用的是**原版**
> `2v2/NoWeapon/HierarchySelfplay.yaml`；而 scaling 系列使用的是生成的
> `2v2/scaling_noweapon/`。两者仅差整个编队沿经度平移 0.005°（约 278 m），
> 间距相同。此差异已在报告中记录。

---

## 4. 官方实验的运行规模与预期输出

| 项目 | 官方值 | 说明 |
|---|---|---|
| `num_env_steps` | `1e8` | 向量化 env step 数（**不乘 agent 数**） |
| `buffer_size` | `3000` | 每轮 PPO 的 rollout 长度 |
| `n_rollout_threads` | `32` | 官方值；并行环境数 |
| episodes | `1e8 / 3000 / 32 = 1041` | 实际训练轮数 |
| checkpoint | `scripts/results/<env>/<scenario>/<algo>/<exp>/run<N>/actor_latest.pt`、`critic_latest.pt` | self-play 额外保存 `actor_<episode>.pt` |
| 日志 | stdout（FPS、average episode rewards、eval rewards） | 我们额外落盘 `metrics.jsonl` |

**实测吞吐（本机，仅供估算，详见 §5）**：官方 1e8 步在本服务器需要
**数百小时**，本次通宵不可能跑完。因此本次策略是：
所有官方入口都用**官方超参数**启动，用**时间上限**轮转，记录
`planned steps / completed steps / 当前趋势 / 预计剩余时间`，
而不是偷偷调小 `num_env_steps` 假装跑完。

---

## 5. 本机实测吞吐（RTX 4090D ×3，48 核）

单进程环境步进（`experiments/2026-10-04-night/scripts/env_bench.py`，随机动作）：

| 规模 | 飞机数 | obs_dim | share_obs_dim | env-steps/s (单核) | 每架飞机耗时 |
|---|---|---|---|---|---|
| 2v2 | 4 | 27 | 108 | 107.8 | 2.32 ms |
| 3v3 | 6 | 39 | 234 | 60.3 | 2.76 ms |
| 5v5 | 10 | 63 | 630 | 25.4 | 3.94 ms |
| 10v10 | 20 | 123 | 2460 | 7.8 | 6.39 ms |

端到端训练 FPS（含策略前向 + PPO 更新）：

| 任务 | threads | FPS |
|---|---|---|
| `official_heading` (SingleControl, ppo) | 10 | 582 |
| `official_2v2_noweapon` (MultipleCombat, mappo+fsp) | 12 | 239 |

**观察**：每架飞机的环境开销随 N 增长（2.32 → 6.39 ms），总开销约 ~O(N^1.7)，
原因是 `MultipleCombatTask.get_obs()` 对每个 agent 遍历其**全部** partner+enemy，
而 `BaseEnv.get_state()` 又对全部 agent 调用 `get_obs` 并 `hstack`，
使每步观测构造为 O(N²)。这是**表示/计算层面的可扩展性瓶颈**，
与 MARL 算法本身无关（详见 `docs/nvn_scalability_audit.md`）。

---

## 6. 本次实际执行的实验列表

见 `experiments/2026-10-04-night/manifest.csv` 与
`docs/overnight_repro_scaling_2026-10-04.md` §5/§7。

---

## 附录：2026-10-07 的一处修正（ELO 是否更新）

本文 §1.2b 写道「`policy_pool[str(episode)] = self.all_args.init_elo`，
**所有历史策略的 ELO 都是同一个初值**」。**该结论只对 MultipleCombat 成立。**
2026-10-07 逐 runner 复核后：

- `runner/share_jsbsim_runner.py:356`（MultipleCombat：2v2/3v3/5v5/10v10）
  确实写常量 `init_elo`（默认 1000.0），ELO 恒定；`PFSP` 因此退化为均匀分布。
  **本文原结论在此成立。**
- `runner/selfplay_jsbsim_runner.py:281`（SingleCombat：1v1）写的是
  `self.latest_elo`，且 `:254`/`:256` 在每次 eval 后更新对手与自身 ELO。
  实测日志 `f6m_official_1v1_selfplay_s1` 打印
  `elo gain: -0.173 | latest elo score: 1203.17`（初值 1000），**ELO 确实在更新**。
  **本文原结论在此不成立。**

**但 §1.2b 的核心结论不变**：两个 runner 的 `FSP.choose` 都是
`np.random.choice(list(agents_elo.keys()))`（`algorithms/utils/selfplay.py:43`），
对手选择与 ELO 无关。因此「MAPPO + 对历史 checkpoint 的均匀随机采样自博弈」
这一表述对两类任务都仍然准确；被修正的只是「ELO 从不更新」这一附带的机制说明。

方法学教训：本文的写法把由「share runner 的保存逻辑」得到的结论外推到了
另一个 runner。**跨 runner 的断言必须逐 runner 验证。**
