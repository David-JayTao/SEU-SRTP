"""Data access layer for the f6m figure pipeline (fig1..fig5).

Everything a figure needs, read straight from the on-disk artefacts.  Nothing
here derives a number from an old PNG, interpolates an unfinished run, or
merges the two experiment families: the ``scaling`` runs (generated
``scaling_*`` configs) and the ``official`` runs (repo configs) stay separate
because their reward scales differ by an order of magnitude and must never
share a y-axis.

Data sources (all under this campaign unless noted)
--------------------------------------------------
* ``metrics/curves/<exp>.csv``          - 14 training curves, one row per
                                          episode (episode = threads * 3000
                                          env steps)          -> load_curves()
* ``metrics/normalized_scaling.csv``    - per-N normalised loss/grad series
                                                              -> load_normalized()
* ``metrics/critic_scaling.json``       - measured + extrapolated critic probe
                                                              -> load_critic()
* ``metrics/resources.csv``             - CPU / RSS / GPU samples -> load_resources()
* ``metrics/equal_sample.csv`` and ``metrics/equal_wallclock.csv`` - matched
  budget / wall-clock tables (may contain "pending")           -> load_equal_*
* ``<repo>/scripts/results/**/<exp>/run1/metrics.jsonl`` - per-run train + eval
  rows                                                        -> load_eval*()
* ``experiments/2026-10-04-night/metrics/env_bench_scaling.json`` and
  ``obs_cost_profile.json`` (the pilot campaign)               -> load_env_bench(),
                                                                 load_obs_cost()

Smoothing contract (binding)
----------------------------
``smooth_by_steps`` rolls a **fixed window in environment steps**
(``DEFAULT_WINDOW`` = 250,000), never in episode indices: a 2v2 episode is
12k steps while a 10v10 episode is 60k, so an episode-indexed window would not
be equivalent across scales.  A smoothed point exists only where a *full*
window of data lies at or before it - the smoothed line never starts before
the data supports it and never extends past the last real sample.  A run
shorter than one window yields ``([], [])`` (draw raw only).  ``matched_budget``
never interpolates: a run that did not reach the budget returns ``None``.
Captions must name the window (e.g. "rolling mean, 250k env steps").

RUN_META
--------
Hand-maintained and audited against the raw CSVs (see ``audit()``); it is the
authoritative per-run metadata for labels, colour lookup and completeness:

    scaling  f6m_2v2_noweapon_s0     N=2  s0  4 threads   6,000,000  complete
             f6m_3v3_noweapon_s0     N=3  s0  8 threads   6,000,000  complete
             f6m_3v3_noweapon_s1     N=3  s1  8 threads   6,000,000  complete
             f6m_5v5_noweapon_s0     N=5  s0  8 threads   6,000,000  complete
             f6m_5v5_noweapon_s1     N=5  s1 10 threads   5,400,000  incomplete
             f6m_5v5_noweapon_s2     N=5  s2  8 threads   2,304,000  incomplete
             f6m_10v10_noweapon_s0   N=10 s0 20 threads   6,000,000  complete
             f6m_10v10_noweapon_s1   N=10 s1 20 threads   1,860,000  incomplete
    official f6m_official_heading_s5            1/heading   6,000,000  complete
             f6m_official_2v2_noweapon_s0       2v2         6,000,000  complete
             f6m_official_1v1_selfplay_s1       1v1         5,994,000  final (time cap)
             f6m_official_1v1_vsbaseline_s1     1v1         5,994,000  final (time cap)
             f6m_official_1v1_hier_selfplay_s1  1v1         5,994,000  final (time cap)
             f6m_official_1v1_shoot_hier_selfplay_s1 1v1     5,994,000  final (time cap)

``complete`` distinguishes "the run is finished" (its curve will not grow
further) from the three partially finished scaling runs.  The four official
1v1 runs finished at 5,994,000 = 666 episodes x 9,000 steps - the last whole
rollout episode below the 6M target with 3 threads (see F17), flagged in
``state`` as "time_cap" rather than "partial".
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
CAMPAIGN = HERE.parents[2]                       # experiments/2026-10-07-08-formal6m
REPO_ROOT = CAMPAIGN.parents[1]                  # the SEU-SRTP repository
PILOT_CAMPAIGN = REPO_ROOT / "experiments" / "2026-10-04-night"
METRICS_DIR = CAMPAIGN / "metrics"
CURVES_DIR = METRICS_DIR / "curves"
RESULTS_DIR = REPO_ROOT / "scripts" / "results"

# the ONE smoothing window every comparable curve must use (env steps)
DEFAULT_WINDOW = 250_000
# default half-bracket for matched_budget (env steps)
MATCHED_WINDOW = 200_000

__all__ = [
    "CAMPAIGN", "REPO_ROOT", "PILOT_CAMPAIGN", "METRICS_DIR", "CURVES_DIR",
    "RESULTS_DIR", "DEFAULT_WINDOW", "MATCHED_WINDOW", "RUN_META",
    "load_curves", "load_normalized", "load_critic", "load_critic_meta",
    "load_resources", "load_equal_sample", "load_equal_wallclock",
    "load_eval", "load_eval_rows", "load_env_bench", "load_obs_cost",
    "smooth_by_steps", "matched_budget", "runs_of", "steps_per_episode",
    "audit",
]


# --------------------------------------------------------------------------
# small parsing helpers (pandas is not installed on this machine - stdlib only)
# --------------------------------------------------------------------------
def _read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _num(v):
    """float(v) when v is a finite number, else None ('' and 'pending' -> None)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return None if v != v else float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return None if f != f else f


