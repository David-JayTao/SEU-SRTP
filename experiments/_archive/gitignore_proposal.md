# .gitignore 审计与修改提案

- 日期：2026-10-08
- 对象仓库：`/root/autodl-tmp/SEU-SRTP`（分支 `exp/formal-6m-20261007`）
- 状态：**提案，未采纳**。本次巡检不改动 `.gitignore`、不提交、不推送；采纳与否由主会话/用户决定。
- 配套文件：同目录 `proposed_gitignore.txt`（与本文 §4 嵌入内容逐字节相同，`cp` 即可启用）。
- 关联规范：仓库 `CLAUDE.md` §二（每轮实验后自动归档、§2.2 策略池检查点留服务器、§2.4 文件大小与 LFS 判断）。

## 0. 一句话结论

现行 `.gitignore` 用 `results` / `scripts/results/` / `*.pt` / `*.log` 四条宽规则，把 `scripts/results`（3.02 GiB）里的**全部**内容挡在 Git 外——包括最有归档价值的 44 份 `metrics.jsonl`（2.66 MiB）、94 份 `*_latest.pt` 最终权重（66.40 MiB），以及 54 份实验日志（含 49 份训练 stdout，2.62 MiB）。本提案改为「体积 × 价值 × 可重建性」精确分档：**3 GB 的逐 episode 策略池继续排除，小体积高价值产物放行**。提案生效后实测（scratch 仓库 `git add -A -n`）：只新增 16 个预期文件；460 个已跟踪文件无一会被新规则挡住。

## 1. 现行 .gitignore 逐条审计（对照仓库真实文件）

方法：`git check-ignore -v`（判定具体由哪一行挡下）+ `git status --ignored --porcelain`（全量被忽略清单）+ `find` 统计（数量与体积）。所有数字为本仓库 2026-10-08 实测。

### 1.1 任务点名的九条

| # | 模式（行号） | 实测挡住什么 | 体积/数量 | 处置 |
|---|---|---|---|---|
| 1 | `results`（L3，裸模式） | **任意层级**名为 `results` 的文件/目录——因此 `scripts/results/` 整个正式实验输出根也被它命中（与 L155、L159 三重叠加） | 4947 个文件 / 3022.27 MiB | **删除**，改为锚定 `/results/`（仅仓库根） |
| 2 | `scripts/results/`（L159） | 正式实验输出根整目录排除；`git check-ignore -v` 对 `actor_*.pt`、`*_latest.pt`、`metrics.jsonl` 均报告由本行最终决定 | 同上 | **删除**，改为内容级精确规则（见 §3） |
| 3 | `*.pt`（L160） | 一切 `.pt`。实测 4903 个中：4809 个逐 episode 策略池快照（2953.20 MiB，值得排除）+ 94 个 `*_latest.pt` 最终权重（66.40 MiB，**不该排除**）。另注意 `envs/JSBSim/model/*.pt` 两个已跟踪文件是历史上 `git add -f` 强行绕过的（`git ls-files -ci --exclude-standard` 可复现） | 3019.60 MiB 合计 | **删除**，改 `actor_[0-9]*.pt` / `critic_[0-9]*.pt` 精确排除 |
| 4 | `*.log`（L72，在 Django 段） | 仓库全部 `.log`：共 54 个 / 2.62 MiB = 训练 stdout 49 个（2026-10-04-night/logs 35 个 + formal6m/logs 14 个）+ `status/` 下 4 个（`auto_finalize.log`、`events_watch.log`、2 个 0 字节 `.tb_*` 标记）+ `system/events.log` | 2.62 MiB | **保留兜底**，在 `experiments/` 树内定向反转放行 |
| 5 | `logs/`（L157，裸模式） | 任意层级叫 `logs` 的目录——这是 `experiments/**/logs/` 也被它覆盖的原因；同时它使任何 `!` 放行失效（git 不进入已排除目录） | 同上 2.62 MiB | **改锚定** `/logs/`（仅仓库根；当前不存在该目录） |
| 6 | `*.acmi`（L6、L163 重复） | 当前 0 命中（仓库无 .acmi）。Tacview 回放录像为二进制大文件（单个可达几十 MB），保留排除合理 | 0 | 保留（去重，见 §3） |
| 7 | `*.npy`（L5） | 当前 0 命中。numpy 原始数组属可重算大体积中间产物，保留排除合理 | 0 | 保留 |
| 8 | `experiments/**/logs/`（L172） | 两处实验 `logs/` 目录（与 L72、L157 三重叠加）。语义上**冗余**（裸 `logs/` 已覆盖任意层级），但它是目录级排除、且晚于 `*.log` 匹配，实际是它的"报告行" | 54 个文件 / 2.62 MiB | **删除**，替换为 `!experiments/**/*.log`（文件级放行，必须排在 `*.log` 之后） |
| 9 | `experiments/**/status/*.status`（L173） | 15 个队列运行状态文件（`queue_*.status`），共 9019 字节 | 9 KB | **保留排除**；等效信息已由 `status/freeze_logs/*.txt`（40 个快照）与 `final_state_history.md` 入库。如需追溯单文件可 `git add -f` |

