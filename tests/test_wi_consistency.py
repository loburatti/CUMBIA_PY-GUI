"""Level 2 - the wi (Mander restrained-bar spacing) calculation.

wi is computed TWICE in this project by two independent pieces of code:

  * main.py::CumbiaApp._compute_wi_mander  - used by the GUI, which passes the
    resulting numbers to the engine as an explicit `wi_input` list;
  * CUMBIA_RECT.py                          - the `wi_input == [0]` auto branch,
    used in script mode.

They must agree, or the same section analysed through the GUI and through the
script gives different confinement. Nothing in the code enforces that today,
so these tests do.

The wi fix is the headline change in CHANGES.md #1, so the properties it
relies on are pinned here as well.
"""
import numpy as np
import pytest

from tests.conftest import run_engine

AUTO_MLR = [[52.7, 4, 25.4], [150.9, 2, 25.4], [249.1, 2, 25.4], [347.3, 4, 25.4]]
CUSTOM_MLR = [[52.7, 3, 25.4], [102.0, 2, 22.2], [200.0, 2, 19.0], [349.0, 3, 22.2]]
# a face that cannot host every declared leg, and a layout with typed positions
SHORT_MLR = [[48.0, 2, 16.0], [175.0, 2, 16.0], [302.0, 3, 16.0]]
PLACED_X = [[52.7, 90.0, 210.0, 247.3], None, None, [52.7, 90.0, 210.0, 247.3]]

# (label, MLR, B, H, clb, ncx, ncy, bar_x)
CASES = [
    ('uniform-2x2', AUTO_MLR, 300.0, 400.0, 40.0, 2, 2, None),
    ('uniform-2x4', AUTO_MLR, 300.0, 400.0, 40.0, 2, 4, None),
    ('uniform-3x4', AUTO_MLR, 300.0, 400.0, 40.0, 3, 4, None),
    ('uniform-4x4', AUTO_MLR, 300.0, 400.0, 40.0, 4, 4, None),
    ('custom-2x2', CUSTOM_MLR, 350.0, 400.0, 40.0, 2, 2, None),
    ('custom-3x3', CUSTOM_MLR, 350.0, 400.0, 40.0, 3, 3, None),
    ('legs-without-bars', SHORT_MLR, 350.0, 350.0, 40.0, 4, 3, None),
    ('typed-positions', AUTO_MLR, 300.0, 400.0, 40.0, 3, 3, PLACED_X),
    ('single-layer', [[200.0, 4, 25.4]], 300.0, 400.0, 40.0, 2, 2, None),
]


def wi_from_gui(gui, mlr, B, H, clb, ncx, ncy, bar_x=None):
    """Call the real GUI method with a stand-in for the widget state.

    Built with CumbiaApp.__new__ rather than a bare class so that the helper
    methods _compute_wi_mander relies on resolve as bound methods. A plain
    stand-in would raise AttributeError, which the method swallows — the test
    would then silently compare two empty lists.
    """
    class _V:
        def __init__(self, value):
            self._v = str(value)

        def get(self):
            return self._v

    app = gui.CumbiaApp.__new__(gui.CumbiaApp)
    app._vars_rect = {'B': _V(B), 'H': _V(H), 'clb': _V(clb)}
    app._v_ncx = _V(ncx)
    app._v_ncy = _V(ncy)

    wi = list(gui.CumbiaApp._compute_wi_mander(app, [list(r) for r in mlr], bar_x))
    assert wi, 'the GUI returned no wi — the stand-in is probably incomplete'
    return wi


def wi_from_engine(mlr, B, H, clb, ncx, ncy, bar_x=None):
    """Run CUMBIA_RECT.py through its wi_input == [0] auto branch."""
    params = {
        'name': 'wi_probe', 'interaction': 'n',
        'B': B, 'H': H, 'clb': clb, 'ncx': ncx, 'ncy': ncy,
        'auto_generate_MLR': False, 'custom_MLR': [list(r) for r in mlr],
        'wi_input': [0],
    }
    if bar_x is not None:
        params['custom_bar_x'] = bar_x
    ns = run_engine('rectangular', params)
    return list(np.asarray(ns['wi'], dtype=float))


