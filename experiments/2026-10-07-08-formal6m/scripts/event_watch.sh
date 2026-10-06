#!/usr/bin/env bash
# Event watcher: blocks until something the operator actually needs to react to.
#
# Polling every 13 minutes burns attention on a campaign whose failure modes are
# rare and discrete. This watcher instead exits -- which is what re-invokes the
# agent -- only on:
#   * a lane losing all its rollout workers        (job died)
#   * a lane reaching its 6M target                (lane free, next job can start)
#   * a Traceback appearing in a log               (crash)
#   * a scheduled decision point being reached     (lane re-use decisions)
#   * a heartbeat, every HEARTBEAT seconds         (so silence is not ambiguous)
#
# It writes a one-line reason to stdout and exits 0. tmux/SIGTERM ends it too.
#
# Usage: event_watch.sh [heartbeat_seconds]
set -u

HEARTBEAT=${1:-7200}   # 2 h
CAMP=/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m
TARGET=6000000

# Lanes expected to be live, with their rollout thread counts.
declare -A LANES=(
  [f6m_10v10_noweapon_s0]=20
  [f6m_5v5_noweapon_s0]=8
  [f6m_3v3_noweapon_s0]=8
  [f6m_2v2_noweapon_s0]=4
  [f6m_official_2v2_noweapon_s0]=4
  [f6m_official_1v1_selfplay_s1]=3
  [f6m_official_1v1_vsbaseline_s1]=3
  [f6m_official_1v1_shoot_hier_selfplay_s1]=3
  [f6m_official_1v1_hier_selfplay_s1]=3
)

# Decision points at which the operator wants to re-plan lane allocation.
DECISION_POINTS=("2026-10-07 15:30" "2026-10-07 22:30" "2026-10-08 00:00" "2026-10-08 01:30" "2026-10-08 08:30" "2026-10-08 09:00")

started=$(date +%s)
declare -A prev_alive prev_steps dp_done

# Seed the baselines so the first sweep does not fire a spurious "lane changed".
for exp in "${!LANES[@]}"; do
    prev_alive[$exp]=$(ps -eo args --no-headers 2>/dev/null | grep -c -- "-MultipleCombat-${exp}\|-SingleCombat-${exp}\|-SingleControl-${exp}")
    prev_steps[$exp]=0
done
for dp in "${DECISION_POINTS[@]}"; do dp_done[$dp]=0; done

while true; do
    now_epoch=$(date +%s)
    now_human=$(date '+%Y-%m-%d %H:%M')

    # --- scheduled decision points
    for dp in "${DECISION_POINTS[@]}"; do
        if [ "${dp_done[$dp]}" = "0" ] && [[ ! "${now_human}" < "${dp}" ]]; then
            dp_done[$dp]=1
            echo "DECISION_POINT reached: ${dp} (now ${now_human}) -- re-plan lane allocation per status/plan.md"
            exit 0
        fi
    done

    # --- heartbeat
    if [ $(( now_epoch - started )) -ge "${HEARTBEAT}" ]; then
        echo "HEARTBEAT after ${HEARTBEAT}s (now ${now_human}) -- routine check"
        exit 0
    fi

    for exp in "${!LANES[@]}"; do
        # workers alive?
        alive=$(ps -eo args --no-headers 2>/dev/null \
            | grep -c -- "-MultipleCombat-${exp}\|-SingleCombat-${exp}\|-SingleControl-${exp}")
        if [ "${prev_alive[$exp]}" -gt 0 ] && [ "${alive}" -eq 0 ]; then
            # distinguish "finished" from "died": look at the last logged step
            steps=$(grep -ho "total num timesteps [0-9]*" -r "${CAMP}/logs" 2>/dev/null | head -0; \
                    find "${CAMP}/logs" -name "${exp}_seed*.log" -exec grep -ho "total num timesteps [0-9]*" {} \; 2>/dev/null \
                    | awk '{print $4}' | sort -n | tail -1)
            steps=${steps:-0}
            if [ "${steps}" -ge "${TARGET}" ]; then
                echo "LANE_FINISHED ${exp} at ${steps} steps (now ${now_human}) -- launch the next queued job"
            else
                echo "LANE_DIED ${exp} at only ${steps} of ${TARGET} steps (now ${now_human}) -- diagnose before restarting"
            fi
            exit 0
        fi
        prev_alive[$exp]=${alive}
    done

    # --- traceback appearing in this campaign's logs
    tb=$(grep -lE "Traceback \(most recent call last\)" "${CAMP}"/logs/*.log 2>/dev/null | head -1)
    if [ -n "${tb}" ] && [ ! -f "${CAMP}/status/.seen_tb_$(basename "$tb")" ]; then
        touch "${CAMP}/status/.seen_tb_$(basename "$tb")"
        echo "TRACEBACK in $(basename "$tb") (now ${now_human}) -- check whether it is a crash or a SIGINT teardown"
        exit 0
    fi

    sleep 60
done
