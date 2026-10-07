# Formal-6M monitor  2026-10-07 17:59:04 

**Aggregate throughput: 990 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,660,000 | 61.0% | 68 | 9.56 | -7.014 | -177.582 | 16.302 | 42.85 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,344,000 | 72.4% | 80 | 5.75 | -72.315 | -88.545 | 4.881 | 73.70 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,200,000 | 70.0% | 77 | 6.49 | 18.556 | 5.864 | 0.207 | 4.67 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,092,000 | 68.2% | 75 | 7.07 | 10.344 | 18.566 | 0.209 | 3.96 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,571,000 | 92.8% | 104 | 1.15 | 34.937 | 33.802 | 2.601 | 60.49 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,240,000 | 54.0% | 61 | 12.57 | -61.383 | 0.230 | 40.341 | 18.11 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,392,000 | 73.2% | 83 | 5.38 | -333.010 | -346.336 | 44.078 | 1274.35 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 180,000 | 3.0% | 80 | 20.21 | -8.258 | -78.044 | 16.581 | 23.21 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 216,000 | 3.6% | 115 | 13.97 | -5.358 | -30.110 | 3.826 | 10.86 | ok |

- load1 **72.35**  container CPU **41.26 / 48.0 cores** (86.0% of quota, throttled 0.4049% of periods)  train procs **69**, **36.04 GB** RSS
- RAM used 87.1 GB / 1007.5 GB (avail 907.2 GB)
- GPU0: util 48%, VRAM 2420 MiB
- GPU1: util 9%, VRAM 1209 MiB
- GPU2: util 12%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_off2v2, f6m_watch
