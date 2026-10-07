# Formal-6M auto-results — machine-generated numeric record

> **This file is machine-generated. Do not hand-edit.** Generated **2026-10-07 17:51:53 CST** (2026-10-07T17:51:53+08:00) by `experiments/2026-10-07-08-formal6m/scripts/make_auto_results.py` (repo HEAD `909a924`, branch `exp/formal-6m-20261007`). 本文件由脚本自动生成，所有数字均来自机器产物。
>
> Campaign: `experiments/2026-10-07-08-formal6m`. Regenerate with: `cd experiments/2026-10-07-08-formal6m && /root/miniconda3/envs/jsbsim/bin/python scripts/make_auto_results.py` (also invoked by `scripts/freeze.sh`, which the tmux auto-finalizer runs on a schedule).
>
> Every value below is read from the files listed under *Sources and freshness*; none is hand-entered, and nothing is extrapolated except where a row explicitly says so. If the hand-written report never gets finished, this document is the complete numeric record.

## Status vocabulary and budget rule

Status is exactly one of six values, derived by this script from the watcher's own flags (`metrics/status.json`) under the rules below (the same rules the monitor uses):

| status | meaning |
|---|---|
| `completed_6M` | reached the full 6,000,000 budget. |
| `completed_at_ceiling` | reached its own reachable ceiling, which is below 6,000,000 (3-thread lanes only). |
| `running` | still writing: log updated within the watcher's 30 min stall threshold. |
| `time_cutoff` | stopped short of its ceiling without crash evidence (wall-clock cap, or log quiet > 30 min). |
| `failed` | Traceback / NaN / Inf observed. |
| `not_applicable` | no data found for the lane. |

The runner floors `episodes = num_env_steps // 3000 // n_rollout_threads` (incident F17), so a lane's ACHIEVABLE ceiling is `(6e6 // 3000 // threads) * 3000 * threads`. Ceilings for the thread counts that actually occur in this campaign:

| threads | episodes | achievable ceiling |
|---|---|---|
| 3 | 666 | 5,994,000 |
| 4 | 500 | 6,000,000 |
| 8 | 250 | 6,000,000 |
| 10 | 200 | 6,000,000 |
| 20 | 100 | 6,000,000 |

