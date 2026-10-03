# 老师指定论文精读：可扩展 MARL 的两条路线

> 本文覆盖两篇指定论文：Paper A（网络化 model-based MARL，Nature Machine Intelligence 2024）与 Paper B（robust MARL / curse of multiagency，arXiv:2409.20067v3）。写作口径：严格区分 **定理（theorem）** 与 **经验主张（empirical claim）**；抽取文本本身有歧义、无法唯一确定的事实标"（待核实）"。源文件：`/root/autodl-tmp/SEU-SRTP/papers/text/paperA_network_control.txt`、`/root/autodl-tmp/SEU-SRTP/papers/text/paperB_curse_of_multiagency.txt`（Paper A 抽取文本含 NUL 字节，命令行检查需 `grep -a`）。

## 0. 一分钟结论

**两篇论文解决的不是同一种"维度灾难"，把它们合并成一句话一定会写错：**

- **Paper A 攻击"全局信息 / 中心化"瓶颈**：中心化学习要求每个 agent 拥有全局观测、要求全局 critic 与全系统信息共享，这在通信受限、成本受限、隐私受限的大规模网络中不可行。A 的解法是图局部性（κ-hop neighbourhood，近似误差随 κ 指数衰减 γ^κ）+ model-based 样本效率。它关心的量是"每个 agent 需要知道/传输/存储多少信息"。全文不使用 "curse" 一词，其用词是 **scalability**。
- **Paper B 攻击"联合动作空间"的统计瓶颈，即 curse of multiagency**：sample complexity 随 agent 数量经联合动作空间 ∏_i |A_i| 指数增长。B 的解法是虚构不确定性集（fictitious uncertainty set，把其他 agent 的行为积分掉）+ adaptive sampling，在 tabular robust Markov game 内把样本复杂度降到对 **Σ_i |A_i| 线性**。它是纯理论工作：无实验、无代码，常数 C1/C2 未给数值。

两条灾难**正交**：A 的 scale 变量是 κ 与图结构（状态/通信轴）；B 的 scale 变量是 n 与 |A_i|（动作统计轴）。核验事实（2026-10-04，对两份抽取文本）：Paper A 全文 0 次出现 "curse"；Paper B 全文 0 次出现 "commun*"——B 假设所有 agent 观测同一完整状态、从中心化 simulator 学习，完全不建模局部性与通信。因此：**Paper A 是 MAPPO 中心化 critic 的近亲（可直接设计实验去检验其主张）；Paper B 是精确术语与诊断词汇（∏ vs Σ）的来源，但其 ∏→Σ 结论属于它自己新引入的 RMG 类，B 在 p.4 footnote 1 明确声明不可与先前工作直接对比。** 术语出处也要注意：B **不是** "curse of multiagency" 的首创者（见 §2.2）。

## 1. Paper A 概览

### 1.1 完整引用与出处

Ma, C., Li, A., Du, Y., Dong, H. & Yang, Y. *Efficient and scalable reinforcement learning for large-scale network control.* **Nature Machine Intelligence** (2024). https://doi.org/10.1038/s42256-024-00879-7 。代码：https://github.com/CDM1619/Networked-MB-MARL 。页码约定：下文 p.x 为抽取文本的页标记（正文 pp.1–15；SI pp.19–43，对应补充材料内部页 1/24–24/24）。

### 1.2 问题背景 / 提出了什么问题

目标场景是大规模网络化系统的协同决策：自适应交通信号（New York 路网）、电网（Real Power-Net）、疫情干预、CACC。论文中心论点：**中心化信息共享不可行**，并从三类耦合成本展开 scalability 问题（论文没有给出它的形式化定义）：

1. **信息 / 通信**：p.1 "achieving comprehensive information sharing across the entire system becomes unfeasible"；且中心化信息收集增加隐私泄漏风险。
2. **计算 / 资源**：CPPO（Centralized PPO，学习全局 critic）理论性能好，但 "due to its dependence on large network size and computing resources, it is difficult to truly achieve theoretical optimal performance"；MAG（全局建模信息 + 全局 critic 的 model-based baseline）"high computational burden and poor scalability"，SI p.21 直说它 "is still essentially a centralized training method"。
3. **数据**：交互成本 "rises exponentially with the scale of the system"（p.1）；"high sample efficiency is also crucial yet unaddressed"（p.3）。

反向的极端——independent learning——"the learning process is unstable"（Fig. 1a caption, p.2）。论文还不接受先前工作的 "completely independent system"（INS）假设：SI p.22 说该假设 "considerably strong and not well-suited for the intricacies of real-world complex systems"，据此设计的算法 "lack scalability"，近似误差随 agent 数增长难以控制。它也点名批评 500+ agent 的先前工作靠 agent grouping 或 mean-field 近似，"The problem setting remains approximately centralized"（p.3）。

### 1.3 形式化设定

（pp.8–9, Methods）n 个 agent 位于**无向、平稳（stationary）图** G=(V,E)；networked MDP 为四元组 (G, {S_i, A_i}, p, r)：

- 每 agent 有局部状态 s_i ∈ S_i、局部动作 a_i ∈ A_i；全局状态/动作是拼接 s=(s_1,…,s_n)、a=(a_1,…,a_n)；状态转移 p(s'|s,a) 满足 Markov 性。
- 每 agent 的局部奖励 r_i(s_i, a_i) 只依赖自身状态与动作；全局奖励 = 平均：r(s,a) = (1/n) Σ_i r_i(s_i,a_i)。
- 目标（eq. (7)）：π_θ* = argmax_{π_θ} E[Σ_{t≥0} γ^t r(s_t,a_t)]，γ∈(0,1)；全局价值（eq. (8)）：V^{π_θ}(s) = (1/n) Σ_i V_i(s)。

**κ-hop neighbourhood**（p.9）：N^κ_i = 与 i 的图上距离 ≤ κ 的节点集合；N_i 为含自身的邻居；N^κ_{−i} = N^κ_i 去掉自身（抽取文本中集合差符号丢失，印成 "N^κ_{−i}=N^κ_i"，语义按定义确定）。"a larger κ implies a broader communication range"（p.2, Fig. 1 caption）；邻接矩阵 A "determined by the system structure and κ"（p.9）。

**local observation**：论文没有给编号定义；操作上等于自身与 κ-hop 邻居的状态 s^{N^κ_i}（依据 Algorithm 2 第 5 行 "Sample action according to decentralized π_θi and local observation s^{N^κ_i}"，p.11）。其合法性来自 locality：拓扑距离越远、影响越小（p.10，引文 [41,70]；SI 的 Ring Attenuation 实验印证）。

**localized policy**（p.9）：π_θi(a_i|s_Ni)，"dependent on only states of its neighbours and itself"，参数 θ_i；联合策略 π_θ(a|s) = ∏_i π_θi(a_i|s_Ni)。注意条件集差别：**policy 用 1-hop 的 s_Ni，而 extended value 与 localized model 用 κ-hop 的 s^{N^κ_i}**。

### 1.4 核心方法

1. **Extended value function**（eq. (1), p.3）：V_i(s^{N^κ_i}) = E_{s^{N^κ_{−i}}}[ Σ_{t≥0} γ^t r_i^t | s_0^{N^κ_i}=s^{N^κ_i} ]——只以 κ-hop 邻域状态为条件，对其余状态取期望；论文断言它 "is a good approximation of V_i(s)"，误差随 κ 指数衰减（定理见 §1.5）。实现上用邻居平均估计 Ṽ_i = (1/n) Σ_{j∈N^κ_i} V_j(s^{N^κ_j})（eq. (4), p.3）构造 advantage（分母取 n 而求和跑遍 N^κ_i，抽取中可能 OC 掉了 |N^κ_i|，待核实；同一量在 Theorem 4 展示处也有 V_j(s^{N^κ_i}) 与 V_j(s^{N^κ_j}) 两处不一致，建议写作时沿用 eq. (4) 的 N^κ_j 形式并注明）。
2. **Localized model**（p.5）：每 agent 用本地数据训练动力学模型，输入为自身动作与 κ-hop 邻居状态，预测下一步局部状态（与奖励）；损失为 MSE：L(ψ_i) = (1/|B|) Σ_{τ∈B} ‖ŝ_{i,τ+1} − s_{i,τ+1}‖²（eq. (6)）。SI §3.1 说明其 graph network 架构 "inherently approximates networked MDPs"，训练流程含真实数据 warm start、控制虚拟数据占比、真实-虚拟差异的自监督校正，"model fitting and strategy improvement are alternating"。
3. **Decentralized PPO + 邻域通信**：actor/critic/model 全部去中心化（无全局 critic），初始化由 κ 构造的邻接矩阵 A 决定（Algorithm 2 line 3）；critic 用邻居平均价值估计代替全局价值。
4. **Branched rollout**（p.5）：模型 rollout 不从初始状态出发，而是从最近真实轨迹 τ 中**随机抽一个状态**出发、固定长度 T；目的是抑制 compounding model error（p.5），该设计有定理层面的收益（§1.5）。

### 1.5 理论结果（严格的定理；Theorem 3 / Theorem 4 按核验后的形式给出）

- **Theorem 3**（eq. (15), p.12）：|V_i(s) − V_i(s^{N^κ_i})| ≤ r_max/(1−γ) · γ^κ。extended value 与真实价值之差随 κ 指数衰减。
- **Remark 1**（eq. (16), p.12）：全局价值同理被邻居平均近似，|V(s) − (1/n) Σ_i V_i(s^{N^κ_i})| ≤ r_max γ^κ/(1−γ)。
- **Theorem 4**（eq. (17), p.12；policy gradient 的局部近似误差界）：

  **|g_i − g̃_i| ≤ γ^{κ−1}/(1−γ) · [1 − (1−γ²)·|N^κ_i|/n] · r_max · g_max**

  其中 Â_t 为 TD residual，g_i = E[Â ∇_{θi} log π_i(a|s)] 为真实 policy gradient，g̃_i 为把 V 换成邻居平均估计后的梯度。**注意：邻域占比 |N^κ_i|/n 在此式中是乘性因子（取值 0→1 时方括号从 1 降到 γ²），不是指数**——主文式 (17) 的扁平排版不足以单独判定，但 SI §4.6 的推导唯一确定此读法（两段误差相加：f·γ^{κ+1} + (1−f)·γ^{κ−1} = γ^{κ−1}[1 − (1−γ²)·f]，f = |N^κ_i|/n；写成指数还会反转单调性，与"占比越大误差越小"自相矛盾）。因此误差随 κ 指数衰减，并随邻域占比增大而进一步下降。
- 其他形式结果（支撑方法设计）：**Theorem 1**（vanilla rollout 的回报差界）；**Theorem 2**（T 步 branched rollout：ε_mi 的系数从 ≤ γ/(1−γ) 降为 ≤ γ(1−γ^T)/(1−γ)；T=0 退化为 model-free 界）；**Corollary 1**（ξ-dependent 系统在 Theorem 2 上加 2 r_max γ ξ/(1−γ)² 项）；**Definitions 1–2**（INS 与 ξ-dependent system, p.10）；eq. (10)（η[π] ≥ η̂[π] − C 的单调改进条件）；eq. (12)（D(p||p̂) ≤ D(p||p̄) + D(p̄||p̂)，dependency bias 分解）。
- **量级提醒（经验上极重要）**：γ^κ 意味着 γ≈1 时要使误差 ≤ ε 需要 κ ≈ ln(1/ε)/(1−γ) 量级。LAG 空战常用 γ=0.99，10% 误差对应 κ 数百——"小的 κ 就够"绝不能当定理使用，必须经验验证（A 自己的 κ=1–2 配置与 κ 最优值 3/4 均为经验观测）。另注意 p.5 的 κ 消融（预测误差随 κ 增大，受网络拟合能力限制）与 p.6 归于 Thm 3/4 的表述（更大的 κ → 更低模型误差）在印刷文本中存在张力，属作者解读层面。

### 1.6 实验规模

- 交通：New York 路网，**最多 436 个可控制路口**（Fig. 5 一处图注印 432，正文与 SI 印 436，待核实）；电力：322-bus（22 agents）与 421-bus（**199 agents**）；疫情：500–10,000 人的 society；CACC。讨论声称可扩展到 "hundreds of agents"（p.8）。
- baseline：CPPO / DPPO / IMPO / MPOna / MAG；κ 消融与 rollout 长度消融（1/25/50/100/200）。
- 通信成本声称仅为中心化方法的约 5–35%（p.5；大规模真实任务约 10%，SI p.30）——**经验主张**。
- 全部实验统计 n = 5。

### 1.7 局限

- 理论依赖 INS / ξ-dependent 假设（Definitions 1–2, p.10）；实验系统"具有 ξ-dependent 性质"只是断言，ξ 仅在 CACC（≈0.2）与 Real Power-Net（≈0.8）被经验估计（SI §3.3），且抽取文本中这两处不等式方向疑似印反（应为 ≤ 却印成 ≥，待核实）。
- Theorem 1–2 中的 |N_i^k| 在抽取文本中未见定义；Theorem 4 中占比 |N^κ_i|/n 的定义也较松散（其乘性角色由 SI 代数确定，见 §1.5）。
- 印刷/抽取不一致：eq. (4) 的分母；eq. (17) 的展示式；436 vs 432；"converging within 1 × 10−5 training steps"（p.5）与图轴（Step ×10⁴ 至 ~20）矛盾，疑为 OCR 掉字（应为 1×10⁵，待核实）。
- 无 sample-complexity / 通信下界；界中的常数未量化、未数值验证；"experimental results are consistent with the theoretical results" 是作者解读。
- p.5 引用了 Algorithm 3 但抽取文本中不存在该算法框；Theorem 2 展示式无编号。

## 2. Paper B 概览

### 2.1 完整引用

Laixi Shi, Jingchu Gai, Eric Mazumdar, Yuejie Chi, Adam Wierman. *Breaking the Curse of Multiagency in Robust Multi-Agent Reinforcement Learning.* **arXiv:2409.20067v3 [cs.LG]**, 31 Jan 2025（2024-09 初版，2025-01 修订）。页码 = PDF 页 1–58。源文件：`/root/autodl-tmp/SEU-SRTP/papers/text/paperB_curse_of_multiagency.txt`。

### 2.2 "curse of multiagency" 的精确含义（含术语出处）

论文没有给编号定义，但给出了可引用的表述（p.3）：**"the sample complexity requirement scales exponentially with the number of agents (induced by the exponentially growing size of the joint action space)"**。在本文献中它被操作化为 sample complexity 里的 ∏_i |A_i| 因子；"打破"它 = 用对 Σ_i |A_i| 的多项式（此处为线性）依赖替换该乘积。

**术语出处（重要，勿误引）**：B **不是**这个术语的首创者。它使用既有词汇，其 related work 引用的先行工作已包括 Wang, Liu, Bai & Jin 的 *Breaking the Curse of Multiagency: Provably Efficient Decentralized Multi-Agent RL with Function Approximation*（COLT 2023），以及标准 MG 中通过 adaptive sampling "成功打破"它的 Jin et al. 2021、Bai & Jin 2020、Song et al. 2021、Li et al. 2022/2023。引用时**应以 Wang et al. 2023（COLT）与标准 MG 线为术语出处，引 B 作为 robust MG 扩展**。

**可比性警告（B 论文自己的声明，引用时必须带上）**：B 引入的是新 RMG 类（fictitious / others-integrated (s,a_i)-rectangularity），其 p.4 footnote 1 明说 "the sample complexity results in this work cannot be directly compared to those in prior studies"；先前的 ∏ 界（eq. (2)）属于不同的 (s,a)-rectangular 类，B 的 Table 1 仅供 "reference"。且标准 MG 的 ∏→Σ 结果早于 B（B 自己的 eq. (1)：Li et al. 2023 的 O~(H⁴ S Σ_i A_i / ε²)）。因此 ∏ vs Σ 应作为**词汇与诊断工具**使用，不能写成"B 相对先前工作的同类 head-to-head 突破"。

### 2.3 形式化设定与全部假设

1. **Finite-horizon、tabular、general-sum MG**：有限状态 S、有限动作 A_i（A = A_1×…×A_n）；每个 agent 有自己的奖励 r_{i,h}(s,a) ∈ [0,1]（一般和，不假定共同奖励）；所有 agent 观测**同一完整状态**（full observability）；只考虑 Markov policy；H 步有限时域。
2. **Robust 不确定性集**：真实转移核仅知位于 nominal kernel P⁰ 的 TV 球内（半径 σ_i ∈ (0,1]）；论文使用新的 "fictitious" 不确定性集，满足 **others-integrated (s,a_i)-rectangularity**（Definition 1, eq. (12)）：把其他 agent 的行为按参考策略积分掉（reference kernel, eq. (11)）。
3. **数据访问**：generative model 可在任意 (h,s,a) 从 **nominal** kernel 抽 i.i.d. 样本（eq. (14)）——**不是** worst-case 样本。nominal kernel 本身**未知**，算法把经验不确定性集中心放在估计核 P^k 上（eq. (18) 中 inf 在 U^{σ_i}(P^k_{i,h}) 内取）；实现是中心化 simulator。写作时不要说"已知 nominal kernel"。
4. **目标解概念**：ε-robust CCE（gap_CCE ≤ ε，eq. (8)/(15)）。不是 NE：general-sum MG 中学 NE 一般需要指数样本复杂度（p.4–5），robust NE 只有存在性（Theorem 1）而没有可学习算法的保证。
5. **参数区域**：σ_i ∈ (0,1]，ε ≤ sqrt(min{H, 1/min_i σ_i})，δ ∈ (0,1)，成功概率 ≥ 1−δ；N、K 满足 eq. (26)。
6. **只考虑 transition kernel 不确定性**；reward uncertainty 明确省略（p.7）。

### 2.4 主要算法：Robust-Q-FTRL

（Algorithm 2, p.13；设计于 pp.10–12；受标准 MG 的 Q-FTRL 启发）按 h=H,…,1 反向进行，每步 K 个 online iterations：

1. **Adaptive N-sample estimation**（Algorithm 1; eqs. (16)–(17), p.11）：对每个 agent i 与每个 (h,s,a_i)，采 N 个样本，其中**其他 agent 的动作从它们当前的策略 π^k_{j,h}(·|s) 模拟**，得经验 reward 与经验 kernel。这是避免枚举 joint action 的结构关键：采样与估计都按 (s,a_i) 进行，复杂度随 Σ_i A_i，而不是 ∏_i A_i。
2. **Robust Q estimate**（eq. (18), p.11）：q^k_{i,h}(s,a_i) = r̂^k_{i,h}(s,a_i) + inf_{P ∈ U^{σ_i}(P^k_{i,h})} P·V̂^k_{i,h+1}。无闭式、需内层优化；论文用 strong duality 化为对偶问题并配 clipping 求解（eqs. (19)–(20)）。
3. **移动平均**：Q^k = (1−α_k) Q^{k−1} + α_k q^k（p.11 正文与 Algorithm 2 step 8；eq. (21) 只定义学习率：α_k = c_alpha·log K / (k−1 + c_alpha·log K)，c_alpha ≥ 24，为 "rescaled linear learning rates"）。
4. **FTRL 策略更新**（eq. (22), p.12）：π^{k+1}_{i,h}(a_i|s) ∝ exp(η_{k+1} Q^k_{i,h}(s,a_i))，η 由 α_k、log K、H 决定。FTRL 的 no-regret 性质用于控制 online learning 误差项（附录 A.3 重述 FTRL regret bound）。
5. **Variance-style optimistic bonus**（eq. (23)）与价值估计（eq. (25)：V̂^k_{i,h}(s) = min{ Σ_k α^K_k ⟨π^k, q^k⟩ + β^k_{i,h}(s), H−h+1 }）。
6. **输出**：对 K 个迭代策略的加权混合分布 ξ̂，权重为 α^K_k（见 Algorithm 2 输出行、eqs. (23)/(25) 与附录 eqs. (36)–(41)；印刷的 eq. (24) 写作 ξ_h(π^k_h):=α_k，掉了上标 K，属排版遗漏）。FTRL 的 no-regret + 混合输出正是"ε-robust CCE"的来源。

**Adaptive sampling 作用的准确定位**：论文没有给 adaptive sampling 的形式化定义，也没有消融；其收益嵌在 Algorithm 1/2 与证明之中，保证只针对完整算法（Theorem 2）。

### 2.5 样本复杂度定理（精确表述）

**Theorem 2（Upper bound, p.12；eq. (26)）**：在 TV 不确定性集（eq. (13)）下，对任意 δ∈(0,1)、任意 σ_i∈(0,1] 的 fictitious RMG，当

- N ≥ (C1·H²/ε²) · min{ 1/min_{1≤i≤n} σ_i , H }，
- K ≥ C1·H³/ε²，

Algorithm 2 以概率 ≥ 1−δ 输出 ε-robust CCE ξ̂；等价地，总样本数

**N_all := H·K·N·S·Σ_{i=1}^n A_i ≥ (C1²·H⁶·S·Σ_i A_i / ε⁴) · min{ H, 1/min_i σ_i }**，

即 headline 形式（eq. (30), p.14）：**O~( S·H⁶·Σ_{i=1}^n A_i / ε⁴ · min{ H, 1/min_{1≤i≤n} σ_i } )**。

动作空间依赖是**对 Σ_i A_i 线性**——没有 ∏_i A_i。两点注意：(i) min{H, 1/min_i σ_i} 是**分子上的乘性因子**（σ_i 越小因子越大，最大到 H）；扁平抽取中该因子位置有歧义，已用 arXiv v3 HTML 与内部一致性 N_all = H·K·N·S·Σ A_i 确认。(ii) 对 H、ε 的依赖（H⁶、ε⁴）不是紧的（见 §2.6）。

### 2.6 下界 / 难度结果

存在形式下界（eqs. (27)–(29), p.13），但它**不证明联合动作乘积不可避免**——相反，它的动作空间依赖是 **max_{1≤i≤n} A_i**，与"Σ/max 型多项式依赖"相容：

- 在 σ_i ∈ (0, 1−c1]（0 < c1 ≤ 1/4）、H > 16 log 2、ε 满足 eq. (27) 的限制下，存在一类 fictitious RMG，使任意 estimator 在 N_all ≤ (C2·S·H³·max_i A_i / ε²) · min{ H, 1/min_i σ_i } 时，最坏情形失败概率 ≥ 1/8（eqs. (28)–(29)）。
- **出处与限制**：它由"除一个 agent 外其余 A_j=1"的实例归约到单 agent robust MDP（(s,a)-rectangularity），再直接引用 Shi et al. (2024, Theorem 2)，属承袭而非本文自证。
- **遗留 gap**：上界 Σ_i A_i vs 下界 max_i A_i 的差距论文未讨论；H⁶ vs H³、ε⁴ vs ε² 的差距被承认（p.14）。另外，general-sum MG 学 NE 需指数复杂度的结论是**引用**（p.5），非本文证明。

### 2.7 局限

- **纯 tabular**：无 function approximation 保证（linear FA 只出现在标准 MG 的先行工作里）；无连续状态/动作空间；**无 deep RL、无实验、无代码**。
- "regardless of the uncertainty set formulation / definition"（p.1 / p.4 / p.14）三处声称**只对 TV 被定理支持**：Theorem 2 与下界都仅对 TV 球成立，KL / χ² / Wasserstein 没有任何定理覆盖。
- reward uncertainty 省略；robust NE 只有存在性；无运行时/计算成本分析；常数 C1（大）、C2（小）无数值；学习对象是 K 个策略的分布（ε-robust CCE），而非可部署的单一策略。
- "adaptive sampling" 无正式定义、无消融；保证只针对完整算法。

## 3. 两篇论文对比表

| 维度 | Paper A — Networked MB-MARL（Ma et al., NMI 2024） | Paper B — Robust-Q-FTRL（Shi et al., arXiv:2409.20067v3） |
|---|---|---|
| 问题 | 大规模网络系统的可扩展协同控制：在通信/隐私/计算受限下，不依赖全局信息仍要可扩展。 | distributionally robust Markov game 中的样本有效均衡学习：打破 ∏_i A_i 的指数依赖。 |
| Scalability 定义 | 无形式定义；三类耦合成本：全局信息共享不可行 + 隐私（p.1）、计算/全局 critic 负担（p.5）、交互成本随规模指数增长（p.1）。交付物：κ-hop 局部性，误差 γ^κ（Thm 3/4）。 | 形式化核心：sample complexity 随 agent 数指数增长，源于指数增长的联合动作空间（p.3）。术语非 B 首创（Wang et al. 2023 COLT 等）；B 的 ∏→Σ 属其新 RMG 类，不可与先前类直接对比（footnote 1, p.4）。 |
| 环境设定 | n 个合作 agent、无向平稳图 G=(V,E)；networked MDP；局部状态/动作、Markov 核、r_i(s_i,a_i)、全局奖励=平均；INS/ξ-dependent 结构；NN 学动力学（连续向量仿真）。 | 有限时域、tabular、general-sum MG；有限 S、A_i；全观测共享状态；TV 球 fictitious 不确定性集，围绕**未知** nominal kernel（仅能经 generative-model sampler 从 nominal 采样；经验集中心在估计核 P^k，eq. (18)）。 |
| Agent 结构 | 同质合作 agent，由拓扑耦合；每 agent 自己的 model/policy/value；去中心化执行；κ 是设计旋钮。 | n 个各自有奖励的 agent；中心化 simulator 学习；解概念 = ε-robust CCE；robust NE 存在（Thm 1）但不学。 |
| 状态表示 | 全局状态可拼接，但学习/推理是局部的：policy 条件 1-hop s_Ni，model/value 条件 κ-hop s^{N^κ_i}；由静态网络中影响指数衰减论证（Ring Attenuation）。 | 完整共享状态 s 被每个 agent 观测；tabular 枚举；无局部性、无部分观测。 |
| 动作表示 | per-agent a_i ∈ A_i；joint action = 拼接；动作空间大小不进入任何界。 | 有限 A_i；joint A = ×_i A_i 是祸首；界含 Σ_i A_i（Thm 2）而非 ∏_i A_i（eq. (2) 的先前界）。 |
| Policy | 去中心化 PPO，π_θi(a_i|s_Ni)；对 policy shift ε_πi 有 trust-region 式约束；联合策略分解。 | per-agent tabular FTRL + entropic 正则，π^{k+1} ∝ exp(η Q^k)；输出 = K 个迭代的 α^K_k 加权混合 → ε-robust CCE。 |
| Critic | per-agent extended value V_i(s^{N^κ_i})；全局价值由局部平均近似，误差 ≤ r_max γ^κ/(1−γ)（Thm 3, Rem 1）；梯度用邻居平均，误差界 eq. (17)（邻域占比为乘性因子）。替代全局 critic。 | per-agent robust Q：q = r̂ + inf_{P∈U} P·V̂，只定义在 (s,a_i)（eq. (18)）；strong duality + clipping 求解；需要完整状态与 generative 采样。 |
| 通信 | 中心议题：图边即信道；最小消息大小 O(|s_i|)（SI Table 1）；成本约为中心化方法的 5–35%（p.5）；κ 决定半径与成本权衡。 | 缺失：不建模通信；中心化 generative model；无消息传递；假设全状态共享。 |
| 样本效率 | 经验主张（localized model + branched rollout）；理论只界定 model error 的影响（Thm 1/2, Cor 1）与单调改进条件（eq. (10)），无 n 的样本复杂度速率。 | 被证明的对象：N_all = O~(S H⁶ Σ_i A_i/ε⁴ · min{H, 1/min_i σ_i}) 样本达到 ε-robust CCE（Thm 2, eq. (30)）；下界 Ω(S H³ max_i A_i/ε² · min{…})（eq. (29)）。无实验。 |
| 联合动作处理 | 从不枚举/分析：策略按构造分解；"joint" 只以 "joint policy" 出现；无 ∏A_i 项。 | 核心：robust Q 索引 (s,a_i)；不确定性集积分掉他者（fictitious; others-integrated (s,a_i)-rectangularity, Def 1）；(s,a_i) 逐点采样、对手取自当前策略（Alg 1, eq. (16)）→ 积变和。 |
| 主要方法 | Networked model-based MARL：localized 动力学模型（MSE）、branched T-step rollout、warm-up + real/model 数据混合、去中心化 PPO、κ-hop critic；公开代码。 | Robust-Q-FTRL：adaptive N-sample 估计；对偶 robust Q；Q 移动平均；FTRL 更新；variance-style optimistic bonus；K 迭代混合输出。纯理论、无代码。 |
| 理论 | Thm 1/2（vanilla vs branched 回报界；ε_mi 系数 γ/(1−γ) → γ(1−γ^T)/(1−γ)）；Cor 1（ξ 项 +2r_max γξ/(1−γ)²）；Thm 3 + Rem 1（γ^κ 价值误差）；Thm 4（γ^{κ−1}[1−(1−γ²)·|N^κ_i|/n] 梯度误差，占比乘性）；eq. (12) dependency-bias 分解。 | Thm 1（robust NE/CCE 存在）；Thm 2 上界（Σ A_i）；eqs. (27)–(29) 下界（≥1/8 失败、max_i A_i、经单 agent 归约承袭自 Shi et al. 2024；不证明 ∏ 形式必要）；H⁶/H³ 与 ε⁴/ε² gap 已承认；Σ vs max gap 未讨论。 |
| Agent 数量 | 实验到 436（NY 路口；一处图注印 432）与 199（电力）；声称 "hundreds"。 | 仅符号 n；无实验；尺度全在 Σ vs ∏。 |
| 实验 | 充分：traffic/power/pandemic/CACC；baseline CPPO/DPPO/IMPO/MPOna/MAG；κ 与 rollout 消融；通信成本表；n = 5。 | 无。纯理论；无代码。 |
| 对 LAG 的可迁移性 | 部分、概念性但可在现有基线上检验：critic 信息局部性消融、通信成本核算、branched-rollout MBRL（高风险）。固定无向图 / 局部奖励平均 / 平稳核假设在 LAG 不成立。 | 仅概念：Σ-vs-∏ 诊断（附类不可比警告）；对 adaptive opponent sampling 与 FSP 的机制级类比（仅 suggestive；FSP 本身不在其覆盖内）；sim-to-real 的 robust-MG 框架；CCE-混合视角。算法与保证不可迁到连续 deep RL。 |
| 实现难度 | 中高：有公开代码但面向其他领域；需要动态邻域构建、per-agent 模型、在现有 MAPPO 管线外加 rollout 回路；风险集中在对抗自博弈下学习局部动力学。 | 不可直接实现：tabular、generative oracle、无代码、常数未给、渐近指数。最多复现一个小型 tabular toy RMG；否则只是写作/框架资源。 |

## 4. 它们解决的是不是同一种"维度灾难"？

**明确回答：不是。** 两篇论文攻击的是正交的两种瓶颈，且都不是经典单 agent 意义上的"维度灾难"：

**(a) Paper A 攻击"全局信息 / 中心化"瓶颈。** 其对立面是"每个 agent（或全局 critic）必须消费全局状态"以及由此而来的通信、隐私、计算成本："centralized learning (left) requires each agent to have global observations, significantly increasing algorithm complexity and communication costs, and reducing scalability"（Fig. 1a caption, p.2）；"achieving comprehensive information sharing across the entire system becomes unfeasible"（p.1）；MAG 的全局 critic "is still essentially a centralized training method"（SI p.21）。修复手段是条件于 κ-hop 邻域（最小消息大小 O(|s_i|)，通信成本约为中心化方法的 5–35%），形式化的脸面是近似误差随邻域半径指数衰减：|V_i(s) − V_i(s^{N^κ_i})| ≤ r_max γ^κ/(1−γ)（Thm 3）及其 policy gradient 版本（Thm 4，邻域占比为乘性因子）。其 scale 变量是 κ 与图结构，**不是动作组合数**。A 的策略按构造分解，从不估计 joint-action 统计，全文没有 ∏|A_i| 项，也没有 n 的 sample-complexity 速率。

**(b) Paper B 攻击"联合动作空间"瓶颈，即 curse of multiagency。** 其对立量是 ∏_{i}|A_i|：先前的 robust-MG 界 O~(S H³ ∏_i A_i / ε² · min{…})（eq. (2)，属不同的 RMG 类），B 的界 O~(S H⁶ Σ_i A_i / ε⁴ · min{…})。机制是结构性的：agent i 的 robust Q 只定义在 (s,a_i) 上，不确定性集把其他 agent 的行为积分掉，每轮采样从当前策略模拟其他 agent（Alg 1）。其 scale 变量是 n 与 |A_i|。B 的 "integration" 是**对行为的边际化**，不是空间/图上的局部化：它假设每个 agent 观测完整状态、由中心化 simulator 学习，全文不讨论通信。因此 B 不解决 A 的问题。

**(c) 为什么同叫 scalability 却正交**：A 管"每个 agent 需要什么信息"（信息/通信/表示的可扩展性）；B 管"每个 learner 需要估计什么统计量"（统计复杂度的可扩展性）。一句话：*Paper A 是关于信息的，Paper B 是关于统计的。* 三条必须避免的错误合并：不能说 "both break the curse via local information"（B 没有信息局部性）；不能说 "both address centralized-critic scalability"（B 假设全状态可达）；不能说 "Paper A solves the joint-action curse"（joint action 在 A 里从不是复杂度变量）。

**(d) 引用 ∏→Σ 时的两点纪律（均来自 B 自身）**：B 的 ∏→Σ 只在其**新 RMG 类**内成立、不可与先前类直接对比（footnote 1, p.4）；标准 MG 的 ∏→Σ 早在 B 之前（eq. (1), Li et al. 2023；亦见 Wang et al. 2023 COLT）。所以 ∏ vs Σ 应作为**诊断分类学**使用（哪些设计继承指数：joint-action-value critic、对 joint action 的精确 best response、joint-action 枚举——是；分解式 actor、per-(s,a_i) 估计——否），而不是当作某篇文章的"突破性对比"来引。

## 5. 对 LAG / MAPPO 空战的可迁移性

（前提：本项目基线 = MAPPO（中心化 critic + 分解 actor）+ FSP 自博弈，环境 LAG。以下审计数字来自 `/root/autodl-tmp/SEU-SRTP/docs/nvn_scalability_audit.md`。）

### 5.1 LAG 的增长点属于哪一类

审计结论（§3.1 / §3.2 / §4.2 / §4.3 / §8）：局部观测 obs_dim = 12N+3；share_obs（全 agent 拼接）= 2N(12N+3) = 24N²+6N；share_obs replay buffer O(N³)；环境观测构造 O(N²)（每步还重复做了两遍）；critic 首层 O(N³)（行数 O(N) × 行宽 O(N²)）；actor 首层 O(N²)（obs_dim = 12N+3 乘以行数）。而 per-agent action space 固定且分解——**N 增大不产生 ∏|A_i| 增长**。§8 的纪律：只有 team-mean 奖励稀释（§5.2）与"若出现"的 critic 拟合困难可以挂到 curse of multiagency；其余都是代码 / 表示可扩展性（computation/representation scalability），不能打扮成算法可扩展性问题。

### 5.2 为什么 Paper A 不能直接替代 MAPPO

1. **没有固定图。** A 的定理条件在 stationary、无向图上，局部有效性来自静态网络中的指数衰减；LAG 的"邻域"是交战几何（射程/传感器范围内），每步重算、本质上有向且对抗。超视距交战中远处 agent 的导弹发射可立即决定性——A 定理的前提在 LAG 恰是需要检验的假设。
2. **奖励不匹配。** A 要求 r_i(s_i,a_i) 且全局奖励 = 局部平均；LAG 是稀疏、非局部的团队奖励（kill/损失事件），无法照搬局部分解。
3. **model-based 管线 vs 对抗自博弈。** A 需要每 agent 学动力学 + branched rollout；在 LAG 中这意味着对 6-DoF JSBSim + 比例导引导弹 + 学习型对手建模，且 ξ-dependent / stationary kernel 假设会被学习对手打破。
4. **是架构替换而非补丁。** A 去掉全局 critic、改变数据回路（模型 rollout、warm-up、真实/虚拟混合）、按邻接初始化。采用它 = 围绕局部性重建 learner，而不是给 MAPPO 加模块。
5. **保证错位。** A 只保证 κ 的近似误差，不保证胜率；前提 1–3 不成立时，一切收益均为经验问题。

### 5.3 为什么 Paper B 不能直接替代（或接入）MAPPO

1. **设定错位**：tabular、有限时域、全观测、general-sum + generative-model oracle（从 nominal kernel 任意 (h,s,a) 采样）；LAG 是连续高维、部分观测、对抗/团队，且 "kernel" 包含学习型对手；oracle 不存在。
2. **算法类错位**：Robust-Q-FTRL 是 tabular no-regret 学习（FTRL + 对偶 robust Q + 迭代混合），没有 actor/critic/GAE 可接、没有代码。
3. **解概念错位**：被证明的是 K 个 tabular 策略上的分布（ε-robust CCE），不是单一去中心化策略；CCE 是 no-regret（估计精度）概念，不是对抗强度。
4. **鲁棒轴错位**：B 处理 TV 球内的 kernel misspecification（sim-to-real 类问题）；LAG 的训练病理是稀疏奖励、对手非平稳、信用分配、表示——且 "regardless of uncertainty set" 只对 TV 有证明。
5. **不可实施**：常数未给；H⁶/ε⁴ 与下界 H³/ε² 有 gap；无实验。
6. **自博弈假设不匹配**：B 的游戏有固定 kernel；FSP 刻意让对手随训练变化，B 的保证需重新推导。

### 5.4 可以借鉴的部分

**Paper A（本项目的可实验来源，按优先级）：**

1. **中心化 critic 的信息局部性消融——最直接的一条。** 在现有 N-v-N 管线里把 full share_obs critic 输入替换为：(i) 仅 ego-team 观测；(ii) 按距离最近的 k 个 agent（动态 κ 类比）；(iii) 距离衰减的全局特征；对比胜率、样本效率与 buffer/内存成本。**注意**：该消融必须同时改观测构造，否则 actor 侧输入仍是 O(N)（obs_dim = 12N+3）、首层仍 O(N²)——只收窄 critic 输入不能消除全部 N 增长。并显式声明：无定理可迁移（静态图前提），这是假设检验。
2. **通信成本核算作为报告方法学**：performance vs 信息半径/字节（仿 A 的 κ 扫描与 SI Table 3）；对数据链受限的 UAV 场景是操作性指标。
3. **extended-value 模式**：per-agent 局部价值头平均成 critic 目标——但仅在先定义局部 shaping reward（如对每架敌机的态势/能量优势）后可行，因 LAG 团队奖励不满足 A 的"局部奖励平均"前件。
4. **Model-based 样本效率（branched rollout、T 截断、warm-up、真实/虚拟混合）**：概念可移植（MBPO 式），但 6-DoF + 导弹 + 自博弈下风险高；持久有用的教训是 T 截断逻辑（compounding error 随 T 增长）。
5. **叙事**：可引 Thm 3/4 作为"局部观测为何可能够用"的形式化陈述，但必须带上 γ≈1 的量级警告（§1.5：γ=0.99 时 10% 误差需 κ 数百跳；小 κ 结论必须经验验证），并指名静态网络假设为空战中的开放问题。

**Paper B（只做框架与诊断，无工件可搬）：**

1. **Σ vs ∏ 诊断**：把每个规模化担忧分类为（i）信息/中心化（share_obs、带宽）还是（ii）联合动作统计（∏ vs Σ）；由此判断候选设计是否继承指数（joint-action-value critic、精确 best response、joint-action 枚举——是；分解式 MAPPO actor——否）。附 §4(d) 的不可比警告。
2. **FSP 的机制级类比（仅 suggestive）**：B 的机制——从当前策略采样对手、对迭代做平均——是 FSP 的抽象形状，说明该 adaptive-sampling 模式在其算法内打破指数的原因；但 B 不分析 FSP，不能宣称给出"FSP 的形式化理由"。
3. **sim-to-real 的 robust-MG 框架**：把现实看作 JSBSim nominal 的 TV 球、σ 作为旋钮——原则性视角；无 deep RL 配方，属研究扩展。
4. **下界 sanity check**：预期至少多项式动作空间成本；对"完全逃脱 agent 数扩展"的方法保持怀疑。
5. **均衡视角**：迭代混合 ≈ population play，可作为对手池讨论的语境（LAG 是对抗/团队，NE/CCE 只能作类比）。

**不要引入**：A 的固定图、局部奖励平均、stationary-ξ 假设与 κ=1–2 结论；B 的 tabular/generative-oracle 机制、未证明的 "regardless of uncertainty set" 声明、以及把 Robust-Q-FTRL 插进 deep RL 的任何期望。

### 5.5 两篇论文都没有回答的问题（SRTP 声明必须保持经验性的部分）

两篇并集仍留有缺口：**没有学习型/对抗对手**（A 是静态合作网络；B 是固定 kernel）；**没有 sensing / 观测噪声**（A 假设精确的 κ-hop 状态；B 假设完整状态被观测）；**没有不完美通信信道**（A 度量消息大小与成本，但其理论无带宽/延迟/丢包模型——O(|s_i|) 消息大小声称与理论之间有此缺口）；**没有带保证的非 tabular / function approximation**（B tabular；A 无样本复杂度速率）。此外奖励稀疏与信用分配两篇都未建模（A 仅在"局部 shaping reward"处被间接涉及）。以上每一条都对应 SRTP 中一个必须保持为**经验命题**（而非引用定理支撑）的声明。

## 6. 与本项目实验的接口

本节由主循环在拿到当晚实测数据后填写，**所有数字都来自本机实测**，
来源：`docs/nvn_scalability_audit.md`、`docs/night_failures.md`、
`experiments/2026-10-04-night/metrics/`。

### 6.1 LAG 的增长点，分别落在哪一篇的坐标系里

| LAG 的实测增长 | 增长阶数 | 对应 Paper A 的轴？ | 对应 Paper B 的轴？ |
|---|---|---|---|
| 局部观测维度 `obs_dim = 12N+3` | O(N) | ✅ **是**（每个 agent 消费多少信息） | ❌ 否 |
| `share_obs_dim = 24N²+6N` | **O(N²)** | ✅ **是**（全局信息 / 中心化） | ❌ 否 |
| critic 首层 MAC/env-step | **O(N³)** | ✅ 是（中心化 critic 的表示成本） | ❌ 否 |
| share_obs replay buffer | **O(N³) 字节** | ⚠️ 间接（信息存储） | ❌ 否 |
| JSBSim 物理仿真 | **O(N) 线性** | ❌ 否 | ❌ 否 |
| 观测构造（工程实现） | **O(N²)，且每步做两遍** | ⚠️ 是 A 的「表示」轴，但成因是实现 | ❌ 否 |
| **联合动作空间** | 理论 O(∏ \|A_i\|)，**MAPPO 未显式枚举** | ❌ | ⚠️ 概念上相关，但见 §6.4 |

**结论：LAG 在 N-v-N 上实测到的所有超线性增长，都落在 Paper A 的坐标系里，
没有一条落在 Paper B 的坐标系里。**

### 6.2 用 Paper A 的语言重新描述 LAG 的现状（这是本报告最有价值的一条连接）

Paper A 的局部性参数是 **κ**（κ-hop 邻域，近似误差 ≤ r_max·γ^κ/(1−γ)，Thm 3）。
把它套到 LAG 上：

> **当前 LAG 的 κ = ∞。**

依据（逐条对应代码）：

1. `MultipleCombatTask.get_obs()` 对每个 agent 遍历
   `agent.partners + agent.enemies` —— **全部**其他飞机，与图距离无关。
   于是 `obs_dim = 9 + (2N−1)·6 = 12N+3`。
2. `BaseEnv.get_state()` 把全部 agent 的观测 `hstack` 成 `24N²+6N` 维，
   并**复制给每一个 agent**。
3. 因此 `obs_dim` 与 `share_obs_dim` 都随 N 发散，**不存在任何
   「每个 agent 只依赖邻域」的结构**。

换句话说：**LAG 目前实现的不是「局部观测 + 集中式 critic」，
而是「全局观测 + 全局 critic」——它连 Paper A 所批评的 baseline 都不如，
因为 A 的 baseline 至少每个 agent 只拿自己的全局状态副本，而 LAG 的每个 agent
拿到的是含全部 N 个 agent 交互信息的稠密向量。**

这一点可以直接转化为一个**可执行、可度量、且与 Paper A 的定理形式一一对应**的实验：

> **实验 A′（κ-sweep）**：把 `get_obs` 的邻居集合从「全部」改成
> 「按图距离/威胁度选取的 κ-hop 或 k-近邻」，
> 则 `obs_dim → O(κ)`（或 O(k)）、`share_obs_dim → O(N·κ)`、
> critic MAC/step → O(N²κ)，且 Paper A 的 Thm 3 直接给出
> 「性能损失随 κ 指数衰减」的可检验预测。
>
> 与 Paper A 的差异需要诚实声明：A 是在**图结构已知、转移可分解**的
> networked MDP 上有定理；空战里「图」需要我们自己定义
> （距离 / 威胁度 AO-TA / 是否被锁定 / 是否同一目标），
> 且 A 的 model-based 部分依赖局部动力学模型——这些在 LAG 上都没有现成实现。

**空战里 κ-邻域的自然候选**（可作为 A′ 的设计输入，按可解释性排序）：

1. **最近 k 架飞机**（图距离 = 欧氏距离）
2. **威胁邻域**：距离 + 相对姿态（AO/TA）+ 是否正在被其锁定
3. **任务邻域**：同一目标 / 同一编队
4. **导弹邻域**：来袭导弹的发射者

注意 LAG 已经有一个「局部性」的抓手：`PostureReward` 已经把
orientation×range 对**每个**敌机求和（详见 §6.3），
把它改成只对「威胁最大的 k 个敌机」求和，就同时得到了
**局部 reward** 与 **局部 critic** —— 这是 A′ 最小的实现路径。

### 6.3 与本文档 §2/§5 的一个隐藏联系：奖励里的 ∏ 与 Σ

LAG 的 `PostureReward` 是对敌机的 **求和**（Σ），不是乘积（∏）：

```python
for enm in env.agents[agent_id].enemies:
    new_reward += self.orientation_fn(AO, TA) * self.range_fn(R / 1000)
```

按本文档 §3/§4 的分类学，这**不属于** curse of multiagency 的 ∏ 结构——
逐敌机奖励是可加分解的，不继承指数复杂度。**但它确实随 N 线性增长**，
我们在实测中直接观察到了这一点：

| N | reward | reward / N |
|---|---|---|
| 2 | -3.52 | **-1.76** |
| 3 | -5.43 | **-1.81** |
| 10 | -17.66 | **-1.77** |

`reward/N` 几乎恒定，直接证明奖励幅度 ∝ N。
**推论**：任何跨 N 的 reward / value_loss / grad_norm 比较**必须归一化**，
否则会把一个奖励设计问题误读成算法问题。见本报告 §11。

### 6.4 为什么 Paper B 的 ∏→Σ 不能直接套到 LAG 上

按 §4(d) 的纪律，∏ vs Σ 是**诊断分类学**，不是可以直接搬过来的结论。对 LAG：

- MAPPO 的 actor 是 **factorized** 的：π(a|o) = ∏_i π_i(a_i|o_i)，
  **不显式枚举联合动作**。因此 ∏|A_i| 不进入网络前向的计算量。
- LAG/MAPPO 里**确实**存在继承指数的组件是**集中式 critic 的输入**，
  但那是 **状态空间**的拼接（O(N²) 维），属于 Paper A 的轴，不是动作空间。
- 真正可能继承 ∏ 的地方是**精确 best response** 与**联合动作价值**，
  LAG 目前都没有用（FSP 用的是策略池采样，不是精确 best response）。

**因此正确表述是**：「LAG 的 MAPPO 不会因为 ∏|A_i| 而计算爆炸；
它的可扩展性瓶颈在状态/信息的拼接上，属于 Paper A 的问题类。」
这一点必须在答辩中讲清楚，否则很容易被问倒。

### 6.5 当晚实测数据对两篇论文主张的（弱）检验

| 论文主张 | 本晚能否检验 | 实测 |
|---|---|---|
| Paper A：全局信息/中心化的成本随规模增长 | ✅ **能，且已观察到** | share_obs 维度 O(N²)、critic MAC/step O(N³)、buffer O(N³) 字节；但 GPU 在 N≤10 未饱和（利用率 0–11%） |
| Paper A：局部化可换取可扩展性 | ⚠️ **尚未做**（本晚未实现 κ-邻域） | 已提出实验 A′ |
| Paper A：误差随 κ 指数衰减 γ^κ | ❌ 不能（需要一个能定义图距离的空战图） | — |
| Paper B：∏|A_i| 导致样本复杂度爆炸 | ❌ **在 MAPPO 路径上不适用**（actor factorized、无联合动作枚举） | — |
| Paper B：Σ 界 | ❌ 不能（需要 tabular + generative model） | — |

> **诚实声明**：本晚的实验**没有**、也不可能验证 Paper B 的任何定理，
> 因为 B 的设定（tabular、finite-horizon、general-sum、generative model、
> robust CCE）与 LAG（连续高维状态、神经网络策略、self-play、非平稳对手）
> 之间存在不可跨越的差距。B 对我们的价值是**术语与诊断工具**，
> 不是可实现的算法。「我们验证了 Paper B」这类说法必须禁止。

## 7. 引用与页码索引

（页码为抽取文本页标记。下列为上文所用、可逐条回查的锚点。）

**Paper A**（`/root/autodl-tmp/SEU-SRTP/papers/text/paperA_network_control.txt`；注意含 NUL 字节）：

- eq. (1) extended value p.3；eq. (4) 邻域平均估计 p.3（分母 n vs |N^κ_i| 存疑，待核实）；eq. (6) 模型 MSE p.5；eq. (7)–(8) 目标/价值 p.9；networked MDP、κ-hop、localized policy 定义 p.9；Definitions 1–2、eq. (10)、eq. (12)、Theorem 1 p.10；Theorem 2、Corollary 1 p.11；Theorem 3、Remark 1、Theorem 4、Remark 2、eqs. (15)–(17) p.12。
- SI：Table 1 与 CPPO 说明 pp.21–22（SI 内部页 2–3/24）；INS 批评原文 SI p.22；Table 3（κ 配置 1/2）p.28；ξ 估计 §3.3 pp.29–30；§4.5 证明 p.36；§4.6 证明 pp.36–37；Lemma 4 p.39；Lemma 5 p.40。436 路口：pp.3, 7 与 SI p.24；432：Fig. 5 caption p.8。通信成本 5–35%：p.5。
- 核验：Paper A 全文 0 次出现 "curse"。

**Paper B**（`/root/autodl-tmp/SEU-SRTP/papers/text/paperB_curse_of_multiagency.txt`）：

- curse 表述 p.3；eq. (1) 标准 MG Σ 界、eq. (2) 先前 ∏ 界 p.3；Table 1、eq. (3)、footnote 1（不可直接对比）p.4；MG 设定与 Markov policy p.6；eq. (5)（robust Q 只定义在 (s,a_i)）、reward uncertainty 省略 p.7；Definition 1 / eq. (12) p.8；Theorem 1 p.9；eqs. (13)–(15) p.10；Algorithm 1 与 eqs. (16)–(20) p.11；eqs. (21)–(25)、Theorem 2 / eq. (26) p.12；Algorithm 2、下界 eqs. (27)–(29) p.13；eq. (30) 与 gap 讨论 p.14；Lemma 10 p.34；附录 FTRL regret p.22。
- 核验：Paper B 全文 0 次出现 "commun*"；min{…} 因子位置（分子乘性）经 arXiv v3 HTML 确认。

**项目文档**：

- `/root/autodl-tmp/SEU-SRTP/docs/nvn_scalability_audit.md`：§3.1 obs_dim = 12N+3；§3.2 share_obs = 24N²+6N；§4.2 critic 首层 O(N³)、buffer O(N³)；§4.3 actor 首层 O(N²)；§5.1 奖励幅度 ∝ N；§5.2 team-mean 稀释；§8 curse 归因纪律。
- `/root/autodl-tmp/SEU-SRTP/docs/baseline_inventory.md`（基线清单）。
