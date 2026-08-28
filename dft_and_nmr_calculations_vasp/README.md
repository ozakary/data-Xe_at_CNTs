# Single-Point and <sub>129</sub>Xe NMR Parameter Calculations Using VASP
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory contains example VASP input files for the ground-state electronic-structure and <sup>129</sup>Xe NMR calculations performed on snapshots sampled from the MLMD trajectories. Two calculation types were carried out. **Single-point** calculations, run on all five Xe@SWCNT systems, give the total energy, atomic forces, and stress tensor. **NMR** calculations, run only on the {1,2,3}Xe@(10,0) and {1,2,3}Xe@(17,0) systems. The example set here, [`INCAR`](./INCAR), [`KPOINTS`](./KPOINTS), [`POSCAR`](./POSCAR), and [`POTCAR`](./POTCAR), corresponds to the combined single-point + NMR run for the 1Xe@(10,0) system.
## Computational Parameters ([`INCAR`](./INCAR))
- **Functional**: PBE-GGA
- **Dispersion correction**: D3(BJ) (`IVDW=12`), accounting for Xe-Xe and Xe-C van der Waals interactions
- **Plane-wave cutoff**: 850 eV (`ENCUT=850`)
- **Precision**: Normal
- **Electronic convergence**: 1×10<sup>-6</sup> eV (`EDIFF=1e-6`)
- **Smearing**: Gaussian, 0.01 eV (`ISMEAR=0`, `SIGMA=0.01`)
- **Real-space projection**: Automatic (`LREAL=A`)
- **Symmetry**: Disabled (`ISYM=0`)
- **Wave functions / charge density**: Not written (`LWAVE=FALSE`, `LCHARG=FALSE`)
- **Start from**: Existing wave functions (`ISTART=2`)
- **NMR magnetic shielding**: Enabled via GIPAW (`LCHIMAG=.TRUE.`, `DQ=0.003`, `ICHIBARE=1`)
- **Electric field gradient**: `LEFG=.TRUE.` with `QUAD_EFG=33.27 -393`
For systems where only the single-point quantities are needed (6Xe@(7,6), 4Xe@(8,8), 4Xe@(14,0)), the same INCAR is used with the `LCHIMAG`, `DQ`, `ICHIBARE`, `LEFG`, and `QUAD_EFG` lines removed.
## k-Point Sampling ([`KPOINTS`](./KPOINTS))
Γ-centered meshes, chosen per system according to tube size.
| System | Atoms | k-mesh | Calculation |
|---|---|---|---|
| 6Xe@(7,6) | 514 | 1×1×1 | Single-point |
| 4Xe@(8,8) | 260 | 1×1×1 | Single-point |
| 4Xe@(14,0) | 284 | 1×1×1 | Single-point |
| {1,2,3}Xe@(10,0) | 121-123 | 1×1×6 | Single-point + NMR |
| {1,2,3}Xe@(17,0) | 137-139 | 1×1×9 | Single-point + NMR |
The example [`KPOINTS`](./KPOINTS) file (1×1×6) corresponds to the {1,2,3}Xe@(10,0) systems.
## Pseudopotentials ([`POTCAR`](./POTCAR))
| Element | Pseudopotential | Core Configuration | Valence Electrons |
|---|---|---|---|
| **C** | PAW_PBE C_GW_new 19Mar2012 | [He] | 2s<sup>2</sup>2p<sup>2</sup> (4 electrons) |
| **Xe** | PAW_PBE Xe_GW 08Jan2009 | [Xe] | 5s<sup>2</sup>5p<sup>6</sup> (8 electrons) |
## NMR Parameter Definitions
The <sup>129</sup>Xe magnetic shielding tensor σ is computed with the GIPAW approach and reported using the Haeberlen convention, with components ordered as |σ<sub>zz</sub> − σ<sub>iso</sub>| ≥ |σ<sub>xx</sub> − σ<sub>iso</sub>| ≥ |σ<sub>yy</sub> − σ<sub>iso</sub>|.
- Isotropic shielding, σ<sub>iso</sub> = (σ<sub>xx</sub> + σ<sub>yy</sub> + σ<sub>zz</sub>) / 3
- Shielding anisotropy, σ<sub>CSA</sub> = σ<sub>zz</sub> − σ<sub>iso</sub>
- Shielding asymmetry, η<sub>CSA</sub> = (σ<sub>yy</sub> − σ<sub>xx</sub>) / σ<sub>CSA</sub>
The chemical shift δ follows the same convention and is obtained from δ<sub>iso</sub> ≈ σ<sub>iso</sub><sup>ref</sup> − σ<sub>iso</sub>, using a reference <sup>129</sup>Xe σ<sub>iso</sub><sup>ref</sup> of 5847.6 ppm.
## Requirements
- **VASP** (used version here is 6.4.1)
---
For further details, please refer to the respective folders or contact the author via the provided email.