def _coerce(rows, int_keys=()):
    """Copy rows, casting numeric cells to float (or int for ``int_keys``).

    Non-numeric cells stay as strings ('pending', experiment ids, brackets);
    empty cells become None so downstream code can test them with ``is None``.
    """
    out = []
    for row in rows:
        d = {}
        for k, v in row.items():
            n = _num(v)
            if n is None:
                d[k] = None if (v is None or str(v).strip() == "") else v
            else:
                d[k] = int(n) if k in int_keys else n
        out.append(d)
    return out


def _read_json(path):
    path = Path(path)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def load_curves(camp=CAMPAIGN):
    """``{experiment: [row, ...]}`` for every curve CSV, sorted by env steps.

    Row values are numbers (episode / total_num_steps are ints); the columns
    are episode, total_num_steps, fps, average_episode_rewards, value_loss,
    policy_loss, policy_entropy_loss, policy_entropy_true_sum, actor_grad_norm,
    critic_grad_norm, ratio, wall_time.  One episode = threads * 3000 env steps
    (``steps_per_episode``).
    """
    out = {}
    cdir = Path(camp) / "metrics" / "curves"
    if not cdir.is_dir():
        return out
    for path in sorted(cdir.glob("*.csv")):
        rows = _coerce(_read_csv(path), int_keys=("episode", "total_num_steps"))
        rows = [r for r in rows if r.get("total_num_steps") is not None]
        rows.sort(key=lambda r: r["total_num_steps"])
        out[path.stem] = rows
    return out


def load_normalized(camp=CAMPAIGN):
    """Rows of metrics/normalized_scaling.csv (experiment, label, team_size,
    total_agents, episode, env_steps, fps, reward, reward_per_enemy,
    value_loss, value_loss_per_N2, critic_grad_norm, critic_grad_norm_per_N,
    entropy_loss, policy_loss)."""
    rows = _read_csv(Path(camp) / "metrics" / "normalized_scaling.csv")
    return _coerce(rows, int_keys=("team_size", "total_agents", "episode",
                                   "env_steps"))


def load_critic(camp=CAMPAIGN):
    """``(measured, extrapolated)`` from metrics/critic_scaling.json.

    The two lists are returned *separately* by contract: extrapolated rows are
    never mixed into a measured plot.  Measured rows carry obs_dim,
    share_obs_dim, actor_params, critic_params, critic_first_layer_params and
    critic_first_layer_MAC_per_envstep for N=2/3/5/10.
    """
    d = _read_json(Path(camp) / "metrics" / "critic_scaling.json") or {}
    return list(d.get("measured", [])), list(d.get("extrapolated", []))


def load_critic_meta(camp=CAMPAIGN):
    """Probe metadata that belongs in a caption (device, effective_G_MAC_per_s,
    batch_threads); {} when the probe file is absent."""
    d = _read_json(Path(camp) / "metrics" / "critic_scaling.json") or {}
    return {k: v for k, v in d.items() if k not in ("measured", "extrapolated")}


