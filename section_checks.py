"""Physical consistency of a rectangular section, before it is analysed.

The analysis engine will run on almost anything: it reads numbers, not a
section. These checks look at the inputs as a detailer would and report what
cannot be built, what can be built but is not what the numbers claim, and what
would be worth changing.

Three severities, and the difference between them is deliberate:

  ERROR    the section cannot exist, or the confinement model cannot describe
           it - bars outside the cover, bars on top of each other, a spacing
           smaller than the bar itself, an effectiveness factor that comes out
           at or below zero. The GUI refuses to run these.
  WARNING  the section can be built, but it is not the one the numbers
           describe: legs that hook nothing, a bar spacing too tight to place
           concrete through, detailing outside what the buckling models were
           calibrated on. The engineer decides.
  ADVICE   nothing is wrong; here is what the layout would allow.

Nothing here corrects an input on its own. A check reports, the engineer
decides, and the analysis runs on exactly what was entered.

Each finding carries a code and the numbers behind it, so the same finding can
be phrased in any language; TEMPLATES holds the English wording and is the
source the report prints.
"""
import numpy as np

import section_geometry as sg

ERROR = 'error'
WARNING = 'warning'
ADVICE = 'advice'

# Clear spacing between parallel bars below which concrete cannot reliably be
# placed and bond is compromised: the larger of one bar diameter and 25 mm.
# A detailing rule of thumb, not part of any model here.
MIN_CLEAR_SPACING = 25.0

# Anti-buckling detailing for a plastic hinge region: the tie spacing is kept
# to a few bar diameters so that a bar cannot buckle between ties. Priestley,
# Calvi and Kowalsky (2007) write it as s <= 6 db. It is a detailing rule, not
# a model input; the Moyer-Kowalsky calibration range is a separate check,
# made by the engine where that model runs.
MAX_S_OVER_DB = 6.0

# Above this fraction, Mander's (1 - sum(wi^2)/(6*bc*dc)) has eaten more than
# half of the confinement the transverse steel could provide.
WI_SHARE_POOR = 0.5

TEMPLATES = {
    'geometry_not_positive':
        'Section dimensions must be positive: {what} = {value:g}.',
    'cover_eats_the_core':
        'The cover leaves no core: clb = {clb:g} mm on a {B:g} x {H:g} mm section.',
    'spacing_below_bar':
        'Transverse spacing s = {s:g} mm is not larger than the bar diameter '
        'dv = {dv:g} mm, so the clear spacing between hoops is {sp:g} mm.',
    'no_reinforcement':
        'No longitudinal reinforcement layer was defined.',
    'empty_layer':
        'The layer at depth {depth:g} mm has {n_bars:g} bars.',
    'single_layer':
        'A single reinforcement layer does not define a section perimeter: '
        'there is no bottom face and no side face for the confinement to act '
        'between. At least two layers are needed.',
    'bar_outside_cover':
        'The layer at depth {depth:g} mm with {dbl:g} mm bars sits outside the '
        'cover: its centre must lie between {low:.1f} and {high:.1f} mm.',
    'bar_x_outside_cover':
        'A bar of the layer at depth {depth:g} mm is at x = {x:g} mm, outside '
        'the range {low:.1f} to {high:.1f} mm the cover leaves.',
    'bars_overlap':
        'Bars overlap in the layer at depth {depth:g} mm: {n_bars:g} bars of '
        '{dbl:g} mm leave a clear spacing of {spacing:.1f} mm.',
    'ke_not_positive':
        'The confinement is not defined: sum(wi^2) = {sum_wi2:.0f} mm^2 reaches '
        '{share:.0%} of 6*bc*dc, so Mander\'s effectiveness factor comes out at '
        'or below zero. Add restrained bars, or check the wi entered by hand.',
    'legs_without_bars_ncy':
        'ncy = {declared} legs parallel to H were declared, but the bar layout '
        'can hold {placed}: a crosstie is straight, so it needs a bar at the '
        'same position on the top and on the bottom face. The transverse steel '
        'area still counts {declared} legs; the confinement counts {placed}.',
    'legs_without_bars_ncx':
        'ncx = {declared} legs parallel to B were declared, but the bar layout '
        'can hold {placed}: a leg spanning the width needs a bar on the left '
        'and on the right face at the same depth. The transverse steel area '
        'still counts {declared} legs; the confinement counts {placed}.',
    'bars_too_close':
        'The layer at depth {depth:g} mm leaves {spacing:.1f} mm between bars, '
        'below the {minimum:.1f} mm normally required to place concrete.',
    'spacing_over_six_db':
        'Transverse spacing s = {s:g} mm is {ratio:.1f} times the extreme-fibre '
        'bar diameter {dbl:g} mm, beyond the anti-buckling detailing usually '
        'required in a plastic hinge region (s <= {limit:g} db). The buckling '
        'models still run; the report states how far each one is from its own '
        'calibration.',
    'confinement_poor':
        'The gaps between restrained bars take {share:.0%} of what Mander\'s '
        'effectiveness factor allows. Crossties on the free bars would recover '
        'most of it.',
    'duplicate_depths':
        'Two reinforcement layers share the depth {depth:g} mm. They are '
        'analysed as separate layers; a single layer with the total bar count '
        'is probably what was meant.',
    'layer_off_the_left_face':
        'The layer at depth {depth:g} mm has no bar against the left face, so '
        'the transverse steel cannot hold it there. Its bars are interior '
        'reinforcement as far as the confinement model is concerned.',
    'layer_off_the_right_face':
        'The layer at depth {depth:g} mm has no bar against the right face, so '
        'the transverse steel cannot hold it there. Its bars are interior '
        'reinforcement as far as the confinement model is concerned.',
    'manual_wi_count':
        '{given} clear distances were entered by hand; the bar layout has '
        '{expected}. The analysis uses the values entered.',
    'manual_wi_differs':
        'The clear distances entered by hand give sum(wi^2) = {given:.0f} mm^2 '
        'against {expected:.0f} mm^2 for the layout drawn. The analysis uses '
        'the values entered.',
    'legs_could_be_added_ncy':
        'The top and bottom faces carry {available} bars a leg could hold, '
        'against ncy = {declared} legs declared. Crossties on the free bars '
        'would tighten the confinement without changing the section.',
    'legs_could_be_added_ncx':
        'The side faces carry {available} bars a leg could hold, against '
        'ncx = {declared} legs declared. Crossties on the free bars would '
        'tighten the confinement without changing the section.',
    'steel_ratio':
        'The longitudinal steel ratio is {ratio:.2%} of the gross area, outside '
        'the {low:.0%} to {high:.0%} range columns are usually detailed in.',
}


