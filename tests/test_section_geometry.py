"""Level 2 - the restraint geometry the Mander clear distances are read from.

wi is no longer derived from the leg count alone: a transverse leg restrains a
longitudinal bar only where there is one for it to hook. These tests pin the
properties that makes the calculation defensible, above all that it reproduces
the uniform-spacing formula it replaces wherever the declared legs can in fact
be placed, and departs from it only towards LESS confinement.
"""
import numpy as np
import pytest

import section_geometry as sg

# four layers, four bars top and bottom, evenly spaced: every leg up to four
# per direction finds a bar to hook
UNIFORM = [[52.7, 4, 25.4], [150.9, 2, 25.4], [249.1, 2, 25.4], [347.3, 4, 25.4]]
B, H, CLB = 300.0, 400.0, 40.0


def legacy_uniform_wi(MLR, B, H, clb, ncx, ncy):
    """The calculation this module replaces: bars assumed evenly spread over
    the net core, as many restrained per face as there are legs.

    Kept here, in the tests only, as the reference the new geometry must
    reproduce on a layout where both descriptions are true at once.
    """
    arr = np.atleast_2d(np.asarray(MLR, dtype=float))
    arr = arr[arr[:, 0].argsort()]
    n_tb, n_side = max(int(ncy), 2), max(int(ncx), 2)
    avg_tb = (arr[0, 2] + arr[-1, 2]) / 2
    avg_side = float(np.mean(arr[:, 2]))
    top = np.full(n_tb - 1, (B - 2 * clb - n_tb * avg_tb) / (n_tb - 1))
    side = np.full(n_side - 1, (H - 2 * clb - n_side * avg_side) / (n_side - 1))
    return np.concatenate((top, top, side, side))


@pytest.mark.parametrize('ncx,ncy', [(2, 2), (2, 4), (4, 2), (4, 4)])
def test_matches_the_uniform_formula_when_every_leg_can_be_placed(ncx, ncy):
    """The headline compatibility property.

    On a uniform layout whose faces carry at least as many bars as there are
    legs, the two descriptions of the section agree, so no result computed on
    a consistently detailed section moves.
    """
    new = sg.wi_mander(UNIFORM, B, H, CLB, ncx, ncy)
    old = legacy_uniform_wi(UNIFORM, B, H, CLB, ncx, ncy)
    assert sorted(np.round(new, 9)) == pytest.approx(sorted(np.round(old, 9)))


def test_a_leg_with_no_bar_to_hook_does_not_restrain_one():
    """Three legs across a face that carries two bars restrain two bars.

    The mismatch is reported through ncy_placed rather than by quietly
    rewriting ncy, which stays the engineer's statement about steel area.
    """
    mlr = [[48.0, 2, 16.0], [302.0, 3, 16.0]]
    layout = sg.restrained_layout(mlr, 350.0, 350.0, 40.0, 2, 3)

    assert layout['ncy_placed'] == 2, 'a third leg was placed on a two-bar face'
    assert layout['tie_x'] == []
    # the bottom face has a middle bar, but no partner on the top face for a
    # straight crosstie, so the gap runs past it
    assert [round(g, 1) for g in layout['wi']][:2] == [238.0, 238.0]


def test_adding_the_missing_bar_lets_the_leg_be_placed():
    """The advice the checks give - add the bar - must actually pay off."""
    without = sg.restrained_layout([[48.0, 2, 16.0], [302.0, 3, 16.0]],
                                   350.0, 350.0, 40.0, 2, 3)
    with_bar = sg.restrained_layout([[48.0, 3, 16.0], [302.0, 3, 16.0]],
                                    350.0, 350.0, 40.0, 2, 3)

    assert with_bar['ncy_placed'] == 3
    assert len(with_bar['tie_x']) == 1
    assert np.sum(with_bar['wi'] ** 2) < np.sum(without['wi'] ** 2)


def test_an_unplaceable_leg_never_improves_confinement():
    """Declaring legs the layout cannot host must not lower sum(wi**2).

    This is the direction that matters: the calculation it replaces assumed
    the bars were there and so overstated the confinement.
    """
    mlr = [[48.0, 2, 16.0], [302.0, 2, 16.0]]
    hoop = sg.wi_mander(mlr, 350.0, 350.0, 40.0, 2, 2)
    claimed = sg.wi_mander(mlr, 350.0, 350.0, 40.0, 4, 4)
    assert np.sum(claimed ** 2) == pytest.approx(np.sum(hoop ** 2))
    assert np.sum(claimed ** 2) > np.sum(
        legacy_uniform_wi(mlr, 350.0, 350.0, 40.0, 4, 4) ** 2)


@pytest.mark.parametrize('ncx,ncy', [(2, 2), (3, 3), (4, 4), (5, 5)])
def test_every_corner_bar_is_restrained(ncx, ncy):
    """The perimeter hoop holds the four corners whatever the leg count."""
    layout = sg.restrained_layout(UNIFORM, B, H, CLB, ncx, ncy)
    for name, face in layout['faces'].items():
        assert face[0].restrained and face[-1].restrained, f'{name} corner is free'


