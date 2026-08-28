# Input Files for Fine-Tuning MACE-OMAT-0 Using MACE
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the SLURM batch job ([`script_mace_fm_fine-tuning.job`](./script_mace_fm_fine-tuning.job)) used to fine-tune the MACE-OMAT-0-medium foundation model on the (7,6) Xe@SWCNT dataset prepared in the previous step. The job script also serves as the MACE training configuration, since `mace_run_train` takes all of its settings as command-line arguments. The training, validation, and test dataset files can be found in the [Zenodo repository](../README.md#dataset) associated with this work. The atomistic foundation model `mace-omat-0-medium.model` is available in the [mace-foundations](https://github.com/ACEsuit/mace-foundations) repository.
## Fine-Tuning Configuration (`mace_run_train`)
**Model and task**  
- `--name="fine-tuned_mace-omat-0-medium"`, run name used to tag output files
- `--foundation_model="./mace-omat-0-medium.model"`, the pretrained MACE-OMAT-0-medium checkpoint being fine-tuned
- `--multiheads_finetuning=False`, single-head fine-tuning on the Xe@SWCNT dataset only, rather than joint multi-head training with the foundation model's original data  
**Dataset**  
- `--train_file`, `--valid_file`, `--test_file`, the three split files from the previous step (`swcnt_7_6_dataset_train/valid/test.xyz`)
- `--E0s="foundation"`, isolated-atom reference energies are inherited from the foundation model rather than recomputed  
**Loss and evaluation**  
- `--loss="universal"`, combined energy, forces, and stress loss
- `--energy_weight=10`, `--forces_weight=10`, `--stress_weight=10`
- `--stress_key="REF_stress"`, matching the header field written by `xyz_splitter.py`
- `--compute_stress=True`, `--compute_forces=True`, `--compute_avg_num_neighbors=True`
- `--error_table="PerAtomMAE"`, `--eval_interval=1`  
**Optimizer and scheduling**  
- `--scaling="rms_forces_scaling"`
- `--lr=0.0001`, `--weight_decay=1e-8`
- `--ema`, `--ema_decay=0.995`, exponential moving average of model weights
- `--scheduler_patience=5`
- `--amsgrad`, `--clip_grad=10`  
**Batching and epochs**  
- `--batch_size=1`, `--valid_batch_size=4`
- `--max_num_epochs=1500`, `--patience=50`  
**Device and reproducibility**  
- `--device="cuda"`, `--default_dtype="float64"`
- `--seed=3`
- `--enable_cueq=True`, cuEquivariance-accelerated equivariant tensor operations on GPU
- `--restart_latest`, resumes from the latest checkpoint if the job is requeued after hitting the walltime limit  
## Requirements
- `pytorch/2.7` module and a Python virtual environment with MACE installed
- The `mace-omat-0-medium.model` foundation model and the fine-tuning dataset, from the Zenodo archive referenced above
## Usage
```bash
sbatch script_mace_fm_fine-tuning.job
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
