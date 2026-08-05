# LAG 服务器环境迁移记录

> 将 LAG (Light Aircraft Game) 从本地 WSL 迁移至 AutoDL 云服务器完整记录

---

## 1. 服务器信息

- **平台**: AutoDL (Seetacloud)
- **GPU**: NVIDIA GeForce RTX 5090 × 1，32GB 显存
- **CPU**: 25 核
- **内存**: 90 GB
- **系统**: Ubuntu 22.04.5 LTS
- **CUDA**: 13.2 (Driver 595.71.05)
- **SSH**: 见服务器
- **密码**: 以后不要写在文档里哦，因为要上传github仓库的
- **子账号**: SEU-SRTP-01（用于自主开关机和查看 SSH 信息）
- **项目目录**: `/root/autodl-tmp/SEU-SRTP-LAG`
- **数据盘**: `/root/autodl-tmp/`（50G，关机不丢失；系统盘 / 仅 30G）

---

## 2. 完整安装命令

### 2.1 SSH 登录

```bash
ssh 
```

### 2.2 克隆仓库（使用学术加速）

```bash
source /etc/network_turbo                          # 开启 AutoDL 学术加速
cd /root/autodl-tmp
git clone https://github.com/liuqh16/LAG.git SEU-SRTP-LAG
unset http_proxy && unset https_proxy             # 关闭加速
```

### 2.3 上传 environment.yml（从本地）

在**本地** Windows 终端执行：

```bash
scp -P 54012 D:\Srtp\RLearning\LAG\environment.yml root@connect.bjb2.seetacloud.com:/root/autodl-tmp/SEU-SRTP-LAG/
```

### 2.4 创建 conda 环境

```bash
# 重要: 不能用 environment.yml 直接创建（Python 3.8 版本太旧，不支持 RTX 5090）
# 采用克隆 base 环境方案（base 预装 torch 2.8.0+cu128）

conda create -n jsbsim --clone base -y
conda activate jsbsim

# 安装 JSBSim 编译依赖
pip install Cython

# 安装项目依赖
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple jsbsim==1.1.6 pymap3d geographiclib gymnasium wandb icecream setproctitle pyyaml shapely sympy networkx
```

### 2.5 初始化 JSBSim 子模块

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG
source /etc/network_turbo
git submodule init
git submodule update
unset http_proxy && unset https_proxy
```

### 2.6 修改 CUDA 设备号

```bash
cd scripts
sed -i 's/CUDA_VISIBLE_DEVICES=[0-9]*/CUDA_VISIBLE_DEVICES=0/' train_heading.sh
sed -i 's/CUDA_VISIBLE_DEVICES=[0-9]*/CUDA_VISIBLE_DEVICES=0/' train_selfplay.sh
sed -i 's/CUDA_VISIBLE_DEVICES=[0-9]*/CUDA_VISIBLE_DEVICES=0/' train_selfplay_shoot.sh
sed -i 's/CUDA_VISIBLE_DEVICES=[0-9]*/CUDA_VISIBLE_DEVICES=0/' train_vsbaseline.sh
```

### 2.7 修复代码兼容性问题

```bash
# Python 3.12 去掉了 np.product，改为 np.prod
sed -i 's/np\.product/np.prod/g' algorithms/utils/flatten.py

# render 脚本缺少 render_mode 字段
# render_jsbsim.py 中 config 字典的 "run_dir": run_dir 后面加一行:
#         "render_mode": "txt"

# render 函数传了不存在的 tacview 参数，去掉
# jsbsim_runner.py 第203行: 删掉 ,tacview=self.tacview
# jsbsim_runner.py 第198行: logging.info 前加 f 前缀
```

---

## 3. 运行命令

### 3.1 Smoke Test（环境验证）

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG
conda activate jsbsim
python test_env.py
```

**产出**: `JSBSimRecording.txt.acmi`（约 563KB）

### 3.2 SingleControl Heading 训练

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG/scripts
conda activate jsbsim
bash train_heading.sh
```

**产出**: `scripts/results/SingleControl/1/heading/ppo/v1/run3/actor_latest.pt` 和 `critic_latest.pt`

### 3.3 Render（生成 ACMI 回放）

```bash
cd /root/autodl-tmp/SEU-SRTP-LAG/scripts
CUDA_VISIBLE_DEVICES=0 python render/render_jsbsim.py \
    --env-name SingleControl --algorithm-name ppo --scenario-name 1/heading --experiment-name v1 \
    --seed 5 --n-training-threads 1 --n-rollout-threads 4 --cuda \
    --log-interval 1 --save-interval 1 \
    --num-mini-batch 5 --buffer-size 3000 --num-env-steps 1e8 \
    --lr 3e-4 --gamma 0.99 --ppo-epoch 4 --clip-params 0.2 --max-grad-norm 2 --entropy-coef 1e-3 \
    --hidden-size "128 128" --act-hidden-size "128 128" --recurrent-hidden-size 128 --recurrent-hidden-layers 1 --data-chunk-length 8 \
    --model-dir './results/SingleControl/1/heading/ppo/v1/run3'
