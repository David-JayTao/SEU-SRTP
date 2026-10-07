# Formal-6M monitor  2026-10-08 01:12:42 

**Aggregate throughput: 1279 env-steps/s** across 12 jobs (78 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 5,340,000 | 89.0% | 66 | 2.78 | 0.579 | -79.138 | 4.550 | 53.51 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 6,000,000 | 100.0% | 77 | — | 21.992 | -99.026 | 0.160 | 8.17 | **complete** |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 6,000,000 | 100.0% | 75 | — | 23.128 | 31.315 | 0.072 | 3.07 | **complete** |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 4,842,000 | 80.7% | 61 | 5.27 | -15.282 | 0.173 | 0.748 | 2.57 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 2,580,000 | 43.0% | 91 | 10.44 | 31.030 | -30.764 | 0.656 | 23.14 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 3,408,000 | 56.8% | 121 | 5.95 | 11.416 | 51.877 | 0.363 | 14.69 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 6,000,000 | 100.0% | 275 | — | 320.474 | — | 8.942 | 119.57 | **complete** |

- load1 **34.47**  container CPU **30.8 / 48.0 cores** (64.2% of quota, throttled 3.7164% of periods)  train procs **45**, **25.23 GB** RSS
- RAM used 50.7 GB / 1007.5 GB (avail 943.1 GB)
- GPU0: util 3%, VRAM 660 MiB
- GPU1: util 0%, VRAM 1 MiB
- GPU2: util 3%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch
