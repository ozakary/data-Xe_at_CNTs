#!/usr/bin/env python3
"""
NMR Dataset Builder for OUT_N directory structure
--------------------------------------------------
Reads POSCAR and nmr_report.txt from each OUT_N sub-directory and
consolidates them into four dataset files:

  structures.csv                  — molecule_name, atom_index, atom, x, y, z
  magnetic_shielding_tensors.csv  — molecule_name, atom_index, XX..ZZ
  nmr_parameters.csv              — molecule_name, atom_index, sigma_iso,
                                     sigma_csa, eta_csa, sigma_11, sigma_22,
                                     sigma_33, span, skew [, C_Q, eta_Q]
  train.csv                       — same columns as structures.csv

Usage
-----
  python nmr_dataset_builder.py \
      --base_dir . --pattern "OUT_*" --output ./dataset --prefix "frame_"

Author : Ouail Zakary (ouail.zakary@oulu.fi)
"""

import os
import re
import glob
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm


# ---------------------------------------------------------------------------
# POSCAR parser
# ---------------------------------------------------------------------------

def parse_poscar(poscar_file):
    """
    Parse a POSCAR file.  Returns a list of dicts:
      { atom_index, atom, x, y, z }
    Handles Direct / Cartesian coordinates and optional Selective Dynamics.
    """
    with open(poscar_file, 'r') as f:
        lines = f.readlines()

    scale = float(lines[1].strip())
    lattice = np.array([
        [float(x) * scale for x in lines[2].split()],
        [float(x) * scale for x in lines[3].split()],
        [float(x) * scale for x in lines[4].split()],
    ])

    atom_types  = lines[5].strip().split()
    atom_counts = [int(x) for x in lines[6].strip().split()]

    idx = 7
    if lines[idx].strip().lower().startswith('s'):   # Selective Dynamics
        idx += 1
    is_direct = lines[idx].strip().lower().startswith(('d', 'f'))
    idx += 1

    atoms = []
    atom_index = 0
    for atom_type, count in zip(atom_types, atom_counts):
        for j in range(count):
            parts = lines[idx + j].split()
            coords = np.array([float(x) for x in parts[:3]])
            if is_direct:
                coords = lattice.T @ coords
            atoms.append({
                'atom_index': atom_index,
                'atom':       atom_type,
                'x':          coords[0],
                'y':          coords[1],
                'z':          coords[2],
            })
            atom_index += 1
        idx += count

    return atoms


# ---------------------------------------------------------------------------
# nmr_report.txt parser
# ---------------------------------------------------------------------------

def parse_nmr_report(report_file):
    """
    Parse nmr_report.txt produced by nmr_vasp.py.

    Per-atom block format (separated by ####... lines):
      Ion Index.: N
      Ion Symbol: El
      Non-diagonalized Total Tensor:
        XX  XY  XZ
        YX  YY  YZ
        ZX  ZY  ZZ
      Principal Components [ppm]:
        sigma_11 = ...
        sigma_22 = ...
        sigma_33 = ...
      Magnetic Shielding Parameters:
        sigma_iso [ppm] = ...
        sigma_csa [ppm] = ...
        eta_csa        = ...
        span [ppm]     = ...
        skew           = ...
      [Quadrupolar Parameters:]        <- optional
        C_Q [MHz]      = ...
        eta_Q          = ...

    Returns
    -------
    tensors    : list of dicts  { atom_index, XX, YX, ZX, XY, YY, ZY, XZ, YZ, ZZ }
    parameters : list of dicts  { atom_index, sigma_iso, sigma_csa, eta_csa,
                                   sigma_11, sigma_22, sigma_33, span, skew
                                   [, C_Q, eta_Q] }
    """
    with open(report_file, 'r') as f:
        content = f.read()

    sections = re.split(r'#{10,}', content)

    tensors    = []
    parameters = []

    for section in sections:
        if not section.strip():
            continue

        # Ion index (1-based -> 0-based)
        m = re.search(r'Ion Index\.\s*:\s*(\d+)', section)
        if not m:
            continue
        atom_index = int(m.group(1)) - 1

        # ---- Non-diagonalized tensor ----
        tm = re.search(
            r'Non-diagonalized Total Tensor:\s*\n'
            r'\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\n'
            r'\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\n'
            r'\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)',
            section,
        )
        if tm:
            v = [float(tm.group(i)) for i in range(1, 10)]
            # rows: [XX XY XZ], [YX YY YZ], [ZX ZY ZZ]
            tensors.append({
                'atom_index': atom_index,
                'XX': v[0], 'XY': v[1], 'XZ': v[2],
                'YX': v[3], 'YY': v[4], 'YZ': v[5],
                'ZX': v[6], 'ZY': v[7], 'ZZ': v[8],
            })

        # ---- Scalar NMR parameters ----
        def _get(pattern):
            mm = re.search(pattern, section)
            return float(mm.group(1)) if mm else None

        sigma_11  = _get(r'sigma_11\s*=\s*([-\d.eE+]+)')
        sigma_22  = _get(r'sigma_22\s*=\s*([-\d.eE+]+)')
        sigma_33  = _get(r'sigma_33\s*=\s*([-\d.eE+]+)')
        sigma_iso = _get(r'sigma_iso\s*\[ppm\]\s*=\s*([-\d.eE+]+)')
        sigma_csa = _get(r'sigma_csa\s*\[ppm\]\s*=\s*([-\d.eE+]+)')
        eta_csa   = _get(r'eta_csa\s*=\s*([-\d.eE+]+)')
        span      = _get(r'span\s*\[ppm\]\s*=\s*([-\d.eE+]+)')
        skew      = _get(r'skew\s*=\s*([-\d.eE+]+)')
        c_q       = _get(r'C_Q\s*\[MHz\]\s*=\s*([-\d.eE+]+)')
        eta_q     = _get(r'eta_Q\s*=\s*([-\d.eE+]+)')

        if sigma_iso is not None:
            row = {
                'atom_index': atom_index,
                'sigma_iso':  sigma_iso,
                'sigma_csa':  sigma_csa,
                'eta_csa':    eta_csa,
                'sigma_11':   sigma_11,
                'sigma_22':   sigma_22,
                'sigma_33':   sigma_33,
                'span':       span,
                'skew':       skew,
            }
            if c_q is not None:
                row['C_Q']   = c_q
            if eta_q is not None:
                row['eta_Q'] = eta_q
            parameters.append(row)

    tensors.sort(   key=lambda d: d['atom_index'])
    parameters.sort(key=lambda d: d['atom_index'])
    return tensors, parameters


