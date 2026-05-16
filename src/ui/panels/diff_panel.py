import os
import re
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QHBoxLayout, QCheckBox, QFileDialog
)

from src.ui.panels.base_panel import BasePanel
import src.analysis.differential as differential


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


def _parse_device(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"_\d+mVs.*$", "", stem, flags=re.IGNORECASE)
    return stem.strip("_") or stem


class DiffPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Differential CV", "dI/dV  —  first derivative of current", parent)
        self._build_config()

    def _build_config(self):
        # ── Input file ────────────────────────────────────────────────────────
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
        fc_layout.addLayout(ci_row)
        self.config_layout.addWidget(file_card)

        # ── Smoothing ─────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Smoothing")
        sm_card, sm_layout = self.card()
        self._smooth_raw_chk = QCheckBox("Smooth raw current (before dI/dV)")
        self._smooth_raw_chk.setChecked(True)
        sm_layout.addWidget(self._smooth_raw_chk)
        self._smooth_div_chk = QCheckBox("Smooth dI/dV result")
        self._smooth_div_chk.setChecked(False)
        sm_layout.addWidget(self._smooth_div_chk)
        hint = QLabel("Both use Savitzky-Golay filter")
        hint.setStyleSheet("font-size: 11px; color: #707A8C;")
        sm_layout.addWidget(hint)
        self.config_layout.addWidget(sm_card)

        # ── Output ────────────────────────────────────────────────────────────
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
        self._update_output_preview()

        # ── Run ───────────────────────────────────────────────────────────────
        self.config_layout.addSpacing(8)
        self._run_btn = QPushButton("∂  Run Differential")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.clicked.connect(self._run)
        self.config_layout.addWidget(self._run_btn)
        clr = QPushButton("Clear")
        clr.setObjectName("DangerBtn")
        clr.clicked.connect(lambda: (self.log_clear(), self.clear_plots()))
        self.config_layout.addWidget(clr)
        self.config_layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DTA File", "", "DTA Files (*.DTA *.dta)")
        if path:
            self._file_edit.setText(path)
            self._update_output_preview()

    def _browse_base_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Output Folder")
        if d:
            self._base_dir_edit.setText(d)

    def _update_output_preview(self):
        if not hasattr(self, "_base_dir_edit") or not hasattr(self, "_out_preview"):
            return
        base = self._base_dir_edit.text().strip()
        path = self._file_edit.text().strip() if hasattr(self, "_file_edit") else ""
        device = _parse_device(path) if path else "device"
        if base:
            self._out_preview.setText(
                os.path.join(base, "differential", _sanitize(device)))
        else:
            self._out_preview.setText("—")

    def _run(self):
        path = self._file_edit.text().strip()
        if not path or not os.path.isfile(path):
            self.log_msg("Please select a valid .DTA file.", "warn"); return

        device   = _parse_device(path)
        base_out = self._base_dir_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"File:    {os.path.basename(path)}", "info")
        self.log_msg(f"Device:  {device}", "info")
        self.log_msg(f"Curve index: {self._curve_idx.value()}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            differential.run,
            path,
            curve_index=self._curve_idx.value(),
            apply_smoothing=self._smooth_raw_chk.isChecked(),
            smooth_derivative=self._smooth_div_chk.isChecked(),
            base_output_dir=base_out,
            experiment_type="differential",
            device_name=device,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        didv = result["didv"]
        v    = result["voltage"]
        peak_idx = int(didv.argmax())
        trough_idx = int(didv.argmin())
        self.log_msg("Done.", "success")
        self.log_msg(
            f"  dI/dV max:  {didv[peak_idx]:.4e} nA/V  at  {v[peak_idx]:.3f} V", "data")
        self.log_msg(
            f"  dI/dV min:  {didv[trough_idx]:.4e} nA/V  at  {v[trough_idx]:.3f} V", "data")
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
