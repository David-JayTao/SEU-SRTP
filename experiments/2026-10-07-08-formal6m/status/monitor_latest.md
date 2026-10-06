# Formal-6M monitor  2026-10-07 03:02:27 

**Aggregate throughput: 385 env-steps/s** across 5 jobs (44 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 0 | 0.0% | — | — | — | — | — | — | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 24,000 | 0.4% | 87 | 19.08 | -9.117 | -120.429 | 14.826 | 22.61 | ok |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 48,000 | 0.8% | 131 | 12.62 | -5.421 | -121.863 | 5.921 | 11.86 | ok |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 36,000 | 0.6% | 86 | 19.26 | -3.487 | -3.003 | 2.145 | 8.01 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 36,000 | 0.6% | 81 | 20.45 | -3.527 | -3.763 | 2.132 | 7.37 | ok |

- load1 **43.5**  cpu_busy **20%**  train procs **54** using **2936.1%** CPU, **27.37 GB** RSS
- RAM used 44.2 GB / 1007.5 GB (avail 952.1 GB)
- GPU0: util 5%, VRAM 1199 MiB
- GPU1: util 3%, VRAM 1205 MiB
- GPU2: util 1%, VRAM 464 MiB
- tmux: f6m_10v10, f6m_2v2, f6m_3v3, f6m_5v5, f6m_off2v2, f6m_watch
