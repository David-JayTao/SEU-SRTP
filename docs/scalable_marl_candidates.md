# 后续可扩展 MARL 候选方向分析

负责人：刘酝潇
日期：2026-10-04
依据：当晚实测数据（`experiments/2026-10-04-night/`）、
`docs/nvn_scalability_audit.md`、`docs/scalable_marl_papers.md`

> **本文件不替项目组做最终选择**，只对每个方向做**客观记录**：
> 它针对哪个已观测到的失效、需要改什么代码、理论依据是什么、
> 能做什么实验、难度与风险、能否泛化到 LAG 之外、与两篇论文的关系。
>
> **原则：先回答「现有 MAPPO 到底在哪坏」，再谈机制。**
> 本文件末尾的 §13 给出「哪条失效已被实测确认 / 哪条仍未确认」的对照表。

---

## 0. 当晚实测确认的失效清单（候选方向的靶子）

| 编号 | 失效 | 证据 | 类别 |
|---|---|---|---|
| **P1** | 观测构造 O(N²)，且**每步做两遍** | `obs_cost_profile`：`get_state` 与「对全部 agent 再跑一遍 `get_obs`」耗时相等（37.18 vs 36.95 ms @10v10）；到 N=10 占整个 env step 的 **40%** | Computational/Representation |
| **P2** | 局部观测不是局部的：`obs_dim = 12N+3` 含**全部**其他飞机 | 代码 + 维度测量 | Representation |
| **P3** | `share_obs = 24N²+6N`，且**复制给每个 agent** | 代码 + 维度测量 | Representation |
| **P4** | share_obs replay buffer **O(N³) 字节**，N=10 已 3.3 GB，N=20 需 26 GB | 实测 + 外推 | Computational |
| **P5** | 归一化后 critic 拟合仍在变难：`value_loss/N²` 0.448→0.638、`grad_norm/N` 2.68→6.16（2v2→10v10） | `normalized_scaling.csv`，matched stage | Learning |
| **P6** | team-mean 奖励使个体贡献按 **1/N** 衰减 | `multiplecombat_env.step()` 代码 | Coordination |
| **P7** | 导弹观测**只有 1 个槽位**（`check_missile_warning` 只返回第一枚） | 代码 | Representation |
| **P8** | 训练**无场景随机化**（初始态势固定），评估**确定性** | `MultipleCombatEnv.reset_simulators()` 不 shuffle；离线评估 std=0.0 | 实验方法学 |
| **P9** | 学习速度随 N 明显下降 | FPS 218→155→60（2v2/3v3/10v10） | Computational（已归因于 P1+P4） |

**注意 P9 的归因**：目前证据指向「计算成本」而非「算法失效」——
主进程在等待、GPU 空闲 0–11%。因此**任何以 P9 为靶子的算法方案，
都必须先证明收益超过 P1 的工程修复**。

---

## 1. Candidate A — Local / sparse centralised critic

| 维度 | 内容 |
|---|---|
| **Target failure** | P2, P3, P5 |
| **Motivation** | 把 `V_i(o_1..o_n)` 换成 `V_i(o_{N_i})`，`N_i` 只含与 i 相关的 agent。obs 与 share_obs 的维度都不再随 N 发散 |
| **Required code changes** | `MultipleCombatTask.get_obs()` 的邻居集合；`BaseEnv.get_state()` 改为按 agent 构造局部共享状态（目前它对所有 agent 返回同一份全局向量）；critic 输入维度随之变化。**不改 MAPPO 更新本身** |
| **Theoretical connection** | 直接对应 Paper A 的 localized policy `π_i(·|s_{N^κ_i})` 与 extended value `V_i(s_{N^κ_i})`；A 的 Thm 3 给出 `|V_i(s) − V_i(s^{N^κ_i})| ≤ r_max·γ^κ/(1−γ)` 的可检验预测 |
| **Expected experiment** | κ-sweep：κ = 1,2,3,…,∞（或 k = 1,2,3,5 近邻），在 2v2/3v3/5v5/10v10 上测 reward、obs_dim、FPS、critic loss。**预测**：κ 越小越快但性能先降后升存在最优 κ；κ=∞ 即当前 baseline |
| **Implementation difficulty** | **中**（观测构造与 critic 输入维度要一起改，且 self-play 的 `num_agents//2` 切分需同步；评估协议也要跟上） |
| **Risk** | 空战的「图」需要自行定义（距离/威胁/目标/导弹），选择本身可能比 κ 更影响结果；且 A 的定理前提（图已知、动力学可分解）在空战不成立，**不能声称有理论保证** |
| **Generalization beyond LAG** | 高——任何 agent 间可定义相似度/邻接的大规模 MARL 都适用 |
| **Relation to Paper A** | **主对应**：这就是 A 的核心思想在 LAG 上的最小落地 |
| **Relation to Paper B** | 弱。B 的「integration」是对**行为**的边际化，不是空间局部化，二者不同（见 papers 文档 §4(c)） |

