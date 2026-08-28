# Procedure for <sup>129</sup>Xe σ<sub>iso</sub> Prediction Using the Trained NMR-ML Model
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the script and job files used to apply a trained NMR-ML (MatTen) model to the production MLMD trajectories, predicting the <sup>129</sup>Xe magnetic shielding tensor for every Xe atom in every sampled snapshot. The example job files use the NMR-ML3 checkpoint, trained on the combined {1,2,3}Xe@(10,0) and {1,2,3}Xe@(17,0) dataset (see [`nmr-ml_matten/`](../nmr-ml_matten/)), applied here to trajectories from all the production systems.
## Input Data
Each production trajectory (100,000 snapshots, see [`mlmd_procedure_lammps/`](../mlmd_procedure_lammps/)) is split into chunks, extended-XYZ files with only species and Cartesian positions, and processed one chunk at a time.
```
1170
Lattice="23.86466077 0.0 0.0 0.0 23.86466077 0.0 0.0 0.0 23.86466077" Properties=species:S:1:pos:R:3
C  ...
Xe  6.82709 11.3068 8.4432
```
## Prediction Script ([`predict_atomic_tensor.py`](./predict_atomic_tensor.py))
Reads a multi-frame XYZ file, converts each frame to a PyMatGen `Structure`, identifies the Xe atoms, and predicts a magnetic shielding tensor for each with the trained MatTen model.
```python
tensors = predict(structure, model_identifier=model_path, checkpoint=checkpoint_name, is_atomic_tensor=True)
sigma_iso = (tensor[0][0] + tensor[1][1] + tensor[2][2]) / 3.0
```
The script's built-in `--model_path` default points to a checkpoint from an earlier, unrelated study, it is always overridden on the command line, as in the job scripts below.
```bash
python3 predict_atomic_tensor.py <input.xyz> <output.csv> \
  --save_every N \
  [--resume] \
  --model_path <path/to/checkpoints/> \
  --checkpoint last.ckpt
```
## Job Submission
### [`script_predict.job`](./script_predict.job)
| Setting | Value |
|---|---|
| Cluster | LUMI, `standard-g` partition |
| GPU | 1x AMD MI250x |
| CPUs | 7, exclusive node, no hyperthreading |
| Walltime | 24:00:00 |
```bash
python3 predict_atomic_tensor.py cnt_traj_out_chunk_01.xyz output_prediction_chunk_01.csv \
  --save_every 1 \
  --model_path ".../matten_proj_xe_swcnts_10_0_and_17_0/4491y9lt/checkpoints/" \
  --checkpoint "last.ckpt"
```
### [`script_predict_resume.job`](./script_predict_resume.job)
Identical, with `--resume` added, for continuing a chunk after the walltime limit or an interruption stops it partway through.
## Output Format
One row per Xe atom per structure.
| Column | Description | Units |
|---|---|---|
| structure_id | Frame index within the chunk | - |
| atom_index | Atom index within the structure | - |
| element | Always `Xe` | - |
| x, y, z | Cartesian coordinates | Å |
| sigma_iso | Isotropic shielding | ppm |
| tensor_xx ... tensor_zz | Full 3x3 shielding tensor components | ppm |
## Files in This Directory
| File | Purpose |
|---|---|
| [`predict_atomic_tensor.py`](./predict_atomic_tensor.py) | Predicts Xe shielding tensors for every structure in an XYZ chunk |
| [`script_predict.job`](./script_predict.job) | SLURM job, first pass over a chunk |
| [`script_predict_resume.job`](./script_predict_resume.job) | SLURM job, resumes an interrupted chunk |
## Usage
```bash
sbatch script_predict.job
# if the walltime limit is hit before a chunk finishes
sbatch script_predict_resume.job
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