`reward_per_enemy` (reward / team_size) is a cross-N-comparable quantity ONLY for the NoWeapon family (PostureReward sums over each agent's enemies). It is withheld for the ShootMissile family here.

Pilot (2026-10-04) and formal (6M) results are separate series and are never merged.

## Sources and freshness

Every number in this document is read from these machine artefacts at generation time. A source newer than a table means the table is a snapshot, not the live state; the live state is always the inventory table below (built from `metrics/status.json`).

| source | last written |
|---|---|
| `manifest.csv` | 2026-10-07 17:50:39 |
| `metrics/status.json` | 2026-10-07 17:50:38 |
| `metrics/summary.csv` | 2026-10-07 17:51:53 |
| `metrics/scaling_table.csv` | 2026-10-07 17:51:53 |
| `metrics/critic_scaling.json` | 2026-10-07 17:50:45 |
| `metrics/equal_sample.csv` | 2026-10-07 17:50:46 |
| `metrics/equal_wallclock.csv` | 2026-10-07 17:50:46 |
| `status/incidents.md` | 2026-10-07 17:26:27 |

## Experiment inventory (every lane)

Live view from `metrics/status.json` (timestamp 2026-10-07 17:50:36; 1.3 min before this file was generated).

| experiment | scenario | algo | seed | thr | achievable ceiling | steps | % ceiling | status | FPS | wall-clock | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `f6m_2v2_noweapon_s0` | 2v2/scaling_noweapon/HierarchySelfplay | mappo | 0 | 4 | 6,000,000 | 4,164,000 | 69.4% | `running` | 77 | 14.9 h | — |
| `f6m_3v3_noweapon_s0` | 3v3/scaling_noweapon/HierarchySelfplay | mappo | 0 | 8 | 6,000,000 | 6,000,000 | 100.0% | `completed_6M` | 125 | 13.3 h | — |
| `f6m_3v3_noweapon_s1` | 3v3/scaling_noweapon/HierarchySelfplay | mappo | 1 | 8 | 6,000,000 | 168,000 | 2.8% | `running` | 114 | 25 min | — |
| `f6m_5v5_noweapon_s0` | 5v5/scaling_noweapon/HierarchySelfplay | mappo | 0 | 8 | 6,000,000 | 4,320,000 | 72.0% | `running` | 80 | 14.9 h | — |
| `f6m_5v5_noweapon_s1` | 5v5/scaling_noweapon/HierarchySelfplay | mappo | 1 | 10 | 6,000,000 | 120,000 | 2.0% | `running` | 81 | 25 min | — |
| `f6m_10v10_noweapon_s0` | 10v10/scaling_noweapon/HierarchySelfplay | mappo | 0 | 20 | 6,000,000 | 3,660,000 | 61.0% | `running` | 68 | 14.9 h | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1v1/NoWeapon/HierarchySelfplay | ppo | 1 | 3 | 5,994,000 | 4,347,000 | 72.5% | `running` | 83 | 14.5 h | — |
| `f6m_official_1v1_selfplay_s1` | 1v1/NoWeapon/Selfplay | ppo | 1 | 3 | 5,994,000 | 5,517,000 | 92.0% | `running` | 104 | 14.7 h | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1v1/ShootMissile/HierarchySelfplay | ppo | 1 | 3 | 5,994,000 | 3,204,000 | 53.5% | `running` | 61 | 14.5 h | — |
| `f6m_official_1v1_vsbaseline_s1` | 1v1/NoWeapon/vsBaseline | ppo | 1 | 3 | 5,994,000 | 5,994,000 | 100.0% | `completed_at_ceiling` | 122 | 13.6 h | — |
| `f6m_official_2v2_noweapon_s0` | 2v2/NoWeapon/HierarchySelfplay | mappo | 0 | 4 | 6,000,000 | 4,044,000 | 67.4% | `running` | 75 | 14.9 h | — |

Totals across 11 lanes: **41,538,000 env steps completed of 65,976,000 achievable** (snapshot); aggregate live throughput **990 env-steps/s**.

### Checkpoints

| experiment | latest checkpoint | state |
|---|---|---|
| `f6m_2v2_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/2v2/scaling_noweapon/HierarchySelfplay/mappo/f6m_2v2_noweapon_s0/run1/actor_latest.pt` | on disk |
| `f6m_3v3_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/3v3/scaling_noweapon/HierarchySelfplay/mappo/f6m_3v3_noweapon_s0/run1/actor_latest.pt` | on disk |
| `f6m_3v3_noweapon_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/3v3/scaling_noweapon/HierarchySelfplay/mappo/f6m_3v3_noweapon_s1/run1/actor_latest.pt` | on disk |
| `f6m_5v5_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/5v5/scaling_noweapon/HierarchySelfplay/mappo/f6m_5v5_noweapon_s0/run1/actor_latest.pt` | on disk |
| `f6m_5v5_noweapon_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/5v5/scaling_noweapon/HierarchySelfplay/mappo/f6m_5v5_noweapon_s1/run1/actor_latest.pt` | on disk |
| `f6m_10v10_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/10v10/scaling_noweapon/HierarchySelfplay/mappo/f6m_10v10_noweapon_s0/run1/actor_latest.pt` | on disk |
| `f6m_official_1v1_hier_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/HierarchySelfplay/ppo/f6m_official_1v1_hier_selfplay_s1/run1/actor_latest.pt` | on disk |
| `f6m_official_1v1_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/Selfplay/ppo/f6m_official_1v1_selfplay_s1/run1/actor_latest.pt` | on disk |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/ShootMissile/HierarchySelfplay/ppo/f6m_official_1v1_shoot_hier_selfplay_s1/run1/actor_latest.pt` | on disk |
| `f6m_official_1v1_vsbaseline_s1` | `/root/autodl-tmp/SEU-SRTP/scripts/results/SingleCombat/1v1/NoWeapon/vsBaseline/ppo/f6m_official_1v1_vsbaseline_s1/run1/actor_latest.pt` | on disk |
| `f6m_official_2v2_noweapon_s0` | `/root/autodl-tmp/SEU-SRTP/scripts/results/MultipleCombat/2v2/NoWeapon/HierarchySelfplay/mappo/f6m_official_2v2_noweapon_s0/run1/actor_latest.pt` | on disk |

## Scaling table (reward and reward-per-enemy)

Snapshot: `metrics/scaling_table.csv` (written 2026-10-07 17:51:53). `reward_per_enemy = train_reward_last / team_size`, computed here and emitted only for the NoWeapon family.

| scale | variant | seed | thr | steps (snapshot) | FPS | train reward (last) | reward/enemy | eval reward (last) | tail slope |
|---|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 0 | 4 | 4,164,000 | 77 | 5.3198 | 2.6599 | -50.3104 | 0.0492 |
| 3v3 | noweapon | 0 | 8 | 6,000,000 | 125 | 35.9318 | 11.9773 | 47.8388 | 0.0089 |
| 3v3 | noweapon | 1 | 8 | 168,000 | 114 | -5.3230 | -1.7743 | -72.5970 | -0.3005 |
| 5v5 | noweapon | 0 | 8 | 4,320,000 | 80 | -66.9209 | -13.3842 | -71.0688 | -1.8708 |
| 5v5 | noweapon | 1 | 10 | 150,000 | 82 | -8.2978 | -1.6596 | -5.6146 | — |
| 10v10 | noweapon | 0 | 20 | 3,660,000 | 68 | -7.0139 | -0.7014 | -177.5817 | 0.0083 |

`reward_per_enemy` is shown as `n/a` for any ShootMissile row by policy. The official-baseline lanes are not part of this table (they are their own series; see the inventory).

## Equal-sample comparison

Reward and reward-per-enemy at fixed vectorised env-step budgets (1M–6M), from the campaign's own equal-sample generator.

Snapshot: `metrics/equal_sample.csv` (written 2026-10-07 17:50:46). `—` = pending (budget not reached at the snapshot); `*` = interpolated between bracketing updates; `†` = first crossing; `§` = before-data / nan-gap. Raw status and bracket per cell: the CSV itself.

**reward**

| experiment | seed | 1M | 2M | 3M | 4M | 5M | 6M |
|---|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -17.2663* | -11.6991* | -10.6261 | — | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 23.7545* | 24.3933* | 16.3153 | 19.9296* | — | — |
| `f6m_3v3_noweapon_s0` | 0 | 31.7989* | 35.3119* | 36.0622 | 35.7911* | 36.0737* | 35.9318 |
| `f6m_3v3_noweapon_s1` | 1 | — | — | — | — | — | — |
| `f6m_5v5_noweapon_s0` | 0 | -1.6399* | 48.8016* | 50.3039 | 23.136* | — | — |
| `f6m_5v5_noweapon_s1` | 1 | — | — | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 20.8747* | 33.1314* | -104.0363* | -8.0676* | — | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -64.9082* | 4.9369* | 25.578* | 13.1161* | 30.3252* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | -17.9232* | -68.9111* | -29.3841* | — | — | — |
| `f6m_official_1v1_vsbaseline_s1` | 1 | 11.2948* | 12.0699* | 23.5194* | 26.4511* | 29.8232* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | 15.1427* | 21.6233* | 23.1315 | 22.4214* | — | — |

**reward per enemy (reward / team_size; NoWeapon family only — `n/a` for ShootMissile)**

| experiment | seed | 1M | 2M | 3M | 4M | 5M | 6M |
|---|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -1.7266* | -1.1699* | -1.0626 | — | — | — |
| `f6m_2v2_noweapon_s0` | 0 | 11.8772* | 12.1967* | 8.1576 | 9.9648* | — | — |
| `f6m_3v3_noweapon_s0` | 0 | 10.5996* | 11.7706* | 12.0207 | 11.9304* | 12.0246* | 11.9773 |
| `f6m_3v3_noweapon_s1` | 1 | — | — | — | — | — | — |
| `f6m_5v5_noweapon_s0` | 0 | -0.328* | 9.7603* | 10.0608 | 4.6272* | — | — |
| `f6m_5v5_noweapon_s1` | 1 | — | — | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 20.8747* | 33.1314* | -104.0363* | -8.0676* | — | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -64.9082* | 4.9369* | 25.578* | 13.1161* | 30.3252* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | n/a | n/a | n/a | n/a | n/a | n/a |
| `f6m_official_1v1_vsbaseline_s1` | 1 | 11.2948* | 12.0699* | 23.5194* | 26.4511* | 29.8232* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | 7.5713* | 10.8116* | 11.5658 | 11.2107* | — | — |

## Equal-wall-clock comparison

Reward and reward-per-enemy at fixed wall-clock budgets (1h–24h), from the campaign's own equal-wall-clock generator.

Snapshot: `metrics/equal_wallclock.csv` (written 2026-10-07 17:50:46). `—` = pending (budget not reached at the snapshot); `*` = interpolated between bracketing updates; `†` = first crossing; `§` = before-data / nan-gap. Raw status and bracket per cell: the CSV itself.

**reward**

| experiment | seed | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -17.4795* | -17.2337* | -16.7635* | -2.6125* | — |
| `f6m_2v2_noweapon_s0` | 0 | 4.319* | 22.78* | 21.2265* | 11.7387* | — |
| `f6m_3v3_noweapon_s0` | 0 | -1.2008* | 35.4391* | 35.5665* | 35.8465* | — |
| `f6m_3v3_noweapon_s1` | 1 | — | — | — | — | — |
| `f6m_5v5_noweapon_s0` | 0 | -7.7217* | -4.2391* | -4.0284* | 27.2418* | — |
| `f6m_5v5_noweapon_s1` | 1 | — | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 23.5967* | 32.6657* | 18.727* | -10.5172* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -156.7427* | -20.3149* | 36.3616* | 29.1071* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | -18.116* | -26.653* | -60.9307* | -12.2356* | — |
| `f6m_official_1v1_vsbaseline_s1` | 1 | -8.6019* | 6.8271* | 12.3685* | 29.2324* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | -0.5935* | 18.718* | 20.9977* | 17.1295* | — |

**reward per enemy (reward / team_size; NoWeapon family only — `n/a` for ShootMissile)**

| experiment | seed | 1h | 3h | 6h | 12h | 24h |
|---|---|---|---|---|---|---|
| `f6m_10v10_noweapon_s0` | 0 | -1.7479* | -1.7234* | -1.6764* | -0.2613* | — |
| `f6m_2v2_noweapon_s0` | 0 | 2.1595* | 11.39* | 10.6132* | 5.8694* | — |
| `f6m_3v3_noweapon_s0` | 0 | -0.4003* | 11.813* | 11.8555* | 11.9488* | — |
| `f6m_3v3_noweapon_s1` | 1 | — | — | — | — | — |
| `f6m_5v5_noweapon_s0` | 0 | -1.5443* | -0.8478* | -0.8057* | 5.4484* | — |
| `f6m_5v5_noweapon_s1` | 1 | — | — | — | — | — |
| `f6m_official_1v1_hier_selfplay_s1` | 1 | 23.5967* | 32.6657* | 18.727* | -10.5172* | — |
| `f6m_official_1v1_selfplay_s1` | 1 | -156.7427* | -20.3149* | 36.3616* | 29.1071* | — |
| `f6m_official_1v1_shoot_hier_selfplay_s1` | 1 | n/a | n/a | n/a | n/a | n/a |
| `f6m_official_1v1_vsbaseline_s1` | 1 | -8.6019* | 6.8271* | 12.3685* | 29.2324* | — |
| `f6m_official_2v2_noweapon_s0` | 0 | -0.2967* | 9.359* | 10.4988* | 8.5647* | — |

## Representation / critic scaling (measured vs extrapolated)

Source: `metrics/critic_scaling.json` (written 2026-10-07 17:50:45); probe = model construction on the real networks, no training. Three tables, never mixed: (1) the four MEASURED points, (2) values derived from those same measurements, (3) predictions beyond the measured range.

### 1. Measured rows (N = 2, 3, 5, 10)

| N | agents | obs dim | share obs dim | actor params | critic params | critic 1st layer params | 1st-layer MAC/envstep | fwd ms (batch) | fwd ms (fixed-256) | bwd ms (fixed-256) | fwd µs/sample |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 154,891 | 163,969 | 13,952 | 331,776 | 0.501 | 0.7886 | 4.9440 | 3.0810 |
| 3 | 6 | 39 | 234 | 156,427 | 180,097 | 30,080 | 1,078,272 | 0.482 | 0.8879 | 4.8455 | 3.4680 |
| 5 | 10 | 63 | 630 | 159,499 | 230,785 | 80,768 | 4,838,400 | 0.477 | 0.8247 | 4.9646 | 3.2220 |
| 10 | 20 | 123 | 2460 | 167,179 | 465,025 | 315,008 | 37,785,600 | 0.529 | 0.6098 | 4.1075 | 2.3820 |

### 2. Derived from the measured points (not new measurements)

Computed from the same N = 2, 3, 5, 10 probe runs; the first-layer values here are identical to table 1 and are checked below. Do not treat this table as independent evidence.

| N | agents | obs dim | share obs dim | critic 1st layer params | 1st-layer MAC/envstep | est. fwd ms/envstep | share-obs buffer GB |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 27 | 108 | 13,952 | 331,776 | 0.0025 | 0.029 |
| 3 | 6 | 39 | 234 | 30,080 | 1,078,272 | 0.0082 | 0.094 |
| 5 | 10 | 63 | 630 | 80,768 | 4,838,400 | 0.0366 | 0.423 |
| 10 | 20 | 123 | 2460 | 315,008 | 37,785,600 | 0.2858 | 3.3 |


### 3. EXTRAPOLATED beyond the measured range (predictions only)

N = 20, 50, 100 were never measured (the probe only built the four networks above). These rows are model-based predictions and must never be mixed with — or quoted as — measurements.

| N | agents | obs dim | share obs dim | critic 1st layer params | 1st-layer MAC/envstep | est. fwd ms/envstep | share-obs buffer GB |
|---|---|---|---|---|---|---|---|
| 20 | 40 | 243 | 9720 | 1,244,288 | 298,598,400 | 2.2589 | 26.08 |
| 50 | 100 | 603 | 60300 | 7,718,528 | 4,631,040,000 | 35.0333 | 404.478 |
| 100 | 200 | 1203 | 240600 | 30,796,928 | 36,956,160,000 | 279.5691 | 3227.773 |

### Closed-form check (computed in this script, not asserted)

Per row: `share_obs = 24N² + 6N`, `critic_params = 128·(24N²+6N) + 150145`, `critic_first_layer_params = 128·(share_obs + 1)`.

| quantity | recorded | closed form | match |
|---|---|---|---|
| N=2 share_obs_dim | 108 | 108 | OK |
| N=2 critic_params | 163,969 | 163,969 | OK |
| N=2 critic_first_layer | 13,952 | 13,952 | OK |
| N=3 share_obs_dim | 234 | 234 | OK |
| N=3 critic_params | 180,097 | 180,097 | OK |
| N=3 critic_first_layer | 30,080 | 30,080 | OK |
| N=5 share_obs_dim | 630 | 630 | OK |
| N=5 critic_params | 230,785 | 230,785 | OK |
| N=5 critic_first_layer | 80,768 | 80,768 | OK |
| N=10 share_obs_dim | 2,460 | 2,460 | OK |
| N=10 critic_params | 465,025 | 465,025 | OK |
| N=10 critic_first_layer | 315,008 | 315,008 | OK |
| N=20 share_obs_dim (extrapolated) | 9,720 | 9,720 | OK |
| N=20 critic_first_layer (extrapolated) | 1,244,288 | 1,244,288 | OK |
| N=50 share_obs_dim (extrapolated) | 60,300 | 60,300 | OK |
| N=50 critic_first_layer (extrapolated) | 7,718,528 | 7,718,528 | OK |
| N=100 share_obs_dim (extrapolated) | 240,600 | 240,600 | OK |
| N=100 critic_first_layer (extrapolated) | 30,796,928 | 30,796,928 | OK |

All closed-form checks passed: **yes**. Probe metadata: device `cuda:0`, effective G-MAC/s 132.19, batch threads 12.

## Computational scalability

Snapshot: `metrics/scaling_table.csv` (written 2026-10-07 17:51:53). `FPS` is the runner's own vectorised env-steps/s; `agent-steps/s = env-steps/s × total agents`.

| scale | variant | thr | FPS (env-steps/s) | env-steps/s per thread | agent-steps/s | agent-steps/s per thread | sec / vectorised step | sec / rollout episode (3000 steps) |
|---|---|---|---|---|---|---|---|---|
| 2v2 | noweapon | 4 | 77 | 19.25 | 308 | 77 | 0.05195 | 155.8 |
| 3v3 | noweapon | 8 | 125 | 15.62 | 750 | 93.8 | 0.064 | 192.0 |
| 3v3 | noweapon | 8 | 114 | 14.25 | 684 | 85.5 | 0.07018 | 210.5 |
| 5v5 | noweapon | 8 | 80 | 10.00 | 800 | 100 | 0.1 | 300.0 |
| 5v5 | noweapon | 10 | 82 | 8.20 | 820 | 82 | 0.12195 | 365.9 |
| 10v10 | noweapon | 20 | 68 | 3.40 | 1360 | 68 | 0.29412 | 882.4 |

Live campaign aggregate throughput at the `metrics/status.json` snapshot: **990 env-steps/s** across all live lanes.

## Failure list (summarised from `status/incidents.md`)

8 incidents recorded for this campaign (Computational scalability: 1, Other: 7). F1–F9 live in `docs/night_failures.md` and belong to the 2026-10-04 pilot; they are not re-listed here.

| id | title | category | detected | summary (symptom/cause excerpt) |
|---|---|---|---|---|
| F10 | CPU-cores column reported a physically impossible value | Other (measurement bug) | 2026-10-07, while reviewing the first `metrics/scaling_table.csv` | `peak_cpu_cores_host = 175.9` on every row of a 48-core box. |
| F11 | Representational-scalability columns were silently empty | Other (missing instrumentation) | 2026-10-07, same review | `local_obs_dim`, `share_obs_dim`, `actor_params`, `critic_params` were blank in `scaling_table.csv`, and `metrics/critic_scaling.json` did not exist. |
| F12 | Finished lanes were reported as still running | Other (instrumentation bug, inherited from the pilot) |  | `make_manifest.py` never registered a lane as finished. |
| F13 | Analysis scripts hardcoded the pilot's campaign path | Other (portability) |  | 11 copied files (7 Python, 4 shell) still pointed at `experiments/2026-10-04-night`, so any run in the new campaign would have silently produced the *pilot's* numbers. |
| F17 | the reachable step budget is quantised by thread count | Other (experiment-design trap) | 2026-10-07 ~17:20, when `f6m_official_1v1_vsbaseline_s1` ended cleanly at **5,994,000** instead of 6,000,000 — exactly below target, not short by accident. | the runner computes `episodes = num_env_steps // buffer_size // n_rollout_threads` (`runner/share_jsbsim_runner.py:72`, `runner/jsbsim_runner.py:41`), so the reachable total is `episodes × 3000 × threads`. With `num_e… |
| F16 | `/proc/stat` is unusable in this container; every CPU figure derived from it was wrong | Other (measurement bug — and the most consequential one found) | 2026-10-07 ~17:21, when adding a lane pushed the reported "cores busy" to 65.5 on a box whose quota is 48. A figure above the quota is impossible, so the instrument was suspect rather than the load. | the `/proc/stat` `cpu` aggregate, sampled every 4–5 s, returned busy deltas alternating between **0.0 cores and ~200 cores** while the container was demonstrably busy. 200 ≈ the **host's** 192 logical CPUs, not the co… |
| F15 | probe `--out` resolves against the repo root, not the invocation cwd | Other (portability trap) | 2026-10-07 05:03, by the first dry-run of `freeze.sh` — the non-fatal step runner surfaced it instead of aborting the freeze | `FileNotFoundError: [Errno 2] No such file or directory: 'metrics/critic_scaling.json'`, raised **after** the probe had printed its entire results table. Easy to miss: the table looks like success. |
| F14 | `1v1` ShootMissile lane is structurally ~2× slower, and will miss 6M | Computational scalability (NOT algorithmic) | 2026-10-07 03:37, from the first stable FPS readings | `f6m_official_1v1_shoot_hier_selfplay_s1` runs at 55 FPS where the sibling `1v1` lanes run at 104–120 FPS on identical thread counts. |

Live health flags at this snapshot: NaN ×0, Inf ×0, traceback ×0; lanes in status `failed`: 0.

## WHAT THIS DOES NOT SHOW

Known limitations; read this before quoting any number above.

1. **Single seed at most scales.** Only the scenarios below carry more than one seed so far; every other scenario is a single-seed result. A between-scale (or between-seed) difference smaller than the run-to-run seed spread is not interpretable, and this document performs no such comparison.
   - multi-seed so far: `3v3/scaling_noweapon/HierarchySelfplay`, `5v5/scaling_noweapon/HierarchySelfplay`
   - single-seed at this generation: `10v10/scaling_noweapon/HierarchySelfplay`, `1v1/NoWeapon/HierarchySelfplay`, `1v1/NoWeapon/Selfplay`, `1v1/NoWeapon/vsBaseline`, `1v1/ShootMissile/HierarchySelfplay`, `2v2/NoWeapon/HierarchySelfplay`, `2v2/scaling_noweapon/HierarchySelfplay`

2. **`n_rollout_threads` is a confound, not a detail.** The thread count differs across scales (forced by wall-clock: at a constant thread count 10v10 cannot reach 6M inside the window) and the PPO update batch size is `threads × 3000`, so batch size differs across scales too.
   - threads per scenario at this generation: `10v10/scaling_noweapon/HierarchySelfplay`: [20] thr (batch [60000]), `1v1/NoWeapon/HierarchySelfplay`: [3] thr (batch [9000]), `1v1/NoWeapon/Selfplay`: [3] thr (batch [9000]), `1v1/NoWeapon/vsBaseline`: [3] thr (batch [9000]), `1v1/ShootMissile/HierarchySelfplay`: [3] thr (batch [9000]), `2v2/NoWeapon/HierarchySelfplay`: [4] thr (batch [12000]), `2v2/scaling_noweapon/HierarchySelfplay`: [4] thr (batch [12000]), `3v3/scaling_noweapon/HierarchySelfplay`: [8] thr (batch [24000]), `5v5/scaling_noweapon/HierarchySelfplay`: [8, 10] thr (batch [24000, 30000])
   - **within-scenario difference across seeds**: `5v5/scaling_noweapon/HierarchySelfplay` — the seed comparison there is confounded by thread count as well.

3. **The 1v1 lanes cannot reach 6,000,000 by construction.** A 3-thread lane floors at 666 episodes, i.e. 5,994,000 of the nominal 6,000,000 (incident F17). Those lanes are reported as `completed_at_ceiling`, not as censored.
   - affected lanes at this generation: `f6m_official_1v1_hier_selfplay_s1`, `f6m_official_1v1_selfplay_s1`, `f6m_official_1v1_shoot_hier_selfplay_s1`, `f6m_official_1v1_vsbaseline_s1`

4. **The 1v1 ShootMissile lane runs with `--use-prior`, which roughly halves throughput** (incident F14, category `Computational scalability` — not algorithmic). Its lower FPS is a property of the official code path, not an algorithmic finding.
   - current FPS: ShootMissile 61 vs sibling 3-thread 1v1 lanes 104, 122, 83 env-steps/s (see inventory).

5. **6M is a budget reduction, not a convergence result.** The official configuration trains for 1e8 steps; this campaign runs 6,000,000 (6% of that). Final rewards are an intermediate-training-state snapshot and must not be presented as converged performance.

Also, by policy:

- `reward_per_enemy` is defined only for the NoWeapon family (PostureReward sums over agents); it is withheld for ShootMissile rows.
- The 2026-10-04 pilot is a separate series and is excluded from this document.
- Tables built from the analysis CSVs are snapshots of those files (mtimes above); only the inventory is the live view. Nothing here is averaged across seeds, fitted, or significance-tested.
- This document is a data record, not an analysis; interpret it with the hand-written report.

## Related artefacts (not embedded here)

- `metrics/scaling_table.csv` — machine-readable version of the scaling table above, and wider (obs dims, parameter counts, CPU/RAM peaks).
- `metrics/normalized_scaling.csv` — per-episode reward and reward/enemy for the scaling family.
- `metrics/sample_efficiency.csv` — reward / reward-per-enemy at fixed budgets up to 6M.
- `metrics/equal_sample.csv`, `metrics/equal_wallclock.csv` — the raw checkpoint tables with per-cell status and bracket.
- `metrics/resources.csv`, `metrics/throughput_history.csv`, `system/system_samples_v2.csv` — resource/throughput time series (the v1 sampler file is unreliably CPU-scaled; see incident F16).
- `figures/` — plots regenerated by `scripts/make_figures.py`.
- `docs/formal_repro_scaling_2026-10-07_08.md` — the hand-written report this document is the safety net for.

