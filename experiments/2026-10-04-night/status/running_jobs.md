# Running Jobs Snapshot

Generated: 2026-10-04T02:51:55+08:00

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
| official_2v2_noweapon | 14 | 663% | 5.80 |
| official_2v2_noweapon_selfplay | 10 | 408% | 4.20 |
| official_heading | 12 | 320% | 4.74 |
| scaling_10v10_noweapon | 20 | 1200% | 14.22 |
| scaling_3v3_noweapon_s1 | 12 | 610% | 5.21 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 396000 | 100000000 | 213. | -3.4955666859944663 | -260.923 |
| official_2v2_noweapon_selfplay | 264000 | 100000000 | 156. | 8.622909545898438 | 11.676282 |
| official_heading | 1140000 | 100000000 | 581. | 8.258093079524254 | - |
| scaling_10v10_noweapon | 54000 | 900000 | 60. | -17.663582356770835 | -279.43216 |
| scaling_3v3_noweapon_s1 | 240000 | 900000 | 155. | -4.58236083984375 | -165.4815 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 8 %, 1359 MiB, 34
1, 7 %, 1405 MiB, 35
2, 0 %, 994 MiB, 36
```

## Last system samples

```
2026-10-04T02:50:42+08:00,44.71,41.87,23,54.0,1007.5,5,11,1804,9,1405,0,994
2026-10-04T02:50:58+08:00,44.60,41.98,23,54.1,1007.5,5,35,1804,4,1405,1,994
2026-10-04T02:51:15+08:00,45.29,42.26,22,54.0,1007.5,5,23,1804,12,1405,1,994
2026-10-04T02:51:31+08:00,46.70,42.73,22,54.0,1007.5,5,20,1804,12,1405,1,994
2026-10-04T02:51:47+08:00,45.92,42.80,19,53.2,1007.5,5,27,1359,3,1405,0,994
```