def test_more_legs_never_widens_the_gaps():
    """Monotonicity: a crosstie splits a gap, and a**2 + b**2 < (a+b)**2."""
    previous = None
    for n in (2, 3, 4):
        total = float(np.sum(sg.wi_mander(UNIFORM, B, H, CLB, n, n) ** 2))
        if previous is not None:
            assert total < previous
        previous = total


@pytest.mark.parametrize('ncx,ncy', [(2, 2), (3, 4), (4, 4), (6, 6)])
def test_gaps_are_positive_and_fit_in_the_core(ncx, ncy):
    wi = sg.wi_mander(UNIFORM, B, H, CLB, ncx, ncy)
    assert all(w > 0 for w in wi)
    assert max(wi) <= max(B - 2 * CLB, H - 2 * CLB) + 1e-9


# ------------------------------------------------------------ custom bars ----
def test_explicit_positions_drive_the_gaps():
    """Bars pushed to one side give one short gap and one long one."""
    mlr = [[52.7, 3, 25.4], [347.3, 3, 25.4]]
    bar_x = [[52.7, 100.0, 247.3], [52.7, 100.0, 247.3]]
    layout = sg.restrained_layout(mlr, B, H, CLB, 2, 3, bar_x)

    assert layout['ncy_placed'] == 3
    assert layout['tie_x'] == pytest.approx([100.0])
    top = [round(g[2], 1) for g in layout['gaps']['top']]
    assert top == [21.9, 121.9], f'gaps do not follow the typed positions: {top}'


def test_a_crosstie_is_placed_on_a_bar_not_at_a_fraction_of_the_width():
    """What the preview draws as a leg has to be where a bar actually is."""
    mlr = [[52.7, 3, 25.4], [347.3, 3, 25.4]]
    bar_x = [[52.7, 90.0, 247.3], [52.7, 90.0, 247.3]]
    layout = sg.restrained_layout(mlr, B, H, CLB, 2, 3, bar_x)
    assert layout['tie_x'] == pytest.approx([90.0])


def test_positions_that_do_not_match_the_bar_count_are_ignored():
    """A half-typed entry must fall back to the uniform spacing, not analyse
    a section nobody asked for."""
    mlr = [[52.7, 3, 25.4], [347.3, 3, 25.4]]
    partial = sg.restrained_layout(mlr, B, H, CLB, 2, 3, [[52.7, 100.0], None])
    uniform = sg.restrained_layout(mlr, B, H, CLB, 2, 3)
    assert partial['wi'] == pytest.approx(uniform['wi'])


def test_positions_follow_their_layer_when_the_rows_are_out_of_order():
    """MLR rows are sorted internally; the positions must travel with them."""
    rows = [[347.3, 3, 25.4], [52.7, 3, 25.4]]
    bar_x = [[52.7, 200.0, 247.3], [52.7, 100.0, 247.3]]
    layout = sg.restrained_layout(rows, B, H, CLB, 2, 2, bar_x)
    assert [b.x for b in layout['faces']['top']] == pytest.approx([52.7, 100.0, 247.3])
    assert [b.x for b in layout['faces']['bottom']] == pytest.approx([52.7, 200.0, 247.3])


def test_a_bar_pushed_off_the_face_is_not_a_face_bar():
    """A side leg needs a bar at the face; one moved well inside is interior
    reinforcement and cannot be hooked by a crosstie spanning the width."""
    mlr = [[52.7, 4, 25.4], [200.0, 2, 25.4], [347.3, 4, 25.4]]
    inside = [None, [140.0, 160.0], None]
    layout = sg.restrained_layout(mlr, B, H, CLB, 3, 2, inside)
    assert layout['ncx_placed'] == 2, 'a leg hooked a bar that is not on the face'
    assert [round(b.y, 1) for b in layout['faces']['left']] == [52.7, 347.3]


# ------------------------------------------------------------- degenerate ----
def test_a_single_layer_has_no_side_face():
    """One layer of bars is not a perimeter: its gaps are counted once and no
    side gap exists. The consistency checks report it; the value stays defined
    so the preview can still draw what was typed."""
    layout = sg.restrained_layout([[200.0, 4, 25.4]], B, H, CLB, 2, 2)
    assert layout['single_layer']
    assert layout['faces']['left'] == [] and layout['faces']['bottom'] == []
    assert len(layout['wi']) == 1


def test_an_empty_matrix_produces_no_gaps():
    layout = sg.restrained_layout([], B, H, CLB, 2, 2)
    assert list(layout['wi']) == []
    assert layout['ncx_placed'] == 0


def test_legs_below_two_are_read_as_a_closed_hoop():
    for bad in (0, 1, -3):
        wi = sg.wi_mander(UNIFORM, B, H, CLB, bad, bad)
        assert wi == pytest.approx(sg.wi_mander(UNIFORM, B, H, CLB, 2, 2))
