# 运行中的任务 — 正式 6M 实验（2026-10-07 → 2026-10-08）

启动于 **2026-10-07 02:54:31 CST**（第 1 波）、**03:10:14**（第 2 波）。
硬截止时间 **2026-10-08 10:00 CST**。
分支：`exp/formal-6m-20261007`。

预算定义：`--num-env-steps 6e6` = **6,000,000 个向量化环境步**，*不是* agent 步。已对照 runner
自身的记账方式验证：`total_num_steps` 每次按 `n_rollout_threads × buffer_size` 递增（buffer_size
固定为官方的 3000），例如 20 线程 → 每次 update 60,000 步。
6M 是*正式预算*下的复现，不是官方的 100M 收敛预算。

**episode 数是精确的，因此 6M 会被精确达到**——runner 计算
`episodes = num_env_steps // buffer_size // n_rollout_threads`
（`runner/share_jsbsim_runner.py:72`、`runner/jsbsim_runner.py:41`），而
`6e6 / (3000 × threads)` 对这里用到的每个通道都能整除：

| 规模 | 线程 | 步/update | episodes | 精确总量 |
|---|---|---|---|---|
| 2v2 / official 2v2 | 4 | 12,000 | 500 | 6,000,000 |
| 3v3 / 5v5 | 8 | 24,000 | 250 | 6,000,000 |
| 10v10 | 20 | 60,000 | 100 | 6,000,000 |

（这*不是*自动成立的：2026-10-04 的 pilot（前序试跑）在 18 线程下损失了其名义 900,000 步
中的 36,000 步，因为 `900000 // 54000 = 16` 个 episode，即 864,000。）

---

## 第 1 波 — 启动于 02:54:31

