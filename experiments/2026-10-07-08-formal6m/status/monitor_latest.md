# Formal-6M monitor  2026-10-07 18:44:46 

**Aggregate throughput: 992 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,840,000 | 64.0% | 67 | 8.96 | -13.076 | -182.417 | 21.093 | 54.09 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,536,000 | 75.6% | 80 | 5.08 | -37.881 | -150.283 | 3.562 | 58.91 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,416,000 | 73.6% | 77 | 5.71 | 23.288 | -59.463 | 0.125 | 6.28 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,296,000 | 71.6% | 75 | 6.31 | 23.190 | 31.095 | 0.083 | 4.33 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,868,000 | 97.8% | 104 | 0.35 | 23.399 | 36.727 | 0.750 | 36.63 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,411,000 | 56.9% | 61 | 11.79 | -15.273 | -0.302 | 0.380 | 3.09 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,635,000 | 77.2% | 83 | 4.57 | 24.808 | 30.155 | 1.592 | 60.50 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 390,000 | 6.5% | 82 | 19.0 | -5.613 | 16.628 | 11.698 | 19.57 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 552,000 | 9.2% | 116 | 13.05 | 1.327 | 40.641 | 1.161 | 12.91 | ok |

- load1 **54.76**  container CPU **43.49 / 48.0 cores** (90.6% of quota, throttled 1.2787% of periods)  train procs **69**, **36.02 GB** RSS
- RAM used 69.6 GB / 1007.5 GB (avail 925.5 GB)
- GPU0: util 40%, VRAM 2865 MiB
- GPU1: util 7%, VRAM 1211 MiB
- GPU2: util 9%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_off2v2, f6m_watch
