# Formal-6M monitor  2026-10-08 03:00:53 

**Aggregate throughput: 1413 env-steps/s** across 6 live jobs (69 rollout threads; 8 lanes completed and release their threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 5,700,000 | 95.0% | 66 | 1.26 | 25.489 | -143.331 | 2.482 | 38.10 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 6,000,000 | 100.0% | 77 | — | 21.992 | -99.026 | 0.160 | 8.17 | **complete** |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 6,000,000 | 100.0% | 75 | — | 23.128 | 31.315 | 0.072 | 3.07 | **complete** |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 5,247,000 | 87.5% | 61 | 3.43 | -7.105 | 18.003 | 0.861 | 4.69 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 3,150,000 | 52.5% | 91 | 8.7 | 16.815 | 14.723 | 0.802 | 31.56 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 4,200,000 | 70.0% | 122 | 4.1 | 36.395 | 47.702 | 0.132 | 7.94 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 6,000,000 | 100.0% | 275 | — | 320.474 | — | 8.942 | 119.57 | **complete** |
| f6m_10v10_noweapon_s1 | 10v10 s1 | 20 | 360,000 | 6.0% | 59 | 26.55 | -17.542 | -149.799 | 67.443 | 48.00 | ok |
| f6m_5v5_noweapon_s2 | 5v5 s2 | 8 | 456,000 | 7.6% | 74 | 20.81 | -8.902 | -178.151 | 9.097 | 21.77 | ok |

- load1 **52.96**  container CPU **44.68 / 48.0 cores** (93.1% of quota, throttled 5.9268% of periods)  train procs **77**, **45.25 GB** RSS
- RAM used 60.8 GB / 1007.5 GB (avail 932.9 GB)
- GPU0: util 3%, VRAM 1321 MiB
- GPU1: util 1%, VRAM 1046 MiB
- GPU2: util 3%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_10v10s1, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_5v5s2, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch
