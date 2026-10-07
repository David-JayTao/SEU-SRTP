#!/usr/bin/env bash
# Dead-man's switch: freeze and commit the campaign WITHOUT needing the agent.
#
# Why this exists
# ---------------
# The training runs live in tmux and survive anything. The *agent* does not: cron
# jobs and background watchers only fire while a Claude session is alive, and on
# 2026-10-07 the session was offline for ~12 h during which nothing was committed.
# Training was never at risk, but the deliverable was: if the platform had shut
# down during that window, the last 12 h of results would have been uncommitted.
#
# This script runs in its own tmux session, on the server, and depends on nothing
# but bash. It takes periodic snapshots, and performs the full final freeze
# (including the inference-only probes) at the deadline. If the agent is awake it
# will also do this; the operations are idempotent, so running both is harmless.
#
# Usage: auto_finalize.sh   (normally launched via tmux, see status/plan.md)
set -u

CAMP=/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m
REPO=/root/autodl-tmp/SEU-SRTP
LOG="${CAMP}/status/auto_finalize.log"

log() { echo "$(date -Is) $*" | tee -a "${LOG}"; }

# Snapshot times (local). The last entry is the real freeze: it additionally runs
# the inference-only probes, which need the training runs to have stopped or at
# least quieted down. Everything before it is cheap insurance.
SNAPSHOTS=(
  "2026-10-07 21:00"
  "2026-10-08 00:00"
  "2026-10-08 03:00"
  "2026-10-08 06:00"
  "2026-10-08 08:30"
  "2026-10-08 09:20"   # FINAL -- with probes
)
FINAL="2026-10-08 09:20"

cd "${CAMP}" || exit 1
log "auto_finalize started; ${#SNAPSHOTS[@]} snapshots scheduled, final at ${FINAL}"

for slot in "${SNAPSHOTS[@]}"; do
    # Sleep until the slot. Both timestamps are "YYYY-MM-DD HH:MM", so bash's
    # string comparison is chronological. Polling once a minute means a clock
    # adjustment or a briefly-killed tmux cannot leave us sleeping forever.
    #
    # If we are starting late, an already-passed *intermediate* snapshot is
    # pointless (the next one supersedes it) so it is skipped; the FINAL slot is
    # always honoured, because a late freeze is still the deliverable.
    if [ "${slot}" != "${FINAL}" ]; then
        now_epoch=$(date -d "$(date '+%Y-%m-%d %H:%M')" +%s)
        slot_epoch=$(date -d "${slot}" +%s)
        if [ $(( now_epoch - slot_epoch )) -gt 10800 ]; then
            log "skipping stale snapshot ${slot} (more than 3h past)"
            continue
        fi
    fi

    while :; do
        now=$(date '+%Y-%m-%d %H:%M')
        if [ "${now}" \> "${slot}" ] || [ "${now}" = "${slot}" ]; then
            break
        fi
        sleep 60
    done

    if [ "${slot}" = "${FINAL}" ]; then
        log "FINAL freeze at ${slot} (with probes)"
        bash scripts/freeze.sh --with-probes >> "${LOG}" 2>&1
    else
        log "snapshot freeze at ${slot}"
        bash scripts/freeze.sh >> "${LOG}" 2>&1
    fi

    # Record what every lane actually reached, so a time-censored run can never be
    # mistaken for a complete one after the fact.
    {
        echo "### snapshot ${slot}"
        /root/miniconda3/envs/jsbsim/bin/python scripts/watch_f6m.py 2>&1 | sed -n '1,40p'
        echo
    } >> "${CAMP}/status/final_state_history.md"

    log "snapshot ${slot} done; HEAD=$(git -C ${REPO} rev-parse --short HEAD)"
done

log "auto_finalize complete -- campaign frozen"
