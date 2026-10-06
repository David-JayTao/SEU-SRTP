# Formal-6M monitor  2026-10-07 03:19:31 

**Aggregate throughput: 668 env-steps/s** across 9 jobs (56 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 60,000 | 1.0% | 70 | 23.57 | -17.621 | -36.671 | 63.635 | 59.75 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 120,000 | 2.0% | 83 | 19.68 | -8.937 | -10.885 | 17.257 | 23.30 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 192,000 | 3.2% | 130 | 12.41 | -2.993 | -54.062 | 4.260 | 11.16 | ok |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 120,000 | 2.0% | 81 | 20.16 | -0.530 | -117.972 | 1.171 | 7.49 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 108,000 | 1.8% | 79 | 20.72 | -2.841 | -79.054 | 1.311 | 8.43 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 54,000 | 0.9% | 107 | 15.44 | -155.711 | 8.461 | 765.437 | 211.68 | ok |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 63,000 | 1.1% | 118 | 13.98 | -209.326 | — | 987.968 | 245.06 | ok |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 0 | 0.0% | — | — | — | — | — | — | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 0 | 0.0% | — | — | — | — | — | — | ok |

- load1 **44.02**  cpu_busy **23%**  train procs **58** using **2780.7%** CPU, **30.43 GB** RSS
- RAM used 51.9 GB / 1007.5 GB (avail 944.3 GB)
- GPU0: util 39%, VRAM 2242 MiB
- GPU1: util 8%, VRAM 1786 MiB
- GPU2: util 2%, VRAM 1493 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_5v5, f6m_off2v2, f6m_watch
