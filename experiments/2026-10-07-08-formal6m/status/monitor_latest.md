# Formal-6M monitor  2026-10-07 17:26:58 

**Aggregate throughput: 889 env-steps/s** across 11 jobs (74 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,540,000 | 59.0% | 68 | 10.05 | -1.158 | -174.117 | 12.044 | 74.15 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,224,000 | 70.4% | 80 | 6.17 | -58.625 | -60.840 | 3.066 | 49.16 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,044,000 | 67.4% | 77 | 7.06 | 11.719 | 32.029 | 0.355 | 11.13 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 3,936,000 | 65.6% | 75 | 7.64 | 24.037 | 29.963 | 0.105 | 6.44 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,364,000 | 89.4% | 104 | 1.7 | 28.180 | 33.136 | 1.023 | 59.61 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,114,000 | 51.9% | 61 | 13.14 | -18.074 | 0.062 | 0.733 | 2.74 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,212,000 | 70.2% | 82 | 6.06 | -3.317 | -511.879 | 7.206 | 221.35 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 30,000 | 0.5% | 95 | 17.46 | -9.054 | — | 13.079 | 22.93 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 0 | 0.0% | — | — | — | — | — | — | ok |

- load1 **65.65**  container CPU **37.03 / 48.0 cores** (77.1% of quota, throttled 0.0357% of periods)  train procs **69**, **35.65 GB** RSS
- RAM used 85.4 GB / 1007.5 GB (avail 909.7 GB)
- GPU0: util 53%, VRAM 2212 MiB
- GPU1: util 11%, VRAM 1207 MiB
- GPU2: util 6%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_off2v2, f6m_watch