---

## 2. Candidate B — Dynamic interaction graph

| 维度 | 内容 |
|---|---|
| **Target failure** | P2, P3（并提供 A 的图定义） |
| **Motivation** | 用**动态图** `G_t = (V, E_t)` 表示当前交互结构，边由 distance / threat / targeting / relative AO-TA / missile threat 决定，随战况变化 |
| **Required code changes** | 新增一个「邻居选择器」，在每一步为每个 agent 产出邻居索引；`get_obs` 消费它；需要缓存与向量化（否则选择器本身会引入 O(N²) 的新开销——**这是主要风险**） |
| **Theoretical connection** | Paper A 的 κ-hop 是**静态图距离**；动态图是它的推广。可对照 FPrint/ConsNet 等只依赖邻域信息的工作（Paper A 的 SI 中有对比） |
| **Expected experiment** | 固定 κ 下比较不同**图定义**（距离 vs 威胁度 vs 混合）；测量 reward 与「邻居集合的稳定性」 |
| **Implementation difficulty** | **中高**（不只是观测，还要保证选择规则的向量化效率） |
| **Risk** | 若邻居选择本身是 O(N²)，则**只换来了表示的可扩展性，没有换来计算的可扩展性**；必须实测选择器开销 |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A** | 强（把 κ-hop 从静态图推广到动态图） |
| **Relation to Paper B** | 弱 |

---

## 3. Candidate C — Dynamic grouping / hierarchical coordination

| 维度 | 内容 |
|---|---|
| **Target failure** | P6（协调/信用分配） |
| **Motivation** | 按空间/目标/威胁/角色动态分组：组内协调、组间聚合，把 1/N 的信用稀释换成 1/组大小 |
| **Required code changes** | 分组逻辑 + 组内 reward 聚合 + 组间信息通路。**会改变奖励与信用分配，因此不再是纯 baseline 复现** |
| **Theoretical connection** | 与 mean-field / 分层 MARL 相关，但**两篇指定论文都没有覆盖** |
| **Expected experiment** | 固定分组 vs 动态分组；测 team-mean 奖励下个体贡献的可辨识度 |
| **Implementation difficulty** | **高**（引入了新的学习结构，需要单独设计消融实验才能归因） |
| **Risk** | 分组规则本身可能是比算法更大的性能来源；容易变成「调参」而非「算法贡献」 |
| **Generalization beyond LAG** | 中（依赖任务有自然的分组语义） |
| **Relation to Paper A** | 弱 |
| **Relation to Paper B** | 弱 |

---

## 4. Candidate D — Attention / sparse attention

| 维度 | 内容 |
|---|---|
| **Target failure** | P2, P3, P7 |
| **Motivation** | 不是「attention 流行」，而是**选择相关 agent**、避免全局拼接。多头注意力天然处理「可变数量的邻居」与「每类实体一个槽位」 |
| **Required code changes** | actor/critic 的编码器从 MLP 换成 attention 编码器；输入从定长拼接改为「实体集合 + mask」。**这会改变网络结构，属于算法改动** |
| **Theoretical connection** | 与 Paper A 的局部化目标一致，但 attention 本身**不给出近似误差界**；A 的 γ^κ 界依赖的是图距离而非学出来的注意力权重 |
| **Expected experiment** | 固定参数量下比较 attention 编码器 vs MLP（在 N=2 上对齐参数量再放大 N） |
| **Implementation difficulty** | **中**（网络改动 + mask 处理；但与本仓库的 RNN 结构需要协调） |
| **Risk** | 注意力权重**可解释 ≠ 可证明**；需要额外实验证明它选中的确实是威胁邻居，否则只是「换了个更大的网络」 |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A** | 中（目标一致、机制不同、无定理） |
| **Relation to Paper B** | 弱 |

