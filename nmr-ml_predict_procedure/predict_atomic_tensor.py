#!/usr/bin/env python3
"""
Predict NMR tensors for Xe atoms from XYZ files using the matten model.

Enhanced version with:
- Incremental saving every N structures
- Resume functionality from interruptions
- Memory management
- Progress tracking

This script reads an XYZ file containing multiple structures with Xe and C atoms,
converts them to PyMatGen Structure objects, and predicts NMR tensors for Xe atoms.

Usage:
    python enhanced_xyz_nmr_predictor.py input.xyz [output.csv] [--save_every N] [--resume]
"""

import sys
import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
from matten.predict import predict
import re
import os
import argparse
import gc
from pathlib import Path
try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Install with 'pip install tqdm' for progress bars.")
    # Fallback: create a simple progress indicator
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total or (len(iterable) if iterable else 0)
            self.desc = desc
            self.current = 0
            if desc:
                print(f"{desc}: 0/{self.total}")
        
        def __iter__(self):
            for item in self.iterable:
                yield item
                self.update(1)
        
        def update(self, n=1):
            self.current += n
            if self.total > 0 and self.current % max(1, self.total // 20) == 0:
                print(f"{self.desc}: {self.current}/{self.total} ({self.current/self.total*100:.1f}%)")
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            if self.desc:
                print(f"{self.desc}: {self.total}/{self.total} (100.0%)")
        
        @staticmethod
        def write(s):
            print(s)


def get_progress_file(output_file):
    """Generate progress tracking filename."""
    output_path = Path(output_file)
    return output_path.parent / f".{output_path.stem}_progress.txt"


def save_progress(progress_file, structure_idx):
    """Save current progress to file."""
    with open(progress_file, 'w') as f:
        f.write(str(structure_idx))


def load_progress(progress_file):
    """Load progress from file."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 0
    return 0


def cleanup_progress(progress_file):
    """Remove progress file when complete."""
    if os.path.exists(progress_file):
        os.remove(progress_file)


def append_results_to_csv(results, output_file, write_header=False):
    """
    Append results to CSV file incrementally.
    
    Args:
        results (list): List of prediction results
        output_file (str): Output CSV filename
        write_header (bool): Whether to write CSV header
    """
    if not results:
        return
    
    df = pd.DataFrame(results)
    
    # Write or append to CSV
    if write_header or not os.path.exists(output_file):
        df.to_csv(output_file, index=False, mode='w')
        print(f"Created new CSV file: {output_file}")
    else:
        df.to_csv(output_file, index=False, mode='a', header=False)
        # Don't print append message here - it's handled in the main function


def count_existing_predictions(output_file):
    """Count how many predictions are already in the output file."""
    if not os.path.exists(output_file):
        return 0
    
    try:
        df = pd.read_csv(output_file)
        return len(df)
    except:
        return 0


def parse_xyz_file(xyz_file):
    """
    Parse XYZ file with multiple structures and extract lattice information.
    
    Args:
        xyz_file (str): Path to XYZ file
        
    Returns:
        list: List of dictionaries containing structure information
    """
    structures = []

    with open(xyz_file, 'r') as f:
        lines = f.readlines()

    i = 0
    structure_id = 0

    print("Parsing XYZ file...")
    
    while i < len(lines):
        # Skip empty lines
        if not lines[i].strip():
            i += 1
            continue

        # Read number of atoms
        try:
            num_atoms = int(lines[i].strip())
        except ValueError:
            i += 1
            continue

        # Read comment line with lattice information
        comment_line = lines[i + 1].strip()

        # Extract lattice parameters from comment line
        lattice_match = re.search(r'Lattice="([^"]+)"', comment_line)
        if lattice_match:
            lattice_str = lattice_match.group(1)
            lattice_values = [float(x) for x in lattice_str.split()]
            lattice_matrix = [
                [lattice_values[0], lattice_values[1], lattice_values[2]],
                [lattice_values[3], lattice_values[4], lattice_values[5]],
                [lattice_values[6], lattice_values[7], lattice_values[8]]
            ]
        else:
            # Default lattice if not found
            if structure_id % 100 == 0:  # Reduce warning frequency
                print(f"Warning: No lattice found for structure {structure_id}, using default")
            lattice_matrix = [[20.0, 0.0, 0.0], [0.0, 20.0, 0.0], [0.0, 0.0, 47.84310123]]

        # Read atomic coordinates
        atoms = []
        coordinates = []
        forces = []  # If available

        for j in range(num_atoms):
            line = lines[i + 2 + j].strip().split()

            if len(line) >= 4:
                atom = line[0]
                x, y, z = float(line[1]), float(line[2]), float(line[3])

                atoms.append(atom)
                coordinates.append([x, y, z])

                # Extract forces if available (columns 4, 5, 6)
                if len(line) >= 7:
                    fx, fy, fz = float(line[4]), float(line[5]), float(line[6])
                    forces.append([fx, fy, fz])

        # Store structure information
        structure_info = {
            'id': structure_id,
            'num_atoms': num_atoms,
            'lattice_matrix': lattice_matrix,
            'atoms': atoms,
            'coordinates': coordinates,
            'forces': forces if forces else None,
            'comment': comment_line
        }

        structures.append(structure_info)

        # Move to next structure
        i += num_atoms + 2
        structure_id += 1

        if structure_id % 1000 == 0:
            print(f"Parsed {structure_id} structures...")

    print(f"Total structures parsed: {len(structures)}")
    return structures


def create_pymatgen_structure(structure_info):
    """
    Convert structure information to PyMatGen Structure object.
    
    Args:
        structure_info (dict): Structure information from XYZ parsing
        
    Returns:
        Structure: PyMatGen Structure object
    """
    lattice = Lattice(structure_info['lattice_matrix'])
    species = structure_info['atoms']
    coords = structure_info['coordinates']

    # Create structure with Cartesian coordinates
    structure = Structure(lattice, species, coords, coords_are_cartesian=True)

    return structure


def predict_nmr_tensors_incremental(structures, model_path, checkpoint_name, output_file, 
                                   save_every=100, start_from=0):
    """
    Predict NMR tensors for all Xe atoms in the structures with incremental saving.
    
    Args:
        structures (list): List of structure information dictionaries
        model_path (str): Path to model directory
        checkpoint_name (str): Checkpoint filename
        output_file (str): Output CSV filename
        save_every (int): Save results every N structures
        start_from (int): Structure index to start from (for resume)
        
    Returns:
        int: Total number of predictions made
    """
    total_predictions = 0
    current_batch_results = []
    progress_file = get_progress_file(output_file)
    structures_processed_in_batch = 0
    
    # Count existing predictions
    existing_predictions = count_existing_predictions(output_file)
    if existing_predictions > 0:
        print(f"Found {existing_predictions} existing predictions in {output_file}")
    
    # Determine if we need to write header
    write_header = (start_from == 0 and existing_predictions == 0)
    
    print(f"Starting NMR tensor prediction for {len(structures)} structures...")
    if start_from > 0:
        print(f"Resuming from structure {start_from + 1}")
    print(f"Saving every {save_every} structures")

    # Process structures starting from start_from
    for i in range(start_from, len(structures)):
        structure_info = structures[i]
        
        print(f"Processing structure {i + 1}/{len(structures)}...")
        
        try:
            # Convert to PyMatGen structure
            structure = create_pymatgen_structure(structure_info)

            # Find Xe atom indices
            xe_indices = []
            for j, site in enumerate(structure.sites):
                if str(site.specie) == 'Xe':
                    xe_indices.append(j)

            if not xe_indices:
                print(f"  No Xe atoms found in structure {i + 1}")
                # Save progress and continue
                save_progress(progress_file, i + 1)
                structures_processed_in_batch += 1
                continue

            print(f"  Found {len(xe_indices)} Xe atoms at indices: {xe_indices}")

            # Predict NMR tensors
            tensors = predict(
                structure,
                model_identifier=model_path,
                checkpoint=checkpoint_name,
                is_atomic_tensor=True,
            )

            # Extract tensors for Xe atoms only
            structure_predictions = 0
            for xe_idx in xe_indices:
                if xe_idx < len(tensors):
                    tensor = tensors[xe_idx]

                    # Calculate isotropic shielding (sigma_iso)
                    sigma_iso = (tensor[0][0] + tensor[1][1] + tensor[2][2]) / 3.0

                    print(f"    Xe atom {xe_idx}: sigma_iso = {sigma_iso:.4f}")

                    result = {
                        'structure_id': structure_info['id'],
                        'atom_index': xe_idx,
                        'element': 'Xe',
                        'x': structure_info['coordinates'][xe_idx][0],
                        'y': structure_info['coordinates'][xe_idx][1],
                        'z': structure_info['coordinates'][xe_idx][2],
                        'sigma_iso': sigma_iso,
                        'tensor_xx': tensor[0][0],
                        'tensor_xy': tensor[0][1],
                        'tensor_xz': tensor[0][2],
                        'tensor_yx': tensor[1][0],
                        'tensor_yy': tensor[1][1],
                        'tensor_yz': tensor[1][2],
                        'tensor_zx': tensor[2][0],
                        'tensor_zy': tensor[2][1],
                        'tensor_zz': tensor[2][2]
                    }

                    current_batch_results.append(result)
                    total_predictions += 1
                    structure_predictions += 1
                else:
                    print(f"    Warning: Tensor not found for Xe atom {xe_idx}")

            # Save progress after processing structure
            save_progress(progress_file, i + 1)
            structures_processed_in_batch += 1
            
            # Save results incrementally every save_every STRUCTURES
            if structures_processed_in_batch >= save_every or i == len(structures) - 1:
                if current_batch_results:
                    batch_size = len(current_batch_results)
                    append_results_to_csv(current_batch_results, output_file, write_header)
                    print(f"  → Saved {batch_size} predictions from {structures_processed_in_batch} structures to CSV")
                    write_header = False  # Only write header once
                    
                    # Reset batch counters
                    current_batch_results.clear()
                    structures_processed_in_batch = 0
                    
                    # Memory management
                    gc.collect()

        except Exception as e:
            print(f"  Error predicting for structure {i + 1}: {e}")
            # Save progress even on error
            save_progress(progress_file, i + 1)
            structures_processed_in_batch += 1
            continue

    # Save any remaining results
    if current_batch_results:
        batch_size = len(current_batch_results)
        append_results_to_csv(current_batch_results, output_file, write_header)
        print(f"  → Saved final {batch_size} predictions from {structures_processed_in_batch} structures to CSV")
    
    # Clean up progress file when complete
    cleanup_progress(progress_file)
    
    return total_predictions


def print_final_statistics(output_file):
    """Print final statistics from the complete CSV file."""
    if not os.path.exists(output_file):
        print("No output file found!")
        return
    
    try:
        df = pd.read_csv(output_file)
        
        print(f"\n✅ Final Results Summary:")
        print(f"Total Xe predictions: {len(df)}")
        print(f"Unique structures: {df['structure_id'].nunique()}")
        
        if len(df) > 0:
            print("\nSigma_iso statistics:")
            print(f"  Mean: {df['sigma_iso'].mean():.4f}")
            print(f"  Std:  {df['sigma_iso'].std():.4f}")
            print(f"  Min:  {df['sigma_iso'].min():.4f}")
            print(f"  Max:  {df['sigma_iso'].max():.4f}")
            
            print(f"\nOutput saved to: {output_file}")
        
    except Exception as e:
        print(f"Error reading final results: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Enhanced XYZ NMR Tensor Predictor')
    parser.add_argument('xyz_file', help='Input XYZ file')
    parser.add_argument('output_file', nargs='?', default='nmr_predictions.csv',
                        help='Output CSV file (default: nmr_predictions.csv)')
    parser.add_argument('--save_every', type=int, default=100,
                        help='Save results every N structures (default: 100)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from previous progress')
    parser.add_argument('--model_path', default="/scratch/plantto/zakaryou/NMR-ML/matten/xe_tba_cc3_1_sym_pbe-svp_1000/training/matten_logs/matten_proj/b1xt05p9/checkpoints/",
                        help='Path to model directory')
    parser.add_argument('--checkpoint', default="last.ckpt",
                        help='Checkpoint filename')

    args = parser.parse_args()

    print(f"Enhanced XYZ NMR Tensor Predictor")
    print(f"Input XYZ file: {args.xyz_file}")
    print(f"Output CSV file: {args.output_file}")
    print(f"Model path: {args.model_path}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Save every: {args.save_every} structures")
    print(f"Resume mode: {args.resume}")
    print()

    # Check if input file exists
    if not os.path.exists(args.xyz_file):
        print(f"Error: Input file '{args.xyz_file}' not found!")
        sys.exit(1)

    # Parse XYZ file
    structures = parse_xyz_file(args.xyz_file)

    if not structures:
        print("No structures found in XYZ file!")
        sys.exit(1)

    # Determine starting point
    start_from = 0
    if args.resume:
        progress_file = get_progress_file(args.output_file)
        start_from = load_progress(progress_file)
        if start_from > 0:
            print(f"Resuming from structure {start_from}")
        else:
            print("No previous progress found, starting from beginning")

    # Check if we're already done
    if start_from >= len(structures):
        print("All structures already processed!")
        print_final_statistics(args.output_file)
        sys.exit(0)

    # Predict NMR tensors with incremental saving
    try:
        total_predictions = predict_nmr_tensors_incremental(
            structures, 
            args.model_path, 
            args.checkpoint,
            args.output_file,
            args.save_every,
            start_from
        )

        print(f"\n✅ NMR tensor prediction completed!")
        print(f"Processed {len(structures) - start_from} structures")
        print(f"Generated {total_predictions} new Xe NMR predictions")
        
        # Print final statistics
        print_final_statistics(args.output_file)

    except KeyboardInterrupt:
        print(f"\n⚠️  Prediction interrupted by user")
        print(f"Progress saved. Use --resume to continue from where you left off.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during prediction: {e}")
        print(f"Progress saved. Use --resume to continue from where you left off.")
        sys.exit(1)


if __name__ == "__main__":
    main()
