import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from src.ui.theme import save_for_paper


class PlotCanvas(QWidget):
    """
    Embeddable matplotlib figure with navigation toolbar
    and an 'Export for Paper' button that saves a white-background version.
    """

    def __init__(self, fig=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if fig is None:
            fig = Figure()

        self.figure = fig
        self.canvas = FigureCanvasQTAgg(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Toolbar row: navigation + export button ──────────────────────────
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setMaximumHeight(36)

        self._export_btn = QPushButton("Export for Paper")
        self._export_btn.setObjectName("SecondaryBtn")
        self._export_btn.setFixedHeight(28)
        self._export_btn.setToolTip(
            "Save a white-background, print-safe version of this figure (300 dpi)"
        )
        self._export_btn.clicked.connect(self._export_paper)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 4, 0)
        toolbar_row.setSpacing(0)
        toolbar_row.addWidget(self.toolbar, stretch=1)
        toolbar_row.addWidget(self._export_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(toolbar_row)
        layout.addWidget(self.canvas)

    def draw(self):
        self.canvas.draw()

    # ── Export ───────────────────────────────────────────────────────────────
    def _export_paper(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Figure for Paper",
            os.path.expanduser("~/figure.png"),
            "PNG Image (*.png);;PDF Vector (*.pdf);;SVG Vector (*.svg)",
        )
        if not path:
            return
        try:
            dpi = 600 if path.lower().endswith(".png") else 300
            save_for_paper(self.figure, path, dpi=dpi)
            # Brief visual confirmation in the button text
            self._export_btn.setText("✓ Saved")
            self._export_btn.setStyleSheet(
                "color: #A6CC70; border-color: #A6CC70;"
            )
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(
                2000,
                lambda: (
                    self._export_btn.setText("Export for Paper"),
                    self._export_btn.setStyleSheet(""),
                ),
            )
        except Exception as e:
            self._export_btn.setText(f"Error: {e}")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self._export_btn.setText("Export for Paper"))