```

**产出**: `scripts/results/SingleControl/1/heading/ppo/v1/render/v1.txt.acmi`（约 22KB）

---

## 4. 报错与解决方法

### 错误 1: GitHub clone 超时

**现象**: `GnuTLS recv error (-110): The TLS connection was non-properly terminated` 或克隆速度极慢

**原因**: 国内服务器直连 GitHub 网络不稳定

**解决**:
```bash
source /etc/network_turbo      # 开启 AutoDL 学术加速
git clone ...
unset http_proxy && unset https_proxy  # 用完关闭
```

### 错误 2: conda activate 失败

**现象**: `CondaError: Run 'conda init' before 'conda activate'`

**原因**: 首次使用 conda 未初始化 shell

**解决**:
```bash
conda init bash
source ~/.bashrc
```

### 错误 3: conda env create 卡在 "Installing pip dependencies"

**现象**: conda 阶段完成后，pip 下载依赖包时 SSH 断连 `client_loop: send disconnect: Connection reset`

**原因**: pip 下载大文件时间过长触发 SSH 超时断连

**解决**: 使用 tmux/screen 后台运行，或改用清华等国内镜像源加速

### 错误 4: torch 2.4.1 不兼容 RTX 5090

**现象**: `RuntimeError: CUDA error: no kernel image is available for execution on the device`

**原因**: torch 2.4.1 是 2024 年版本，不含 RTX 5090 (Blackwell 架构, 2025) 的 CUDA kernel。需要 torch 2.6+

**解决**: 不新建 Python 3.8 环境 + 装 torch 2.4.1，而是克隆 base 环境（预装 torch 2.8.0+cu128）

### 错误 5: JSBSim 编译失败

**现象**: `error: unknown file type '.pyx'`

**原因**: JSBSim 需要 Cython 编译 .pyx 扩展，但环境未装 Cython

**解决**: `pip install Cython` 后再装 jsbsim

### 错误 6: np.product 不存在

**现象**: `AttributeError: module 'numpy' has no attribute 'product'`

**原因**: Python 3.12 中去掉了旧的 `np.product`（之前是 `np.prod` 的别名）

**解决**: `sed -i 's/np\.product/np.prod/g' algorithms/utils/flatten.py`

### 错误 7: render 缺少 render_mode

**现象**: `KeyError: 'render_mode'`

**原因**: render_jsbsim.py 创建的 config 字典中没有 render_mode 字段

**解决**: 在 config 字典中加 `"render_mode": "txt"`

### 错误 8: render 报错 tacview 参数

**现象**: `TypeError: DummyVecEnv.render() got an unexpected keyword argument 'tacview'`

**原因**: DummyVecEnv 的 render 方法不接受 tacview 参数

**解决**: 在 jsbsim_runner.py 第203行删掉 `,tacview=self.tacview`

---

## 5. 验证结果

| 验证项 | 状态 | 产物 |
|--------|------|------|
| Smoke Test | ✅ 通过 | `JSBSimRecording.txt.acmi` (563KB) |
| Heading 训练 | ✅ 通过 | `run3/actor_latest.pt` + `critic_latest.pt` |
| ACMI Render | ✅ 通过 | `render/v1.txt.acmi` (22KB) |

---

## 6. 注意事项

- **用完记得关机！** 通过 AutoDL 网页控制台或子账号关机，避免浪费 GPU 时长
- **容器 15 天自动释放**：数据盘 `/root/autodl-tmp/` 内容会丢失，重要产出（checkpoint、ACMI）及时下载到本地
- **子账号** `SEU-SRTP-01` 可以让多个组员登录、开关机、查看 SSH 信息
- **运行长时间任务用 tmux**：`tmux new -s <名字>`，防止 SSH 断连杀死训练
- **监控 GPU**：`watch -n 1 nvidia-smi`
- **学术加速** `source /etc/network_turbo` 仅加速 GitHub/HuggingFace，用后关闭否则 pip 会更慢
- **项目统一路径**：`/root/autodl-tmp/SEU-SRTP-LAG`