### 1.2 其余模式分组审计（全部 0 命中，实测无实际影响）

| 分组 | 模式 | 实测 |
|---|---|---|
| 本地产物 | `test.py`、`runs` | 0 命中（无 `test.py`；无 `runs/` 目录） |
| IDE 配置 | `.vscode`、`.idea`（各出现两次） | 0 命中；预防性 |
| Python 缓存 | `__pycache__/`、`*.py[cod]`、`*$py.class`（前两者重复出现两次） | 挡住 17 个 `__pycache__` 目录（含 `experiments/2026-10-07-08-formal6m/scripts/__pycache__/`、`runner/__pycache__/` 等） |
| C 扩展 | `*.so` | 0 命中（JSBSim C++ 产物由 `envs/JSBSim/data` 子模块自带 .gitignore 管理，见 §1.3） |
| 打包/分发 | `.Python`、`build/`、`dist/`、`downloads/`、`eggs/`、`.eggs/`、`lib/`、`lib64/`、`parts/`、`sdist/`、`var/`、`wheels/`、`pip-wheel-metadata/`、`share/python-wheels/`、`*.egg-info/`、`.installed.cfg`、`*.egg`、`MANIFEST`、`develop-eggs/` | 0 命中。注意 `lib/`、`var/`、`build/` 无锚定、匹配任意层级，偏宽（仓库当前无同名目录，已加警示注释） |
| PyInstaller / 安装器日志 | `*.manifest`、`*.spec`、`pip-log.txt`、`pip-delete-this-directory.txt` | 0 命中 |
| 覆盖率/单测 | `htmlcov/`、`.tox/`、`.nox/`、`.coverage*`、`.cache`、`coverage.xml`、`.pytest_cache/` 等 | 0 命中 |
| 翻译 | `*.mo`、`*.pot` | 0 命中 |
| 其他框架 | `local_settings.py`、`db.sqlite3*`、`instance/`、`.webassets-cache`、`.scrapy`、`docs/_build/`、`target/`、`.ipynb_checkpoints`、`profile_default/`、`ipython_config.py` | 0 命中（`docs/_build/` 注意只挡 Sphinx 输出，`docs/` 其余内容含 PDF/PNG 正常入库——已实测 `docs/group_progress_report_2026-10-04.pdf` 被跟踪） |
| pyenv/pipenv/mkdocs/类型检查 | `.python-version`、`#Pipfile.lock`（注释行）、`__pypackages__/`、`/site`、`.mypy_cache/`、`.pyre/` 等 | 0 命中 |
| 虚拟环境/凭据（红线） | `.env`（两次）、`.env.*`、`*.pem`、`*.key`、`condaenv.*.requirements.txt`、`.venv`、`env/`、`venv/`、`ENV/`、`env.bak/`、`venv.bak/` | 0 命中；**保留，不得放宽** |
| Celery/Sage/Spyder/Rope | `celerybeat-*`、`*.sage.py`、`.spyderproject`、`.spyproject`、`.ropeproject` | 0 命中 |

### 1.3 额外发现（写进档案，供归档时注意）

