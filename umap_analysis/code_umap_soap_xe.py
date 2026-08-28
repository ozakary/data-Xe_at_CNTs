#!/usr/bin/env python3
# UMAP projection of SOAP-encoded Xe local environments, colored by system
#
# Requires: ase, dscribe, umap-learn, scikit-learn, numpy, matplotlib, seaborn
#   pip install ase dscribe umap-learn scikit-learn

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ase.io import read
from dscribe.descriptors import SOAP
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import umap

# Try to import the figure_formatting module
try:
    import figure_formatting_v2 as ff
    ff.set_rcParams(ff.master_formatting)
    FIGSIZE = (ff.FIGSIZE[0] * 1.6, ff.FIGSIZE[0])
except ImportError:
    print("figure_formatting_v2 module not available. Using default matplotlib settings.")
    FIGSIZE = (10, 7)

sns.set(style="whitegrid")
sns.set_context("paper", font_scale=1.2)


# -----------------------------------------------------------------------
# 1. Dataset sources
#    - (8,8) and (14,0) files each hold a single fixed loading (4 Xe/frame)
#    - (10,0) and (17,0) files mix 1, 2 and 3 Xe per frame; frames are
#      assigned to a system by counting the Xe atoms actually present
# -----------------------------------------------------------------------
SOURCES = [
    {'file': './8_8_cnt/xe_cnt_8-8_all.xyz',                          'fixed_label': '4Xe@(8,8)'},
    {'file': './14_0_cnt/xe_cnt_14-0_all.xyz',                        'fixed_label': '4Xe@(14,0)'},
    {'file': './10_0_cnt/cnt_10_0_u3_Xe1-2-3_all_frames.xyz',         'label_template': '{n}Xe@(10,0)'},
    {'file': './17_0_cnt/cnt_17_0_u2_Xe1-2-3_all_frames.xyz',         'label_template': '{n}Xe@(17,0)'},
]

# Color per system: one hue family per chirality, shade intensity tracks
# Xe loading (lighter = fewer Xe, darker = more Xe)
SYSTEM_COLORS = {
    '4Xe@(8,8)':   '#264653',
    '4Xe@(14,0)':  '#2A9D8F',
    '1Xe@(10,0)':  '#F6D18A',
    '2Xe@(10,0)':  '#EF9B4E',
    '3Xe@(10,0)':  '#B4530A',
    '1Xe@(17,0)':  '#D8B7E8',
    '2Xe@(17,0)':  '#9D4EDD',
    '3Xe@(17,0)':  '#5A189A',
}

# SOAP descriptor settings (adjust to taste)
SOAP_SPECIES = ['C', 'Xe']
SOAP_RCUT = 14.0      # local environment cutoff radius, Angstrom
SOAP_NMAX = 10
SOAP_LMAX = 8
SOAP_SIGMA = 0.5

# UMAP settings
UMAP_N_NEIGHBORS = 30
UMAP_MIN_DIST = 0.5
UMAP_N_COMPONENTS = 2
UMAP_METRIC = 'cosine'
UMAP_RANDOM_STATE = 42


def load_labeled_frames(sources):
    """
    Read every source file and return a flat list of (ase.Atoms, system_label)
    pairs, one entry per frame, with frames from mixed files split by their
    actual Xe count.
    """
    labeled_frames = []

    for source in sources:
        filename = source['file']
        print(f"Reading {filename} ...")
        try:
            frames = read(filename, index=':')
        except Exception as e:
            print(f"  Could not read {filename}: {e}")
            continue

        for atoms in tqdm(frames, desc=f"  Labeling {filename}", unit="frame"):
            n_xe = int(np.sum(np.array(atoms.get_chemical_symbols()) == 'Xe'))

            if 'fixed_label' in source:
                label = source['fixed_label']
            else:
                if n_xe == 0:
                    continue
                label = source['label_template'].format(n=n_xe)

            labeled_frames.append((atoms, label))

        print(f"  {len(frames)} frames read")

    return labeled_frames


def compute_soap_per_xe(labeled_frames, soap):
    """
    Compute one SOAP vector per Xe atom (its local environment), across all
    frames.

    Returns:
    - X: (n_points, n_features) SOAP feature matrix
    - y: (n_points,) array of system labels, one per Xe atom
    """
    feature_rows = []
    system_labels = []

    for atoms, label in tqdm(labeled_frames, desc="  Computing SOAP", unit="frame"):
        xe_indices = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == 'Xe']
        if not xe_indices:
            continue

        soap_vectors = soap.create(atoms, centers=xe_indices)
        feature_rows.append(soap_vectors)
        system_labels.extend([label] * len(xe_indices))

    X = np.vstack(feature_rows)
    y = np.array(system_labels)
    return X, y


def main():
    labeled_frames = load_labeled_frames(SOURCES)
    if not labeled_frames:
        raise SystemExit("No frames were read. Check the file paths above.")

    print(f"\nTotal frames read: {len(labeled_frames)}")

    soap = SOAP(
        species=SOAP_SPECIES,
        r_cut=SOAP_RCUT,
        n_max=SOAP_NMAX,
        l_max=SOAP_LMAX,
        sigma=SOAP_SIGMA,
        periodic=True,
    )

    print("\nComputing SOAP descriptors for each Xe local environment...")
    X, y = compute_soap_per_xe(labeled_frames, soap)
    print(f"SOAP feature matrix: {X.shape[0]} Xe environments x {X.shape[1]} features")

    for label in sorted(set(y)):
        print(f"  {label}: {np.sum(y == label)} points")

    print("\nStandardizing features...")
    X_scaled = StandardScaler().fit_transform(X)

    print("Running UMAP...")
    reducer = umap.UMAP(
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        n_components=UMAP_N_COMPONENTS,
        metric=UMAP_METRIC,
        random_state=UMAP_RANDOM_STATE,
        verbose=True,
    )
    embedding = reducer.fit_transform(X_scaled)

    print("Creating UMAP plot...")
    fig, ax = plt.subplots(figsize=FIGSIZE)

    system_order = [
        '4Xe@(8,8)', '4Xe@(14,0)',
        '1Xe@(10,0)', '2Xe@(10,0)', '3Xe@(10,0)',
        '1Xe@(17,0)', '2Xe@(17,0)', '3Xe@(17,0)',
    ]

    for label in system_order:
        mask = y == label
        if not np.any(mask):
            continue
        ax.scatter(
            embedding[mask, 0], embedding[mask, 1],
            s=18, alpha=0.75, linewidths=0,
            color=SYSTEM_COLORS.get(label, '#999999'),
            label=label,
        )

    # No spines, ticks, tick labels, or axis titles
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
          ncol=4, frameon=False, markerscale=1.5)

    plt.tight_layout()
    plt.savefig('umap_xe_soap.png', dpi=300, bbox_inches='tight')
    plt.savefig('umap_xe_soap.svg', format='svg', bbox_inches='tight')

    print("Done!")
    plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
