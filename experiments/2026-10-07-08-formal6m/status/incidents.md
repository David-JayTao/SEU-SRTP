# 故障记录 — 正式 6M 实验

接续 `docs/night_failures.md` 的 F1–F9 系列。分类词汇与前文相同，并严格沿用：
`Code scalability` / `Computational scalability` /
`Representation scalability` / `Sample scalability` / `Algorithmic scalability` /
`Coordination scalability` / `Other`。

**从 pilot（前序试跑）继承的规则：** 测量或工程上的缺陷永远不是关于算法的证据。
以下任何内容都不得被引用来支持多智能体诅咒（curse of multiagency）的说法。

---

## F10 — CPU 核数列报告了一个物理上不可能的值

- **分类**：`Other`（测量缺陷）
- **发现**：2026-10-07，在审查第一份 `metrics/scaling_table.csv` 时
- **症状**：在一台 48 核的机器上，每一行都是 `peak_cpu_cores_host = 175.9`。
- **原因**：`os_watchdog.sh` 写入的 `cpu_busy_pct` **已经按 48 核 cgroup 配额
  归一化**，但 `scaling_table.py` 又把它乘以 `192/100`——这个常数对 *pilot 的*
  `monitor.sh` 才是对的，因为后者是按宿主机的 192 个逻辑 CPU 归一化的。
  两个采样器、两个分母、一个列名。
- **修复**：在运行时从 `/sys/fs/cgroup/cpu.max` 推导乘数
  （`4800000 100000` → 48），从 CSV 表头识别采样器模式
  （存在 `train_cpu_pct` ⇒ 已按配额归一化），并把**输出列重命名为
  `peak_busy_cores_of_48_quota`**，同时附带 `peak_cpu_pct_of_quota`。
- **验证**：修复后该值为 48 核中的 46.8 核忙碌（峰值时占配额的 97.6%），
  与 `load1 ≈ 44` 和采样器原始行一致。旧版 pilot 模式仍能精确重建其历史上的 65.3。
- **语义影响**：无——仅分析，未触碰任何训练代码。
- **为什么值得记录**：这是一个看起来像"规模效应"的数字（N=10 时的 175.9），
  实为量纲错误。正是 pilot 警告过的那种失败模式。

---

## F11 — 表示可扩展性（Representational-scalability）的各列静默为空

- **分类**：`Other`（缺少测量）
- **发现**：2026-10-07，同一次审查
- **症状**：`local_obs_dim`、`share_obs_dim`、`actor_params`、`critic_params`
  在 `scaling_table.csv` 中为空，且 `metrics/critic_scaling.json` 不存在。
- **原因**：`critic_scaling_probe.py` 存在且可用，但没有任何东西调用它。
  测量方法是在的，缺的只是那次调用。
- **修复**：`scaling_table.py` 现在从 `summary.csv` 推导所需的队伍规模，
  通过 subprocess 运行该探针（约 7 s，上限 240 s，带缓存，重复扫描时跳过）
  并合并结果。
- **验证**：N = 2/3/5/10 的数值与
  2026-10-04 的 pilot 独立测得的数值**逐比特相同**——
  (27, 108, 154891, 163969)、(39, 234, 156427, 180097)、
  (63, 630, 159499, 230785)、(123, 2460, 167179, 465025)——且生成的 JSON
  与 pilot 的键集合相同。报告第 10 节就建立在这上面。
- **语义影响**：无。

---

## F12 — 已完成的通道被报告为仍在运行

- **分类**：`Other`（测量缺陷，继承自 pilot）
- **症状**：`make_manifest.py` 从不把通道登记为已完成。
- **原因**：正则 `<<< (\S+) end rc=(\d+)` 与台账的实际行格式
  `<<< <name> end <ISO-timestamp> rc=<N>` 不匹配。
- **修复**：`<<< (\S+) end\b.*?\brc=(-?\d+)`。
- **验证**：已退出的通道现在会从 `running` 状态转出。
- **语义影响**：无。注意它恢复出的 `rc` 本身就没有意义
  （见报告 13.4——没有 `pipefail`），因此完成与否以
  `metrics.jsonl` 的步数进度判定，绝不依据 `rc`。

---

## F13 — 分析脚本硬编码了 pilot 的实验路径

- **分类**：`Other`（可移植性）
- **症状**：11 个复制的文件（7 个 Python、4 个 shell）仍指向
  `experiments/2026-10-04-night`，因此新实验中的任何运行都会
  静默地产生 *pilot 的*数字。
- **修复**：每个脚本现在从自身位置推导其实验根目录
  （`Path(__file__).resolve().parents[1]`），并为跨实验读取提供显式的
  `--campaign-root` / `CAMPAIGN_ROOT` 覆盖。
- **验证**：pilot 目录树未被触碰
  （`find experiments/2026-10-04-night -newermt 2026-10-05` → 空），且
  pilot 的 `summary.csv` 重新生成时**零列不匹配**，即该重构对它原本
  针对的实验是行为保持的。

---

## F17 — 可达到的步数预算被线程数量化

- **分类**：`Other`（实验设计陷阱）
- **发现**：2026-10-07 约 17:20，`f6m_official_1v1_vsbaseline_s1` 干净地结束在
  **5,994,000** 而不是 6,000,000——恰好低于目标，不是偶然少跑。
- **原因**：runner 计算
  `episodes = num_env_steps // buffer_size // n_rollout_threads`
  （`runner/share_jsbsim_runner.py:72`、`runner/jsbsim_runner.py:41`），因此
  可达到的总量是 `episodes × 3000 × threads`。在 `num_env_steps = 6e6` 和
  `buffer_size = 3000` 下，通道**只有在线程数整除 2000 时**才能达到完整预算：

  | 线程 | episodes | 达到 | 相对 6M |
  |---|---|---|---|
  | 3 | 666 | 5,994,000 | 99.9% |
  | 4 | 500 | 6,000,000 | 100% |
  | 8 | 250 | 6,000,000 | 100% |
  | 10 | 200 | 6,000,000 | 100% |
  | 20 | 100 | 6,000,000 | 100% |

- **症状是静默的**：没有警告、没有报错、没有截断运行的标记。任务只是少 6,000 步
  结束，并报告 `exited with code 0`。
- **修复**：**未做回溯性修复。** 为改变线程数而重跑会创建第二个 `run<N>/`
  （见报告 13.4），而拼接的轨迹不是一次干净的正式运行。四个 1v1 通道全部使用
  3 线程，因此封顶在 5,994,000。它们被报告为**在 5,994,000 处 `completed`
  （名义预算的 99.9%）**，并注明原因——**不是** `completed_6M`，也不是
  `time_cutoff`（没有任何东西被砍；目标在构造上就不可达）。
- **此后已应用**：在这之后启动的每个通道，其线程数都被选为能整除 2000——
  5v5 种子 1 用 10 线程（200 个 episode），3v3 种子 1 用 8 线程（250 个 episode）。
- **验证**：8 线程的 3v3 种子 0 恰好达到 6,000,000；3 线程的 1v1 vsBaseline
  恰好停在 666 × 9000 = 5,994,000。
- **可迁移的教训**：当预算以会被 harness 向下取整的单位表示时，
  *在启动时检查整除性*。pilot 也栽在同一个陷阱上：它 18 线程的运行只达到名义
  900,000 中的 864,000，而报告时没有解释这一缺口。

---

## F16 — `/proc/stat` 在这个容器里不可用；由它推导的每一个 CPU 数字都是错的

- **分类**：`Other`（测量缺陷——而且是已发现的最严重的一个）
- **发现**：2026-10-07 约 17:21，当时加入一个通道把报告的"忙碌核数"推到了
  65.5，而这台机器的配额只有 48。超过配额的数字不可能成立，因此可疑的是
  仪器而不是负载。
- **症状**：每 4–5 s 采样一次的 `/proc/stat` `cpu` 聚合值，返回的忙碌增量在
  **0.0 核和约 200 核**之间交替，而容器明明很忙。200 ≈ **宿主机的** 192 个
  逻辑 CPU，不是容器的 48。整个实验期间报告过的值最高达到配额的 124%。
- **原因**：容器的 `/proc/stat` 暴露的是宿主全局计数器（lxcfs 风格的视图），
  而 `nproc` 报告 48、`/sys/fs/cgroup/cpu.max` 授予 48。三者互相矛盾。
  因此朴素的 `busy_ticks / (elapsed × USER_HZ)` 测的是*宿主机*，不是这个容器。
- **权威来源**（现在使用）：容器自己的 cgroup 记账——
  `/sys/fs/cgroup/cpu.stat` 的 `usage_usec` 增量，配额取自
  `/sys/fs/cgroup/cpu.max`。按这个口径，本次实验使用了 **48 核中的约 38–42 核
  （80–87%）**，`nr_throttled` 维持在**周期的 0.02–0.04%**，即 CPU 配额
  **从未真正构成约束**。
- **修复**：
  - `os_watchdog.sh` 现在从 cgroup `cpu.stat` 测量，并写入
    `system/system_samples_v2.csv`，列为
    `cpu_busy_pct_of_quota, busy_cores_of_quota, quota_cores, nr_throttled_pct`。
    v1 文件**原样保留在磁盘上作为历史记录**，但其 `cpu_busy_pct` 列不得使用。
  - `watch_f6m.py` 使用同一来源，并打印
    `container CPU X / 48 cores (Y% of quota, throttled Z% of periods)`。
  - `scaling_table.py` 和 `make_manifest.py` 优先使用 v2 文件，**直接读取
    `busy_cores_of_quota` 而不重新缩放**，并在输出中标注来源
    （`cgroup cpu.stat (authoritative)`）；旧路径只为让旧文件仍能解析而保留，
    并标注为 `UNRELIABLE`。
