# Freeze 20261008_000047 — step outcomes

- auto_results: ok
- collect_metrics: ok
- critic_probe: ok
- equal_sample: ok
- equal_wallclock: ok
- figures: ok
- fill_report: ok
- make_manifest: ok
- normalized: ok
- report_tables: ok
- sample_efficiency: ok
- scaling_table: ok

## final per-job state
# Formal-6M monitor  2026-10-08 00:00:47 

**Aggregate throughput: 1277 env-steps/s** across 12 jobs (78 rollout threads)

| experiment | scale | thr | steps | % | FPS | ETA h | reward | eval | v_loss | critic_gn | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f6m_10v10_noweapon_s0 | 10v10 | 20 | 4,980,000 | 83.0% | 66 | 4.29 | -0.355 | -133.353 | 4.400 | 37.18 | ok |
| f6m_5v5_noweapon_s0 | 5v5 | 8 | 6,000,000 | 100.0% | 79 | — | 39.786 | -222.715 | 0.776 | 20.83 | **complete** |
| f6m_3v3_noweapon_s0 | 3v3 | 8 | 6,000,000 | 100.0% | 125 | — | 35.932 | 47.839 | 0.178 | 7.31 | **complete** |
| f6m_2v2_noweapon_s0 | 2v2 | 4 | 5,892,000 | 98.2% | 77 | 0.39 | 24.063 | -106.758 | 0.085 | 3.02 | ok |
| f6m_official_2v2_noweapon_s0 | official_2v2 | 4 | 5,736,000 | 95.6% | 75 | 0.98 | 23.474 | 29.885 | 0.083 | 6.12 | ok |
| f6m_official_1v1_selfplay_s1 | o_1v1_selfplay | 3 | 5,994,000 | 99.9% | 104 | 0.02 | 26.933 | 36.368 | 0.671 | 33.88 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_vsbaseline_s1 | o_1v1_vsbaseline | 3 | 5,994,000 | 99.9% | 122 | 0.01 | 27.785 | — | 0.997 | 19.78 | **complete 5,994,000 of 6,000,000** |
| f6m_official_1v1_shoot_hier_selfplay_s1 | o_1v1_shoot | 3 | 4,572,000 | 76.2% | 61 | 6.5 | -116.094 | 0.146 | 64.905 | 464.07 | ok |
| f6m_official_1v1_hier_selfplay_s1 | o_1v1_hier | 3 | 5,994,000 | 99.9% | 83 | 0.02 | -92.807 | -307.067 | 8.124 | 441.28 | **complete 5,994,000 of 6,000,000** |
| f6m_5v5_noweapon_s1 | 5v5 s1 | 10 | 2,190,000 | 36.5% | 91 | 11.63 | 14.674 | -68.572 | 0.636 | 16.31 | ok |
| f6m_3v3_noweapon_s1 | 3v3 s1 | 8 | 2,856,000 | 47.6% | 120 | 7.28 | 35.694 | 47.507 | 0.194 | 11.08 | ok |
| f6m_official_heading_s5 | o_heading | 4 | 4,932,000 | 82.2% | 274 | 1.08 | 265.967 | — | 6.183 | 113.21 | ok |

- load1 **52.9**  container CPU **25.43 / 48.0 cores** (53.0% of quota, throttled 3.926% of periods)  train procs **58**, **31.19 GB** RSS
- RAM used 58.3 GB / 1007.5 GB (avail 935.5 GB)
- GPU0: util 31%, VRAM 1882 MiB
- GPU1: util 3%, VRAM 546 MiB
- GPU2: util 8%, VRAM 2388 MiB
- tmux: f6m_10v10, f6m_1v1hier, f6m_1v1shoot, f6m_1v1sp, f6m_1v1vs, f6m_2v2, f6m_3v3, f6m_3v3s1, f6m_5v5, f6m_5v5s1, f6m_events, f6m_finalize, f6m_heading, f6m_off2v2, f6m_watch
