import os
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QComboBox, QHBoxLayout, QFileDialog
)

from src.ui.panels.base_panel import BasePanel
from src.analysis.efficiency import REACTION_COLUMNS
import src.analysis.efficiency as efficiency


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
        browse_btn.setObjectName("SecondaryBtn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_file)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self._file_edit)
        row.addWidget(browse_btn)
        fc_layout.addLayout(row)

        hint = QLabel(
            "Expected columns: device, grafting, click_ox, click_red,\n"
            "edcnhs_ox, edcnhs_red, hatu_ox, hatu_red  (values in Coulombs)"
        )
        hint.setStyleSheet("font-size: 11px; color: #707A8C; line-height: 1.5;")
        hint.setWordWrap(True)
        fc_layout.addWidget(hint)
        self.config_layout.addWidget(file_card)

        # ── Reaction type ─────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Reaction Type")
        rt_card, rt_layout = self.card()
        self._reaction_combo = QComboBox()
        self._reaction_combo.addItems(list(REACTION_COLUMNS.keys()))
        rt_layout.addWidget(self._reaction_combo)
        self.config_layout.addWidget(rt_card)

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

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self._out_edit.setText(d)

    def _run(self):
        csv_path = self._file_edit.text().strip()
        if not csv_path or not os.path.isfile(csv_path):
            self.log_msg("Please select a valid CSV file.", "warn")
            return

        reaction = self._reaction_combo.currentText()
        out_dir = self._out_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"File:     {os.path.basename(csv_path)}", "info")
        self.log_msg(f"Reaction: {reaction}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            efficiency.run,
            csv_path, reaction,
            output_dir=out_dir,
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
            f"  (IQR-filtered n={s['n_filtered']}): "
            f"{s['mean_eff_filtered']:.2f}%  ±  {s['std_eff_filtered']:.2f}%",
            "data"
        )
        self.show_figures(result["figures"])

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
