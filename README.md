# Supporting Code for “*Xenon Transport and NMR Response in Carbon Nanotubes from Equivariant Neural Networks*”

## Graphical Abstract

![Graphical Abstract](./blank.png)

---

📄 Author: **Ouail Zakary**

---

👤 Corresponding Author: **Ouail Zakary**  
- 📧 Email: [Ouail.Zakary@oulu.fi](mailto:Ouail.Zakary@oulu.fi)  
- 🔗 ORCID: [0000-0002-7793-3306](https://orcid.org/0000-0002-7793-3306)  
- 🌐 Website: [cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html](https://cc.oulu.fi/~nmrwww/members/Ouail_Zakary.html)  
- 📁 Personal Website: [ozakary.github.io](https://ozakary.github.io/)

---

This is the Supporting Code for the manuscript “*Xenon Transport and NMR Response in Carbon Nanotubes from Equivariant Neural Networks*”. [DOI: TBA]

The dataset comprises the following sections:

1. First principle calculations for generating the transferability dataset. ([directory](./dft_calculations/))
2. Procedure for processing and preparing the dataset for training Allegro.  ([directory](./mlip_dataset/))
3. Allegro model training, validation, and testing configuration scripts. ([directory](./configs_mlip/))
4. Transferability tests for the trained MLIP model. ([directory](./mlip_transferability/))
5. Procedure for processing and preparing the dataset for training SchNet.  ([directory](./nmr-ml_dataset/))
6. SchNet model training, validation, and testing configuration code. ([directory](./nmr-ml_config/))
7. Transferability tests for the trained NMR-ML model. ([directory](./nmr-ml_transferability/))
8. Python scripts for creating the initial Xe@SWCNTs models (i.e., SWCNTs with different radii and lengths). ([directory](./xe-at-swcnts_construction/))
9. LAMMPS MLMD simulation procedure and input scripts. ([directory](./mlmd_procedure/))
10. Procedure for computing the MSD and diffusion coefficients. ([directory](./msd_and_diff-coeff_procedure/))
11. Procedure for <sup>129</sup>Xe σ<sub>iso</sub> prediction using the trained NMR-ML model. ([directory](./nmr-ml_predict_procedure/))
12. Python scripts and raw numerical data for all figures included in the main manuscript and the Supporting Information. ([directory](./figures/))

## Citations
If you use the code in this repository, please cite the following:

### Paper  

```bibtex
@article{zakary_xe-at-cnts_2026,
  title={Xenon Transport and NMR Response in Carbon Nanotubes from Equivariant Neural Networks},
  author={Zakary, Ouail and Jacklin, Tiia and Lantto, Perttu},
  journal={ChemRxiv},
  volume={},
  pages={}, 
  year={2026},
  publisher={TBA},
  doi={TBA},
  url={TBA}
}
```

### Dataset  

```bibtex
@dataset{zakary_xe-at-cnts_2026,
  author = {Zakary, Ouail and Jacklin, Tiia and Lantto, Perttu},
  title = {Supporting Data for "Xenon Transport and NMR Response in Carbon Nanotubes from Equivariant Neural Networks"},
  year = {2026},
  publisher = {Zenodo},
  doi = {TBA},
  url = {TBA}
}
```

### Code  
```bibtex
@misc{zakary_xe-at-cnts_2026,
  author = {Zakary, Ouail and Jacklin, Tiia and Lantto, Perttu},
  title = {Supporting Code for "Xenon Transport and NMR Response in Carbon Nanotubes from Equivariant Neural Networks"},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/ozakary/data-Xe_at_CNTs}},
  url = {https://github.com/ozakary/data-Xe_at_CNTs}
}
```

---
For further details, please refer to the respective folders or contact the author via the provided email.
