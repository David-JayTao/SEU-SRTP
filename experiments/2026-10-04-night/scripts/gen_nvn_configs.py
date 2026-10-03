#!/usr/bin/env python
"""Generate N-v-N MultipleCombat scenario YAMLs from an official template.

Why this exists
---------------
The upstream repo ships only `2v2/*` configs. To study scalability we need
3v3 / 5v5 / 10v10. Rather than fork the task code we (a) parameterised
`MultipleCombatTask.num_agents` to read the scenario's own `aircraft_configs`,
and (b) generate new YAMLs that differ from the official 2v2 template *only*
in the `aircraft_configs` block. Every reward / termination / simulation
parameter is inherited verbatim from the official file, so any behavioural
difference across N is attributable to team size, not to a config edit.

Formation
---------
Line abreast, constant lateral spacing, centred on the battlefield longitude:
    lon_i = center_lon + (i - (N-1)/2) * spacing_deg        for i in 0..N-1
    Red  team: latitude center_lat, heading 0   (flying north)
    Blue team: latitude center_lat + 0.1, heading 180 (flying south)
Spacing is held at 0.01 deg (~556 m at 60N) so that inter-aircraft geometry is
N-invariant; the *front width* therefore grows linearly with N (2v2: 0.56 km,
10v10: 5.0 km). This is a deliberate, documented design choice.
"""
import argparse
import copy
import os
import sys

import yaml

REPO = "/root/autodl-tmp/SEU-SRTP"
CONFIG_DIR = os.path.join(REPO, "envs/JSBSim/configs")

# variant -> (template path relative to configs/, output subdir).
# The output subdir is variant-specific on purpose: writing both variants into a
# shared "scaling/" directory silently overwrites one with the other.
VARIANTS = {
    "noweapon": ("2v2/NoWeapon/HierarchySelfplay.yaml", "scaling_noweapon"),
    "shoot": ("2v2/ShootMissile/HierarchySelfplay.yaml", "scaling_shoot"),
}


def build_aircraft_configs(template_ac, n, spacing_deg, base_lon, base_lat):
    """Interpolate the template's Red/Blue aircraft entry into an N-v-N layout."""
    red_tmpl = next(c for c in template_ac.values() if c["color"] == "Red")
    blue_tmpl = next(c for c in template_ac.values() if c["color"] == "Blue")

    out = {}
    for team, tmpl, lat in (("A", red_tmpl, base_lat), ("B", blue_tmpl, base_lat + 0.1)):
        for i in range(n):
            lon = round(base_lon + (i - (n - 1) / 2.0) * spacing_deg, 6)
            # A0100 / A0200 ... keeps the uid[0] team convention used by env_base
            uid = f"{team}{i + 1:02d}00"
            ac = copy.deepcopy(tmpl)
            ac["init_state"] = dict(tmpl["init_state"])
            ac["init_state"]["ic_long_gc_deg"] = lon
            ac["init_state"]["ic_lat_geod_deg"] = lat
            out[uid] = ac
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    p.add_argument("--n", type=int, nargs="+", required=True, help="team size(s)")
    p.add_argument("--spacing-deg", type=float, default=0.01)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    tmpl_rel, out_subdir = VARIANTS[args.variant]
    tmpl_path = os.path.join(CONFIG_DIR, tmpl_rel)
    with open(tmpl_path, "r", encoding="utf-8") as f:
        base = yaml.load(f, Loader=yaml.FullLoader)

    base_lon, base_lat, _ = base["battle_field_center"]
    base_lat = 60.0  # 2v2 template puts Red at latitude 60.0

    for n in args.n:
        cfg = copy.deepcopy(base)
        cfg["aircraft_configs"] = build_aircraft_configs(
            base["aircraft_configs"], n, args.spacing_deg, base_lon, base_lat)
        # explicit override -> makes the intent legible in the YAML itself
        cfg["num_agents"] = 2 * n
        cfg["team_size"] = n

        rel = os.path.join(f"{n}v{n}", out_subdir, "HierarchySelfplay.yaml")
        out_path = os.path.join(CONFIG_DIR, rel)
        if args.dry_run:
            print(f"[dry-run] would write {rel}  ({2 * n} aircraft)")
            continue
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, sort_keys=False, default_flow_style=False)
        print(f"wrote {rel}  ({2 * n} aircraft, {n} per team)")


if __name__ == "__main__":
    main()
