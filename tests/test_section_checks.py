"""Level 2 - the consistency checks that stand between the inputs and a run.

Two things matter here. Every check must be reachable, or it is decoration:
SCENARIOS names one section per finding code and the suite fails if a code has
no section that produces it. And every finding must be sayable in both
interface languages, since the GUI prints them next to the section.
"""
import pytest

import section_checks as sc

# a consistently detailed section: four layers, four bars per face, every
# declared leg on a bar
GOOD = dict(B=300.0, H=400.0, clb=40.0, dv=9.5, s=120.0, ncx=4, ncy=4,
            mlr=[[52.7, 4, 25.4], [150.9, 2, 25.4],
                 [249.1, 2, 25.4], [347.3, 4, 25.4]])


def run(**overrides):
    params = dict(GOOD)
    params.update(overrides)
    return sc.check_rectangular(**params)


def codes(findings):
    return [f.code for f in findings]


# one section per code, so a check that stops firing is caught
SCENARIOS = {
    'geometry_not_positive': dict(B=0.0),
    'cover_eats_the_core': dict(clb=200.0),
    'spacing_below_bar': dict(s=8.0),
    'no_reinforcement': dict(mlr=[]),
    'empty_layer': dict(mlr=[[52.7, 0, 25.4], [347.3, 4, 25.4]]),
    'single_layer': dict(mlr=[[200.0, 4, 25.4]]),
    'bar_outside_cover': dict(mlr=[[10.0, 4, 25.4], [347.3, 4, 25.4]]),
    'bar_x_outside_cover': dict(
        mlr=[[52.7, 3, 25.4], [347.3, 3, 25.4]],
        bar_x=[[5.0, 150.0, 247.3], None]),
    'bars_overlap': dict(mlr=[[52.7, 12, 25.4], [347.3, 4, 25.4]]),
    'bars_too_close': dict(mlr=[[52.7, 8, 25.4], [347.3, 4, 25.4]]),
    # an elongated section held only at the corners: the gaps eat the whole of
    # Mander's effectiveness factor
    'ke_not_positive': dict(B=1080.0, H=380.0, ncx=2, ncy=2,
                            mlr=[[52.7, 2, 25.4], [327.3, 2, 25.4]]),
    'confinement_poor': dict(B=400.0, H=700.0, ncx=2, ncy=2,
                             mlr=[[52.7, 2, 25.4], [647.3, 2, 25.4]]),
    'legs_without_bars_ncy': dict(ncy=3, mlr=[[52.7, 2, 25.4], [347.3, 3, 25.4]]),
    'legs_without_bars_ncx': dict(ncx=3, mlr=[[52.7, 4, 25.4], [347.3, 4, 25.4]]),
    'spacing_over_six_db': dict(s=200.0),
    'duplicate_depths': dict(mlr=[[52.7, 4, 25.4], [52.7, 2, 25.4],
                                  [347.3, 4, 25.4]]),
    'layer_off_the_left_face': dict(
        mlr=[[52.7, 4, 25.4], [200.0, 2, 25.4], [347.3, 4, 25.4]],
        bar_x=[None, [140.0, 160.0], None]),
    'layer_off_the_right_face': dict(
        mlr=[[52.7, 4, 25.4], [200.0, 2, 25.4], [347.3, 4, 25.4]],
        bar_x=[None, [140.0, 160.0], None]),
    'manual_wi_count': dict(wi=[100.0], wi_auto=False),
    'manual_wi_differs': dict(wi=[10.0] * 12, wi_auto=False),
    'legs_could_be_added_ncy': dict(ncy=2),
    'legs_could_be_added_ncx': dict(ncx=2),
    'steel_ratio': dict(mlr=[[52.7, 2, 12.0], [347.3, 2, 12.0]]),
}


@pytest.mark.parametrize('code', sorted(SCENARIOS))
def test_every_check_is_reachable(code):
    assert code in codes(run(**SCENARIOS[code])), (
        f'{code} did not fire on the section written for it')


