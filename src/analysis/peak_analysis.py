import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.data_loader import load_curve
from src.core.baseline import compute_baseline
from src.core.peak_detection import smooth, find_peaks
from src.ui.theme import apply_mpl_style, PLOT_COLORS


def run(file_path, baseline_points, curve_index=1, apply_smoothing=True, output_dir=None, label=""):
    """
    Full peak analysis for one .DTA file.
    Returns dict: voltage, current, baseline, diff, peak_ox, peak_red, figures[(fig,title)...]
    """
    apply_mpl_style()
    voltage, current_raw = load_curve(file_path, curve_index)
    current = smooth(np.asarray(current_raw, dtype=float)) if apply_smoothing else np.asarray(current_raw, dtype=float)

    baseline = compute_baseline(voltage, current, baseline_points)
    diff = np.nan_to_num(current - baseline)
    peak_ox, peak_red = find_peaks(voltage, current, baseline)

    i1, i2, i3, i4 = baseline_points
    v = np.asarray(voltage, dtype=float)
    n_ticks = 5
    tick_idx = np.linspace(0, len(v) - 1, n_ticks, dtype=int)
    tick_lbl = [f"{v[i]:.2f}" for i in tick_idx]

    # ── Figure 1: CV with baseline ──────────────────────────────────────────
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(v, current, color=PLOT_COLORS[1], linewidth=1.8, label="CV Curve")
    ax1.scatter(v[[i1, i2, i3, i4]], current[[i1, i2, i3, i4]],
                color=PLOT_COLORS[3], zorder=5, s=60, label="Baseline points")
    ax1.plot(v[i1:i2 + 1], baseline[i1:i2 + 1], color=PLOT_COLORS[0],
             linestyle="--", linewidth=1.4, label="Baseline")
    ax1.plot(v[i3:i4 + 1], baseline[i3:i4 + 1], color=PLOT_COLORS[0],
             linestyle="--", linewidth=1.4)
    ax1.set_xlabel("Potential (V)", fontsize=13)
    ax1.set_ylabel("Current (nA)", fontsize=13)
    ax1.legend(fontsize=11)
    fig1.tight_layout()

    # ── Figure 2: Baseline-corrected peaks ──────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(diff, color=PLOT_COLORS[1], linewidth=1.8)
    ax2.axhline(0, color="#707A8C", linewidth=0.8, linestyle="--")
    ax2.annotate(f"Ox  {peak_ox[0]:.3f} V\n{peak_ox[1]:.2e} nA",
                 xy=(np.argmax(diff), peak_ox[1]),
                 xytext=(10, 10), textcoords="offset points",
                 color=PLOT_COLORS[0], fontsize=10,
                 arrowprops=dict(arrowstyle="->", color=PLOT_COLORS[0], lw=1))
    ax2.annotate(f"Red {peak_red[0]:.3f} V\n{peak_red[1]:.2e} nA",
                 xy=(np.argmin(diff), peak_red[1]),
                 xytext=(10, -30), textcoords="offset points",
                 color=PLOT_COLORS[3], fontsize=10,
                 arrowprops=dict(arrowstyle="->", color=PLOT_COLORS[3], lw=1))
    ax2.set_xlabel("Potential (V)", fontsize=13)
    ax2.set_ylabel("Peak Current (nA)", fontsize=13)
    ax2.set_xticks(tick_idx)
    ax2.set_xticklabels(tick_lbl)
    fig2.tight_layout()

    figures = [(fig1, "CV + Baseline"), (fig2, "Baseline-Corrected Peaks")]

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        stem = label or os.path.splitext(os.path.basename(file_path))[0]
        fig1.savefig(os.path.join(output_dir, f"{stem}_cv_baseline.png"), dpi=150)
        fig2.savefig(os.path.join(output_dir, f"{stem}_peaks.png"), dpi=150)

    return {
        "voltage": v,
        "current": current,
        "baseline": baseline,
        "diff": diff,
        "peak_ox": peak_ox,
        "peak_red": peak_red,
        "figures": figures,
    }
