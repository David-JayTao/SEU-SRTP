# Running Jobs Snapshot

Generated: 2026-10-04T03:36:46+08:00

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
queue started gpu=0 at 2026-10-04T02:19:02+08:00
>>> official_heading start 2026-10-04T02:19:02+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
queue started gpu=0 at 2026-10-04T02:22:10+08:00
>>> official_2v2_noweapon_selfplay start 2026-10-04T02:22:10+08:00 gpu=0 threads=8 steps=1e8 limit=5400s
<<< official_heading end 2026-10-04T03:29:04+08:00 rc=0
>>> official_1v1_vsbaseline start 2026-10-04T03:29:04+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
```
### queue_gpu1
```
queue started gpu=1 at 2026-10-04T02:19:02+08:00
>>> official_2v2_noweapon start 2026-10-04T02:19:02+08:00 gpu=1 threads=12 steps=1e8 limit=7200s
queue started gpu=1 at 2026-10-04T02:25:45+08:00
>>> scaling_3v3_noweapon_s1 start 2026-10-04T02:25:46+08:00 gpu=1 threads=10 steps=900000 limit=5400s
```
### queue_gpu2
```
queue started gpu=2 at 2026-10-04T02:19:02+08:00
>>> scaling_10v10_noweapon start 2026-10-04T02:19:02+08:00 gpu=2 threads=18 steps=900000 limit=10800s
```

## Live training processes (aggregated per experiment)

| experiment | n_procs | total_cpu_pct | total_rss_gb |
|---|---|---|---|
| official_1v1_vsbaseline | 12 | 472% | 5.13 |
| official_2v2_noweapon | 14 | 668% | 5.80 |
| official_2v2_noweapon_selfplay | 10 | 414% | 4.19 |
| scaling_10v10_noweapon | 20 | 1191% | 13.83 |
| scaling_3v3_noweapon_s1 | 12 | 620% | 5.21 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_1v1_vsbaseline | 150000 | 100000000 | 348. | -211.94630142405063 | - |
| official_2v2_noweapon | 972000 | 100000000 | 209. | -0.27233338356018066 | -127.80173 |
| official_2v2_noweapon_selfplay | 672000 | 100000000 | 153. | 18.130230494907924 | -6.583122 |
| official_heading | 2460000 | 100000000 | 590. | 100.61372375488281 | - |
| scaling_10v10_noweapon | 216000 | 900000 | 55. | -17.645338270399307 | -129.76001 |
| scaling_3v3_noweapon_s1 | 660000 | 900000 | 159. | -1.1083086649576823 | 21.429422 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 9 %, 1315 MiB, 34
1, 4 %, 1405 MiB, 36
2, 0 %, 994 MiB, 35
```

## Last system samples

```
2026-10-04T03:35:39+08:00,41.78,39.96,22,57.5,1007.5,5,19,1315,7,1405,0,994
2026-10-04T03:35:55+08:00,42.13,40.13,22,57.5,1007.5,5,7,1315,4,1405,1,994
2026-10-04T03:36:11+08:00,42.75,40.36,22,57.5,1007.5,5,18,1315,3,1405,1,994
2026-10-04T03:36:27+08:00,42.82,40.47,18,57.5,1007.5,5,9,1315,8,1405,0,994
2026-10-04T03:36:43+08:00,41.48,40.27,23,57.9,1007.5,5,3,1315,7,1405,0,994
```
