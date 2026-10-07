#!/usr/bin/env bash
# OS-level sampler for the formal-6M campaign. Runs inside tmux so it survives
# a dead Claude/VS Code session -- it is the durable trace of what happened,
# independent of whether anyone was watching.
#
# It does NOT restart jobs: a restart would create run2/ and muddy the
# provenance of a formal run, so restarts are decided deliberately (and logged
# in status/incidents.md) rather than automatically.
#
# Column schema is a SUPERSET of the 2026-10-04 campaign's system_samples.csv so
# that make_manifest.py (whose resource_peaks() selects columns by the regex
# `gpu\d_mem_mb`) works unmodified.
#
# CPU measurement -- IMPORTANT (incident F16)
# -------------------------------------------
# /proc/stat is NOT a reliable CPU source in this container. It reports the HOST's
# 192 logical CPUs and, in repeated 5-second samples, returns deltas alternating
# between 0 and ~200 cores' worth of ticks while the container is demonstrably
# busy. Any "N of 48 cores busy" figure derived from it is meaningless.
#
# The authoritative source is the container's own cgroup accounting:
#   /sys/fs/cgroup/cpu.stat  usage_usec   (microseconds of CPU actually consumed)
# and the quota is /sys/fs/cgroup/cpu.max (4800000/100000 = 48 cores).
# We therefore emit cpu_busy_pct measured as a fraction of the QUOTA from
# cpu.stat, plus the raw cores, and we no longer emit a /proc/stat-derived value.
# v1 samples (system_samples.csv) used the /proc/stat method and must not be used
# for CPU claims; v2 writes system_samples_v2.csv with the corrected schema.
#
# Usage: os_watchdog.sh [interval_seconds]
set -u

INTERVAL=${1:-600}
CAMP=/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m
CONDA=/root/miniconda3
PY=${CONDA}/envs/jsbsim/bin/python
SAMPLES="${CAMP}/system/system_samples_v2.csv"
EVENTS="${CAMP}/system/events.log"

mkdir -p "${CAMP}/system" "${CAMP}/status"

if [ ! -f "${SAMPLES}" ]; then
    echo "timestamp,load1,load5,cpu_busy_pct_of_quota,busy_cores_of_quota,quota_cores,nr_throttled_pct,mem_used_gb,mem_total_gb,n_train_procs,gpu0_util,gpu0_mem_mb,gpu1_util,gpu1_mem_mb,gpu2_util,gpu2_mem_mb,train_rss_gb,tmux_sessions" > "${SAMPLES}"
fi

echo "$(date -Is) watchdog started interval=${INTERVAL}s" >> "${EVENTS}"

while true; do
    TS=$(date -Is)
    read -r LOAD1 LOAD5 < <(cut -d' ' -f1,2 /proc/loadavg)
    read -r MEMTOT MEMUSED < <(free -m | awk '/^Mem:/{printf "%.1f %.1f", $2/1024, $3/1024}')

    GPU=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' ' | paste -sd,)
    G0U=$(echo "$GPU" | cut -d, -f1); G0M=$(echo "$GPU" | cut -d, -f2)
    G1U=$(echo "$GPU" | cut -d, -f3); G1M=$(echo "$GPU" | cut -d, -f4)
    G2U=$(echo "$GPU" | cut -d, -f5); G2M=$(echo "$GPU" | cut -d, -f6)

    # CPU occupancy from the container's own cgroup accounting (see header).
    QUOTA=$(awk '{print $1/$2}' /sys/fs/cgroup/cpu.max 2>/dev/null)
    QUOTA=${QUOTA:-48}
    U1=$(awk '/usage_usec/{print $2}' /sys/fs/cgroup/cpu.stat)
    sleep 2
    U2=$(awk '/usage_usec/{print $2}' /sys/fs/cgroup/cpu.stat)
    CORES=$(awk -v a="${U1}" -v b="${U2}" 'BEGIN{printf "%.2f", (b-a)/1e6/2}')
    BUSYQ=$(awk -v c="${CORES}" -v q="${QUOTA}" 'BEGIN{printf "%.1f", 100.0*c/q}')
    # throttling over the whole container life -- a leading indicator that the
    # quota is actually binding
    THROT=$(awk '/nr_periods/{p=$2} /nr_throttled/{t=$2} END{if(p>0) printf "%.4f", 100.0*t/p; else print "0"}' \
            /sys/fs/cgroup/cpu.stat)

    read -r NPROC RSS < <(ps -eo rss,args --no-headers 2>/dev/null \
        | grep -E -- "-MultipleCombat-|train_jsbsim.py" \
        | awk '{n++; r+=$1} END {printf "%d %.2f", n, r/1024/1024}')

    NSESS=$(tmux ls 2>/dev/null | wc -l)

    echo "${TS},${LOAD1},${LOAD5},${BUSYQ},${CORES},${QUOTA},${THROT},${MEMUSED},${MEMTOT},${NPROC:-0},${G0U},${G0M},${G1U},${G1M},${G2U},${G2M},${RSS:-0},${NSESS}" >> "${SAMPLES}"

    # Event detection: a job's worker count dropping to zero while it has not
    # finished is the signal worth recording.
    for exp in f6m_10v10_noweapon_s0 f6m_5v5_noweapon_s0 f6m_3v3_noweapon_s0 \
               f6m_2v2_noweapon_s0 f6m_official_2v2_noweapon_s0; do
        c=$(ps -eo args --no-headers | grep -c -- "-MultipleCombat-${exp}")
        if [ "$c" -eq 0 ]; then
            if [ ! -f "${CAMP}/status/.down_${exp}" ]; then
                touch "${CAMP}/status/.down_${exp}"
                echo "${TS} DEAD ${exp} (no rollout workers)" >> "${EVENTS}"
            fi
        else
            rm -f "${CAMP}/status/.down_${exp}"
        fi
    done

    for f in $(grep -lE "Traceback \(most recent call last\)" "${CAMP}"/logs/*.log 2>/dev/null); do
        if [ ! -f "${CAMP}/status/.tb_$(basename "$f")" ]; then
            touch "${CAMP}/status/.tb_$(basename "$f")"
            echo "${TS} TRACEBACK in $(basename "$f")" >> "${EVENTS}"
        fi
    done

    "${PY}" "${CAMP}/scripts/watch_f6m.py" > "${CAMP}/status/monitor_latest.md.tmp" 2>/dev/null \
        && mv "${CAMP}/status/monitor_latest.md.tmp" "${CAMP}/status/monitor_latest.md"

    sleep "${INTERVAL}"
done
