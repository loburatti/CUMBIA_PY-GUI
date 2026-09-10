"""Level 4 - every option the GUI offers must actually run.

The GUI presents combo boxes for material models, bending configuration,
hinge method, P-Delta and interaction. Each combination is a distinct code
path through the engines, and a path that raises leaves the user with a
traceback in a dialog box after a full analysis has already been computed.
These tests walk the options the GUI can produce.

Interaction analysis is switched off where it is not the subject of the test:
it roughly doubles the run time and is covered separately.
"""
import numpy as np
import pytest

from tests.conftest import run_engine


def _healthy(ns):
    assert ns['Mn'] > 0
    assert np.all(np.isfinite(np.asarray(ns['mom'], dtype=float)))
    assert np.all(np.isfinite(np.asarray(ns['curv'], dtype=float)))
    assert np.asarray(ns['mom'], dtype=float).max() > 0


# ------------------------------------------------------- material models ----
# the option lists mirror CIR_PARAMS / RECT_PARAMS in main.py
@pytest.mark.parametrize('confined', ['mc', 'mu', 'mclw'])
def test_circular_confined_models(confined):
    _healthy(run_engine('circular', {
        'name': f'sm_cir_c_{confined}', 'interaction': 'n',
        'confined': confined}))


@pytest.mark.parametrize('unconfined', ['mc', 'mu', 'mclw', 'mulw'])
def test_circular_unconfined_models(unconfined):
    _healthy(run_engine('circular', {
        'name': f'sm_cir_u_{unconfined}', 'interaction': 'n',
        'unconfined': unconfined}))


@pytest.mark.parametrize('confined', ['mc', 'mclw'])
def test_rectangular_confined_models(confined):
    _healthy(run_engine('rectangular', {
        'name': f'sm_rect_c_{confined}', 'interaction': 'n',
        'confined': confined}))


@pytest.mark.parametrize('unconfined', ['mu', 'mulw', 'mclw'])
def test_rectangular_unconfined_models(unconfined):
    _healthy(run_engine('rectangular', {
        'name': f'sm_rect_u_{unconfined}', 'interaction': 'n',
        'unconfined': unconfined}))


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
@pytest.mark.parametrize('rebar', ['ra', 'ks'])
def test_rebar_models(section, rebar):
    _healthy(run_engine(section, {
        'name': f'sm_{section}_{rebar}', 'interaction': 'n', 'rebar': rebar}))


# ------------------------------------------------------ member behaviour ----
@pytest.mark.parametrize('section', ['circular', 'rectangular'])
@pytest.mark.parametrize('bending', ['single', 'double'])
def test_bending_configurations(section, bending):
    _healthy(run_engine(section, {
        'name': f'sm_{section}_{bending}', 'interaction': 'n',
        'bending': bending}))


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
@pytest.mark.parametrize('hinge', ['pck', 'modified_lpr'])
def test_hinge_methods(section, hinge):
    _healthy(run_engine(section, {
        'name': f'sm_{section}_{hinge}', 'interaction': 'n',
        'hinge_method': hinge}))


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
@pytest.mark.parametrize('mode', ['uniaxial', 'biaxial'])
def test_ductility_modes(section, mode):
    _healthy(run_engine(section, {
        'name': f'sm_{section}_{mode}', 'interaction': 'n',
        'ductilitymode': mode}))


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
@pytest.mark.parametrize('interaction', ['y', 'n'])
def test_interaction_toggle(section, interaction):
    """interaction='n' used to crash CUMBIA_CIR.py with a NameError on PTid."""
    _healthy(run_engine(section, {
        'name': f'sm_{section}_int_{interaction}', 'interaction': interaction}))


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
def test_p_delta_reduces_the_force_capacity(section):
    """P-Delta subtracts the overturning moment, so the force must not rise."""
    off = run_engine(section, {'name': f'sm_{section}_pd_n',
                               'interaction': 'n', 'p_delta': 'n'})
    on = run_engine(section, {'name': f'sm_{section}_pd_y',
                              'interaction': 'n', 'p_delta': 'y'})
    f_off = np.asarray(off['Force'], dtype=float)
    f_on = np.asarray(on['Force'], dtype=float)
    assert f_on.shape == f_off.shape
    assert np.all(f_on <= f_off + 1e-9)
    assert f_on.max() < f_off.max(), 'P-Delta had no effect at all'


# --------------------------------------------------------- input variety ----
@pytest.mark.parametrize('ecdam', ['twth', 0.018])
def test_ecdam_accepts_keyword_and_number(ecdam):
    """'twth' means 2/3 of ultimate; a number is used directly."""
    _healthy(run_engine('rectangular', {
        'name': 'sm_ecdam', 'interaction': 'n', 'ecdam': ecdam}))


@pytest.mark.parametrize('P_kN', [-200.0, 0.0, 250.0, 1500.0])
def test_axial_load_range(P_kN):
    """Tension, zero, service and high compression must all analyse."""
    ns = run_engine('rectangular', {
        'name': 'sm_axial', 'interaction': 'n', 'P_kN': P_kN})
    _healthy(ns)
    assert ns['P'] == pytest.approx(P_kN * 1000)


def test_custom_mlr_layout_is_honoured():
    """A custom bar layout must change Ast, not be silently ignored."""
    custom = [[52.7, 3, 25.4], [102.0, 2, 22.2],
              [200.0, 2, 19.0], [349.0, 3, 22.2]]
    ns = run_engine('rectangular', {
        'name': 'sm_mlr', 'interaction': 'n',
        'auto_generate_MLR': False, 'custom_MLR': custom,
        'wi_input': [0]})
    expected = sum(n * np.pi * d ** 2 / 4 for _, n, d in custom)
    assert ns['Ast'] == pytest.approx(expected, rel=1e-9)


def test_auto_mlr_generates_the_expected_bar_count():
    ns = run_engine('rectangular', {
        'name': 'sm_auto_mlr', 'interaction': 'n',
        'auto_generate_MLR': True, 'n_top_bot': 4, 'n_side': 2,
        'Dbl_auto': 25.4, 'wi_input': [0]})
    mlr = np.asarray(ns['MLR'], dtype=float)
    # top + bottom rows plus one row per side level
    assert len(mlr) == 4
    assert mlr[:, 1].sum() == 4 + 4 + 2 + 2


@pytest.mark.parametrize('type_reinf', ['spirals', 'hoops'])
def test_circular_transverse_reinforcement_types(type_reinf):
    _healthy(run_engine('circular', {
        'name': f'sm_cir_{type_reinf}', 'interaction': 'n',
        'type_reinf': type_reinf}))


# ---------------------------------------------------------- error paths ----
def test_invalid_interaction_flag_is_rejected():
    with pytest.raises(ValueError, match="'y' or 'n'"):
        run_engine('circular', {'name': 'sm_bad', 'interaction': 'maybe'})


def test_invalid_transverse_reinforcement_is_rejected():
    with pytest.raises(ValueError):
        run_engine('circular', {'name': 'sm_bad2', 'interaction': 'n',
                                'type_reinf': 'wedges'})
