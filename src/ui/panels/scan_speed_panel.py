import os
import re
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QHBoxLayout, QCheckBox, QFileDialog
)

from src.ui.panels.base_panel import BasePanel
import src.analysis.scan_speed as scan_speed

PRESETS = {
    "Click Chemistry (S9D1)": {"device": "S9D1",  "pts": [100, 290, 550, 750]},
    "Metallic Glass (MG1)":   {"device": "MG1",   "pts": [100, 290, 550, 750]},
    "EDC-NHS (A5D6)":         {"device": "A5D6",  "pts": [150, 380, 700, 800]},
    "HATU (S4D5)":            {"device": "S4D5",  "pts": [200, 420, 700, 800]},
    "Custom":                 {"device": "",       "pts": [100, 300, 550, 750]},
}


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


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
        browse_btn.setObjectName("SecondaryBtn"); browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dir)
        row = QHBoxLayout(); row.setSpacing(6)
        row.addWidget(self._dir_edit); row.addWidget(browse_btn)
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
        self.add_section_title("Device Name")
        dev_card, dev_layout = self.card()
        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("Device"))
        self._device_edit = QLineEdit()
        self._device_edit.setPlaceholderText("e.g. S9D1  (leave empty = all)")
        self._device_edit.textChanged.connect(self._update_output_preview)
        dev_row.addWidget(self._device_edit)
        dev_layout.addLayout(dev_row)
        self.config_layout.addWidget(dev_card)

        # ── Baseline points ───────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Default Baseline Points")
        bp_card, bp_layout = self.card()
        self._bp_spins: list[QSpinBox] = []
        for lbl in ["P1", "P2", "P3", "P4"]:
            r = QHBoxLayout(); r.addWidget(QLabel(lbl))
            sp = QSpinBox(); sp.setRange(0, 9999); sp.setFixedWidth(80)
            r.addWidget(sp); bp_layout.addLayout(r)
            self._bp_spins.append(sp)
        self._smooth_chk = QCheckBox("Apply Savitzky-Golay smoothing")
        self._smooth_chk.setChecked(True)
        bp_layout.addWidget(self._smooth_chk)
        self.config_layout.addWidget(bp_card)
        self._apply_preset(self._preset_combo.currentText())

        # ── Auto output preview ───────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Output Directory")
        out_card, out_layout = self.card()
        base_row = QHBoxLayout(); base_row.setSpacing(6)
        self._base_dir_edit = QLineEdit()
        self._base_dir_edit.setText(os.path.join(os.path.expanduser("~"), "cv_output"))
        self._base_dir_edit.textChanged.connect(self._update_output_preview)
        base_btn = QPushButton("Change")
        base_btn.setObjectName("SecondaryBtn"); base_btn.setFixedWidth(70)
        base_btn.clicked.connect(self._browse_base_output)
        base_row.addWidget(self._base_dir_edit); base_row.addWidget(base_btn)
        out_layout.addLayout(base_row)
        self._out_preview = QLabel("—")
        self._out_preview.setStyleSheet(
            "color: #707A8C; font-size: 10px; font-family: Consolas;")
        self._out_preview.setWordWrap(True)
        out_layout.addWidget(self._out_preview)
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

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Data Folder")
        if d:
            self._dir_edit.setText(d)

    def _browse_base_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Output Folder")
        if d:
            self._base_dir_edit.setText(d)

    def _apply_preset(self, name: str):
        p = PRESETS.get(name, PRESETS["Custom"])
        self._device_edit.setText(p["device"])
        for sp, val in zip(self._bp_spins, p["pts"]):
            sp.setValue(val)
        self._update_output_preview()

    def _update_output_preview(self):
        if not hasattr(self, "_base_dir_edit") or not hasattr(self, "_out_preview"):
            return
        base   = self._base_dir_edit.text().strip()
        device = self._device_edit.text().strip() or "device"
        preset = self._preset_combo.currentText()
        exp    = re.sub(r"\s*\(.*?\)", "", preset).strip()  # strip "(S9D1)" suffix
        if base:
            self._out_preview.setText(
                os.path.join(base, _sanitize(exp), _sanitize(device))
            )
        else:
            self._out_preview.setText("—")

    def _run(self):
        data_dir = self._dir_edit.text().strip()
        if not data_dir or not os.path.isdir(data_dir):
            self.log_msg("Please select a valid data directory.", "warn"); return

        pts      = [sp.value() for sp in self._bp_spins]
        device   = self._device_edit.text().strip() or None
        smoothing = self._smooth_chk.isChecked()
        base_out = self._base_dir_edit.text().strip() or None
        preset   = self._preset_combo.currentText()
        exp_type = re.sub(r"\s*\(.*?\)", "", preset).strip()

        self.log_clear()
        self.log_msg(f"Directory:  {data_dir}", "info")
        self.log_msg(f"Experiment: {exp_type}  |  Device: {device or 'all'}", "info")
        self.log_msg(f"Baseline pts: {pts}", "info")
        if base_out:
            self.log_msg(f"Saving to: {os.path.join(base_out, _sanitize(exp_type), _sanitize(device or 'device'))}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            scan_speed.run,
            data_dir, pts,
            device_filter=device,
            apply_smoothing=smoothing,
            experiment_type=exp_type,
            base_output_dir=base_out,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        records, skipped = result["records"], result["skipped"]
        self.log_msg(f"Processed {len(records)} files.", "success")
        for r in records:
            self.log_msg(
                f"  {r['rate']:>5} mV/s  |  Ox {r['peak_ox'][0]:.3f} V {r['peak_ox'][1]:.2e} nA"
                f"  |  Red {r['peak_red'][0]:.3f} V {r['peak_red'][1]:.2e} nA", "data")
        if skipped:
            self.log_msg(f"Skipped: {', '.join(skipped)}", "warn")
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
