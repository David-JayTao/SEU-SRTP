#!/usr/bin/env bash
# Regenerate experiments/2026-10-04-night/status/running_jobs.md from live state.
# Safe to run at any time; it only reads.
set -u

REPO=/root/autodl-tmp/SEU-SRTP
EXPDIR="${REPO}/experiments/2026-10-04-night"
OUT="${EXPDIR}/status/running_jobs.md"

{
echo "# Running Jobs Snapshot"
echo
echo "Generated: $(date -Is)"
echo
echo "## tmux sessions"
echo
echo '```'
tmux ls 2>&1
echo '```'
echo
echo "## Queue states"
echo
for f in "${EXPDIR}"/status/queue_*.status; do
    [ -e "$f" ] || continue
    echo "### $(basename "$f" .status)"
    echo '```'
    tail -6 "$f"
    echo '```'
done
echo
echo "## Live training processes (aggregated per experiment)"
echo
echo "| experiment | n_procs | total_cpu_pct | total_rss_gb |"
echo "|---|---|---|---|"
python3 - <<'PYEOF'
import os, re, collections
# Rollout workers rename themselves via setproctitle to
#   "<algo>-<env>-<experiment>@<user>"
# while the parent keeps the argparse command line, so match both.
pat = re.compile(r"--experiment-name (\S+)")
title = re.compile(r"^(?:ppo|mappo)-[^-]+-(.+)@[^@]*$")
agg = collections.defaultdict(lambda: [0, 0.0, 0])
clock = os.sysconf("SC_CLK_TCK")
uptime = float(open("/proc/uptime").read().split()[0])
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().replace(b"\0", b" ").decode(errors="replace")
        m = pat.search(cmd) or title.match(cmd.strip())
        if not m:
            continue
        exp = m.group(1)
        st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        utime, stime, starttime, rss_pages = int(st[11]), int(st[12]), int(st[19]), int(st[21])
        cpu = 100.0 * (utime + stime) / clock / max(uptime - starttime / clock, 1e-6)
        agg[exp][0] += 1
        agg[exp][1] += cpu
        agg[exp][2] += rss_pages * 4096
    except (OSError, IndexError, ValueError):
        continue
for exp in sorted(agg):
    n, cpu, rss = agg[exp]
    print(f"| {exp} | {n} | {cpu:.0f}% | {rss/1024**3:.2f} |")
PYEOF
echo
echo "## Progress (from logs)"
echo
echo "| experiment | steps | target | FPS | train reward | eval reward |"
echo "|---|---|---|---|---|---|"
for f in "${EXPDIR}"/logs/*_seed*_gpu*.log; do
    [ -e "$f" ] || continue
    n=$(basename "$f" | sed 's/_seed.*//')
    line=$(grep -E "updates " "$f" 2>/dev/null | tail -1)
    [ -z "$line" ] && continue
    steps=$(echo "$line" | sed -n 's/.*timesteps \([0-9]*\)\/.*/\1/p')
    tot=$(echo "$line" | sed -n 's/.*timesteps [0-9]*\/\([0-9]*\),.*/\1/p')
    fps=$(echo "$line" | sed -n 's/.*FPS \([0-9.]*\).*/\1/p')
    rew=$(grep "average episode rewards is" "$f" | tail -1 | sed 's/.*is //')
    ev=$(grep "eval average episode rewards:" "$f" | tail -1 | sed 's/.*rewards: //')
    printf "| %s | %s | %s | %s | %s | %s |\n" "$n" "$steps" "$tot" "$fps" "${rew:--}" "${ev:--}"
done
echo
echo "## GPUs"
echo
echo '```'
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,temperature.gpu --format=csv
echo '```'
echo
echo "## Last system samples"
echo
echo '```'
tail -5 "${EXPDIR}/system/system_samples.csv" 2>/dev/null
echo '```'
} > "${OUT}"

echo "wrote ${OUT}"
