"""Shared matplotlib style for the paper's charts: one IEEE column wide, vector PDF, colour-blind-safe.

Colours are slots 1 and 2 of the dataviz reference palette (blue, orange); validated with validate_palette
(adjacent CVD delta E 24.7, normal-vision 33.6). Series also differ by marker and line style so that the
charts survive greyscale printing.
"""
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#d9d8d3"

COL_W = 3.5  # IEEE column width, inches

REPO = os.environ.get("ASTRO_REPO", "/home/user/astrofixer-baby/astrofixxer-android")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def setup():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Liberation Serif", "Times New Roman", "Nimbus Roman", "TeX Gyre Termes", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": MUTED,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.4,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    })


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path)
    print("wrote", os.path.normpath(path))