class Finding:
    """One check result: how serious, which check, and the numbers behind it."""

    __slots__ = ('severity', 'code', 'params')

    def __init__(self, severity, code, **params):
        self.severity = severity
        self.code = code
        self.params = params

    @property
    def message(self):
        return TEMPLATES[self.code].format(**self.params)

    def __repr__(self):
        return f'Finding({self.severity}, {self.code})'


def _layer_bounds(H, clb, dbl):
    return clb + dbl / 2.0, H - clb - dbl / 2.0


def check_rectangular(B, H, clb, dv, s, ncx, ncy, mlr, bar_x=None,
                      wi=None, wi_auto=True, P=None, fpc=None):
    """Every finding for one rectangular section, most serious first.

    `wi` is the list the analysis will actually use - the layout's own values
    in automatic mode, the engineer's in manual mode - so the checks that
    depend on wi describe the run that is about to happen.
    """
    findings = []
    add = findings.append
    tol = 0.5  # mm, so a rounded input is not reported as a geometric error

    # --- the numbers themselves ---------------------------------------------
    for what, value in (('B', B), ('H', H), ('clb', clb), ('dv', dv), ('s', s)):
        if value is None or value <= 0:
            add(Finding(ERROR, 'geometry_not_positive', what=what,
                        value=0 if value is None else value))
    if not findings and (B - 2 * clb <= 0 or H - 2 * clb <= 0):
        add(Finding(ERROR, 'cover_eats_the_core', clb=clb, B=B, H=H))
    if not findings and s <= dv:
        add(Finding(ERROR, 'spacing_below_bar', s=s, dv=dv, sp=s - dv))
    if findings:
        # every check below reads these; there is nothing more to say until
        # they make sense
        return findings

    layers = sg.section_layers(mlr, B, clb, bar_x)
    if not layers:
        return [Finding(ERROR, 'no_reinforcement')]

    layout = sg.restrained_layout(mlr, B, H, clb, ncx, ncy, bar_x)
    if wi is None:
        wi = list(layout['wi'])

    # --- each layer on its own ----------------------------------------------
    seen_depths = {}
    for layer in layers:
        depth, dbl, xs = layer['depth'], layer['dbl'], layer['x']
        if not xs:
            add(Finding(ERROR, 'empty_layer', depth=depth, n_bars=len(xs)))
            continue

        low, high = _layer_bounds(H, clb, dbl)
        if depth < low - tol or depth > high + tol:
            add(Finding(ERROR, 'bar_outside_cover', depth=depth, dbl=dbl,
                        low=low, high=high))

        x_low, x_high = _layer_bounds(B, clb, dbl)
        for x in xs:
            if x < x_low - tol or x > x_high + tol:
                add(Finding(ERROR, 'bar_x_outside_cover', depth=depth, x=x,
                            low=x_low, high=x_high))
                break

        if len(xs) > 1:
            spacing = min(b - a for a, b in zip(xs, xs[1:])) - dbl
            if spacing <= 0:
                add(Finding(ERROR, 'bars_overlap', depth=depth,
                            n_bars=len(xs), dbl=dbl, spacing=spacing))
            elif spacing < max(dbl, MIN_CLEAR_SPACING):
                add(Finding(WARNING, 'bars_too_close', depth=depth,
                            spacing=spacing, minimum=max(dbl, MIN_CLEAR_SPACING)))

        key = round(depth, 3)
        if key in seen_depths:
            add(Finding(WARNING, 'duplicate_depths', depth=depth))
        seen_depths[key] = True

    if layout['single_layer']:
        add(Finding(ERROR, 'single_layer'))

    # --- the confinement the layout produces --------------------------------
    bc, dc = B - 2 * clb + dv, H - 2 * clb + dv
    sum_wi2 = float(np.sum(np.square(np.asarray(wi, dtype=float)))) if len(wi) else 0.0
    share = sum_wi2 / (6 * bc * dc)
    if share >= 1.0:
        add(Finding(ERROR, 'ke_not_positive', sum_wi2=sum_wi2, share=share))
    elif share > WI_SHARE_POOR:
        add(Finding(WARNING, 'confinement_poor', share=share))

    # --- legs against bars ---------------------------------------------------
    for suffix, declared, placed, faces in (
            ('ncy', max(int(ncy), 2), layout['ncy_placed'], ('top', 'bottom')),
            ('ncx', max(int(ncx), 2), layout['ncx_placed'], ('left', 'right'))):
        available = (0 if layout['single_layer'] else
                     min(len(layout['faces'][f]) for f in faces))
        if placed < declared:
            add(Finding(WARNING, f'legs_without_bars_{suffix}',
                        declared=declared, placed=placed))
        elif available > declared:
            add(Finding(ADVICE, f'legs_could_be_added_{suffix}',
                        available=available, declared=declared))

    # --- layers with nothing against a side face -----------------------------
    for name in ('left', 'right'):
        on_face = {round(bar.y, 3) for bar in layout['faces'][name]}
        for layer in (layers if not layout['single_layer'] else []):
            if round(layer['depth'], 3) not in on_face:
                add(Finding(WARNING, f'layer_off_the_{name}_face',
                            depth=layer['depth']))

    # --- detailing the buckling models assume --------------------------------
    dbl_extreme = min(layers[0]['dbl'], layers[-1]['dbl'])
    ratio = s / dbl_extreme
    if ratio > MAX_S_OVER_DB:
        add(Finding(WARNING, 'spacing_over_six_db', s=s, ratio=ratio,
                    dbl=dbl_extreme, limit=MAX_S_OVER_DB))

    # --- wi entered by hand --------------------------------------------------
    if not wi_auto:
        expected = list(layout['wi'])
        if len(wi) != len(expected):
            add(Finding(WARNING, 'manual_wi_count', given=len(wi),
                        expected=len(expected)))
        else:
            given = float(np.sum(np.square(np.asarray(wi, dtype=float))))
            reference = float(np.sum(np.square(np.asarray(expected, dtype=float))))
            if abs(given - reference) > 1e-6 * max(1.0, reference):
                add(Finding(WARNING, 'manual_wi_differs', given=given,
                            expected=reference))

    # --- how much steel ------------------------------------------------------
    area = sum(len(layer['x']) * np.pi * layer['dbl'] ** 2 / 4 for layer in layers)
    gross = B * H
    if gross > 0:
        ratio = area / gross
        if ratio < 0.01 or ratio > 0.04:
            add(Finding(ADVICE, 'steel_ratio', ratio=ratio, low=0.01, high=0.04))

    order = {ERROR: 0, WARNING: 1, ADVICE: 2}
    findings.sort(key=lambda f: order[f.severity])
    return findings


def report_lines(findings):
    """The findings as report text, for the engine's consistency section."""
    lines = ['Section consistency checks:', '']
    if not findings:
        lines.append('  No inconsistency found between the bar layout, the')
        lines.append('  transverse reinforcement and the section geometry.')
        lines.append('')
        return lines

    label = {ERROR: 'ERROR  ', WARNING: 'WARNING', ADVICE: 'ADVICE '}
    import textwrap
    for finding in findings:
        wrapped = textwrap.wrap(finding.message, width=78)
        indent = ' ' * (len('  WARNING  '))
        lines.append(f'  {label[finding.severity]}  {wrapped[0]}')
        for extra in wrapped[1:]:
            lines.append(indent + extra)
        lines.append('')
    return lines
