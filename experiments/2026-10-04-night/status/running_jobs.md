# Running Jobs Snapshot

Generated: 2026-10-04T05:41:36+08:00

## tmux sessions

```
monitor: 1 windows (created Sun Oct  4 02:21:38 2026)
q_extra: 1 windows (created Sun Oct  4 02:22:10 2026)
q_gpu0: 1 windows (created Sun Oct  4 02:19:02 2026)
q_gpu1: 1 windows (created Sun Oct  4 02:19:02 2026)
q_gpu2: 1 windows (created Sun Oct  4 02:19:02 2026)
q_seeds: 1 windows (created Sun Oct  4 02:25:45 2026)
```

## Queue states

### queue_gpu0
```
<<< official_2v2_noweapon_selfplay end 2026-10-04T03:52:12+08:00 rc=0
>>> scaling_2v2_shoot start 2026-10-04T03:52:12+08:00 gpu=0 threads=8 steps=900000 limit=5400s
<<< official_1v1_vsbaseline end 2026-10-04T04:39:05+08:00 rc=0
>>> official_1v1_selfplay start 2026-10-04T04:39:05+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
<<< scaling_2v2_shoot end 2026-10-04T05:22:13+08:00 rc=0
>>> scaling_3v3_shoot start 2026-10-04T05:22:13+08:00 gpu=0 threads=8 steps=900000 limit=7200s
```
### queue_gpu1
```
<<< scaling_3v3_noweapon_s1 end 2026-10-04T03:55:47+08:00 rc=0
>>> scaling_2v2_noweapon_s1 start 2026-10-04T03:55:47+08:00 gpu=1 threads=10 steps=900000 limit=5400s
<<< official_2v2_noweapon end 2026-10-04T04:19:04+08:00 rc=0
>>> official_2v2_shoot start 2026-10-04T04:19:04+08:00 gpu=1 threads=12 steps=1e8 limit=7200s
<<< scaling_2v2_noweapon_s1 end 2026-10-04T05:16:15+08:00 rc=0
>>> scaling_5v5_noweapon_s1 start 2026-10-04T05:16:15+08:00 gpu=1 threads=10 steps=900000 limit=7200s
```
### queue_gpu2
```
queue started gpu=2 at 2026-10-04T02:19:02+08:00
>>> scaling_10v10_noweapon start 2026-10-04T02:19:02+08:00 gpu=2 threads=18 steps=900000 limit=10800s
<<< scaling_10v10_noweapon end 2026-10-04T05:19:04+08:00 rc=0
>>> scaling_5v5_noweapon start 2026-10-04T05:19:04+08:00 gpu=2 threads=18 steps=900000 limit=7200s
```

## Live training processes (aggregated per experiment)

| experiment | n_procs | total_cpu_pct | total_rss_gb |
|---|---|---|---|
| official_1v1_selfplay | 12 | 346% | 4.77 |
| official_2v2_shoot | 14 | 686% | 5.78 |
| scaling_3v3_shoot | 10 | 511% | 4.47 |
| scaling_5v5_noweapon | 20 | 1113% | 8.81 |
| scaling_5v5_noweapon_s1 | 12 | 656% | 5.60 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_1v1_selfplay | 1200000 | 100000000 | 323. | -95.91552734375 | - |
| official_1v1_vsbaseline | 1500000 | 100000000 | 357. | -1.9254876413652975 | - |
| official_2v2_noweapon | 1476000 | 100000000 | 208. | 1.2035396893819172 | 7.953659 |
| official_2v2_noweapon_selfplay | 816000 | 100000000 | 154. | -16.140660439768144 | 24.192276 |
| official_2v2_shoot | 792000 | 100000000 | 163. | -35.54886308547136 | -38.31012 |
| official_heading | 2460000 | 100000000 | 590. | 100.61372375488281 | - |
| scaling_10v10_noweapon | 648000 | 900000 | 61. | -16.431697591145834 | -4.4320607 |
| scaling_2v2_noweapon_s1 | 900000 | 900000 | 186. | 3.7388484954833983 | -1.6435177 |
| scaling_2v2_shoot | 624000 | 900000 | 115. | -12.47608670321378 | -42.079113 |
| scaling_3v3_noweapon_s1 | 840000 | 900000 | 159. | 19.542348225911457 | 43.62738 |
| scaling_3v3_shoot | 96000 | 900000 | 90. | -22.549563172043012 | 37.49546 |
| scaling_5v5_noweapon_s1 | 120000 | 900000 | 91. | -8.551014404296875 | -5.6146135 |
| scaling_5v5_noweapon | 162000 | 900000 | 160. | -9.094508870442708 | -225.1307 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 21 %, 1267 MiB, 34
1, 8 %, 1343 MiB, 36
2, 1 %, 902 MiB, 36
```

## Last system samples

```
2026-10-04T05:40:30+08:00,44.66,43.19,21,52.5,1007.5,5,15,1265,11,1343,1,902
2026-10-04T05:40:46+08:00,42.89,42.91,22,52.5,1007.5,5,17,1265,9,1343,1,902
2026-10-04T05:41:03+08:00,39.82,42.24,20,52.7,1007.5,5,19,1267,10,1343,1,902
2026-10-04T05:41:19+08:00,38.42,41.80,21,52.7,1007.5,5,9,1267,2,1343,1,902
2026-10-04T05:41:35+08:00,41.34,42.25,21,52.8,1007.5,5,20,1267,2,1343,1,902
```
