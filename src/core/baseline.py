import numpy as np


def compute_baseline(voltage, current, points):
    """
    4-point linear baseline over two segments.
    points = [i1, i2, i3, i4]  (index positions in voltage/current)
    Returns baseline array; NaN outside the two defined segments.
    """
    i1, i2, i3, i4 = points
    v = np.asarray(voltage, dtype=float)
    c = np.asarray(current, dtype=float)

    def _seg(ia, ib):
        dv = v[ib] - v[ia]
        slope = (c[ib] - c[ia]) / dv if dv != 0 else 0.0
        return c[ia] + slope * (v[ia:ib + 1] - v[ia])

    baseline = np.full(len(v), np.nan)
    baseline[i1:i2 + 1] = _seg(i1, i2)
    baseline[i3:i4 + 1] = _seg(i3, i4)
    return baseline
