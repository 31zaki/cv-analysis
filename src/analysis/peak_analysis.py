import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.data_loader import load_curve
from src.core.baseline import compute_baseline
from src.core.peak_detection import smooth, find_peaks
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


def _paper_cv_figure(v, current, baseline, pts, peak_ox, peak_red):
    """
    Paper-ready CV + baseline figure.
    Shows the curve and baseline lines only — NO selection point markers.
    """
    i1, i2, i3, i4 = pts
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(v, current, color="black", linewidth=1.6, label="CV Curve")
    ax.plot(v[i1:i2 + 1], baseline[i1:i2 + 1],
            color="#1565C0", linestyle="--", linewidth=1.4, label="Baseline")
    ax.plot(v[i3:i4 + 1], baseline[i3:i4 + 1],
            color="#1565C0", linestyle="--", linewidth=1.4)
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Current (nA)", fontsize=13)
    ax.legend(fontsize=11)
    fig.tight_layout()
    return fig


def _paper_peaks_figure(v, diff, peak_ox, peak_red):
    """Paper-ready baseline-corrected peaks figure."""
    n_t = 5
    t_idx = np.linspace(0, len(v) - 1, n_t, dtype=int)
    t_lbl = [f"{v[i]:.2f}" for i in t_idx]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(diff, color="black", linewidth=1.6)
    ax.axhline(0, color="#888888", linewidth=0.8, linestyle="--")
    ax.annotate(
        f"Ox  {peak_ox[0]:.3f} V\n{peak_ox[1]:.2e} nA",
        xy=(int(np.argmax(diff)), peak_ox[1]),
        xytext=(10, 10), textcoords="offset points",
        color="#1565C0", fontsize=10,
        arrowprops=dict(arrowstyle="->", color="#1565C0", lw=1),
    )
    ax.annotate(
        f"Red  {peak_red[0]:.3f} V\n{peak_red[1]:.2e} nA",
        xy=(int(np.argmin(diff)), peak_red[1]),
        xytext=(10, -30), textcoords="offset points",
        color="#C62828", fontsize=10,
        arrowprops=dict(arrowstyle="->", color="#C62828", lw=1),
    )
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Peak Current (nA)", fontsize=13)
    ax.set_xticks(t_idx)
    ax.set_xticklabels(t_lbl)
    fig.tight_layout()
    return fig


def _screen_cv_figure(v, current, baseline, pts):
    """Screen figure: CV + baseline with selection point markers (Ayu style)."""
    apply_mpl_style()
    i1, i2, i3, i4 = pts
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(v, current, color=PLOT_COLORS[1], linewidth=1.8, label="CV Curve")
    ax.scatter(v[[i1, i2, i3, i4]], current[[i1, i2, i3, i4]],
               color=PLOT_COLORS[3], zorder=5, s=60, label="Baseline points")
    ax.plot(v[i1:i2 + 1], baseline[i1:i2 + 1],
            color=PLOT_COLORS[0], linestyle="--", linewidth=1.4, label="Baseline")
    ax.plot(v[i3:i4 + 1], baseline[i3:i4 + 1],
            color=PLOT_COLORS[0], linestyle="--", linewidth=1.4)
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Current (nA)", fontsize=13)
    ax.legend(fontsize=11)
    fig.tight_layout()
    return fig


def _screen_peaks_figure(v, diff, peak_ox, peak_red):
    """Screen figure: baseline-corrected peaks (Ayu style)."""
    apply_mpl_style()
    n_t = 5
    t_idx = np.linspace(0, len(v) - 1, n_t, dtype=int)
    t_lbl = [f"{v[i]:.2f}" for i in t_idx]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(diff, color=PLOT_COLORS[1], linewidth=1.8)
    ax.axhline(0, color="#707A8C", linewidth=0.8, linestyle="--")
    ax.annotate(
        f"Ox  {peak_ox[0]:.3f} V\n{peak_ox[1]:.2e} nA",
        xy=(int(np.argmax(diff)), peak_ox[1]),
        xytext=(10, 10), textcoords="offset points",
        color=PLOT_COLORS[0], fontsize=10,
        arrowprops=dict(arrowstyle="->", color=PLOT_COLORS[0], lw=1),
    )
    ax.annotate(
        f"Red  {peak_red[0]:.3f} V\n{peak_red[1]:.2e} nA",
        xy=(int(np.argmin(diff)), peak_red[1]),
        xytext=(10, -30), textcoords="offset points",
        color=PLOT_COLORS[3], fontsize=10,
        arrowprops=dict(arrowstyle="->", color=PLOT_COLORS[3], lw=1),
    )
    ax.set_xlabel("Potential (V)", fontsize=13)
    ax.set_ylabel("Peak Current (nA)", fontsize=13)
    ax.set_xticks(t_idx)
    ax.set_xticklabels(t_lbl)
    fig.tight_layout()
    return fig


def auto_output_dir(base_dir: str, experiment_type: str, device: str) -> str:
    """Build and create: base_dir / experiment_type / device /"""
    folder = os.path.join(base_dir, _sanitize(experiment_type), _sanitize(device))
    os.makedirs(folder, exist_ok=True)
    return folder


def run(file_path, baseline_points, curve_index=1, apply_smoothing=True,
        experiment_type="experiment", device_name=None, base_output_dir=None):
    """
    Full peak analysis for one .DTA file.

    Saves paper-quality figures (white bg, no selection markers) to:
        base_output_dir / experiment_type / device_name /

    Returns dict with screen figures (Ayu dark, with markers) for display.
    """
    voltage, current_raw = load_curve(file_path, curve_index)
    c = smooth(np.asarray(current_raw, dtype=float)) if apply_smoothing else np.asarray(current_raw, dtype=float)
    v = np.asarray(voltage, dtype=float)

    baseline = compute_baseline(v, c, baseline_points)
    diff     = np.nan_to_num(c - baseline)
    peak_ox, peak_red = find_peaks(v, c, baseline)

    # Screen figures (Ayu dark, shown in the UI)
    screen_figs = [
        (_screen_cv_figure(v, c, baseline, baseline_points),    "CV + Baseline"),
        (_screen_peaks_figure(v, diff, peak_ox, peak_red),      "Baseline-Corrected Peaks"),
    ]

    # Paper save
    if base_output_dir:
        dev = _sanitize(device_name or os.path.splitext(os.path.basename(file_path))[0])
        out = auto_output_dir(base_output_dir, experiment_type, dev)

        pfig_cv    = _paper_cv_figure(v, c, baseline, baseline_points, peak_ox, peak_red)
        pfig_peaks = _paper_peaks_figure(v, diff, peak_ox, peak_red)
        save_for_paper(pfig_cv,    os.path.join(out, f"{dev}_cv_baseline.png"))
        save_for_paper(pfig_peaks, os.path.join(out, f"{dev}_peaks.png"))
        plt.close(pfig_cv)
        plt.close(pfig_peaks)

    return {
        "voltage": v, "current": c,
        "baseline": baseline, "diff": diff,
        "peak_ox": peak_ox, "peak_red": peak_red,
        "figures": screen_figs,
    }
