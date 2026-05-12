"""Ayu Mirage color palette, QSS stylesheet, and matplotlib theme."""
from cycler import cycler
import os

# ── Palette ─────────────────────────────────────────────────────────────────
BG_DEEP   = "#1A1F29"
BG_MAIN   = "#1F2430"
BG_PANEL  = "#232834"
BG_INPUT  = "#272D3D"
BORDER    = "#2D3444"
TEXT      = "#CCCAC2"
TEXT_DIM  = "#707A8C"
TEXT_BRT  = "#F8F8F2"
ACCENT    = "#FFCC66"
BLUE      = "#73D0FF"
GREEN     = "#A6CC70"
RED       = "#F07178"
ORANGE    = "#FFB454"
PURPLE    = "#D4BFFF"
CYAN      = "#5CCFE6"

PLOT_COLORS = [ACCENT, BLUE, GREEN, RED, ORANGE, PURPLE, CYAN, "#BAE67E"]


def apply_mpl_style():
    """Apply Ayu Mirage style to matplotlib globally."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor":  BG_PANEL,
        "axes.facecolor":    BG_MAIN,
        "axes.edgecolor":    BORDER,
        "axes.labelcolor":   TEXT,
        "axes.prop_cycle":   cycler("color", PLOT_COLORS),
        "axes.grid":         True,
        "grid.color":        BORDER,
        "grid.linewidth":    0.8,
        "grid.alpha":        0.6,
        "text.color":        TEXT,
        "xtick.color":       TEXT,
        "ytick.color":       TEXT,
        "xtick.labelsize":   11,
        "ytick.labelsize":   11,
        "axes.labelsize":    13,
        "axes.titlesize":    13,
        "axes.titlecolor":   TEXT_BRT,
        "legend.facecolor":  BG_PANEL,
        "legend.edgecolor":  BORDER,
        "legend.labelcolor": TEXT,
        "legend.fontsize":   10,
        "lines.linewidth":   1.8,
        "figure.autolayout": True,
        "savefig.facecolor": BG_PANEL,
        "savefig.dpi":       150,
    })


# ── Full QSS Stylesheet ──────────────────────────────────────────────────────
STYLESHEET = f"""
/* ===== Base ===== */
QMainWindow, QDialog {{
    background-color: {BG_MAIN};
}}
QWidget {{
    background-color: {BG_MAIN};
    color: {TEXT};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: {ACCENT}44;
    selection-color: {TEXT_BRT};
}}

/* ===== Sidebar ===== */
#Sidebar {{
    background-color: {BG_DEEP};
    border-right: 1px solid {BORDER};
}}
#AppLogoLabel {{
    color: {ACCENT};
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 0 0 0 4px;
}}
#AppSubLabel {{
    color: {TEXT_DIM};
    font-size: 11px;
    letter-spacing: 0.5px;
}}
#SidebarDivider {{
    background-color: {BORDER};
    max-height: 1px;
    border: none;
}}
#VersionLabel {{
    color: {TEXT_DIM};
    font-size: 10px;
}}

/* ===== Nav Buttons ===== */
#NavButton {{
    background-color: transparent;
    color: {TEXT_DIM};
    border: none;
    border-radius: 6px;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
}}
#NavButton:hover {{
    background-color: {BG_PANEL};
    color: {TEXT};
}}
#NavButton[active="true"] {{
    background-color: {BG_PANEL};
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    padding-left: 9px;
    font-weight: bold;
}}

/* ===== Panel Header ===== */
#PanelHeader {{
    background-color: {BG_DEEP};
    border-bottom: 1px solid {BORDER};
}}
#PageTitle {{
    color: {TEXT_BRT};
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}
#PageSubtitle {{
    color: {TEXT_DIM};
    font-size: 11px;
}}

/* ===== Config Cards ===== */
#ConfigCard {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}
#SectionTitle {{
    color: {ACCENT};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.8px;
    text-transform: uppercase;
}}

/* ===== Buttons ===== */
QPushButton {{
    background-color: {ACCENT};
    color: {BG_DEEP};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: #FFD680;
}}
QPushButton:pressed {{
    background-color: #E6B84D;
}}
QPushButton:disabled {{
    background-color: {BORDER};
    color: {TEXT_DIM};
}}
#SecondaryBtn {{
    background-color: transparent;
    color: {BLUE};
    border: 1px solid {BLUE}88;
    font-weight: normal;
}}
#SecondaryBtn:hover {{
    background-color: {BLUE}22;
    border-color: {BLUE};
}}
#DangerBtn {{
    background-color: transparent;
    color: {RED};
    border: 1px solid {RED}88;
    font-weight: normal;
}}
#DangerBtn:hover {{
    background-color: {RED}22;
    border-color: {RED};
}}
#GreenBtn {{
    background-color: {GREEN};
    color: {BG_DEEP};
}}
#GreenBtn:hover {{
    background-color: #B8DC82;
}}