1. **被忽略条目全量**：`git status --ignored --porcelain` 共 40 条 = 17 个 `__pycache__` + 2 个 `logs/` 目录 + 15 个 `.status` + 2 个 `status/*.log` + 2 个 0 字节 `.tb_*.log` + 1 个 `system/events.log` + 1 条 `scripts/results/`（折叠整目录）。
2. **`envs/JSBSim/data/.gitignore` 是子模块自带**（`git ls-files -s` 显示 gitlink `160000`，指向 `https://github.com/JSBSim-Team/jsbsim.git`），属上游文件，不属本项目忽略策略，不建议动。
3. **`scripts/results` 里没有任何被跟踪文件**（`git ls-files scripts/results | wc -l` = 0），所以本次改动只影响未来 `git add`，不影响历史。
4. **2 个空 run 目录**：`SMOKE_heading/run1`、`official_1v1_shoot_hier_vsbaseline/run1` 完全为空；归档时可跳过。
5. **`git check-ignore -v` 的显示陷阱**：它打印"最后一条匹配"的规则，**否定规则（`!`）也会被打印**。判断"是否被忽略"必须看退出码（0=被忽略）或 `git add -n`，不能看有无输出（本提案验证过程中实际踩过这个坑，见 §7 V1）。
6. **gitignore 不支持行内注释**：`*.tmp  # 注释` 会变成模式 `*.tmp  # 注释`，规则静默失效（实测见 §7 V0）。因此中文注释必须独立成行（本提案文件已全部如此）。

## 2. 分档决策（A/B/C/D/E 档）

| 档 | 内容 | 实测规模 | 处置 | 依据 |
|---|---|---|---|---|
| A | 逐 episode 策略池快照 `actor_<数字>.pt`（`runner/selfplay_jsbsim_runner.py:280` 每个 episode 落一个） | 4809 个 / 2953.20 MiB | 排除，服务器留档 | 可重建的大体积中间产物；CLAUDE.md §2.2 明文「留在服务器」 |
| B | 最终滚动权重 `actor_latest.pt` / `critic_latest.pt`（`runner/base_runner.py:110-112`、`selfplay_jsbsim_runner.py:276-278`） | 94 个 / 66.40 MiB，最大单文件 703287 B | **放行** | 评测、复现论文结果的直接输入；CLAUDE.md §2.1 要求归档 |
| C | 曲线数据 `metrics.jsonl`（`runner/base_runner.py:144` 追加写） | 44 个 / 2.66 MiB（平均 62 KB） | **放行** | 论文绘图唯一一手数据 |
| D | 实验日志（stdout 49 个 + 脚本日志与空标记 5 个） | 2.62 MiB | **放行**（限 `experiments/` 树内） | 纯文本、小体积、append-only，是复现/排障第一手材料 |
| E | 队列状态 `.status` | 15 个 / 9019 B | 继续排除 | 等效信息已在 `freeze_logs/*.txt` 与 `final_state_history.md`；`git add -f` 为逃生口 |
| F | 缓存类（`__pycache__` 17 个目录、`.pyc` 等） | — | 继续排除 | 缓存，见 §1.2 |
| G | 凭据类（`.env`、`*.pem`、`*.key`） | 0 命中 | 继续排除（红线） | 安全 |

## 3. 修改摘要（相对现行 .gitignore 的 diff 清单）

1. 顶部「ignore files」段：删除裸 `results`、`runs` 两行（防整目录排除；移到训练产出节并改为锚定）。
2. 「Training outputs」段：
   - `results/` → `/results/`（只挡仓库根）；`runs/` → `/runs/`；`logs/` → `/logs/`（锚定是把 `experiments/**/logs/` 救出来的前提）。
   - **删除** `scripts/results/` 整目录排除。
   - **删除** `*.pt` 一刀切；新增 `actor_[0-9]*.pt`、`critic_[0-9]*.pt`（精确到命名，`actor_latest.pt` 不匹配数字前缀，天然放行）。
   - 新增防御性规则 `events.out.tfevents.*`（当前无 TB 文件，实测若不加会被放行，已补挡）。
   - `*.pth`、`*.ckpt`、`wandb/` 保留；与顶部重复的 `*.acmi` 去重。
3. 实验基础设施段：**删除** `experiments/**/logs/`；在文件**末尾**（必须晚于 `*.log` 兜底）新增 `!experiments/**/*.log`；`experiments/**/status/*.status` 保留。
4. 全文加入中文注释（独立行；每组规则注明挡住什么、为什么这样分档）。
5. 其余全部原样保留（含历史重复段，如第二组 `__pycache__/`、`.vscode/`、`.env`）。