def load_resources(camp=CAMPAIGN):
    """Rows of metrics/resources.csv sorted by time; adds ``dt`` (datetime) and
    ``epoch`` (POSIX seconds) next to the raw timestamp string."""
    rows = _coerce(_read_csv(Path(camp) / "metrics" / "resources.csv"),
                   int_keys=("n_procs", "gpu_id", "gpu_vram_mb"))
    for r in rows:
        dt = None
        ts = r.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                dt = None
        r["dt"] = dt
        r["epoch"] = dt.timestamp() if dt else None
    rows.sort(key=lambda r: (r["epoch"] if r["epoch"] is not None else 0.0,
                             r.get("experiment") or ""))
    return rows


def load_equal_sample(camp=CAMPAIGN):
    """Rows of metrics/equal_sample.csv (reward@1M..6M + status per bracket).

    Status strings are kept verbatim: "exact" / "interp" / "pending" - never
    coerce "pending" into a number.
    """
    rows = _read_csv(Path(camp) / "metrics" / "equal_sample.csv")
    return _coerce(rows, int_keys=("team_size", "seed", "n_rollout_threads",
                                   "steps_target", "data_age_min",
                                   "train_rows", "max_steps"))


def load_equal_wallclock(camp=CAMPAIGN):
    """Rows of metrics/equal_wallclock.csv (reward@1h/3h/6h/12h/24h + status)."""
    rows = _read_csv(Path(camp) / "metrics" / "equal_wallclock.csv")
    return _coerce(rows, int_keys=("team_size", "seed", "n_rollout_threads",
                                   "steps_target", "data_age_min",
                                   "train_rows", "max_steps"))


def _run_jsonl(exp):
    """<repo>/scripts/results/**/<exp>/run1/metrics.jsonl, or None."""
    hits = sorted(Path(RESULTS_DIR).glob(f"**/{exp}/run1/metrics.jsonl"))
    return hits[0] if hits else None


_EVAL_CACHE = {}


def load_eval_rows(exp):
    """Every eval row of a run as a dict (total_num_steps, wall_time,
    eval_average_episode_rewards, eval_opponent_average_episode_rewards,
    eval_elo_gain, latest_elo), sorted by total_num_steps; [] when the run
    directory is not on disk."""
    if exp in _EVAL_CACHE:
        return _EVAL_CACHE[exp]
    rows = []
    path = _run_jsonl(exp)
    if path is not None:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("eval_average_episode_rewards") is None:
                    continue  # training row
                r["total_num_steps"] = int(_num(r.get("total_num_steps")) or 0)
                for k in ("eval_average_episode_rewards",
                          "eval_opponent_average_episode_rewards",
                          "eval_elo_gain", "latest_elo", "wall_time"):
                    if k in r:
                        r[k] = _num(r[k])
                rows.append(r)
    rows.sort(key=lambda r: r["total_num_steps"])
    _EVAL_CACHE[exp] = rows
    return rows


def load_eval(exp):
    """``[(env_steps, eval_reward), ...]`` from the eval rows of the run;
    [] when the run has no eval file on disk."""
    return [(r["total_num_steps"], r["eval_average_episode_rewards"])
            for r in load_eval_rows(exp)
            if r["eval_average_episode_rewards"] is not None]


def load_env_bench(camp=PILOT_CAMPAIGN):
    """``{"quiet": [...], "loaded": [...]}`` from the 2026-10-04-night pilot:
    per-N env_steps_per_s, sec_per_env_step, per_aircraft_ms (each row also has
    obs_dim / share_obs_dim / note)."""
    d = _read_json(Path(camp) / "metrics" / "env_bench_scaling.json") or {}
    return {"quiet": list(d.get("quiet", [])), "loaded": list(d.get("loaded", []))}


def load_obs_cost(camp=PILOT_CAMPAIGN):
    """Per-N step-cost decomposition: get_obs_all_ms, get_state_ms, sim_run_ms,
    full_step_ms, obs_share_of_step_pct, get_state_per_agent_us."""
    return list(_read_json(Path(camp) / "metrics" / "obs_cost_profile.json") or [])


