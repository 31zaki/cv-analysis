import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.core.data_loader import load_curve, parse_scan_filename
from src.core.baseline import compute_baseline
from src.core.peak_detection import smooth, find_peaks
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


def run(data_dir, baseline_points, device_filter=None, apply_smoothing=True,
        experiment_type="scan_speed", base_output_dir=None):
    apply_mpl_style()

    dta_files = sorted(f for f in os.listdir(data_dir) if f.upper().endswith(".DTA"))
    if not dta_files:
        raise FileNotFoundError(f"No .DTA files in: {data_dir}")

    records, skipped = [], []
    for fname in dta_files:
        device, rate = parse_scan_filename(fname)
        if device is None:
            skipped.append(fname); continue
        if device_filter and device.upper() != device_filter.upper():
            continue
        path = os.path.join(data_dir, fname)
        try:
            v, c_raw = load_curve(path, curve_index=1)
        except Exception as e:
            skipped.append(f"{fname} ({e})"); continue

        c   = smooth(np.asarray(c_raw, dtype=float)) if apply_smoothing else np.asarray(c_raw, dtype=float)
        pts = baseline_points[rate] if isinstance(baseline_points, dict) else baseline_points
        b   = compute_baseline(v, c, pts)
        diff = np.nan_to_num(c - b)
        ox, red = find_peaks(v, c, b)

        records.append({
            "device": device, "rate": rate,
            "voltage": np.asarray(v, dtype=float),
            "current": c, "baseline": b, "diff": diff,
            "peak_ox": ox, "peak_red": red,
        })

    if not records:
        raise ValueError("No valid files matched. Check device filter and filename format.")

    records.sort(key=lambda r: r["rate"])

    # Screen figures (Ayu dark)
    screen_figs = _make_screen_figures(records)

    # Paper save
    if base_output_dir:
        dev = _sanitize(records[0]["device"])
        out = os.path.join(base_output_dir, _sanitize(experiment_type), dev)
        os.makedirs(out, exist_ok=True)
        for pfig, stem in _make_paper_figures(records):
            save_for_paper(pfig, os.path.join(out, f"{dev}_{stem}.png"))
            plt.close(pfig)

    return {"records": records, "skipped": skipped, "figures": screen_figs}


# ── Screen figures ────────────────────────────────────────────────────────────
def _make_screen_figures(records):
    apply_mpl_style()
    nc = len(PLOT_COLORS)
    figs = []

    fig1 = Figure(figsize=(9, 5))
    ax1 = fig1.add_subplot(111)
    for i, r in enumerate(records):
        ax1.plot(r["voltage"], r["current"], color=PLOT_COLORS[i % nc],
                 linewidth=1.6, label=f"{r['rate']} mV/s")
    ax1.set_xlabel("Potential (V)", fontsize=13); ax1.set_ylabel("Current (nA)", fontsize=13)
    ax1.legend(fontsize=10); fig1.tight_layout()
    figs.append((fig1, "All CV (Raw)"))

    v_ref = records[-1]["voltage"]
    t_idx = np.linspace(0, len(v_ref) - 1, 5, dtype=int)
    t_lbl = [f"{v_ref[j]:.2f}" for j in t_idx]

    fig2 = Figure(figsize=(9, 5))
    ax2 = fig2.add_subplot(111)
    for i, r in enumerate(records):
        ax2.plot(r["diff"], color=PLOT_COLORS[i % nc], linewidth=1.6, label=f"{r['rate']} mV/s")
    ax2.set_xticks(t_idx); ax2.set_xticklabels(t_lbl)
    ax2.set_xlabel("Potential (V)", fontsize=13); ax2.set_ylabel("Peak Current (nA)", fontsize=13)
    ax2.legend(fontsize=10); fig2.tight_layout()
    figs.append((fig2, "Baseline-Subtracted"))

    fig3 = Figure(figsize=(8, 5))
    ax3 = fig3.add_subplot(111)
    rates = np.array([r["rate"] for r in records], dtype=float)
    ox_v  = [r["peak_ox"][1]  for r in records]
    red_v = [r["peak_red"][1] for r in records]
    ax3.plot(rates, ox_v,  "o", color=PLOT_COLORS[0], label="Oxidation")
    ax3.plot(rates, red_v, "s", color=PLOT_COLORS[3], label="Reduction")
    ax3.plot(rates, np.poly1d(np.polyfit(rates, ox_v,  1))(rates), "--", color=PLOT_COLORS[0], alpha=0.7, lw=1.2)
    ax3.plot(rates, np.poly1d(np.polyfit(rates, red_v, 1))(rates), "--", color=PLOT_COLORS[3], alpha=0.7, lw=1.2)
    ax3.set_xlabel("Scan Rate (mV/s)", fontsize=13); ax3.set_ylabel("Peak Current (nA)", fontsize=13)
    ax3.legend(fontsize=11); fig3.tight_layout()
    figs.append((fig3, "Peak vs Scan Rate"))

    return figs


