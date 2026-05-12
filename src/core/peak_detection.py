import numpy as np
from scipy.signal import savgol_filter


def smooth(current, window_length=11, polyorder=2):
    """Savitzky-Golay smoothing. Gracefully handles short arrays."""
    c = np.asarray(current, dtype=float)
    n = len(c)
    wl = min(window_length, n - 1)
    if wl % 2 == 0:
        wl -= 1
    if wl < polyorder + 2:
        return c
    return savgol_filter(c, window_length=wl, polyorder=polyorder)


def find_peaks(voltage, current, baseline):
    """
    Locate oxidation (max) and reduction (min) peaks in the baseline-corrected signal.
    Returns ((ox_V, ox_I), (red_V, red_I)) in V and nA.
    """
    v = np.asarray(voltage, dtype=float)
    diff = np.nan_to_num(np.asarray(current, dtype=float) - np.asarray(baseline, dtype=float))
    ox_i = int(np.argmax(diff))
    red_i = int(np.argmin(diff))
    return (float(v[ox_i]), float(diff[ox_i])), (float(v[red_i]), float(diff[red_i]))
