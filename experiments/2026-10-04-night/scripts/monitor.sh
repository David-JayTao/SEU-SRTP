#!/usr/bin/env bash
# Lightweight system sampler for the overnight run.
# Appends one CSV row every SAMPLE_INTERVAL seconds: load, CPU busy, per-GPU
# utilisation and VRAM, and the RSS of the training processes.
#
# Deliberately dependency-free (no psutil/pynvml) so it cannot fail on this box.
set -u

OUT=${1:-/root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night/system/system_samples.csv}
INTERVAL=${2:-15}

mkdir -p "$(dirname "${OUT}")"
if [ ! -s "${OUT}" ]; then
    echo "timestamp,load1,load5,cpu_busy_pct,mem_used_gb,mem_total_gb,n_train_procs,gpu0_util,gpu0_mem_mb,gpu1_util,gpu1_mem_mb,gpu2_util,gpu2_mem_mb" > "${OUT}"
fi

while true; do
    TS=$(date -Is)
    read -r L1 L5 _ < /proc/loadavg

    # CPU busy from /proc/stat deltas over 1s
    read -r _ u n s i rest < /proc/stat
    T1=$((u + n + s + i)); I1=$i
    sleep 1
    read -r _ u n s i rest < /proc/stat
    T2=$((u + n + s + i)); I2=$i
    DT=$((T2 - T1)); DI=$((I2 - I1))
    if [ "${DT}" -gt 0 ]; then BUSY=$(( (100 * (DT - DI)) / DT )); else BUSY=0; fi

    MEM=$(awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{printf "%.1f,%.1f", (t-a)/1048576, t/1048576}' /proc/meminfo)
    NPROC=$(pgrep -fc "train_jsbsim.py" || true)
    [ -z "${NPROC}" ] && NPROC=0

    GPU=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | paste -sd, - | tr -d ' ')
    [ -z "${GPU}" ] && GPU=",,,,,"

    echo "${TS},${L1},${L5},${BUSY},${MEM},${NPROC},${GPU}" >> "${OUT}"
    sleep "${INTERVAL}"
done
