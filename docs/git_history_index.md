# SEU-SRTP Git 历史索引（中文）

> 本索引由脚本生成于 2026-10-08 12:18 CST。
> 用于在 commit message 统一中文化之后回溯历史，以及给协作者一份可读的变更总览。

- 仓库：`David-JayTao/SEU-SRTP`
- 索引范围：`main..exp/formal-6m-20261007`，共 **74** 个 commit
- 生成时的 HEAD：`d3c1995`
- `main`：`60a3e2d`

## 一、本地分支与远程分支

| 本地分支 | HEAD | 标题 |
|---|---|---|
| `backup/formal-6m-english` | `6c5bd99` | docs: freeze formal-6M campaign artefacts (20261008_092029) |
| `exp/formal-6m-20261007` | `d3c1995` | 文档：第 14 节术语统一为「种子 0/1」，修正 hash 映射表的核验基准 |
| `exp/repro-scaling-20261004` | `d133be6` | 导出了进展的pdf |
| `main` | `60a3e2d` | Merge pull request #1 from David-JayTao/infra/rtx5090-compat |

| 远程分支 | commit |
|---|---|
| `HEAD` | `60a3e2d` |
| `refs/heads/backup/formal-6m-english` | `6c5bd99` |
| `refs/heads/backup/pre-chinese-rewrite` | `6c5bd99` |
| `refs/heads/exp/formal-6m-20261007` | `d3c1995` |
| `refs/heads/exp/repro-scaling-20261004` | `20f39d3` |
| `refs/heads/infra/rtx5090-compat` | `14e6350` |
| `refs/heads/main` | `60a3e2d` |
| `refs/pull/1/head` | `14e6350` |

## 二、Commit 索引（旧 → 新）

