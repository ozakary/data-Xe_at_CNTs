# LAMMPS MLMD Simulation Procedure and Input Scripts
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory documents the production MLMD procedure used to generate the trajectories for the twenty initial configurations, run with LAMMPS using the fine-tuned atomistic foundation model (FT-AFM) through the `pair_symmetrix` interface, on LUMI with 8 AMD MI250x GPUs per simulation. [`xe_cnt_lammps.in`](./xe_cnt_lammps.in) shows the complete script for one system, 13Xe@(22,0) at 100 K.
## Simulation Protocol
1. **Energy minimization**, energy and force tolerances of 10<sup>-4</sup> and 10<sup>-6</sup>, up to 1000 iterations and 10,000 force evaluations
2. **Equilibration**, 100 ps NVT at `TEMP`, velocities initialized at `TEMP`
3. **Production**, 10 ns NVT at `TEMP`
Both NVT stages use a Nose-Hoover thermostat (damping constant 100 timesteps), a 1 fs timestep, and a binning neighbor list with a 1 Å skin distance, rebuilt every step after a 5-step delay. 100,000 snapshots are sampled per trajectory (every 100 steps).
## Force Field
```lammps
pair_style    symmetrix/mace
pair_coeff    * * ../../../../../fine-tuned_mace-omat-0-medium-54-6.json C Xe
```
The FT-AFM is the MACE-OMAT-0-medium model fine-tuned on the (7,6) Xe@SWCNT dataset (see [`ft-afm_mace/`](../ft-afm_mace/)), loaded through LAMMPS-Symmetrix's `pair_symmetrix` interface.
## SLURM Job Script ([`lammps-gpu.sh`](./lammps-gpu.sh))
| Setting | Value |
|---|---|
| Cluster | LUMI, `standard-g` partition |
| GPUs | 8x AMD MI250x, one per MPI task |
| CPUs per task | 7 |
| Walltime | 48:00:00 |
```bash
srun --ntasks=8 --gpus-per-task=1 --gpu-bind=closest \
  $SYMMETRIX_BASE/bin/lmp \
  -in xe_cnt_lammps.in \
  -k on g 1 \
  -sf kk \
  -pk kokkos newton on neigh half
```
## Files in This Directory
| File | Purpose |
|---|---|
| [`xe_cnt_lammps.in`](./xe_cnt_lammps.in) | Complete LAMMPS input, minimization, equilibration, and 10 ns production |
| [`lammps-gpu.sh`](./lammps-gpu.sh) | SLURM job for `xe_cnt_lammps.in` |
## Usage
```bash
sbatch lammps-gpu.sh
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
