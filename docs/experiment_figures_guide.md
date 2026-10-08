# 实验图表指南（`figures_v2`）

负责人：刘酝潇
最后更新：2026-10-08
绘图入口：`experiments/2026-10-07-08-formal6m/scripts/figures/make_all.py`

---

## 0. 一条命令重生成全部图

```bash
cd experiments/2026-10-07-08-formal6m/scripts/figures
/root/miniconda3/envs/jsbsim/bin/python make_all.py
```

模块缺失或单张失败会被跳过并打印警告，不会整体崩掉。产物同时输出
**PNG（dpi=300）** 与 **PDF（矢量）**，均在 `figures_v2/`。

**旧图保留在 `experiments/2026-10-07-08-formal6m/figures/`**（工程监控风格那一套），
未删除，作为历史对照。本目录是论文/答辩用的一套。

---

## 1. 代码结构

| 文件 | 职责 |
|---|---|
| `style.py` | 配色、rcParams、保存、平滑/原始曲线绘制、末端标注、caption |
| `data.py` | 全部数据加载 + `RUN_META`（14 个 run 的 n/seed/线程/完成度）+ 按步窗口平滑 + matched-budget 取值 |
| `fig1_official_baselines.py` | Figure 1 及其附图 |
| `fig2_scaling_curves.py` | Figure 2 及其附图 |
| `fig3_matched_budget.py` | Figure 3 |
| `fig4_computational.py` | Figure 4 |
| `fig5_critic_scaling.py` | Figure 5 |
| `make_all.py` | 统一入口 |

**分层原则**：加载 / 校验 / 平滑 / 归一化 / 绘图 / 导出各自独立，换数据源只动 `data.py`。
**不修改任何训练数据**。

---

## 2. 统一口径（所有图一致，不得逐图更改）

### 2.1 平滑

| 项目 | 取值 |
|---|---|
| 方法 | rolling mean，**按环境步窗口**，不按 episode 序号 |
| 窗口 | **250,000 环境步**（`data.DEFAULT_WINDOW`） |
| raw 曲线 | `lw=0.7, alpha=0.15`，同色 |
| 平滑曲线 | `lw=2.2, alpha=1.0`，同色同线型 |
| 末端约束 | 平滑线**不越过真实数据末端**；数据不足一个窗口时只画 raw |

**为什么按步而不按 episode**：各规模每个 episode 的步数不同
（2v2 每 episode 12k 步、3v3/5v5 24k、10v10 60k），按序号平滑会导致窗口不等价。

### 2.2 配色（Okabe-Ito 色盲友好，同一规模跨图固定）

| 规模 | 颜色 |
|---|---|
| N=1（1v1） | `#56B4E9` 浅蓝 |
| N=2（2v2） | `#0072B2` 蓝 |
| N=3（3v3） | `#009E73` 绿 |
| N=5（5v5） | `#E69F00` 橙 |
| N=10（10v10） | `#D55E00` 朱红 |
| SingleControl | `#CC79A7` 品红 |

同一规模的多个 seed：**同色、不同线型**（实线=seed0，虚线=seed1，点划线=seed2）。
透明度只用于 raw 曲线，不用于区分 seed。

### 2.3 归一化

| 图 | 口径 |
|---|---|
| Fig 3 | `reward_per_enemy = reward / team_size`，**仅对 NoWeapon 家族有效** |
| Fig 5D | `critic_grad_norm_per_N` |

> **reward/N 的局限**：`PostureReward` 按敌机数量累加，所以跨 N 的原始 reward 不可直接比。
> 但 `reward/N` **不等于统一的任务成功率**——不同 N 的任务规模、奖励构成、难度都可能不同。
> 本轮**没有可靠的胜率或统一评测指标**，因此 Fig 3 是**训练奖励的探索性比较**，
> 图中 caption 已明确写出这一点。

### 2.4 统计口径

- matched-budget 值 = `[budget - 200k, budget]` 步区间内的平均，**不是取单点尖峰**
- 误差棒 = **样本标准差**（`±1 s.d.`），**仅当 seed 数 ≥ 3** 才画
- seed 数 1~2 的点**只画点，不画误差带**
- 箱线图的箱 = 每 episode 分布的中位数 / IQR / 1.5-IQR 须，**不是置信区间**

