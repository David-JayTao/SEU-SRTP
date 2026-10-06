#!/usr/bin/env python
"""Build the scaling comparison table required by the brief (section 20).

Emits metrics/scaling_table.csv (machine readable) and a markdown rendering on
stdout, with one row per (scale, variant, seed) that has real data.

Every column is either measured or derived from the code-review-verified
formulas; nothing here is asserted from expectation.
  obs_dim          = 12N + 3        (NoWeapon)      / 12N + 9 (Shoot)
  share_obs_dim    = 2N * obs_dim
  actor_params     = measured from the real PPOActor
  critic_params    = measured from the real PPOCritic
    -- all four of these come from metrics/critic_scaling.json, written by
       scripts/critic_scaling_probe.py (pure model construction on the real
       networks; no training).  The probe is run automatically whenever the
       existing JSON does not cover a team size the scaling runs need.
  FPS / steps / rewards / losses   from logs + metrics.jsonl
  CPU / RAM / VRAM  from system_samples.csv during the run.  cpu_busy_pct is
    quota-normalised in the formal-6M sampler (its header carries train_cpu_pct)
    and host-normalised in the pilot sampler, so the cores multiplier is chosen
    from the sampler schema and the quota is read from /sys/fs/cgroup/cpu.max --
    never hardcoded.  Emitted as peak_busy_cores_of_<quota>_quota and
    peak_cpu_pct_of_quota.

Partial runs are fine: summary.csv is rebuilt from on-disk artefacts, and every
column a young run has not produced yet is simply left empty.

The campaign root is DERIVED FROM THIS FILE'S LOCATION
(<campaign>/scripts/scaling_table.py -> parents[1] = <campaign>), so the same
script targets whichever campaign it is copied into. Explicit overrides for
cross-campaign comparisons (point the READS at the foreign campaign and the
writes back home, so the foreign campaign stays untouched):
    --campaign-root DIR / CAMPAIGN_ROOT   campaign that is read
    --out-dir DIR       / OUT_DIR         where scaling_table.csv goes
                                          (default: <campaign-root>/metrics)
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_CAMPAIGN = Path(__file__).resolve().parents[1]

# CPU accounting inputs.  The quota (cgroup v2) is the resource CPU-bound jobs
# actually contend for -- on this box "<quota> <period>" = "4800000 100000" =
# 48 cores -- and it is read at run time, never hardcoded.  The probe script is
# the sibling copy in this campaign's scripts/ directory.
CGROUP_CPU_MAX = Path("/sys/fs/cgroup/cpu.max")
PROBE_SCRIPT = Path(__file__).resolve().parent / "critic_scaling_probe.py"

# Scaling-run names, both campaign generations:
#   pilot 2026-10-04 night : scaling_<N>v<N>_<variant>[_s<seed>]
#   formal 6M campaign     : f6m_<N>v<N>_<variant>_s<seed>
# "official_*" anchor runs are deliberately NOT matched here -- this matches
# the pilot output schema, where the official anchors are their own series in
# normalized_scaling.py.
SCALING_RE = re.compile(
    r"^(?:scaling_|f6m_)(?P<n>\d+)v\d+_(?P<variant>noweapon|shoot)(?:_s(?P<seed>\d))?$")


def resolve_paths(argv=None):
    """(campaign read, metrics dir written).

    --campaign-root / $CAMPAIGN_ROOT selects the campaign that is read;
    --out-dir / $OUT_DIR selects where outputs go (default: that campaign's
    metrics/). Splitting the two is what lets a cross-campaign comparison read
    a foreign campaign without writing anything into it.
    """
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--campaign-root", default=None)
    ap.add_argument("--out-dir", default=None)
    ns, _ = ap.parse_known_args(argv)
    root = ns.campaign_root or os.environ.get("CAMPAIGN_ROOT")
    campaign = Path(root).expanduser().resolve() if root else DEFAULT_CAMPAIGN
    out = ns.out_dir or os.environ.get("OUT_DIR")
    out_dir = Path(out).expanduser().resolve() if out else campaign / "metrics"
    return campaign, out_dir


def read_csv(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_arch(metrics_dir, out_dir=None):
    """(measured, extrapolated) probe tables keyed by team_size.

    Reads metrics/critic_scaling.json from out_dir first (the copy this run just
    ensured) and then from the campaign being read.  The out_dir copy wins per
    team_size, but sizes only the read campaign measured are kept -- that is
    what lets a cross-campaign run reuse the pilot's richer probe file without
    writing anything into the foreign campaign.
    """
    merged_m, merged_e = {}, {}
    dirs = []
    if out_dir is not None and Path(out_dir) != Path(metrics_dir):
        dirs.append(Path(out_dir))
    dirs.append(Path(metrics_dir))
    for d in dirs:
        p = d / "critic_scaling.json"
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        for m in data.get("measured", []):
            merged_m.setdefault(m.get("team_size"), m)
        for e in data.get("extrapolated", []):
            merged_e.setdefault(e.get("team_size"), e)
    return merged_m, merged_e


def load_resources(campaign):
    """(header, rows) of system/system_samples.csv.

    The header is returned even for a file with no data rows yet, because the
    column set identifies the sampler generation (see cpu_peaks).
    """
    p = campaign / "system" / "system_samples.csv"
    if not os.path.exists(p):
        return [], []
    with open(p, newline="") as f:
        r = csv.reader(f)
        header = next(r, [])
        return header, [dict(zip(header, row)) for row in r]


def read_quota_cores():
    """Cores this cgroup may spend, from cgroup-v2 /sys/fs/cgroup/cpu.max.

    The file holds "<quota_us> <period_us>" ("max" when unlimited), e.g.
    "4800000 100000" -> 48 cores.  Returns None when unavailable so callers can
    fall back to the host CPU count instead of guessing.
    """
    try:
        quota, period = CGROUP_CPU_MAX.read_text().split()
        if quota != "max" and float(period) > 0:
            return float(quota) / float(period)
    except (OSError, ValueError):
        pass
    return None


def read_host_cores():
    """Logical CPUs the /proc/stat aggregate line averages over.

    Both sampler generations derive cpu_busy_pct from that aggregate, so this --
    not os.cpu_count() -- is the denominator those percentages mean.
    """
    try:
        with open("/proc/stat") as f:
            n = sum(1 for line in f if re.match(r"cpu\d", line))
        if n:
            return float(n)
    except OSError:
        pass
    return float(os.cpu_count() or 1)


def cpu_peaks(header, rows, quota):
    """(peak pct of quota, peak busy cores of quota, source label).

    Two sampler schemas write cpu_busy_pct with different denominators, and the
    cores multiplier must follow the schema or the column is nonsense:
      * formal 6M os_watchdog.sh -- header carries train_cpu_pct, and
        cpu_busy_pct is ALREADY a % of the cgroup quota: cores = pct*quota/100.
      * pilot monitor.sh -- no train_cpu_pct; cpu_busy_pct is a % of the host's
        logical CPUs (/proc/stat aggregate), so rescale it to the quota first
        (host_cores/quota_cores, the same factor os_watchdog.sh applies in
        reverse); net effect for the cores column: pct * host_cores/100, i.e.
        exactly the pilot's old 1.92 multiplier for that schema.
    Returns (None, None, None) when no usable samples exist.
    """
    vals = [fnum(r.get("cpu_busy_pct")) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None, None
    if "train_cpu_pct" in header:
        pct = max(vals)                                   # already % of quota
        src = "formal-6M sampler (quota-normalised)"
    else:
        pct = max(vals) * read_host_cores() / quota       # host-% -> quota-%
        src = "pilot sampler (host-normalised, rescaled to quota)"
    return pct, pct * quota / 100.0, src


def arch_sizes(path):
    """Team sizes a critic_scaling.json can serve (measured + extrapolated)."""
    try:
        with open(path) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return set()
    return {m.get("team_size")
            for k in ("measured", "extrapolated") for m in d.get(k, [])}


def ensure_critic_scaling(needed, campaign, out_dir):
    """Make sure out_dir/critic_scaling.json covers every needed team size.

    The representation columns are measured by scripts/critic_scaling_probe.py,
    which builds the real PPOActor/PPOCritic and counts parameters -- pure model
    construction, no training.  Reuse an existing probe file whenever the read
    campaign or out_dir already covers all needed sizes; regenerate into out_dir
    otherwise (a foreign campaign is only ever read, never written).  Failures
    are loud on stderr but non-fatal: the table is still emitted with whatever
    the JSON files provide.
    """
    if not needed:
        return
    local = Path(out_dir) / "critic_scaling.json"
    foreign = Path(campaign).resolve() / "metrics" / "critic_scaling.json"
    if needed <= arch_sizes(local):
        return
    if foreign != local and needed <= arch_sizes(foreign):
        return
    if not PROBE_SCRIPT.exists():
        print(f"[scaling_table] WARNING: {PROBE_SCRIPT} missing; representation "
              f"columns may stay empty", file=sys.stderr)
        return
    local.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(PROBE_SCRIPT), "--out", str(local),
           "--n", *[str(n) for n in sorted(needed)]]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(PROBE_SCRIPT.parent), timeout=240)
    except (OSError, subprocess.SubprocessError) as e:    # includes TimeoutExpired
        print(f"[scaling_table] WARNING: critic_scaling_probe.py failed to run: {e}",
              file=sys.stderr)
        return
    if proc.returncode != 0:
        print(f"[scaling_table] WARNING: critic_scaling_probe.py exited "
              f"{proc.returncode}; stderr tail:\n{proc.stderr.strip()[-1500:]}",
              file=sys.stderr)
        return
    print(f"[scaling_table] critic_scaling_probe.py N={sorted(needed)} -> {local} "
          f"in {time.time() - t0:.1f}s", file=sys.stderr)


def has_nan(metrics_dir, exp):
    """A NaN in the run would show up as a nan reward or a pdb.set_trace hang;
    the assert in env_base._pack would abort the run. Report from the curve."""
    p = os.path.join(metrics_dir, "curves", f"{exp}.csv")
    for r in read_csv(p):
        for k in ("average_episode_rewards", "value_loss", "critic_grad_norm"):
            v = r.get(k, "")
            if v and v.lower() == "nan":
                return "yes"
    return "no"


def main(argv=None):
    campaign, out_dir = resolve_paths(argv)
    metrics = campaign / "metrics"
    summary = read_csv(metrics / "summary.csv")

    # Representation columns: make sure the probe measurement exists for every
    # team size a scaling row needs, then read it (out_dir first, campaign second).
    needed = set()
    for s in summary:
        m = SCALING_RE.match(s.get("experiment", ""))
        if m:
            needed.add(int(m.group("n")))
    ensure_critic_scaling(needed, campaign, out_dir)
    meas, ext = load_arch(metrics, out_dir)

    res_header, res = load_resources(campaign)
    quota = read_quota_cores() or read_host_cores()
    peak_vram = 0
    for c in ("gpu0_mem_mb", "gpu1_mem_mb", "gpu2_mem_mb"):
        for r in res:
            peak_vram = max(peak_vram, fnum(r.get(c)) or 0)
    peak_ram = max((fnum(r.get("mem_used_gb")) or 0 for r in res), default=0)
    peak_pct, peak_cores, cpu_src = cpu_peaks(res_header, res, quota)
    # Column name carries the quota it is measured against (48 on this box), so
    # the number can never again be read as "cores on the 192-core host".
    cpu_cores_col = f"peak_busy_cores_of_{quota:g}_quota"

    rows = []
    for s in summary:
        e = s["experiment"]
        m = SCALING_RE.match(e)
        if not m:
            continue
        n = int(m.group("n"))
        variant = m.group("variant")
        a = meas.get(n) or ext.get(n) or {}
        obs_dim = a.get("obs_dim")
        share_dim = a.get("share_obs_dim")
        if variant == "shoot" and obs_dim is not None:
            obs_dim = 12 * n + 9
            share_dim = 2 * n * obs_dim
        fps = fnum(s.get("fps_last"))
        thr = fnum(s.get("n_rollout_threads"))
        # Wall-clock normalisations. FPS counts *individual* env-steps/s summed
        # over the rollout threads, so:
        #   seconds per vectorised rollout step = threads / FPS
        #   agent-steps/s = FPS * total_agents
        # Thread counts differ between scales (they were sized to the measured
        # cost), so the per-thread figure is the only fair cross-scale one.
        rows.append({
            "scale": f"{n}v{n}",
            "variant": variant,
            "team_size": n,
            "total_agents": 2 * n,
            "local_obs_dim": obs_dim,
            "share_obs_dim": share_dim,
            "actor_params": a.get("actor_params"),
            "critic_params": a.get("critic_params"),
            "n_rollout_threads": s.get("n_rollout_threads"),
            "seed": s.get("seed"),
            "fps": s.get("fps_last"),
            "sec_per_vectorised_step": (round(thr / fps, 5) if (fps and thr) else None),
            "sec_per_rollout_episode": (round(3000 * thr / fps, 1) if (fps and thr) else None),
            "agent_steps_per_s": (round(fps * 2 * n, 1) if fps else None),
            "agent_steps_per_s_per_thread": (round(fps * 2 * n / thr, 1) if (fps and thr) else None),
            "env_steps": s.get("steps_done"),
            "episodes_logged": s.get("episodes_logged"),
            "train_reward_last": s.get("train_reward_last"),
            "train_reward_first": s.get("train_reward_first"),
            "train_reward_tail_slope": s.get("train_reward_tail_slope"),
            "eval_reward_last": s.get("eval_reward_last"),
            "critic_loss_value": s.get("value_loss_last"),
            "policy_loss": s.get("policy_loss_last"),
            "entropy_loss": s.get("entropy_loss_last"),
            "critic_grad_norm": s.get("critic_grad_norm_last"),
            "actor_grad_norm": s.get("actor_grad_norm_last"),
            "ratio": s.get("ratio_last"),
            "nan_observed": has_nan(metrics, e),
            cpu_cores_col: ("" if peak_cores is None else round(peak_cores, 1)),
            "peak_cpu_pct_of_quota": ("" if peak_pct is None else round(peak_pct, 1)),
            "peak_ram_gb_host": round(peak_ram, 1),
            "peak_vram_mb_host": round(peak_vram),
            "checkpoint": s.get("checkpoint_path"),
        })

    rows.sort(key=lambda r: (r["variant"], r["team_size"], str(r["seed"])))
    out = out_dir / "scaling_table.csv"
    if rows:
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out} ({len(rows)} rows)\n")

    hdr = ["scale", "variant", "agents", "obs", "share_obs", "actor_p",
           "critic_p", "thr", "seed", "FPS", "s/vec-step", "s/rollout-ep",
           "agent-steps/s", "ag-steps/s/thr", "steps", "eps", "rew_first",
           "rew_last", "slope", "eval_rew", "value_loss", "critic_gn",
           "entropy", "NaN?", "learnable?"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in rows:
        def g(k, nd=3):
            v = r.get(k)
            if v is None or v == "":
                return "-"
            try:
                return f"{float(v):.{nd}g}"
            except (TypeError, ValueError):
                return str(v)
        slope = fnum(r["train_reward_tail_slope"])
        learning = "improving" if (slope or 0) > 0.05 else ("flat/declining" if slope is not None else "?")
        print("| " + " | ".join([
            r["scale"], r["variant"], str(r["total_agents"]), str(r["local_obs_dim"]),
            str(r["share_obs_dim"]), str(r["actor_params"]), str(r["critic_params"]),
            str(r["n_rollout_threads"]), str(r["seed"]), g("fps"),
            g("sec_per_vectorised_step", 3), g("sec_per_rollout_episode", 4),
            g("agent_steps_per_s", 4), g("agent_steps_per_s_per_thread", 3),
            str(r["env_steps"]),
            str(r["episodes_logged"]), g("train_reward_first"), g("train_reward_last"),
            ("-" if slope is None else f"{slope:+.3g}"), g("eval_reward_last"),
            g("critic_loss_value"), g("critic_grad_norm"), g("entropy_loss"),
            r["nan_observed"], learning,
        ]) + " |")
    if peak_cores is None:
        cpu_txt = "CPU n/a (no usable system_samples rows yet)"
    else:
        cpu_txt = (f"CPU peak {peak_cores:.1f} busy cores of the {quota:g}-core quota "
                   f"({peak_pct:.1f}% of quota; {cpu_src})")
    print(f"\ncampaign peaks so far: {cpu_txt}, RAM {peak_ram:.1f} GB, "
          f"VRAM {peak_vram:.0f} MB (single job uses <1.5 GB)")


if __name__ == "__main__":
    main()