---

## 5. Candidate E — Graph critic（message passing）

| 维度 | 内容 |
|---|---|
| **Target failure** | P4, P5, P7 |
| **Motivation** | 用消息传递聚合局部交互，而不是拼接全局向量。相对 concat 的优势是**计算与内存随边数而不是节点数平方增长** |
| **Required code changes** | critic 换成 GNN；`share_obs` 不再需要 `24N²+6N` 的稠密向量，可换成 (节点特征, 边索引)。**这是最直接缓解 P4 内存墙的方案** |
| **Theoretical connection** | Paper A 的局部聚合思想；GNN 的 expressiveness 与 κ-hop 感受野直接对应（L 层 GNN ≈ L-hop） |
| **Expected experiment** | 在相同 κ 下比较 GNN critic vs MLP critic 的 value_loss、buffer 内存、FPS |
| **Implementation difficulty** | **中高**（要重写 critic 与 buffer 的存储格式；self-play 与 eval 路径都要跟） |
| **Risk** | 需要额外依赖（torch_geometric 或不必要的自研）；**只有当 N 足够大、内存墙真的出现时才值得**（当前 N≤10 时 GPU 未饱和、内存 3.3 GB） |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A** | 强 |
| **Relation to Paper B** | 弱 |

---

## 6. Candidate F — Value decomposition（VDN / QMIX / counterfactual critic）

| 维度 | 内容 |
|---|---|
| **Target failure** | P5, P6 |
| **Motivation** | 把团队价值分解为个体价值，缓解 team-mean 奖励的信用稀释；counterfactual baseline 提供 per-agent 优势 |
| **Required code changes** | 从 MAPPO（on-policy actor-critic）换成 value-based 分解方法，或者给现有 actor 加 counterfactual baseline。**前者是换算法族，后者改动可控** |
| **Theoretical connection** | 合作型 MARL 的经典路线；与两篇指定论文**都不直接对应** |
| **Expected experiment** | 现有 MAPPO + counterfactual advantage vs team-mean advantage |
| **Implementation difficulty** | 换族：**高**；只加 counterfactual baseline：**中** |
| **Risk** | LAG 是**竞争性**（红蓝对抗）而非纯合作，VDN/QMIX 的单调性假设针对的是合作团队——**需要小心论证适用性** |
| **Generalization beyond LAG** | 中 |
| **Relation to Paper A** | 弱 |
| **Relation to Paper B** | 弱（B 是 general-sum 但 tabular） |

---

## 7. Candidate G — Mean-field approximation

| 维度 | 内容 |
|---|---|
| **Target failure** | P2, P3, P4, P7 |
| **Motivation** | 大规模时不用显式建模所有其他 agent，而用 population statistics / mean action / local density 近似 |
| **Required code changes** | 观测构造改为「自身 + 邻居统计量」；critic 输入改为统计量 |
| **Theoretical connection** | mean-field MARL 文献；**两篇指定论文均未涉及**。注意与 Paper A 的区别：A 是**图局部化**，mean-field 是**分布近似**，两者可以叠加但不等价 |
| **Expected experiment** | 在 10v10/20v20 上比较 mean-field 聚合 vs 全局拼接 |
| **Implementation difficulty** | **中** |
| **Risk** | 空战是**高度异质**的（谁是威胁、谁在掩护判然不同），用均值可能抹掉关键信息，性能损失可能很大 |
| **Generalization beyond LAG** | 高（在**同质**大规模群体上最强） |
| **Relation to Paper A** | 中（同为降维局部化，机制不同） |
| **Relation to Paper B** | 弱 |

---

## 8. Candidate H — Parameter sharing + role embedding

| 维度 | 内容 |
|---|---|
| **Target failure** | P6 |
| **Motivation** | 当前所有飞机同构、共享 actor。未来引入 attacker / support / defender / scout 等角色，用 role embedding 区分 |
| **Required code changes** | 给 actor 加 role 输入；需要在 config 里定义角色并生成不同初始态势 |
| **Theoretical connection** | 无直接对应 |
| **Expected experiment** | 同构 vs 分角色的 5v5（需要先设计角色） |
| **Implementation difficulty** | **中**（但要先有「角色」这个任务设定，属于任务设计而非算法） |
| **Risk** | 当前 LAG 的 2v2 里没有角色语义，**在没有角色定义的场景上无法验证** |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A / B** | 弱 / 弱 |