| # | commit | 日期 | 中文标题 | 改动 |
|---|---|---|---|---|
| 1 | `48bf779` | 2026-10-04 | 杂项：搭建过夜实验基础设施，用于复现与 N-v-N 扩展 | 17文件s, 1123 insertions(+), 2 deletions(-) |
| 2 | `d0512c4` | 2026-10-04 | 文档：官方 baseline 清单 + N-v-N 扩展性审计 | 6文件s, 946 insertions(+) |
| 3 | `bd51ce5` | 2026-10-04 | 功能：metrics 采集、图表与实时状态工具 | 17文件s, 813 insertions(+) |
| 4 | `06c8bf7` | 2026-10-04 | 修复：把实验元数据写进日志，并对同一步的 metrics 记录取并集 | 12文件s, 571 insertions(+), 37 deletions(-) |
| 5 | `4e32506` | 2026-10-04 | 功能：reward 归一化的跨 N critic 分析 + 扩展对比表 | 9文件s, 327 insertions(+), 17 deletions(-) |
| 6 | `3ce1a26` | 2026-10-04 | 文档：过夜复现与扩展性报告（实时草稿） | 1文件, 509 insertions(+) |
| 7 | `c125039` | 2026-10-04 | 功能：reward 归一化 critic 扩展性图表 | 6文件s, 52 insertions(+) |
| 8 | `4555043` | 2026-10-04 | 实验：把 env-step 开销归因到物理仿真与观测工程 | 5文件s, 220 insertions(+), 2 deletions(-) |
| 9 | `0c66687` | 2026-10-04 | 实验：离线评估器；MultipleCombat 的评估是确定性的 | 9文件s, 259 insertions(+), 17 deletions(-) |
| 10 | `986bd00` | 2026-10-04 | 文档：两篇论文分析（58k agent-token 工作流）+ LAG 接口一节 | 2文件s, 380 insertions(+) |
| 11 | `6e14c7c` | 2026-10-04 | 文档：可扩展 MARL 候选方向及证据强度台账 | 2文件s, 333 insertions(+), 1 deletion(-) |
| 12 | `7320fd8` | 2026-10-04 | 功能：给离线评估器加上团队协同代理指标 | 2文件s, 67 insertions(+), 1 deletion(-) |
| 13 | `3666422` | 2026-10-04 | 实验：在 N=20 和 N=50 实测 critic，而不是外推 | 18文件s, 297 insertions(+), 116 deletions(-) |
| 14 | `0c55175` | 2026-10-04 | 功能：逐实验资源采样与资源-对-N 图表 | 17文件s, 194 insertions(+), 55 deletions(-) |
| 15 | `6b862eb` | 2026-10-04 | 文档：官方的 "FSP" 是 checkpoint 历史上的均匀采样，不是 FSP | 2文件s, 90 insertions(+) |
| 16 | `bd50337` | 2026-10-04 | 实验：1e5-1e6 步后策略仍近似均匀（两种方法测量） | 14文件s, 391 insertions(+), 93 deletions(-) |
| 17 | `0183761` | 2026-10-04 | 文档：诊断"学得慢"还是"学坏了"（critic 收敛，actor 几乎不动） | 1文件, 29 insertions(+) |
| 18 | `0e7310e` | 2026-10-04 | 文档：env-step 扩展的最小二乘拟合（N^1.64，R^2=0.999） | 2文件s, 28 insertions(+), 1 deletion(-) |
| 19 | `86d0d45` | 2026-10-04 | 功能：扩展表中加入 wall-clock 归一化 | 16文件s, 110 insertions(+), 30 deletions(-) |
| 20 | `31b182e` | 2026-10-04 | 功能：每次 sweep 自动生成可直接粘贴的报告表格 | 4文件s, 180 insertions(+) |
| 21 | `40eb460` | 2026-10-04 | 文档：reward/N 归一化只对 NoWeapon family 精确 | 1文件, 27 insertions(+) |
| 22 | `5cf5822` | 2026-10-04 | 文档：自我纠正——战斗 baseline 确实在学习，只是非常慢 | 21文件s, 331 insertions(+), 69 deletions(-) |
| 23 | `fa0c870` | 2026-10-04 | 功能：遇到真实失败就提前退出的 watchdog 循环 | 19文件s, 175 insertions(+), 69 deletions(-) |
| 24 | `193b41c` | 2026-10-04 | 功能：匹配步数的样本效率表 | 3文件s, 142 insertions(+) |
| 25 | `c22ce59` | 2026-10-04 | 文档：实测协同代理指标，以及它们支撑不了什么 | 2文件s, 68 insertions(+), 3 deletions(-) |
| 26 | `f0aac70` | 2026-10-04 | 文档：用两篇论文的分析填充报告第 14-16 节 | 1文件, 99 insertions(+), 7 deletions(-) |
| 27 | `e691226` | 2026-10-04 | 文档：按所针对的实测失败排序的具体后续实验计划 | 1文件, 64 insertions(+), 12 deletions(-) |
| 28 | `ccff3fb` | 2026-10-04 | 文档：按后续测量收紧 curse-of-multiagency 一节 | 1文件, 25 insertions(+), 10 deletions(-) |
| 29 | `d2ffdd0` | 2026-10-04 | 文档：用官方 2v2 baseline 验证生成的 scaling family | 1文件, 19 insertions(+) |
| 30 | `7f573f1` | 2026-10-04 | 功能：头条扩展性图表——每敌机 reward 对步数以及对 wall-clock | 27文件s, 975 insertions(+), 83 deletions(-) |
| 31 | `7a04ced` | 2026-10-04 | 文档：记录头条扩展性读数及其限制 | 1文件, 34 insertions(+) |
| 32 | `b3ddea2` | 2026-10-04 | 实验：归一化 critic 指标按 episode 平均，而不是单点 | 21文件s, 291 insertions(+), 63 deletions(-) |
| 33 | `db31578` | 2026-10-04 | 文档：用强化后的归一化数字同步 curse 一节 | 1文件, 5 insertions(+), 3 deletions(-) |
| 34 | `428cdee` | 2026-10-04 | 文档：新增面向课题组的 SRTP 进展报告，含实验图表与导航 | 47文件s, 17227 insertions(+), 127 deletions(-) |
| 35 | `c5bfbae` | 2026-10-04 | 文档：用最终数字收尾技术报告 | 1文件, 81 insertions(+), 44 deletions(-) |
| 36 | `f6e84a1` | 2026-10-06 | 导出了进展的pdf | 3文件s, 2 insertions(+), 2 deletions(-) |
| 37 | `5c8b7fb` | 2026-10-07 | 杂项：初始化 6M 正式实验 campaign | 29文件s, 3537 insertions(+) |
| 38 | `bbeb5d7` | 2026-10-07 | 实验：启动 6M 正式 campaign——四尺度 NoWeapon 扩展 + 官方 baseline | 12文件s, 566 insertions(+), 107 deletions(-) |
| 39 | `1fe6c67` | 2026-10-07 | 实验：把四个官方 1v1 baseline 作为并行 lane 运行 | 34文件s, 2838 insertions(+), 280 deletions(-) |
| 40 | `d2a2cc1` | 2026-10-07 | 实验：记录 9 lane 稳态标定与 1v1-shoot 的 budget 风险 | 45文件s, 1999 insertions(+), 614 deletions(-) |
| 41 | `1c4b44d` | 2026-10-07 | 功能：campaign 参数化的分析管线 + 等样本/等 wall-clock 表 | 45文件s, 1461 insertions(+), 379 deletions(-) |
| 42 | `3daf8e3` | 2026-10-07 | 文档：表示/critic 扩展一节、失败 F10-F14、事故日志 | 2文件s, 241 insertions(+), 2 deletions(-) |
| 43 | `7e8e4a2` | 2026-10-07 | 功能：campaign 结束 freeze 脚本，以及 critic 内存墙预测 | 57文件s, 1256 insertions(+), 241 deletions(-) |
| 44 | `635a77d` | 2026-10-07 | 文档：计算扩展性一节，依据本征 benchmark 拟合 | 1文件, 88 insertions(+), 1 deletion(-) |
| 45 | `528a810` | 2026-10-07 | 功能：只在真实事件上唤醒操作者的 event watcher | 1文件, 96 insertions(+) |
| 46 | `7e80c60` | 2026-10-07 | 文档：把六张必需的图嵌入报告 | 1文件, 36 insertions(+) |
| 47 | `9c2beb0` | 2026-10-07 | 文档：critic 扩展一节改用精确闭式替换拟合指数 | 1文件, 39 insertions(+), 20 deletions(-) |
| 48 | `ed3b352` | 2026-10-07 | 修复：/proc/stat 在此容器中不可用——更正所有 CPU 数字（F16） | 17文件s, 617 insertions(+), 232 deletions(-) |
| 49 | `314e47c` | 2026-10-07 | 文档：记录 F17，可达步数预算的线程数量化 | 1文件, 42 insertions(+) |
| 50 | `1fdb28c` | 2026-10-07 | 修复：按 lane 自身可达预算而非名义预算判定完成 | 4文件s, 292 insertions(+), 203 deletions(-) |
| 51 | `cc88524` | 2026-10-07 | 文档：CPU 更正后的修订排空计划 | 1文件, 37 insertions(+) |
| 52 | `74810c1` | 2026-10-07 | 文档：记录在 CPU quota 用到 91% 时不再加第四个 seed 的决定 | 1文件, 14 insertions(+) |
| 53 | `eef285e` | 2026-10-07 | 功能：死亡开关——没有 agent 也能 freeze 并提交 | 5文件s, 205 insertions(+), 116 deletions(-) |
| 54 | `cfc033e` | 2026-10-07 | 功能：让报告自填充，交付物不再依赖存活的 agent | 67文件s, 7665 insertions(+), 303 deletions(-) |
| 55 | `8504c27` | 2026-10-07 | 文档：记录 hierarchical 1v1 lane 的真实退化，以及它并非发散的检查 | 6文件s, 203 insertions(+), 131 deletions(-) |
| 56 | `6c374c0` | 2026-10-07 | 文档：写第 15、16 节——现在就写，因为两者都不依赖最终数字 | 1文件, 136 insertions(+), 2 deletions(-) |
| 57 | `f5c114d` | 2026-10-07 | 修复：offline_eval 的默认对手是 NULL policy——其默认数字毫无意义（F18） | 7文件s, 188 insertions(+), 124 deletions(-) |
| 58 | `3eeb00e` | 2026-10-07 | 文档：实测 episode 长度混杂，随后撤回它似乎要证明的那个更正 | 1文件, 120 insertions(+), 40 deletions(-) |
| 59 | `e6d35a7` | 2026-10-07 | 文档：CPU 已到 quota 边缘（1.28% 限流）；规划最后一条官方 L1 lane | 5文件s, 163 insertions(+), 123 deletions(-) |
| 60 | `3795900` | 2026-10-07 | 文档：更正 pilot 的一个论断——ELO 只在 MultipleCombat 静态，SingleCombat 不是 | 2文件s, 45 insertions(+), 2 deletions(-) |
| 61 | `c00e686` | 2026-10-07 | 文档：真正的并发限制是突发性限流，不是平均 CPU 使用率 | 7文件s, 166 insertions(+), 124 deletions(-) |
| 62 | `4edb8de` | 2026-10-07 | 杂项：把 event watcher 重新对准仍在运行的 lane | 1文件, 4 insertions(+), 3 deletions(-) |
| 63 | `95feb58` | 2026-10-07 | 文档：扩充 1v1 退化记录，确认它不是数值发散 | 1文件, 44 insertions(+), 32 deletions(-) |
| 64 | `e12e05d` | 2026-10-07 | 文档：冻结 formal-6M campaign 产物（20261007_210033） | 49文件s, 2057 insertions(+), 553 deletions(-) |
| 65 | `895e730` | 2026-10-08 | 文档：冻结 formal-6M campaign 产物（20261008_000047） | 49文件s, 1871 insertions(+), 404 deletions(-) |
| 66 | `5bbc4ba` | 2026-10-08 | 实验：第 6 波——把 10v10 seed 1 和 5v5 seed 2 放进五个完成作业腾出的容量 | 8文件s, 215 insertions(+), 110 deletions(-) |
| 67 | `8fd154d` | 2026-10-08 | 修复：聚合吞吐行只统计在跑的 lane | 7文件s, 383 insertions(+), 314 deletions(-) |
| 68 | `fdd6b88` | 2026-10-08 | 文档：冻结 formal-6M campaign 产物（20261008_030053） | 48文件s, 1405 insertions(+), 352 deletions(-) |
| 69 | `8deab5a` | 2026-10-08 | 文档：冻结 formal-6M campaign 产物（20261008_060010） | 46文件s, 1263 insertions(+), 355 deletions(-) |
| 70 | `fe58eac` | 2026-10-08 | 文档：冻结 formal-6M campaign 产物（20261008_083023） | 45文件s, 1002 insertions(+), 308 deletions(-) |
| 71 | `fa4c6e9` | 2026-10-08 | 文档：冻结 formal-6M campaign 产物（20261008_092029） | 49文件s, 882 insertions(+), 235 deletions(-) |
| 72 | `ef2f0f9` | 2026-10-08 | 文档：正式实验文档全部转为中文，补齐结论一节，commit message 统一改中文 | 13文件s, 2049 insertions(+), 1837 deletions(-) |
| 73 | `a72f6f7` | 2026-10-08 | 文档：收尾主报告翻译的最后润色，并并入 hash 映射表 | 2文件s, 4 insertions(+), 2 deletions(-) |
| 74 | `d3c1995` | 2026-10-08 | 文档：第 14 节术语统一为「种子 0/1」，修正 hash 映射表的核验基准 | 2文件s, 7 insertions(+), 7 deletions(-) |

