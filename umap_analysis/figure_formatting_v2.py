import matplotlib
import matplotlib.image as image
from matplotlib import rc, rcParams
import matplotlib.pyplot as plt
import numpy as np

# ── Colors ────────────────────────────────────────────────────────────────────

nearly_black  = '#161616'
light_grey    = '#EEEEEE'
lighter_grey  = '#F5F5F5'
white         = '#FFFFFF'
light_blue    = '#6d9fd1'

# dark blue, teal, gold, orange, light orange
# colors = ['#264653', '#2A9D8F', '#E9C46A', '#E76F51', '#F3B6A5']

tableau10 = [
    '#4379a7', '#f28e2b', '#e15759',
    '#76b7b2', '#59a14f', '#edc948',
    '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac',
]

# ── Font sizes ────────────────────────────────────────────────────────────────

fontsize_1 = 20   # general font
fontsize_2 = 22   # axis labels
fontsize_3 = 22   # title
fontsize_4 = 20   # tick labels
fontsize_5 = 18   # legend

# ── Universal figure dimensions ───────────────────────────────────────────────
#
# FIGSIZE controls the total canvas size (inches).
# AX_BOX controls the axes rectangle [left, bottom, width, height] in
# figure-fraction units.  These fractions are chosen so that the physical
# size of the black frame is:
#
#   frame_width  = FIGSIZE[0] * AX_BOX[2]  inches
#   frame_height = FIGSIZE[1] * AX_BOX[3]  inches
#
# Both quantities stay constant regardless of tick-label length, because
# apply_fixed_layout() sets the axes position explicitly after the figure
# is created, overriding matplotlib's automatic margin algorithm.
#
# To change the universal frame size, edit these two constants only.

# Two named canvas/frame presets. Use FIGSIZE_1/AX_BOX_1 for one plot type
# (e.g. histograms) and FIGSIZE_2/AX_BOX_2 for another (e.g. 2D heatmaps).
# Each preset's frame size is:
#   frame_width  = FIGSIZE_n[0] * AX_BOX_n[2]  inches
#   frame_height = FIGSIZE_n[1] * AX_BOX_n[3]  inches
# All plots using the same preset share exactly that frame size in the
# saved SVG/PNG, so they align perfectly in Inkscape without manual resizing.

FIGSIZE_1 = (3.5, 3.5)          # e.g. histograms
AX_BOX_1  = (0.22, 0.18,
              0.70, 0.72)

FIGSIZE_2 = (3.5, 3.5)          # e.g. 2D heatmaps
AX_BOX_2  = (0.22, 0.18,
              0.70, 0.72)

# Backward-compatible aliases — kept so existing scripts using
# ff.FIGSIZE / ff.AX_BOX without specifying a preset keep working unchanged.
FIGSIZE = FIGSIZE_1
AX_BOX  = AX_BOX_1


# ── rcParams dict ─────────────────────────────────────────────────────────────

master_formatting = {
    'xtick.major.pad':      12,
    'ytick.major.pad':      12,
    'ytick.color':          nearly_black,
    'xtick.color':          nearly_black,
    'xtick.direction':      'out',
    'xtick.major.size':     8,
    'ytick.direction':      'out',
    'ytick.right':          False,
    'ytick.major.size':     8,
    'xtick.major.width':    1.5,
    'ytick.major.width':    1.5,
    'axes.labelcolor':      nearly_black,
    'axes.labelsize':       fontsize_2,
    'legend.facecolor':     light_grey,
    'pdf.fonttype':         42,
    'ps.fonttype':          42,
    'mathtext.fontset':     'custom',
    'font.size':            fontsize_1,
    'mathtext.rm':          'Helvetica Neue',
    'mathtext.it':          'Helvetica Neue:italic',
    'mathtext.bf':          'Helvetica Neue:bold',
    'savefig.bbox':         'tight',
    'axes.facecolor':       white,
    'axes.labelpad':        10.0,
    'axes.titlesize':       fontsize_3,
    'axes.titlepad':        32,
    'axes.spines.right':    False,
    'axes.spines.left':     True,
    'axes.spines.top':      False,
    'axes.spines.bottom':   True,
    'axes.linewidth':       1.5,
    'lines.markersize':     10.0,
    'lines.markeredgewidth': 1.5,
    'lines.linewidth':      2.0,
    'lines.scale_dashes':   False,
    'xtick.labelsize':      fontsize_4,
    'ytick.labelsize':      fontsize_4,
    'legend.fontsize':      fontsize_5,
    'text.latex.preamble':  r'\usepackage{amssymb}\usepackage{amsmath}',
}


# ── Functions ─────────────────────────────────────────────────────────────────

def set_rcParams(formatting):
    """Apply a formatting dict to matplotlib rcParams."""
    for k, v in formatting.items():
        if k == 'text.latex.preamble' and isinstance(v, list):
            v = '\n'.join(v)
        rcParams[k] = v


def make_figure(figsize=None, ax_box=None, preset=None):
    """
    Create a figure with a universal canvas size and return (fig, ax).

    The axes box is positioned using ax_box so the physical frame size is
    fixed regardless of tick-label length.  Call this instead of
    plt.subplots() in every plotting script to guarantee identical frame
    sizes across all figures that share the same preset.

    Parameters
    ----------
    figsize : tuple (width, height) in inches, optional
        Override the figure size for this call only.
    ax_box : tuple (left, bottom, width, height), optional
        Override the axes box fractions for this call only.
    preset : int or None, optional
        Pick a named preset: 1 -> FIGSIZE_1/AX_BOX_1, 2 -> FIGSIZE_2/AX_BOX_2.
        Ignored if figsize and ax_box are both given explicitly.
        Leave as None to use preset 1 (the default/backward-compatible size).

    Returns
    -------
    fig, ax
    """
    presets = {
        1: (FIGSIZE_1, AX_BOX_1),
        2: (FIGSIZE_2, AX_BOX_2),
    }
    default_fs, default_box = presets.get(preset, (FIGSIZE_1, AX_BOX_1))

    fs  = figsize if figsize is not None else default_fs
    box = ax_box  if ax_box  is not None else default_box

    fig = plt.figure(figsize=fs)
    ax  = fig.add_axes(box)
    return fig, ax


def apply_fixed_layout(fig, ax):
    """
    Fix the axes box of an existing (fig, ax) pair to AX_BOX.

    Use this when you cannot call make_figure() — e.g. after plt.subplots()
    or when a third-party function creates the figure.  Call it just before
    plt.savefig().

    Parameters
    ----------
    fig : matplotlib Figure
    ax  : matplotlib Axes
    """
    ax.set_position(AX_BOX)
