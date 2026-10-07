# Formal-6M monitor  2026-10-07 18:09:13 

**Aggregate throughput: 987 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,720,000 | 62.0% | 67 | 9.45 | 0.677 | -177.582 | 10.269 | 52.59 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,392,000 | 73.2% | 80 | 5.58 | -57.229 | -81.914 | 6.302 | 58.48 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,248,000 | 70.8% | 77 | 6.32 | 23.749 | -55.534 | 0.171 | 8.45 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,140,000 | 69.0% | 75 | 6.89 | 24.622 | 33.715 | 0.067 | 2.20 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,643,000 | 94.0% | 104 | 0.95 | 24.820 | 34.234 | 0.836 | 34.89 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,276,000 | 54.6% | 61 | 12.4 | -41.619 | 0.305 | 19.091 | 8.66 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,446,000 | 74.1% | 83 | 5.2 | -48.674 | -151.952 | 11.461 | 358.24 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 210,000 | 3.5% | 80 | 20.1 | -7.761 | -161.544 | 14.900 | 22.18 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 288,000 | 4.8% | 113 | 14.04 | -3.566 | -7.136 | 2.837 | 20.13 | ok |

- load1 **50.14**  container CPU **44.56 / 48.0 cores** (92.8% of quota, throttled 0.588% of periods)  train procs **69**, **36.02 GB** RSS
- RAM used 65.7 GB / 1007.5 GB (avail 929.4 GB)
- GPU0: util 57%, VRAM 2865 MiB
- GPU1: util 7%, VRAM 1209 MiB
- GPU2: util 12%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_off2v2, f6m_watch
