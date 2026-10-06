#!/usr/bin/env bash
# Sequential job queue for one GPU.
#
# Why: GPU count (3) << number of experiments, and the real bottleneck is the
# CPU-side JSBSim rollout anyway. Each GPU runs one long-lived tmux session that
# walks its queue. A per-job wall-clock cap (`RUN_TIME_LIMIT`) guarantees a slow
# scale cannot starve the later jobs; checkpoints are saved every episode so a
# timeout costs at most the in-flight episode.
#
# Queue line format (pipe separated, '#' comments and blank lines ignored):
#   name|n_threads|num_env_steps|time_limit_sec|env_name|scenario|algo|seed|extra
#
# Usage: run_queue.sh <gpu_id> <queue_file>
set -u

GPU_ID=${1:?gpu id}
QUEUE=${2:?queue file}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS="${SCRIPT_DIR}/../status/queue_$(basename "${QUEUE}" .txt).status"
REPO=/root/autodl-tmp/SEU-SRTP

mkdir -p "$(dirname "${STATUS}")"

echo "queue started gpu=${GPU_ID} at $(date -Is)" >> "${STATUS}"

while IFS='|' read -r name threads steps tlimit env scenario algo seed extra; do
    # strip surrounding whitespace; skip comments / blanks
    name="$(echo "$name" | xargs)"
    [ -z "${name}" ] && continue
    case "${name}" in \#*) continue ;; esac

    echo ">>> ${name} start $(date -Is) gpu=${GPU_ID} threads=${threads} steps=${steps} limit=${tlimit}s" >> "${STATUS}"
    echo "----------------------------------------------------------------"
    echo "QUEUE gpu${GPU_ID}: starting ${name}  ($(date -Is))"
    echo "----------------------------------------------------------------"

    RUN_TIME_LIMIT="${tlimit}" \
    RUN_LOG_DIR="${SCRIPT_DIR}/../logs" \
        bash "${SCRIPT_DIR}/run_train.sh" \
            "${GPU_ID}" "${env}" "${scenario}" "${algo}" "${name}" "${seed}" \
            "${threads}" "${steps}" ${extra}
    rc=$?

    echo "<<< ${name} end $(date -Is) rc=${rc}" >> "${STATUS}"
    echo "QUEUE gpu${GPU_ID}: ${name} finished rc=${rc}"
done < "${QUEUE}"

echo "queue drained gpu=${GPU_ID} at $(date -Is)" >> "${STATUS}"
echo "QUEUE gpu${GPU_ID}: drained."
