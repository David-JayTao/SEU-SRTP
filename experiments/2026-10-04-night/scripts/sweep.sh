#!/usr/bin/env bash
# One monitoring sweep: refresh every derived artefact and report health.
# Read-only with respect to the training runs -- it never touches a job.
set -u

REPO=/root/autodl-tmp/SEU-SRTP
EXP="${REPO}/experiments/2026-10-04-night"
CONDA=/root/miniconda3

source ${CONDA}/etc/profile.d/conda.sh
conda activate jsbsim
cd "${REPO}"

echo "================================================================"
echo "SWEEP $(date -Is)"
echo "================================================================"

python experiments/2026-10-04-night/scripts/collect_metrics.py 2>&1 | head -20
python experiments/2026-10-04-night/scripts/make_manifest.py 2>&1 | head -30
python experiments/2026-10-04-night/scripts/normalized_scaling.py 2>&1 | tail -14
python experiments/2026-10-04-night/scripts/make_figures.py 2>&1 | grep -E "wrote|Error"
bash experiments/2026-10-04-night/scripts/snapshot_status.sh >/dev/null

echo
echo "--- health ---"
CRASH=$(grep -l "Traceback" "${EXP}"/logs/*.log 2>/dev/null | wc -l)
echo "logs_with_traceback: ${CRASH}"
echo "tmux_sessions: $(tmux ls 2>/dev/null | wc -l)"
echo "live_train_procs: $(pgrep -fc train_jsbsim.py || echo 0)"
echo "load: $(cut -d' ' -f1-3 /proc/loadavg)"
echo "disk_autodl_tmp: $(df -h /root/autodl-tmp | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
echo "mem: $(free -g | awk '/Mem:/{print $3"/"$2" GB"}')"
echo
echo "--- queue ledgers ---"
for f in "${EXP}"/status/queue_*.status; do
    [ -e "$f" ] || continue
    echo "[$(basename "$f" .status)] started=$(grep -c '^>>>' "$f") finished=$(grep -c '^<<<' "$f")"
    tail -1 "$f"
done
echo
echo "--- progress ---"
for f in "${EXP}"/logs/*_seed*_gpu*.log; do
    [ -e "$f" ] || continue
    n=$(basename "$f" | sed 's/_seed.*//')
    line=$(grep -E "updates " "$f" 2>/dev/null | tail -1)
    [ -z "$line" ] && { echo "  ${n}: (first episode in progress)"; continue; }
    echo "  ${n}: $(echo "$line" | sed 's/.*updates /ep /; s/ episodes.*timesteps / steps=/; s/, FPS/ FPS=/')"
done
echo "SWEEP-END $(date -Is)"
