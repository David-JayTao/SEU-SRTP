# Formal-6M monitor  2026-10-07 19:01:29 

**Aggregate throughput: 992 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,900,000 | 65.0% | 67 | 8.71 | -13.073 | -182.417 | 16.991 | 41.10 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,632,000 | 77.2% | 79 | 4.81 | 48.254 | -190.812 | 1.691 | 65.25 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,488,000 | 74.8% | 77 | 5.45 | 23.639 | -145.324 | 0.113 | 3.74 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,380,000 | 73.0% | 75 | 6.0 | 2.207 | 26.748 | 0.199 | 5.26 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,976,000 | 99.6% | 104 | 0.06 | 31.100 | 33.804 | 18.774 | 119.73 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,483,000 | 58.0% | 61 | 11.46 | -17.671 | 0.178 | 0.471 | 1.82 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,716,000 | 78.6% | 83 | 4.3 | 45.685 | 31.238 | 3.464 | 107.72 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 480,000 | 8.0% | 82 | 18.7 | -3.715 | 1.008 | 9.361 | 26.42 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 672,000 | 11.2% | 117 | 12.65 | 5.787 | 29.737 | 0.798 | 14.09 | ok |

- load1 **53.4**  container CPU **26.46 / 48.0 cores** (55.1% of quota, throttled 1.4906% of periods)  train procs **70**, **36.03 GB** RSS
- RAM used 69.9 GB / 1007.5 GB (avail 924.2 GB)
- GPU0: util 57%, VRAM 2985 MiB
- GPU1: util 3%, VRAM 1211 MiB
- GPU2: util 15%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch
