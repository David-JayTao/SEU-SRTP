# Incidents — formal 6M campaign

Continues the `docs/night_failures.md` F1–F9 series. Category vocabulary is the
same and is held strictly: `Code scalability` / `Computational scalability` /
`Representation scalability` / `Sample scalability` / `Algorithmic scalability` /
`Coordination scalability` / `Other`.

**Rule inherited from the pilot:** an instrumentation or engineering defect is
never evidence about the algorithm. Nothing below may be cited in support of a
curse-of-multiagency claim.

---

## F10 — CPU-cores column reported a physically impossible value

- **Category**: `Other` (measurement bug)
- **Detected**: 2026-10-07, while reviewing the first `metrics/scaling_table.csv`
- **Symptom**: `peak_cpu_cores_host = 175.9` on every row of a 48-core box.
- **Cause**: `os_watchdog.sh` writes `cpu_busy_pct` **already normalised to the
  48-core cgroup quota**, but `scaling_table.py` multiplied it by `192/100` — the
  constant right for the *pilot's* `monitor.sh`, which normalised against the
  host's 192 logical CPUs. Two samplers, two denominators, one column name.
- **Fix**: derive the multiplier from `/sys/fs/cgroup/cpu.max` at runtime
  (`4800000 100000` → 48), detect the sampler schema from the CSV header
  (`train_cpu_pct` present ⇒ quota-normalised), and **rename the output column to
  `peak_busy_cores_of_48_quota`** with a companion `peak_cpu_pct_of_quota`.
- **Verification**: after the fix the value is 46.8 busy cores of 48 (97.6% of
  quota at peak), consistent with `load1 ≈ 44` and the raw sampler rows. The
  legacy pilot schema still reconstructs its historical 65.3 exactly.
- **Semantic impact**: none — analysis only, no training code touched.
- **Why it is worth recording**: it is a scaled-looking number (175.9 at N=10)
  that was a unit error. Exactly the failure mode the pilot warned about.

---

## F11 — Representational-scalability columns were silently empty

- **Category**: `Other` (missing instrumentation)
- **Detected**: 2026-10-07, same review
- **Symptom**: `local_obs_dim`, `share_obs_dim`, `actor_params`, `critic_params`
  were blank in `scaling_table.csv`, and `metrics/critic_scaling.json` did not exist.
- **Cause**: `critic_scaling_probe.py` existed and worked, but nothing invoked it.
  The measurement method was present; only the call was missing.
- **Fix**: `scaling_table.py` now derives the required team sizes from
  `summary.csv`, runs the probe via subprocess (~7 s, 240 s cap, cached so repeat
  sweeps skip it) and merges the result.
- **Verification**: the N = 2/3/5/10 values are **bit-identical to the ones the
  2026-10-04 pilot measured independently** —
  (27, 108, 154891, 163969), (39, 234, 156427, 180097),
  (63, 630, 159499, 230785), (123, 2460, 167179, 465025) — and the emitted JSON
  has the same key set as the pilot's. Section 10 of the report rests on this.
- **Semantic impact**: none.

---

## F12 — Finished lanes were reported as still running

- **Category**: `Other` (instrumentation bug, inherited from the pilot)
- **Symptom**: `make_manifest.py` never registered a lane as finished.
- **Cause**: the regex `<<< (\S+) end rc=(\d+)` does not match the ledger's actual
  line format, `<<< <name> end <ISO-timestamp> rc=<N>`.
- **Fix**: `<<< (\S+) end\b.*?\brc=(-?\d+)`.
- **Verification**: a lane that has exited now transitions out of `running`.
- **Semantic impact**: none. Note the `rc` it recovers is itself meaningless
  (see 13.4 of the report — no `pipefail`), so completion is judged from
  `metrics.jsonl` step progress, never from `rc`.

---

## F13 — Analysis scripts hardcoded the pilot's campaign path

- **Category**: `Other` (portability)
- **Symptom**: 11 copied files (7 Python, 4 shell) still pointed at
  `experiments/2026-10-04-night`, so any run in the new campaign would have
  silently produced the *pilot's* numbers.
- **Fix**: each script now derives its campaign root from its own location
  (`Path(__file__).resolve().parents[1]`), with an explicit `--campaign-root` /
  `CAMPAIGN_ROOT` override for cross-campaign reads.
- **Verification**: the pilot tree is untouched
  (`find experiments/2026-10-04-night -newermt 2026-10-05` → empty), and the
  pilot's `summary.csv` regenerates with **zero column mismatches**, i.e. the
  refactor is behaviour-preserving on the campaign it was written for.

---

## F17 — the reachable step budget is quantised by thread count

- **Category**: `Other` (experiment-design trap)
- **Detected**: 2026-10-07 ~17:20, when `f6m_official_1v1_vsbaseline_s1` ended
  cleanly at **5,994,000** instead of 6,000,000 — exactly below target, not short
  by accident.
