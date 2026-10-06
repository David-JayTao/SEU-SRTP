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
# that experiments/2026-10-07-08-formal6m/scripts/make_manifest.py (whose
# resource_peaks() selects columns by the regex `gpu\d_mem_mb`) works unmodified.
#
# cpu_busy_pct is expressed as a percentage of the 48-core cgroup QUOTA, not of
# the host's 192 logical CPUs -- the quota is the resource we can actually spend.
#
# Usage: os_watchdog.sh [interval_seconds]
set -u

INTERVAL=${1:-600}
CAMP=/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m
CONDA=/root/miniconda3
PY=${CONDA}/envs/jsbsim/bin/python
SAMPLES="${CAMP}/system/system_samples.csv"
EVENTS="${CAMP}/system/events.log"

mkdir -p "${CAMP}/system" "${CAMP}/status"

if [ ! -f "${SAMPLES}" ]; then
    echo "timestamp,load1,load5,cpu_busy_pct,mem_used_gb,mem_total_gb,n_train_procs,gpu0_util,gpu0_mem_mb,gpu1_util,gpu1_mem_mb,gpu2_util,gpu2_mem_mb,train_cpu_pct,train_rss_gb,tmux_sessions" > "${SAMPLES}"
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

    # CPU occupancy from /proc/stat deltas. /proc/stat's aggregate line counts
    # all host CPUs, so normalise against the observed total, not the quota.
    read -r _ u n s i w irq sirq st _ < /proc/stat
    T1=$((u+n+s+i+w+irq+sirq+st)); I1=$i
    sleep 2
    read -r _ u n s i w irq sirq st _ < /proc/stat
    T2=$((u+n+s+i+w+irq+sirq+st)); I2=$i
    DT=$((T2-T1)); DI=$((I2-I1))
    # busy_core_seconds/s -> cores; express as % of the 48-core quota
    BUSY=$(awk -v dt="${DT}" -v di="${DI}" 'BEGIN{ if(dt>0) printf "%.1f", 100.0*(dt-di)/dt; else print "0" }')
    # BUSY is % of host logical CPUs; convert to % of quota (48 of 192)
    BUSYQ=$(awk -v b="${BUSY}" 'BEGIN{ printf "%.1f", b*192.0/48.0 }')

    read -r NPROC CPU RSS < <(ps -eo rss,pcpu,args --no-headers 2>/dev/null \
        | grep -E -- "-MultipleCombat-|train_jsbsim.py" \
        | awk '{n++; c+=$2; r+=$1} END {printf "%d %.1f %.2f", n, c, r/1024/1024}')

    NSESS=$(tmux ls 2>/dev/null | wc -l)

    echo "${TS},${LOAD1},${LOAD5},${BUSYQ},${MEMUSED},${MEMTOT},${NPROC:-0},${G0U},${G0M},${G1U},${G1M},${G2U},${G2M},${CPU:-0},${RSS:-0},${NSESS}" >> "${SAMPLES}"

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