# ── Paper figures (white bg, black lines, no extra markers) ──────────────────
def _make_paper_figures(records):
    """Yields (fig, stem) pairs ready for save_for_paper."""
    nc = 8
    _PAPER_COLORS = ["#1f77b4","#d62728","#2ca02c","#ff7f0e","#9467bd","#8c564b","#e377c2","#17becf"]

    fig1 = Figure(figsize=(8, 5))
    ax1 = fig1.add_subplot(111)
    for i, r in enumerate(records):
        ax1.plot(r["voltage"], r["current"], color=_PAPER_COLORS[i % nc],
                 linewidth=1.6, label=f"{r['rate']} mV/s")
    ax1.set_xlabel("Potential (V)", fontsize=13); ax1.set_ylabel("Current (nA)", fontsize=13)
    ax1.legend(fontsize=10); fig1.tight_layout()
    yield fig1, "all_cv_raw"

    v_ref = records[-1]["voltage"]
    t_idx = np.linspace(0, len(v_ref) - 1, 5, dtype=int)
    t_lbl = [f"{v_ref[j]:.2f}" for j in t_idx]

    fig2 = Figure(figsize=(8, 5))
    ax2 = fig2.add_subplot(111)
    for i, r in enumerate(records):
        ax2.plot(r["diff"], color=_PAPER_COLORS[i % nc], linewidth=1.6, label=f"{r['rate']} mV/s")
    ax2.set_xticks(t_idx); ax2.set_xticklabels(t_lbl)
    ax2.set_xlabel("Potential (V)", fontsize=13); ax2.set_ylabel("Peak Current (nA)", fontsize=13)
    ax2.legend(fontsize=10); fig2.tight_layout()
    yield fig2, "all_cv_baseline_sub"

    rates = np.array([r["rate"] for r in records], dtype=float)
    ox_v  = [r["peak_ox"][1]  for r in records]
    red_v = [r["peak_red"][1] for r in records]

    fig3 = Figure(figsize=(8, 5))
    ax3 = fig3.add_subplot(111)
    ax3.plot(rates, ox_v,  "o", color="#1565C0", label="Oxidation", markersize=7)
    ax3.plot(rates, red_v, "s", color="#C62828", label="Reduction", markersize=7)
    ax3.plot(rates, np.poly1d(np.polyfit(rates, ox_v,  1))(rates), "--", color="#1565C0", lw=1.2)
    ax3.plot(rates, np.poly1d(np.polyfit(rates, red_v, 1))(rates), "--", color="#C62828", lw=1.2)
    ax3.set_xlabel("Scan Rate (mV/s)", fontsize=13); ax3.set_ylabel("Peak Current (nA)", fontsize=13)
    ax3.legend(fontsize=11); fig3.tight_layout()
    yield fig3, "peak_vs_scanrate"