# --------------------------------------------------------------------------
# smoothing / matched budget - fixed in ENV STEPS, never in episode index
# --------------------------------------------------------------------------
def smooth_by_steps(rows, window=DEFAULT_WINDOW,
                    value_key="average_episode_rewards",
                    x_key="total_num_steps"):
    """Rolling mean with a fixed *environment-step* window.  -> (xs, ys).

    A point is emitted at every real sample ``x`` with
    ``x - x_first >= window``; its value is the mean of every sample in
    ``[x - window, x]``.  Consequences, by design:

    * the smoothed series starts only once a full window of data exists
      (the first ``window`` steps stay raw) and never extends past the last
      real sample - no extrapolation in either direction;
    * a run spanning less than one window returns ``([], [])`` (draw raw only);
    * the same ``window`` means the same number of environment steps at every
      scale, which an episode-indexed window could not guarantee (2v2 episodes
      are 12k steps, 10v10 episodes 60k).

    Rows with missing/non-numeric x or value are skipped; both returned lists
    are plain Python floats, JSON-serialisable, and equal in length.
    """
    if window is None or window <= 0:
        raise ValueError(f"window must be a positive number of env steps, got {window!r}")
    pts = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        x = _num(r.get(x_key))
        y = _num(r.get(value_key))
        if x is None or y is None:
            continue
        pts.append((x, y))
    pts.sort(key=lambda p: p[0])
    if len(pts) < 2:
        return [], []
    x0 = pts[0][0]
    xs, ys = [], []
    j = 0            # first index inside the current window
    run = 0.0        # sum of values in pts[j..i]
    for i, (xi, yi) in enumerate(pts):
        run += yi
        lo = xi - window
        while pts[j][0] < lo:
            run -= pts[j][1]
            j += 1
        if xi - x0 >= window:      # full window available
            xs.append(xi)
            ys.append(run / (i - j + 1))
    return xs, ys


def matched_budget(rows, budget, window=MATCHED_WINDOW,
                   value_key="average_episode_rewards",
                   x_key="total_num_steps"):
    """Mean reward over ``[budget - window, budget]`` env steps, or None.

    Returns None when the run never reached ``budget`` (no interpolation, no
    extrapolation) or when no sample falls inside the bracket.  ``window`` is
    in environment steps, so the same bracket means the same amount of
    experience for every team size.
    """
    pts = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        x = _num(r.get(x_key))
        y = _num(r.get(value_key))
        if x is None or y is None:
            continue
        pts.append((x, y))
    if not pts:
        return None
    pts.sort(key=lambda p: p[0])
    if pts[-1][0] < budget:
        return None
    vals = [y for x, y in pts if budget - window <= x <= budget]
    if not vals:
        return None
    return sum(vals) / len(vals)


# --------------------------------------------------------------------------
# RUN_META - audited against the raw CSVs, see audit()
# --------------------------------------------------------------------------
def _run(n, seed, threads, family, weapon, label, target_steps, last_steps,
         complete, env, scenario, algo, state):
    return {
        "n": n, "seed": seed, "threads": threads, "family": family,
        "weapon": weapon, "label": label, "target_steps": target_steps,
        "last_steps": last_steps, "complete": complete, "env": env,
        "scenario": scenario, "algo": algo, "state": state,
    }