---

## 9. Candidate I — Curriculum scaling（2v2→3v3→5v5→10v10）

| 维度 | 内容 |
|---|---|
| **Target failure** | P9 |
| **Motivation** | 不从零训练 10v10，而是从 2v2 学到的策略热启动，逐步扩规模 |
| **Required code changes** | **很小**：本仓库已支持 `--model-dir` 加载 checkpoint，只需让 N 变化时观测维度对齐的问题得到处理（不同 N 的 obs_dim 不同，**不能直接加载**） |
| **Theoretical connection** | 课程学习；论文均未涉及 |
| **Expected experiment** | 10v10 从零 vs 从 5v5 热启动（需要解决维度不匹配——见下） |
| **Implementation difficulty** | **低—中**，但有一个**硬障碍**：`obs_dim = 12N+3` 随 N 变化，**不同 N 的 actor 无法直接迁移权重**。这正是 Candidate A/D/E 要解决的问题——**只有先把观测变成与 N 无关（或定长 k-邻域）的表示，课程迁移才可行** |
| **Risk** | 若表示不变，Curriculum 在本仓库**根本做不了**；这是一个「依赖其他候选方向」的方案 |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A / B** | 弱 / 弱 |

> **这一条值得特别标注**：它揭示了一个结构性的耦合——
> **「与 N 无关的观测表示」是课程学习、迁移学习、以及跨规模实验的共同前提。**

---

## 10. Candidate J — Adaptive sampling

| 维度 | 内容 |
|---|---|
| **Target failure** | 样本效率（P9 中「学习慢」的部分） |
| **Motivation** | 借鉴 Paper B 的 adaptive sampling：不平均地探索所有交互，而是对**难对手 / 难场景 / 高威胁交互**加密采样 |
| **Required code changes** | 已有 `algorithms/utils/selfplay.py` 的策略池与 `SelfplayJSBSimRunner.reset_opponent()`，可在其中替换采样分布；场景采样需要先有场景随机化（当前没有，见 P8） |
| **Theoretical connection** | Paper B 的 Algorithm 1 用当前策略模拟其他 agent 并从生成模型中采样——**其理论保证依赖 generative model**，LAG 没有。因此只能借**思想**，不能借**保证** |
| **Expected experiment** | uniform 采样 vs PFSP（已有实现）vs 基于「难度」的采样；测达到同等 reward 所需 env steps |
| **Implementation difficulty** | **低**（self-play 侧改动小） |
| **Risk** | 容易退化成「调了个采样分布」，需要严格的 matched-budget 对比 |
| **Generalization beyond LAG** | 高 |
| **Relation to Paper A** | 弱 |
| **Relation to Paper B** | **主对应**（但只是思想层面，且 B 自己声明其界仅在其 RMG 类内成立） |

---

## 11. Candidate K — Model-based MARL（localized model + branched rollout）

| 维度 | 内容 |
|---|---|
| **Target failure** | 样本效率 |
| **Motivation** | 学局部动力学模型，用 model rollout 提高样本效率（Paper A 的核心之一） |
| **Required code changes** | 新增 `p̂_i`（局部模型）、branched rollout 采样器、以及 model error 的控制逻辑。**是本次清单里改动最大的一项** |
| **Theoretical connection** | Paper A 的主线：localized model + extended value + branched rollout，且有 model error 的复合误差分析 |
| **Expected experiment** | 先只在 2v2 上验证（对比 model-free 的样本效率），成功再谈放大 |
| **Implementation difficulty** | **高**（模型学习 + rollout 分支 + 误差控制，且 JSBSim 的高维连续动力学本身很难学） |
| **Risk** | JSBSim 动力学是**已知且精确的**——在本项目里学动力学模型的动机比 Paper A 的网络控制场景弱得多（A 的场景无法解析建模，LAG 的可以）。**这一点必须诚实评估** |
| **Generalization beyond LAG** | 高（但本项目内动机较弱） |
| **Relation to Paper A** | **主对应** |
| **Relation to Paper B** | 弱 |

---

## 12. 一个不在用户清单里、但**证据最强**的方向：Candidate L — 修复观测构造的冗余

