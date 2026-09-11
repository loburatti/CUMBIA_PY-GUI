"""Axis ticks on the dual-scale figures.

CUMBIA_CIR.py and CUMBIA_RECT.py draw force-displacement plots with kN on the
left axis and F/P on the right. The step used to be hardcoded at 0.4 in ratio
units, so whenever the axial load dwarfed the force scale every tick above
zero fell outside the plotted range and the axis came out blank apart from the
origin. Reported from a real circular run under high axial load.
"""
import numpy as np
import pytest

import plot_utils as pu
from tests.conftest import run_engine


# --------------------------------------------------------------- helpers ----
@pytest.mark.parametrize('span', [0.05, 0.3, 0.47, 1.0, 3.2, 17.0, 250.0])
def test_nice_step_divides_the_span_sensibly(span):
    step = pu.nice_step(span, target_ticks=5)
    assert step > 0
    n = span / step
    assert 1 <= n <= 12, f'span {span} split into {n:.1f} intervals'
    mantissa = step / 10.0 ** np.floor(np.log10(step))
    assert mantissa == pytest.approx(
        min((1.0, 2.0, 2.5, 5.0), key=lambda m: abs(m - mantissa)))


@pytest.mark.parametrize('reference,upper', [
    (2000.0, 931.9),    # repository default: used to work
    (3000.0, 700.0),    # used to render a bare axis
    (5000.0, 1200.0),   # used to render a bare axis
    (8000.0, 1500.0),   # used to render a bare axis
    (250.0, 1800.0),    # force scale far above the reference
    (1.0, 1e6),         # extreme ratio
])
def test_ratio_ticks_stay_inside_the_axis(reference, upper):
    ticks = pu.ratio_ticks(upper, reference)
    assert len(ticks) >= 2, 'an axis needs more than the origin to be readable'
    absolute = ticks * abs(reference)
    assert absolute.min() == 0
    assert absolute.max() <= upper + 1e-9, 'a tick was placed off the axis'
    assert np.all(np.diff(absolute) > 0)


def test_the_old_hardcoded_step_is_what_broke():
    """Pin the regression: the previous formula really did yield one tick."""
    reference, upper = 5000.0, 1200.0
    old_max = int(np.ceil(upper / reference * 10))
    old_ticks = [i / 10 for i in range(0, old_max + 1, 4)]
    assert old_ticks == [0.0], 'this case no longer reproduces the old bug'
    assert len(pu.ratio_ticks(upper, reference)) >= 2


@pytest.mark.parametrize('bad', [0, -5, float('nan'), float('inf')])
def test_degenerate_input_never_raises(bad):
    assert len(pu.ratio_ticks(bad, 100.0)) >= 1
    assert len(pu.ratio_ticks(100.0, bad)) >= 1


# ---------------------------------------------------------- real figures ----
def _force_axis_ticks(ns, fig_key):
    """Y ticks actually drawn inside the force-displacement axes."""
    ax = ns[fig_key].axes[0]
    lo, hi = ax.get_ylim()
    return [t for t in ax.get_yticks() if lo - 1e-9 <= t <= hi + 1e-9]


@pytest.mark.parametrize('P_kN', [2000.0, 5000.0, 8000.0])
def test_circular_force_axis_is_labelled_under_high_axial_load(P_kN):
    """The reported symptom: only the zero showed on the Force axis."""
    ns = run_engine('circular', {
        'name': f'axis_cir_{int(P_kN)}', 'interaction': 'n', 'P_kN': P_kN})

    for fig_key in ('fig6', 'fig7'):
        ticks = _force_axis_ticks(ns, fig_key)
        assert len(ticks) >= 2, (
            f'{fig_key} with P={P_kN} kN: only {len(ticks)} tick on the '
            f'force axis — the axis is unreadable')


@pytest.mark.parametrize('P_kN', [250.0, 3000.0])
def test_rectangular_force_axis_is_labelled(P_kN):
    """Same code path, so the same guard."""
    ns = run_engine('rectangular', {
        'name': f'axis_rect_{int(P_kN)}', 'interaction': 'n', 'P_kN': P_kN})

    for fig_key in ('fig6', 'fig7'):
        assert len(_force_axis_ticks(ns, fig_key)) >= 2


def test_left_and_right_force_axes_stay_aligned():
    """The right axis shows the same ticks expressed as F/P; they must be the
    same physical positions, which is the whole reason the step is shared."""
    P_kN = 5000.0
    ns = run_engine('circular', {
        'name': 'axis_align', 'interaction': 'n', 'P_kN': P_kN})

    axes = ns['fig6'].axes
    left = axes[0]
    ratio_axes = [a for a in axes[1:] if a.get_ylabel()]
    assert ratio_axes, 'no ratio axis found'
    right = ratio_axes[0]

    lo, hi = left.get_ylim()
    left_ticks = np.array([t for t in left.get_yticks() if lo - 1e-9 <= t <= hi + 1e-9])
    rlo, rhi = right.get_ylim()
    right_ticks = np.array([t for t in right.get_yticks() if rlo - 1e-9 <= t <= rhi + 1e-9])

    assert len(left_ticks) == len(right_ticks)
    assert np.allclose(right_ticks * P_kN, left_ticks, rtol=1e-9, atol=1e-6)
