# 失败与修复记录（2026-10-04 通宵实验）

负责人：刘酝潇
格式统一为：Failure ID / Experiment / Symptoms / Cause / Code location / Fix /
Verification / Category。

**Category 取值**（严格区分，避免把工程问题包装成算法问题）：
`Code scalability` / `Computational scalability` / `Representation scalability` /
`Sample scalability` / `Algorithmic scalability` / `Coordination scalability` / `Other`

---

## F1 — JSBSim 气动数据缺失，环境完全无法初始化

- **Failure ID**: F1
- **Experiment**: 全部（首次 smoke test 即失败）
- **Symptoms**:
  ```
  Could not open file: Path ".../envs/JSBSim/utils/../data/aircraft/f16/f16.xml"
  JSBSim failed to open the configuration file
  Attempt to divide by zero in method FGColumnVector3::operator/(const double scalar)
  A proper axis type has NOT been selected. Check your aerodynamics definition.
  ```
- **Cause**: `envs/JSBSim/data` 是一个 **git submodule**（`.gitmodules` 指向
  `https://github.com/JSBSim-Team/jsbsim.git`），克隆仓库时未初始化，目录为空。
  这不是代码 bug，是环境搭建步骤缺失。
- **Code location**: `.gitmodules`；`envs/JSBSim/core/simulatior.py` 中
  `FGFDMExec` 加载 `aircraft/f16/f16.xml`
- **Fix**: `git submodule update --init --depth 1 envs/JSBSim/data`
  （浅克隆即可，14 MB，秒级完成）
- **Verification**: `ls envs/JSBSim/data/aircraft/f16/` 出现 `f16.xml`；
  `MultipleCombatEnv('2v2/NoWeapon/HierarchySelfplay')` 正常构造，
  obs=(27,)、share_obs=(108,)
- **Category**: `Other`（环境搭建，非算法、非可扩展性）

---

## F2 — `gym` 包缺失

- **Failure ID**: F2
- **Experiment**: 无（不影响训练主路径）
- **Symptoms**: `ModuleNotFoundError: No module named 'gym'`
- **Cause**: 仓库 README 要求 `gym==0.20.0`，但当前镜像未安装。
  全仓库只有 **一处** 用到：
  `renders/render_2v2_indepent.py:7: from gym import spaces`。
  其余全部使用 `gymnasium`（`envs/JSBSim/envs/env_base.py` 等）。
- **Code location**: `renders/render_2v2_indepent.py`
- **Fix**: 不修复。该脚本不在训练/eval 主路径上，本次实验未使用。
  记录在此以免日后误判为环境损坏。
- **Verification**: `grep -rn "^import gym\|from gym " --include=*.py .` 仅命中该文件
- **Category**: `Other`

---

## F3 — 关闭 wandb 后，PPO 诊断量被静默丢弃（**最重要的一个**）

- **Failure ID**: F3
- **Experiment**: 全部（在启动正式队列前发现）
- **Symptoms**: 无报错。但 `runner/base_runner.Runner.log_info` 的非 wandb 分支是
  一个空的 `pass`，导致 `value_loss` / `policy_loss` / `policy_entropy_loss` /
  `actor_grad_norm` / `critic_grad_norm` / `ratio` **被计算但从不落盘**，
  stdout 也只打印 `average_episode_rewards`。
- **Cause**: 上游设计假设使用者一定开 wandb。在本服务器上必须关掉 wandb
  （无账号/网络），于是所有诊断信号消失。
- **Code location**: `runner/base_runner.py :: Runner.log_info`
- **Fix**: 在非 wandb 分支增加 JSONL 落盘
  `<save_dir>/metrics.jsonl`，记录全部 infos + `total_num_steps` + `wall_time`。
  **纯日志改动，不触碰任何算法量、不改任何超参数。**
- **Verification**: 跑 1 个 episode 后
  `scripts/results/MultipleCombat/2v2/scaling_noweapon/HierarchySelfplay/mappo/METRICS_TEST/run1/metrics.jsonl`
  内容：
  ```json
  {"total_num_steps": 6000, "value_loss": 1.7408, "policy_loss": -0.0107,
   "policy_entropy_loss": -0.00317, "actor_grad_norm": 1.323, "critic_grad_norm": 7.931,
   "ratio": 0.9995, "average_episode_rewards": -3.534}
  ```
- **Category**: `Other`（实验方法学；若不修，第 9/11 节（学习/协调可扩展性）
  将完全无数据可分析）

