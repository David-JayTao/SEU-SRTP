# Running Jobs Snapshot

Generated: 2026-10-04T03:02:29+08:00

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
| official_2v2_noweapon | 14 | 660% | 5.77 |
| official_2v2_noweapon_selfplay | 10 | 407% | 4.19 |
| official_heading | 12 | 323% | 4.75 |
| scaling_10v10_noweapon | 20 | 1219% | 13.82 |
| scaling_3v3_noweapon_s1 | 12 | 611% | 5.18 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 540000 | 100000000 | 211. | -3.4978345235188804 | -40.157967 |
| official_2v2_noweapon_selfplay | 360000 | 100000000 | 154. | 14.481517727092161 | 15.312804 |
| official_heading | 1500000 | 100000000 | 585. | 29.20049370659722 | - |
| scaling_10v10_noweapon | 108000 | 900000 | 53. | -17.572593858506945 | -279.43216 |
| scaling_3v3_noweapon_s1 | 330000 | 900000 | 155. | -0.5674128214518229 | -136.22977 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 22 %, 1359 MiB, 34
1, 14 %, 1405 MiB, 36
2, 1 %, 994 MiB, 36
```

## Last system samples

```
2026-10-04T03:01:12+08:00,37.91,40.77,19,56.6,1007.5,5,23,1359,7,1405,0,994
2026-10-04T03:01:28+08:00,37.80,40.60,21,56.6,1007.5,5,19,1359,3,1405,1,994
2026-10-04T03:01:45+08:00,37.78,40.46,19,56.5,1007.5,5,16,1359,17,1405,0,994
2026-10-04T03:02:01+08:00,37.00,40.17,17,56.5,1007.5,5,19,1359,11,1405,0,994
2026-10-04T03:02:17+08:00,37.09,40.02,20,56.4,1007.5,5,23,1359,13,1405,0,994
```
