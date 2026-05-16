import os
import re
import numpy as np
from matplotlib.figure import Figure

from src.core.data_loader import load_curve
from src.core.peak_detection import smooth
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS

# Labels and colors for each scan segment
_SEG_LABELS = ["Forward", "Reverse", "Forward 2", "Reverse 2"]
_PAPER_COLORS = ["#1565C0", "#C62828", "#2E7D32", "#C07000"]


def _find_segments(v, c):
    """
    Split CV data at voltage turning points.

    Returns list of (v_seg, c_seg, label) for each monotonic segment.
    A 'turning point' is where dV changes sign (voltage reverses direction).
    """
    dv = np.diff(v)
    # Ignore tiny numerical noise: only count sign flips larger than 1% of range
    tol = 0.01 * (v.max() - v.min())
    sign = np.sign(dv)
    sign[np.abs(dv) < tol] = 0  # treat near-zero steps as neutral

    # Forward-fill zeros so we get clean sign transitions
    for i in range(1, len(sign)):
        if sign[i] == 0:
            sign[i] = sign[i - 1]

    # Find indices where sign actually changes
    changes = np.where(np.diff(sign) != 0)[0] + 1  # +1 → index in original array

    # Build segments between consecutive turning points
    boundaries = [0, *changes.tolist(), len(v)]
    segments = []
    for k in range(len(boundaries) - 1):
        s, e = boundaries[k], boundaries[k + 1]
        seg_v, seg_c = v[s:e], c[s:e]
        if len(seg_v) < 4:          # skip tiny edge artefacts
            continue
        label = _SEG_LABELS[k] if k < len(_SEG_LABELS) else f"Segment {k + 1}"
        segments.append((seg_v, seg_c, label))

    return segments


def _segment_didv(seg_v, seg_c, smooth_result=False):
    """
    dI/dV for one monotonic segment using numpy.gradient.
    Sign is always defined as dI / d(|V|) so forward and reverse are comparable.
    """
    # gradient handles monotonically increasing or decreasing v correctly,
    # but we normalize by the scan direction so the sign is intuitive.
    direction = 1 if seg_v[-1] > seg_v[0] else -1
    didv = np.gradient(seg_c, seg_v) * direction   # always positive dV denominator
    if smooth_result:
        didv = smooth(didv)
    return didv


def run(file_path, curve_index=1, apply_smoothing=True,
        smooth_derivative=False, base_output_dir=None,
        experiment_type="differential", device_name=None):
    """
    Compute dI/dV for each scan segment (forward / reverse) of a CV .DTA file.

    Because CV voltage reverses direction, the data is split at turning points
    before differentiation so each segment is monotonic.
    """
    voltage, current_raw = load_curve(file_path, curve_index)
    v = np.asarray(voltage, dtype=float)
    c = np.asarray(current_raw, dtype=float)

    if apply_smoothing:
        c = smooth(c)

    segments = _find_segments(v, c)
    if not segments:
        raise ValueError("Could not detect scan segments — check curve index.")

    results = []
    for seg_v, seg_c, label in segments:
        didv = _segment_didv(seg_v, seg_c, smooth_result=smooth_derivative)
        results.append({"v": seg_v, "c": seg_c, "didv": didv, "label": label})

    device = device_name or os.path.splitext(os.path.basename(file_path))[0]

    screen_figs = [(_screen_fig(results, device), "dI/dV")]

    if base_output_dir:
        def _san(s): return re.sub(r"[^a-zA-Z0-9_\-]", "_", s).strip("_")
        out = os.path.join(base_output_dir, _san(experiment_type), _san(device))
        os.makedirs(out, exist_ok=True)
        pfig = _paper_fig(results, device)
        save_for_paper(pfig, os.path.join(out, f"{_san(device)}_didv.png"))
        pfig.clf()

    return {"segments": results, "figures": screen_figs}


# ── Screen figure ─────────────────────────────────────────────────────────────
def _screen_fig(results, title):
    apply_mpl_style()
    fig = Figure(figsize=(9, 8))

    # Top: raw CV (all segments, coloured by direction)
    ax1 = fig.add_subplot(211)
    for k, r in enumerate(results):
        color = PLOT_COLORS[k % len(PLOT_COLORS)]
        ax1.plot(r["v"], r["c"], color=color, linewidth=1.6, label=r["label"])
    ax1.set_ylabel("Current  (nA)", fontsize=12)
    ax1.set_title(title, fontsize=11)
    ax1.legend(fontsize=10)

    # Bottom: dI/dV per segment
    ax2 = fig.add_subplot(212, sharex=ax1)
    for k, r in enumerate(results):
        color = PLOT_COLORS[k % len(PLOT_COLORS)]
        ax2.plot(r["v"], r["didv"], color=color, linewidth=1.6, label=r["label"])
    ax2.axhline(0, color="#707A8C", linewidth=0.8, linestyle="--")
    ax2.set_xlabel("Potential  (V)", fontsize=12)
    ax2.set_ylabel("dI/dV  (nA V⁻¹)", fontsize=12)
    ax2.legend(fontsize=10)

    fig.tight_layout()
    return fig


# ── Paper figure ──────────────────────────────────────────────────────────────
def _paper_fig(results, title):
    fig = Figure(figsize=(9, 8))

    ax1 = fig.add_subplot(211)
    for k, r in enumerate(results):
        ax1.plot(r["v"], r["c"],
                 color=_PAPER_COLORS[k % len(_PAPER_COLORS)],
                 linewidth=1.6, label=r["label"])
    ax1.set_ylabel("Current  (nA)", fontsize=12)
    ax1.set_title(title, fontsize=11)
    ax1.legend(fontsize=10)

    ax2 = fig.add_subplot(212, sharex=ax1)
    for k, r in enumerate(results):
        ax2.plot(r["v"], r["didv"],
                 color=_PAPER_COLORS[k % len(_PAPER_COLORS)],
                 linewidth=1.6, label=r["label"])
    ax2.axhline(0, color="#888888", linewidth=0.8, linestyle="--")
    ax2.set_xlabel("Potential  (V)", fontsize=12)
    ax2.set_ylabel("dI/dV  (nA V⁻¹)", fontsize=12)
    ax2.legend(fontsize=10)

    fig.tight_layout()
    return fig
