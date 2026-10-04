# Running Jobs Snapshot

Generated: 2026-10-04T13:39:45+08:00

## tmux sessions

```
no server running on /tmp/tmux-0/default
```

## Queue states

### queue_gpu0
```
<<< scaling_3v3_noweapon_s3 end 2026-10-04T10:52:17+08:00 rc=0
queue drained gpu=0 at 2026-10-04T10:52:17+08:00
<<< official_1v1_dodge_vsbaseline end 2026-10-04T11:39:17+08:00 rc=0
>>> official_1v1_hier_dodge_vsbaseline start 2026-10-04T11:39:17+08:00 gpu=0 threads=10 steps=1e8 limit=4200s
<<< official_1v1_hier_dodge_vsbaseline end 2026-10-04T12:49:19+08:00 rc=0
queue drained gpu=0 at 2026-10-04T12:49:19+08:00
```
### queue_gpu1
```
<<< scaling_2v2_noweapon_s2 end 2026-10-04T10:05:00+08:00 rc=0
queue drained gpu=1 at 2026-10-04T10:05:00+08:00
<<< scaling_10v10_noweapon_s1 end 2026-10-04T10:16:18+08:00 rc=0
>>> scaling_3v3_noweapon_s2 start 2026-10-04T10:16:18+08:00 gpu=1 threads=10 steps=900000 limit=5400s
<<< scaling_3v3_noweapon_s2 end 2026-10-04T11:46:20+08:00 rc=0
queue drained gpu=1 at 2026-10-04T11:46:20+08:00
```
### queue_gpu2
```
<<< scaling_3v3_noweapon end 2026-10-04T07:48:18+08:00 rc=0
>>> scaling_5v5_noweapon_s2 start 2026-10-04T07:48:18+08:00 gpu=2 threads=18 steps=900000 limit=7200s
<<< scaling_5v5_noweapon_s2 end 2026-10-04T09:20:22+08:00 rc=0
>>> scaling_10v10_noweapon_s2 start 2026-10-04T09:20:22+08:00 gpu=2 threads=18 steps=900000 limit=10800s
<<< scaling_10v10_noweapon_s2 end 2026-10-04T12:20:24+08:00 rc=0
queue drained gpu=2 at 2026-10-04T12:20:24+08:00
```

## Live training processes (aggregated per experiment)

| experiment | n_procs | total_cpu_pct | total_rss_gb |
|---|---|---|---|

## Progress (from logs)

| experiment | steps | target | FPS | train reward | eval reward |
|---|---|---|---|---|---|
| METRICS_TEST | 6000 | 6000 | 41. | -3.5340681076049805 | - |
| SMOKE_2v2 | 12000 | 240000 | 80. | -3.506592273712158 | -290.6607 |
| SMOKE_heading | 36000 | 240000 | 234. | -13.130021528764205 | - |
| SMOKE_vsbaseline | 24000 | 240000 | 145. | -210.46957859848484 | - |
| official_1v1_dodge_vsbaseline | 1020000 | 100000000 | 249. | -249.46162823932926 | -230.68643 |
| official_1v1_dodgemissile_selfplay | 900000 | 100000000 | 218. | -0.36502485275268554 | - |
| official_1v1_hier_dodge_vsbaseline | 1140000 | 100000000 | 277. | -43.22066116333008 | -218.88385 |
| official_1v1_hier_selfplay | 1140000 | 100000000 | 276. | 36.76605224609375 | - |
| official_1v1_selfplay | 1350000 | 100000000 | 325. | -91.13390048238254 | - |
| official_1v1_shoot_hier_selfplay | 720000 | 100000000 | 172. | -21.063981797960068 | - |
| official_1v1_shoot_selfplay | 660000 | 100000000 | 160. | -225.7453748082822 | - |
| official_1v1_vsbaseline | 1500000 | 100000000 | 357. | -1.9254876413652975 | - |
| official_2v2_noweapon_s1b | 1152000 | 100000000 | 219. | 8.633499145507812 | -162.50797 |
| official_2v2_noweapon | 1476000 | 100000000 | 208. | 1.2035396893819172 | 7.953659 |
| official_2v2_noweapon_selfplay | 816000 | 100000000 | 154. | -16.140660439768144 | 24.192276 |
| official_2v2_shoot | 1152000 | 100000000 | 163. | 9.077198122258771 | -9.131655 |
| official_heading | 2460000 | 100000000 | 590. | 100.61372375488281 | - |
| scaling_10v10_noweapon_s1 | 594000 | 900000 | 57. | -15.281882052951389 | -17.556185 |
| scaling_10v10_noweapon_s2 | 594000 | 900000 | 57. | -15.893421766493056 | -21.813602 |
| scaling_10v10_noweapon | 648000 | 900000 | 61. | -16.431697591145834 | -4.4320607 |
| scaling_2v2_noweapon_s1 | 900000 | 900000 | 186. | 3.7388484954833983 | -1.6435177 |
| scaling_2v2_noweapon_s2 | 900000 | 900000 | 220. | -1.2398699124654133 | -2.2117054 |
| scaling_2v2_noweapon | 900000 | 900000 | 223. | -0.12228802839914958 | -48.365887 |
| scaling_2v2_shoot | 624000 | 900000 | 115. | -12.47608670321378 | -42.079113 |
| scaling_3v3_noweapon_s1 | 840000 | 900000 | 159. | 19.542348225911457 | 43.62738 |
| scaling_3v3_noweapon_s2 | 840000 | 900000 | 160. | -3.435217793782552 | -32.769936 |
| scaling_3v3_noweapon_s3 | 672000 | 900000 | 126. | -1.4603516260782878 | -7.6902595 |
| scaling_3v3_noweapon | 864000 | 900000 | 257. | -1.4961116932056568 | -6.9778333 |
| scaling_3v3_shoot | 648000 | 900000 | 90. | -19.014289793494154 | -31.709074 |
| scaling_5v5_noweapon_s1 | 630000 | 900000 | 92. | 5.041533203125 | 8.471016 |
| scaling_5v5_noweapon_s2 | 864000 | 900000 | 156. | -4.014883761935764 | -151.49178 |
| scaling_5v5_noweapon | 864000 | 900000 | 154. | -8.668863932291666 | -12.092153 |
| scaling_5v5_shoot | 384000 | 900000 | 55. | 11.843868761446886 | 0.3638309 |

## GPUs

```
index, utilization.gpu [%], memory.used [MiB], temperature.gpu
0, 0 %, 1 MiB, 30
1, 0 %, 1 MiB, 31
2, 0 %, 1 MiB, 28
```

## Last system samples

```
2026-10-04T12:59:05+08:00,21.08,19.49,9,64.2,1007.5,0,0,1,0,1,0,1
2026-10-04T12:59:21+08:00,21.40,19.70,8,64.3,1007.5,0,0,1,0,1,0,1
2026-10-04T12:59:37+08:00,22.05,19.91,10,64.2,1007.5,0,0,1,0,1,0,1
2026-10-04T12:59:54+08:00,21.07,19.80,12,64.2,1007.5,0,0,1,0,1,0,1
2026-10-04T13:00:10+08:00,20.75,19.79,11,64.4,1007.5,0,0,1,0,1,0,1
```
