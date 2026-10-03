# Running Jobs Snapshot

Generated: 2026-10-04T06:10:26+08:00

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
<<< official_1v1_vsbaseline end 2026-10-04T04:39:05+08:00 rc=0
>>> official_1v1_selfplay start 2026-10-04T04:39:05+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
<<< scaling_2v2_shoot end 2026-10-04T05:22:13+08:00 rc=0
>>> scaling_3v3_shoot start 2026-10-04T05:22:13+08:00 gpu=0 threads=8 steps=900000 limit=7200s
<<< official_1v1_selfplay end 2026-10-04T05:49:06+08:00 rc=0
>>> official_1v1_hier_selfplay start 2026-10-04T05:49:06+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
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
| official_1v1_hier_selfplay | 12 | 453% | 5.02 |
| official_2v2_shoot | 14 | 684% | 5.76 |
| scaling_3v3_shoot | 10 | 512% | 4.48 |
| scaling_5v5_noweapon | 20 | 1108% | 8.81 |
| scaling_5v5_noweapon_s1 | 12 | 649% | 5.60 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_1v1_hier_selfplay | 330000 | 100000000 | 278. | -42.75230102539062 | - |
| official_1v1_selfplay | 1350000 | 100000000 | 325. | -91.13390048238254 | - |
| official_1v1_vsbaseline | 1500000 | 100000000 | 357. | -1.9254876413652975 | - |
| official_2v2_noweapon | 1476000 | 100000000 | 208. | 1.2035396893819172 | 7.953659 |
| official_2v2_noweapon_selfplay | 816000 | 100000000 | 154. | -16.140660439768144 | 24.192276 |
| official_2v2_shoot | 1080000 | 100000000 | 162. | -2.1260626220703127 | -1.9939407 |
| official_heading | 2460000 | 100000000 | 590. | 100.61372375488281 | - |
| scaling_10v10_noweapon | 648000 | 900000 | 61. | -16.431697591145834 | -4.4320607 |
| scaling_2v2_noweapon_s1 | 900000 | 900000 | 186. | 3.7388484954833983 | -1.6435177 |
| scaling_2v2_shoot | 624000 | 900000 | 115. | -12.47608670321378 | -42.079113 |
| scaling_3v3_noweapon_s1 | 840000 | 900000 | 159. | 19.542348225911457 | 43.62738 |
| scaling_3v3_shoot | 240000 | 900000 | 89. | -19.567659153926858 | -26.883072 |
| scaling_5v5_noweapon_s1 | 270000 | 900000 | 90. | -7.3886566162109375 | 39.514507 |
| scaling_5v5_noweapon | 432000 | 900000 | 150. | -8.987238226996528 | -11.901924 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 12 %, 1241 MiB, 34
1, 3 %, 1343 MiB, 36
2, 1 %, 902 MiB, 36
```

## Last system samples

```
2026-10-04T06:09:18+08:00,47.11,43.34,21,53.1,1007.5,5,14,1241,3,1343,1,902
2026-10-04T06:09:34+08:00,45.69,43.24,21,53.0,1007.5,5,10,1241,3,1343,1,902
2026-10-04T06:09:50+08:00,47.24,43.71,22,52.8,1007.5,5,4,1241,2,1343,1,902
2026-10-04T06:10:06+08:00,45.52,43.54,23,52.9,1007.5,5,15,1241,2,1343,1,902
2026-10-04T06:10:23+08:00,43.93,43.29,22,53.1,1007.5,5,12,1241,2,1343,1,902
```
