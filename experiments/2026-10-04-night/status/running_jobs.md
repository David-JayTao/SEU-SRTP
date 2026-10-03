# Running Jobs Snapshot

Generated: 2026-10-04T02:53:13+08:00

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
| official_2v2_noweapon | 14 | 662% | 5.80 |
| official_2v2_noweapon_selfplay | 10 | 408% | 4.20 |
| official_heading | 12 | 321% | 4.74 |
| scaling_10v10_noweapon | 20 | 1185% | 13.82 |
| scaling_3v3_noweapon_s1 | 12 | 612% | 5.21 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 432000 | 100000000 | 212. | -3.521298408508301 | -260.923 |
| official_2v2_noweapon_selfplay | 288000 | 100000000 | 155. | 12.1150458984375 | 29.512 |
| official_heading | 1170000 | 100000000 | 581. | 7.585162353515625 | - |
| scaling_10v10_noweapon | 108000 | 900000 | 53. | -17.572593858506945 | -279.43216 |
| scaling_3v3_noweapon_s1 | 240000 | 900000 | 155. | -4.58236083984375 | -165.4815 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 23 %, 1359 MiB, 34
1, 12 %, 1405 MiB, 35
2, 1 %, 994 MiB, 36
```

## Last system samples

```
2026-10-04T02:52:03+08:00,42.75,42.27,14,58.9,1007.5,5,19,1359,7,1405,13,994
2026-10-04T02:52:19+08:00,40.22,41.76,15,57.4,1007.5,5,42,1842,8,1405,0,994
2026-10-04T02:52:35+08:00,38.19,41.21,20,53.0,1007.5,5,10,1359,3,1405,1,994
2026-10-04T02:52:52+08:00,40.44,41.56,20,53.1,1007.5,5,18,1359,3,1405,0,994
2026-10-04T02:53:08+08:00,40.22,41.46,16,53.1,1007.5,5,16,1359,9,1405,0,994
```
