import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.data_loader import load_curve, parse_scan_filename
from src.core.baseline import compute_baseline
from src.core.peak_detection import smooth, find_peaks
from src.ui.theme import apply_mpl_style, PLOT_COLORS


def run(data_dir, baseline_points, device_filter=None, apply_smoothing=True, output_dir=None):
    """
    Scan-speed comparison for all DEVICE_NNmVs.DTA files in data_dir.
    baseline_points: [i1,i2,i3,i4] applied to all files (or dict {rate: [...]}).
    Returns dict with per-file results and summary figures.
    """
    apply_mpl_style()

    dta_files = sorted(
        f for f in os.listdir(data_dir) if f.upper().endswith(".DTA")
    )
    if not dta_files:
        raise FileNotFoundError(f"No .DTA files in: {data_dir}")

    records = []
    skipped = []

    for fname in dta_files:
        device, rate = parse_scan_filename(fname)
        if device is None:
            skipped.append(fname)
            continue
        if device_filter and device.upper() != device_filter.upper():
            continue

        path = os.path.join(data_dir, fname)
        try:
            v, c_raw = load_curve(path, curve_index=1)
        except Exception as e:
            skipped.append(f"{fname} ({e})")
            continue

        c = smooth(np.asarray(c_raw, dtype=float)) if apply_smoothing else np.asarray(c_raw, dtype=float)

        pts = baseline_points[rate] if isinstance(baseline_points, dict) else baseline_points
        b = compute_baseline(v, c, pts)
        diff = np.nan_to_num(c - b)
        ox, red = find_peaks(v, c, b)

        records.append({
            "device": device,
            "rate": rate,
            "voltage": np.asarray(v, dtype=float),
            "current": c,
            "baseline": b,
            "diff": diff,
            "peak_ox": ox,
            "peak_red": red,
        })

    if not records:
        raise ValueError("No valid files matched. Check device filter and filename format.")

    records.sort(key=lambda r: r["rate"])
    figures = _make_figures(records, output_dir)

    return {"records": records, "skipped": skipped, "figures": figures}


def _make_figures(records, output_dir):
    figs = []
    rates = [r["rate"] for r in records]
    n_col = min(len(PLOT_COLORS), len(records))

    # ── Fig 1: All raw CV curves ────────────────────────────────────────────
    fig1, ax1 = plt.subplots(figsize=(9, 5))
    for i, r in enumerate(records):
        ax1.plot(r["voltage"], r["current"], color=PLOT_COLORS[i % n_col],
                 linewidth=1.6, label=f"{r['rate']} mV/s")
    ax1.set_xlabel("Potential (V)", fontsize=13)
    ax1.set_ylabel("Current (nA)", fontsize=13)
    ax1.legend(fontsize=10, loc="best")
    fig1.tight_layout()
    figs.append((fig1, "All CV (Raw)"))

    # ── Fig 2: All baseline-subtracted ──────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    for i, r in enumerate(records):
        v, diff = r["voltage"], r["diff"]
        n_t = 5
        t_idx = np.linspace(0, len(v) - 1, n_t, dtype=int)
        ax2.plot(diff, color=PLOT_COLORS[i % n_col], linewidth=1.6, label=f"{r['rate']} mV/s")
    ax2.set_xticks(t_idx)
    ax2.set_xticklabels([f"{v[j]:.2f}" for j in t_idx])
    ax2.set_xlabel("Potential (V)", fontsize=13)
    ax2.set_ylabel("Peak Current (nA)", fontsize=13)
    ax2.legend(fontsize=10, loc="best")
    fig2.tight_layout()
    figs.append((fig2, "Baseline-Subtracted"))

    # ── Fig 3: Peak current vs scan rate ────────────────────────────────────
    ox_vals = [r["peak_ox"][1] for r in records]
    red_vals = [r["peak_red"][1] for r in records]
    rates_np = np.array(rates, dtype=float)
    ox_fit = np.poly1d(np.polyfit(rates_np, ox_vals, 1))(rates_np)
    red_fit = np.poly1d(np.polyfit(rates_np, red_vals, 1))(rates_np)

    fig3, ax3 = plt.subplots(figsize=(8, 5))
    ax3.plot(rates, ox_vals, "o", color=PLOT_COLORS[0], label="Oxidation peak")
    ax3.plot(rates, red_vals, "s", color=PLOT_COLORS[3], label="Reduction peak")
    ax3.plot(rates_np, ox_fit, "--", color=PLOT_COLORS[0], alpha=0.7, linewidth=1.2)
    ax3.plot(rates_np, red_fit, "--", color=PLOT_COLORS[3], alpha=0.7, linewidth=1.2)
    ax3.set_xlabel("Scan Rate (mV/s)", fontsize=13)
    ax3.set_ylabel("Peak Current (nA)", fontsize=13)
    ax3.legend(fontsize=11)
    fig3.tight_layout()
    figs.append((fig3, "Peak vs Scan Rate"))

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig1.savefig(os.path.join(output_dir, "all_cv_raw.png"), dpi=150)
        fig2.savefig(os.path.join(output_dir, "all_cv_baseline_sub.png"), dpi=150)
        fig3.savefig(os.path.join(output_dir, "peak_vs_scanrate.png"), dpi=150)

    return figs
