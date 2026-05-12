from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSplitter, QTabWidget, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

from src.ui.plot_canvas import PlotCanvas
from src.ui.theme import TEXT_DIM, GREEN, RED, ORANGE, ACCENT


# ── Worker Thread ────────────────────────────────────────────────────────────
class Worker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)
    log      = pyqtSignal(str, str)   # (message, level)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ── Base Panel ───────────────────────────────────────────────────────────────
class BasePanel(QWidget):
    """
    Two-column layout:
      Left  – scrollable config area (fixed 290 px)
      Right – tabbed plot viewer + log strip
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._worker: Worker | None = None
        self._build(title, subtitle)

    # ── Layout construction ──────────────────────────────────────────────────
    def _build(self, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(self._make_header(title, subtitle))

        # Body splitter
        self._hsplit = QSplitter(Qt.Horizontal)
        self._hsplit.setChildrenCollapsible(False)

        # Left config scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(260)
        scroll.setMaximumWidth(320)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        config_inner = QWidget()
        self.config_layout = QVBoxLayout(config_inner)
        self.config_layout.setContentsMargins(14, 14, 14, 14)
        self.config_layout.setSpacing(10)
        self.config_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(config_inner)

        # Right: plots + log
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.plot_tabs = QTabWidget()
        self.plot_tabs.setObjectName("PlotTabs")
        self.plot_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.log = QTextEdit()
        self.log.setObjectName("LogOutput")
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(90)
        self.log.setMaximumHeight(160)
        self.log.document().setMaximumBlockCount(500)

        vsplit = QSplitter(Qt.Vertical)
        vsplit.setChildrenCollapsible(False)
        vsplit.addWidget(self.plot_tabs)
        vsplit.addWidget(self.log)
        vsplit.setSizes([700, 130])
        right_layout.addWidget(vsplit)

        self._hsplit.addWidget(scroll)
        self._hsplit.addWidget(right)
        self._hsplit.setSizes([290, 900])
        root.addWidget(self._hsplit)

    def _make_header(self, title: str, subtitle: str) -> QWidget:
        header = QWidget()
        header.setObjectName("PanelHeader")
        header.setFixedHeight(54)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("PageTitle")

        hl.addWidget(title_lbl)
        if subtitle:
            sep = QLabel("·")
            sep.setStyleSheet(f"color: {TEXT_DIM}; font-size: 16px; padding: 0 6px;")
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("PageSubtitle")
            hl.addWidget(sep)
            hl.addWidget(sub_lbl)
        hl.addStretch()
        return header

    # ── Helpers for subclasses ───────────────────────────────────────────────
    def add_section_title(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("SectionTitle")
        self.config_layout.addWidget(lbl)
        return lbl

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        self.config_layout.addWidget(line)

    def card(self, layout_type=QVBoxLayout) -> tuple:
        """Return (card_widget, card_inner_layout) wrapped in a styled card."""
        wrapper = QWidget()
        wrapper.setObjectName("ConfigCard")
        inner_layout = layout_type(wrapper)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(8)
        return wrapper, inner_layout

    # ── Logging ──────────────────────────────────────────────────────────────
    _LEVEL_COLORS = {
        "info":    TEXT_DIM,
        "data":    "#CCCAC2",
        "success": GREEN,
        "warn":    ORANGE,
        "error":   RED,
        "accent":  ACCENT,
    }

    def log_msg(self, msg: str, level: str = "data"):
        color = self._LEVEL_COLORS.get(level, "#CCCAC2")
        self.log.append(f'<span style="color:{color}">{msg}</span>')
        self.log.moveCursor(QTextCursor.End)

    def log_clear(self):
        self.log.clear()

    # ── Plot management ──────────────────────────────────────────────────────
    def show_figures(self, figures: list):
        """figures: list of (matplotlib.Figure, title_str)"""
        self.plot_tabs.clear()
        for fig, title in figures:
            canvas = PlotCanvas(fig)
            self.plot_tabs.addTab(canvas, title)

    def clear_plots(self):
        self.plot_tabs.clear()

    # ── Thread helpers ───────────────────────────────────────────────────────
    def _run_worker(self, func, *args, on_finish=None, on_error=None, **kwargs):
        if self._worker and self._worker.isRunning():
            return
        self._worker = Worker(func, *args, **kwargs)
        if on_finish:
            self._worker.finished.connect(on_finish)
        if on_error:
            self._worker.error.connect(on_error)
        self._worker.error.connect(lambda e: self.log_msg(f"Error: {e}", "error"))
        self._worker.start()
