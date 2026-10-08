# commit hash 映射表（英文 message -> 中文 message）

2026-10-08 用 `git filter-branch --msg-filter` 把分支 `exp/formal-6m-20261007` 上 `main..HEAD` 的 71 个 commit message（改写时的全部内容）从英文改写为中文。
**除 message 外没有任何改动**：每个 commit 的 tree、author/committer 身份与时间戳都与旧 commit 逐条核对一致。改写后的 tip 是 `fa4c6e9`，`git diff backup/pre-chinese-rewrite fa4c6e9 --stat` 为空（只改 message，内容一个字都没变）；`main` 分支本身未动。

commit message 参与 commit hash 的计算，message 一改 hash 必变，所以：

- **pilot 的 `manifest.csv` 和 `docs/baseline_inventory.md` 里记录的旧 hash 已失效**，要用下面这张表回溯；旧 hash 与新 hash 之间没有前缀关系，不要前缀匹配。
- 备份（均未删除）：tag `backup/pre-chinese-rewrite` 与 branch `backup/formal-6m-english` 都仍指向旧的最终 commit `6c5bd99`；filter-branch 另外留下 `refs/original/refs/heads/exp/formal-6m-20261007`，同样指向 `6c5bd99`。
- 唯一无需翻译的 commit 是 `d133be63`（"导出了进展的pdf"，本来就是中文），其 message 逐字节未改；但它的父 commit 也被重写，所以它的 hash 仍然变了——71 个 commit 的 hash 全部变化。
- 改写完成之后本分支又新增了 2 个 commit（不属于本次改写，也不在本表里）：`ef2f0f9` 文档：正式实验文档全部转为中文，补齐结论一节，commit message 统一改中文；`a72f6f7` 文档：收尾主报告翻译的最后润色，并并入 hash 映射表。
- 表按时间顺序（旧 -> 新）排列，与 `git log --reverse` 的输出一致。

改写命令（filter-branch 要求工作区干净，而主工作区有实验监控在写的未提交文件，所以在一个干净的临时 worktree 里执行）：

```
git worktree add --detach <tmp> exp/formal-6m-20261007
git filter-branch --msg-filter 'python3 -I rewrite_msgs.py' main..exp/formal-6m-20261007
```

