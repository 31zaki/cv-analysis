import re
from io import StringIO
import pandas as pd
import numpy as np

_DTA_COLS = ["Pt", "T", "Vf", "Im", "Vu", "Sig", "Ach", "IERange", "Over", "Temp"]


def _curve_indices(lines):
    return [
        i for i, ln in enumerate(lines)
        if ln.strip().startswith("CURVE") and "TABLE" in ln
    ]


def _parse_section(lines, idx, indices):
    start = idx + 3
    end = indices[indices.index(idx) + 1] if indices.index(idx) + 1 < len(indices) else len(lines)
    section = StringIO("".join(lines[start:end]))
    df = pd.read_csv(section, delimiter="\t", names=_DTA_COLS, comment="#")
    df = df[(df["Vf"] != "Vf") & (df["Im"] != "Im")]
    voltage = df["Vf"].astype(float).reset_index(drop=True)
    current = df["Im"].astype(float).reset_index(drop=True) * 1e9  # A → nA
    return voltage, current


def load_curve(file_path, curve_index=1):
    """Load a single CV curve from a .DTA file by index. Returns (voltage, current_nA)."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    idxs = _curve_indices(lines)
    if not idxs:
        raise ValueError(f"No CURVE TABLE sections in: {file_path}")
    if curve_index >= len(idxs):
        raise ValueError(f"curve_index={curve_index} out of range (found {len(idxs)})")
    return _parse_section(lines, idxs[curve_index], idxs)


def load_all_curves(file_path, max_curves=None):
    """Load all CV curves from a .DTA file. Returns list of (voltage, current_nA)."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    idxs = _curve_indices(lines)
    n = len(idxs) if max_curves is None else min(len(idxs), max_curves)
    curves = []
    for i in range(n):
        try:
            v, c = _parse_section(lines, idxs[i], idxs)
            if not v.empty:
                curves.append((v, c))
        except Exception:
            continue
    return curves


def count_curves(file_path):
    """Return the number of CURVE TABLE sections in a .DTA file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    return len(_curve_indices(lines))


def parse_scan_filename(filename):
    """Parse 'DEVICE_NNmVs.DTA' → (device_str, scan_rate_int). Returns (None, None) on failure."""
    m = re.match(r"^(.+?)_(\d+)mVs\.DTA$", filename, re.IGNORECASE)
    if m:
        return m.group(1), int(m.group(2))
    return None, None
