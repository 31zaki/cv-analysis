"""
Interactive matplotlib canvas for baseline point selection.
  Left-click  → snap to nearest data point (up to 4)
  Right-click → undo last point
"""
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from src.ui.theme import apply_mpl_style, BLUE, ACCENT, ORANGE, GREEN, RED, TEXT_DIM

# Colors / labels for the 4 baseline points
_PT_COLORS = [ACCENT, ACCENT, ORANGE, ORANGE]
_PT_LABELS = ["P1  (ox start)", "P2  (ox end)", "P3  (red start)", "P4  (red end)"]
_MAX_PTS = 4


class InteractiveCanvas(QWidget):
    """
    Embeddable canvas with:
    - set_data(voltage, current) to load CV
    - set_selection_mode(bool) to toggle click-to-select
    - points_changed signal emits list[int] (indices into voltage array)
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
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

    # ── Internals ─────────────────────────────────────────────────────────────
    def _exit_toolbar_mode(self):
        """Deactivate zoom/pan if either is currently active."""
        mode = getattr(self.toolbar, "mode", "")
        if "zoom" in str(mode).lower():
            self.toolbar.zoom()
        elif "pan" in str(mode).lower():
            self.toolbar.pan()

    def _on_click(self, event):
        if not self._selection_mode:
            return
        if event.inaxes is None or self._voltage is None:
            return
        if self.toolbar.mode:       # skip when zoom / pan active
            return

        if event.button == 1:       # left-click → add point
            if len(self._indices) >= _MAX_PTS:
                return
            idx = int(np.argmin(np.abs(self._voltage - event.xdata)))
            if idx not in self._indices:
                self._indices.append(idx)
                self._draw()
                self.points_changed.emit(self._indices.copy())
                if len(self._indices) == _MAX_PTS:
                    self.set_selection_mode(False)

        elif event.button == 3:     # right-click → undo last
            if self._indices:
                self._indices.pop()
                self._draw()
                self.points_changed.emit(self._indices.copy())

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

        # ── CV curve ──────────────────────────────────────────────────────────
        ax.plot(self._voltage, self._current, color=BLUE,
                linewidth=1.8, label="CV Curve", zorder=2)

        # ── Selected points ───────────────────────────────────────────────────
        for i, idx in enumerate(self._indices):
            col = _PT_COLORS[i]
            ax.axvline(self._voltage[idx], color=col,
                       alpha=0.45, linewidth=1.1, linestyle=":")
            ax.scatter([self._voltage[idx]], [self._current[idx]],
                       color=col, s=90, zorder=7,
                       label=f"{_PT_LABELS[i]}\n    {self._voltage[idx]:.3f} V  (idx {idx})")

        # ── Live baseline segment 1 (after points 1 & 2) ─────────────────────
        if len(self._indices) >= 2:
            ia, ib = self._indices[0], self._indices[1]
            ax.plot(self._voltage[ia:ib + 1],
                    self._linear_seg(ia, ib),
                    color=ACCENT, linestyle="--", linewidth=1.6,
                    alpha=0.9, zorder=3)

        # ── Live baseline segment 2 (after all 4 points) ─────────────────────
        if len(self._indices) == 4:
            ic, id_ = self._indices[2], self._indices[3]
            ax.plot(self._voltage[ic:id_ + 1],
                    self._linear_seg(ic, id_),
                    color=ORANGE, linestyle="--", linewidth=1.6,
                    alpha=0.9, zorder=3)

        # ── Title / hint ──────────────────────────────────────────────────────
        n = len(self._indices)
        if self._selection_mode:
            ax.set_title(
                f"Click to select point {n + 1} / {_MAX_PTS}   ·   Right-click to undo",
                color=ACCENT, fontsize=11, pad=6,
            )
        elif n > 0 and n < _MAX_PTS:
            ax.set_title(
                f"{n} / {_MAX_PTS} points selected  —  press 'Select Points' to continue",
                color=TEXT_DIM, fontsize=11, pad=6,
            )
        elif n == _MAX_PTS:
            ax.set_title(
                "✓  4 baseline points selected  —  click 'Run Analysis'",
                color=GREEN, fontsize=11, pad=6,
            )

        ax.set_xlabel("Potential (V)", fontsize=13)
        ax.set_ylabel("Current (nA)", fontsize=13)
        if self._indices:
            ax.legend(fontsize=10, loc="best",
                      handlelength=1.2, borderpad=0.7, labelspacing=0.4)
        self.figure.tight_layout()
        self.canvas.draw()

    def _linear_seg(self, ia: int, ib: int) -> np.ndarray:
        v, c = self._voltage, self._current
        dv = v[ib] - v[ia]
        slope = (c[ib] - c[ia]) / dv if dv != 0 else 0.0
        return c[ia] + slope * (v[ia:ib + 1] - v[ia])
