import os
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QHBoxLayout, QVBoxLayout, QCheckBox, QFileDialog, QWidget
)
from PyQt5.QtCore import Qt

from src.ui.panels.base_panel import BasePanel
import src.analysis.peak_analysis as peak_analysis

# ── Presets: experiment type → baseline points ──────────────────────────────
PRESETS = {
    "Click Chemistry":  [105, 300, 560, 750],
    "Metallic Glass":   [105, 300, 560, 750],
    "EDC-NHS":          [150, 420, 820, 1080],
    "HATU":             [200, 400, 700, 900],
    "Custom":           [100, 300, 550, 750],
}


class PeakPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Peak Analysis", "Baseline correction & peak detection", parent)
        self._build_config()

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
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self._file_edit)
        row.addWidget(browse_btn)
        fc_layout.addLayout(row)
        self.config_layout.addWidget(file_card)

        # ── Curve index ───────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Curve Settings")
        curve_card, curve_layout = self.card()

        row_ci = QHBoxLayout()
        row_ci.addWidget(QLabel("Curve index"))
        self._curve_idx = QSpinBox()
        self._curve_idx.setRange(0, 20)
        self._curve_idx.setValue(1)
        self._curve_idx.setToolTip("0 = first CURVE section, 1 = second (typical for CV)")
        row_ci.addWidget(self._curve_idx)
        curve_layout.addLayout(row_ci)

        self._smooth_chk = QCheckBox("Apply Savitzky-Golay smoothing")
        self._smooth_chk.setChecked(True)
        curve_layout.addWidget(self._smooth_chk)
        self.config_layout.addWidget(curve_card)

        # ── Preset ───────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Experiment Preset")
        preset_card, preset_layout = self.card()

        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(PRESETS.keys()))
        self._preset_combo.currentTextChanged.connect(self._apply_preset)
        preset_layout.addWidget(self._preset_combo)
        self.config_layout.addWidget(preset_card)

        # ── Baseline points ───────────────────────────────────────────────────
        self.add_section_title("Baseline Points (index)")
        bp_card, bp_layout = self.card()

        self._bp_spins: list[QSpinBox] = []
        labels = ["P1 (ox start)", "P2 (ox end)", "P3 (red start)", "P4 (red end)"]
        for lbl in labels:
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl))
            sp = QSpinBox()
            sp.setRange(0, 9999)
            sp.setFixedWidth(80)
            row.addWidget(sp)
            bp_layout.addLayout(row)
            self._bp_spins.append(sp)
        self.config_layout.addWidget(bp_card)

        # Apply default preset values
        self._apply_preset(self._preset_combo.currentText())

        # ── Output dir ────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Output (optional)")
        out_card, out_layout = self.card()
        self._out_edit = QLineEdit()
        self._out_edit.setPlaceholderText("Save figures to folder… (leave empty to skip)")
        out_btn = QPushButton("Browse")
        out_btn.setObjectName("SecondaryBtn")
        out_btn.setFixedWidth(80)
        out_btn.clicked.connect(self._browse_output)
        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        out_row.addWidget(self._out_edit)
        out_row.addWidget(out_btn)
        out_layout.addLayout(out_row)
        self.config_layout.addWidget(out_card)

        # ── Run button ────────────────────────────────────────────────────────
        self.config_layout.addSpacing(8)
        self._run_btn = QPushButton("⚡  Run Peak Analysis")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.clicked.connect(self._run)
        self.config_layout.addWidget(self._run_btn)

        clr_btn = QPushButton("Clear")
        clr_btn.setObjectName("DangerBtn")
        clr_btn.clicked.connect(self._clear)
        self.config_layout.addWidget(clr_btn)
        self.config_layout.addStretch()

    # ── Slots ────────────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open DTA file", "", "DTA Files (*.DTA *.dta)")
        if path:
            self._file_edit.setText(path)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._out_edit.setText(d)

    def _apply_preset(self, name: str):
        pts = PRESETS.get(name, PRESETS["Custom"])
        for sp, val in zip(self._bp_spins, pts):
            sp.setValue(val)

    def _run(self):
        file_path = self._file_edit.text().strip()
        if not file_path or not os.path.isfile(file_path):
            self.log_msg("Please select a valid .DTA file.", "warn")
            return

        pts = [sp.value() for sp in self._bp_spins]
        curve_idx = self._curve_idx.value()
        smoothing = self._smooth_chk.isChecked()
        out_dir = self._out_edit.text().strip() or None
        label = os.path.splitext(os.path.basename(file_path))[0]

        self.log_clear()
        self.log_msg(f"File:        {os.path.basename(file_path)}", "info")
        self.log_msg(f"Curve index: {curve_idx}", "info")
        self.log_msg(f"Baseline pts:{pts}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            peak_analysis.run,
            file_path, pts,
            curve_index=curve_idx,
            apply_smoothing=smoothing,
            output_dir=out_dir,
            label=label,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        ox = result["peak_ox"]
        red = result["peak_red"]
        self.log_msg("Done.", "success")
        self.log_msg(f"Oxidation peak :  {ox[0]:.4f} V  |  {ox[1]:.3e} nA", "data")
        self.log_msg(f"Reduction peak :  {red[0]:.4f} V  |  {red[1]:.3e} nA", "data")
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")

    def _clear(self):
        self.log_clear()
        self.clear_plots()
