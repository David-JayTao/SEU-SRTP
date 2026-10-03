#!/usr/bin/env bash
# Periodic sweep loop that exits early on a real problem, so a long quiet run
# does not also mean a long blind run.
#
# Exits immediately if:
#   - an unhandled (non-timeout) traceback appears in any experiment log
#   - no training process is alive while queue ledgers still have unfinished jobs
#   - free disk on /root/autodl-tmp drops below 5 GB
# Otherwise it sweeps every INTERVAL seconds for CYCLES cycles.
set -u

REPO=/root/autodl-tmp/SEU-SRTP
EXP="${REPO}/experiments/2026-10-04-night"
INTERVAL=${1:-570}
CYCLES=${2:-6}

unhandled() {
    local n=0
    for f in "${EXP}"/logs/*.log; do
        [ -e "$f" ] || continue
        if grep -q "Traceback" "$f" 2>/dev/null && \
           ! tail -40 "$f" | grep -qE "^(KeyboardInterrupt|SystemExit)"; then
            n=$((n+1))
            echo "!! unhandled traceback: $f"
        fi
    done
    return ${n}
}

for i in $(seq 1 "${CYCLES}"); do
    sleep "${INTERVAL}"
    bash "${EXP}/scripts/sweep.sh" 2>&1 | tail -60

    if ! unhandled > /tmp/_unhandled.txt 2>&1; then
        echo "WATCHDOG: aborting on unhandled traceback"
        cat /tmp/_unhandled.txt
        exit 2
    fi

    live=$(pgrep -fc "train_jsbsim.py" || true)
    pending=$(grep -hs "^>>>" "${EXP}"/status/queue_*.status 2>/dev/null | wc -l)
    done_=$(grep -hs "^<<<" "${EXP}"/status/queue_*.status 2>/dev/null | wc -l)
    if [ "${live:-0}" -eq 0 ] && [ "${pending}" -gt "${done_}" ]; then
        echo "WATCHDOG: no training process alive but queues still have work"
        exit 3
    fi

    avail=$(df -m /root/autodl-tmp | tail -1 | awk '{print $4}')
    if [ "${avail}" -lt 5120 ]; then
        echo "WATCHDOG: low disk (${avail} MB free)"
        exit 4
    fi
done
echo "WATCHDOG: completed ${CYCLES} sweeps normally"