- **Cause**: the runner computes
  `episodes = num_env_steps // buffer_size // n_rollout_threads`
  (`runner/share_jsbsim_runner.py:72`, `runner/jsbsim_runner.py:41`), so the
  reachable total is `episodes × 3000 × threads`. With `num_env_steps = 6e6` and
  `buffer_size = 3000`, a lane reaches the full budget **only if the thread count
  divides 2000**:

  | threads | episodes | reached | vs 6M |
  |---|---|---|---|
  | 3 | 666 | 5,994,000 | 99.9% |
  | 4 | 500 | 6,000,000 | 100% |
  | 8 | 250 | 6,000,000 | 100% |
  | 10 | 200 | 6,000,000 | 100% |
  | 20 | 100 | 6,000,000 | 100% |

- **Symptom is silent**: no warning, no error, no truncated-run marker. The job
  simply finishes 6,000 steps short and reports `exited with code 0`.
- **Fix**: **not applied retrospectively.** Relaunching to change the thread count
  would create a second `run<N>/` (see 13.4 of the report) and a spliced
  trajectory is not a clean formal run. All four 1v1 lanes use 3 threads and are
  therefore capped at 5,994,000. They are reported as **`completed` at
  5,994,000 (99.9% of the nominal budget)** with the reason stated — **not** as
  `completed_6M`, and not as `time_cutoff` (nothing was cut; the target was
  unreachable by construction).
- **Applied going forward**: every lane launched after this was chosen so that
  its thread count divides 2000 — 5v5 seed 1 at 10 threads (200 episodes), 3v3
  seed 1 at 8 threads (250 episodes).
- **Verification**: 3v3 seed 0 at 8 threads reached exactly 6,000,000; 1v1
  vsBaseline at 3 threads stopped at exactly 666 × 9000 = 5,994,000.
- **Transferable lesson**: when a budget is expressed in units that the harness
  floors, *check divisibility at launch time*. The same trap bit the pilot, whose
  18-thread runs reached 864,000 of a nominal 900,000 and were reported with the
  shortfall unexplained.

---

## F16 — `/proc/stat` is unusable in this container; every CPU figure derived from it was wrong

- **Category**: `Other` (measurement bug — and the most consequential one found)
- **Detected**: 2026-10-07 ~17:21, when adding a lane pushed the reported
  "cores busy" to 65.5 on a box whose quota is 48. A figure above the quota is
  impossible, so the instrument was suspect rather than the load.
- **Symptoms**: the `/proc/stat` `cpu` aggregate, sampled every 4–5 s, returned
  busy deltas alternating between **0.0 cores and ~200 cores** while the
  container was demonstrably busy. 200 ≈ the **host's** 192 logical CPUs, not the
  container's 48. Reported values over the campaign's life ranged up to 124% of
  quota.
- **Cause**: the container's `/proc/stat` exposes host-wide counters (an lxcfs
  style view), while `nproc` reports 48 and `/sys/fs/cgroup/cpu.max` grants 48.
  The three disagree. A naive `busy_ticks / (elapsed × USER_HZ)` therefore
  measures the *host*, not this container.
- **Authoritative source** (now used): the container's own cgroup accounting —
  `/sys/fs/cgroup/cpu.stat` `usage_usec` deltas, with the quota from
  `/sys/fs/cgroup/cpu.max`. By that measure the campaign used **~38–42 of 48
  cores (80–87%)** and `nr_throttled` stayed at **0.02–0.04% of periods**, i.e.
  the CPU quota was **never actually binding**.
- **Fix**:
  - `os_watchdog.sh` now measures from cgroup `cpu.stat` and writes
    `system/system_samples_v2.csv` with columns
    `cpu_busy_pct_of_quota, busy_cores_of_quota, quota_cores, nr_throttled_pct`.
    The v1 file is **kept on disk unaltered as the historical record** but its
    `cpu_busy_pct` column must not be used.
  - `watch_f6m.py` uses the same source and prints
    `container CPU X / 48 cores (Y% of quota, throttled Z% of periods)`.
  - `scaling_table.py` and `make_manifest.py` prefer the v2 file, read
    `busy_cores_of_quota` **directly without rescaling**, and label the source in
    their output (`cgroup cpu.stat (authoritative)`); the legacy path is retained
    only so old files still parse, and is labelled `UNRELIABLE`.
- **Verification**: v1 vs v2 at the same instant — v1 `124.4`, v2 `79.6%` =
  `38.21 / 48` cores. `scaling_table.csv` now reports
  `peak_busy_cores_of_48_quota = 38.2` with the authoritative label.
- **Semantic impact on the experiment**: none — training was unaffected.
  **Semantic impact on the report**: large. Section 9.3's "≈43 of 48 cores,
  saturated" narrative was an artifact, and the claim that adding lanes cost the
  10v10 lane throughput is **not supported** — the quota was never saturated, and
  the observed cumulative-FPS dip is explained by cumulative averaging alone.
  Both were corrected rather than left standing.
