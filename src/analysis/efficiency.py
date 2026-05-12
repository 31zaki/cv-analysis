import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS

REACTION_COLUMNS = {
    "Click Chemistry": ("click_ox",  "click_red"),
    "EDC-NHS":         ("edcnhs_ox", "edcnhs_red"),
    "HATU":            ("hatu_ox",   "hatu_red"),
}


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


def run(csv_path, reaction_type="Click Chemistry",
        experiment_type="efficiency", base_output_dir=None):
    """
    Efficiency correlation: grafting charge vs reaction charge.
    Saves paper-quality figures to:
        base_output_dir / experiment_type / reaction_type /
    """
    apply_mpl_style()

    if reaction_type not in REACTION_COLUMNS:
        raise ValueError(f"Unknown reaction type: {reaction_type}. "
                         f"Choose from {list(REACTION_COLUMNS)}")

    col_ox, col_red = REACTION_COLUMNS[reaction_type]
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    missing = [c for c in ["grafting", col_ox, col_red] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}\nFound: {list(df.columns)}")

    df_v = df[df[[col_ox, col_red]].notna().all(axis=1)].copy()
    if df_v.empty:
        raise ValueError("No rows with complete data for both ox and red columns.")

    df_v["grafting_nC"] = df_v["grafting"].astype(float) * 1e9
    df_v["ox_nC"]       = df_v[col_ox].astype(float) * 1e9
    df_v["red_nC"]      = df_v[col_red].astype(float) * 1e9
    df_v["reaction_nC"] = (df_v["ox_nC"] + df_v["red_nC"]) / 2
    df_v["efficiency"]  = df_v["reaction_nC"] / df_v["grafting_nC"] * 100

    graft = df_v["grafting_nC"].values
    react = df_v["reaction_nC"].values
    eff   = df_v["efficiency"].values

    corr = float(df_v["grafting_nC"].corr(df_v["reaction_nC"]))
    n    = len(df_v)

    q1, q3 = np.percentile(eff, 25), np.percentile(eff, 75)
    iqr     = q3 - q1
    eff_f   = eff[(eff >= q1 - 1.5 * iqr) & (eff <= q3 + 1.5 * iqr)]

    stats = {
        "n": n, "correlation": corr,
        "mean_eff": float(np.mean(eff)),    "std_eff": float(np.std(eff, ddof=1)),
        "mean_eff_filtered": float(np.mean(eff_f)),
        "std_eff_filtered":  float(np.std(eff_f, ddof=1)),
        "n_filtered": len(eff_f),
    }

    # Screen figures (Ayu dark)
    screen_figs = _make_screen_figures(graft, react, eff, reaction_type, stats)

    # Paper save
    if base_output_dir:
        out = os.path.join(base_output_dir,
                           _sanitize(experiment_type),
                           _sanitize(reaction_type))
        os.makedirs(out, exist_ok=True)
        for pfig, stem in _make_paper_figures(graft, react, eff, reaction_type, stats):
            save_for_paper(pfig, os.path.join(out, f"{_sanitize(reaction_type)}_{stem}.png"))
            pfig.clf()
            plt.close("all")

    return {"stats": stats, "dataframe": df_v, "figures": screen_figs}


# ── Screen figures (Ayu dark) ─────────────────────────────────────────────────
def _make_screen_figures(graft, react, eff, label, stats):
    apply_mpl_style()
    figs = []

    fit   = np.poly1d(np.polyfit(graft, react, 1))
    x_fit = np.linspace(graft.min(), graft.max(), 200)

    fig1 = Figure(figsize=(8, 5))
    ax1 = fig1.add_subplot(111)
    ax1.scatter(graft, react, color=PLOT_COLORS[1], s=60, zorder=5, label="Devices")
    ax1.plot(x_fit, fit(x_fit), color=PLOT_COLORS[0], lw=1.5, ls="--", label="Linear fit")
    ax1.set_xlabel("Grafting Charge (nC)", fontsize=13)
    ax1.set_ylabel(f"{label} Charge (nC)", fontsize=13)
    ax1.text(0.97, 0.97, f"n = {stats['n']}\nr = {stats['correlation']:.3f}",
             transform=ax1.transAxes, fontsize=11, va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#232834", edgecolor="#2D3444"))
    ax1.legend(fontsize=11)
    fig1.tight_layout()
    figs.append((fig1, "Grafting vs Reaction"))

    fig2 = Figure(figsize=(6, 6))
    ax2 = fig2.add_subplot(111)
    ax2.boxplot(eff, vert=True, patch_artist=True,
                boxprops=dict(facecolor=PLOT_COLORS[1] + "55", edgecolor=PLOT_COLORS[1]),
                medianprops=dict(color=PLOT_COLORS[0], linewidth=2),
                whiskerprops=dict(color=PLOT_COLORS[1]),
                capprops=dict(color=PLOT_COLORS[1]),
                flierprops=dict(marker="o", color=PLOT_COLORS[3], markersize=5))
    ax2.set_ylabel("Efficiency (%)", fontsize=13)
    ax2.set_xticks([])
    ax2.text(0.97, 0.97,
             f"n = {stats['n']}\nmean = {stats['mean_eff_filtered']:.1f}%\n"
             f"std = {stats['std_eff_filtered']:.1f}%",
             transform=ax2.transAxes, fontsize=11, va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#232834", edgecolor="#2D3444"))
    fig2.tight_layout()
    figs.append((fig2, "Efficiency (%)"))
    return figs


# ── Paper figures (white bg, publication colors) ──────────────────────────────
def _make_paper_figures(graft, react, eff, label, stats):
    """Yields (fig, stem) pairs ready for save_for_paper."""
    fit   = np.poly1d(np.polyfit(graft, react, 1))
    x_fit = np.linspace(graft.min(), graft.max(), 200)

    fig1 = Figure(figsize=(8, 5))
    ax1 = fig1.add_subplot(111)
    ax1.scatter(graft, react, color="#1565C0", s=60, zorder=5, label="Devices")
    ax1.plot(x_fit, fit(x_fit), color="#C07000", lw=1.5, ls="--", label="Linear fit")
    ax1.set_xlabel("Grafting Charge (nC)", fontsize=13)
    ax1.set_ylabel(f"{label} Charge (nC)", fontsize=13)
    ax1.text(0.97, 0.97, f"n = {stats['n']}\nr = {stats['correlation']:.3f}",
             transform=ax1.transAxes, fontsize=11, va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#AAAAAA"))
    ax1.legend(fontsize=11)
    fig1.tight_layout()
    yield fig1, "grafting_vs_reaction"

    fig2 = Figure(figsize=(6, 6))
    ax2 = fig2.add_subplot(111)
    ax2.boxplot(eff, vert=True, patch_artist=True,
                boxprops=dict(facecolor="#BBDEFB", edgecolor="#1565C0"),
                medianprops=dict(color="#C62828", linewidth=2),
                whiskerprops=dict(color="#1565C0"),
                capprops=dict(color="#1565C0"),
                flierprops=dict(marker="o", color="#C62828", markersize=5))
    ax2.set_ylabel("Efficiency (%)", fontsize=13)
    ax2.set_xticks([])
    ax2.text(0.97, 0.97,
             f"n = {stats['n']}\nmean = {stats['mean_eff_filtered']:.1f}%\n"
             f"std = {stats['std_eff_filtered']:.1f}%",
             transform=ax2.transAxes, fontsize=11, va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#AAAAAA"))
    fig2.tight_layout()
    yield fig2, "efficiency_boxplot"
