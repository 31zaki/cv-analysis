from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QStatusBar, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.ui.sidebar import Sidebar
from src.ui.panels.home_panel            import HomePanel
from src.ui.panels.peak_panel            import PeakPanel
from src.ui.panels.scan_speed_panel      import ScanSpeedPanel
from src.ui.panels.electrografting_panel import ElectrograftingPanel
from src.ui.panels.efficiency_panel      import EfficiencyPanel
from src.ui.panels.diff_panel            import DiffPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CV Analysis Suite  ·  Yuan Lab")
        self.resize(1280, 780)
        self.setMinimumSize(900, 600)

        # ── Central layout ───────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        h_layout = QHBoxLayout(central)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)

        # Stacked pages
        self.stack = QStackedWidget()
        self._panels = [
            HomePanel(),
            PeakPanel(),
            ScanSpeedPanel(),
            ElectrograftingPanel(),
            EfficiencyPanel(),
            DiffPanel(),
        ]
        for panel in self._panels:
            self.stack.addWidget(panel)

        h_layout.addWidget(self.sidebar)
        h_layout.addWidget(self.stack, stretch=1)

        # ── Status bar ───────────────────────────────────────────────────────
        self._status_lbl = QLabel("Ready")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status_lbl)
        status_bar.addPermanentWidget(QLabel("Yuan Lab  ·  CV Analysis Suite  v1.0"))
        self.setStatusBar(status_bar)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)

    def set_status(self, msg: str):
        self._status_lbl.setText(msg)
