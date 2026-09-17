"""Level 5 - the buckling models must stay internally consistent.

The four buckling models are post-processing scalars layered on top of the
moment-curvature analysis, and nothing else in the engines reads them back.
That isolation is convenient, but it also means a wrong constant or a wrong
length can sit in the code for a long time without breaking anything visible.
These tests pin the invariants that caught the two defects fixed in 0.3.4:

* the Goodnight drift model must return the same limit for the same physical
  column whether it is idealised as a cantilever or as a fixed-fixed member;
* every model written in terms of the transverse ratio rho_s must be fed the
  same rho_s.
"""
import numpy as np
import pytest

from tests.conftest import run_engine


# --------------------------------------------------- Goodnight drift model ----
# A fixed-fixed member of length L with its point of contraflexure at midheight
# is the same physical column as a cantilever of length L/2, and drift ratio is
# the same quantity in both idealisations (d_total/L_total == d_tip/Lc). The
# aspect-ratio term therefore has to use the shear span, not the member length.
@pytest.mark.parametrize('section,kwargs_single,kwargs_double', [
    ('circular',
     {'name': 'bk_cir_s', 'bending': 'single', 'L': 2000.0},
     {'name': 'bk_cir_d', 'bending': 'double', 'L': 4000.0}),
    ('rectangular',
     {'name': 'bk_rect_s', 'bending': 'single', 'L': 2000.0},
     {'name': 'bk_rect_d', 'bending': 'double', 'L': 4000.0}),
])
def test_goodnight_drift_limit_is_idealisation_invariant(
        section, kwargs_single, kwargs_double):
    base = {'interaction': 'n'}
    single = run_engine(section, {**base, **kwargs_single})
    double = run_engine(section, {**base, **kwargs_double})

    assert single['drift_bb_pct'] == pytest.approx(double['drift_bb_pct'], rel=1e-12)


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
def test_goodnight_drift_uses_the_shear_span(section):
    """The aspect-ratio term must be built on LBE, the shear span."""
    ns = run_engine(section, {'name': f'bk_span_{section}', 'interaction': 'n',
                              'bending': 'double', 'L': 4000.0})
    depth = ns['D'] if section == 'circular' else ns['H']
    rho = (ns['TransvSteelRatio'] if section == 'circular'
           else ns['TransvSteelRatioVolumetric'])

    expected = (0.9 - 3.13 * ns['AxialRatio']
                + 142000 * rho * (ns['fyh'] / ns['Es'])
                + 0.45 * (ns['LBE'] / depth))
    assert ns['drift_bb_pct'] == pytest.approx(expected, rel=1e-12)
    assert ns['LBE'] == pytest.approx(ns['L'] / 2)


# ------------------------------------------------------ rho_s consistency ----
def test_rectangular_models_share_one_volumetric_ratio():
    """Berry-Eberhard and both Goodnight models must see the same rho_s.

    rho_s for a rectangular core is rho_x + rho_y. Feeding one model the
    average of the two directions and another their sum is a silent factor of
    two between models that are meant to be compared on the same plot.
    """
    ns = run_engine('rectangular', {'name': 'bk_rho', 'interaction': 'n'})
    rho_s = ns['TransvSteelRatioVolumetric']

    assert rho_s == pytest.approx(ns['TransvSteelRatioX'] + ns['TransvSteelRatioY'])
    assert rho_s == pytest.approx(2 * ns['TransvSteelRatioAverage'])

    assert ns['roeff'] == pytest.approx(rho_s * ns['fyh'] / ns['fpc'], rel=1e-12)
    assert ns['es_bb'] == pytest.approx(
        0.03 + 700 * rho_s * (ns['fyh'] / ns['Es']) - 0.1 * ns['AxialRatio'],
        rel=1e-12)


def test_circular_transverse_ratio_is_volumetric():
    """The circular engine already carries rho_s directly; guard the meaning."""
    ns = run_engine('circular', {'name': 'bk_rho_cir', 'interaction': 'n'})
    assert ns['TransvSteelRatio'] == pytest.approx(
        np.pi * ns['Dh']**2 / (ns['s'] * ns['Dsp']))
    assert ns['roeff'] == pytest.approx(
        ns['TransvSteelRatio'] * ns['fyh'] / ns['fpc'], rel=1e-12)


# ------------------------------------------- Moyer-Kowalsky growth strain ----
@pytest.mark.parametrize('section', ['circular', 'rectangular'])
def test_growth_strain_follows_the_published_interpolation(section):
    """Section 6 of the Theory Guide: the growth strain is zero at mu_phi = 1.

    It then interpolates linearly up to esgr4 at mu_phi = 4, and equals half
    the peak tension strain beyond that. The superseded form (esgr4/4)*mu_phi
    left a step of esgr4/4 at mu_phi = 1; comparing the whole array against
    the published expression rules it out without depending on where the
    curvature samples happen to fall.
    """
    ns = run_engine(section, {'name': f'bk_esgr_{section}', 'interaction': 'n'})
    if 'esfl' not in ns:
        pytest.skip('Moyer-Kowalsky did not run for this section')

    CuDu = np.asarray(ns['CuDu'], dtype=float)
    esfl = np.asarray(ns['esfl'], dtype=float)
    steelstrain = np.asarray(ns['steelstrain'], dtype=float)
    escc, esgr4 = ns['escc'], ns['esgr4']

    esgr = escc - esfl
    expected = np.where(
        CuDu < 1, 0.0,
        np.where(CuDu <= 4, esgr4 * (CuDu - 1) / 3.0, -0.5 * steelstrain))
    assert np.allclose(esgr, expected, atol=1e-15, rtol=0)

    # Below yield the limit is the characteristic capacity, untouched.
    assert np.all(esfl[CuDu < 1] == escc)


def test_applicability_notes_stay_quiet_on_a_well_detailed_circular_section():
    """The circular defaults are seismically detailed: nothing to report."""
    ns = run_engine('circular', {'name': 'bk_notes_cir', 'interaction': 'n'})
    assert ns['s'] / ns['Dbl'] <= 8, 'default section is no longer well detailed'
    assert ns['buckling_notes'] == []


def test_rectangular_always_reports_the_goodnight_extrapolation():
    """Applying a circular-column calibration to a rectangular core is a
    standing caveat, not a conditional one: it holds however good the
    detailing is, so it must be stated on every run that reports a Goodnight
    result. The M&K notes, by contrast, are conditional and must stay silent
    on a well detailed section."""
    ns = run_engine('rectangular', {'name': 'bk_notes_rect', 'interaction': 'n'})
    assert ns['s'] / ns['dbl_extreme'] <= 8, 'default section is no longer well detailed'

    notes = ns['buckling_notes']
    assert len(notes) == 1
    assert notes[0].startswith('Goodnight')
    assert 'Moyer-Kowalsky' not in ' '.join(notes)


def test_applicability_notes_fire_on_wide_tie_spacing():
    """A tie spacing well outside the M&K calibration must be reported."""
    ns = run_engine('rectangular', {
        'name': 'bk_notes_wide', 'interaction': 'n',
        'bending': 'double', 'L': 4000.0, 'B': 350.0, 'H': 350.0,
        's': 200.0, 'dv': 8.0, 'ncx': 3, 'ncy': 3,
        'n_top_bot': 3, 'n_side': 1, 'Dbl_auto': 16.0, 'P_kN': 500.0})

    assert ns['s'] / ns['dbl_extreme'] > 8
    notes = ' '.join(ns['buckling_notes'])
    assert 'Moyer-Kowalsky' in notes
    assert 'Goodnight' in notes
