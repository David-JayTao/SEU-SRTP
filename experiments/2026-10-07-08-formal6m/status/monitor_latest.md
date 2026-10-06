# Formal-6M monitor  2026-10-07 03:42:41 

**Aggregate throughput: 799 env-steps/s** across 9 jobs (56 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 180,000 | 3.0% | 67 | 24.13 | -17.680 | -93.849 | 74.679 | 47.42 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 216,000 | 3.6% | 81 | 19.84 | -6.085 | -11.185 | 15.537 | 22.16 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 360,000 | 6.0% | 128 | 12.24 | -2.306 | -5.313 | 2.654 | 11.90 | ok |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 228,000 | 3.8% | 79 | 20.3 | -1.732 | 24.168 | 0.529 | 10.25 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 216,000 | 3.6% | 78 | 20.6 | 1.566 | -380.363 | 0.659 | 18.58 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 207,000 | 3.5% | 107 | 15.04 | -157.963 | -317.961 | 504.982 | 286.11 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 225,000 | 3.8% | 119 | 13.48 | -213.338 | — | 705.587 | 255.79 | ok |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 81,000 | 1.4% | 55 | 29.89 | -101.678 | -434.710 | 149.914 | 47.22 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 126,000 | 2.1% | 85 | 19.2 | 7.494 | -146.426 | 19.114 | 83.11 | ok |

- load1 **39.36**  cpu_busy **22%** (of the host's 192 logical CPUs; multiply by 4 to read as a fraction of the 48-core quota)  train procs **58** using **2765.7%** CPU, **30.43 GB** RSS
- RAM used 49.0 GB / 1007.5 GB (avail 947.8 GB)
- GPU0: util 43%, VRAM 2358 MiB
- GPU1: util 25%, VRAM 1810 MiB
- GPU2: util 2%, VRAM 1619 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_5v5, f6m_off2v2, f6m_watch