---

## 3. 图清单

### Figure 1 — `fig1_official_baselines.png` / `.pdf`

- **入口**：`fig1_official_baselines.py`
- **数据源**：`metrics/curves/` 下 6 个 `f6m_official_*` 曲线 CSV
- **结构**：2×2，四个**独立 y 轴**的子图
  - A. SingleControl `1/heading`（单智能体）
  - B. 1v1 NoWeapon：Selfplay / vsBaseline / HierarchySelfplay
  - C. 1v1 ShootMissile：HierarchySelfplay
  - D. 2v2 MultipleCombat：NoWeapon HierarchySelfplay
- **要点**：四个任务的 reward 量级差一个数量级（±320 / ±200 / ±200 / ±40），
  **绝不能共用 y 轴**；B 子图用阴影带 + 箭头标出后期不稳定区间
- **答辩用途**：证明"官方 baseline 我们真的复现了"，一页讲完 6 个官方入口

**附图 `fig1b_1v1_hier_raw.png`**：只画 1v1 HierarchySelfplay 的**完整 raw 曲线**，
不叠加平滑。用于专门讲后期不稳定（平滑会把负向尖峰抹掉）。

---

### Figure 2 — `fig2_scaling_curves.png` / `.pdf`  ← **本轮最重要**

- **入口**：`fig2_scaling_curves.py`
- **数据源**：`metrics/curves/` 下 8 个 scaling 家族曲线 CSV
- **结构**：2×2 小面板，左上 2v2、右上 3v3、左下 5v5、右下 10v10
- **要点**：
  - 横轴四面板统一 **0–6M**
  - 每面板**独立 y 轴**，y 轴标签注明该规模的 reward 量级
  - 未完成的 run **自然截止**并标注 `(censored at 5.4M)`
  - 末端直接标注 seed，不用大图例
- **答辩用途**：主图。回答"每个规模是否在学习、学得多快、seed 稳不稳"

**附图 `fig2b_scaling_shared_axis.png`**：四规模**共用同一 y 轴**的版本。
它的用途是**解释为什么旧图看不见 10v10**——图内直接标注
"10v10 spans 35 of the 116 reward units on this axis (it only looks flat because
the shared scale is set by 5v5)"。这是诊断图，不是主图。

> **10v10 数据是完整的**（seed 0 跑满 6,000,000 步，seed 1 到 1,860,000 被时间截断）。
> 旧图中它"消失"纯粹是共享 y 轴的尺度问题，**不是数据缺失、不是被过滤**。

---

### Figure 3 — `fig3_matched_budget.png` / `.pdf`

- **入口**：`fig3_matched_budget.py`
- **数据源**：`metrics/normalized_scaling.csv`
- **结构**：
  - A. matched reward per enemy vs team size N（形状=预算 1M/2M/4M/6M，颜色=规模，
    灰线=同一预算跨 N 的轨迹）
  - B. matched reward per enemy vs 预算（每规模一条线）
- **要点**：**只有真正达到该预算的 run 才进入比较**，未达标直接不画、不插值；
  误差棒仅在 seed ≥ 3 处画；每个点标注 seed 数
- **答辩用途**：回答"跨规模谁学得更好"，且能挡住"你们只比了最后一帧"的质疑

---

### Figure 4 — `fig4_computational.png` / `.pdf`

- **入口**：`fig4_computational.py`
- **数据源**：A/B 用 `metrics/curves/*.csv` 的 `fps` 列与 `wall_time`；
  C 用 `metrics/resources.csv`；D 用 pilot 的 `metrics/obs_cost_profile.json`；
  参考线用 pilot 的 `metrics/env_bench_scaling.json`
- **结构**：
  - A. 训练吞吐 vs total agents（含 idle-machine 参考线）
  - B. 达到 1M 环境步所需 wall-clock 小时数 vs total agents
  - C. 每 run 峰值 CPU / RSS / VRAM
  - D. 每步耗时分解（仿真 / 观测构造 / 状态构造 / 其他）
