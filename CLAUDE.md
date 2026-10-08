# SEU-SRTP 项目工作规范

本文件是本仓库对 Claude Code 的**强制约定**。每次会话开始时应被视为已经读过。

项目：LAG（JSBSim 空战仿真）环境下的多智能体强化学习，研究
curse of multiagency / scalability / sample efficiency / 集中式 critic 扩展性。
负责人：刘酝潇。

---

## 一、Commit Message 一律用中文

**所有 git commit message 必须用中文书写。** 不得用英文。

标题行格式：`类型：简短动作描述`，动词开头，不超过约 40 字。

| 类型 | 用途 | 示例 |
|---|---|---|
| `实验：` | 启动/完成实验、修改实验参数 | `实验：完成 MAPPO 6M 步训练` |
| `修复：` | 修 bug、修工程错误 | `修复：解决训练中断问题` |
| `优化：` | 性能、吞吐、资源利用 | `优化：提升并行采样效率` |
| `文档：` | 报告、说明、分析 | `文档：更新实验结果分析` |
| `功能：` | 新增脚本、工具、管线 | `功能：新增实验归档脚本` |
| `杂项：` | 基建、目录整理、依赖 | `杂项：搭建实验基础设施` |

正文（可选）说明**为什么**这么改、验证方式、以及有没有留下已知限制。
正文也必须是中文。

**保留英文原样的内容**：文件名、路径、函数名、类名、实验 ID
（如 `f6m_10v10_noweapon_s0`）、命令行参数、代码符号（如 `share_obs`）、
超参数名（如 `n_rollout_threads`）、失败编号（如 F16）、状态枚举
（如 `completed_6M`、`time_cutoff`）。

`Co-Authored-By:` 之类的 trailer 按 harness 要求保留英文。

**写作用语**：如实记录失败与自我更正。如果之前的判断是错的，commit 里要写明
「原判断是什么、错在哪、如何更正」，不要悄悄改掉。这个项目的历史记录里
有价值的一部分正是这些更正过程（见 `docs/night_failures.md`、`status/incidents.md`）。

---

## 二、每轮实验结束后必须自动归档

一轮实验（一次通宵、一次正式 campaign）结束后，**在推送之前**完成以下归档：

### 2.1 必须保存的内容

1. **训练曲线**：每个实验的 `metrics.jsonl`（这是最有价值的产物，体积小、
   含全部训练与 eval 记录）。复制到 `experiments/_archive/curves/<实验ID>/`。
2. **最终权重**：`actor_latest.pt` / `critic_latest.pt`（每个约 600 KB）。
   复制到 `experiments/_archive/checkpoints/<实验ID>/`。
3. **配置与种子**：启动脚本、queue 文件、场景 YAML 的快照、随机种子。
4. **表格与图表**：所有 CSV / JSON 指标、所有 PNG 图。
5. **报告与结论**：实验报告、状态台账、故障记录。
6. **评测数据**：`offline_eval` 结果、探针输出。

### 2.2 明确不进 Git 的内容

- 逐 episode 的策略池检查点（`actor_<数字>.pt` / `critic_<数字>.pt`）——
  动辄数 GB，且可复现。**留在服务器**，在归档 README 里写明其位置。
- 缓存、`__pycache__`、临时文件、重复依赖。
- 任何凭据、私钥、token、`.env`。

### 2.3 归档操作规范

- **只用 `cp` 复制，绝不 `mv` / `rm` 原件**。服务器原件是最后的真相来源。
- 归档树按 `<实验ID>/` 分目录，防止重名覆盖。
- 生成 `experiments/_archive/ARCHIVE_MANIFEST.csv`，逐文件记录：
  `experiment, artifact_type, original_path, archive_path, bytes, sha256_short, status`。
- **不能上传的必须写明原因**，不得假装已归档。在 README 与清单里都标注
  `skipped_too_large` 或 `excluded_by_policy`。
- 复制后抽样比对 sha256，确认副本与原件逐字节一致，且原件数量未变。

### 2.4 文件大小与 Git LFS 的判断标准

GitHub 的限制（用于判断，不必每次都重新查）：

