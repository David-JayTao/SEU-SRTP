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

