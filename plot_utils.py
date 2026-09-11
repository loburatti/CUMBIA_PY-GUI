"""Shared helpers for the figures produced by the analysis engines.

Both CUMBIA_CIR.py and CUMBIA_RECT.py draw the same pair of dual-scale axes
(absolute units on the left, a normalised ratio on the right), so the tick
logic lives here rather than being copied into each script.
"""
import numpy as np

# steps that read naturally on an axis, within each decade
_NICE_STEPS = (1.0, 2.0, 2.5, 5.0, 10.0)


def nice_step(span, target_ticks=5):
    """A round step that divides `span` into roughly `target_ticks` intervals.

    Returns one of 1, 2, 2.5 or 5 times a power of ten — the steps that read
    naturally on an axis — never zero.
    """
    span = float(span)
    if not np.isfinite(span) or span <= 0:
        return 1.0
    target_ticks = max(int(target_ticks), 1)

    raw = span / target_ticks
    decade = 10.0 ** np.floor(np.log10(raw))
    for step in _NICE_STEPS:
        if step * decade >= raw:
            return step * decade
    return _NICE_STEPS[-1] * decade


def ratio_ticks(upper_limit, reference, target_ticks=5):
    """Ticks for an axis labelled both in absolute units and as a ratio.

    `upper_limit` is the top of the absolute axis and `reference` the value
    the ratio is taken against (the axial load, the nominal moment). Returns
    the ratio values, all of which fall inside the axis.

    The engines used to hardcode a step of 0.4 in ratio units. Whenever the
    reference dwarfed the axis — a column under high axial load, where the
    lateral force never approaches P — every tick above zero landed outside
    the plotted range and the axis came out blank apart from the origin.
    """
    upper_limit = float(upper_limit)
    reference = abs(float(reference))
    if not np.isfinite(upper_limit) or upper_limit <= 0:
        return np.array([0.0])
    if not np.isfinite(reference) or reference <= 0:
        return np.array([0.0])

    span = upper_limit / reference
    step = nice_step(span, target_ticks)
    n = int(np.floor(span / step + 1e-9))
    return np.arange(0, n + 1) * step