| tmux | 实验 ID | 场景 | 算法 | 种子 | GPU | 线程 | 目标 | 上限 | 实测 FPS | ETA（自 03:11 起算） |
|---|---|---|---|---|---|---|---|---|---|---|
| `f6m_10v10` | `f6m_10v10_noweapon_s0` | `10v10/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 2 | 20 | 6e6 | 108000 s | **70** | **03:00 Oct 8** |
| `f6m_5v5` | `f6m_5v5_noweapon_s0` | `5v5/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 1 | 8 | 6e6 | 108000 s | **85** | 22:45 Oct 7 |
| `f6m_3v3` | `f6m_3v3_noweapon_s0` | `3v3/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 8 | 6e6 | 108000 s | **133** | 15:40 Oct 7 |
| `f6m_2v2` | `f6m_2v2_noweapon_s0` | `2v2/scaling_noweapon/HierarchySelfplay` | mappo | 0 | 0 | 4 | 6e6 | 108000 s | **84** | 23:00 Oct 7 |
| `f6m_off2v2` | `f6m_official_2v2_noweapon_s0` | `2v2/NoWeapon/HierarchySelfplay` *（L1 官方）* | mappo | 0 | 1 | 4 | 6e6 | 108000 s | **79** | 00:15 Oct 8 |

**03:11 的总吞吐 = 451 env-steps/s**（五个 FPS 值之和）。
按当前速率，这五个任务都预计在截止时间*之前*达到 6M。

## 第 2 波 — 启动于 03:10:14（P1 官方 SingleCombat 系列）

两个通道，各 3 个 rollout 线程，每个通道顺序运行两个基线。
仅在第 1 波实测确认仍留有 CPU 余量后才加入（03:11 时 48 核配额中有 42 核忙碌）。

| tmux | 通道队列 | 任务顺序 | env/场景 | 算法 | 种子 | GPU | 线程 |
|---|---|---|---|---|---|---|---|
| `f6m_1v1sp` | `configs/queue_1v1a.txt` | 1. `f6m_official_1v1_selfplay_s1` 2. `f6m_official_1v1_shoot_hier_selfplay_s1` | `1v1/NoWeapon/Selfplay`，然后 `1v1/ShootMissile/HierarchySelfplay` *（均为 L1）* | ppo | 1 | 0 | 3 |
| `f6m_1v1vs` | `configs/queue_1v1b.txt` | 1. `f6m_official_1v1_vsbaseline_s1` 2. `f6m_official_1v1_hier_selfplay_s1` | `1v1/NoWeapon/vsBaseline` *（L1）*，然后 `1v1/NoWeapon/HierarchySelfplay` *（L2）* | ppo | 1 | 1 | 3 |

`1v1/ShootMissile/HierarchySelfplay` 以 `--use-prior` 启动，与官方 `scripts/train_selfplay_shoot.sh`
一致。`--use-prior` 只存在于 `algorithms/ppo/ppo_actor.py`（出现 5 次）；它对 mappo 没有意义，
因此没有任何 MultipleCombat 任务传入它。

**明确未运行**：`1v1/ShootMissile/HierarchyVsBaseline`——它是唯一一个完全无法运行的官方配置
场景（pilot 故障 F9：在第一个 env step 就挂掉，报
`TypeError: 'NoneType' object is not subscriptable`，位于
`envs/JSBSim/tasks/singlecombat_with_missle_task.py:226`）。它被记为
`not_applicable`，而不是本次实验的故障。

## 总线程预算

| 通道 | 线程 |
|---|---|
| `f6m_10v10` | 20 |
| `f6m_5v5` | 8 |
| `f6m_3v3` | 8 |
| `f6m_2v2` | 4 |
| `f6m_off2v2` | 4 |
| `f6m_1v1sp` | 3 |
| `f6m_1v1vs` | 3 |
| **总计** | **50** |

03:11 实测占用：**48 核 cgroup 配额中的 42.0 核（88%）**。
GPU 分配是随意的——每块 GPU 显存占用约 1.2 GB，GPU 利用率
0–12%；**CPU 才是真正的约束**，因此调度目标是总有效 env-steps/s，而不是把 GPU 填满。

## 启动命令

```bash
cd experiments/2026-10-07-08-formal6m
tmux new-session -d -s <lane> "bash scripts/run_queue_lane.sh <gpu_id> configs/<queue>.txt; exec bash"
```

第 1 波使用 `scripts/run_queue.sh`，它仅依据 `gpu_id` 推导状态台账——因此两个 GPU0 通道
（3v3、2v2）和两个 GPU1 通道（5v5、off2v2）共用一个台账文件。第 2 波使用
`scripts/run_queue_lane.sh`，这是一个改为以队列文件名作为台账键的副本。原脚本保持
未动，因为正在运行的 bash 脚本不能就地编辑。

`run_train.sh` 逐字复现官方 `scripts/*.sh` 的超参数
（lr 3e-4、gamma 0.99、ppo-epoch 4、clip 0.2、max-grad-norm 2、entropy 1e-3、
hidden 128×128、act-hidden 128×128、recurrent 128×1、data-chunk 8、
num-mini-batch 5、buffer-size 3000），只有两处已记录的兼容性
偏差（不使用 wandb；`--clip-param` 按默认值显式传入）。
相对官方的运行层面偏离：`num_env_steps` 1e8→6e6，
`n_rollout_threads` 32→{3,4,8,20}。除此之外没有别的。

## 已知的测量注意事项

- **`rc` 没有意义。** `run_train.sh:102-104` 从一条 `python … | tee` 管道中捕获
  `$?` 而没有启用 `pipefail`，因此每个任务都记录为 `exited with code 0`——包括崩溃和
  SIGINT 超时。故障必须从日志正文中识别（TypeError / EOFError / 步数停滞），这正是
  `scripts/watch_f6m.py` 和 `scripts/os_watchdog.sh` 所做的。
- **没有任何东西会自动重启。** `scripts/train/train_jsbsim.py:107-133` 总是分配下一个
  空闲的 `run<N>` 目录，且没有任何启动器暴露 `--model-dir`，因此重新启动会在 `run2/`
  里悄悄开始一次*全新*运行，而拼接出来的轨迹将无法解释。因此重启是一个经过
  深思熟虑的决定，记录在 `status/incidents.md`。

## 需要在报告中披露的偏离

1. **`n_rollout_threads` 随规模不同**（2v2=4、3v3=8、5v5=8、10v10=20）。
   这是墙钟时间逼出来的：在固定线程数下，10v10 无法在窗口内达到 6M。
   后果：PPO 的 update batch 为 `n_rollout_threads × 3000`，即 N=2/3/5/10 时分别为
   12k / 24k / 24k / 60k 个样本。**这对跨 N 比较是一个真实的混淆因素，并已如实记录。**
   它在各种子之间恒定，因此种子方差比较和同 N 比较仍然干净。
2. 官方基线保留官方的 `--eval-interval 1`；生成的 scaling 配置使用
   `--eval-interval 2`（与 2026-10-04 的 pilot 一样），以削减 eval 开销。Eval 在独立的
   env 中运行，不影响训练。
3. `2v2/NoWeapon/HierarchySelfplay`（官方）与 `2v2/scaling_noweapon/`
   （生成）的差异只有 0.005° 的经度编队偏移；两者都跑，这样官方基线不受污染，
   scaling 序列也保持内部一致。

## 已被第 1 波取代

2026-10-04 那次实验的运行属于 **pilot / 探索性**（全部 ≤1.48M 步；29 个完成的运行中
23 个被墙钟上限杀掉，6 个提前干净退出，1 个在 5 秒内崩溃）。它们作为 pilot 曲线保留，
与 6M 正式运行分开绘图。没有任何一个被延续成正式的 6M 运行。

## 监控

```bash
python experiments/2026-10-07-08-formal6m/scripts/watch_f6m.py
```

写入 `metrics/status.json`、`status/monitor_latest.md`，并追加到
`metrics/throughput_history.csv`。`tmux f6m_watch` 另外运行
`scripts/os_watchdog.sh 600`，它追加写入 `system/system_samples.csv` 和
`system/events.log`，并且能在 Claude/VS Code 会话死掉后继续存活。

---

# 2026-10-07 17:35 的状态（已过 14.7 h）

## 已完成（达到完整预算）

| 实验 | 步数 | 目标 | FPS | 释放的通道 |
|---|---|---|---|---|
| `f6m_3v3_noweapon_s0` | **6,000,000** | 6,000,000 | 125 | 16:12（8 线程） |
| `f6m_official_1v1_vsbaseline_s1` | **5,994,000** | 6,000,000 | 122 | 16:45（3 线程） |

两者都干净退出（没有泄漏的 worker；队列台账显示 `queue drained`）。

**1v1 通道无法达到 6,000,000**——见下文"粒度"一节。5,994,000 是它们可达到的最大值，
即名义预算的 99.9%，因此记为 `completed` 而不是 `time_cutoff`。

## 第 4 波 — 第二种子，启动于 17:20 和 17:27

| tmux | 实验 | 场景 | 种子 | GPU | 线程 | 启动 | 预计 |
|---|---|---|---|---|---|---|---|
| `f6m_5v5s1` | `f6m_5v5_noweapon_s1` | `5v5/scaling_noweapon/HierarchySelfplay` | 1 | 2 | 10 | 17:20 | ~09:30–10:00 → 很可能在 5.9M 附近 `time_cutoff` |
| `f6m_3v3s1` | `f6m_3v3_noweapon_s1` | `3v3/scaling_noweapon/HierarchySelfplay` | 1 | 0 | 8 | 17:27 | ~06:50 → 应能完成 |

遵循的优先级顺序（任务书 §14 节）：先 5v5 第二种子（仍然可行的最高优先级规模），
然后 3v3——之所以选它而不是 2v2，是因为 pilot 在 N=3 测到了**最大**的种子间离散度
（7.66 reward/N，超过任何跨规模差距），是现有信息量最大的方差数据点。

两者使用与种子 0 完全相同的配置、算法和超参数；**只有 `--seed` 不同**。

## 粒度：可达到的步数预算被线程数量化

runner 计算 `episodes = num_env_steps // buffer_size // n_rollout_threads`
（`runner/share_jsbsim_runner.py:72`），因此达到的总量为
`episodes × 3000 × threads`：

| 线程 | episodes | 达到的步数 | 相对 6M |
|---|---|---|---|
| 3 | 666 | **5,994,000** | 99.9% |
| 4 | 500 | 6,000,000 | 100% |
| 8 | 250 | 6,000,000 | 100% |
| 10 | 200 | 6,000,000 | 100% |
| 20 | 100 | 6,000,000 | 100% |

**教训**：线程数必须能整除 `6e6 / 3000 = 2000`，否则名义预算在构造上就不可达——
而且是静默的，没有任何报错。3 线程的 1v1 通道是唯一受影响的（4 线程本可精确达到 6M）。
记为 F17；不"修复"，因为改动意味着要重启到一个 `run2/`。

## CPU 测量已修正（F16）

17:23 之前的所有 CPU 数字都来自 `/proc/stat`，它在这个容器里上报的是**宿主机的**
192 个 CPU，返回的增量在 0 和约 200 核之间来回跳。它们是**错误的**，不得使用。
权威的测量方式是容器自己的 cgroup `cpu.stat`：

- 本次实验 CPU：**48 核配额中的约 38–42 核（约 80–87%）**
- `nr_throttled`：**占周期的 0.02–0.04%**——配额**从未构成约束**

所以早先"我们已经 48/48 打满、没有余量"的结论是假象，而上面那两个第二种子正是
部分利用这份余量启动的。