def test_no_check_is_left_without_a_scenario():
    """A new finding must come with the section that produces it."""
    assert sorted(SCENARIOS) == sorted(sc.TEMPLATES), (
        'SCENARIOS and TEMPLATES have drifted apart')


def test_a_consistent_section_raises_nothing_serious():
    findings = run()
    assert [f for f in findings if f.severity != sc.ADVICE] == [], (
        f'a consistently detailed section was flagged: {codes(findings)}')


def test_the_shipped_defaults_are_analysable():
    """The section CUMBIA_RECT.py ships with must not be blocked."""
    findings = sc.check_rectangular(
        B=300.0, H=400.0, clb=40.0, dv=9.5, s=120.0, ncx=2, ncy=2,
        mlr=[[52.7, 4, 25.4], [150.9, 2, 25.4], [249.1, 2, 25.4], [347.3, 4, 25.4]])
    assert [f for f in findings if f.severity == sc.ERROR] == []


def test_errors_come_first():
    findings = run(**SCENARIOS['bar_outside_cover'])
    severities = [f.severity for f in findings]
    assert severities == sorted(severities, key=[sc.ERROR, sc.WARNING, sc.ADVICE].index)


def test_broken_geometry_stops_before_the_layer_checks():
    """With B or s meaningless there is nothing to say about the bars, and
    saying it anyway would bury the one finding that matters."""
    assert codes(run(B=-1.0)) == ['geometry_not_positive']


def test_declared_legs_are_never_rewritten():
    """The checks report; they do not correct the input. ncy stays what the
    engineer typed, because it states the transverse steel area."""
    findings = run(**SCENARIOS['legs_without_bars_ncy'])
    leg = next(f for f in findings if f.code == 'legs_without_bars_ncy')
    assert leg.params['declared'] == 3 and leg.params['placed'] == 2
    assert leg.severity == sc.WARNING, 'a detailing mismatch must not block a run'


def test_a_section_whose_ke_vanishes_is_an_error():
    findings = run(**SCENARIOS['ke_not_positive'])
    ke = next(f for f in findings if f.code == 'ke_not_positive')
    assert ke.severity == sc.ERROR
    assert ke.params['share'] >= 1.0


# ------------------------------------------------------------- wording -------
@pytest.mark.parametrize('code', sorted(SCENARIOS))
def test_every_finding_can_be_said_in_both_languages(code):
    import i18n

    finding = next(f for f in run(**SCENARIOS[code]) if f.code == code)
    english = finding.message
    italian = i18n._STRINGS['it'].get(f'check_{code}')
    assert italian, f'check_{code} has no Italian wording'
    assert italian.format(**finding.params), f'check_{code} does not format'
    assert english and english != italian


def test_the_report_block_wraps_and_labels_every_finding():
    lines = sc.report_lines(run(**SCENARIOS['legs_without_bars_ncy']))
    assert lines[0].startswith('Section consistency checks')
    assert any('WARNING' in line for line in lines)
    assert all(len(line) <= 90 for line in lines)


def test_the_report_block_says_so_when_there_is_nothing_to_report():
    lines = sc.report_lines([])
    assert any('No inconsistency' in line for line in lines)


# ------------------------------------------------------------ the engine -----
def test_the_engine_reports_its_own_findings():
    """Script mode must carry the checks too: the GUI is not the only way in."""
    from tests.conftest import run_engine

    ns = run_engine('rectangular', {
        'name': 'checks_probe', 'interaction': 'n',
        'B': 350.0, 'H': 350.0, 'clb': 40.0, 'dv': 8.0, 's': 200.0,
        'ncx': 4, 'ncy': 3, 'auto_generate_MLR': False,
        'custom_MLR': [[48.0, 2, 16.0], [175.0, 2, 16.0], [302.0, 3, 16.0]],
        'wi_input': [0]})

    assert 'legs_without_bars_ncy' in [f.code for f in ns['section_findings']]
    text = '\n'.join(' '.join(str(c) for c in row) for row in ns['report_data'])
    assert 'Section consistency checks' in text
    assert 'ncy = 2 of 3' in text, 'the report does not say how many legs hold a bar'