## 三、关于历史中文化的说明

2026-10-08 按用户要求，把该范围内的全部 commit message 从英文统一改写为中文。

- **只改 message，不改内容**：每个 commit 的 tree、作者/提交者身份与时间戳均逐条核对一致。
- 核验方式：`git diff backup/pre-chinese-rewrite fa4c6e9 --stat` 输出为空，
  其中 `fa4c6e9` 是改写刚完成时的 tip（其后新增的提交本身带内容改动，故不用 HEAD 做该核验）。
- **改写导致所有 commit hash 变化**（message 参与 hash 计算）。
- 改写前的完整状态保留在两处，均可回退：
  - tag `backup/pre-chinese-rewrite` → `6c5bd99`
  - branch `backup/formal-6m-english` → `6c5bd99`
  - 两者均已推送到远程，具备异地冗余
- 新旧 hash 逐条对应见 `experiments/2026-10-07-08-formal6m/status/commit_hash_mapping.md`。
- **已知影响**：pilot 自己记录的旧 hash（`docs/baseline_inventory.md` 的 `@ 60a3e2d`、
  `experiments/2026-10-04-night/manifest.csv` 的 `git_commit` 列）已失效，需用映射表回溯。
  远程分支 `exp/repro-scaling-20261004` 仍指向改写前的 `20f39d3`，**未被改动**。