**为什么分档不是一刀切**：忽略规则的粒度上限是「路径 + 命名」，表达不了体积。`scripts/results` 里 3 GB 与 69 MB 的产物混在同一命名空间，只能靠命名区分——而命名恰好天然分开了策略池（`actor_<数字>.pt`）与最终权重（`actor_latest.pt`）。这就是本提案的全部技巧：**用命名分档替代目录一刀切**。

## 4. 完整提案文件（可直接采用）

以下内容与同目录 `proposed_gitignore.txt` 逐字节一致（组装时程序化拷贝，已抽样 diff 验证）。

```gitignore
# ==============================================================================
# SEU-SRTP .gitignore（中文注释版提案 · 2026-10-08）
# ==============================================================================
# 阅读说明：gitignore 不支持「行内注释」——模式后面跟的 # 文字会被当作模式本身
# 的一部分，规则静默失效（实测见 gitignore_proposal.md 验证记录 V0）。因此本文件
# 所有中文注释一律独立成行、写在对应模式的上方。
# 每条注释说明「该规则实际挡住仓库里的什么」；分档决策与理由汇总见文末
# 「训练产出分档」一节；完整审计与验证记录见同目录 gitignore_proposal.md。
# ==============================================================================

# ---- 上游遗留的本地产物与数据文件 ----

# 挡任意层级名为 test.py 的临时脚本；本仓库无此文件（test_env.py / tests/ 不受影响）
test.py

# 挡所有 numpy 原始数组（离线回放、特征缓存等可重算的大体积产物）；仓库当前没有 .npy
*.npy

# 挡所有 ACMI 空战回放录像（Tacview 二进制轨迹，单个可达几十 MB）；仓库当前没有 .acmi
*.acmi

# 注：原第 3、4 行的 results / runs 已移至下方「训练产出」节并锚定为
# /results/、/runs/，避免整目录排除 scripts/results/（正式实验输出所在，约 3 GB）。

# ---- VS Code / PyCharm 工程配置（个人偏好，不入库） ----

.vscode
.idea

# ---- Python 字节码与缓存 ----

# 挡所有 __pycache__ 目录（仓库实测 16 处，含 experiments/**/scripts/__pycache__）
__pycache__/

# 挡 .pyc / .pyo / .pyd 编译产物
*.py[cod]

# 挡 Cython 编译产物
*$py.class

# ---- C 扩展 ----

# 挡编译出的 C 扩展；本仓库无（JSBSim C++ 由 envs/JSBSim/data 子模块自带的 .gitignore 管理）
*.so

# ---- 打包 / 分发中间产物 ----

.Python

# 挡任意层级 build/ 目录（setuptools、Cython 中间产物）
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/

# 注意：下面这条匹配任意层级名为 lib 的目录，偏宽；仓库当前无 lib/。
# 若未来出现源码级 lib/（如 envs/xxx/lib/），应改为锚定的 /lib/ 或精确路径。
lib/
lib64/
parts/
sdist/

# 同样匹配任意层级 var/ 目录（偏宽）；仓库当前无
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# ---- PyInstaller ----

*.manifest
*.spec

# ---- pip 安装器日志 ----

pip-log.txt
pip-delete-this-directory.txt

# ---- 单测 / 覆盖率报告 ----

htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# ---- 翻译中间文件 ----

*.mo
*.pot

# ---- 杂项日志与本地配置 ----
# 【兜底规则】挡住所有 *.log。训练 stdout 已在文末「实验日志放行」中定向放行；
# 其余散落的 .log（pip、各脚本临时输出等）继续排除。
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# ---- Flask ----

instance/
.webassets-cache

# ---- Scrapy ----

.scrapy

# ---- Sphinx 构建产物 ----

# 只挡 docs/_build/（Sphinx 输出）；docs/ 其余内容正常入库（含 PDF / PNG）
docs/_build/

# ---- PyBuilder ----

target/

# ---- Jupyter / IPython ----

.ipynb_checkpoints
profile_default/
ipython_config.py

# ---- pyenv / pipenv / PEP 582 ----

.python-version
#Pipfile.lock
__pypackages__/

# ---- Celery ----

celerybeat-schedule
celerybeat.pid

# ---- SageMath ----

*.sage.py

# ---- 虚拟环境目录与凭据（红线：绝不入库） ----

# 【重要】环境变量文件可能含凭据，必须排除
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# ---- IDE 配置（Spyder / Rope） ----

.spyderproject
.spyproject
.ropeproject

# ---- mkdocs 站点输出 ----

# 只挡仓库根目录 site/
/site

# ---- 类型检查缓存 ----

.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# ---- 本地环境临时文件与凭据 ----

condaenv.*.requirements.txt

# 与上方重复，保留原样（无副作用）
.env

# 挡 .env.local 等变体
.env.*

# 挡证书私钥
*.pem

# 挡私钥
*.key

# ---- 原「Python cache」重复段（保留原样，无副作用） ----

__pycache__/
*.py[cod]

# ==============================================================================
# 训练产出分档（2026-10-08 修订）
# ==============================================================================
# 分档依据 = 体积 × 价值 × 可重建性：
#   A 档 逐 episode 策略池快照 actor_<数字>.pt（4809 个 / 2.95 GB）→ 排除，服务器留档
#        （runner/selfplay_jsbsim_runner.py:280 每个 episode 落一个，供 selfplay 对手池取样，
#          属可重建的大体积中间产物）
#   B 档 最终滚动权重 actor_latest.pt / critic_latest.pt（94 个 / 66.4 MB，单个 ≤ 0.71 MB）→ 放行
#   C 档 曲线数据 metrics.jsonl（44 个 / 2.66 MB，单个约 62 KB）→ 放行（论文绘图的一手数据）
#   D 档 stdout / TensorBoard / 回放录像等运行日志 → 排除（服务器留档；实验日志见文末定向放行）

# 只挡仓库根目录 results/（上游原版代码的默认输出位置）；锚定 / 后不波及 scripts/results/
/results/

# 只挡根目录 runs/；仓库当前无此目录，属预防性规则
/runs/

# 只挡根目录 logs/；锚定后才能放行 experiments/**/logs/（见文末放行规则）
/logs/

# 任意层级 wandb 目录（本地 run 缓存，含大量二进制 event 文件）
wandb/

# 原先整目录排除的 scripts/results/ 改为下列精确规则
# （正式输出根 = scripts/results，由 scripts/train/train_jsbsim.py:107 以绝对路径写死）：

# A 档：逐 episode 策略池快照（actor_0.pt … actor_665.pt）→ 排除
actor_[0-9]*.pt

# 同类 critic 数字快照；当前仓库没有，防御未来命名变体
critic_[0-9]*.pt

# 其它框架权重后缀（Lightning 等）；仓库无
*.pth

# 同上；仓库无
*.ckpt

# 防御性规则：TensorBoard event 文件（当前仓库无；若未来启用 TB 会落到 run 目录里，
# 曲线数据已由 metrics.jsonl 完整覆盖，event 文件可重建，不进 Git）
events.out.tfevents.*

# 已删除原来的 *.pt 一刀切：它会连 B 档最终权重和 envs/JSBSim/model/*.pt 基线模型一起挡掉。
# 现规则下允许入库的 .pt = *_latest.pt（94 个）+ envs/JSBSim/model/*.pt（2 个，各 ≤ 0.71 MB）。
# 提交前自查：git status --porcelain | grep '\.pt$'，逐个确认体积 ≤ 1 MB 再 add。

# ---- 编辑器重复段（原样保留） ----

.vscode/
.idea/

# ==============================================================================
# SRTP 实验基础设施（2026-10-04 引入；2026-10-08 修订）
# ==============================================================================
# experiments/ 是实验归档主目录：manifest.csv（清单）、metrics/（指标提取）、
# figures/（图表）、configs/（队列配置）、scripts/（采集脚本）、status/*.md（过程文档）、
# status/freeze_logs/*.txt（冻结快照）等中小体量文件不被本文件任何模式匹配，
# 天然可入库（已验证），无需额外放行。

# 挡 status/queue_*.status（15 个 / 9 KB）：队列「正在跑什么」的运行时状态。
# 同一信息已由 freeze_logs/*.txt（40 个快照）与 final_state_history.md 入库成功；
# 保留排除以防实时状态抖动污染 diff。如需单个文件可 git add -f。
experiments/**/status/*.status

# 实验日志放行（替代原先的 experiments/**/logs/ 整目录排除）：
# 现存 54 个 .log = 训练 stdout 49 个（2026-10-04-night/logs 35 个 + formal6m/logs 14 个，
# 每个 60 KB ~ 430 KB）+ status 下 4 个（auto_finalize.log、events_watch.log、2 个 0 字节
# .tb_* 标记）+ system/events.log 1 个。
# 理由：纯文本、小体积、append-only，是复现 / 排障 / 写论文的第一手材料。
# 注意：若保留整目录排除 logs/，本条 ! 放行会失效（git 不进入已排除的目录），
#      故本提案已把 /logs/ 锚定到仓库根，并删除 experiments/**/logs/ 规则。
!experiments/**/*.log
```