---

## F4 — 官方脚本的两个缺陷（复现保真度）

- **Failure ID**: F4
- **Experiment**: 全部官方入口
- **Symptoms**:
  1. 六个 `.sh` 全部传 `--clip-params 0.2`，而 `config.py` 定义的是
     `--clip-param`。`train_jsbsim.py` 使用 `parser.parse_known_args()`，
     **未知参数被静默忽略**，没有任何警告。
  2. 多个 `.sh` 传 `--use-wandb`，在无 W&B 账号的服务器上会失败/挂起；
     且 `use_wandb=True` 时 `save_dir` 被指向 `wandb.run.dir`，
     checkpoint 位置会变得不可预期。
- **Cause**: 上游拼写错误 + 对 wandb 的硬依赖。
- **Code location**: `scripts/*.sh`；`scripts/train/train_jsbsim.py:80`（parse_known_args）；
  `runner/base_runner.py:49-54`
- **Fix**: 我们的启动器 (`experiments/.../scripts/run_train.sh`)：
  1. 显式传 `--clip-param 0.2`。因默认值本就是 0.2，**语义完全不变**。
  2. 去掉 `--use-wandb`，走官方代码里本就存在的非 wandb 分支，
     checkpoint 落到 `scripts/results/...`。
- **Verification**: 见 `docs/baseline_inventory.md` §1.2；对比启动器命令行与官方 `.sh`
- **Semantic impact**: **无**（两者都不改变任何生效超参数或算法路径）
- **Category**: `Other`

---

## F5 — 自建配置生成器的变体覆盖 bug（**我们自己的错，不是仓库问题**）

- **Failure ID**: F5
- **Experiment**: N-v-N 配置生成
- **Symptoms**: 生成 `scaling/` 目录时，先跑 `--variant noweapon --n 2 3 5 10`，
  再跑 `--variant shoot --n 2 3 5`。第二次运行把 `2v2/scaling`、`3v3/scaling`、
  `5v5/scaling` **覆盖**成 shoot 变体，而 `10v10/scaling` 仍是 noweapon 变体。
  结果：同一个「scaling 系列」里混了两种 task（`hierarchical_multiplecombat` 与
  `hierarchical_multiplecombat_shoot`），**跨 N 的观测维度和奖励配置不一致**，
  一旦拿去跑就是无效对比。
- **Cause**: 输出目录只按 `<N>v<N>/scaling/` 组织，未把 variant 编入路径。
- **Code location**: `experiments/2026-10-04-night/scripts/gen_nvn_configs.py`
- **Fix**: 把 variant 编入输出子目录（`scaling_noweapon/` 与 `scaling_shoot/`），
  删除被污染的目录后重新生成；并在生成后立即用脚本打印每个 YAML 的
  `task / 飞机数 / 队伍构成 / num_agents` 做交叉核对。
- **Verification**: 重新生成后 7 个配置的 task 与队伍构成全部正确：
  `10v10/scaling_noweapon` → `hierarchical_multiplecombat`, 20 机, {Red:10, Blue:10}
- **Category**: `Other`（实验基础设施 bug）

---

## F6 — 状态快照脚本的两个缺陷

- **Failure ID**: F6
- **Experiment**: 监控工具
- **Symptoms**:
  1. `bc: command not found` → RSS 列恒为 0.00
  2. 进程表只统计到 4 个进程、CPU 恒为 0.0%
- **Cause**:
  1. 镜像内无 `bc`
  2. runner 用 `setproctitle` 把 rollout 子进程改名为
     `mappo-MultipleCombat-<exp>@<user>`，命令行里**不再含** `--experiment-name`，
     只按 argparse 命令行匹配会把 10~20 个真正干活的进程全部漏掉
- **Code location**: `experiments/2026-10-04-night/scripts/snapshot_status.sh`
- **Fix**: 改用 Python 直接读 `/proc/<pid>/{cmdline,stat}`，同时匹配
  `--experiment-name X` 与 setproctitle 形式 `^(ppo|mappo)-[^-]+-(.+)@`；
  CPU 用 `(utime+stime)/CLK_TCK / (uptime - starttime)` 计算
- **Verification**: 修复后 `official_2v2_noweapon` 显示 14 个进程、671% CPU、5.83 GB RSS
- **Category**: `Other`

---

## F7 — 环境基准被并发负载污染（**方法学问题，必须记录**）

