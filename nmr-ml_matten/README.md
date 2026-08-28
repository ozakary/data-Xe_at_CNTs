# Input Files for Training MatTen
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the configuration file, training scripts, and SLURM job scripts used to train *MatTen* (version 0.0.1), an E(3)-equivariant graph neural network, on the <sup>129</sup>Xe magnetic shielding tensor. Three models were trained, NMR-ML1, NMR-ML2, and NMR-ML3, sharing an identical architecture and training protocol, and differing only in the atomic-graph cutoff radius and the training set.
## Models Trained
| Model | Dataset | Snapshots | `r_cut` | Train / Val / Test |
|---|---|---|---|---|
| NMR-ML1 | {1,2,3}Xe@(10,0) | 750 | 5.5 Å | 600 / 75 / 75 |
| NMR-ML2 | {1,2,3}Xe@(17,0) | 750 | 10.0 Å | 600 / 75 / 75 |
| NMR-ML3 | {1,2,3}Xe@(10,0) + {1,2,3}Xe@(17,0) | 1500 | 10.0 Å | 1200 / 150 / 150 |
## Directory Structure
```
./
├── configs/
│   └── atomic_tensor.yaml           # Model configuration (shown here for NMR-ML3)
├── datasets/
│   ├── dataset_train.json           # Training dataset
│   ├── dataset_val.json             # Validation dataset
│   └── dataset_test.json            # Test dataset
├── matten_logs/                     # Training logs and checkpoints (Weights & Biases)
├── train_atomic_tensor.py           # Training script, from scratch
├── train_atomic_tensor_resume_v2.py # Training script, resumes from the latest checkpoint
├── script_train.job                 # SLURM job, from scratch
└── script_train_resume_v2.job       # SLURM job, resume
```
## Model Configuration ([`configs/atomic_tensor.yaml`](./configs/atomic_tensor.yaml))
### Core Settings
```yaml
seed_everything: 35
log_level: info
```
### Data
```yaml
data:
  tensor_target_name: nmr_tensor
  atom_selector: atom_selector
  tensor_target_formula: ij=ji     # target tensor symmetrized before training
  r_cut: 10                        # 5.5 for NMR-ML1, 10.0 for NMR-ML2 and NMR-ML3
  loader_kwargs:
    batch_size: 4
    shuffle: true
```
### Model Architecture
```yaml
species_embedding_dim: 64          # atomic species embedding
irreps_edge_sh: 0e + 1o + 2e       # spherical harmonics, edge direction
radial_basis_type: bessel
num_radial_basis: 16
radial_basis_start: 0.
radial_basis_end: 5.

num_layers: 3                      # message passing conv layers
invariant_layers: 2                # radial network layers
invariant_neurons: 64              # hidden neurons per radial layer
average_num_neighbors: auto        # determined from the training set

conv_layer_irreps: 64x0o+64x0e + 32x1o+32x1e + 16x2o+16x2e
nonlinearity_type: gate
normalization: batch
resnet: true

output_format: irreps              # loss computed in irreps space
output_formula: ij=ji
reduce: mean                       # node to graph pooling
```
### Training Parameters
```yaml
trainer:
  max_epochs: 5000
  accelerator: cuda
  devices: 1
  callbacks:
    - ModelCheckpoint, monitor val/score, mode min, save_top_k 3, save_last true
    - EarlyStopping, monitor val/score, mode min, patience 150
    - ModelSummary, max_depth -1
  logger:
    WandbLogger, save_dir matten_logs, project matten_proj_xe_swcnts_10_0_and_17_0
```
### Optimization
```yaml
optimizer:
  Adam, lr 0.005, weight_decay 0.00001
lr_scheduler:
  ReduceLROnPlateau, mode min, factor 0.5, patience 50
```
All three models use the same seed (35), so differences between them come only from `r_cut` and the training data.
## Training Scripts
### [`train_atomic_tensor.py`](./train_atomic_tensor.py)
Loads `configs/atomic_tensor.yaml`, builds the `TensorDataModule` and `AtomicTensorModel`, and runs `trainer.fit` followed by `trainer.test(ckpt_path="best")`. This is the entry point used for the first submission of each model.
### [`train_atomic_tensor_resume_v2.py`](./train_atomic_tensor_resume_v2.py)
Same setup, but before training it searches `matten_logs/` recursively for the most recently modified `last.ckpt` and, if one is found, resumes `trainer.fit` from it, otherwise it starts from scratch. Used with [`script_train_resume_v2.job`](./script_train_resume_v2.job) to continue a model across successive job submissions after the walltime limit is reached.
## Job Submission
### [`script_train.job`](./script_train.job)
| Setting | Value |
|---|---|
| Cluster | Puhti supercomputer, CSC |
| Partition | `gpu` |
| GPU | 1x Nvidia V100 (`gpu:v100:1`), 32 GB |
| CPUs / memory | 20 cores, 8 GB per CPU |
### [`script_train_resume_v2.job`](./script_train_resume_v2.job)
Same cluster and GPU request, with `--mem-per-cpu=9G` and `--time=36:00:00`, and runs `python3 train_atomic_tensor_resume_v2.py` instead.
## Files in This Directory
| File | Purpose |
|---|---|
| [`configs/atomic_tensor.yaml`](./configs/atomic_tensor.yaml) | MatTen model, data, and training configuration (NMR-ML3 values shown) |
| [`train_atomic_tensor.py`](./train_atomic_tensor.py) | Training script, from scratch |
| [`train_atomic_tensor_resume_v2.py`](./train_atomic_tensor_resume_v2.py) | Training script, resumes from the latest checkpoint |
| [`script_train.job`](./script_train.job) | SLURM job, from scratch |
| [`script_train_resume_v2.job`](./script_train_resume_v2.job) | SLURM job, resume |
## Requirements
- Access to the Puhti supercomputer at CSC, IT Center for Science (Finland), with a single Nvidia V100 GPU (32 GB)
- `python-data/3.10` module and a Python virtual environment with MatTen installed
- `pytorch-lightning`, `torch`, `loguru`, `pyyaml`, `wandb`
- The `dataset_train/val/test.json` files for the relevant model, from the [previous step](../nmr-ml_dataset/), placed under `datasets/`
## Usage
```bash
# First submission
sbatch script_train.job

# If the walltime limit is hit before training finishes, resubmit with the resume script
sbatch script_train_resume_v2.job
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
