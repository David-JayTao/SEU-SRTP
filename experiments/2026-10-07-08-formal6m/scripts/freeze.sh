#!/usr/bin/env bash
# End-of-campaign freeze: snapshot state, regenerate every derived artefact, commit.
#
# Deliberately idempotent and non-fatal: a failing analysis step must not stop the
# rest of the freeze, because the alternative is a report with stale numbers.
# Every step's output is kept under status/freeze_logs/ so a failure is visible
# afterwards rather than swallowed.
#
# Usage:
#   bash scripts/freeze.sh                 # snapshot + regenerate + commit
#   bash scripts/freeze.sh --with-probes   # additionally run the expensive
#                                          # inference-only probes (offline_eval,
#                                          # env_bench, obs_cost_profile)
#   bash scripts/freeze.sh --no-commit
set -u

CAMP=/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m
REPO=/root/autodl-tmp/SEU-SRTP
PY=/root/miniconda3/envs/jsbsim/bin/python
LOGS="${CAMP}/status/freeze_logs"
mkdir -p "${LOGS}"

WITH_PROBES=0
COMMIT=1
for a in "$@"; do
    case "$a" in
        --with-probes) WITH_PROBES=1 ;;
        --no-commit)   COMMIT=0 ;;
    esac
done

cd "${CAMP}" || exit 1
STAMP=$(date +%Y%m%d_%H%M%S)
echo "=== freeze started $(date -Is) ==="

# ---------------------------------------------------------------- 1. snapshot
{
    echo "# Freeze snapshot ${STAMP}"
    date -Is
    echo
    echo "## running processes"
    tmux ls 2>&1
    echo
    ps -eo pid,etime,pcpu,args --no-headers 2>/dev/null \
        | grep -E -- "-MultipleCombat-|-SingleCombat-|-SingleControl-" | head -80
} > "${LOGS}/processes_${STAMP}.txt" 2>&1

# Final per-job ledger row: steps, FPS, run dir, whether the target was reached.
"${PY}" "${CAMP}/scripts/watch_f6m.py" > "${LOGS}/monitor_${STAMP}.txt" 2>&1

# ------------------------------------------------- 2. the derived-artefact sweep
declare -A STEP_STATE
run_step () {
    local name="$1"; shift
    if timeout 900 "$@" > "${LOGS}/${name}_${STAMP}.txt" 2>&1; then
        STEP_STATE[$name]=ok
        printf '  %-22s ok\n' "$name"
    else
        STEP_STATE[$name]="FAILED($?)"
        printf '  %-22s FAILED -- see status/freeze_logs/%s_%s.txt\n' "$name" "$name" "$STAMP"
    fi
}

echo "--- regeneration sweep"
run_step collect_metrics   "${PY}" scripts/collect_metrics.py
run_step make_manifest     "${PY}" scripts/make_manifest.py
# NOTE the absolute --out: critic_scaling_probe.py does os.chdir(REPO) at import
# time, so a relative path resolves against the repo root, not the invocation cwd,
# and the probe prints its whole table before dying on the write (incident F15).
run_step critic_probe      "${PY}" scripts/critic_scaling_probe.py \
                               --out "${CAMP}/metrics/critic_scaling.json"
run_step scaling_table     "${PY}" scripts/scaling_table.py
run_step normalized        "${PY}" scripts/normalized_scaling.py
run_step sample_efficiency "${PY}" scripts/sample_efficiency.py
run_step equal_sample      "${PY}" scripts/equal_sample.py
run_step equal_wallclock   "${PY}" scripts/equal_wallclock.py
run_step figures           "${PY}" scripts/make_figures.py
run_step report_tables     "${PY}" scripts/make_report_tables.py
# Self-filling report: rewrites the AUTO-marked regions of
# docs/formal_repro_scaling_2026-10-07_08.md (§5-§8, §11, §12, §17) from the
# CSVs regenerated above. Runs after watch_f6m.py (section 1), whose fresh
# metrics/status.json supplies live steps/reward for lanes still training, so
# this works whether a human agent is awake or only auto_finalize.sh is.
run_step fill_report       "${PY}" scripts/fill_report.py
# The unattended safety net: regenerates docs/formal_repro_scaling_auto_results.md
# from the freshly collected metrics, so the numeric record exists even if the
# hand-written report is never finished. Deliberately LAST: it reads the outputs
# of all the steps above.
run_step auto_results      "${PY}" scripts/make_auto_results.py

# ------------------------------------- 3. inference-only probes (optional, slow)
# These need the training runs to have stopped, or at least to be quiet, otherwise
# their timings measure contention rather than intrinsic cost.
if [ "${WITH_PROBES}" = "1" ]; then
    echo "--- inference-only probes (single core, taskset-pinned)"
    # offline_eval per live scaling lane: gives mean_return/std/mean_episode_length
    # on the FINAL checkpoint. mean_episode_length is the one that matters -- it
    # tests whether per-episode reward is comparable across N (see status/plan.md).
    for exp in f6m_2v2_noweapon_s0 f6m_3v3_noweapon_s0 f6m_5v5_noweapon_s0 f6m_10v10_noweapon_s0; do
        d=$(find "${REPO}/scripts/results" -type d -name "${exp}" 2>/dev/null | head -1)
        [ -z "$d" ] && continue
        run_step "offline_eval_${exp}" \
            taskset -c 0,1 "${PY}" scripts/offline_eval.py --run-dir "${d}/run1" \
            --episodes 8 --threads 2
    done
    run_step env_bench        taskset -c 0 "${PY}" scripts/env_bench.py
    run_step obs_cost_profile taskset -c 0 "${PY}" scripts/obs_cost_profile.py
fi

# ------------------------------------------------------------------- 4. report
{
    echo "# Freeze ${STAMP} — step outcomes"
    echo
    for k in "${!STEP_STATE[@]}"; do echo "- ${k}: ${STEP_STATE[$k]}"; done | sort
    echo
    echo "## final per-job state"
    cat "${LOGS}/monitor_${STAMP}.txt"
} > "${CAMP}/status/freeze_summary.md"

echo "--- wrote status/freeze_summary.md"

# ------------------------------------------------------------------ 5. commit
if [ "${COMMIT}" = "1" ]; then
    cd "${REPO}" || exit 1
    git add -A "experiments/2026-10-07-08-formal6m" "docs/formal_repro_scaling_2026-10-07_08.md" "docs/formal_repro_scaling_auto_results.md"
    if git diff --cached --quiet; then
        echo "--- nothing to commit"
    else
        git commit -q -m "docs: freeze formal-6M campaign artefacts (${STAMP})

Regenerated every derived artefact from the frozen run outputs: metrics CSVs,
the equal-sample and equal-wall-clock tables, figures, report tables and the
representation-scaling probe.

Step outcomes are recorded in status/freeze_summary.md; any step that failed is
named there rather than silently omitted.

Co-Authored-By: Claude Code <noreply@anthropic.com>"
        echo "--- committed $(git rev-parse --short HEAD)"
    fi
fi

echo "=== freeze finished $(date -Is) ==="
