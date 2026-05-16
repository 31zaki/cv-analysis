import os
import re
import numpy as np
from scipy.signal import find_peaks
from matplotlib.figure import Figure

from src.core.data_loader import load_curve
from src.core.peak_detection import smooth
from src.ui.theme import apply_mpl_style, save_for_paper, PLOT_COLORS

_SEG_LABELS  = ["Forward", "Reverse", "Forward 2", "Reverse 2"]
_PAPER_COLORS = ["#1565C0", "#C62828", "#2E7D32", "#C07000"]


# ── Segment detection ─────────────────────────────────────────────────────────
def _find_segments(v, c):
    """
    Split CV at voltage turning points (VLIMIT1, VLIMIT2 …).

    Uses scipy.signal.find_peaks on the voltage array so the detection is
    robust regardless of step size.  Each returned segment is monotonic in V.
    """
    n = len(v)
    v_range = v.max() - v.min()
    # Turning points must be at least 10 % of the dataset apart and have
    # at least 5 % of the voltage range as prominence.
    min_dist   = max(10, n // 10)
    prominence = v_range * 0.05

    peaks,   _ = find_peaks( v, distance=min_dist, prominence=prominence)
    troughs, _ = find_peaks(-v, distance=min_dist, prominence=prominence)
    turns = sorted(peaks.tolist() + troughs.tolist())

    boundaries = [0] + turns + [n - 1]
    segments = []
    for k in range(len(boundaries) - 1):
        s = boundaries[k]
        e = boundaries[k + 1] + 1          # include the turning-point sample
        if e - s < 4:
            continue
        label = _SEG_LABELS[k] if k < len(_SEG_LABELS) else f"Segment {k + 1}"
        segments.append((v[s:e], c[s:e], label))

    # Fall-back: if no turns found return the whole sweep as one segment
    if not segments:
        segments = [(v, c, _SEG_LABELS[0])]

    return segments


def _segment_didv(seg_v, seg_c, smooth_result=False):
    """
    dI/dV for one monotonic segment.

    - numpy.gradient handles non-uniform spacing.
    - Sign is normalised to d(I)/d(|V|) so both scan directions are
      directly comparable (positive = current rising with |V|).
    - Edge points (prone to one-sided-difference artefacts near the
      turning point) are replaced by their nearest interior neighbour.
    """
    direction = 1 if seg_v[-1] >= seg_v[0] else -1
    didv = np.gradient(seg_c, seg_v) * direction

    # Suppress endpoint artefacts: replace first & last sample with
    # the adjacent interior value
    if len(didv) > 4:
        didv[0]  = didv[1]
        didv[-1] = didv[-2]

    if smooth_result:
        didv = smooth(didv)
    return didv


# ── Public entry point ────────────────────────────────────────────────────────
def run(file_path, curve_index=1, apply_smoothing=True,
        smooth_derivative=False, base_output_dir=None,
        experiment_type="differential", device_name=None):
    """
    Compute dI/dV per scan segment (forward / reverse) of a CV .DTA file.
    """
    voltage, current_raw = load_curve(file_path, curve_index)
    v = np.asarray(voltage,     dtype=float)
    c = np.asarray(current_raw, dtype=float)

    if apply_smoothing:
        c = smooth(c)

    segments = _find_segments(v, c)

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

    ax1 = fig.add_subplot(211)
    for k, r in enumerate(results):
        ax1.plot(r["v"], r["c"],
                 color=PLOT_COLORS[k % len(PLOT_COLORS)],
                 linewidth=1.6, label=r["label"])
    ax1.set_ylabel("Current  (nA)", fontsize=12)
    ax1.set_title(title, fontsize=11)
    ax1.legend(fontsize=10)

    ax2 = fig.add_subplot(212, sharex=ax1)
    for k, r in enumerate(results):
        ax2.plot(r["v"], r["didv"],
                 color=PLOT_COLORS[k % len(PLOT_COLORS)],
                 linewidth=1.6, label=r["label"])
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
