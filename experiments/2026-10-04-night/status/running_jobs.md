# Running Jobs Snapshot

Generated: 2026-10-04T02:28:07+08:00

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
| official_2v2_noweapon | 14 | 671% | 5.83 |
| official_2v2_noweapon_selfplay | 10 | 413% | 4.18 |
| official_heading | 12 | 319% | 4.74 |
| scaling_10v10_noweapon | 20 | 1252% | 11.53 |
| scaling_3v3_noweapon_s1 | 12 | 628% | 4.83 |

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_2v2_noweapon | 108000 | 100000000 | 219. | -3.4849637349446616 | -99.72075 |
| official_2v2_noweapon_selfplay | 48000 | 100000000 | 155. | 11.616110137014678 | 14.200148 |
| official_heading | 300000 | 100000000 | 563. | -0.15490232755060065 | - |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 11 %, 1257 MiB, 34
1, 3 %, 1207 MiB, 36
2, 0 %, 464 MiB, 35
```

## Last system samples

```
2026-10-04T02:27:01+08:00,38.38,26.66,19,49.4,1007.5,5,21,1257,4,1207,0,464
2026-10-04T02:27:17+08:00,39.83,27.52,19,49.2,1007.5,5,14,1257,16,1207,0,464
2026-10-04T02:27:34+08:00,39.67,28.07,18,49.5,1007.5,5,11,1257,6,1207,0,464
2026-10-04T02:27:50+08:00,38.15,28.31,19,49.6,1007.5,5,13,1257,5,1207,1,464
2026-10-04T02:28:06+08:00,37.37,28.76,21,49.8,1007.5,5,11,1257,7,1207,0,464
```