- **验证**：同一时刻 v1 对 v2——v1 `124.4`，v2 `79.6%` = `38.21 / 48` 核。
  `scaling_table.csv` 现在报告 `peak_busy_cores_of_48_quota = 38.2`，
  并带有权威来源标注。
- **对实验的语义影响**：无——训练未受影响。
  **对报告的语义影响**：很大。第 9.3 节"≈43 of 48 cores, saturated"的叙述
  是假象，而"加入通道使 10v10 通道吞吐受损"的说法**不成立**——配额从未饱和，
  观察到的累计 FPS 下沉完全可以由累计平均本身解释。两者都被更正，
  而不是留在原处。
- **可迁移的教训**：一个派生指标如果超出其自身的物理边界（核数 > 配额、
  利用率 > 100%），那是*量纲错误*，不是发现。这与 F10 属于同一类错误——
  F10 的 175.9 "核"和这一次有共同的根因：信任采样器的分母，而不是拿它
  对照 cgroup 核实。另请注意 pilot 的 `monitor.sh` 用的是同一套 `/proc/stat`
  方法，因此 pilot 的 CPU 列带有同样的缺陷。

---

## F15 — 探针的 `--out` 相对仓库根目录解析，而不是调用时的 cwd

- **分类**：`Other`（可移植性陷阱）
- **发现**：2026-10-07 05:03，由 `freeze.sh` 的第一次 dry-run——是非致命的
  步骤运行器把它暴露出来，而不是让冻结中止
- **症状**：`FileNotFoundError: [Errno 2] No such file or directory:
  'metrics/critic_scaling.json'`，是在探针已经打印完整张结果表**之后**才抛出的。
  很容易漏掉：那张表看起来就像成功。
- **原因**：`critic_scaling_probe.py:27` 在 import 时执行 `os.chdir(REPO)`
  （与 `offline_eval.py` 一样），因此相对的 `--out` 会相对
  `/root/autodl-tmp/SEU-SRTP` 解析，而不是调用者的 cwd。那里并不存在
  `metrics/` 目录。
- **修复**：`freeze.sh` 传入绝对路径的 `--out`。陷阱留在探针本身里
  （它几乎是 pilot 版本的原样拷贝，且 `scaling_table.py` 本来就用绝对路径
  调用它），但已在注释中明确指出。
- **验证**：冻结扫描 10/10 全 `ok`；`metrics/critic_scaling.json`
  有 4 条 `measured` + 7 条 `extrapolated` 记录。
- **语义影响**：无，但请注意*第一次*冻结运行时报告了 `critic_probe FAILED`，
  而 `metrics/critic_scaling.json` 仍存在于更早一次 `scaling_table.py` 调用
  留下的文件——即陈旧产物可以掩盖一个坏掉的再生成步骤。这就是为什么各步骤的
  结果被显式记录在 `status/freeze_summary.md`，而不是从输出文件是否存在来推断。

---

## F14 — `1v1` ShootMissile 通道在结构上慢约 2×，并且将错过 6M

- **分类**：`Computational scalability`（不是 algorithmic）
- **发现**：2026-10-07 03:37，来自第一批稳定的 FPS 读数
- **症状**：在相同线程数下，`f6m_official_1v1_shoot_hier_selfplay_s1` 跑 55 FPS，
  而它的兄弟 `1v1` 通道跑 104–120 FPS。
- **原因**：`--use-prior`（仅实现在 `algorithms/ppo/ppo_actor.py` 中，出现 5 次）
  把 SingleCombat 的吞吐大约减半。在相同 10 线程下与 pilot 对照确认：
  `official_1v1_selfplay` 324 FPS 对 `official_1v1_shoot_hier_selfplay` 170 FPS——
  同样的约 2:1 比例。这是代码路径本身的性质，不是资源争用；同一台机器上的
  兄弟通道不受影响。
- **修复**：**故意不修。** 3 线程下它需要约 30.3 h，而窗口是 29.9 h，因此预计
  只能落在 **6M 的约 98%**。杀掉并重跑会创建第二个 `run<N>/` 目录，而重启后的
  部分轨迹不是一次干净的正式运行（见报告 13.4）。它将按实际达到的步数记为
  `time_cutoff`——**绝不**记为 `completed_6M`。
- **验证**：pilot 日志 `logs/official_1v1_shoot_hier_selfplay_seed1_gpu0_20261004_065907.log`
  尾部 10 线程下 FPS 169–172，对照 `official_1v1_selfplay` 10 线程下 324–325。
