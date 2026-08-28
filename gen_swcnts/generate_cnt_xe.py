"""
generate_cnt_xe.py
------------------
Generate CNT + Xe initial configurations from a TOML config file.

Xe loading can be specified in three ways per [[tubes]] block:
  1. n_xe = <int>                     — explicit atom count (original behaviour)
  2. xe_density_mode = "low"/"high"   — fraction of geometric maximum
  3. xe_linear_density = <float>      — explicit atoms/Å value

Density modes are computed from [xe_density] settings:
  low_loading_fraction  (default 0.20) × geometric_max
  high_loading_fraction (default 0.80) × geometric_max

[[density_sweep]] blocks generate one XYZ per density point, evenly spaced
between low and high loading for a given tube.

Usage:
    python generate_cnt_xe.py              # reads config.toml
    python generate_cnt_xe.py my.toml      # reads a specific config file

Python compatibility:
    Python >= 3.11 : tomllib is built-in
    Python <  3.11 : pip install tomli
"""

import sys
import csv
import numpy as np
from ase import Atoms
from ase.io import write
from ase.build import nanotube

# --------------------------------------------------------------------------- #
# TOML loader
# --------------------------------------------------------------------------- #
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "TOML support not found.\n"
            "  Python >= 3.11  : tomllib is built-in.\n"
            "  Python <  3.11  : pip install tomli"
        )


# =========================================================================== #
# CNT geometry
# =========================================================================== #

def create_cnt(n, m, num_units=1):
    """
    Build a CNT supercell and return (cnt, radius, length).

    Uses cell[2,2] for the box z-length — NOT the atom extent — to avoid
    the PBC ring artefact for zigzag and chiral tubes.
    """
    cnt    = nanotube(n, m, length=num_units)
    pos    = cnt.get_positions()
    radius = np.mean(np.sqrt(pos[:, 0]**2 + pos[:, 1]**2))
    length = cnt.cell[2, 2]
    return cnt, radius, length


def calculate_volume(radius, length):
    """Interior cylinder volume π r² L (Å³)."""
    return np.pi * radius**2 * length


# =========================================================================== #
# Geometric Xe capacity
# =========================================================================== #

def geometric_max_xe(radius, length, sigma_xe=4.32, r_xe=2.16, r_c=1.7):
    """
    Estimate the maximum number of Xe atoms that can fit inside a tube
    based on simple geometric packing.

    Narrow tubes (r_max < sigma/2): single-file along z
    Medium tubes (sigma/2 <= r_max < sigma): 2 Xe per z-slice
    Wide tubes   (r_max >= sigma):            3 Xe per z-slice

    r_max = r_pore - r_xe  (how far Xe centre can be from tube axis)
    """
    r_pore = radius - r_c
    r_max  = max(0.0, r_pore - r_xe)
    n_z    = max(1, int(length / sigma_xe))
    if r_max < sigma_xe / 2:
        n_xy = 1
    elif r_max < sigma_xe:
        n_xy = 2
    else:
        n_xy = 3
    return n_z * n_xy


def n_xe_from_mode(mode, radius, length, xe_density_cfg):
    """
    Compute n_xe from a density mode string ("low" or "high").
    """
    geo_max   = geometric_max_xe(radius, length)
    low_frac  = xe_density_cfg.get("low_loading_fraction",  0.20)
    high_frac = xe_density_cfg.get("high_loading_fraction", 0.80)

    if mode == "low":
        return max(1, round(low_frac * geo_max))
    elif mode == "high":
        return max(1, round(high_frac * geo_max))
    else:
        raise ValueError(f"Unknown xe_density_mode '{mode}'. Use 'low' or 'high'.")


def n_xe_sweep_points(radius, length, n_points, xe_density_cfg):
    """
    Return a list of n_points evenly spaced integers from n_xe_low to n_xe_high.
    """
    n_low  = n_xe_from_mode("low",  radius, length, xe_density_cfg)
    n_high = n_xe_from_mode("high", radius, length, xe_density_cfg)
    pts    = np.linspace(n_low, n_high, n_points)
    # Round, deduplicate, preserve order
    pts_int = sorted(set(max(1, round(x)) for x in pts))
    return pts_int


