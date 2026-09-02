# Procedure for Processing and Preparing the Dataset for Training MatTen
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the workflow for processing <sup>129</sup>Xe NMR magnetic shielding tensors and converting them into the JSON format required by the *MatTen* architecture.
## Overview
The dataset is built independently for each of the six NMR systems, {1,2,3}Xe@(10,0) and {1,2,3}Xe@(17,0), and only combined at the final JSON-conversion step.
## Workflow Pipeline
### Stage 1, Per-Frame NMR Extraction ([`nmr_vasp.py`](./nmr_vasp.py))
For each sampled MLMD snapshot, `nmr_vasp.py` reads the frame's `POSCAR` and `OUTCAR` and computes, for every atom, the non-diagonalized and diagonalized magnetic shielding tensor, the principal components (σ<sub>11</sub>, σ<sub>22</sub>, σ<sub>33</sub>), σ<sub>iso</sub>, σ<sub>csa</sub>, η<sub>csa</sub>, span, and skew, following the same Haeberlen-convention definitions used for the NMR calculations. Quadrupolar parameters (C<sub>Q</sub>, η<sub>Q</sub>) are also extracted when present in the `OUTCAR`. Run per system, looping over its frame directories, as in [`extract_nmr.txt`](./extract_nmr.txt).
```bash
for i in $(seq 1 1 250); do python3 nmr_vasp.py --poscar ./OUT_${i}/POSCAR --outcar ./OUT_${i}/OUTCAR --report ./OUT_${i}/nmr_report.txt --organized_report ./OUT_${i}/nmr_organized_report.md --csv OUT_${i}/nmr_data.csv; done
```
The frame count (250 above) and the `OUT_*` directory naming vary by system. Each run produces a `nmr_report.txt` per frame, the input expected by the merging step below. An optional `--sanity_check` flag compares the computed σ<sub>iso</sub>, span, and skew against VASP's own CSA tensor block for validation.
### Stage 2, Per-System Dataset Merging ([`schnet_nmr-dataset_builder.py`](./schnet_nmr-dataset_builder.py))
Reads every `POSCAR` and `nmr_report.txt` pair from the `OUT_*` frame directories of one system and merge them into four CSV files, `structures.csv`, `magnetic_shielding_tensors.csv`, `nmr_parameters.csv`, and `train.csv`.
```bash
python3 schnet_nmr-dataset_builder.py --base_dir ./ --pattern "OUT_*" --output ./schnet_nmr-dataset --prefix "cnt_10_0_u3_Xe1_frame_"
```
See [`instructions_schnet_nmr-dataset_builder.txt`](./instructions_schnet_nmr-dataset_builder.txt) for the general form and prefix options. This step is repeated once per system, with the `--prefix` and `--base_dir` changed accordingly, and the resulting `structures.csv` / `magnetic_shielding_tensors.csv` renamed per system (for example `structures_cnt_10_0_u3_Xe1.csv`) before Stage 3.
### Stage 3, Isotropic Shielding Integration (`code_data_cnt_*.py`)
One script per system recomputes σ<sub>iso</sub> directly from the tensor data, as a consistency-checked companion to the value already written by `nmr_vasp.py` in Stage 1, and merges it into the structure data.
```python
tensor_components = 0.5 * (tensor_components + np.transpose(tensor_components, (0, 2, 1)))
w, _ = np.linalg.eigh(tensor_components)
sigma_iso = np.mean(w, axis=1)
```
| Script | System |
|---|---|
| [`code_data_cnt_10_0_u3_Xe1.py`](./code_data_cnt_10_0_u3_Xe1.py) | 1Xe@(10,0) |
| [`code_data_cnt_10_0_u3_Xe2.py`](./code_data_cnt_10_0_u3_Xe2.py) | 2Xe@(10,0) |
| [`code_data_cnt_10_0_u3_Xe3.py`](./code_data_cnt_10_0_u3_Xe3.py) | 3Xe@(10,0) |
| [`code_data_cnt_17_0_u2_Xe1.py`](./code_data_cnt_17_0_u2_Xe1.py) | 1Xe@(17,0) |
| [`code_data_cnt_17_0_u2_Xe2.py`](./code_data_cnt_17_0_u2_Xe2.py) | 2Xe@(17,0) |
| [`code_data_cnt_17_0_u2_Xe3.py`](./code_data_cnt_17_0_u2_Xe3.py) | 3Xe@(17,0) |
Each script loads that system's `structures_cnt_*.csv` and `magnetic_shielding_tensors_cnt_*.csv`, symmetrizes the 3x3 tensor per atom, takes σ<sub>iso</sub> as the mean of its eigenvalues, and writes `structures_with_sigma_iso_cnt_*.csv`.
### Stage 4, JSON Conversion for MatTen ([`csv_to_json_converter_enhanced.py`](./csv_to_json_converter_enhanced.py))
Combines all six systems and produces the final training, validation, and test datasets.
#### Configuration ([`config.txt`](./config.txt))
Each line lists one system's structure CSV, tensor CSV, and flattened 3x3 lattice matrix.
```
../structures_with_sigma_iso_cnt_10_0_u3_Xe1.csv,../../magnetic_shielding_tensors_cnt_10_0_u3_Xe1.csv,24.8288703150 0.0000000000 0.0000000000 0.0000000000 24.8288703150 0.0000000000 0.0000000000 0.0000000000 12.7800000000
../structures_with_sigma_iso_cnt_17_0_u2_Xe1.csv,../../magnetic_shielding_tensors_cnt_17_0_u2_Xe1.csv,30.3090795355 0.0000000000 0.0000000000 0.0000000000 30.3090795355 0.0000000000 0.0000000000 0.0000000000 8.5200000000
```
The lattice values match the CNT simulation box dimensions from the structure-generation step.
#### Running the code
```bash
python csv_to_json_converter_enhanced.py config.txt
```
See [`usage_csv-to-json.txt`](./usage_csv-to-json.txt) for the config-file and direct command-line calling conventions.
#### JSON Structure for MatTen
```json
{
  "sigma_iso": {"0": [values], "1": [values], ...},
  "Qn": {"0": [values], "1": [values], ...},
  "structure": {"0": pymatgen_structure, "1": pymatgen_structure, ...},
  "species": {"0": [atomic_numbers], "1": [atomic_numbers], ...},
  "nmr_tensor": {"0": [3x3_matrices], "1": [3x3_matrices], ...},
  "atom_selector": {"0": [booleans], "1": [booleans], ...}
}
```
Only Xe atoms are flagged `True` in `atom_selector`, so carbon atoms contribute to the structure geometry but not to the NMR training targets.
**Tensor symmetry validation.** Every tensor is checked for symmetry and, if needed, symmetrized by averaging (`T_sym = (T + T^T) / 2`), with σ<sub>iso</sub> recalculated from the corrected tensor and the correction rate reported.
**Dataset splitting.** 80% training, 10% validation, 10% test, via `train_test_split` with a fixed random state (42).
#### Output Files
```
dataset_train.json                              # Training set (JSON)
dataset_val.json                                # Validation set (JSON)
dataset_test.json                                # Test set (JSON)
dataset_test_structures.xyz                     # Test structures (XYZ)
structures_with_sigma_iso_and_tensors.csv       # Test data (CSV)
```
## Systems Processed
| System | Tube box (Å) | Tube length (Å) |
|---|---|---|
| {1,2,3}Xe@(10,0) | 24.8288703150 x 24.8288703150 | 12.78 |
| {1,2,3}Xe@(17,0) | 30.3090795355 x 30.3090795355 | 8.52 |
## Data Flow Summary
```
VASP GIPAW Calculations (OUT_*/POSCAR, OUT_*/OUTCAR), per system
    ↓
Per-Frame NMR Extraction (nmr_vasp.py)
    ↓
Per-System Dataset Consolidation (schnet_nmr-dataset_builder.py)
    ↓
Isotropic Shielding Integration (code_data_cnt_*.py), per system
    ↓
JSON Formatting for MatTen (csv_to_json_converter_enhanced.py), all systems combined
    ↓
Training-Ready Dataset
├── dataset_train.json
├── dataset_val.json
└── dataset_test.json
```
## Files in This Directory
| File | Purpose |
|---|---|
| [`nmr_vasp.py`](./nmr_vasp.py) | Extracts per-atom NMR tensors and parameters from a VASP `OUTCAR`/`POSCAR` pair |
| [`extract_nmr.txt`](./extract_nmr.txt) | Example loop applying `nmr_vasp.py` across a system's sampled frames |
| [`schnet_nmr-dataset_builder.py`](./schnet_nmr-dataset_builder.py) | Consolidates per-frame `POSCAR` and `nmr_report.txt` files into per-system dataset CSVs |
| [`instructions_schnet_nmr-dataset_builder.txt`](./instructions_schnet_nmr-dataset_builder.txt) | Usage notes for `schnet_nmr-dataset_builder.py` |
| [`code_data_cnt_10_0_u3_Xe1.py`](./code_data_cnt_10_0_u3_Xe1.py) | σ<sub>iso</sub> integration for 1Xe@(10,0) |
| [`code_data_cnt_10_0_u3_Xe2.py`](./code_data_cnt_10_0_u3_Xe2.py) | σ<sub>iso</sub> integration for 2Xe@(10,0) |
| [`code_data_cnt_10_0_u3_Xe3.py`](./code_data_cnt_10_0_u3_Xe3.py) | σ<sub>iso</sub> integration for 3Xe@(10,0) |
| [`code_data_cnt_17_0_u2_Xe1.py`](./code_data_cnt_17_0_u2_Xe1.py) | σ<sub>iso</sub> integration for 1Xe@(17,0) |
| [`code_data_cnt_17_0_u2_Xe2.py`](./code_data_cnt_17_0_u2_Xe2.py) | σ<sub>iso</sub> integration for 2Xe@(17,0) |
| [`code_data_cnt_17_0_u2_Xe3.py`](./code_data_cnt_17_0_u2_Xe3.py) | σ<sub>iso</sub> integration for 3Xe@(17,0) |
| [`csv_to_json_converter_enhanced.py`](./csv_to_json_converter_enhanced.py) | Combines all systems and writes the train/val/test JSON datasets for MatTen |
| [`usage_csv-to-json.txt`](./usage_csv-to-json.txt) | Usage notes for `csv_to_json_converter_enhanced.py` |
| [`config.txt`](./config.txt) | Example configuration listing the six systems' CSV files and lattice parameters |
## Requirements
- Python 3, with `numpy`, `pandas`, `scikit-learn`, and `tqdm`
## Usage Instructions
```bash
# Stage 1-2: per system
for i in $(seq 1 1 N_FRAMES); do
    python3 nmr_vasp.py --poscar ./OUT_${i}/POSCAR --outcar ./OUT_${i}/OUTCAR \
        --report ./OUT_${i}/nmr_report.txt --organized_report ./OUT_${i}/nmr_organized_report.md \
        --csv ./OUT_${i}/nmr_data.csv
done
python3 schnet_nmr-dataset_builder.py --base_dir ./ --pattern "OUT_*" --output ./schnet_nmr-dataset --prefix "<system_prefix>"

# Stage 3: per system
python3 code_data_cnt_10_0_u3_Xe1.py   # repeat with the matching script for each system

# Stage 4: all systems combined
python csv_to_json_converter_enhanced.py config.txt
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
