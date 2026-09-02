# Code for Generating SWCNTs
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains the Python script and TOML configuration files used to generate the initial CNT + Xe atomic configurations used in the manuscript. Structures were built for both **armchair** and **zigzag** single-walled carbon nanotubes (SWCNTs) across a range of chiralities, tube lengths, and Xe loadings, covering the **transferability-test set** ((8,8), (14,0), (10,0), and (17,0)) and the **production-simulation set** used for the size, temperature, and density studies.

## Xe Loading Strategies
Each `[[tubes]]` block in a config file sets the Xe loading in one of three ways:
- **Explicit count**: `n_xe = <int>`, used throughout the transferability-test configs
- **Density mode**: `xe_density_mode = "low"` or `"high"`, a fraction (default 20% / 80%) of the geometric maximum Xe capacity of the tube, used in the production config
- **Linear density**: `xe_linear_density = <float>`, an explicit Xe atoms per angstrom along the tube axis
A `[[density_sweep]]` block generates several structures for one tube, evenly spaced in Xe count between the low and high loading values.
## CNT Construction and Xe Placement
- **Builder**: ASE `nanotube(n, m, length=num_units)`
- **Box length (z)**: taken from the true periodic cell vector `cell[2, 2]`, not the atom coordinate extent, to avoid a spurious PBC ring artifact at the zigzag/chiral cell boundary
- **Box cross section (x, y)**: `2 * radius + vacuum_padding`, with `vacuum_padding` (default 17 Å) chosen for a 15-20 Å gap between periodic images
- **Xe-C minimum distance**: 3.86 Å (`min_xe_c`)
- **Xe-Xe minimum distance**: 4.32 Å (`min_xe_xe`)
- **Placement strategy**: single file along the tube axis for narrow tubes (radius below `narrow_radius_threshold`, default 5.0 Å), random rejection sampling on the cross section for wide tubes
## Files in This Directory
| File | Purpose |
|---|---|
| [`generate_cnt_xe.py`](./generate_cnt_xe.py) | Structure generator script |
| [`config_transferability_8-8_and_14-0.toml`](./config_transferability_8-8_and_14-0.toml) | Transferability-test set, part 1, (8,8) and (14,0) |
| [`config_transferability_10-0_and_17-0.toml`](./config_transferability_10-0_and_17-0.toml) | Transferability-test set, part 2, (10,0) and (17,0) |
| [`config_production.toml`](./config_production.toml) | Production-simulation set, zigzag and chiral tube families, Cases 1-3 |
## Usage
```bash
python generate_cnt_xe.py config_transferability_8-8_and_14-0.toml
python generate_cnt_xe.py config_transferability_10-0_and_17-0.toml
python generate_cnt_xe.py config_production.toml
```
Running with no argument defaults to `config.toml` in the working directory. Python 3.11 or newer is required for the built-in `tomllib` parser. For older versions, install `tomli` with `pip install tomli`. ASE and NumPy are also required.
## Output Files
- `cnt_{n}_{m}_u{num_units}_Xe{n_xe}.xyz`: one extended-XYZ structure per generated system (cell, PBC flags, and species included)
- `{config_name}_report.csv`: one row per structure, reporting chirality, diameter, radius, effective pore radius, tube length, box dimensions, interior volume, carbon and Xe atom counts, Xe linear and volumetric density, geometric maximum Xe capacity (production runs only), placement strategy, and whether the target Xe count was fully placed
---
For further details, please refer to the respective folders or contact the author via the provided email.
