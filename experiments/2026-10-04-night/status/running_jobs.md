# Running Jobs Snapshot

Generated: 2026-10-04T03:40:47+08:00

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
| official_1v1_vsbaseline | 12 | 467% | 5.16 |
| official_2v2_noweapon | 14 | 669% | 5.80 |
| official_2v2_noweapon_selfplay | 10 | 414% | 4.19 |
| scaling_10v10_noweapon | 20 | 1155% | 13.83 |
| scaling_3v3_noweapon_s1 | 12 | 620% | 5.21 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_1v1_vsbaseline | 240000 | 100000000 | 346. | -210.61115506329114 | - |
| official_2v2_noweapon | 1008000 | 100000000 | 209. | -2.9926106135050454 | -119.02939 |
| official_2v2_noweapon_selfplay | 720000 | 100000000 | 153. | -11.902143205915179 | 25.624353 |
| official_heading | 2460000 | 100000000 | 590. | 100.61372375488281 | - |
| scaling_10v10_noweapon | 270000 | 900000 | 57. | -17.45848388671875 | -134.56442 |
| scaling_3v3_noweapon_s1 | 690000 | 900000 | 159. | -0.6657419840494792 | 13.721066 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 11 %, 1315 MiB, 34
1, 13 %, 1405 MiB, 36
2, 1 %, 994 MiB, 35
```

## Last system samples

```
2026-10-04T03:39:41+08:00,29.11,35.41,15,58.1,1007.5,5,11,1315,9,1405,0,994
2026-10-04T03:39:57+08:00,31.99,35.75,21,58.1,1007.5,5,10,1315,2,1405,0,994
2026-10-04T03:40:13+08:00,37.02,36.72,20,58.1,1007.5,5,16,1315,10,1405,0,994
2026-10-04T03:40:29+08:00,38.39,37.06,21,58.0,1007.5,5,10,1315,3,1405,0,994
2026-10-04T03:40:45+08:00,39.45,37.39,21,58.0,1007.5,5,11,1315,4,1405,0,994
```
