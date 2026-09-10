"""Level 3 - end-to-end regression against recorded reference results.

The engines have no unit-testable seams, so the guard against silent numerical
drift is a golden file: a full run is executed and its key outputs are compared
against values recorded when the suite was written.

To re-record after an INTENTIONAL change:

    CUMBIA_REGEN_GOLDEN=1 python -m pytest tests/test_regression_golden.py

then inspect the diff in tests/golden/*.json before committing it. A golden
file changing is not automatically a bug - but it must never change by
accident.
"""
import json
import os

import numpy as np
import pytest

from tests.conftest import GOLDEN_DIR, regen_requested, run_engine

# scalars that summarise the whole analysis
SCALARS = ['Ast', 'Agross', 'Acore', 'LongSteelRatio', 'AxialRatio', 'Mn',
           'ecu', 'ecumander', 'DisplDuct', 'Ieq_val', 'K_factor', 'Bi', 'Lp']
# response curves
ARRAYS = ['curv', 'mom', 'displ', 'Force', 'coverstrain', 'steelstrain']

CONFIGS = {
    'circular_default': ('circular', {'name': 'golden_cir'}),
    'circular_modified_lpr': ('circular', {
        'name': 'golden_cir_lpr', 'hinge_method': 'modified_lpr',
        'interaction': 'n'}),
    'rectangular_default': ('rectangular', {'name': 'golden_rect'}),
    'rectangular_crossties': ('rectangular', {
        'name': 'golden_rect_ct', 'interaction': 'n',
        'ncx': 4, 'ncy': 4, 'wi_input': [0],
        'auto_generate_MLR': False,
        'custom_MLR': [[52.7, 3, 25.4], [102.0, 2, 22.2],
                       [200.0, 2, 19.0], [349.0, 3, 22.2]]}),
}


def _extract(ns):
    out = {'scalars': {}, 'arrays': {}}
    for key in SCALARS:
        if key in ns:
            out['scalars'][key] = float(ns[key])
    for key in ARRAYS:
        if key in ns:
            out['arrays'][key] = np.asarray(ns[key], dtype=float).tolist()
    return out


@pytest.mark.parametrize('config', sorted(CONFIGS))
def test_engine_output_matches_golden(config):
    section, params = CONFIGS[config]
    path = os.path.join(GOLDEN_DIR, f'{config}.json')

    actual = _extract(run_engine(section, params))

    if regen_requested() or not os.path.isfile(path):
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(actual, fh, indent=1)
        if regen_requested():
            pytest.skip(f'golden re-recorded: {os.path.basename(path)}')
        pytest.fail(f'golden file was missing and has been created: {path} '
                    '- inspect it, then re-run')

    with open(path, encoding='utf-8') as fh:
        expected = json.load(fh)

    assert actual['scalars'].keys() == expected['scalars'].keys()
    for key, want in expected['scalars'].items():
        assert actual['scalars'][key] == pytest.approx(want, rel=1e-6), (
            f'{config}: scalar {key} drifted')

    for key, want in expected['arrays'].items():
        got = np.asarray(actual['arrays'][key])
        want = np.asarray(want)
        assert got.shape == want.shape, (
            f'{config}: array {key} changed length '
            f'{want.shape} -> {got.shape}')
        assert np.allclose(got, want, rtol=1e-6, atol=1e-9), (
            f'{config}: array {key} drifted '
            f'(max abs diff {np.max(np.abs(got - want)):.3e})')


@pytest.mark.parametrize('config', sorted(CONFIGS))
def test_response_curves_are_self_consistent(config):
    """Physical sanity that must hold whatever the golden values are."""
    section, params = CONFIGS[config]
    ns = run_engine(section, params)

    curv = np.asarray(ns['curv'], dtype=float)
    mom = np.asarray(ns['mom'], dtype=float)
    displ = np.asarray(ns['displ'], dtype=float)
    cover = np.asarray(ns['coverstrain'], dtype=float)

    assert len(curv) == len(mom) == len(displ)
    assert np.all(np.diff(curv) > 0), 'curvature must increase monotonically'
    assert np.all(np.diff(cover) > 0), 'cover strain must increase monotonically'
    assert np.all(displ >= 0)
    assert mom.max() > 0
    assert ns['Mn'] > 0
    assert 0 < ns['LongSteelRatio'] < 0.10, 'implausible longitudinal steel ratio'
    assert ns['DisplDuct'] > 1.0, 'displacement ductility must exceed 1'
