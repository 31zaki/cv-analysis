"""
Interactive matplotlib canvas for baseline point selection.

  Left-click  → snap to nearest data point in 2D (x+y),
                constrained to indices AFTER the last selected point
  Right-click → undo last selection
"""
import os
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from src.ui.theme import apply_mpl_style, save_for_paper, BLUE, ACCENT, ORANGE, GREEN, TEXT_DIM, BORDER

_PT_COLORS = [ACCENT, ACCENT, ORANGE, ORANGE]
_PT_LABELS = ["P1  (ox start)", "P2  (ox end)", "P3  (red start)", "P4  (red end)"]
_MAX_PTS   = 4


class InteractiveCanvas(QWidget):
    """
    CV canvas with click-to-select baseline points.

    Rules enforced:
    - Indices are always strictly increasing  (P1 < P2 < P3 < P4)
    - Snapping uses 2D normalised distance so clicking on one branch
      of the CV loop cannot accidentally snap to the other branch
      at the same voltage.
    - P1/P2 live on the forward scan; P3/P4 on the return scan,
      naturally, because the index constraint propagates from the
      user's earlier choices.
    """
    points_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._voltage: np.ndarray | None = None
        self._current: np.ndarray | None = None
        self._indices: list[int] = []
        self._selection_mode = False

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setMaximumHeight(36)

        self._export_btn = QPushButton("Export for Paper")
        self._export_btn.setObjectName("SecondaryBtn")
        self._export_btn.setFixedHeight(28)
        self._export_btn.setToolTip(
            "Save a white-background, print-safe version of this figure (600 dpi)"
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

        self._cid = self.canvas.mpl_connect("button_press_event", self._on_click)
        self._draw()

    # ── Public API ────────────────────────────────────────────────────────────
    def set_data(self, voltage, current):
        self._voltage = np.asarray(voltage, dtype=float)
        self._current = np.asarray(current, dtype=float)
        self._indices = []
        self._selection_mode = False
        self.canvas.setCursor(Qt.ArrowCursor)
        self._draw()
        self.points_changed.emit([])

    def set_selection_mode(self, active: bool):
        self._selection_mode = active
        if active:
            self._exit_toolbar_mode()
            self.canvas.setCursor(Qt.CrossCursor)
        else:
            self.canvas.setCursor(Qt.ArrowCursor)
        self._draw()

    def clear_selection(self):
        self._indices = []
        self._draw()
        self.points_changed.emit([])

    @property
    def selected_indices(self) -> list[int]:
        return self._indices.copy()

    # ── Click handler ─────────────────────────────────────────────────────────
    def _on_click(self, event):
        if not self._selection_mode:
            return
        if event.inaxes is None or self._voltage is None:
            return
        if self.toolbar.mode:           # zoom / pan active — don't interfere
            return

        if event.button == 1:           # left-click → add point
            if len(self._indices) >= _MAX_PTS:
                return

            idx = self._nearest_index(event.xdata, event.ydata)
            if idx is not None and idx not in self._indices:
                self._indices.append(idx)
                self._draw()
                self.points_changed.emit(self._indices.copy())
                if len(self._indices) == _MAX_PTS:
                    self.set_selection_mode(False)

        elif event.button == 3:         # right-click → undo
            if self._indices:
                self._indices.pop()
                self._draw()
                self.points_changed.emit(self._indices.copy())

    def _nearest_index(self, x_click: float, y_click: float) -> int | None:
        """
        Find the nearest data point using 2D normalised Euclidean distance.
        Only candidates with index STRICTLY GREATER than the last selected
        index are considered, enforcing ascending order.
        """
        v, c = self._voltage, self._current

        v_range = v.max() - v.min()
        c_range = c.max() - c.min()
        if v_range == 0 or c_range == 0:
            return None

        # Normalise to [0, 1]
        vn = (v - v.min()) / v_range
        cn = (c - c.min()) / c_range
        xn = (x_click - v.min()) / v_range
        yn = (y_click - c.min()) / c_range

        dist = np.sqrt((vn - xn) ** 2 + (cn - yn) ** 2)

        # Mask out already-passed indices (enforce strictly increasing order)
        if self._indices:
            dist[: self._indices[-1] + 1] = np.inf

        best = int(np.argmin(dist))
        return None if np.isinf(dist[best]) else best

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        apply_mpl_style()
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # ── Empty state ───────────────────────────────────────────────────────
        if self._voltage is None:
            ax.text(0.5, 0.5,
                    "Browse and load a .DTA file\nto preview the CV curve",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=13, color=TEXT_DIM)
            self.canvas.draw()
            return

        v, c = self._voltage, self._current
        n_sel = len(self._indices)

        # ── CV curve: dim passed region, highlight selectable region ──────────
        split = self._indices[-1] + 1 if self._indices else 0

        if self._selection_mode and n_sel > 0:
            # Already-chosen section: dimmed
            ax.plot(v[:split], c[:split],
                    color=TEXT_DIM, linewidth=1.2, alpha=0.35, zorder=1)
            # Still-selectable section: bright
            ax.plot(v[split:], c[split:],
                    color=BLUE, linewidth=2.0, zorder=2, label="CV Curve")
        else:
            ax.plot(v, c, color=BLUE, linewidth=1.8, zorder=2, label="CV Curve")

        # ── Selected point markers ────────────────────────────────────────────
        for i, idx in enumerate(self._indices):
            col = _PT_COLORS[i]
            ax.axvline(v[idx], color=col, alpha=0.40, linewidth=1.0, linestyle=":")
            ax.scatter([v[idx]], [c[idx]], color=col, s=90, zorder=7,
                       label=f"{_PT_LABELS[i]}  ({v[idx]:.3f} V, idx {idx})")

        # ── Live baseline segment 1 (P1→P2) ──────────────────────────────────
        if n_sel >= 2:
            ia, ib = self._indices[0], self._indices[1]
            ax.plot(v[ia:ib + 1], self._seg(ia, ib),
                    color=ACCENT, linestyle="--", linewidth=1.6, alpha=0.9,
                    label="Baseline seg 1", zorder=3)

        # ── Live baseline segment 2 (P3→P4) ──────────────────────────────────
        if n_sel == 4:
            ic, id_ = self._indices[2], self._indices[3]
            ax.plot(v[ic:id_ + 1], self._seg(ic, id_),
                    color=ORANGE, linestyle="--", linewidth=1.6, alpha=0.9,
                    label="Baseline seg 2", zorder=3)

        # ── Title hint ────────────────────────────────────────────────────────
        if self._selection_mode:
            ax.set_title(
                f"Click point {n_sel + 1} / {_MAX_PTS}  on the bright curve  "
                f"·  Right-click to undo",
                color=ACCENT, fontsize=11, pad=6,
            )
        elif n_sel == _MAX_PTS:
            ax.set_title("✓  4 points selected  —  click Run Analysis",
                         color=GREEN, fontsize=11, pad=6)
        elif n_sel > 0:
            ax.set_title(
                f"{n_sel} / {_MAX_PTS} points  —  click 'Select Points' to continue",
                color=TEXT_DIM, fontsize=11, pad=6,
            )

        ax.set_xlabel("Potential (V)", fontsize=13)
        ax.set_ylabel("Current (nA)", fontsize=13)
        if self._indices:
            ax.legend(fontsize=10, loc="best",
                      handlelength=1.2, borderpad=0.7, labelspacing=0.4)
        self.figure.tight_layout()
        self.canvas.draw()

    def _seg(self, ia: int, ib: int) -> np.ndarray:
        v, c = self._voltage, self._current
        dv = v[ib] - v[ia]
        slope = (c[ib] - c[ia]) / dv if dv != 0 else 0.0
        return c[ia] + slope * (v[ia:ib + 1] - v[ia])

    def _export_paper(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Figure for Paper",
            os.path.expanduser("~/cv_preview.png"),
            "PNG Image (*.png);;PDF Vector (*.pdf);;SVG Vector (*.svg)",
        )
        if not path:
            return
        try:
            dpi = 600 if path.lower().endswith(".png") else 300
            save_for_paper(self.figure, path, dpi=dpi)
            self._export_btn.setText("✓ Saved")
            self._export_btn.setStyleSheet("color: #A6CC70; border-color: #A6CC70;")
            QTimer.singleShot(2000, lambda: (
                self._export_btn.setText("Export for Paper"),
                self._export_btn.setStyleSheet(""),
            ))
        except Exception as e:
            self._export_btn.setText(f"Error: {e}")
            QTimer.singleShot(3000, lambda: self._export_btn.setText("Export for Paper"))

    def _exit_toolbar_mode(self):
        mode = str(getattr(self.toolbar, "mode", "")).lower()
        if "zoom" in mode:
            self.toolbar.zoom()
        elif "pan" in mode:
            self.toolbar.pan()