## 5. 采纳方式（建议）

```bash
# 1) 备份现行文件（保留现状可回溯）
cp /root/autodl-tmp/SEU-SRTP/.gitignore /root/autodl-tmp/SEU-SRTP/experiments/_archive/gitignore.old.txt
# 2) 启用提案
cp /root/autodl-tmp/SEU-SRTP/experiments/_archive/proposed_gitignore.txt /root/autodl-tmp/SEU-SRTP/.gitignore
# 3) 单独中文 commit（可引用本文件）
#    杂项：修订 .gitignore 分档规则，放行最终权重、metrics 与实验日志
```

修改 `.gitignore` 只影响未来 `git add`，不改动任何已跟踪文件与历史提交（§7 V3 已回归验证）。

## 6. 文件大小与 LFS 评估（对齐 CLAUDE.md §2.4）

- 提案放行物的**最大单文件** = `703287 B ≈ 0.67 MiB`（`official_2v2_noweapon_selfplay/run1/actor_latest.pt`），远低于 GitHub 50 MiB 告警线与 100 MiB 拒绝线。
- 提案生效后一轮归档的新增总量 ≈ 66.40（B 档）+ 2.66（C 档）+ 2.62（D 档）≈ **71.7 MiB < 300 MB**。
- 按 CLAUDE.md §2.4 判断规则 → **用普通 Git，不启用 LFS**（避免占用 1 GB 免费配额、增加 clone 复杂度）。
- 本机实测 `git lfs version` → `git: 'lfs' is not a git command`，推送环境并未安装 git-lfs；启用 LFS 还需额外安装配置，进一步支持本轮不启用。
- 备用触发条件：若未来某轮出现 >50 MiB 单文件，或单轮归档新增 >300 MB（例如决定把策略池快照也纳入远端），再启用 LFS，` .gitattributes` 参考片段：
  ```
  *_latest.pt filter=lfs diff=lfs merge=lfs -text
  ```
  注意：已入库的 `envs/JSBSim/model/*.pt` 是历史普通对象，转 LFS 需历史迁移（破坏性操作，须用户确认后再做，不要顺手做）。

