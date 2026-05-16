import os
import numpy as np
from matplotlib.figure import Figure

from src.core.data_loader import load_curve
from src.core.peak_detection import smooth
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS


def run(file_path, curve_index=1, apply_smoothing=True,
        smooth_derivative=False, base_output_dir=None,
        experiment_type="differential", device_name=None):
    """
    Compute and plot dI/dV for a single .DTA file.

    Parameters
    ----------
    apply_smoothing    : Savitzky-Golay on raw current before differentiation
    smooth_derivative  : Savitzky-Golay on the dI/dV result itself
    """
    voltage, current_raw = load_curve(file_path, curve_index)
    v = np.asarray(voltage, dtype=float)
    c = np.asarray(current_raw, dtype=float)

    if apply_smoothing:
        c = smooth(c)

    # dI/dV via numpy.gradient (central differences, handles non-uniform spacing)
    didv = np.gradient(c, v)

    if smooth_derivative:
        didv = smooth(didv)

    device = device_name or os.path.splitext(os.path.basename(file_path))[0]

    screen_figs = [
        (_screen_fig(v, c, didv, device), "dI/dV"),
    ]

    if base_output_dir:
        import re
        def _san(s): return re.sub(r"[^a-zA-Z0-9_\-]", "_", s).strip("_")
        out = os.path.join(base_output_dir, _san(experiment_type), _san(device))
        os.makedirs(out, exist_ok=True)
        pfig = _paper_fig(v, c, didv, device)
        save_for_paper(pfig, os.path.join(out, f"{_san(device)}_didv.png"))
        pfig.clf()

    return {"voltage": v, "current": c, "didv": didv, "figures": screen_figs}


def _screen_fig(v, c, didv, label):
    apply_mpl_style()
    fig = Figure(figsize=(9, 8))

    # Top: raw CV
    ax1 = fig.add_subplot(211)
    ax1.plot(v, c, color=PLOT_COLORS[1], linewidth=1.6, label="CV")
    ax1.set_ylabel("Current (nA)", fontsize=12)
    ax1.set_title(label, fontsize=11)
    ax1.legend(fontsize=10)

    # Bottom: dI/dV
    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.plot(v, didv, color=PLOT_COLORS[0], linewidth=1.6, label="dI/dV")
    ax2.axhline(0, color="#707A8C", linewidth=0.8, linestyle="--")
    ax2.set_xlabel("Potential (V)", fontsize=12)
    ax2.set_ylabel("dI/dV  (nA / V)", fontsize=12)
    ax2.legend(fontsize=10)

    fig.tight_layout()
    return fig


def _paper_fig(v, c, didv, label):
    fig = Figure(figsize=(9, 8))

    ax1 = fig.add_subplot(211)
    ax1.plot(v, c, color="#1565C0", linewidth=1.6, label="CV")
    ax1.set_ylabel("Current (nA)", fontsize=12)
    ax1.set_title(label, fontsize=11)
    ax1.legend(fontsize=10)

    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.plot(v, didv, color="#C07000", linewidth=1.6, label="dI/dV")
    ax2.axhline(0, color="#888888", linewidth=0.8, linestyle="--")
    ax2.set_xlabel("Potential (V)", fontsize=12)
    ax2.set_ylabel("dI/dV  (nA / V)", fontsize=12)
    ax2.legend(fontsize=10)

    fig.tight_layout()
    return fig
