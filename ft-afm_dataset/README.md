# Procedure for Processing and Preparing the Dataset for Fine-Tuning MACE-OMAT-0
---
📄 Author: **Ouail Zakary** 
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)
---
This directory documents the procedure used to turn the 1500 single-point VASP calculations of the 6Xe@(7,6) system into the training, validation, and test sets used to fine-tune MACE-OMAT-0.
## Step 1, OUTCAR to XYZ Conversion
Each of the 1500 sampled snapshots has its own VASP `OUTCAR`, containing the converged total energy, atomic forces, and stress tensor. Each `OUTCAR` is converted to an extended-XYZ file with ASE.
```bash
for i in $(seq 1 1 1500); do ase convert OUTCAR.${i} snapshot_${i}.xyz; done
```
### Extended-XYZ Format
```
514
Lattice="20.0 0.0 0.0 0.0 20.0 0.0 0.0 0.0 47.84310123" Properties=species:S:1:pos:R:3:forces:R:3 energy=-4675.3534552 stress="-0.005413435627134075 0.00027086901304508164 -0.0009012239857045355 0.00027086901304508164 -0.004427607985228192 0.0003476895073664528 -0.0009012239857045355 0.0003476895073664528 -0.01084025929134317" free_energy=-4675.3534552 pbc="T T T"
C       11.71187000      14.25840000      46.66362000       0.60352300      -0.62469100       0.12496000
C       11.58331000      14.17414000       1.30175000      -1.32780600       1.47428900      -2.00977000
...
Xe       9.41947000      10.60908000      32.63503000       0.14067100      -0.15048700      -0.03715600
Xe      11.06250000       9.92570000      36.42016000      -0.74025300       0.06873100       0.00377100
Xe       9.53863000      10.71110000      42.60055000       0.18742300      -0.09395700       0.00187200
Xe      10.02510000      10.94340000       2.20571000       0.05067800      -0.28714400       0.00156900
514
Lattice="20.0 0.0 0.0 0.0 20.0 0.0 0.0 0.0 47.84310123" Properties=species:S:1:pos:R:3:forces:R:3 energy=-4676.80830489 stress="-0.004368463444751322 0.00048451587042406554 -0.0010015624864122348 0.00048451587042406554 -0.003437692154844855 -0.0015095713971861248 -0.0010015624864122348 -0.0015095713971861248 -0.009992306586028047" free_energy=-4676.80830489 pbc="T T T"
C       10.30858000      14.23397000      46.25715000      -1.36409800       0.02501800      -0.40577300
...
```
## Step 2, Concatenation
The 1500 XYZ files are concatenated into one XYZ file.
```bash
cat snapshot_*.xyz > cnt_7_6_u1_Xe6_tiia_all_frames.xyz
```
## Step 3, Train / Validation / Test Split
We use [`xyz_splitter.py`](https://github.com/ozakary/xyz-dataset-splitter/blob/main/xyz_splitter.py) from the repository [`xyz-dataset-splitter`](https://github.com/ozakary/xyz-dataset-splitter). This splits the XYZ file into training, validation, and test sets, and rewrites the extended-XYZ header of every frame to the property names expected by MACE.
```bash
python xyz_splitter.py ./cnt_7_6_u1_Xe6_tiia_all_frames.xyz --train_size 1200 --valid_size 150 --test_size 150 --rand_split true --output_prefix ./swcnt_7_6_dataset --seed 123
```
---
For further details, please refer to the respective folders or contact the author via the provided email.