# ---------------------------------------------------------------------------
# Frame processor
# ---------------------------------------------------------------------------

def process_frame(frame_dir, molecule_name):
    poscar_file = os.path.join(frame_dir, 'POSCAR')
    report_file = os.path.join(frame_dir, 'nmr_report.txt')

    if not os.path.isfile(poscar_file):
        raise FileNotFoundError(f"POSCAR not found:         {poscar_file}")
    if not os.path.isfile(report_file):
        raise FileNotFoundError(f"nmr_report.txt not found: {report_file}")

    atoms     = parse_poscar(poscar_file)
    struct_df = pd.DataFrame(atoms)
    struct_df.insert(0, 'molecule_name', molecule_name)

    tensor_data, param_data = parse_nmr_report(report_file)

    tensors_df = pd.DataFrame(tensor_data)
    tensors_df.insert(0, 'molecule_name', molecule_name)
    # Reorder tensor columns to match target format
    tensor_cols = ['molecule_name', 'atom_index',
                   'XX', 'YX', 'ZX', 'XY', 'YY', 'ZY', 'XZ', 'YZ', 'ZZ']
    tensors_df = tensors_df[[c for c in tensor_cols if c in tensors_df.columns]]

    params_df = pd.DataFrame(param_data)
    params_df.insert(0, 'molecule_name', molecule_name)

    n_atoms = len(struct_df)
    if len(tensors_df) != n_atoms or len(params_df) != n_atoms:
        raise ValueError(
            f"Atom count mismatch in {frame_dir}: "
            f"POSCAR={n_atoms}, tensors={len(tensors_df)}, params={len(params_df)}"
        )

    train_df = struct_df.copy()

    return struct_df, tensors_df, params_df, train_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Consolidate per-frame NMR reports into a dataset.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--base_dir',  default='.',
                        help='Directory containing the OUT_N sub-directories.')
    parser.add_argument('--pattern',   default='OUT_*',
                        help='Glob pattern for frame directories.')
    parser.add_argument('--output',    default='./dataset',
                        help='Output directory for the consolidated CSV files.')
    parser.add_argument('--prefix',    default='frame_',
                        help='Prefix prepended to the directory name.')
    parser.add_argument('--verbosity', type=int, choices=[0, 1, 2], default=1)
    args = parser.parse_args()

    all_dirs = glob.glob(os.path.join(args.base_dir, args.pattern))
    if not all_dirs:
        print(f"No directories found matching: {os.path.join(args.base_dir, args.pattern)}")
        return 1

    def numeric_key(d):
        digits = ''.join(filter(str.isdigit, os.path.basename(d)))
        return int(digits) if digits else 0

    all_dirs = sorted(all_dirs, key=numeric_key)
    print(f"Found {len(all_dirs)} frame directories.")

    os.makedirs(args.output, exist_ok=True)
    structures_file = os.path.join(args.output, 'structures.csv')
    tensors_file    = os.path.join(args.output, 'magnetic_shielding_tensors.csv')
    params_file     = os.path.join(args.output, 'nmr_parameters.csv')
    train_file      = os.path.join(args.output, 'train.csv')

    success = 0
    skipped = 0
    first   = True

    for frame_dir in tqdm(all_dirs, desc='Building dataset',
                          disable=(args.verbosity == 0)):
        dir_name      = os.path.basename(frame_dir)
        molecule_name = f"{args.prefix}{dir_name}"

        try:
            struct_df, tensors_df, params_df, train_df = process_frame(
                frame_dir, molecule_name
            )
        except FileNotFoundError as e:
            if args.verbosity >= 1:
                print(f"  Skipping {dir_name}: {e}")
            skipped += 1
            continue
        except Exception as e:
            print(f"  Error in {dir_name}: {e}")
            skipped += 1
            continue

        mode   = 'w' if first else 'a'
        header = first

        struct_df.to_csv(structures_file, mode=mode, header=header, index=False)
        tensors_df.to_csv(tensors_file,   mode=mode, header=header, index=False)
        params_df.to_csv(params_file,     mode=mode, header=header, index=False)
        train_df.to_csv(train_file,       mode=mode, header=header, index=False)

        first = False
        success += 1

        if args.verbosity >= 2:
            print(f"  {molecule_name}: {len(struct_df)} atoms written")

    print(f"\nDone: {success} frames written, {skipped} skipped.")
    for path in [structures_file, tensors_file, params_file, train_file]:
        print(f"  {path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
