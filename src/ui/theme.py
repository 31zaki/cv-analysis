"""Ayu Light color palette, QSS stylesheet, and matplotlib theme."""
from cycler import cycler
import os

# ── Ayu Light Palette ────────────────────────────────────────────────────────
BG_DEEP   = "#F0F1F2"   # sidebar / header
BG_MAIN   = "#FAFAFA"   # app background
BG_PANEL  = "#FFFFFF"   # cards / panels
BG_INPUT  = "#FFFFFF"   # input fields
BORDER    = "#D9DCE3"   # borders
TEXT      = "#3D4350"   # primary text
TEXT_DIM  = "#8B949E"   # secondary / placeholder text
TEXT_BRT  = "#1A1F29"   # headings
ACCENT    = "#399EE6"   # Ayu Light blue (entity / active)
GREEN     = "#2E7D32"   # dark green (success)
RED       = "#C62828"   # dark red (error / danger)
ORANGE    = "#E65100"   # burnt orange (warning)
PURPLE    = "#6A1B9A"   # deep purple
CYAN      = "#00838F"   # deep teal

# ── Plot colors — paper-quality, readable on white ───────────────────────────
PLOT_COLORS = [
    "#1565C0",  # deep blue
    "#C62828",  # deep red
    "#2E7D32",  # deep green
    "#E65100",  # burnt orange
    "#6A1B9A",  # deep purple
    "#00838F",  # deep teal
    "#F57F17",  # deep amber
    "#37474F",  # blue-grey
]


def apply_mpl_style():
    """Apply Ayu Light style to matplotlib (white background, paper-quality colors)."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "axes.edgecolor":    "#CCCCCC",
        "axes.labelcolor":   "#333333",
        "axes.prop_cycle":   cycler("color", PLOT_COLORS),
        "axes.grid":         True,
        "grid.color":        "#E5E5E5",
        "grid.linewidth":    0.8,
        "grid.alpha":        1.0,
        "text.color":        "#333333",
        "xtick.color":       "#333333",
        "ytick.color":       "#333333",
        "xtick.labelsize":   11,
        "ytick.labelsize":   11,
        "axes.labelsize":    13,
        "axes.titlesize":    13,
        "axes.titlecolor":   "#1A1F29",
        "legend.facecolor":  "white",
        "legend.edgecolor":  "#CCCCCC",
        "legend.labelcolor": "#333333",
        "legend.fontsize":   10,
        "lines.linewidth":   1.8,
        "figure.autolayout": True,
        "savefig.facecolor": "white",
        "savefig.dpi":       150,
    })


def save_for_paper(fig, path: str, dpi: int = 300):
    """
    Save fig to path at high DPI.
    Screen and paper styles are now identical (white background,
    paper-quality colors) so no color conversion is needed.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, facecolor="white", dpi=dpi, bbox_inches="tight")


# ── Full QSS Stylesheet — Ayu Light ─────────────────────────────────────────
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
    selection-background-color: {ACCENT}33;
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
    background-color: {BORDER};
    color: {TEXT};
}}
#NavButton[active="true"] {{
    background-color: {ACCENT}18;
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    padding-left: 9px;
    font-weight: bold;
}}

/* ===== Panel Header ===== */
#PanelHeader {{
    background-color: {BG_PANEL};
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
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: #2D8FD6;
}}
QPushButton:pressed {{
    background-color: #1A6EB0;
}}
QPushButton:disabled {{
    background-color: {BORDER};
    color: {TEXT_DIM};
}}
#SecondaryBtn {{
    background-color: transparent;
    color: {ACCENT};
    border: 1px solid {ACCENT}99;
    font-weight: normal;
}}
#SecondaryBtn:hover {{
    background-color: {ACCENT}18;
    border-color: {ACCENT};
}}
#DangerBtn {{
    background-color: transparent;
    color: {RED};
    border: 1px solid {RED}88;
    font-weight: normal;
}}
#DangerBtn:hover {{
    background-color: {RED}18;
    border-color: {RED};
}}
#GreenBtn {{
    background-color: {GREEN};
    color: white;
}}
#GreenBtn:hover {{
    background-color: #388E3C;
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
}}
QLineEdit:read-only {{
    background-color: {BG_DEEP};
    color: {TEXT_DIM};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {BG_DEEP};
    border: none;
    width: 18px;
    border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {BORDER};
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
    selection-background-color: {ACCENT}22;
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
    border: 1.5px solid {BORDER};
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
    color: {TEXT};
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
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background-color: {BORDER};
    color: {TEXT};
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {{
    background-color: {BG_MAIN};
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
    background-color: {BG_MAIN};
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
    background-color: {BG_DEEP};
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
    background-color: {ACCENT}22;
    color: {ACCENT};
}}
"""
