# Formal-6M monitor  2026-10-07 05:04:53 

**Aggregate throughput: 798 env-steps/s** across 9 jobs (56 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 540,000 | 9.0% | 76 | 19.96 | -17.613 | -55.891 | 70.401 | 47.24 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 624,000 | 10.4% | 82 | 18.21 | -6.661 | -12.025 | 7.255 | 24.17 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 984,000 | 16.4% | 127 | 10.97 | 26.641 | 17.553 | 0.918 | 10.95 | ok |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 600,000 | 10.0% | 77 | 19.48 | 20.485 | -0.928 | 0.375 | 10.07 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 588,000 | 9.8% | 76 | 19.78 | 10.988 | 29.017 | 0.387 | 7.74 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 711,000 | 11.8% | 103 | 14.26 | -79.477 | -278.469 | 34.649 | 341.51 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 828,000 | 13.8% | 120 | 11.97 | -32.710 | — | 17.844 | 109.90 | ok |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 360,000 | 6.0% | 56 | 27.98 | -21.936 | -434.719 | 5.330 | 5.58 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 522,000 | 8.7% | 81 | 18.79 | 10.441 | 31.438 | 11.410 | 175.28 | ok |

- load1 **43.68**  cpu_busy **24%** (of the host's 192 logical CPUs; multiply by 4 to read as a fraction of the 48-core quota)  train procs **58** using **2819.5%** CPU, **30.45 GB** RSS
- RAM used 51.4 GB / 1007.5 GB (avail 944.8 GB)
- GPU0: util 46%, VRAM 2386 MiB
- GPU1: util 12%, VRAM 1866 MiB
- GPU2: util 7%, VRAM 1671 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_5v5, f6m_off2v2, f6m_watch