@pytest.mark.parametrize('label,mlr,B,H,clb,ncx,ncy,bar_x', CASES,
                         ids=[c[0] for c in CASES])
def test_gui_and_engine_agree_on_wi(gui, label, mlr, B, H, clb, ncx, ncy, bar_x):
    """The two implementations must produce identical wi arrays."""
    from_gui = wi_from_gui(gui, mlr, B, H, clb, ncx, ncy, bar_x)
    from_engine = wi_from_engine(mlr, B, H, clb, ncx, ncy, bar_x)

    assert len(from_gui) == len(from_engine), (
        f'{label}: GUI produced {len(from_gui)} gaps, '
        f'engine produced {len(from_engine)}')
    assert np.allclose(from_gui, from_engine, rtol=1e-12, atol=1e-9), (
        f'{label}: GUI {np.round(from_gui, 4)} != engine '
        f'{np.round(from_engine, 4)}')


@pytest.mark.parametrize('label,mlr,B,H,clb,ncx,ncy,bar_x', CASES,
                         ids=[c[0] for c in CASES])
def test_wi_gaps_are_physically_possible(gui, label, mlr, B, H, clb, ncx, ncy, bar_x):
    """Every clear distance must be positive and fit inside the core."""
    wi = wi_from_gui(gui, mlr, B, H, clb, ncx, ncy, bar_x)
    assert wi, f'{label}: no wi produced'
    assert all(w > 0 for w in wi), f'{label}: non-positive gap in {wi}'
    largest = max(B - 2 * clb, H - 2 * clb)
    assert max(wi) <= largest + 1e-9, (
        f'{label}: gap {max(wi):.1f} exceeds the core dimension {largest:.1f}')


def test_wi_count_follows_the_bars_the_legs_can_hold(gui):
    """Mander counts one gap per pair of adjacent restrained bars, on four
    faces. A leg holds a bar only where there is one: AUTO_MLR carries four
    bars per face, so beyond four legs the count stops growing."""
    for ncx, ncy in [(2, 2), (2, 4), (3, 4), (4, 4), (5, 3), (6, 6)]:
        wi = wi_from_gui(gui, AUTO_MLR, 300.0, 400.0, 40.0, ncx, ncy)
        expected = 2 * (min(max(ncy, 2), 4) - 1) + 2 * (min(max(ncx, 2), 4) - 1)
        assert len(wi) == expected, f'ncx={ncx} ncy={ncy}: {len(wi)} != {expected}'


def test_the_engine_reads_typed_bar_positions(gui):
    """custom_bar_x must survive the JSON round trip into the engine: it is
    the one nested list that may not be turned into a numpy matrix."""
    uniform = wi_from_engine(AUTO_MLR, 300.0, 400.0, 40.0, 3, 3)
    typed = wi_from_engine(AUTO_MLR, 300.0, 400.0, 40.0, 3, 3, PLACED_X)
    assert not np.allclose(sorted(uniform), sorted(typed)), (
        'the engine ignored the typed bar positions')


def test_more_legs_means_tighter_gaps(gui):
    """Adding crossties must reduce sum(wi^2), i.e. improve confinement.
    This is the engineering point of CHANGES.md #1."""
    loose = wi_from_gui(gui, AUTO_MLR, 300.0, 400.0, 40.0, 2, 2)
    tight = wi_from_gui(gui, AUTO_MLR, 300.0, 400.0, 40.0, 4, 4)
    assert np.sum(np.square(tight)) < np.sum(np.square(loose))


def test_two_legs_gives_the_corner_to_corner_clear_distance(gui):
    """With only a perimeter hoop, the single gap per face is the clear
    distance between the two corner bars - a value that can be checked by hand."""
    B, H, clb, dbl = 300.0, 400.0, 40.0, 25.4
    mlr = [[clb + dbl / 2, 4, dbl], [H - clb - dbl / 2, 4, dbl]]
    wi = wi_from_gui(gui, mlr, B, H, clb, 2, 2)

    top_gap = (B - 2 * clb) - 2 * dbl
    side_gap = (H - 2 * clb) - 2 * dbl
    assert wi[:2] == pytest.approx([top_gap, top_gap])
    assert wi[2:] == pytest.approx([side_gap, side_gap])