- **Failure ID**: F7
- **Experiment**: `env_bench.py` 的环境吞吐测量
- **Symptoms**: 同一场景 `2v2/scaling_noweapon` 两次测量差异巨大：
  静默机器 **107.8 steps/s**（9.27 ms/step），
  5 条队列并发时 **67.2 steps/s**（14.89 ms/step）。
  10v10 从 7.82 → 6.6 steps/s。
- **Cause**: 第二次测量时机器 CPU 已被 40 个 rollout 进程占满约 40/48 核，
  测量到的是「争用下的有效成本」而非**内在成本**。
- **Code location**: `experiments/2026-10-04-night/scripts/env_bench.py`
- **Fix**: 两种条件**都保留**并分别标注
  （`metrics/env_bench_scaling.json` 的 `quiet` / `loaded` 两组）。
  报告中凡是引用「每次 env step 的内在开销」用 quiet 组；
  凡是讨论「并发吞吐下降」用 loaded 组。
- **Verification**: `quiet` 每架飞机耗时为 2.32/2.76/3.94/6.39 ms；
  `loaded` 为 3.72/4.88/6.60/7.60 ms
- **Category**: `Computational scalability`（且是**测量方法**层面的教训：
  任何 scaling 结论都必须声明是在什么负载下测的）

---

## F8 — 环境吞吐远低于孤立基准：JSBSim + vec-env 的实际成本

- **Failure ID**: F8
- **Experiment**: 全部 N-v-N 训练（在 `scaling_10v10_noweapon` 上最明显）
- **Symptoms**: 训练时的环境步进吞吐 **系统性低于** 孤立基准 2–4 倍：

  | 规模 | 孤立基准（并发负载下）steps/s/进程 | 训练实测 steps/s/线程 | 达成率 |
  |---|---|---|---|
  | 2v2（12 线程） | 67.2 | 18.3 | **27%** |
  | 3v3（10 线程） | 34.2 | 16.1 | **47%** |
  | 10v10（18 线程） | 6.58 | 3.33 | **51%** |

  最直观的表现：10v10 完成 episode 0（3000 个向量化步）需 **约 15 分钟**，
  FPS 60。
- **Precise diagnosis（逐进程采样 /proc，不是推测）**:
  - 18 个 rollout worker 全部处于 `state=R`，各约 **0.72 核**，合计 **13.2 核**
  - **主进程 `state=S`，仅 0.11 核** —— 它在**等待**，不是瓶颈
  - GPU 利用率 **0–1%**，显存 464 MB
  → 瓶颈 **完全在 CPU 侧的环境仿真**，既不是 PPO 更新，也不是 GPU。
- **Cause（已定位，分三层）**:
  1. **观测构造 O(N²)**：`MultipleCombatTask.get_obs()` 对每个 agent 遍历全部
     partner+enemy；`BaseEnv.get_state()` 又对全部 2N 个 agent 各调用一次
     `get_obs` 再 `hstack`。每步做两遍 O(N²)，且 share_obs 向量被复制 2N 份。
  2. **跨进程传输**：10v10 每步每个 env 要 pickle 20×2460 = 49,200 个 float
     的 share_obs，18 个 env 合计约 3.5 MB/向量化步。
  3. **CPU 争用**：40 个 rollout 进程竞争 48 核配额，每个只能拿到约 0.72 核。
- **Code location**: `envs/JSBSim/tasks/multiplecombat_task.py::get_obs`、
  `envs/JSBSim/envs/env_base.py::get_state`、`envs/env_wrappers.py`
- **Fix**: 未修改（保持官方实现以便公平复现）。**可做的纯工程优化**（不在本次范围）：
  在 `get_state()` 中复用同一步内已经算过的 `get_obs` 结果，把每步的 O(N²)
  观测构造从两遍降到一遍；以及避免把同一个 share_obs 复制 2N 份。
  这两项是**实现优化**，若将来采用，**必须**声明它改变了基线实现，
  不得与算法改进混为一谈。
- **Verification**: 见上表与逐进程采样；`metrics/env_bench_scaling.json` 的
  `quiet` / `loaded` 两组数据支持该归因
- **Category**: `Computational scalability`
  （**明确不是** algorithmic scalability —— 主进程在等待、算法并未参与瓶颈）

---

## 判定纪律

以上 F1–F8 **没有一条**可以支撑「curse of multiagency」的结论。
它们分别是环境、日志、脚本、工具、测量方法层面的问题。
若最终 10v10 学不动，必须先排除 F8 类因素，再讨论算法层面的可扩展性。
