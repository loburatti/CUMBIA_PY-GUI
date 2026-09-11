"""Level 1 - unit tests for the constitutive models in material_models.py.

These are the only genuinely pure functions in the project, so they carry the
most precise assertions: branch behaviour of each stress-strain law, the
Mander confinement algebra, and the error paths.
"""
import numpy as np
import pytest

import material_models as mm

DELS = 0.0001
STEEL = dict(Es=200000.0, fy=450.0, fsu=600.0, esh=0.008, esu=0.15)
CONC = dict(Ec=5000 * 28.0 ** 0.5, Ast=6080.0, Dh=9.5, clb=40.0, s=120.0,
            fpc=28.0, fy=400.0, eco=0.002, esm=0.12, espall=0.0064)


def _circ(**over):
    kw = dict(CONC, section='circular', D=400.0, d=0, b=0,
              ncx=0, ncy=0, wi=0, dels=DELS, type_reinf='spirals')
    kw.update(over)
    return kw


def _unconf(**over):
    """manderun names the transverse yield stress 'fyh', manderconf 'fy'."""
    kw = _circ(**over)
    kw.pop('type_reinf', None)
    kw['fyh'] = kw.pop('fy')
    return kw


def _rect(**over):
    kw = dict(CONC, section='rectangular', D=0, d=400.0, b=300.0,
              ncx=2, ncy=2, wi=[169.2, 169.2, 269.2, 269.2],
              dels=DELS, type_reinf='hoops')
    kw.update(over)
    return kw


# ---------------------------------------------------------------- steel ----
@pytest.mark.parametrize('model', ['raynor', 'king'])
def test_steel_starts_at_origin_and_is_monotonic(model):
    if model == 'raynor':
        es, fs = mm.Raynor(dels=DELS, C1=3.5, Ey=350.0, **STEEL)
    else:
        es, fs = mm.steelking(dels=DELS, **STEEL)

    assert len(es) == len(fs)
    assert fs[0] == 0.0
    assert np.all(np.diff(fs) >= -1e-9), 'the steel law must not soften'
    assert es[-1] == pytest.approx(STEEL['esu'], abs=DELS)


@pytest.mark.parametrize('model', ['raynor', 'king'])
def test_steel_elastic_branch_follows_youngs_modulus(model):
    if model == 'raynor':
        es, fs = mm.Raynor(dels=DELS, C1=3.5, Ey=350.0, **STEEL)
    else:
        es, fs = mm.steelking(dels=DELS, **STEEL)

    ey = STEEL['fy'] / STEEL['Es']
    i = int(np.argmin(np.abs(es - ey / 2)))
    assert fs[i] == pytest.approx(STEEL['Es'] * es[i], rel=1e-12)


def test_king_has_a_flat_yield_plateau():
    es, fs = mm.steelking(dels=DELS, **STEEL)
    ey = STEEL['fy'] / STEEL['Es']
    on_plateau = (es >= ey) & (es <= STEEL['esh'])
    assert np.allclose(fs[on_plateau], STEEL['fy'])


def test_raynor_plateau_is_inclined_by_Ey():
    """Raynor differs from King exactly here: the plateau has slope Ey."""
    Ey = 350.0
    es, fs = mm.Raynor(dels=DELS, C1=3.5, Ey=Ey, **STEEL)
    ey = STEEL['fy'] / STEEL['Es']
    on_plateau = (es > ey + DELS) & (es < STEEL['esh'] - DELS)
    slope = np.diff(fs[on_plateau]) / np.diff(es[on_plateau])
    assert np.allclose(slope, Ey, rtol=1e-6)


@pytest.mark.parametrize('model', ['raynor', 'king'])
def test_steel_reaches_ultimate_stress(model):
    if model == 'raynor':
        es, fs = mm.Raynor(dels=DELS, C1=3.5, Ey=350.0, **STEEL)
    else:
        es, fs = mm.steelking(dels=DELS, **STEEL)
    assert fs[-1] == pytest.approx(STEEL['fsu'], rel=1e-6)