- **Transferred lesson**: a derived metric that exceeds its own physical bound
  (cores > quota, utilisation > 100%) is a *unit error*, not a finding. The same
  class of error as F10 — and F10's 175.9 "cores" and this one share a root
  cause: trusting a sampler's denominator instead of checking it against the
  cgroup. Note also that the pilot's `monitor.sh` used the same `/proc/stat`
  method, so the pilot's CPU columns carry the same defect.

---

## F15 — probe `--out` resolves against the repo root, not the invocation cwd

- **Category**: `Other` (portability trap)
- **Detected**: 2026-10-07 05:03, by the first dry-run of `freeze.sh` — the
  non-fatal step runner surfaced it instead of aborting the freeze
- **Symptoms**: `FileNotFoundError: [Errno 2] No such file or directory:
  'metrics/critic_scaling.json'`, raised **after** the probe had printed its
  entire results table. Easy to miss: the table looks like success.
- **Cause**: `critic_scaling_probe.py:27` does `os.chdir(REPO)` at import time
  (as `offline_eval.py` does), so a relative `--out` is resolved against
  `/root/autodl-tmp/SEU-SRTP`, not the caller's cwd. No `metrics/` directory
  exists there.
- **Fix**: `freeze.sh` passes an absolute `--out`. The trap is left in the probe
  itself (it is a near-verbatim copy of the pilot's, and `scaling_table.py`
  already calls it with an absolute path) but is now called out in a comment.
- **Verification**: freeze sweep goes 10/10 `ok`; `metrics/critic_scaling.json`
  has 4 `measured` + 7 `extrapolated` entries.
- **Semantic impact**: none, but note the *first* freeze run reported
  `critic_probe FAILED` while `metrics/critic_scaling.json` still existed from an
  earlier `scaling_table.py` invocation — i.e. a stale artefact can mask a broken
  regeneration step. This is why the step outcomes are recorded explicitly in
  `status/freeze_summary.md` rather than inferred from the presence of outputs.

---

## F14 — `1v1` ShootMissile lane is structurally ~2× slower, and will miss 6M

- **Category**: `Computational scalability` (NOT algorithmic)
- **Detected**: 2026-10-07 03:37, from the first stable FPS readings
- **Symptom**: `f6m_official_1v1_shoot_hier_selfplay_s1` runs at 55 FPS where the
  sibling `1v1` lanes run at 104–120 FPS on identical thread counts.
- **Cause**: `--use-prior` (implemented only in `algorithms/ppo/ppo_actor.py`,
  5 occurrences) roughly halves SingleCombat throughput. Confirmed against the
  pilot at an identical 10 threads: `official_1v1_selfplay` 324 FPS vs
  `official_1v1_shoot_hier_selfplay` 170 FPS — the same ~2:1 ratio. This is a
  property of the code path, not of contention; the sibling lanes on the same
  box are unaffected.
- **Fix**: **not fixed, deliberately.** At 3 threads it needs ~30.3 h against a
  29.9 h window, so it is expected to land at roughly **98% of 6M**. Killing and
  relaunching it would create a second `run<N>/` directory and a restarted
  partial trajectory is not a clean formal run (see 13.4 of the report). It will
  be reported as `time_cutoff` with the steps actually reached — **never** as
  `completed_6M`.
- **Verification**: pilot log `logs/official_1v1_shoot_hier_selfplay_seed1_gpu0_20261004_065907.log`
  tail FPS 169–172 at 10 threads vs `official_1v1_selfplay` 324–325 at 10 threads.
- **Lesson**: `--use-prior` is an official flag on an official entry point, so it
  is preserved — but it must be budgeted for. A per-lane thread allocation that
  ignores per-lane FPS/thread will systematically starve the armed baselines.

---

## N1 — NOT A FAILURE. `1v1/NoWeapon/HierarchySelfplay` degrades in its second half

Logged here only so it is not later mistaken for an unrecorded anomaly. Full
write-up in `docs/formal_repro_scaling_2026-10-07_08.md` §11.1.

- **Category**: `Algorithmic scalability` / `Sample scalability` (candidate — not established)
- **Evidence**: splitting `f6m_official_1v1_hier_selfplay_s1` (488 training rows)
  into quarters gives monotone `critic_grad_norm` medians **108 → 112 → 266 → 473**
  against reward medians **+24.1 → +22.4 → −17.2 → −89.7**, with almost no
  overlap between the first and last quarter's interquartile ranges.
- **Checked first, deliberately**: the triggering point (`critic_grad_norm = 1274`,
  reward `−333` at 4.39M steps) is the extreme of a real trend, *not* divergence —
  no NaN, no Inf anywhere in the run (or in any of the 11 lanes).
- **Contrast**: the sibling `f6m_official_1v1_selfplay_s1` (same env, scenario
  family, seed and hyperparameters; **non**-hierarchical task) has a falling
  critic gradient and rising reward over the same window.
- **Action taken**: **none.** A degradation is a result, not an engineering
  fault; §16 of the brief forbids modifying the algorithm to rescue a run. The
  lane finishes and is reported at whatever it reaches.
- **Not evidence for** a curse of multiagency: N=1 per side, single seed.
