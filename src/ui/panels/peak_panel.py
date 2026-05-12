import os
import re
import numpy as np
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QHBoxLayout, QVBoxLayout, QCheckBox, QFileDialog,
    QWidget, QGridLayout
)
from PyQt5.QtCore import Qt

from src.ui.panels.base_panel import BasePanel
from src.ui.interactive_canvas import InteractiveCanvas
from src.ui.plot_canvas import PlotCanvas
from src.ui.theme import ACCENT, GREEN, TEXT_DIM, ORANGE
from src.core.data_loader import load_curve
from src.core.peak_detection import smooth
import src.analysis.peak_analysis as peak_analysis

PRESETS = {
    "Click Chemistry": [105, 300, 560, 750],
    "Metallic Glass":  [105, 300, 560, 750],
    "EDC-NHS":         [150, 420, 820, 1080],
    "HATU":            [200, 400, 700, 900],
}

_POINT_COLORS = [ACCENT, ACCENT, ORANGE, ORANGE]
_POINT_LABELS = ["P1  ox-start", "P2  ox-end", "P3  red-start", "P4  red-end"]


def _parse_device(file_path: str) -> str:
    stem = os.path.splitext(os.path.basename(file_path))[0]
    stem = re.sub(r"_\d+mVs.*$", "", stem, flags=re.IGNORECASE)
    return stem.strip("_") or stem


class PeakPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Peak Analysis", "Baseline correction & peak detection", parent)
        self._voltage = None
        self._current = None
        self._build_config()
        self._setup_canvas()

    def _setup_canvas(self):
        self._icanvas = InteractiveCanvas()
        self._icanvas.points_changed.connect(self._on_points_changed)
        self.plot_tabs.addTab(self._icanvas, "CV Preview")

    def _build_config(self):
        # ── File ─────────────────────────────────────────────────────────────
        self.add_section_title("Input File")
        file_card, fc_layout = self.card()
        self._file_edit = QLineEdit()
        self._file_edit.setPlaceholderText("Select a .DTA file…")
        self._file_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SecondaryBtn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_file)
        row = QHBoxLayout(); row.setSpacing(6)
        row.addWidget(self._file_edit); row.addWidget(browse_btn)
        fc_layout.addLayout(row)

        ci_row = QHBoxLayout()
        ci_row.addWidget(QLabel("Curve index"))
        self._curve_idx = QSpinBox()
        self._curve_idx.setRange(0, 20); self._curve_idx.setValue(1)
        self._curve_idx.setFixedWidth(60)
        self._curve_idx.setToolTip("0 = first CURVE TABLE, 1 = second (typical)")
        ci_row.addWidget(self._curve_idx); ci_row.addStretch()
        self._smooth_chk = QCheckBox("Smooth")
        self._smooth_chk.setChecked(True)
        ci_row.addWidget(self._smooth_chk)
        fc_layout.addLayout(ci_row)

        self._load_btn = QPushButton("Load CV")
        self._load_btn.setObjectName("GreenBtn")
        self._load_btn.setMinimumHeight(34)
        self._load_btn.clicked.connect(self._load_cv)
        fc_layout.addWidget(self._load_btn)
        self.config_layout.addWidget(file_card)

        # ── Experiment + Device ───────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Experiment")
        exp_card, exp_layout = self.card()

        exp_layout.addWidget(QLabel("Type"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(PRESETS.keys()))
        self._preset_combo.currentTextChanged.connect(self._update_output_preview)
        exp_layout.addWidget(self._preset_combo)

        exp_layout.addWidget(QLabel("Device name"))
        self._device_edit = QLineEdit()
        self._device_edit.setPlaceholderText("auto-detected from filename")
        self._device_edit.textChanged.connect(self._update_output_preview)
        exp_layout.addWidget(self._device_edit)
        self.config_layout.addWidget(exp_card)

        # ── Baseline point selection ──────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Baseline Points")
        sel_card, sel_layout = self.card()

        self._sel_btn = QPushButton("  ✦  Click to Select Points  (0 / 4)")
        self._sel_btn.setCheckable(True)
        self._sel_btn.setObjectName("SecondaryBtn")
        self._sel_btn.setMinimumHeight(34)
        self._sel_btn.toggled.connect(self._toggle_selection)
        self._sel_btn.setEnabled(False)
        sel_layout.addWidget(self._sel_btn)

        self._clr_pts_btn = QPushButton("Clear selection")
        self._clr_pts_btn.setObjectName("DangerBtn")
        self._clr_pts_btn.clicked.connect(self._clear_selection)
        self._clr_pts_btn.setEnabled(False)
        sel_layout.addWidget(self._clr_pts_btn)

        self._pt_labels: list[QLabel] = []
        grid = QGridLayout(); grid.setSpacing(4); grid.setColumnStretch(1, 1)
        for i in range(4):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {_POINT_COLORS[i]}; font-size: 14px;")
            name_lbl = QLabel(_POINT_LABELS[i])
            name_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
            val_lbl = QLabel("—")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lbl.setStyleSheet("font-size: 11px; font-family: Consolas;")
            grid.addWidget(dot, i, 0); grid.addWidget(name_lbl, i, 1); grid.addWidget(val_lbl, i, 2)
            self._pt_labels.append(val_lbl)
        sel_layout.addLayout(grid)
        self.config_layout.addWidget(sel_card)

        # ── Auto output preview ───────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Output Directory")
        out_card, out_layout = self.card()

        base_row = QHBoxLayout(); base_row.setSpacing(6)
        self._base_dir_edit = QLineEdit()
        self._base_dir_edit.setPlaceholderText("Base output folder…")
        self._base_dir_edit.setText(
            os.path.join(os.path.expanduser("~"), "cv_output")
        )
        self._base_dir_edit.textChanged.connect(self._update_output_preview)
        base_btn = QPushButton("Change")
        base_btn.setObjectName("SecondaryBtn"); base_btn.setFixedWidth(70)
        base_btn.clicked.connect(self._browse_base_output)
        base_row.addWidget(self._base_dir_edit); base_row.addWidget(base_btn)
        out_layout.addLayout(base_row)

        self._out_preview = QLabel("—")
        self._out_preview.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 10px; font-family: Consolas;"
        )
        self._out_preview.setWordWrap(True)
        out_layout.addWidget(self._out_preview)
        self.config_layout.addWidget(out_card)

        # ── Run ───────────────────────────────────────────────────────────────
        self.config_layout.addSpacing(8)
        self._run_btn = QPushButton("⚡  Run Analysis")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.setEnabled(False)
        self._run_btn.clicked.connect(self._run)
        self.config_layout.addWidget(self._run_btn)
        clr_all = QPushButton("Clear all")
        clr_all.setObjectName("DangerBtn")
        clr_all.clicked.connect(self._clear_all)
        self.config_layout.addWidget(clr_all)
        self.config_layout.addStretch()

    # ── Output path preview ──────────────────────────────────────────────────
    def _update_output_preview(self):
        base = self._base_dir_edit.text().strip()
        exp  = self._preset_combo.currentText()
        dev  = self._device_edit.text().strip() or "device"
        if base:
            preview = os.path.join(base,
                                   re.sub(r"[^a-zA-Z0-9_\-]", "_", exp).strip("_"),
                                   re.sub(r"[^a-zA-Z0-9_\-]", "_", dev).strip("_"))
            self._out_preview.setText(preview)
        else:
            self._out_preview.setText("—")

    def _browse_base_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Output Folder")
        if d:
            self._base_dir_edit.setText(d)

    # ── File load ────────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DTA File", "", "DTA Files (*.DTA *.dta)")
        if path:
            self._file_edit.setText(path)
            detected = _parse_device(path)
            self._device_edit.setText(detected)
            self._update_output_preview()

    def _load_cv(self):
        path = self._file_edit.text().strip()
        if not path or not os.path.isfile(path):
            self.log_msg("Please browse for a .DTA file first.", "warn"); return
        try:
            v, c_raw = load_curve(path, self._curve_idx.value())
            c = smooth(np.asarray(c_raw, dtype=float)) if self._smooth_chk.isChecked() \
                else np.asarray(c_raw, dtype=float)
            self._voltage, self._current = v, c
            self._icanvas.set_data(v, c)
            self._sel_btn.setEnabled(True)
            self._sel_btn.setText("  ✦  Click to Select Points  (0 / 4)")
            self.plot_tabs.setCurrentIndex(0)
            self.log_msg(f"Loaded: {os.path.basename(path)}", "success")
            self.log_msg(f"  {len(v)} data points  |  curve index {self._curve_idx.value()}", "info")
            self.log_msg(f"Preset '{self._preset_combo.currentText()}': "
                         f"suggested indices {PRESETS[self._preset_combo.currentText()]}", "info")
            self.log_msg("Click 'Click to Select Points' to pick baseline interactively.", "accent")
        except Exception as e:
            self.log_msg(f"Error loading file: {e}", "error")

    # ── Selection ────────────────────────────────────────────────────────────
    def _toggle_selection(self, checked: bool):
        if self._voltage is None:
            self._sel_btn.setChecked(False); return
        self._icanvas.set_selection_mode(checked)
        n = len(self._icanvas.selected_indices)
        if checked:
            self._sel_btn.setText(f"  ✦  Selecting…  ({n} / 4)   — click to cancel")
            self.plot_tabs.setCurrentIndex(0)
        else:
            self._sel_btn.setText(f"  ✦  Click to Select Points  ({n} / 4)")

    def _on_points_changed(self, indices: list):
        n = len(indices)
        if self._sel_btn.isChecked() and n < 4:
            self._sel_btn.setText(f"  ✦  Selecting…  ({n} / 4)   — click to cancel")
        else:
            self._sel_btn.setText(f"  ✦  Click to Select Points  ({n} / 4)")
            self._sel_btn.setChecked(False)

        v = np.asarray(self._voltage, dtype=float) if self._voltage is not None else None
        for i, lbl in enumerate(self._pt_labels):
            if i < n:
                idx = indices[i]
                volt = f"{v[idx]:.3f} V" if v is not None else ""
                lbl.setText(f"idx {idx}  {volt}")
                lbl.setStyleSheet(f"color: {_POINT_COLORS[i]}; font-size: 11px; font-family: Consolas;")
            else:
                lbl.setText("—")
                lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-family: Consolas;")

        self._clr_pts_btn.setEnabled(n > 0)
        self._run_btn.setEnabled(n == 4)
        if n == 4:
            self.log_msg(f"✓ 4 points selected: {indices}", "success")
            self.log_msg("Ready — click 'Run Analysis'.", "accent")

    def _clear_selection(self):
        self._icanvas.clear_selection()
        self._sel_btn.setText("  ✦  Click to Select Points  (0 / 4)")
        self._sel_btn.setChecked(False)
        self._run_btn.setEnabled(False)
        self._clr_pts_btn.setEnabled(False)

    # ── Run ──────────────────────────────────────────────────────────────────
    def _run(self):
        file_path = self._file_edit.text().strip()
        indices   = self._icanvas.selected_indices
        if len(indices) != 4:
            self.log_msg("Select exactly 4 baseline points first.", "warn"); return

        pts      = sorted(indices[:2]) + sorted(indices[2:])
        exp_type = self._preset_combo.currentText()
        device   = self._device_edit.text().strip() or _parse_device(file_path)
        base_out = self._base_dir_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"File:        {os.path.basename(file_path)}", "info")
        self.log_msg(f"Experiment:  {exp_type}  |  Device: {device}", "info")
        self.log_msg(f"Points:      {pts}", "info")
        if base_out:
            out_dir = os.path.join(base_out,
                                   re.sub(r"[^a-zA-Z0-9_\-]", "_", exp_type).strip("_"),
                                   re.sub(r"[^a-zA-Z0-9_\-]", "_", device).strip("_"))
            self.log_msg(f"Saving to:   {out_dir}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            peak_analysis.run,
            file_path, pts,
            curve_index=self._curve_idx.value(),
            apply_smoothing=self._smooth_chk.isChecked(),
            experiment_type=exp_type,
            device_name=device,
            base_output_dir=base_out,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        ox, red = result["peak_ox"], result["peak_red"]
        self.log_msg("Done.", "success")
        self.log_msg(f"Oxidation peak :  {ox[0]:.4f} V  |  {ox[1]:.3e} nA", "data")
        self.log_msg(f"Reduction peak :  {red[0]:.4f} V  |  {red[1]:.3e} nA", "data")
        while self.plot_tabs.count() > 1:
            self.plot_tabs.removeTab(1)
        for fig, title in result["figures"]:
            self.plot_tabs.addTab(PlotCanvas(fig), title)
        if self.plot_tabs.count() > 2:
            self.plot_tabs.setCurrentIndex(2)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")

    def _clear_all(self):
        self._clear_selection()
        self.log_clear()
        while self.plot_tabs.count() > 1:
            self.plot_tabs.removeTab(1)
        if self._voltage is not None:
            self._icanvas.set_data(self._voltage, self._current)