- 单文件 **> 100 MiB**：推送会被拒绝；**> 50 MiB** 会告警。
- 仓库建议 **< 1 GB**；接近 5 GB 会被要求瘦身。
- Git LFS 免费额度：**1 GB 存储 + 1 GB/月流量**。

**判断规则**：归档前先看**最大单文件**体积。

- 若最大单文件 < 50 MB 且新增总量 < 300 MB → **直接用普通 Git，不要启用 LFS**。
  这种规模下 LFS 只会白白占用 1 GB 配额、并让别人的 clone 变麻烦。
- 若确有大文件（模型权重、数据集、视频）→ 才引入 LFS，写 `.gitattributes`
  并在 README 记录已用配额。
- 无论哪种情况，**都要在归档清单里报告实际体积**，并把超出限制的文件列入
  「未上传」并给出额外备份方案（服务器留存 / 网盘 / 对象存储）。

---

## 三、提交与推送规范

1. 每轮实验完成后，**在合适的检查点提交 Git**：先提交归档与文档，再推送。
2. 推送前先检查远程状态：`git ls-remote <remote>` 与 `git status`，
   确认远程分支有没有被别人推进过。
3. 优先 **fast-forward**。**禁止 `git push --force`**，
   禁止删除远程历史或覆盖他人成果。
4. 若必须重写历史：**先建备份 ref**（tag 或分支），确认涉及的分支
   **确实没有推送到共享远端**之后才能做；一旦涉及已共享历史，
   改为生成「中文 Commit 历史索引」并**报告给用户确认**，不要擅自重写。
5. 推送后**重新拉取远程状态**，核验目标分支的 commit hash 与关键文件确实同步成功。
6. 保留实验分支与备份分支，不要为了「干净」删除它们。

---

## 四、服务器关闭 / 释放前

服务器准备关机或释放时，按以下顺序检查：

1. **确认重要实验成果已经上传**：`git status` 干净、关键分支已推送到远端、
   归档清单里的文件确实在远程可见。
2. **确认有可靠备份**：远端至少有实验分支 + 备份分支两个 ref。
3. **确认没有正在写入的文件被归档**：训练进程还在跑时，
   只归档**已完成**的实验与安全快照，不要碰正在写的文件，也不要中断训练。
4. 把「未上传清单」写进报告，说明原因与后续方案。

---

## 五、实验纪律

- **不得为了让结果好看而修改算法**：reward、网络、学习率、gamma、entropy、
  clip、PPO epoch、self-play 算法、观测/动作语义，正式实验中一律不动。
- 修明确的工程 bug 是允许的，但必须记录：原行为、错误、原因、修改、验证、
  是否影响算法语义。
- **不得过度解读**。区分 `事实 / 观察 / 假设 / 不能结论` 四个层级。
  单 seed 只能给趋势，不能给统计结论。
- **失败必须记录**，并归入正确类别：`Code / Computational / Representation /
  Sample / Algorithmic / Coordination scalability / Other`。
  不得把工程问题包装成算法结论。
- 实验预算若与官方不同（例如 6M 而非官方 1e8），必须**明确声明是预算削减**，
  不能声称已复现官方完整收敛。

---

## 六、环境备忘（本服务器）

- conda 环境：`jsbsim`（Python 3.12，torch 2.8.0+cu128）。Python 路径
  `/root/miniconda3/envs/jsbsim/bin/python`。
- **CPU 才是瓶颈，不是 GPU**。GPU 显存每作业 < 2.5 GB，利用率常年个位数百分比。
- 判定 CPU 用量**必须**用容器自身 cgroup `cpu.stat usage_usec`，
  配额读 `/sys/fs/cgroup/cpu.max`（本机 4800000/100000 = 48 核）。
  **`/proc/stat` 在本容器里报的是宿主机 192 个逻辑核，不可用**（见 F16）。
- 长任务一律用 `tmux`，不要挂在会话里。
- 需要无人值守收口时用 `experiments/*/scripts/auto_finalize.sh` 那套模式
  （独立 tmux + 定时快照 + 最终冻结提交）。
- 推送用 SSH deploy key：remote `ssh-origin` = `git@github-seu-srtp:David-JayTao/SEU-SRTP.git`
  （见 `~/.ssh/config`）。HTTPS 的 `origin` **没有**配置凭据，推不了。