| 旧 hash | 新 hash | 中文标题 |
| --- | --- | --- |
| d0d9bd0 | 48bf779 | 杂项：搭建过夜实验基础设施，用于复现与 N-v-N 扩展 |
| e6dc095 | d0512c4 | 文档：官方 baseline 清单 + N-v-N 扩展性审计 |
| 353ea10 | bd51ce5 | 功能：metrics 采集、图表与实时状态工具 |
| 088c6bd | 06c8bf7 | 修复：把实验元数据写进日志，并对同一步的 metrics 记录取并集 |
| 02c5935 | 4e32506 | 功能：reward 归一化的跨 N critic 分析 + 扩展对比表 |
| eb3791f | 3ce1a26 | 文档：过夜复现与扩展性报告（实时草稿） |
| 100702c | c125039 | 功能：reward 归一化 critic 扩展性图表 |
| 45e4b2b | 4555043 | 实验：把 env-step 开销归因到物理仿真与观测工程 |
| d9dd61c | 0c66687 | 实验：离线评估器；MultipleCombat 的评估是确定性的 |
| 501461e | 986bd00 | 文档：两篇论文分析（58k agent-token 工作流）+ LAG 接口一节 |
| 64777b0 | 6e14c7c | 文档：可扩展 MARL 候选方向及证据强度台账 |
| 768c8a5 | 7320fd8 | 功能：给离线评估器加上团队协同代理指标 |
| e882431 | 3666422 | 实验：在 N=20 和 N=50 实测 critic，而不是外推 |
| 8b8bead | 0c55175 | 功能：逐实验资源采样与资源-对-N 图表 |
| 183f094 | 6b862eb | 文档：官方的 "FSP" 是 checkpoint 历史上的均匀采样，不是 FSP |
| d283229 | bd50337 | 实验：1e5-1e6 步后策略仍近似均匀（两种方法测量） |
| a9fdfe7 | 0183761 | 文档：诊断"学得慢"还是"学坏了"（critic 收敛，actor 几乎不动） |
| 0ac9e1c | 0e7310e | 文档：env-step 扩展的最小二乘拟合（N^1.64，R^2=0.999） |
| 691c219 | 86d0d45 | 功能：扩展表中加入 wall-clock 归一化 |
| f7ab37e | 31b182e | 功能：每次 sweep 自动生成可直接粘贴的报告表格 |
| 34851d3 | 40eb460 | 文档：reward/N 归一化只对 NoWeapon family 精确 |
| 14d5e72 | 5cf5822 | 文档：自我纠正——战斗 baseline 确实在学习，只是非常慢 |
| fbc182c | fa0c870 | 功能：遇到真实失败就提前退出的 watchdog 循环 |
| 9df7a34 | 193b41c | 功能：匹配步数的样本效率表 |
| f9b04b6 | c22ce59 | 文档：实测协同代理指标，以及它们支撑不了什么 |
| 49b33e8 | f0aac70 | 文档：用两篇论文的分析填充报告第 14-16 节 |
| 318e862 | e691226 | 文档：按所针对的实测失败排序的具体后续实验计划 |
| f9d8dfa | ccff3fb | 文档：按后续测量收紧 curse-of-multiagency 一节 |
| 607a6d3 | d2ffdd0 | 文档：用官方 2v2 baseline 验证生成的 scaling family |
| cefc843 | 7f573f1 | 功能：头条扩展性图表——每敌机 reward 对步数以及对 wall-clock |
| d9550d3 | 7a04ced | 文档：记录头条扩展性读数及其限制 |
| 411657f | b3ddea2 | 实验：归一化 critic 指标按 episode 平均，而不是单点 |
| c144989 | db31578 | 文档：用强化后的归一化数字同步 curse 一节 |
| 753658a | 428cdee | 文档：新增面向课题组的 SRTP 进展报告，含实验图表与导航 |
| 20f39d3 | c5bfbae | 文档：用最终数字收尾技术报告 |
| d133be6 | f6e84a1 | 导出了进展的pdf |
| ee51b29 | 5c8b7fb | 杂项：初始化 6M 正式实验 campaign |
| 2f549ad | bbeb5d7 | 实验：启动 6M 正式 campaign——四尺度 NoWeapon 扩展 + 官方 baseline |
| 48ff550 | 1fe6c67 | 实验：把四个官方 1v1 baseline 作为并行 lane 运行 |
| 67172f9 | d2a2cc1 | 实验：记录 9 lane 稳态标定与 1v1-shoot 的 budget 风险 |
| 0fa6a82 | 1c4b44d | 功能：campaign 参数化的分析管线 + 等样本/等 wall-clock 表 |
| 67a0595 | 3daf8e3 | 文档：表示/critic 扩展一节、失败 F10-F14、事故日志 |
| 4fb9c8f | 7e8e4a2 | 功能：campaign 结束 freeze 脚本，以及 critic 内存墙预测 |
| e3be6c8 | 635a77d | 文档：计算扩展性一节，依据本征 benchmark 拟合 |
| 98335a8 | 528a810 | 功能：只在真实事件上唤醒操作者的 event watcher |
| 187c779 | 7e80c60 | 文档：把六张必需的图嵌入报告 |
| 5155777 | 9c2beb0 | 文档：critic 扩展一节改用精确闭式替换拟合指数 |
| 2caac5d | ed3b352 | 修复：/proc/stat 在此容器中不可用——更正所有 CPU 数字（F16） |
| b405478 | 314e47c | 文档：记录 F17，可达步数预算的线程数量化 |
| 69882ec | 1fdb28c | 修复：按 lane 自身可达预算而非名义预算判定完成 |
| 0d11bda | cc88524 | 文档：CPU 更正后的修订排空计划 |
| a8425e3 | 74810c1 | 文档：记录在 CPU quota 用到 91% 时不再加第四个 seed 的决定 |
| 909a924 | eef285e | 功能：死亡开关——没有 agent 也能 freeze 并提交 |
| 9ec8332 | cfc033e | 功能：让报告自填充，交付物不再依赖存活的 agent |
| 75839a6 | 8504c27 | 文档：记录 hierarchical 1v1 lane 的真实退化，以及它并非发散的检查 |
| ed0f298 | 6c374c0 | 文档：写第 15、16 节——现在就写，因为两者都不依赖最终数字 |
| 5759636 | f5c114d | 修复：offline_eval 的默认对手是 NULL policy——其默认数字毫无意义（F18） |
| 6372848 | 3eeb00e | 文档：实测 episode 长度混杂，随后撤回它似乎要证明的那个更正 |
| 1feac2e | e6d35a7 | 文档：CPU 已到 quota 边缘（1.28% 限流）；规划最后一条官方 L1 lane |
| df4adeb | 3795900 | 文档：更正 pilot 的一个论断——ELO 只在 MultipleCombat 静态，SingleCombat 不是 |
| c589d04 | c00e686 | 文档：真正的并发限制是突发性限流，不是平均 CPU 使用率 |
| 8f411be | 4edb8de | 杂项：把 event watcher 重新对准仍在运行的 lane |
| d88ac6b | 95feb58 | 文档：扩充 1v1 退化记录，确认它不是数值发散 |
| 0068b28 | e12e05d | 文档：冻结 formal-6M campaign 产物（20261007_210033） |
| d127a40 | 895e730 | 文档：冻结 formal-6M campaign 产物（20261008_000047） |
| d8b8908 | 5bbc4ba | 实验：第 6 波——把 10v10 seed 1 和 5v5 seed 2 放进五个完成作业腾出的容量 |
| 31f14e5 | 8fd154d | 修复：聚合吞吐行只统计在跑的 lane |
| c60a17b | fdd6b88 | 文档：冻结 formal-6M campaign 产物（20261008_030053） |
| f4441cc | 8deab5a | 文档：冻结 formal-6M campaign 产物（20261008_060010） |
| 48dffca | fe58eac | 文档：冻结 formal-6M campaign 产物（20261008_083023） |
| 6c5bd99 | fa4c6e9 | 文档：冻结 formal-6M campaign 产物（20261008_092029） |

