# Equal-wall-clock comparison -- 2026-10-07-08-formal6m

- generated: 2026-10-07 03:42:54
- source campaign: `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m`
- run outputs: `/root/autodl-tmp/SEU-SRTP/scripts/results`
- budgets: 1h, 3h, 6h, 12h, 24h of elapsed run time (wall_time minus the run's FIRST timestamp)
- value at budget: bracketing linear interpolation; `pending` = not reached yet, nothing extrapolated

## Mean episode reward at equal wall-clock budgets

cells: mean reward (mean reward per enemy) [runs contributing]; * = at least one run interpolated between bracketing updates; `pending` = no run has reached the budget yet

| variant | N | runs | furthest h | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|---|---|
| noweapon | 2 | 1/1 | 0.76 | pending | pending | pending | pending | pending |
| noweapon | 3 | 1/1 | 0.74 | pending | pending | pending | pending | pending |
| noweapon | 5 | 1/1 | 0.67 | pending | pending | pending | pending | pending |
| noweapon | 10 | 1/1 | 0.54 | pending | pending | pending | pending | pending |
| official_hier_selfplay | 1 | 1/1 | 0.38 | pending | pending | pending | pending | pending |
| official_selfplay | 1 | 1/1 | 0.52 | pending | pending | pending | pending | pending |
| official_shoot_hier_selfplay | 1 | 1/1 | 0.37 | pending | pending | pending | pending | pending |
| official_vsbaseline | 1 | 1/1 | 0.52 | pending | pending | pending | pending | pending |
| official_noweapon | 2 | 1/1 | 0.73 | pending | pending | pending | pending | pending |

## Per-run detail

| experiment | N | seed | thr | rows | elapsed h | max steps | state | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 1 | 3 | 14 | 0.38 | 126000 | active | pending | pending | pending | pending | pending |
| f6m_official_1v1_selfplay_s1 | 1 | 1 | 3 | 23 | 0.52 | 207000 | active | pending | pending | pending | pending | pending |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 1 | 3 | 9 | 0.37 | 81000 | active | pending | pending | pending | pending | pending |
| f6m_official_1v1_vsbaseline_s1 | 1 | 1 | 3 | 26 | 0.52 | 234000 | active | pending | pending | pending | pending | pending |
| f6m_2v2_noweapon_s0 | 2 | 0 | 4 | 19 | 0.76 | 228000 | active | pending | pending | pending | pending | pending |
| f6m_official_2v2_noweapon_s0 | 2 | 0 | 4 | 18 | 0.73 | 216000 | active | pending | pending | pending | pending | pending |
| f6m_3v3_noweapon_s0 | 3 | 0 | 8 | 15 | 0.74 | 360000 | active | pending | pending | pending | pending | pending |
| f6m_5v5_noweapon_s0 | 5 | 0 | 8 | 9 | 0.67 | 216000 | active | pending | pending | pending | pending | pending |
| f6m_10v10_noweapon_s0 | 10 | 0 | 20 | 3 | 0.54 | 180000 | active | pending | pending | pending | pending | pending |

## Notes

- `reward` is `average_episode_rewards` from the metrics.jsonl training rows; elapsed time is `wall_time - min(wall_time)`, both from the run's own file, so it excludes queueing/startup before the first logged update.
- A run contributes to a group mean at a budget only once its metrics.jsonl reaches that budget; the [k] suffix counts contributing runs.
- Scales use different n_rollout_threads (sized to measured cost), so wall-clock reflects both learning speed and the scheduling choice.
- Cross-campaign reference: `--root <campaign dir>` (or LAG_CAMPAIGN_ROOT); outputs always land in this campaign's metrics/.
- Raw per-cell statuses/brackets: metrics/equal_wallclock.csv.

