# Freeze 20261008_092029 — step outcomes

- auto_results: ok
- collect_metrics: ok
- critic_probe: ok
- env_bench: FAILED(2)
- equal_sample: ok
- equal_wallclock: ok
- figures: ok
- fill_report: ok
- make_manifest: ok
- normalized: ok
- obs_cost_profile: ok
- offline_eval_f6m_10v10_noweapon_s0: FAILED(124)
- offline_eval_f6m_2v2_noweapon_s0: ok
- offline_eval_f6m_3v3_noweapon_s0: ok
- offline_eval_f6m_5v5_noweapon_s0: ok
- report_tables: ok
- sample_efficiency: ok
- scaling_table: ok

## final per-job state
# Formal-6M monitor  2026-10-08 09:20:30 

**Aggregate throughput: 1426 env-steps/s** across 3 live jobs (38 rollout threads; 11 lanes completed and release their threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 6,000,000 | 100.0% | 65 | — | 0.392 | -87.864 | 3.787 | 55.16 | **complete** |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 6,000,000 | 100.0% | 77 | — | 21.992 | -99.026 | 0.160 | 8.17 | **complete** |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 6,000,000 | 100.0% | 75 | — | 23.128 | 31.315 | 0.072 | 3.07 | **complete** |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 5,994,000 | 99.9% | 61 | 0.03 | -7.771 | 18.354 | 0.815 | 3.98 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 5,400,000 | 90.0% | 93 | 1.79 | 34.019 | -2.814 | 0.657 | 14.74 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 6,000,000 | 100.0% | 124 | — | 34.473 | 47.648 | 0.120 | 6.23 | **complete** |
| f6m_official_heading_s5 | o_heading | 4 | 6,000,000 | 100.0% | 275 | — | 320.474 | — | 8.942 | 119.57 | **complete** |
| f6m_10v10_noweapon_s1 | 10v10 s1 | 20 | 1,860,000 | 31.0% | 64 | 17.97 | 3.287 | -30.863 | 33.364 | 45.19 | ok |
| f6m_5v5_noweapon_s2 | 5v5 s2 | 8 | 2,304,000 | 38.4% | 79 | 13.0 | 7.951 | -58.163 | 0.983 | 22.71 | ok |

- load1 **34.09**  container CPU **25.47 / 48.0 cores** (53.1% of quota, throttled 6.0215% of periods)  train procs **44**, **25.66 GB** RSS
- RAM used 43.4 GB / 1007.5 GB (avail 951.0 GB)
- GPU0: util 1%, VRAM 666 MiB
- GPU1: util 0%, VRAM 1046 MiB
- GPU2: util 1%, VRAM 722 MiB
- tmux: f6m_10v10, f6m_10v10s1, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_5v5s2, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch
