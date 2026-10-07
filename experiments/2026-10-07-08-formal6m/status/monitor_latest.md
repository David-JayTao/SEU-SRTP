# Formal-6M monitor  2026-10-07 17:23:30 

**Aggregate throughput: 794 env-steps/s** across 9 jobs (56 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 3,540,000 | 59.0% | 68 | 10.05 | -1.158 | -174.117 | 12.044 | 74.15 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 4,200,000 | 70.0% | 80 | 6.25 | -75.802 | -60.840 | 3.907 | 73.11 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **STALL 71.5m** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 4,032,000 | 67.2% | 77 | 7.1 | -0.131 | 3.308 | 1.965 | 50.10 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 3,924,000 | 65.4% | 75 | 7.69 | 24.254 | 32.489 | 0.098 | 5.29 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,337,000 | 89.0% | 104 | 1.77 | 24.369 | 37.459 | 0.970 | 54.73 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **STALL 37.7m** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 3,096,000 | 51.6% | 61 | 13.22 | -21.811 | 0.063 | 0.852 | 6.67 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 4,194,000 | 69.9% | 82 | 6.12 | -74.660 | -170.298 | 16.296 | 272.94 | ok |

- load1 **76.25**  container CPU **39.11 / 48.0 cores** (81.5% of quota, throttled 0.0223% of periods)  train procs **59**, **31.03 GB** RSS
- RAM used 82.1 GB / 1007.5 GB (avail 913.0 GB)
- GPU0: util 42%, VRAM 1764 MiB
- GPU1: util 9%, VRAM 1207 MiB
- GPU2: util 5%, VRAM 2118 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_5v5, f6m_5v5s1, f6m_off2v2, f6m_watch
