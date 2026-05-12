import os
import re
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QSpinBox, QHBoxLayout, QFileDialog
)

from src.ui.panels.base_panel import BasePanel
import src.analysis.electrografting as electrografting


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


class ElectrograftingPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__("Electrografting", "Multi-cycle CV visualisation", parent)
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

        # ── Settings ──────────────────────────────────────────────────────────
        self.add_separator()
        self.add_section_title("Settings")
        cfg_card, cfg_layout = self.card()
        cycles_row = QHBoxLayout()
        cycles_row.addWidget(QLabel("Max cycles per file"))
        self._cycles_spin = QSpinBox()
        self._cycles_spin.setRange(1, 10); self._cycles_spin.setValue(3)
        self._cycles_spin.setFixedWidth(70)
        cycles_row.addWidget(self._cycles_spin)
        cfg_layout.addLayout(cycles_row)

        exp_row = QHBoxLayout()
        exp_row.addWidget(QLabel("Experiment label"))
        self._exp_edit = QLineEdit("electrografting")
        self._exp_edit.textChanged.connect(self._update_output_preview)
        exp_row.addWidget(self._exp_edit)
        cfg_layout.addLayout(exp_row)
        self.config_layout.addWidget(cfg_card)

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
        self._run_btn = QPushButton("∿  Run Electrografting Analysis")
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
            self._update_output_preview()

    def _browse_base_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Base Output Folder")
        if d:
            self._base_dir_edit.setText(d)

    def _update_output_preview(self):
        base = self._base_dir_edit.text().strip()
        exp  = self._exp_edit.text().strip() or "electrografting"
        if base:
            self._out_preview.setText(
                os.path.join(base, _sanitize(exp), "{device}"))
        else:
            self._out_preview.setText("—")

    def _run(self):
        data_dir = self._dir_edit.text().strip()
        if not data_dir or not os.path.isdir(data_dir):
            self.log_msg("Please select a valid data directory.", "warn"); return

        max_cycles = self._cycles_spin.value()
        exp_type   = self._exp_edit.text().strip() or "electrografting"
        base_out   = self._base_dir_edit.text().strip() or None

        self.log_clear()
        self.log_msg(f"Directory:  {data_dir}", "info")
        self.log_msg(f"Max cycles: {max_cycles}", "info")
        if base_out:
            self.log_msg(f"Saving to:  {os.path.join(base_out, _sanitize(exp_type), '{device}')}", "info")
        self.log_msg("Running…", "accent")
        self._run_btn.setEnabled(False)

        self._run_worker(
            electrografting.run,
            data_dir,
            max_cycles=max_cycles,
            experiment_type=exp_type,
            base_output_dir=base_out,
            on_finish=self._on_done,
            on_error=self._on_error,
        )

    def _on_done(self, result: dict):
        self._run_btn.setEnabled(True)
        per_file = result["per_file"]
        ok  = [r for r in per_file if r["figure"] is not None]
        err = [r for r in per_file if r["error"]]
        self.log_msg(f"Processed {len(ok)} / {len(per_file)} files.", "success")
        for r in ok:  self.log_msg(f"  ✓ {r['label']}", "data")
        for r in err: self.log_msg(f"  ✗ {r['label']} — {r['error']}", "warn")
        figs = [(r["figure"], r["label"]) for r in ok]
        if result["grid_figure"]:
            figs.insert(0, (result["grid_figure"], "All Devices (Grid)"))
        self.show_figures(figs)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self.log_msg(f"Error: {msg}", "error")
