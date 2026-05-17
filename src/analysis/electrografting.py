import os
import re
import math
import numpy as np
from matplotlib.figure import Figure

from src.core.data_loader import load_all_curves
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


_CYCLE_LABELS = ["1st Cycle", "2nd Cycle", "3rd Cycle", "4th Cycle", "5th Cycle"]


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

        fig = _single_fig(curves, label)
        per_file.append({"label": label, "figure": fig, "error": None, "curves": curves})

        if base_output_dir:
            m = re.match(r"^[A-Za-z0-9]+", label)
            dev = _sanitize(m.group()) if m else _sanitize(label)
            out = os.path.join(base_output_dir, _sanitize(experiment_type), dev)
            os.makedirs(out, exist_ok=True)
            save_for_paper(fig, os.path.join(out, f"{_sanitize(label)}_electrografting.png"))

    grid_fig = _grid_figure(per_file)
    return {"per_file": per_file, "grid_figure": grid_fig}


def _single_fig(curves, label):
    apply_mpl_style()
    fig = Figure(figsize=(8, 5))
    ax  = fig.add_subplot(111)
    for i, (v, c) in enumerate(curves):
        lbl = _CYCLE_LABELS[i] if i < len(_CYCLE_LABELS) else f"Cycle {i + 1}"
        ax.plot(np.asarray(v, dtype=float), np.asarray(c, dtype=float),
                color=PLOT_COLORS[i % len(PLOT_COLORS)], linewidth=1.8, label=lbl)
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
    grid_fig = Figure(figsize=(6 * cols, 4 * rows))
    axes = grid_fig.subplots(rows, cols, squeeze=False)
    for i, r in enumerate(valid):
        row, col = divmod(i, cols)
        ax = axes[row][col]
        src_lines = r["figure"].axes[0].lines
        for ln in src_lines:
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
