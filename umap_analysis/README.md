# Code for Performing UMAP Analysis
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the script used to visualize the structural diversity of the Xe local environments sampled across the 4Xe@(8,8), 4Xe@(14,0), {1,2,3}Xe@(10,0), and {1,2,3}Xe@(17,0) transferability-test systems. For every Xe atom in the dataset, a Smooth Overlap of Atomic Positions (SOAP) descriptor is computed and the resulting feature matrix is projected into two dimensions with Uniform Manifold Approximation and Projection (UMAP).
## Data Sources
| File | Labeling |
|---|---|
| `8_8_cnt/xe_cnt_8-8_all.xyz` | Fixed, all frames labeled `4Xe@(8,8)` |
| `14_0_cnt/xe_cnt_14-0_all.xyz` | Fixed, all frames labeled `4Xe@(14,0)` |
| `10_0_cnt/cnt_10_0_u3_Xe1-2-3_all_frames.xyz` | Mixed, labeled `1Xe@(10,0)`, `2Xe@(10,0)`, or `3Xe@(10,0)` by Xe count |
| `17_0_cnt/cnt_17_0_u2_Xe1-2-3_all_frames.xyz` | Mixed, labeled `1Xe@(17,0)`, `2Xe@(17,0)`, or `3Xe@(17,0)` by Xe count |
These trajectory files are part of the same [Zenodo repository](./).
## SOAP Descriptor Settings
Generated with DScribe, one vector per Xe atom, centered on its local environment.
| Setting | Value |
|---|---|
| Species | C, Xe |
| Cutoff radius (`r_cut`) | 14 Å |
| Radial basis truncation (`n_max`) | 10 |
| Angular basis truncation (`l_max`) | 8 |
| Gaussian smearing width (`sigma`) | 0.5 Å |
| Periodic | True |
Frames with multiple Xe atoms contribute multiple SOAP vectors, one per Xe atom.
## UMAP Settings
The standardized SOAP feature matrix (zero mean, unit variance per feature, via scikit-learn) is reduced to two dimensions with umap-learn.
| Setting | Value |
|---|---|
| `n_neighbors` | 30 |
| `min_dist` | 0.5 |
| `n_components` | 2 |
| `metric` | cosine |
| `random_state` | 42 |
## Files in This Directory
| File | Purpose |
|---|---|
| [`code_umap_soap_xe.py`](./code_umap_soap_xe.py) | Reads the trajectories, computes per-Xe SOAP descriptors, runs UMAP, and produces the embedding plot |
|[`figure_formatting_v2.py`](./figure_formatting_v2.py) | An optional custom matplotlib style module |
## Requirements
- Python packages, `ase`, `dscribe`, `umap-learn`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `tqdm`
  ```bash
  pip install ase dscribe umap-learn scikit-learn numpy matplotlib seaborn tqdm
  ```
## Usage
```bash
python code_umap_soap_xe.py
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
