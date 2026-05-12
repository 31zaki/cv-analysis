import os
import re
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QComboBox, QHBoxLayout, QFileDialog
)

from src.ui.panels.base_panel import BasePanel
from src.analysis.efficiency import REACTION_COLUMNS
import src.analysis.efficiency as efficiency


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


class EfficiencyPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Efficiency", "Grafting vs reaction yield correlation", parent)
        self._build_config()

    def _build_config(self):
        # ── CSV file ──────────────────────────────────────────────────────────
        self.add_section_title("Input CSV")
        file_card, fc_layout = self.card()
        self._file_edit = QLineEdit()
        self._file_edit.setPlaceholderText("Select integrate.csv…")
        self._file_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SecondaryBtn"); browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_file)
        row = QHBoxLayout(); row.setSpacing(6)
        row.addWidget(self._file_edit); row.addWidget(browse_btn)
        fc_layout.addLayout(row)
        hint = QLabel(
            "Expected columns: device, grafting, click_ox, click_red,\n"
            "edcnhs_ox, edcnhs_red, hatu_ox, hatu_red  (values in Coulombs)")
        hint.setStyleSheet("font-size: 11px; color: #707A8C;")
        hint.setWordWrap(True)
        fc_layout.addWidget(hint)
        self.config_layout.addWidget(file_card)

        # ── Reaction type ─────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Reaction Type")
        rt_card, rt_layout = self.card()
        self._reaction_combo = QComboBox()
        self._reaction_combo.addItems(list(REACTION_COLUMNS.keys()))
        self._reaction_combo.currentTextChanged.connect(self._update_output_preview)
        rt_layout.addWidget(self._reaction_combo)
        self.config_layout.addWidget(rt_card)

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
        self._update_output_preview()

        # ── Run ───────────────────────────────────────────────────────────────
        self.config_layout.addSpacing(8)
        self._run_btn = QPushButton("◎  Run Efficiency Analysis")
        self._run_btn.setMinimumHeight(40)
        self._run_btn.clicked.connect(self._run)
        self.config_layout.addWidget(self._run_btn)
        clr = QPushButton("Clear")
        clr.setObjectName("DangerBtn")
        clr.clicked.connect(lambda: (self.log_clear(), self.clear_plots()))
        self.config_layout.addWidget(clr)
        self.config_layout.addStretch()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self._file_edit.setText(path)

    def _browse_base_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Output Folder")
        if d:
            self._base_dir_edit.setText(d)

    def _update_output_preview(self):
        base     = self._base_dir_edit.text().strip()
        reaction = self._reaction_combo.currentText()
        if base:
            self._out_preview.setText(
                os.path.join(base, "efficiency", _sanitize(reaction)))
        else:
            self._out_preview.setText("—")

    def _run(self):
        csv_path = self._file_edit.text().strip()
        if not csv_path or not os.path.isfile(csv_path):
            self.log_msg("Please select a valid CSV file.", "warn"); return

        reaction = self._reaction_combo.currentText()
        base_out = self._base_dir_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"File:     {os.path.basename(csv_path)}", "info")
        self.log_msg(f"Reaction: {reaction}", "info")
        if base_out:
            self.log_msg(
                f"Saving to: {os.path.join(base_out, 'efficiency', _sanitize(reaction))}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            efficiency.run,
            csv_path, reaction,
            experiment_type="efficiency",
            base_output_dir=base_out,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        s = result["stats"]
        self.log_msg("Done.", "success")
        self.log_msg(f"N samples      : {s['n']}", "data")
        self.log_msg(f"Correlation r  : {s['correlation']:.4f}", "data")
        self.log_msg(f"Mean efficiency: {s['mean_eff']:.2f}%  ±  {s['std_eff']:.2f}%", "data")
        self.log_msg(
            f"  IQR-filtered (n={s['n_filtered']}): "
            f"{s['mean_eff_filtered']:.2f}%  ±  {s['std_eff_filtered']:.2f}%", "data")
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