/* ===== Inputs ===== */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACCENT};
    background-color: {BG_INPUT};
}}
QLineEdit:read-only {{
    color: {TEXT_DIM};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {BORDER};
    border: none;
    width: 18px;
    border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {TEXT_DIM};
}}

/* ===== ComboBox ===== */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
}}
QComboBox:focus {{
    border: 1px solid {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    border-radius: 0 6px 6px 0;
}}
QComboBox::down-arrow {{
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT_DIM};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT};
    selection-background-color: {ACCENT}44;
    selection-color: {TEXT_BRT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 2px;
    outline: none;
}}

/* ===== CheckBox ===== */
QCheckBox {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

/* ===== Log Output ===== */
#LogOutput {{
    background-color: {BG_DEEP};
    color: {GREEN};
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 0 8px 8px 8px;
    top: -1px;
}}
QTabBar {{
    background-color: transparent;
}}
QTabBar::tab {{
    background-color: {BG_DEEP};
    color: {TEXT_DIM};
    padding: 7px 18px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background-color: {BG_PANEL};
    color: {ACCENT};
    border-bottom: 1px solid {BG_PANEL};
}}
QTabBar::tab:hover:!selected {{
    background-color: {BG_PANEL};
    color: {TEXT};
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {{
    background-color: {BG_DEEP};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background-color: {BG_DEEP};
    height: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: {BORDER};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_DIM};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ===== Splitter ===== */
QSplitter::handle:vertical {{
    background-color: {BORDER};
    height: 2px;
    margin: 2px 0;
}}
QSplitter::handle:horizontal {{
    background-color: {BORDER};
    width: 2px;
    margin: 0 2px;
}}
QSplitter::handle:hover {{
    background-color: {ACCENT};
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {BG_DEEP};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    font-size: 11px;
    padding: 0 8px;
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}

/* ===== Tooltip ===== */
QToolTip {{
    background-color: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ===== Separator ===== */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    background-color: {BORDER};
    border: none;
}}

/* ===== Matplotlib NavigationToolbar ===== */
NavigationToolbar2QT {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
    spacing: 2px;
    padding: 2px;
}}
NavigationToolbar2QT QToolButton {{
    background-color: transparent;
    color: {TEXT};
    border: none;
    border-radius: 4px;
    padding: 4px;
}}
NavigationToolbar2QT QToolButton:hover {{
    background-color: {BORDER};
}}
NavigationToolbar2QT QToolButton:checked {{
    background-color: {ACCENT}44;
    color: {ACCENT};
}}
"""

# ── Paper-export color map: Ayu Mirage → print-friendly darks ───────────────
# Keys are lowercase hex; values are darker equivalents readable on white.
_PAPER_COLOR_MAP: dict[str, str] = {
    "#73d0ff": "#1565C0",   # BLUE       → dark blue
    "#ffcc66": "#C07000",   # ACCENT     → dark amber
    "#a6cc70": "#2E7D32",   # GREEN      → dark green
    "#f07178": "#C62828",   # RED        → dark red
    "#ffb454": "#E65100",   # ORANGE     → burnt orange
    "#d4bfff": "#6A1B9A",   # PURPLE     → dark purple
    "#5ccfe6": "#00838F",   # CYAN       → dark teal
    "#bae67e": "#558B2F",   # LIME       → dark lime
}


def _paper_color(c) -> str:
    """Map an Ayu screen color to its paper-export equivalent."""
    import matplotlib.colors as mcolors
    try:
        rgba = mcolors.to_rgba(c)
        hex_c = mcolors.to_hex(rgba).lower()
        return _PAPER_COLOR_MAP.get(hex_c, hex_c)
    except Exception:
        return c


def _capture(ax) -> dict:
    """Snapshot all color/style properties of an Axes for later restore."""
    xticks = ax.xaxis.get_major_ticks()
    yticks = ax.yaxis.get_major_ticks()
    state = {
        "facecolor":    ax.get_facecolor(),
        "xlabel_color": ax.xaxis.label.get_color(),
        "ylabel_color": ax.yaxis.label.get_color(),
        "title_color":  ax.title.get_color(),
        "xtick_color":  xticks[0].tick1line.get_color() if xticks else TEXT,
        "ytick_color":  yticks[0].tick1line.get_color() if yticks else TEXT,
        "xticklab_color": xticks[0].label1.get_color() if xticks else TEXT,
        "yticklab_color": yticks[0].label1.get_color() if yticks else TEXT,
        "spines":       {k: (v.get_edgecolor(), v.get_linewidth())
                         for k, v in ax.spines.items()},
        "gridlines":    [(gl, gl.get_color(), gl.get_alpha(), gl.get_linewidth())
                         for gl in ax.xaxis.get_gridlines() + ax.yaxis.get_gridlines()],
        "lines":        [(ln, ln.get_color(), ln.get_linewidth()) for ln in ax.lines],
        "collections":  [(col, col.get_facecolor().copy(), col.get_edgecolor().copy())
                         for col in ax.collections],
        "legend":       None,
    }
    leg = ax.get_legend()
    if leg:
        state["legend"] = {
            "facecolor": leg.get_frame().get_facecolor(),
            "edgecolor": leg.get_frame().get_edgecolor(),
            "text_colors": [t.get_color() for t in leg.get_texts()],
        }
    return state


def _restore(ax, state: dict):
    ax.set_facecolor(state["facecolor"])
    ax.xaxis.label.set_color(state["xlabel_color"])
    ax.yaxis.label.set_color(state["ylabel_color"])
    ax.title.set_color(state["title_color"])

    for tick in ax.xaxis.get_major_ticks():
        tick.tick1line.set_color(state["xtick_color"])
        tick.tick2line.set_color(state["xtick_color"])
        tick.label1.set_color(state["xticklab_color"])
    for tick in ax.yaxis.get_major_ticks():
        tick.tick1line.set_color(state["ytick_color"])
        tick.tick2line.set_color(state["ytick_color"])
        tick.label1.set_color(state["yticklab_color"])

    for k, (ec, lw) in state["spines"].items():
        ax.spines[k].set_edgecolor(ec)
        ax.spines[k].set_linewidth(lw)

    for gl, col, alpha, lw in state["gridlines"]:
        gl.set_color(col)
        gl.set_alpha(alpha)
        gl.set_linewidth(lw)

    for ln, col, lw in state["lines"]:
        ln.set_color(col)
        ln.set_linewidth(lw)

    for col, fc, ec in state["collections"]:
        col.set_facecolor(fc)
        col.set_edgecolor(ec)

    leg = ax.get_legend()
    if leg and state["legend"]:
        s = state["legend"]
        leg.get_frame().set_facecolor(s["facecolor"])
        leg.get_frame().set_edgecolor(s["edgecolor"])
        for t, c in zip(leg.get_texts(), s["text_colors"]):
            t.set_color(c)


def save_for_paper(fig, path: str, dpi: int = 300):
    """
    Save *fig* to *path* with a white background and print-safe colors,
    then restore the original on-screen appearance.
    """
    import numpy as np

    orig_fig_face = fig.get_facecolor()
    axes_states = [_capture(ax) for ax in fig.axes]

    try:
        # ── Apply paper style ────────────────────────────────────────────────
        fig.patch.set_facecolor("white")

        for ax in fig.axes:
            ax.set_facecolor("white")
            ax.xaxis.label.set_color("black")
            ax.yaxis.label.set_color("black")
            ax.title.set_color("black")

            for tick in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
                tick.tick1line.set_color("black")
                tick.tick2line.set_color("black")
                tick.label1.set_color("black")

            for spine in ax.spines.values():
                spine.set_edgecolor("black")
                spine.set_linewidth(0.8)

            for gl in ax.xaxis.get_gridlines() + ax.yaxis.get_gridlines():
                gl.set_color("#BBBBBB")
                gl.set_alpha(0.9)
                gl.set_linewidth(0.7)

            for ln in ax.lines:
                ln.set_color(_paper_color(ln.get_color()))

            # Scatter / PathCollection face+edge colors
            for col in ax.collections:
                fc = col.get_facecolor()
                ec = col.get_edgecolor()
                if fc is not None and len(fc):
                    col.set_facecolor([_paper_color(c) for c in fc])
                if ec is not None and len(ec):
                    new_ec = [_paper_color(c) for c in ec]
                    col.set_edgecolor(new_ec)

            leg = ax.get_legend()
            if leg:
                leg.get_frame().set_facecolor("white")
                leg.get_frame().set_edgecolor("#AAAAAA")
                for t in leg.get_texts():
                    t.set_color("black")

        # ── Save ─────────────────────────────────────────────────────────────
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        fig.savefig(path, facecolor="white", dpi=dpi, bbox_inches="tight")

    finally:
        # ── Always restore on-screen style ───────────────────────────────────
        fig.patch.set_facecolor(orig_fig_face)
        for ax, state in zip(fig.axes, axes_states):
            _restore(ax, state)
        fig.canvas.draw_idle()