旧 message 标题（供对照）：

| 旧 hash | 英文标题 |
| --- | --- |
| d0d9bd0 | chore: add overnight experiment infrastructure for repro + N-v-N scaling |
| e6dc095 | docs: official baseline inventory + N-v-N scalability audit |
| 353ea10 | feat: metrics collection, figures and live status tooling |
| 088c6bd | fix: capture experiment metadata in the log, and union per-step metrics records |
| 02c5935 | feat: reward-normalised cross-N critic analysis + scaling comparison table |
| eb3791f | docs: overnight reproduction and scaling report (live draft) |
| 100702c | feat: figure for reward-normalised critic scaling |
| 45e4b2b | exp: attribute the env-step cost to physics vs observation engineering |
| d9dd61c | exp: offline evaluator; MultipleCombat evaluation is deterministic |
| 501461e | docs: two-paper analysis (58k-agent-token workflow) + LAG interface section |
| 64777b0 | docs: candidate scalable-MARL directions with evidence-strength ledger |
| 768c8a5 | feat: add team-coordination proxies to the offline evaluator |
| e882431 | exp: measure the critic at N=20 and N=50 instead of extrapolating |
| 8b8bead | feat: per-experiment resource sampling and a resource-vs-N figure |
| 183f094 | docs: the official "FSP" is uniform sampling over checkpoint history, not FSP |
| d283229 | exp: policies are still near-uniform after 1e5-1e6 steps (measured two ways) |
| a9fdfe7 | docs: diagnose slow vs broken learning (critic converges, actor barely moves) |
| 0ac9e1c | docs: least-squares fit of the env-step scaling (N^1.64, R^2=0.999) |
| 691c219 | feat: wall-clock normalisations in the scaling table |
| f7ab37e | feat: auto-generate paste-ready report tables each sweep |
| 34851d3 | docs: reward/N normalisation is exact only for the NoWeapon family |
| 14d5e72 | docs: self-correct -- combat baselines DO learn, just very slowly |
| fbc182c | feat: watchdog loop that aborts early on a real failure |
| 9df7a34 | feat: matched-step sample-efficiency table |
| f9b04b6 | docs: measured coordination proxies, and what they cannot support |
| 49b33e8 | docs: populate report sections 14-16 from the two-paper analysis |
| 318e862 | docs: concrete next-experiment plan ranked by which measured failure it targets |
| f9d8dfa | docs: tighten the curse-of-multiagency section against the later measurements |
| 607a6d3 | docs: validate the generated scaling family against the official 2v2 baseline |
| cefc843 | feat: headline scaling figure -- reward per enemy vs steps AND vs wall-clock |
| d9550d3 | docs: record the headline scaling reading with its limits attached |
| 411657f | exp: average the normalised critic metrics over episodes, not one point |
| c144989 | docs: sync the curse section with the strengthened normalised numbers |
| 753658a | docs: add group-facing SRTP progress report with experiment figures and navigation |
| 20f39d3 | docs: close out the technical report with final numbers |
| d133be6 | 导出了进展的pdf |
| ee51b29 | chore: initialize formal 6M experiment campaign |
| 2f549ad | exp: launch 6M formal campaign -- four-scale NoWeapon scaling + official baselines |
| 48ff550 | exp: run the four official 1v1 baselines as parallel lanes |
| 67172f9 | exp: record 9-lane steady-state calibration and the 1v1-shoot budget risk |
| 0fa6a82 | feat: campaign-parameterised analysis pipeline + equal-sample/wall-clock tables |
| 67a0595 | docs: representation/critic scaling section, failures F10-F14, incident log |
| 4fb9c8f | feat: end-of-campaign freeze script, plus the critic memory-wall projection |
| e3be6c8 | docs: computational scalability section, fitted from the intrinsic benchmark |
| 98335a8 | feat: event watcher that wakes the operator only on real events |
| 187c779 | docs: embed the six required figures in the report |
| 5155777 | docs: replace fitted exponents with exact closed forms in the critic-scaling section |
| 2caac5d | fix: /proc/stat is unusable in this container -- correct every CPU figure (F16) |
| b405478 | docs: record F17, the thread-count quantisation of the reachable step budget |
| 69882ec | fix: judge lane completion against its own reachable budget, not the nominal one |
| 0d11bda | docs: revised drain plan after the CPU correction |
| a8425e3 | docs: record the decision not to add a fourth seed at 91% of CPU quota |
| 909a924 | feat: dead-man's switch -- freeze and commit without the agent |
| 9ec8332 | feat: make the report self-filling, so the deliverable no longer needs a live agent |
| 75839a6 | docs: record a real degradation in the hierarchical 1v1 lane, and the check that it is not divergence |
| ed0f298 | docs: write sections 15 and 16 -- written now because neither depends on final numbers |
| 5759636 | fix: offline_eval's default opponent is a NULL policy -- its default numbers are meaningless (F18) |
| 6372848 | docs: measure the episode-length confound, then withdraw the correction it appeared to justify |
| 1feac2e | docs: CPU is now at the quota edge (1.28% throttling); plan the last official L1 lane |
| df4adeb | docs: correct a pilot claim -- ELO is static only for MultipleCombat, not for SingleCombat |
| c589d04 | docs: the real concurrency limit is bursty throttling, not average CPU usage |
| 8f411be | chore: retarget the event watcher at the lanes still running |
| d88ac6b | docs: extend the 1v1 degradation record and confirm it is not numerical divergence |
| 0068b28 | docs: freeze formal-6M campaign artefacts (20261007_210033) |
| d127a40 | docs: freeze formal-6M campaign artefacts (20261008_000047) |
| d8b8908 | exp: wave 6 -- 10v10 seed 1 and 5v5 seed 2 into the capacity freed by five completions |
| 31f14e5 | fix: count only live lanes in the aggregate throughput line |
| c60a17b | docs: freeze formal-6M campaign artefacts (20261008_030053) |
| f4441cc | docs: freeze formal-6M campaign artefacts (20261008_060010) |
| 48dffca | docs: freeze formal-6M campaign artefacts (20261008_083023) |
| 6c5bd99 | docs: freeze formal-6M campaign artefacts (20261008_092029) |