def test_explicit_wi_input_is_passed_through_untouched():
    """A non-zero wi_input must bypass the auto branch entirely."""
    explicit = [111.0, 222.0, 133.0, 144.0]
    ns = run_engine('rectangular', {
        'name': 'wi_explicit', 'interaction': 'n', 'wi_input': explicit,
    })
    assert list(np.asarray(ns['wi'], dtype=float)) == pytest.approx(explicit)


def test_wi_enters_confinement_through_sum_of_squares():
    """ke depends on sum(wi^2) only, so reordering wi must not change f'cc.
    (This is why the stale default wi_input in CUMBIA_RECT.py, which has the
    B-face and H-face values swapped, does not change the result.)"""
    base = [272.0, 272.0, 172.0, 172.0]
    swapped = [172.0, 172.0, 272.0, 272.0]
    a = run_engine('rectangular', {'name': 'wi_a', 'interaction': 'n',
                                   'wi_input': base})
    b = run_engine('rectangular', {'name': 'wi_b', 'interaction': 'n',
                                   'wi_input': swapped})
    assert a['fc'].max() == pytest.approx(b['fc'].max(), rel=1e-12)


# ------------------------------------------------ single source of truth ----
def test_both_callers_delegate_to_the_shared_geometry(gui):
    """GUI and engine must both go through section_geometry.wi_mander.

    If either grows its own copy of the formula again, the values may still
    agree on the day it is written and drift later; this checks the shared
    function is what actually produces them.
    """
    import section_geometry as sg

    for label, mlr, B, H, clb, ncx, ncy, bar_x in CASES:
        shared = list(np.asarray(sg.wi_mander(mlr, B, H, clb, ncx, ncy, bar_x), float))
        assert wi_from_gui(gui, mlr, B, H, clb, ncx, ncy, bar_x) == pytest.approx(shared), (
            f'{label}: the GUI no longer matches section_geometry.wi_mander')
        assert wi_from_engine(mlr, B, H, clb, ncx, ncy, bar_x) == pytest.approx(shared), (
            f'{label}: the engine no longer matches section_geometry.wi_mander')


def test_the_wi_formula_appears_only_once_in_the_sources():
    """A guard against a copy-paste reappearing in either caller."""
    import os
    import re

    from tests.conftest import REPO_ROOT

    # the distinctive term of the clear-distance formula
    pattern = re.compile(r'\(a\.dbl \+ b\.dbl\) / 2')
    hits = []
    for name in ('main.py', 'CUMBIA_RECT.py', 'material_models.py',
                 'section_geometry.py'):
        src = open(os.path.join(REPO_ROOT, name), encoding='utf-8').read()
        if pattern.search(src):
            hits.append(name)
    assert hits == ['section_geometry.py'], (
        f'the wi formula should live only in section_geometry.py, found in {hits}')


def test_gui_returns_plain_floats_for_the_parameter_file(gui):
    """wi_input is written to JSON, which cannot serialise numpy types."""
    import json

    wi = wi_from_gui(gui, AUTO_MLR, 300.0, 400.0, 40.0, 3, 4)
    assert all(type(v) is float for v in wi), f'non-float values: {wi}'
    json.dumps({'wi_input': wi})


def test_engine_default_uses_the_automatic_calculation():
    """CUMBIA_RECT.py ships wi_input = [0], so script mode and GUI mode
    analyse the same section with the same confinement."""
    import section_geometry as sg

    ns = run_engine('rectangular', {'name': 'wi_default', 'interaction': 'n'})
    expected = sg.wi_mander(ns['MLR'], ns['B'], ns['H'], ns['clb'],
                            ns['ncx'], ns['ncy'], ns['MLR_X'])
    assert np.allclose(np.asarray(ns['wi'], float), expected)
