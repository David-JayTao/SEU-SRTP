#!/usr/bin/env bash
# Unified launcher for LAG reproduction + scaling experiments.
#
# Reproduces the *exact* hyper-parameters of the official scripts/*.sh entries,
# with two documented compatibility deviations:
#   (1) --use-wandb is dropped (no external W&B account/network on this server).
#       With use_wandb=False the runner writes checkpoints to scripts/results/...
#       exactly like the official non-wandb code path. No algorithmic change.
#   (2) official scripts pass `--clip-params 0.2` (typo). config.py defines
#       `--clip-param` (default 0.2) and train_jsbsim.py uses parse_known_args,
#       so the official scripts silently fall back to the 0.2 default.
#       We pass `--clip-param 0.2` explicitly -> identical value, no semantic change.
#
# Usage: run_train.sh <gpu_id> <env_name> <scenario> <algo> <exp_name> <seed> \
#                     <n_rollout_threads> <num_env_steps> <extra args...>
set -u

GPU_ID=${1:?gpu id}
ENV_NAME=${2:?env name}
SCENARIO=${3:?scenario}
ALGO=${4:?algorithm}
EXP=${5:?experiment name}
SEED=${6:?seed}
NTHREADS=${7:?n rollout threads}
NSTEPS=${8:?num env steps}
shift 8
EXTRA="$*"

REPO=/root/autodl-tmp/SEU-SRTP
CONDA=/root/miniconda3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_LOG_DIR="${RUN_LOG_DIR:-$SCRIPT_DIR/../logs}"

export CUDA_VISIBLE_DEVICES=${GPU_ID}
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export WANDB_MODE=disabled
export PYTHONUNBUFFERED=1

source ${CONDA}/etc/profile.d/conda.sh
conda activate jsbsim
cd "${REPO}/scripts"

STAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="${RUN_LOG_DIR}/${EXP}_seed${SEED}_gpu${GPU_ID}_${STAMP}.log"

echo "================================================================"
echo "EXPERIMENT : ${EXP}"
echo "git commit : $(git -C ${REPO} rev-parse HEAD)  branch=$(git -C ${REPO} rev-parse --abbrev-ref HEAD)"
echo "env/scen   : ${ENV_NAME} / ${SCENARIO}"
echo "algo       : ${ALGO}   seed=${SEED}"
echo "gpu        : ${GPU_ID}"
echo "threads    : ${NTHREADS}   num_env_steps=${NSTEPS}"
echo "extra      : ${EXTRA}"
echo "log        : ${LOGFILE}"
echo "start      : $(date -Is)"
echo "================================================================"

# Optional hard wall-clock cap (seconds). The queue runner uses this so that a
# slow scale cannot block every later job; checkpoints are written every
# episode, so at most the in-flight episode is lost on timeout.
TIMEOUT_PREFIX=""
if [ -n "${RUN_TIME_LIMIT:-}" ]; then
    TIMEOUT_PREFIX="timeout -k 60 -s INT ${RUN_TIME_LIMIT}"
fi

# shellcheck disable=SC2086
${TIMEOUT_PREFIX} python train/train_jsbsim.py \
    --env-name "${ENV_NAME}" \
    --scenario-name "${SCENARIO}" \
    --algorithm-name "${ALGO}" \
    --experiment-name "${EXP}" \
    --seed "${SEED}" \
    --n-training-threads 1 \
    --n-rollout-threads "${NTHREADS}" \
    --cuda \
    --log-interval 1 \
    --save-interval 1 \
    --num-mini-batch 5 \
    --buffer-size 3000 \
    --num-env-steps "${NSTEPS}" \
    --lr 3e-4 \
    --gamma 0.99 \
    --ppo-epoch 4 \
    --clip-param 0.2 \
    --max-grad-norm 2 \
    --entropy-coef 1e-3 \
    --hidden-size "128 128" \
    --act-hidden-size "128 128" \
    --recurrent-hidden-size 128 \
    --recurrent-hidden-layers 1 \
    --data-chunk-length 8 \
    --user-name "liuyunxiao" \
    ${EXTRA} 2>&1 | tee "${LOGFILE}"

echo "================================================================"
echo "EXPERIMENT ${EXP} exited with code ${PIPESTATUS[0]} at $(date -Is)"
echo "================================================================"
