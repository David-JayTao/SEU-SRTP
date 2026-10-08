### snapshot 2026-10-07 21:00
# Formal-6M monitor  2026-10-07 21:01:43 

**Aggregate throughput: 1271 env-steps/s** across 12 jobs (78 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 4,320,000 | 72.0% | 66 | 7.07 | -0.150 | -34.074 | 6.229 | 44.17 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 5,184,000 | 86.4% | 79 | 2.87 | 30.456 | -61.483 | 0.758 | 11.64 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 5,052,000 | 84.2% | 77 | 3.42 | 24.692 | -12.768 | 0.114 | 4.90 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 4,920,000 | 82.0% | 75 | 4.0 | 19.587 | 7.430 | 0.448 | 10.26 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,924,000 | 65.4% | 61 | 9.45 | -54.206 | 0.133 | 30.775 | 36.26 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,310,000 | 88.5% | 83 | 2.31 | -59.148 | -401.628 | 9.315 | 252.93 | ok |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 1,170,000 | 19.5% | 89 | 15.07 | 6.211 | 42.159 | 2.314 | 25.94 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 1,512,000 | 25.2% | 118 | 10.56 | 4.315 | 46.352 | 0.436 | 10.68 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 1,980,000 | 33.0% | 272 | 4.11 | 168.262 | — | 6.775 | 119.75 | ok |

- load1 **47.87**  container CPU **42.8 / 48.0 cores** (89.2% of quota, throttled 2.6384% of periods)  train procs **69**, **36.05 GB** RSS
- RAM used 58.8 GB / 1007.5 GB (avail 938.5 GB)
- GPU0: util 41%, VRAM 2426 MiB
- GPU1: util 10%, VRAM 1211 MiB
- GPU2: util 10%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch

### snapshot 2026-10-08 00:00
# Formal-6M monitor  2026-10-08 00:01:49 

**Aggregate throughput: 1277 env-steps/s** across 12 jobs (78 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 4,980,000 | 83.0% | 66 | 4.29 | -0.355 | -133.353 | 4.400 | 37.18 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 5,892,000 | 98.2% | 77 | 0.39 | 24.063 | 32.704 | 0.085 | 3.02 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 5,748,000 | 95.8% | 75 | 0.93 | 24.635 | 30.189 | 0.073 | 3.17 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 4,572,000 | 76.2% | 61 | 6.5 | -116.094 | 0.146 | 64.905 | 464.07 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 2,190,000 | 36.5% | 91 | 11.63 | 14.674 | 48.219 | 0.636 | 16.31 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 2,856,000 | 47.6% | 120 | 7.28 | 35.694 | 47.507 | 0.194 | 11.08 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 4,956,000 | 82.6% | 274 | 1.06 | 266.548 | — | 5.685 | 65.95 | ok |

- load1 **51.28**  container CPU **34.07 / 48.0 cores** (71.0% of quota, throttled 3.9232% of periods)  train procs **58**, **31.2 GB** RSS
- RAM used 58.4 GB / 1007.5 GB (avail 935.3 GB)
- GPU0: util 34%, VRAM 1882 MiB
- GPU1: util 1%, VRAM 546 MiB
- GPU2: util 14%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch

### snapshot 2026-10-08 03:00
# Formal-6M monitor  2026-10-08 03:02:07 

**Aggregate throughput: 1412 env-steps/s** across 6 live jobs (69 rollout threads; 8 lanes completed and release their threads)

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
| f6m_5v5_noweapon_s2 | 5v5 s2 | 8 | 480,000 | 8.0% | 73 | 21.0 | -8.777 | -178.151 | 7.722 | 18.81 | ok |

- load1 **54.43**  container CPU **44.37 / 48.0 cores** (92.4% of quota, throttled 5.9695% of periods)  train procs **77**, **45.71 GB** RSS
- RAM used 61.2 GB / 1007.5 GB (avail 932.6 GB)
- GPU0: util 4%, VRAM 1321 MiB
- GPU1: util 0%, VRAM 1046 MiB
- GPU2: util 3%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_10v10s1, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_5v5s2, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch

### snapshot 2026-10-08 06:00
# Formal-6M monitor  2026-10-08 06:01:20 

**Aggregate throughput: 1419 env-steps/s** across 5 live jobs (49 rollout threads; 9 lanes completed and release their threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 6,000,000 | 100.0% | 65 | — | 0.392 | -87.864 | 3.787 | 55.16 | **complete** |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 6,000,000 | 100.0% | 77 | — | 21.992 | -99.026 | 0.160 | 8.17 | **complete** |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 6,000,000 | 100.0% | 75 | — | 23.128 | 31.315 | 0.072 | 3.07 | **complete** |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 5,931,000 | 98.8% | 61 | 0.31 | -8.778 | 18.212 | 0.730 | 3.79 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 4,170,000 | 69.5% | 91 | 5.59 | 54.962 | 68.700 | 0.477 | 15.83 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 5,616,000 | 93.6% | 124 | 0.86 | 34.411 | 48.106 | 0.139 | 6.53 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 6,000,000 | 100.0% | 275 | — | 320.474 | — | 8.942 | 119.57 | **complete** |
| f6m_10v10_noweapon_s1 | 10v10 s1 | 20 | 1,020,000 | 17.0% | 61 | 22.68 | -11.843 | -218.319 | 55.365 | 47.64 | ok |
| f6m_5v5_noweapon_s2 | 5v5 s2 | 8 | 1,320,000 | 22.0% | 77 | 16.88 | 3.292 | -33.995 | 1.736 | 57.03 | ok |

- load1 **44.87**  container CPU **33.32 / 48.0 cores** (69.4% of quota, throttled 6.7555% of periods)  train procs **55**, **30.08 GB** RSS
- RAM used 51.1 GB / 1007.5 GB (avail 942.7 GB)
- GPU0: util 3%, VRAM 1321 MiB
- GPU1: util 0%, VRAM 1046 MiB
- GPU2: util 5%, VRAM 1347 MiB
- tmux: f6m_10v10, f6m_10v10s1, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_5v5s2, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch

### snapshot 2026-10-08 08:30
# Formal-6M monitor  2026-10-08 08:31:27 

**Aggregate throughput: 1424 env-steps/s** across 3 live jobs (38 rollout threads; 11 lanes completed and release their threads)

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
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 5,100,000 | 85.0% | 93 | 2.69 | 13.869 | 29.219 | 0.481 | 11.61 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 6,000,000 | 100.0% | 124 | — | 34.473 | 47.648 | 0.120 | 6.23 | **complete** |
| f6m_official_heading_s5 | o_heading | 4 | 6,000,000 | 100.0% | 275 | — | 320.474 | — | 8.942 | 119.57 | **complete** |
| f6m_10v10_noweapon_s1 | 10v10 s1 | 20 | 1,620,000 | 27.0% | 63 | 19.31 | 7.378 | 0.604 | 39.692 | 57.68 | ok |
| f6m_5v5_noweapon_s2 | 5v5 s2 | 8 | 2,064,000 | 34.4% | 78 | 14.02 | 7.446 | -1.979 | 1.150 | 26.15 | ok |

- load1 **28.64**  container CPU **25.36 / 48.0 cores** (52.8% of quota, throttled 6.1871% of periods)  train procs **44**, **25.65 GB** RSS
- RAM used 43.6 GB / 1007.5 GB (avail 950.8 GB)
- GPU0: util 1%, VRAM 666 MiB
- GPU1: util 1%, VRAM 1046 MiB
- GPU2: util 1%, VRAM 722 MiB
- tmux: f6m_10v10, f6m_10v10s1, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_5v5s2, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch

