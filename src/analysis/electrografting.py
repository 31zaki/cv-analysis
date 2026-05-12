import os
import re
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.data_loader import load_all_curves
from src.ui.theme import apply_mpl_style, PLOT_COLORS

_CYCLE_LABELS = ["1st Cycle", "2nd Cycle", "3rd Cycle", "4th Cycle", "5th Cycle"]


def run(data_dir, max_cycles=3, output_dir=None):
    """
    Plot multi-cycle CV curves for every .DTA file in data_dir.
    Returns dict with per-file figures and a summary grid figure.
    """
    apply_mpl_style()

    dta_files = sorted(f for f in os.listdir(data_dir) if f.upper().endswith(".DTA"))
    if not dta_files:
        raise FileNotFoundError(f"No .DTA files in: {data_dir}")

    per_file = []
    for fname in dta_files:
        path = os.path.join(data_dir, fname)
        label = os.path.splitext(fname)[0]
        try:
            curves = load_all_curves(path, max_curves=max_cycles)
        except Exception as e:
            per_file.append({"label": label, "error": str(e), "figure": None})
            continue

        fig = _single_device_figure(curves, label)
        per_file.append({"label": label, "figure": fig, "error": None})

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            fig.savefig(os.path.join(output_dir, f"{label}_electrografting.png"), dpi=150)

    grid_fig = _grid_figure(per_file)
    if output_dir and grid_fig:
        grid_fig.savefig(os.path.join(output_dir, "all_devices_grid.png"), dpi=150)

    return {"per_file": per_file, "grid_figure": grid_fig}


def _single_device_figure(curves, label):
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (v, c) in enumerate(curves):
        lbl = _CYCLE_LABELS[i] if i < len(_CYCLE_LABELS) else f"Cycle {i + 1}"
        ax.plot(np.asarray(v, dtype=float), np.asarray(c, dtype=float),
                color=PLOT_COLORS[i % len(PLOT_COLORS)], linewidth=1.8, label=lbl)
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Current (nA)", fontsize=13)
    ax.set_title(label, fontsize=13)
    ax.legend(fontsize=11, loc="best")
    fig.tight_layout()
    return fig


def _grid_figure(per_file):
    valid = [r for r in per_file if r["figure"] is not None]
    if not valid:
        return None

    cols = min(3, len(valid))
    rows = math.ceil(len(valid) / cols)
    grid_fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), squeeze=False)

    for i, r in enumerate(valid):
        row, col = divmod(i, cols)
        ax = axes[row][col]
        src_ax = r["figure"].axes[0]
        for line in src_ax.lines:
            ax.plot(line.get_xdata(), line.get_ydata(),
                    color=line.get_color(), linewidth=1.4, label=line.get_label())
        ax.set_title(r["label"], fontsize=11)
        ax.set_xlabel("Potential (V)", fontsize=9)
        ax.set_ylabel("Current (nA)", fontsize=9)
        ax.legend(fontsize=8)

    for i in range(len(valid), rows * cols):
        row, col = divmod(i, cols)
        grid_fig.delaxes(axes[row][col])

    grid_fig.tight_layout()
    return grid_fig
