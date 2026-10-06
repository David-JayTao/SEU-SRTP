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