| 维度 | 内容 |
|---|---|
| **Target failure** | **P1（实测证据最强：每步做了两遍 O(N²)，占 10v10 步时的 40%）** |
| **Motivation** | `get_state()` 对全部 agent 重复调用 `get_obs()`，在同一 step 内做了完全相同的 O(N²) 工作。缓存复用即可把观测开销减半 |
| **Required code changes** | **很小**：在 `BaseEnv.step()` 内缓存 `task.get_obs` 的结果，`get_state` 复用；或让 `get_state` 接收已算好的 obs 字典 |
| **Theoretical connection** | 无（纯工程） |
| **Expected experiment** | 改前/改后测 `obs_cost_profile` 的 `get_state_ms` 与 `full_step_ms`；预测 10v10 单步降低约 20% |
| **Implementation difficulty** | **低** |
| **Risk** | **低**，但必须声明：**这改变了基线实现**，不能与算法改进混为一谈；也应向上游提 PR 而不是只留在本仓库 |
| **Generalization beyond LAG** | 中（LAG 特定） |
| **Relation to Paper A / B** | 无 / 无 |

> **为什么单列它**：用户 §38 要求「先回答现有 MAPPO 到底在哪坏」。
> 实测数据显示，当前最大的单点浪费是**每步重复一遍 O(N²) 观测构造**。
> 在做任何算法创新之前，这 40% 里的一半应当先被拿回来。
> 否则任何「新方法更快」的结论都会被这个工程 bug 污染。

---

## 13. 客观对照表

| Candidate | Target | 证据强度 | 改动量 | 难度 | 与 A | 与 B | 泛化 |
|---|---|---|---|---|---|---|---|
| **L. 观测构造去冗余** | P1 | **强（实测）** | 极小 | 低 | — | — | 中 |
| **A. Local/sparse critic** | P2,P3,P5 | **强（维度实测）** | 中 | 中 | **主** | 弱 | 高 |
| **B. Dynamic graph** | P2,P3 | 中 | 中高 | 中高 | 强 | 弱 | 高 |
| **I. Curriculum scaling** | P9 | 中 | 小 | 低—中 | 弱 | 弱 | 高 |
| **J. Adaptive sampling** | 样本效率 | 中 | 小 | 低 | 弱 | **主** | 高 |
| **E. Graph critic** | P4,P5,P7 | 中 | 中高 | 中高 | 强 | 弱 | 高 |
| **D. Attention** | P2,P3,P7 | 中 | 中 | 中 | 中 | 弱 | 高 |
| **G. Mean-field** | P2,P3,P4,P7 | 弱—中 | 中 | 中 | 中 | 弱 | 高 |
| **F. Value decomposition** | P5,P6 | 弱—中 | 中/高 | 中/高 | 弱 | 弱 | 中 |
| **K. Model-based** | 样本效率 | 弱（本场景动机弱） | 高 | 高 | **主** | 弱 | 高 |
| **C. Dynamic grouping** | P6 | 弱 | 高 | 高 | 弱 | 弱 | 中 |
| **H. Role embedding** | P6 | 弱（无角色语义） | 中 | 中 | 弱 | 弱 | 高 |

### 仍未确认的失效

| 失效 | 状态 |
|---|---|
| P5（critic 拟合随 N 变难） | **单种子、early-training**，需 `queue_seeds` 的种子重复确认 |
| P6（1/N 信用稀释导致协调变差） | **仅代码推论**，本晚**未测量**协调指标（如重复攻击、目标分配冲突） |
| 「算法层面」的 scalability 失效 | **本晚证据不支持**：瓶颈在 CPU 环境与内存，主进程在等待、GPU 空闲 |

### 三条必须先说清楚的纪律

1. **P1 是工程冗余，不是算法问题**；不先修它，「新方法更快」的结论不可信。
2. **Paper B 不能用来实现 LAG 上的算法**（tabular + generative model + robust CCE），
   只能借「adaptive sampling / agent-wise treatment / 避免显式联合动作估计」的**思想**。
3. **Paper A 的定理在空战里没有前提保证**（图、可分解动力学、局部模型都不存在），
   但它的 **κ 局部化框架可以直接设计成实验**（Candidate A），
   并且是本清单中**与实测失效 P2/P3/P5 最直接对应**的方向。