## 7. 验证记录（全部可复现）

### V0：gitignore 行内注释陷阱（决定注释写法的实测）

```bash
mkdir /tmp/gi_comment_test && cd /tmp/gi_comment_test && git init -q .
printf '*.tmp  # this is my comment\n*.bak\n' > .gitignore
touch a.tmp b.bak
git check-ignore -q a.tmp; echo $?   # → 1（没挡住！行内注释成了模式的一部分）
git check-ignore -q b.bak; echo $?   # → 0（正常挡住）
git add -An                          # → add 'a.tmp'（果然漏网）
```

### V1：提案生效后的 add 干跑（scratch 仓库，结构镜像真实仓库）

```bash
# scratch：/tmp/gi_test/repo，复制 proposed_gitignore.txt 为 .gitignore，
# 按真实仓库造出 30 个探针文件（含 3 类误挡物、归档树、缓存、凭据等）
cd /tmp/gi_test/repo && git add -A -n
```

输出（16 个新增，全部是预期放行物）：

```
add '.gitignore'
add 'envs/JSBSim/model/baseline_model.pt'
add 'experiments/2026-10-04-night/logs/official_heading_seed5_gpu0.log'
add 'experiments/2026-10-07-08-formal6m/logs/f6m_5v5_noweapon_s0_seed0_gpu1.log'
add 'experiments/2026-10-07-08-formal6m/manifest.csv'
add 'experiments/2026-10-07-08-formal6m/status/.tb_marker.log'
add 'experiments/2026-10-07-08-formal6m/status/auto_finalize.log'
add 'experiments/2026-10-07-08-formal6m/status/final_state_history.md'
add 'experiments/2026-10-07-08-formal6m/status/freeze_logs/auto_results.txt'
add 'experiments/2026-10-07-08-formal6m/system/events.log'
add 'experiments/_archive/ARCHIVE_MANIFEST.csv'
add 'experiments/_archive/checkpoints/f6m_10v10_noweapon_s0/actor_latest.pt'
add 'experiments/_archive/curves/f6m_10v10_noweapon_s0/metrics.jsonl'
add 'scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/actor_latest.pt'
add 'scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/critic_latest.pt'
add 'scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/metrics.jsonl'
```