# ------------------------------------------------------------- concrete ----
def test_confined_concrete_is_stronger_than_unconfined():
    ec_c, fc_c = mm.manderconf(**_circ())
    ec_u, fc_u = mm.manderun(**_unconf())
    assert fc_c.max() > fc_u.max() > 0
    assert ec_c[-1] > ec_u[-1], 'confinement must extend the useful strain'


def test_spirals_confine_better_than_hoops():
    """ke_hoops = ke_spirals**2 < ke_spirals, so f'cc must be lower."""
    _, fc_sp = mm.manderconf(**_circ(type_reinf='spirals'))
    _, fc_hp = mm.manderconf(**_circ(type_reinf='hoops'))
    assert fc_hp.max() < fc_sp.max()


def test_unconfined_peaks_at_fpc_and_vanishes_at_spalling():
    ec, fc = mm.manderun(**_unconf())
    assert fc[0] == 0.0
    assert fc.max() == pytest.approx(CONC['fpc'], rel=1e-9)
    assert ec[int(np.argmax(fc))] == pytest.approx(CONC['eco'], abs=DELS)
    assert fc[-1] == pytest.approx(0.0, abs=1e-9)
    assert ec[-1] == pytest.approx(CONC['espall'], abs=DELS)


def test_lightweight_confined_uses_the_kowalsky_formula():
    """f'cc = (1 + f'l/(2 f'c)) f'c - a linear law, unlike the normal-weight one."""
    kw = _circ()
    _, fc_lw = mm.manderconflw(**kw)
    _, fc_nw = mm.manderconf(**kw)
    assert CONC['fpc'] < fc_lw.max() < fc_nw.max()


def test_wi_increases_reduce_the_confined_strength():
    """Sum(wi^2) enters ke negatively: wider gaps between restrained bars
    mean weaker confinement. This is the property CHANGES.md relies on."""
    tight = mm.manderconf(**_rect(wi=[80.0] * 4))[1].max()
    loose = mm.manderconf(**_rect(wi=[260.0] * 4))[1].max()
    assert tight > loose


def test_rectangular_ke_matches_the_mander_expression():
    """Recompute ke/f'l/f'cc independently and compare with the model output."""
    kw = _rect()
    B, H, clb, dv, s = kw['b'], kw['d'], kw['clb'], kw['Dh'], kw['s']
    bc, dc = B - 2 * clb + dv, H - 2 * clb + dv
    sp = s - dv
    Ash = 0.25 * np.pi * dv ** 2
    ros = (kw['ncx'] * Ash) / (s * dc) + (kw['ncy'] * Ash) / (s * bc)
    rocc = kw['Ast'] / (bc * dc)
    wi = np.array(kw['wi'])
    ke = ((1 - np.sum(wi ** 2) / (6 * bc * dc))
          * (1 - sp / (2 * bc)) * (1 - sp / (2 * dc))) / (1 - rocc)
    fpl = ke * 0.5 * ros * kw['fy']
    expected = (-1.254 + 2.254 * np.sqrt(1 + 7.94 * fpl / kw['fpc'])
                - 2 * fpl / kw['fpc']) * kw['fpc']

    _, fc = mm.manderconf(**kw)
    # fc.max() is the peak of the *sampled* curve, so it sits just below the
    # analytical f'cc unless a sample lands exactly on ecc.
    assert fc.max() <= expected + 1e-9
    assert fc.max() == pytest.approx(expected, rel=1e-3)


# --------------------------------------------------------------- errors ----
def test_unknown_section_raises():
    with pytest.raises(ValueError, match='Section not available'):
        mm.manderconf(**_circ(section='triangular'))


def test_unknown_transverse_reinforcement_raises():
    with pytest.raises(ValueError, match="'spirals' or 'hoops'"):
        mm.manderconf(**_circ(type_reinf='wedges'))


@pytest.mark.parametrize('func', [mm.manderconf, mm.manderconflw])
def test_confinement_models_reject_bad_input_consistently(func):
    with pytest.raises(ValueError):
        func(**_circ(section='hexagonal'))
