# Equal-wall-clock comparison -- 2026-10-07-08-formal6m

- generated: 2026-10-08 00:00:57
- source campaign: `/root/autodl-tmp/SEU-SRTP/experiments/2026-10-07-08-formal6m`
- run outputs: `/root/autodl-tmp/SEU-SRTP/scripts/results`
- budgets: 1h, 3h, 6h, 12h, 24h of elapsed run time (wall_time minus the run's FIRST timestamp)
- value at budget: bracketing linear interpolation; `pending` = not reached yet, nothing extrapolated

## Mean episode reward at equal wall-clock budgets

cells: mean reward (mean reward per enemy) [runs contributing]; * = at least one run interpolated between bracketing updates; `pending` = no run has reached the budget yet

| variant | N | runs | furthest h | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|---|---|
| noweapon | 2 | 1/1 | 21.06 | +4.32 (+2.16)* [1] | +22.78 (+11.39)* [1] | +21.23 (+10.61)* [1] | +11.74 (+5.87)* [1] | pending |
| noweapon | 3 | 2/2 | 13.24 | -0.62 (-0.21)* [2] | +35.85 (+11.95)* [2] | +34.83 (+11.61)* [2] | +35.85 (+11.95)* [1] | pending |
| noweapon | 5 | 2/2 | 20.86 | -6.68 (-1.34)* [2] | -2.04 (-0.41)* [2] | +6.19 (+1.24)* [2] | +27.24 (+5.45)* [1] | pending |
| noweapon | 10 | 1/1 | 20.71 | -17.48 (-1.75)* [1] | -17.23 (-1.72)* [1] | -16.76 (-1.68)* [1] | -2.61 (-0.26)* [1] | pending |
| official_hier_selfplay | 1 | 1/1 | 20.02 | +23.60 (+23.60)* [1] | +32.67 (+32.67)* [1] | +18.73 (+18.73)* [1] | -10.52 (-10.52)* [1] | pending |
| official_selfplay | 1 | 1/1 | 15.87 | -156.74 (-156.74)* [1] | -20.31 (-20.31)* [1] | +36.36 (+36.36)* [1] | +29.11 (+29.11)* [1] | pending |
| official_shoot_hier_selfplay | 1 | 1/1 | 20.65 | -18.12 (-18.12)* [1] | -26.65 (-26.65)* [1] | -60.93 (-60.93)* [1] | -12.24 (-12.24)* [1] | pending |
| official_vsbaseline | 1 | 1/1 | 13.57 | -8.60 (-8.60)* [1] | +6.83 (+6.83)* [1] | +12.37 (+12.37)* [1] | +29.23 (+29.23)* [1] | pending |
| official_noweapon | 2 | 1/1 | 21.06 | -0.59 (-0.30)* [1] | +18.72 (+9.36)* [1] | +21.00 (+10.50)* [1] | +17.13 (+8.56)* [1] | pending |

## Per-run detail

| experiment | N | seed | thr | rows | elapsed h | max steps | state | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_official_1v1_hier_selfplay_s1 | 1 | 1 | 3 | 666 | 20.02 | 5994000 | idle | +23.60 (+23.60)* | +32.67 (+32.67)* | +18.73 (+18.73)* | -10.52 (-10.52)* | pending |
| f6m_official_1v1_selfplay_s1 | 1 | 1 | 3 | 666 | 15.87 | 5994000 | idle | -156.74 (-156.74)* | -20.31 (-20.31)* | +36.36 (+36.36)* | +29.11 (+29.11)* | pending |
| f6m_official_1v1_shoot_hier_selfplay_s1 | 1 | 1 | 3 | 508 | 20.65 | 4572000 | active | -18.12 (-18.12)* | -26.65 (-26.65)* | -60.93 (-60.93)* | -12.24 (-12.24)* | pending |
| f6m_official_1v1_vsbaseline_s1 | 1 | 1 | 3 | 666 | 13.57 | 5994000 | idle | -8.60 (-8.60)* | +6.83 (+6.83)* | +12.37 (+12.37)* | +29.23 (+29.23)* | pending |
| f6m_2v2_noweapon_s0 | 2 | 0 | 4 | 491 | 21.06 | 5892000 | active | +4.32 (+2.16)* | +22.78 (+11.39)* | +21.23 (+10.61)* | +11.74 (+5.87)* | pending |
| f6m_official_2v2_noweapon_s0 | 2 | 0 | 4 | 479 | 21.06 | 5748000 | active | -0.59 (-0.30)* | +18.72 (+9.36)* | +21.00 (+10.50)* | +17.13 (+8.56)* | pending |
| f6m_3v3_noweapon_s0 | 3 | 0 | 8 | 250 | 13.24 | 6000000 | complete | -1.20 (-0.40)* | +35.44 (+11.81)* | +35.57 (+11.86)* | +35.85 (+11.95)* | pending |
| f6m_3v3_noweapon_s1 | 3 | 1 | 8 | 119 | 6.53 | 2856000 | active | -0.04 (-0.01)* | +36.27 (+12.09)* | +34.08 (+11.36)* | pending | pending |
| f6m_5v5_noweapon_s0 | 5 | 0 | 8 | 250 | 20.86 | 6000000 | complete | -7.72 (-1.54)* | -4.24 (-0.85)* | -4.03 (-0.81)* | +27.24 (+5.45)* | pending |
| f6m_5v5_noweapon_s1 | 5 | 1 | 10 | 73 | 6.57 | 2190000 | active | -5.65 (-1.13)* | +0.17 (+0.03)* | +16.40 (+3.28)* | pending | pending |
| f6m_10v10_noweapon_s0 | 10 | 0 | 20 | 83 | 20.71 | 4980000 | active | -17.48 (-1.75)* | -17.23 (-1.72)* | -16.76 (-1.68)* | -2.61 (-0.26)* | pending |

## Notes

- `reward` is `average_episode_rewards` from the metrics.jsonl training rows; elapsed time is `wall_time - min(wall_time)`, both from the run's own file, so it excludes queueing/startup before the first logged update.
- A run contributes to a group mean at a budget only once its metrics.jsonl reaches that budget; the [k] suffix counts contributing runs.
- Scales use different n_rollout_threads (sized to measured cost), so wall-clock reflects both learning speed and the scheduling choice.
- Cross-campaign reference: `--root <campaign dir>` (or LAG_CAMPAIGN_ROOT); outputs always land in this campaign's metrics/.
- Raw per-cell statuses/brackets: metrics/equal_wallclock.csv.
- skipped (no NvN scale token in name): f6m_official_heading_s5