# =========================================================================== #
# Distance checks (PBC-aware)
# =========================================================================== #

def check_distances(new_pos, existing_positions, min_dist, box_size):
    if len(existing_positions) == 0:
        return True
    diffs = np.abs(existing_positions - new_pos)
    for dim in range(3):
        diffs[:, dim] = np.minimum(diffs[:, dim], box_size[dim] - diffs[:, dim])
    return np.all(np.sqrt(np.sum(diffs**2, axis=1)) >= min_dist)


# =========================================================================== #
# Xe placement
# =========================================================================== #

def place_xe_atoms(cnt_positions, n_xe, radius, box_size,
                   min_xe_c=3.86, min_xe_xe=4.32,
                   max_attempts=300000, narrow_threshold=5.0):
    """
    Place n_xe Xe atoms inside a CNT respecting Xe-C and Xe-Xe distance
    constraints with PBC.

    Narrow tubes (radius < narrow_threshold): evenly spaced single-file along z.
    Wide tubes: random rejection sampling within the tube cross-section.
    """
    if n_xe <= 0:
        return np.empty((0, 3))

    center_xy = np.mean(cnt_positions, axis=0)[:2]

    # Narrow: single-file
    if radius < narrow_threshold:
        print(f"  Narrow tube (r = {radius:.2f} Å): single-file placement")
        positions   = np.zeros((n_xe, 3))
        z_spacing   = box_size[2] / n_xe
        for i in range(n_xe):
            positions[i] = [center_xy[0], center_xy[1],
                            z_spacing / 2 + i * z_spacing]
        return positions

    # Wide: rejection sampling
    print(f"  Wide tube (r = {radius:.2f} Å): random disk placement "
          f"for {n_xe} Xe atoms")
    positions     = np.zeros((n_xe, 3))
    placed        = 0
    progress_step = max(1, n_xe // 5)

    for _ in range(max_attempts):
        r_samp  = np.random.uniform(0, radius * 0.95)
        theta   = np.random.uniform(0, 2 * np.pi)
        z       = np.random.uniform(0, box_size[2])
        new_pos = np.array([center_xy[0] + r_samp * np.cos(theta),
                             center_xy[1] + r_samp * np.sin(theta),
                             z])

        diffs = np.abs(cnt_positions - new_pos)
        for dim in range(3):
            diffs[:, dim] = np.minimum(diffs[:, dim],
                                       box_size[dim] - diffs[:, dim])
        if not np.all(np.sqrt(np.sum(diffs**2, axis=1)) >= min_xe_c):
            continue

        if check_distances(new_pos, positions[:placed], min_xe_xe, box_size):
            positions[placed] = new_pos
            placed += 1
            if placed % progress_step == 0:
                print(f"    Placed {placed}/{n_xe} Xe atoms")
            if placed == n_xe:
                break

    if placed < n_xe:
        print(f"  Warning: placed {placed}/{n_xe} Xe atoms "
              f"(max_attempts exhausted). Consider increasing max_attempts.")
        return positions[:placed] if placed > 0 else None

    print(f"  Successfully placed all {n_xe} Xe atoms")
    return positions


# =========================================================================== #
# Build and save one CNT+Xe system
# =========================================================================== #

def build_and_save(n, m, num_units, n_xe, defaults, label_suffix=""):
    """
    Build one CNT+Xe structure, write it to disk, and return a CSV report row.
    Returns None if placement fails.
    """
    min_xe_c         = defaults["min_xe_c"]
    min_xe_xe        = defaults["min_xe_xe"]
    max_attempts     = defaults["max_attempts"]
    narrow_threshold = defaults["narrow_radius_threshold"]
    vacuum_padding   = defaults["vacuum_padding"]
    output_format    = defaults["output_format"]

    cnt, radius, length = create_cnt(n, m, num_units)
    xy       = 2 * radius + vacuum_padding
    box_size = [xy, xy, length]

    # Centre tube in x-y
    pos = cnt.get_positions()
    cx, cy = np.mean(pos, axis=0)[:2]
    cnt.positions += [xy / 2 - cx, xy / 2 - cy, 0]
    pos = cnt.get_positions()

    n_c    = len(cnt)
    volume = calculate_volume(radius, length)

    print(f"\n{'─'*60}")
    print(f"  CNT ({n},{m})  ·  {num_units} unit cell(s){label_suffix}")
    print(f"  r = {radius:.2f} Å  ·  L = {length:.2f} Å  ·  "
          f"box = {xy:.1f}×{xy:.1f}×{length:.2f} Å")
    print(f"  C atoms = {n_c}  ·  Xe target = {n_xe}  ·  total = {n_c + n_xe}")
    print(f"  Linear density = {n_xe / length:.4f} atoms/Å  ·  "
          f"Geo max = {geometric_max_xe(radius, length)}  ·  "
          f"Loading = {n_xe / geometric_max_xe(radius, length) * 100:.1f}% of max")

    xe_pos = place_xe_atoms(pos, n_xe, radius, box_size,
                             min_xe_c, min_xe_xe, max_attempts, narrow_threshold)

    if xe_pos is None or len(xe_pos) == 0:
        print("  Skipping: failed to place any Xe atoms.")
        return None

    n_xe_placed = len(xe_pos)

    system      = cnt.copy()
    system.extend(Atoms("Xe" + str(n_xe_placed), positions=xe_pos))
    system.cell = np.diag(box_size)
    system.pbc  = [True, True, True]

    ext   = "xyz" if output_format == "extxyz" else output_format
    fname = f"cnt_{n}_{m}_u{num_units}_Xe{n_xe_placed}.{ext}"
    write(fname, system, format=output_format)
    print(f"  Saved → {fname}  ({n_c + n_xe_placed} atoms total)")

    r_pore          = radius - 1.7
    placement_mode  = "single-file" if radius < narrow_threshold else "random-disk"
    geo_max         = geometric_max_xe(radius, length)

    return {
        "filename":                fname,
        "chirality":               f"({n},{m})",
        "num_units":               num_units,
        "diameter_A":              round(2 * radius, 4),
        "radius_A":                round(radius, 4),
        "pore_radius_A":           round(r_pore, 4),
        "length_A":                round(length, 4),
        "box_x_A":                 round(xy, 4),
        "box_y_A":                 round(xy, 4),
        "box_z_A":                 round(length, 4),
        "volume_A3":               round(volume, 4),
        "geometric_max_Xe":        geo_max,
        "n_C":                     n_c,
        "n_Xe":                    n_xe_placed,
        "n_total":                 n_c + n_xe_placed,
        "Xe_linear_density_per_A": round(n_xe_placed / length, 6),
        "placement_mode":          placement_mode,
        "status":  "ok" if n_xe_placed == n_xe else f"partial ({n_xe_placed}/{n_xe})",
    }


# =========================================================================== #
# Entry point
# =========================================================================== #

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    print(f"Loading config: {config_path}")

    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    # ── Global settings ────────────────────────────────────────────────────
    raw      = cfg.get("settings", {})
    defaults = {
        "min_xe_c":               raw.get("min_xe_c",               3.86),
        "min_xe_xe":              raw.get("min_xe_xe",               4.32),
        "max_attempts":           raw.get("max_attempts",           300000),
        "narrow_radius_threshold":raw.get("narrow_radius_threshold",  5.0),
        "vacuum_padding":         raw.get("vacuum_padding",          17.0),
        "output_format":          raw.get("output_format",        "extxyz"),
    }

    # ── Xe density settings ────────────────────────────────────────────────
    xe_density_cfg = cfg.get("xe_density", {})

    report_rows = []

    # ── [[tubes]] blocks ───────────────────────────────────────────────────
    tubes = cfg.get("tubes", [])
    if tubes:
        print(f"\n{'='*60}")
        print(f"  Processing {len(tubes)} [[tubes]] block(s)")
        print(f"{'='*60}")

    for tube_cfg in tubes:
        n         = tube_cfg["n"]
        m         = tube_cfg["m"]
        num_units = tube_cfg.get("num_units", 1)

        # Per-tube overrides for placement settings
        local_defaults = defaults.copy()
        for key in ("min_xe_c", "min_xe_xe", "max_attempts",
                    "narrow_radius_threshold", "vacuum_padding"):
            if key in tube_cfg:
                local_defaults[key] = tube_cfg[key]

        # Determine n_xe — priority: n_xe > xe_density_mode > xe_linear_density
        if "n_xe" in tube_cfg:
            n_xe = int(tube_cfg["n_xe"])
            print(f"\n  ({n},{m}) u={num_units}: explicit n_xe = {n_xe}")

        elif "xe_density_mode" in tube_cfg:
            mode = tube_cfg["xe_density_mode"]
            _, radius, length = create_cnt(n, m, num_units)
            n_xe = n_xe_from_mode(mode, radius, length, xe_density_cfg)
            geo  = geometric_max_xe(radius, length)
            print(f"\n  ({n},{m}) u={num_units}: mode={mode}  "
                  f"geo_max={geo}  n_xe={n_xe}")

        elif "xe_linear_density" in tube_cfg:
            _, _, length = create_cnt(n, m, num_units)
            n_xe = max(1, round(tube_cfg["xe_linear_density"] * length))
            print(f"\n  ({n},{m}) u={num_units}: "
                  f"linear density={tube_cfg['xe_linear_density']:.4f} atoms/Å  "
                  f"n_xe={n_xe}")

        else:
            print(f"\n  ({n},{m}) u={num_units}: WARNING — no Xe loading specified, "
                  f"defaulting to 1 Xe")
            n_xe = 1

        row = build_and_save(n, m, num_units, n_xe, local_defaults)
        if row is not None:
            report_rows.append(row)

    # ── [[density_sweep]] blocks ───────────────────────────────────────────
    sweeps = cfg.get("density_sweep", [])
    if sweeps:
        print(f"\n{'='*60}")
        print(f"  Processing {len(sweeps)} [[density_sweep]] block(s)")
        print(f"{'='*60}")

    for sweep_cfg in sweeps:
        n         = sweep_cfg["n"]
        m         = sweep_cfg["m"]
        num_units = sweep_cfg.get("num_units", 1)
        n_points  = sweep_cfg.get("n_density_points",
                                  xe_density_cfg.get("n_density_points", 6))

        local_defaults = defaults.copy()
        for key in ("min_xe_c", "min_xe_xe", "max_attempts",
                    "narrow_radius_threshold", "vacuum_padding"):
            if key in sweep_cfg:
                local_defaults[key] = sweep_cfg[key]

        _, radius, length = create_cnt(n, m, num_units)
        pts = n_xe_sweep_points(radius, length, n_points, xe_density_cfg)

        print(f"\n  Density sweep ({n},{m}) u={num_units}:  "
              f"{n_points} points → {pts}")

        for n_xe in pts:
            row = build_and_save(n, m, num_units, n_xe, local_defaults,
                                 label_suffix=f"  [sweep: Xe={n_xe}]")
            if row is not None:
                report_rows.append(row)

    # ── CSV report ─────────────────────────────────────────────────────────
    report_path = config_path.replace(".toml", "_report.csv")
    if report_rows:
        fieldnames = list(report_rows[0].keys())
        with open(report_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_rows)
        print(f"\n  Report → {report_path}  ({len(report_rows)} structures)")

    print(f"\n{'='*60}")
    print("  All done.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
