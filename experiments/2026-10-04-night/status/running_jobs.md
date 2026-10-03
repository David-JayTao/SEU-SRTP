# Running Jobs Snapshot

Generated: 2026-10-04T02:41:03+08:00

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
| official_2v2_noweapon | 14 | 681% | 5.80 |
| official_2v2_noweapon_selfplay | 10 | 416% | 4.18 |
| official_heading | 12 | 320% | 4.74 |
| scaling_10v10_noweapon | 20 | 1129% | 13.82 |
| scaling_3v3_noweapon_s1 | 12 | 618% | 5.21 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 252000 | 100000000 | 217. | -3.4729833602905273 | -279.51077 |
| official_2v2_noweapon_selfplay | 168000 | 100000000 | 154. | 9.70662245639535 | 1.440997 |
| official_heading | 750000 | 100000000 | 571. | 1.287450439453125 | - |
| scaling_10v10_noweapon | 54000 | 900000 | 60. | -17.663582356770835 | -279.43216 |
| scaling_3v3_noweapon_s1 | 120000 | 900000 | 158. | -5.347088623046875 | -144.33318 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 21 %, 1319 MiB, 34
1, 7 %, 1405 MiB, 35
2, 1 %, 994 MiB, 36
```

## Last system samples

```
2026-10-04T02:39:56+08:00,32.79,34.12,19,52.6,1007.5,5,25,1319,4,1405,1,994
2026-10-04T02:40:13+08:00,32.79,34.06,19,52.6,1007.5,5,11,1319,11,1405,0,994
2026-10-04T02:40:29+08:00,34.72,34.43,20,52.7,1007.5,5,16,1319,14,1405,0,994
2026-10-04T02:40:45+08:00,35.89,34.73,19,52.7,1007.5,5,22,1319,6,1405,0,994
2026-10-04T02:41:01+08:00,37.57,35.17,19,52.7,1007.5,5,18,1319,15,1405,0,994
```
