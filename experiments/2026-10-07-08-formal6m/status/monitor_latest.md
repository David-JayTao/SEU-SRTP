# Formal-6M monitor  2026-10-07 04:53:07 

**Aggregate throughput: 799 env-steps/s** across 9 jobs (56 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 540,000 | 9.0% | 76 | 19.96 | -17.613 | -155.668 | 70.401 | 47.24 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 576,000 | 9.6% | 82 | 18.37 | -6.183 | -10.967 | 7.768 | 31.05 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 888,000 | 14.8% | 127 | 11.18 | 32.999 | 42.143 | 0.980 | 22.50 | ok |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 540,000 | 9.0% | 77 | 19.7 | -2.167 | -3.713 | 0.346 | 8.75 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 540,000 | 9.0% | 76 | 19.96 | 4.258 | -354.031 | 0.375 | 8.56 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 639,000 | 10.7% | 103 | 14.46 | -182.687 | -91.190 | 165.938 | 447.06 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 738,000 | 12.3% | 120 | 12.18 | 7.011 | — | 5.227 | 92.64 | ok |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 315,000 | 5.2% | 56 | 28.2 | -63.423 | -434.710 | 103.339 | 32.94 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 468,000 | 7.8% | 82 | 18.74 | 37.446 | 35.469 | 7.852 | 118.43 | ok |

- load1 **38.21**  cpu_busy **15%** (of the host's 192 logical CPUs; multiply by 4 to read as a fraction of the 48-core quota)  train procs **58** using **2826.4%** CPU, **30.43 GB** RSS
- RAM used 49.2 GB / 1007.5 GB (avail 947.6 GB)
- GPU0: util 55%, VRAM 2386 MiB
- GPU1: util 21%, VRAM 1866 MiB
- GPU2: util 3%, VRAM 1671 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_5v5, f6m_off2v2, f6m_watch
