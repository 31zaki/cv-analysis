from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from src.ui.theme import ACCENT, BLUE, GREEN, ORANGE, PURPLE, TEXT, TEXT_DIM, BG_PANEL, BORDER


def _feature_card(icon: str, title: str, desc: str, color: str) -> QWidget:
    card = QWidget()
    card.setObjectName("ConfigCard")
    card.setMinimumWidth(220)
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(6)

    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet(f"color: {color}; font-size: 26px;")
    icon_lbl.setAlignment(Qt.AlignLeft)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

    desc_lbl = QLabel(desc)
    desc_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
    desc_lbl.setWordWrap(True)

    layout.addWidget(icon_lbl)
    layout.addWidget(title_lbl)
    layout.addWidget(desc_lbl)
    return card


class HomePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setObjectName("PanelHeader")
        header.setFixedHeight(54)
        h_hl = QHBoxLayout(header)
        h_hl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("CV Analysis Suite")
        title_lbl.setObjectName("PageTitle")
        h_hl.addWidget(title_lbl)
        h_hl.addStretch()
        outer.addWidget(header)

        # Body
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(48, 40, 48, 40)
        body_layout.setSpacing(28)
        body_layout.setAlignment(Qt.AlignTop)

        # ── Hero ────────────────────────────────────────────────────────────
        hero_lbl = QLabel("Welcome to CV Analysis Suite")
        hero_lbl.setStyleSheet(
            f"color: {ACCENT}; font-size: 26px; font-weight: bold; letter-spacing: 0.5px;"
        )

        sub_lbl = QLabel(
            "A unified tool for cyclic voltammetry data processing — "
            "baseline correction, peak detection, scan-rate analysis, "
            "electrografting visualisation, and reaction efficiency."
        )
        sub_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 14px; line-height: 1.6;")
        sub_lbl.setWordWrap(True)

        body_layout.addWidget(hero_lbl)
        body_layout.addWidget(sub_lbl)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        body_layout.addWidget(div)

        # ── Feature cards ────────────────────────────────────────────────────
        cards_label = QLabel("MODULES")
        cards_label.setObjectName("SectionTitle")
        body_layout.addWidget(cards_label)

        grid = QGridLayout()
        grid.setSpacing(12)
        cards = [
            ("⚡", "Peak Analysis",
             "Load a single .DTA file. Apply 4-point baseline correction and detect oxidation / reduction peaks.",
             ACCENT),
            ("≋", "Scan Speed",
             "Compare CV responses across multiple scan rates. View baseline-subtracted curves and peak-vs-rate trends.",
             BLUE),
            ("∿", "Electrografting",
             "Plot multi-cycle CV curves for all devices in a folder. Batch-process and export grid summaries.",
             GREEN),
            ("◎", "Efficiency",
             "Correlate electrografting charge with click / EDC-NHS / HATU coupling yield. Boxplot and statistics.",
             ORANGE),
        ]
        for i, (icon, title, desc, color) in enumerate(cards):
            grid.addWidget(_feature_card(icon, title, desc, color), i // 2, i % 2)

        body_layout.addLayout(grid)

        # ── Quick-start hint ─────────────────────────────────────────────────
        hint_frame = QWidget()
        hint_frame.setObjectName("ConfigCard")
        hint_l = QHBoxLayout(hint_frame)
        hint_l.setContentsMargins(14, 12, 14, 12)
        icon = QLabel("ⓘ")
        icon.setStyleSheet(f"color: {BLUE}; font-size: 18px;")
        hint_txt = QLabel(
            "Select a module from the left sidebar to get started.  "
            "Use  <b>Browse</b>  to load your .DTA or .csv files, configure parameters, then click  <b>Run</b>."
        )
        hint_txt.setStyleSheet(f"color: {TEXT}; font-size: 13px;")
        hint_txt.setWordWrap(True)
        hint_l.addWidget(icon)
        hint_l.addSpacing(8)
        hint_l.addWidget(hint_txt, stretch=1)
        body_layout.addWidget(hint_frame)

        body_layout.addStretch()
        outer.addWidget(body, stretch=1)
