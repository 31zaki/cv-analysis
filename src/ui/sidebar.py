from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

NAV_ITEMS = [
    ("⌂",  "Home"),
    ("⚡", "Peak Analysis"),
    ("≋",  "Scan Speed"),
    ("∿",  "Electrografting"),
    ("◎",  "Efficiency"),
    ("∂",  "Differential"),
]


class NavButton(QPushButton):
    def __init__(self, icon, label, index, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.setObjectName("NavButton")
        self.index = index
        self.setCheckable(False)
        self.setProperty("active", False)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(0)

        # ── Logo ────────────────────────────────────────────────────────────
        logo = QLabel("CV Analysis")
        logo.setObjectName("AppLogoLabel")
        sub = QLabel("Suite  v1.0")
        sub.setObjectName("AppSubLabel")
        layout.addWidget(logo)
        layout.addWidget(sub)

        # Divider
        layout.addSpacing(16)
        div = QFrame()
        div.setObjectName("SidebarDivider")
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        layout.addWidget(div)
        layout.addSpacing(12)

        # ── Nav Buttons ──────────────────────────────────────────────────────
        self._buttons: list[NavButton] = []
        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = NavButton(icon, label, i)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav(idx))
            layout.addWidget(btn)
            layout.addSpacing(2)
            self._buttons.append(btn)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ── Bottom divider + version ─────────────────────────────────────────
        div2 = QFrame()
        div2.setObjectName("SidebarDivider")
        div2.setFrameShape(QFrame.HLine)
        div2.setFixedHeight(1)
        layout.addWidget(div2)
        layout.addSpacing(8)

        ver = QLabel("Yuan Lab · Electrochemistry")
        ver.setObjectName("VersionLabel")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)

        self._select(0)

    def _on_nav(self, index: int):
        self._select(index)
        self.page_changed.emit(index)

    def _select(self, index: int):
        for btn in self._buttons:
            btn.set_active(btn.index == index)
