import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.ui.theme import apply_mpl_style, PLOT_COLORS

REACTION_COLUMNS = {
    "Click Chemistry":  ("click_ox",   "click_red"),
    "EDC-NHS":          ("edcnhs_ox",  "edcnhs_red"),
    "HATU":             ("hatu_ox",    "hatu_red"),
}


def run(csv_path, reaction_type="Click Chemistry", output_dir=None):
    """
    Efficiency correlation: grafting charge vs reaction charge.
    csv_path: CSV with columns [device, grafting, <reaction>_ox, <reaction>_red].
    Returns dict with stats and figures.
    """
    apply_mpl_style()

    if reaction_type not in REACTION_COLUMNS:
        raise ValueError(f"Unknown reaction type: {reaction_type}. Choose from {list(REACTION_COLUMNS)}")

    col_ox, col_red = REACTION_COLUMNS[reaction_type]
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    required = ["grafting", col_ox, col_red]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}\nFound: {list(df.columns)}")

    df_valid = df[df[[col_ox, col_red]].notna().all(axis=1)].copy()
    if df_valid.empty:
        raise ValueError("No rows with complete data for both ox and red columns.")

    df_valid["grafting_nC"]  = df_valid["grafting"].astype(float) * 1e9
    df_valid["ox_nC"]        = df_valid[col_ox].astype(float) * 1e9
    df_valid["red_nC"]       = df_valid[col_red].astype(float) * 1e9
    df_valid["reaction_nC"]  = (df_valid["ox_nC"] + df_valid["red_nC"]) / 2
    df_valid["efficiency"]   = df_valid["reaction_nC"] / df_valid["grafting_nC"] * 100

    graft = df_valid["grafting_nC"].values
    react = df_valid["reaction_nC"].values
    eff   = df_valid["efficiency"].values

    corr = float(df_valid["grafting_nC"].corr(df_valid["reaction_nC"]))
    n    = len(df_valid)

    # IQR-filtered stats
    q1, q3 = np.percentile(eff, 25), np.percentile(eff, 75)
    iqr = q3 - q1
    eff_f = eff[(eff >= q1 - 1.5 * iqr) & (eff <= q3 + 1.5 * iqr)]
    mean_f, std_f = float(np.mean(eff_f)), float(np.std(eff_f, ddof=1))

    stats = {
        "n": n,
        "correlation": corr,
        "mean_eff":   float(np.mean(eff)),
        "std_eff":    float(np.std(eff, ddof=1)),
        "mean_eff_filtered": mean_f,
        "std_eff_filtered":  std_f,
        "n_filtered": len(eff_f),
    }

    figures = _make_figures(graft, react, eff, reaction_type, stats, output_dir)
    return {"stats": stats, "dataframe": df_valid, "figures": figures}


def _make_figures(graft, react, eff, label, stats, output_dir):
    figs = []

    # ── Fig 1: Scatter – grafting vs reaction charge ─────────────────────
    fit = np.poly1d(np.polyfit(graft, react, 1))
    x_fit = np.linspace(graft.min(), graft.max(), 200)

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.scatter(graft, react, color=PLOT_COLORS[1], s=60, zorder=5, label="Devices")
    ax1.plot(x_fit, fit(x_fit), color=PLOT_COLORS[0], linewidth=1.5, linestyle="--", label="Linear fit")
    ax1.set_xlabel("Grafting Charge (nC)", fontsize=13)
    ax1.set_ylabel(f"{label} Charge (nC)", fontsize=13)
    ax1.text(0.97, 0.97,
             f"n = {stats['n']}\nr = {stats['correlation']:.3f}",
             transform=ax1.transAxes, fontsize=11,
             va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#232834", edgecolor="#2D3444"))
    ax1.legend(fontsize=11)
    fig1.tight_layout()
    figs.append((fig1, "Grafting vs Reaction"))

    # ── Fig 2: Efficiency box plot ────────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    bp = ax2.boxplot(eff, vert=True, patch_artist=True,
                     boxprops=dict(facecolor=PLOT_COLORS[1] + "55", edgecolor=PLOT_COLORS[1]),
                     medianprops=dict(color=PLOT_COLORS[0], linewidth=2),
                     whiskerprops=dict(color=PLOT_COLORS[1]),
                     capprops=dict(color=PLOT_COLORS[1]),
                     flierprops=dict(marker="o", color=PLOT_COLORS[3], markersize=5))
    ax2.set_ylabel("Efficiency (%)", fontsize=13)
    ax2.set_xticks([])
    ax2.text(0.97, 0.97,
             f"n = {stats['n']}\n"
             f"mean = {stats['mean_eff_filtered']:.1f}%\n"
             f"std = {stats['std_eff_filtered']:.1f}%",
             transform=ax2.transAxes, fontsize=11,
             va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#232834", edgecolor="#2D3444"))
    fig2.tight_layout()
    figs.append((fig2, "Efficiency (%)"))

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig1.savefig(os.path.join(output_dir, "grafting_vs_reaction.png"), dpi=150)
        fig2.savefig(os.path.join(output_dir, "efficiency_boxplot.png"), dpi=150)

    return figs