- **要点**：**每个点都标注了它对应的 rollout 线程数**——线程数不同（4/8/8-10/20），
  点与点不是同一算力配额下的对比；C 面板的 CPU 一栏明确标注
  *"unreliable: sampler read host-wide /proc/stat (F16) - relative only"*
- **答辩用途**：回答"瓶颈在哪"。D 面板最直接：**观测构造占每步耗时
  27.6% → 34.7% → 45.7% → 40.3%**，随 N 上升，这是当前最明显的 scalability 瓶颈

---

### Figure 5 — `fig5_critic_scaling.png` / `.pdf`

- **入口**：`fig5_critic_scaling.py`
- **数据源**：A–C 用 `metrics/critic_scaling.json` 的 **measured 4 条**；
  D 用 `metrics/normalized_scaling.csv` 的 `critic_grad_norm_per_N`
- **结构**：
  - A. obs dim vs N 与 share_obs dim vs N（**两个 y 轴，量级差 20 倍**）
  - B. critic 与 actor 参数量 vs N
  - C. critic 第一层每环境步 MAC vs N（含 log-log 插图）
  - D. 归一化 critic 梯度范数按 N 的箱线图
- **要点**：
  - 精确闭式：`obs = 12N+3`、`share_obs = 2N(12N+3) = 24N²+6N`、
    `critic_params = 128(24N²+6N) + 150145`
  - **N=20/50/100 的外推值一律不画**（caption 已声明）
  - D 面板仅用 measured 的 N
- **答辩用途**：回答"集中式 critic 能不能扩展"

---

## 4. 哪张图适合哪一页 PPT

| PPT 页 | 用哪张 | 一句话 |
|---|---|---|
| 背景 / 我们做了什么 | `fig1_official_baselines.png` | 6 个官方 baseline 全部复现 |
| **核心结果页** | `fig2_scaling_curves.png` | 四个规模的学习趋势 |
| 为什么之前看不见 10v10 | `fig2b_scaling_shared_axis.png` | 共享轴造成的视觉压缩（诊断页） |
| 跨规模定量比较 | `fig3_matched_budget.png` | 等预算比较 + 逐点 seed 数 |
| 瓶颈分析 | `fig4_computational.png` | 算力/显存/观测构造瓶颈 |
| 表示层面瓶颈 | `fig5_critic_scaling.png` | critic 的 O(N²) 表示与 Θ(N³) 每步代价 |
| 训练不稳定性 | `fig1b_1v1_hier_raw.png` | 1v1 层次化自博弈后期退化 |

**30 秒看懂路径**：`fig2` → `fig4D` → `fig5A`。
即"四个规模都学了，但 N=10 明显更慢" → "因为观测构造成本随 N 上升" →
"而 critic 的输入维度是 O(N²)"。

---

## 5. 当前**不能**支持的结论

1. **不能**说完成了 100M 收敛复现。每 run 是 6M 预算（官方 1e8 的 6%）。
2. **不能**说证明了 curse of multiagency。N=10 落后是可复现的观察，
   但**没有受控的 critic 变体实验**把表示/计算层面的量级与"学习变慢"因果连起来。
3. **不能**把跨面板的 reward 高度当作算法优劣。四个任务 reward 定义不同。
4. **不能**把 `reward/N` 当作胜率或统一成功率。当前无可靠胜率指标。
5. **不能**从单 seed 得出统计结论。2v2 与 10v10 在 6M 处各只有 1 个 seed。
6. **不能**忽略线程数混淆。各规模 `n_rollout_threads` 不同（4/8/8-10/20），
   跨规模比较混入了 batch size 差异。
7. **不能**把 10v10 的平坦解读为"算法失败"。它在 6M 内单调改善，
   只是远慢于小规模（−1.73 → +0.04 每敌机）。

---

## 6. 数据完整性

- 全部图**从 `metrics/*.csv`、`metrics/*.json` 与 `scripts/results/**/metrics.jsonl` 生成**，
  没有从任何旧 PNG 反推数据。
- **未插值补齐**任何未完成的 run；**未剔除**任何 seed。
- 平滑窗口、seed 数、线程数、统计口径均写在每张图的 caption 中。
- 原始训练数据未做任何修改（`git status` 中 `scripts/results/` 无变更）。
