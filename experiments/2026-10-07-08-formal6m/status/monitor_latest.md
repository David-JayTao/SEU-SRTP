# Formal-6M monitor  2026-10-07 17:31:06 

**Aggregate throughput: 1011 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,600,000 | 60.0% | 68 | 9.8 | -6.951 | -174.117 | 16.066 | 88.63 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,248,000 | 70.8% | 80 | 6.08 | -56.212 | -35.957 | 2.315 | 39.87 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,068,000 | 67.8% | 77 | 6.97 | 21.930 | 32.517 | 0.183 | 8.05 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 3,960,000 | 66.0% | 75 | 7.56 | 23.181 | 30.643 | 0.153 | 2.33 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,391,000 | 89.8% | 104 | 1.63 | 30.038 | 29.187 | 6.845 | 108.46 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,132,000 | 52.2% | 61 | 13.06 | -14.570 | 0.064 | 0.688 | 2.75 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,239,000 | 70.7% | 82 | 5.97 | -139.029 | -167.837 | 30.137 | 425.15 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 30,000 | 0.5% | 95 | 17.46 | -9.054 | 0.968 | 13.079 | 22.93 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 24,000 | 0.4% | 122 | 13.61 | -5.436 | -7.225 | 4.247 | 11.80 | ok |

- load1 **72.91**  container CPU **43.13 / 48.0 cores** (89.9% of quota, throttled 0.0783% of periods)  train procs **69**, **36.01 GB** RSS
- RAM used 85.2 GB / 1007.5 GB (avail 909.9 GB)
- GPU0: util 41%, VRAM 2420 MiB
- GPU1: util 1%, VRAM 1207 MiB
- GPU2: util 14%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_off2v2, f6m_watch
