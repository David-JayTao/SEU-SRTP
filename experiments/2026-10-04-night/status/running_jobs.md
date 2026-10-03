# Running Jobs Snapshot

Generated: 2026-10-04T02:25:34+08:00

## tmux sessions

```
monitor: 1 windows (created Sun Oct  4 02:21:38 2026)
q_extra: 1 windows (created Sun Oct  4 02:22:10 2026)
q_gpu0: 1 windows (created Sun Oct  4 02:19:02 2026)
q_gpu1: 1 windows (created Sun Oct  4 02:19:02 2026)
q_gpu2: 1 windows (created Sun Oct  4 02:19:02 2026)
```

## Queue states

### queue_gpu0
```
queue started gpu=0 at 2026-10-04T02:19:02+08:00
>>> official_heading start 2026-10-04T02:19:02+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
queue started gpu=0 at 2026-10-04T02:22:10+08:00
>>> official_2v2_noweapon_selfplay start 2026-10-04T02:22:10+08:00 gpu=0 threads=8 steps=1e8 limit=5400s
```
### queue_gpu1
```
queue started gpu=1 at 2026-10-04T02:19:02+08:00
>>> official_2v2_noweapon start 2026-10-04T02:19:02+08:00 gpu=1 threads=12 steps=1e8 limit=7200s
```
### queue_gpu2
```
queue started gpu=2 at 2026-10-04T02:19:02+08:00
>>> scaling_10v10_noweapon start 2026-10-04T02:19:02+08:00 gpu=2 threads=18 steps=900000 limit=10800s
```

## Live training processes (aggregated per experiment)

| experiment | n_procs | total_cpu_pct | total_rss_gb |
|---|---|---|---|
| official_2v2_noweapon | 14 | 658% | 5.76 |
| official_2v2_noweapon_selfplay | 10 | 420% | 4.15 |
| official_heading | 12 | 318% | 4.74 |
| scaling_10v10_noweapon | 20 | 1239% | 10.50 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 72000 | 100000000 | 222. | -3.3416884740193686 | -126.63839 |
| official_2v2_noweapon_selfplay | 24000 | 100000000 | 154. | 11.160446281719924 | 29.738264 |
| official_heading | 210000 | 100000000 | 562. | -7.895653719027367 | - |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 12 %, 1257 MiB, 34
1, 2 %, 760 MiB, 36
2, 1 %, 464 MiB, 36
```

## Last system samples

```
2026-10-04T02:24:20+08:00,31.00,20.71,13,46.4,1007.5,4,17,1085,2,760,1,464
2026-10-04T02:24:36+08:00,30.79,21.29,11,46.6,1007.5,4,20,1085,3,760,1,464
2026-10-04T02:24:52+08:00,30.37,21.66,14,47.0,1007.5,4,15,1257,2,760,0,464
2026-10-04T02:25:08+08:00,28.46,21.67,14,47.1,1007.5,4,20,1257,2,760,1,464
2026-10-04T02:25:24+08:00,27.00,21.71,16,47.2,1007.5,4,13,1257,2,760,1,464
```