- **教训**：`--use-prior` 是官方入口点上的官方 flag，所以保留——但必须把它
  计入预算。按通道分配线程却忽略各通道的 FPS/线程，会系统性地饿死带武器基线。

---

## F18 — `offline_eval.py` 的默认对手是 NULL 策略，所以它的默认数字毫无意义

- **分类**：`Other`（测量陷阱——最危险的一种：它产生看起来合理的数字）
- **发现**：2026-10-07 约 18:05，在已完成的 `f6m_3v3_noweapon_s0` 通道上
  验证冻结时刻探针、在依赖它之前。
- **症状**：默认调用在一个**训练** reward 为 **+35.93** 的通道上返回了
  `mean_return = −55.85`、`std_return = 0.0`、`mean_episode_length = 1000`。
  两个危险信号：与训练值相差 90 点，以及 episode 长度恰好钉在 `max_steps`。
- **原因**：在 `scripts/offline_eval.py` 中，除非传入 `--selfplay`，
  对手的动作被填充为**零**：
  ```python
  if is_multi and args.selfplay:
      full[n_ego:] = actions        # mirror match
  elif n_ego < n_agents:
      full[n_ego:] = 0              # NULL opponent -- never manoeuvres, never fires
  ```
  空对手无法结束 episode，所以**length = 1000 是对手什么都不做的产物**，
  而 −55.85 是对着一个毫不抵抗的目标拿到的 reward。这两个数字都不描述
  训练出来的策略。
- **为什么危险**：`mean_return = −55.85` 看起来像一个结果。脱离这一语境
  引用它，会读成"3v3 策略很差"，而实际含义是"3v3 策略在一个从不移动的
  对手面前累积了 −55.85"。这与 F10（175.9 核）和 F16（48 核中的 62 核）属于
  同一类失败：一个*内部*自洽、而*对外*毫无意义的数字。
- **在同一文件里发现的第二个、独立的 bug**：`build_run_dir_args` 读取
  `algo = cfg[-2]`，那是**实验名**，不是算法（`cfg[-3]`）。已验证*对这个
  脚本*而言只是表面问题——策略类是根据 `env_name`
  （`is_multi = env_name == "MultipleCombat"`）而非 `algo` 选择的——但这个被
  错误解析的值会作为出处信息写进输出 JSON，所以它对"评估了什么"这件事
  是在主动误导。
- **修复**：
  1. `algo = cfg[-3]`。
  2. 空对手分支现在带有明确的注释，说明默认模式不是一次评估，并且任何
     想要有意义的测量都必须加 `--selfplay`。
  3. `freeze.sh` 现在为每一次冻结时刻的离线评估都传入 `--selfplay`。
  4. 跨 N 的 episode 长度比较只在 `--selfplay` 模式下进行。
- **验证**：在同一 checkpoint 上用 `--selfplay` 重跑；报告的
  `selfplay_mirror` flag 翻转为 `true`，结果在冻结时刻记录到
  `metrics/offline_eval_*.json`。
- **教训**：当一个测量工具有默认模式时，*在信任其输出之前先读读默认模式
  到底做什么*——尤其是当输出看起来很合理时。这次检查只花了约 10 分钟，
  否则最终报告里就会多出一条像是编造出来的"评估"。

---

## N1 — 不是故障。`1v1/NoWeapon/HierarchySelfplay` 在后半程退化

记录在这里，只是为了日后不被误认为一次未记录的异常。完整记述见
`docs/formal_repro_scaling_2026-10-07_08.md` §11.1。

- **分类**：`Algorithmic scalability` / `Sample scalability`（候选——尚未确立）
- **证据**：把 `f6m_official_1v1_hier_selfplay_s1`（488 个训练行）等分为四段后，
  `critic_grad_norm` 的中位数为单调的 **108 → 112 → 266 → 473**，对应的 reward
  中位数为 **+24.1 → +22.4 → −17.2 → −89.7**，且第一段与最后一段的四分位距
  几乎没有重叠。
- **有意先做了检查**：触发点（`critic_grad_norm = 1274`、4.39M 步处 reward
  `−333`）是真实趋势的极端值，*不是*发散——整个运行中（以及全部 11 个通道中）
  没有任何 NaN、任何 Inf。
- **对照**：兄弟通道 `f6m_official_1v1_selfplay_s1`（相同 env、场景系列、
  种子和超参数；**非**层级化任务）在同一窗口内 critic 梯度下降而 reward 上升。
- **采取的行动**：**无。** 退化是一个结果，不是工程故障；任务书 §16 节禁止
  为挽救一次运行而修改算法。该通道跑完，并按它达到的水平报告。
- **不能作为**多智能体诅咒的证据：每边 N=1，单个种子。