同时**未被** add 的探针（用 `git check-ignore -q` 退出码复核，0=被挡）：`actor_0.pt`/`actor_123.pt`/`actor_499.pt`（`actor_[0-9]*.pt`）、`events.out.tfevents.123`（防御规则）、`queue_gpu0.status`（`experiments/**/status/*.status`）、`__pycache__/x.pyc`、根 `results/legacy.csv`（`/results/`）、根 `logs/root_log.log`（`/logs/`）、`docs/_build/index.html`、`lib/source.py`、`test.py`、`.env`、`secrets.pem`、`data.npy`、`demo.acmi`。归档树用例 `_archive/checkpoints/.../actor_latest.pt`、`_archive/curves/.../metrics.jsonl`、`_archive/ARCHIVE_MANIFEST.csv` 全部放行。

### V2：真实仓库现状取证（本仓库直接运行，未做任何修改）

```bash
git check-ignore -v scripts/results/.../run1/metrics.jsonl
# → .gitignore:159:scripts/results/   （现行规则由 L159 决定）
git check-ignore -v experiments/2026-10-07-08-formal6m/logs/f6m_5v5_noweapon_s0_seed0_gpu1.log
# → .gitignore:172:experiments/**/logs/
git check-ignore -v experiments/2026-10-07-08-formal6m/status/queue_gpu0.status
# → .gitignore:173:experiments/**/status/*.status
git ls-files -ci --exclude-standard
# → envs/JSBSim/model/baseline_model.pt
#   envs/JSBSim/model/dodge_missile_model.pt   （历史上被 git add -f 绕过 *.pt）
git status --ignored --porcelain | grep -c '^!!'   # → 40 条
find scripts/results -name '*.pt' | wc -l          # → 4903（4809 池 + 94 latest）
find scripts/results -name '*.jsonl' | wc -l       # → 44
```

### V3：已跟踪文件回归（确保提案不"误伤"任何在库文件）

```bash
cd /tmp/gi_test/repo   # 已换成提案 .gitignore
( git -C /root/autodl-tmp/SEU-SRTP ls-files; \
  echo "scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/actor_0.pt" ) \
  | git check-ignore --stdin --no-index
# 输出只有阳性对照那 1 行 actor_0.pt；
# 460 个已跟踪文件被提案规则挡住的个数 = 0
```

## 8. 残余风险与待确认点

1. **`git add -A` 的范围**：提案生效后，仓库根 `git add -A` 会一次吞下 `scripts/results` 的 94+44 个放行物（约 69 MiB）。若主会话只打算提交 `experiments/_archive/` 精选副本，建议显式路径 add（如 `git add experiments/_archive experiments/2026-10-07-08-formal6m`），不要用 `-A`。
2. **未声明命名的大 `.pt` 不再有兜底**（`*.pt` 已删）。防护 = 提案文件里已写的提交前自查：`git status --porcelain | grep '\.pt$'` 逐个确认 ≤ 1 MiB。如用户仍想要兜底，可改回 `*.pt` + `!*_latest.pt` 方案，但那会违背「策略池用精确命名排除」的要求。
3. **`!experiments/**/*.log` 的放行范围**是实验树内全部 `.log`（含未来可能出现的噪声日志）。要更严格可改成三条窄规则（`!experiments/**/logs/*.log`、`!experiments/**/status/*.log`、`!experiments/**/system/*.log`），二选一由用户定。
4. **`.status` 仍被排除**：如需入库，`git add -f` 或把内容并进 `status/*.md`。
5. **两个空 run 目录**（`SMOKE_heading/run1`、`official_1v1_shoot_hier_vsbaseline/run1`）无内容，归档跳过即可。
6. 本提案**不涉及**：删除任何文件、改动 `.git`、重写历史、触碰 `scripts/results` 原件。与 CLAUDE.md「只用 cp、绝不 mv/rm」一致。
