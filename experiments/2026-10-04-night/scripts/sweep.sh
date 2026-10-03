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

# Per-experiment resource sample. /proc only; rollout workers rename themselves
# via setproctitle, so both the argparse line and the title form are matched.
python3 - <<'PYEOF'
import csv, os, re, subprocess, time, collections

EXP = "/root/autodl-tmp/SEU-SRTP/experiments/2026-10-04-night"
OUT = os.path.join(EXP, "metrics/resources.csv")
gpus = {}
try:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used",
         "--format=csv,noheader,nounits"], text=True)
    for line in out.strip().splitlines():
        i, u, m = [x.strip() for x in line.split(",")]
        gpus[int(i)] = (float(u), float(m))
except Exception:
    pass

# experiment -> gpu from the queue definitions
exp_gpu = {}
for qf in os.listdir(os.path.join(EXP, "configs")):
    if not qf.startswith("queue_"):
        continue
    g = {"queue_gpu0.txt": 0, "queue_extra.txt": 0, "queue_gpu1.txt": 1,
         "queue_seeds.txt": 1, "queue_gpu2.txt": 2}.get(qf, "")
    for line in open(os.path.join(EXP, "configs", qf)):
        line = line.strip()
        if line and not line.startswith("#"):
            exp_gpu[line.split("|")[0]] = g

pat = re.compile(r"--experiment-name (\S+)")
title = re.compile(r"^(?:ppo|mappo)-[^-]+-(.+)@[^@]*$")
agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
clock = os.sysconf("SC_CLK_TCK")
uptime = float(open("/proc/uptime").read().split()[0])
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
        m = pat.search(cmd) or title.match(cmd.strip())
        if not m:
            continue
        e = m.group(1)
        st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        u, s, stt, rss = int(st[11]), int(st[12]), int(st[19]), int(st[21])
        agg[e][0] += 1
        agg[e][1] += 100.0 * (u + s) / clock / max(uptime - stt / clock, 1e-6)
        agg[e][2] += rss * 4096
    except (OSError, IndexError, ValueError):
        continue

new = not os.path.exists(OUT)
with open(OUT, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["timestamp", "experiment", "n_procs", "cpu_pct", "rss_gb",
                    "gpu_id", "gpu_util", "gpu_vram_mb"])
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    for e, (n, cpu, rss) in sorted(agg.items()):
        g = exp_gpu.get(e, "")
        gu, gm = gpus.get(g, ("", "")) if g != "" else ("", "")
        w.writerow([ts, e, n, round(cpu, 1), round(rss / 1024**3, 3), g, gu, gm])
print(f"resource sample: {len(agg)} experiments -> {OUT}")
PYEOF

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
