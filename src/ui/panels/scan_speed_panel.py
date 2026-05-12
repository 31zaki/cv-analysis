import os
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QHBoxLayout, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt

from src.ui.panels.base_panel import BasePanel
import src.analysis.scan_speed as scan_speed

PRESETS = {
    "Click Chemistry (S9D1)":  {"device": "S9D1",  "pts": [100, 290, 550, 750]},
    "Metallic Glass (MG1)":    {"device": "MG1",   "pts": [100, 290, 550, 750]},
    "EDC-NHS (A5D6)":          {"device": "A5D6",  "pts": [150, 380, 700, 800]},
    "HATU (S4D5)":             {"device": "S4D5",  "pts": [200, 420, 700, 800]},
    "Custom":                  {"device": "",       "pts": [100, 300, 550, 750]},
}


class ScanSpeedPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Scan Speed", "Multi-rate CV comparison", parent)
        self._build_config()

    def _build_config(self):
        # ── Data directory ────────────────────────────────────────────────────
        self.add_section_title("Data Directory")
        dir_card, dir_layout = self.card()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Folder containing .DTA files…")
        self._dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SecondaryBtn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dir)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self._dir_edit)
        row.addWidget(browse_btn)
        dir_layout.addLayout(row)
        self.config_layout.addWidget(dir_card)

        # ── Preset ───────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Experiment Preset")
        preset_card, preset_layout = self.card()
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(PRESETS.keys()))
        self._preset_combo.currentTextChanged.connect(self._apply_preset)
        preset_layout.addWidget(self._preset_combo)
        self.config_layout.addWidget(preset_card)

        # ── Device filter ─────────────────────────────────────────────────────
        self.add_section_title("Device Filter")
        dev_card, dev_layout = self.card()
        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("Device name"))
        self._device_edit = QLineEdit()
        self._device_edit.setPlaceholderText("e.g. S9D1  (leave empty = all)")
        dev_row.addWidget(self._device_edit)
        dev_layout.addLayout(dev_row)
        self.config_layout.addWidget(dev_card)

        # ── Baseline points ───────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Default Baseline Points")
        bp_card, bp_layout = self.card()
        self._bp_spins: list[QSpinBox] = []
        labels = ["P1", "P2", "P3", "P4"]
        for lbl in labels:
            row2 = QHBoxLayout()
            row2.addWidget(QLabel(lbl))
            sp = QSpinBox()
            sp.setRange(0, 9999)
            sp.setFixedWidth(80)
            row2.addWidget(sp)
            bp_layout.addLayout(row2)
            self._bp_spins.append(sp)

        self._smooth_chk = QCheckBox("Apply Savitzky-Golay smoothing")
        self._smooth_chk.setChecked(True)
        bp_layout.addWidget(self._smooth_chk)
        self.config_layout.addWidget(bp_card)

        self._apply_preset(self._preset_combo.currentText())

        # ── Output dir ────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Output (optional)")
        out_card, out_layout = self.card()
        self._out_edit = QLineEdit()
        self._out_edit.setPlaceholderText("Save figures to folder…")
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

        # ── Run ───────────────────────────────────────────────────────────────
        self.config_layout.addSpacing(8)
        self._run_btn = QPushButton("≋  Run Scan Speed Analysis")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.clicked.connect(self._run)
        self.config_layout.addWidget(self._run_btn)
        clr = QPushButton("Clear")
        clr.setObjectName("DangerBtn")
        clr.clicked.connect(lambda: (self.log_clear(), self.clear_plots()))
        self.config_layout.addWidget(clr)
        self.config_layout.addStretch()

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Data Folder")
        if d:
            self._dir_edit.setText(d)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._out_edit.setText(d)

    def _apply_preset(self, name: str):
        p = PRESETS.get(name, PRESETS["Custom"])
        self._device_edit.setText(p["device"])
        for sp, val in zip(self._bp_spins, p["pts"]):
            sp.setValue(val)

    def _run(self):
        data_dir = self._dir_edit.text().strip()
        if not data_dir or not os.path.isdir(data_dir):
            self.log_msg("Please select a valid data directory.", "warn")
            return

        pts = [sp.value() for sp in self._bp_spins]
        device = self._device_edit.text().strip() or None
        smoothing = self._smooth_chk.isChecked()
        out_dir = self._out_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"Directory: {data_dir}", "info")
        self.log_msg(f"Device filter: {device or 'all'}", "info")
        self.log_msg(f"Baseline pts:  {pts}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            scan_speed.run,
            data_dir, pts,
            device_filter=device,
            apply_smoothing=smoothing,
            output_dir=out_dir,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        records = result["records"]
        skipped = result["skipped"]
        self.log_msg(f"Processed {len(records)} files.", "success")
        for r in records:
            self.log_msg(
                f"  {r['rate']:>5} mV/s  |  Ox {r['peak_ox'][0]:.3f} V {r['peak_ox'][1]:.2e} nA"
                f"  |  Red {r['peak_red'][0]:.3f} V {r['peak_red'][1]:.2e} nA",
                "data"
            )
        if skipped:
            self.log_msg(f"Skipped: {', '.join(skipped)}", "warn")
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
