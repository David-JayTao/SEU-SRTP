# 实验成果归档说明（`experiments/_archive`）

- 归档时间：2026-10-08 12:28（CST）
- 仓库：`/root/autodl-tmp/SEU-SRTP`（分支 `exp/formal-6m-20261007`）
- 范围：2026-10-07 ~ 10-08 正式实验（formal6m）与 `scripts/results` 下全部历史实验的曲线、最终权重、启动配置
- 原则：**只复制（`cp -a`）、不移动、不删除**；`scripts/results` 原件是最终真相来源
- 本目录的 Git 提交由主会话执行；本归档过程自身不执行任何 git 操作

## 1. 归档时间与前提

训练已于 2026-10-08 10:00 全部结束（无 tmux server、无 `train_jsbsim` 进程）；`scripts/results` 最后一次写入时间为 10:26。归档开始时确认无任何进程在写入，未中断、未触碰任何正在使用的文件。

## 2. 来源路径

| 内容 | 来源 |
|---|---|
| 训练曲线、最终权重 | `/root/autodl-tmp/SEU-SRTP/scripts/results` |
| 启动队列（queue_*.txt） | `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m/configs` |
| 场景 YAML 快照 | `/root/autodl-tmp/SEU-SRTP/envs/JSBSim/configs` |

所有来源文件均原地保留，未移动、未修改（校验见 §8）。

## 3. 目录约定

```
_archive/
├── README.md                     # 本文档
├── ARCHIVE_MANIFEST.csv          # 逐文件清单（列：experiment / artifact_type / original_path / archive_path / bytes / sha256_short / status）
├── curves/<实验ID>/metrics.jsonl             # 训练+eval 曲线数据（44 个实验）
├── checkpoints/<实验ID>/actor_latest.pt      # 最终权重（47 个实验 × actor+critic，共 94 个文件）
├── checkpoints/<实验ID>/critic_latest.pt
├── configs/queue_*.txt                       # 14 份启动队列（formal6m）
├── configs/scenarios/<相对路径>.yaml         # 7 份 scaling_*/10v10 场景快照
└── gitignore_proposal.md / proposed_gitignore.txt   # 此前 .gitignore 普查产出的提案（原样保留）
```

- `<实验ID>` 取运行目录（runN）的父目录名（如 `f6m_5v5_noweapon_s0`、`official_heading`），经核对全局唯一，不会重名覆盖。
- 权重文件名保持原名（`actor_latest.pt` / `critic_latest.pt`），便于程序直接加载。
- 清单汇总行（`experiment=__SUMMARY__`）的 `artifact_type` 在无对应产物类型时记 `other`，`archive_path` 列填写未归档原因。

## 4. 归档内容统计

| 类型 | 数量 | 体积 | 说明 |
|---|---|---|---|
| curve | 44 | 2,793,930 B（2.66 MiB） | 全部 44 个 metrics.jsonl，一个不漏 |
| checkpoint | 94 | 69,628,927 B（66.40 MiB） | 47 个实验 ×（actor_latest + critic_latest）；含 3 个 SMOKE 冒烟实验（只有权重、没有曲线） |
| config | 21 | 19,918 B | 14 份 queue_*.txt + 7 份场景 YAML |
| **归档产物合计** | **159** | **72,442,775 B（69.09 MiB）** | |
| 清单汇总行 | 2 | — | skipped_too_large ×1、excluded_by_policy ×1 |
| 策略池（未归档） | 4,809 | 3,096,657,101 B（2953.20 MiB） | 见 §5.1 |
| 原件总量（未变） | 4,947 | 3,169,079,958 B（3022.27 MiB） | scripts/results 复制前后完全一致 |

- 最大单文件：`checkpoints/scaling_10v10_noweapon_s2/critic_latest.pt` = 1,868,230 B（1.78 MiB）。
- 44 份曲线对应实验包括：`f6m_*` 12 条训练通道及相关历史实验（`scaling_*`、`official_*`、`f6m_*_s1/s2`、`heading` 等）；完整列表见 `ARCHIVE_MANIFEST.csv`。

## 5. 未归档内容及原因

### 5.1 策略池逐 episode 检查点 —— `skipped_too_large`

- 内容：`scripts/results/**/<实验>/runN/actor_<数字>.pt` 与 `critic_<数字>.pt`，共 4,809 个、2953.20 MiB。
- 原因：单文件不大（约 0.3–1.8 MiB），但整体近 3 GB，远超归档体积预算；且按项目规范（CLAUDE.md §2.2），逐 episode 策略池属于可重建的大体积中间产物，**留在服务器**。
- 位置（原封未动）：`/root/autodl-tmp/SEU-SRTP/scripts/results/.../<实验>/runN/` 内。
- 如需某实验的中间快照，直接按上述路径从服务器复制对应 `actor_<步数>.pt` 即可。

### 5.2 按策略排除 —— `excluded_by_policy`

