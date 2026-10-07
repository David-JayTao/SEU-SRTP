# Formal-6M monitor  2026-10-07 17:53:59 

**Aggregate throughput: 990 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,660,000 | 61.0% | 68 | 9.56 | -7.014 | -177.582 | 16.302 | 42.85 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,344,000 | 72.4% | 80 | 5.75 | -72.315 | -71.069 | 4.881 | 73.70 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,176,000 | 69.6% | 77 | 6.58 | 24.139 | -50.310 | 0.088 | 2.57 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,068,000 | 67.8% | 75 | 7.16 | 24.117 | 32.667 | 0.080 | 2.95 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,535,000 | 92.2% | 104 | 1.24 | 13.201 | 34.507 | 4.432 | 85.32 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,222,000 | 53.7% | 61 | 12.65 | -76.169 | 0.012 | 42.201 | 95.13 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,365,000 | 72.8% | 83 | 5.47 | -102.027 | -311.689 | 20.960 | 616.28 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 150,000 | 2.5% | 82 | 19.82 | -8.298 | -78.044 | 16.565 | 22.27 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 192,000 | 3.2% | 113 | 14.28 | -5.065 | -72.597 | 4.024 | 13.80 | ok |

- load1 **72.44**  container CPU **38.85 / 48.0 cores** (80.9% of quota, throttled 0.3475% of periods)  train procs **69**, **36.04 GB** RSS
- RAM used 86.5 GB / 1007.5 GB (avail 907.5 GB)
- GPU0: util 45%, VRAM 2420 MiB
- GPU1: util 7%, VRAM 1209 MiB
- GPU2: util 10%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_off2v2, f6m_watch