RUN_META = {
    # ---- scaling family: generated scaling_* configs, NoWeapon -------------
    "f6m_2v2_noweapon_s0": _run(
        2, 0, 4, "scaling", "noweapon", "2v2 seed 0", 6_000_000, 6_000_000,
        True, "MultipleCombat", "2v2/scaling_noweapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_3v3_noweapon_s0": _run(
        3, 0, 8, "scaling", "noweapon", "3v3 seed 0", 6_000_000, 6_000_000,
        True, "MultipleCombat", "3v3/scaling_noweapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_3v3_noweapon_s1": _run(
        3, 1, 8, "scaling", "noweapon", "3v3 seed 1", 6_000_000, 6_000_000,
        True, "MultipleCombat", "3v3/scaling_noweapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_5v5_noweapon_s0": _run(
        5, 0, 8, "scaling", "noweapon", "5v5 seed 0", 6_000_000, 6_000_000,
        True, "MultipleCombat", "5v5/scaling_noweapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_5v5_noweapon_s1": _run(
        5, 1, 10, "scaling", "noweapon", "5v5 seed 1", 6_000_000, 5_400_000,
        False, "MultipleCombat", "5v5/scaling_noweapon/HierarchySelfplay",
        "mappo", "partial"),
    "f6m_5v5_noweapon_s2": _run(
        5, 2, 8, "scaling", "noweapon", "5v5 seed 2", 6_000_000, 2_304_000,
        False, "MultipleCombat", "5v5/scaling_noweapon/HierarchySelfplay",
        "mappo", "partial"),
    "f6m_10v10_noweapon_s0": _run(
        10, 0, 20, "scaling", "noweapon", "10v10 seed 0", 6_000_000, 6_000_000,
        True, "MultipleCombat", "10v10/scaling_noweapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_10v10_noweapon_s1": _run(
        10, 1, 20, "scaling", "noweapon", "10v10 seed 1", 6_000_000, 1_860_000,
        False, "MultipleCombat", "10v10/scaling_noweapon/HierarchySelfplay",
        "mappo", "partial"),

    # ---- official family: repo configs, a different experiment family ------
    "f6m_official_heading_s5": _run(
        1, 5, 4, "official", "none", "SingleControl heading", 6_000_000,
        6_000_000, True, "SingleControl", "1/heading", "ppo", "complete"),
    "f6m_official_2v2_noweapon_s0": _run(
        2, 0, 4, "official", "noweapon", "2v2 seed 0 (official)", 6_000_000,
        6_000_000, True, "MultipleCombat", "2v2/NoWeapon/HierarchySelfplay",
        "mappo", "complete"),
    "f6m_official_1v1_selfplay_s1": _run(
        1, 1, 3, "official", "noweapon", "1v1 Selfplay", 6_000_000, 5_994_000,
        True, "SingleCombat", "1v1/NoWeapon/Selfplay", "ppo", "time_cap"),
    "f6m_official_1v1_vsbaseline_s1": _run(
        1, 1, 3, "official", "noweapon", "1v1 vsBaseline", 6_000_000,
        5_994_000, True, "SingleCombat", "1v1/NoWeapon/vsBaseline", "ppo",
        "time_cap"),
    "f6m_official_1v1_hier_selfplay_s1": _run(
        1, 1, 3, "official", "noweapon", "1v1 HierSelfplay", 6_000_000,
        5_994_000, True, "SingleCombat", "1v1/NoWeapon/HierarchySelfplay",
        "ppo", "time_cap"),
    "f6m_official_1v1_shoot_hier_selfplay_s1": _run(
        1, 1, 3, "official", "shoot", "1v1 ShootHier", 6_000_000, 5_994_000,
        True, "SingleCombat", "1v1/ShootMissile/HierarchySelfplay", "ppo",
        "time_cap"),
}


def runs_of(family=None, n=None, complete_only=False):
    """Experiment ids sorted by (team size, seed) - deterministic plot order.

    Use it instead of iterating a dict so every figure draws the same order.
    """
    out = []
    for exp, meta in RUN_META.items():
        if family is not None and meta["family"] != family:
            continue
        if n is not None and meta["n"] != n:
            continue
        if complete_only and not meta["complete"]:
            continue
        out.append(exp)
    out.sort(key=lambda e: (RUN_META[e]["n"], RUN_META[e]["seed"]))
    return out


def steps_per_episode(exp):
    """Environment steps per logged episode for a run (threads * 3000)."""
    return RUN_META[exp]["threads"] * 3000


def audit(curves=None):
    """Check RUN_META against the raw curve CSVs.  -> list of problem strings.

    Verifies for all 14 runs that the CSV exists, that its step column is a
    uniform grid of ``steps_per_episode``, that the last logged step equals
    ``RUN_META[exp]['last_steps']``, and that first/last steps are consistent
    with the family split.  Empty list == RUN_META matches the audit table.
    """
    curves = load_curves() if curves is None else curves
    problems = []
    for exp, meta in sorted(RUN_META.items()):
        rows = curves.get(exp)
        if not rows:
            problems.append(f"{exp}: no curve CSV rows")
            continue
        steps = [r["total_num_steps"] for r in rows]
        spe = steps_per_episode(exp)
        if any(b - a != spe for a, b in zip(steps, steps[1:])):
            problems.append(f"{exp}: step grid is not uniform at {spe}")
        if steps[0] != spe:
            problems.append(f"{exp}: first step {steps[0]} != {spe}")
        if steps[-1] != meta["last_steps"]:
            problems.append(
                f"{exp}: last step {steps[-1]} != RUN_META.last_steps "
                f"{meta['last_steps']}")
        if (steps[-1] >= meta["target_steps"]) and not meta["complete"]:
            problems.append(f"{exp}: reached target but complete=False")
        if meta["complete"] and meta["state"] == "partial":
            problems.append(f"{exp}: complete=True with state='partial'")
    for exp in curves:
        if exp not in RUN_META:
            problems.append(f"{exp}: CSV present but missing from RUN_META")
    return problems
