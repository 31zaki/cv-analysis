import os
import re
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.data_loader import load_all_curves
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS

_CYCLE_LABELS = ["1st Cycle", "2nd Cycle", "3rd Cycle", "4th Cycle", "5th Cycle"]
_PAPER_COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd"]


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


def run(data_dir, max_cycles=3, experiment_type="electrografting", base_output_dir=None):
    apply_mpl_style()

    dta_files = sorted(f for f in os.listdir(data_dir) if f.upper().endswith(".DTA"))
    if not dta_files:
        raise FileNotFoundError(f"No .DTA files in: {data_dir}")

    per_file = []
    for fname in dta_files:
        path  = os.path.join(data_dir, fname)
        label = os.path.splitext(fname)[0]
        try:
            curves = load_all_curves(path, max_curves=max_cycles)
        except Exception as e:
            per_file.append({"label": label, "error": str(e), "figure": None, "curves": []}); continue

        # Screen figure (Ayu dark)
        fig = _single_fig(curves, label, paper=False)
        per_file.append({"label": label, "figure": fig, "error": None, "curves": curves})

        # Paper save — per device subfolder
        if base_output_dir:
            dev = _sanitize(re.match(r"^[A-Za-z0-9]+", label).group()) if re.match(r"^[A-Za-z0-9]+", label) else _sanitize(label)
            out = os.path.join(base_output_dir, _sanitize(experiment_type), dev)
            os.makedirs(out, exist_ok=True)
            pfig = _single_fig(curves, label, paper=True)
            save_for_paper(pfig, os.path.join(out, f"{_sanitize(label)}_electrografting.png"))
            plt.close(pfig)

    # Grid figure (screen only — overview, not exported individually)
    grid_fig = _grid_figure(per_file)

    return {"per_file": per_file, "grid_figure": grid_fig}


def _single_fig(curves, label, paper=False):
    colors = _PAPER_COLORS if paper else PLOT_COLORS
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (v, c) in enumerate(curves):
        lbl = _CYCLE_LABELS[i] if i < len(_CYCLE_LABELS) else f"Cycle {i + 1}"
        ax.plot(np.asarray(v, dtype=float), np.asarray(c, dtype=float),
                color=colors[i % len(colors)], linewidth=1.8, label=lbl)
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Current (nA)", fontsize=13)
    ax.set_title(label, fontsize=12)
    ax.legend(fontsize=11, loc="best")
    fig.tight_layout()
    return fig


def _grid_figure(per_file):
    valid = [r for r in per_file if r["figure"] is not None]
    if not valid:
        return None
    cols = min(3, len(valid))
    rows = math.ceil(len(valid) / cols)
    apply_mpl_style()
    grid_fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), squeeze=False)
    for i, r in enumerate(valid):
        row, col = divmod(i, cols)
        ax = axes[row][col]
        for v, c in r["curves"]:
            src_lines = r["figure"].axes[0].lines
            for j, ln in enumerate(src_lines):
                ax.plot(ln.get_xdata(), ln.get_ydata(),
                        color=ln.get_color(), linewidth=1.4, label=ln.get_label())
        ax.set_title(r["label"], fontsize=10)
        ax.set_xlabel("Potential (V)", fontsize=9)
        ax.set_ylabel("Current (nA)", fontsize=9)
        ax.legend(fontsize=8)
    for i in range(len(valid), rows * cols):
        row, col = divmod(i, cols)
        grid_fig.delaxes(axes[row][col])
    grid_fig.tight_layout()
    return grid_fig