- Python 缓存（`__pycache__/`、75 个 `*.pyc`，合计 947,188 B）：可由代码重建，不入归档。
- 凭据类（`.env`、`*.pem`、`*.key`）：安全红线，实测 0 命中，一律不写入归档。
- 临时文件（`*.tmp`、`*.swp`）：0 命中。
- `*.acmi` / `*.npy`：实测 0 命中（本次训练输出中不存在轨迹回放/中间数组文件）。
- 空 run 目录 2 个：`SMOKE_heading/run1`、`official_1v1_shoot_hier_vsbaseline/run1`（完全为空，无内容可归档）。

### 5.3 本树范围之外（仍在原目录，未搬动）

- 报告、表格、图表：`experiments/2026-10-07-08-formal6m/` 下的 `metrics/`（scaling 对比表与曲线 CSV）、`figures/`、`manifest.csv`、`status/`、`logs/`、`system/`、`scripts/` 仍在原目录，由主会话按需提交 Git。
- 场景 YAML 只归档了用于本次训练的 scaling_*/10v10 共 7 份；其余场景配置（1v1、heading 等）本就随代码在 Git 中跟踪，未重复复制。

## 6. 与 Git / Git LFS 的判断

> 依据 CLAUDE.md §2.4：最大单文件 < 50 MB 且新增总量 < 300 MB → 用普通 Git，不启用 LFS。

- 归档产物最大单文件 1.78 MiB；新增总量 69.09 MiB。
- **结论：无需 Git LFS**，普通 commit 即可（LFS 免费配额 1 GB 不受影响）。
- 无超过 GitHub 限制的文件，无需额外付费备份；若需异地备份，建议在服务器侧打压缩包（3 GB 策略池不随 Git 走）。

## 7. 如何从归档还原一次分析

```bash
cd /root/autodl-tmp/SEU-SRTP/experiments/_archive

# 1) 读训练曲线（JSONL，每行一条记录，含 training/eval 指标）
/root/miniconda3/envs/jsbsim/bin/python -c "
import json
rows = [json.loads(l) for l in open('curves/f6m_5v5_noweapon_s0/metrics.jsonl')]
print(len(rows)); print(rows[-1])"

# 2) 加载最终权重（CPU 可读）
/root/miniconda3/envs/jsbsim/bin/python -c "
import torch
ck = torch.load('checkpoints/f6m_5v5_noweapon_s0/actor_latest.pt', map_location='cpu')
print(type(ck))"

# 3) 对照实验时所用场景配置（应与原始 YAML 逐字节一致）
diff configs/scenarios/5v5/scaling_noweapon/HierarchySelfplay.yaml \
     /root/autodl-tmp/SEU-SRTP/envs/JSBSim/configs/5v5/scaling_noweapon/HierarchySelfplay.yaml
```

- 精确超参数与随机种子：见 `configs/queue_*.txt`（每行一个作业：`实验ID|线程数|总步数|…|附加参数`，含 `--seed` 等）与 `experiments/2026-10-07-08-formal6m/scripts/` 下的启动脚本。
- 复现评测：用上面的 actor/critic 权重 + 对应场景 YAML 走 `runner/` 的 eval 流程。
- 需要中间步数权重时回服务器取 `scripts/results/.../runN/actor_<步数>.pt`（见 §5.1）。

## 8. 完整性与安全校验记录

- 复制前 `scripts/results`：4,947 个文件 / 3,169,079,958 B；复制后：**完全相同**（逐文件计数与字节求和）。
- 每个副本复制后逐文件核对：字节数一致 + sha256 一致，159/159 通过。
- 抽查 3 份曲线 + 3 份权重（sha256 前 12 位）：

| 文件 | sha256（前 12 位） | 结果 |
|---|---|---|
| curves/f6m_5v5_noweapon_s0/metrics.jsonl | 11ede61492a2 | 与原件一致 |
| curves/f6m_10v10_noweapon_s0/metrics.jsonl | 51a53cdfbddf | 与原件一致 |
| curves/official_heading/metrics.jsonl | e608b1680593 | 与原件一致 |
| checkpoints/f6m_official_2v2_noweapon_s0/actor_latest.pt | dd834c881218 | 与原件一致 |
| checkpoints/scaling_3v3_shoot/critic_latest.pt | 1baf3ccd97f7 | 与原件一致 |
| checkpoints/f6m_official_heading_s5/actor_latest.pt | 0756a8a505a8 | 与原件一致 |

- 时间戳：`cp -a` 保留原 mtime（抽查 `f6m_5v5_noweapon_s0/actor_latest.pt` 两侧均为 `2026-10-07 23:51:02.685245582`）。
- 全过程只使用 `mkdir` / `cp -a` / `find` / `sha256sum` / 只读 Python；**未执行任何 `mv`、`rm`，未写入原件目录**。

## 9. 维护约定

- 后续每轮实验完成后按 CLAUDE.md §二自动追加：曲线 → `curves/<实验ID>/`，最终权重 → `checkpoints/<实验ID>/`，配置 → `configs/`，并同步更新 `ARCHIVE_MANIFEST.csv` 与本文档统计。
- 追加归档同样要求：复制前核对原件计数与总字节，复制后逐文件 sha256 比对，仅在无进程写入时执行。
