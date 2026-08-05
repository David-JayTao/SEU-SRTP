# AutoDL 新容器快速配置指南 — LAG 项目

> 适用于：新租容器、旧容器释放后重建、其他组员从零开始

---

## 0. 前置知识：AutoDL 文件结构

| 路径 | 容量 | 持久性 | 放什么 |
|------|------|--------|--------|
| `/` (系统盘) | 30G | 关机保留，释放丢失 | 代码、配置文件、conda 环境 |
| `/root/autodl-tmp/` (数据盘) | 分配额度 | 关机保留，释放丢失 | **项目代码、数据、checkpoint、日志** |
| `/root/autodl-fs/` | 网络存储 | 跨实例共享 | 长期备份（如已购买） |

**核心原则**：所有干活的东西都放 `/root/autodl-tmp/`，系统盘只放 conda 和系统包。

### 推荐目录结构

```
/root/autodl-tmp/
├── SEU-SRTP-LAG/          # LAG 项目主目录（git clone）
│   ├── docs/              # 文档和配置记录
│   ├── scripts/
│   │   └── results/       # 训练产物：checkpoint、日志、ACMI
│   └── ...
├── data/                  # 可选：额外数据集或模型文件
└── backups/               # 可选：重要产出的备份
```

---

## 1. 新容器上线 — 快速配置清单

共计 **~20 分钟**，如下步骤按顺序执行：

### Step 1: SSH 登录

```bash
ssh -p <端口> root@connect.<区域>.seetacloud.com
```

登录后看到 AutoDL 欢迎界面，确认 GPU 型号正确。

### Step 2: 确认基础环境

```bash
nvidia-smi                   # 确认 GPU 和 CUDA 版本
which conda && conda --version
python --version
python -c "import torch; print(torch.__version__)"
```

四个命令一次跑，确认 GPU、conda、Python、torch 都就绪。

如果缺少 conda 或 torch，用：
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /root/miniconda3
eval "$(/root/miniconda3/bin/conda shell.bash hook)"
conda init bash
```

### Step 3: 克隆 LAG 仓库

```bash
source /etc/network_turbo                          # 加速 GitHub
cd /root/autodl-tmp
git clone https://github.com/liuqh16/LAG.git SEU-SRTP-LAG
cd SEU-SRTP-LAG
git submodule init
git submodule update
unset http_proxy && unset https_proxy             # 关闭加速
```

### Step 4: 创建 conda 环境

**⚠️ 不用 README 的 `conda env create -f environment.yml`**（Python 3.8 太旧不支持 5090）。

直接用克隆 base 环境的方案：

```bash
conda create -n jsbsim --clone base -y
conda activate jsbsim
conda init bash && source ~/.bashrc

# 装项目依赖
pip install Cython
pip install jsbsim==1.1.6 pymap3d geographiclib gymnasium wandb icecream setproctitle pyyaml shapely sympy networkx
```

### Step 5: 应用必要修复

复制粘贴一次性执行：

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG

# CUDA 设备改为 0
sed -i 's/CUDA_VISIBLE_DEVICES=[0-9]*/CUDA_VISIBLE_DEVICES=0/' scripts/train_*.sh

# numpy 兼容性 (Python 3.12)
sed -i 's/np\.product/np.prod/g' algorithms/utils/flatten.py

# render 脚本补 render_mode
sed -i 's/"run_dir": run_dir/"run_dir": run_dir,\n        "render_mode": "txt"/' scripts/render/render_jsbsim.py

# render 函数补 f-string + 移除 tacview 参数
sed -i '198s/logging.info("\\nStart render/logging.info(f"\\nStart render/' runner/jsbsim_runner.py
sed -i '203s/,tacview=self.tacview//' runner/jsbsim_runner.py
```

### Step 6: 验证环境

```bash
conda activate jsbsim
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import jsbsim; print('JSBSim OK')"

cd /root/autodl-tmp/SEU-SRTP-LAG
python test_env.py
ls -la JSBSimRecording.txt.acmi
```

最后一行看到 `.acmi` 文件且 size > 0，说明一切 OK。

---

## 2. 常用操作速查

### 后台运行任务（防 SSH 断连）

```bash
tmux new -s <名字>                  # 创建会话
# 在 tmux 里跑你的任务...
# Ctrl+B 再按 D                      # 分离，任务继续在后台跑
tmux attach -t <名字>               # 重新连上
tmux ls                             # 查看所有会话

# 让 tmux 支持鼠标滚轮
echo "set -g mouse on" >> ~/.tmux.conf
```

### 训练

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG/scripts
conda activate jsbsim
bash train_heading.sh                # SingleControl heading
# bash train_selfplay.sh             # 1v1 selfplay
# bash train_selfplay_shoot.sh       # 1v1 shoot missile
# bash train_vsbaseline.sh           # 1v1 vs baseline
# bash train_share_selfplay.sh       # 2v2 multi-agent
```

### 监控 GPU

```bash
watch -n 1 nvidia-smi
```

### 下载产物到本地

```bash
# 在本地 Windows 执行
scp -P <端口> -r root@connect.<区域>.seetacloud.com:/root/autodl-tmp/SEU-SRTP-LAG/scripts/results/ D:\本地目录\
```

### 关机

```bash
shutdown -h now
# 或通过 AutoDL 网页控制台点关机
```

---

## 3. 潜在问题快速修复

| 症状 | 修复 |
|------|------|
| GitHub clone 超时/慢 | `source /etc/network_turbo` |
| `conda activate` 报错 | `conda init bash && source ~/.bashrc` |
| `no kernel image available` | torch 版本太老不支持 5090 → 用克隆 base 方案 |
| `np.product` 报错 | `sed -i 's/np\.product/np.prod/g' algorithms/utils/flatten.py` |
| `KeyError: 'render_mode'` | 在 render_jsbsim.py 的 config 字典加 `"render_mode": "txt"` |
| SSH 断连训练被杀 | 开 tmux 再跑任务 |
| pip 下载太慢 | `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <包名>` |

---

## 4. 注意事项

- **用完关机** — 按量计费从创建实例那一刻开始扣钱
- **重要产出及时下载** — 容器 15 天自动释放，数据盘内容消失
- **系统盘只有 30G** — 数据文件放 `/root/autodl-tmp/`
- **`source /etc/network_turbo` 只加速 GitHub/HuggingFace** — 用完关，否则 pip 更慢
- **tmux 里 Ctrl+B 再按 D 是分离** — 不是 Ctrl+C
- **新容器只需执行 Step 1-6，不用再做踩坑调查**
