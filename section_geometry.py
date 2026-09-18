"""Bar-by-bar geometry of a rectangular section, and the Mander clear distances.

Mander's confinement effectiveness factor sums wi**2 over the clear distances
between longitudinal bars that are *actually held* by a stirrup corner or a
crosstie. Which bars those are is a property of the bar layout and of where a
transverse leg can physically hook: a crosstie is a straight bar, so it can
only be placed where there is a longitudinal bar on both of the faces it
spans. The leg count on its own does not say that - a section detailed with
three legs in one direction but only two bars on the face they cross cannot
restrain three bars, and assuming it does overstates the confinement.

This module builds the geometry once, from the reinforcement layer matrix,
and derives wi from it. The GUI preview, the wi that enters the confinement
model and the consistency checks all read the same layout, so the picture on
screen and the number in the report describe the same section.

Conventions, unchanged from the rest of the project:

  * MLR rows are [depth from the top face, number of bars, bar diameter];
  * ncx counts the transverse legs parallel to B. Each one spans the width and
    restrains a bar on the left and on the right face;
  * ncy counts the legs parallel to H. Each one spans the height and restrains
    a bar on the top and on the bottom face;
  * the two outermost legs of each direction are the sides of the perimeter
    hoop, which always restrains the four corner bars, so a value below 2 is
    read as 2.

Only the restraint geometry lives here. The transverse steel area, and with it
rho_x, rho_y and every buckling model, stays a function of ncx and ncy as the
engineer entered them: a leg that cannot hook a longitudinal bar still
contributes its area. The two are reported separately rather than one being
silently corrected from the other.
"""
import numpy as np

# How far from the nominal cover line a bar may sit and still count as a bar
# *on* that face, as a multiple of its own diameter. It exists for custom bar
# positions: a layer whose outer bar is pushed well inside the face has no bar
# for a leg to hook there, and must not be counted as if it had one.
FACE_TOL_DB = 1.0


class Bar:
    """One longitudinal bar: position, diameter and whether a leg holds it."""

    __slots__ = ('x', 'y', 'dbl', 'restrained')

    def __init__(self, x, y, dbl, restrained=False):
        self.x = float(x)
        self.y = float(y)
        self.dbl = float(dbl)
        self.restrained = bool(restrained)

    def __repr__(self):
        held = 'held' if self.restrained else 'free'
        return f'Bar(x={self.x:.1f}, y={self.y:.1f}, d={self.dbl:.1f}, {held})'


def layer_x_positions(n_bars, dbl, B, clb, explicit=None):
    """The x coordinates of one layer's bars.

    `explicit` overrides the uniform distribution, which is what a custom
    layout uses; it is ignored unless it carries exactly `n_bars` values, so a
    half-typed entry in the GUI falls back to the uniform spacing rather than
    drawing a section that was never asked for.
    """
    n = int(n_bars)
    if n <= 0:
        return []
    if explicit is not None:
        values = [float(v) for v in explicit]
        if len(values) == n:
            return sorted(values)
    if n == 1:
        return [B / 2.0]
    edge = clb + dbl / 2.0
    return [float(v) for v in np.linspace(edge, B - edge, n)]


def section_layers(MLR, B, clb, bar_x=None):
    """The reinforcement layers, ordered top down, with bar coordinates.

    `bar_x` is optional and parallel to the MLR rows *as given*: entry i holds
    the x coordinates of row i, or None/empty for the uniform spacing. It is
    reordered together with the rows.
    """
    arr = np.atleast_2d(np.asarray(MLR, dtype=float))
    if arr.size == 0:
        return []

    order = list(np.argsort(arr[:, 0], kind='stable'))
    layers = []
    for i in order:
        depth = float(arr[i, 0])
        n_bars = int(round(float(arr[i, 1])))
        dbl = float(arr[i, 2])
        explicit = None
        if bar_x is not None and i < len(bar_x) and bar_x[i]:
            explicit = bar_x[i]
        xs = layer_x_positions(n_bars, dbl, B, clb, explicit)
        layers.append({'depth': depth, 'dbl': dbl, 'x': xs})
    return layers


def _pick_uniform(candidates, lo, hi, n_wanted, key):
    """`n_wanted` candidates spread as evenly as possible between lo and hi.

    Used to place the intermediate legs on the bars that are there. A detailer
    distributes crossties as uniformly as the bar layout allows, so each leg
    goes to the free bar nearest its ideal position, taken in order. Returns
    the chosen candidates sorted by position; fewer than asked for when the
    layout cannot host them all.
    """
    pool = list(candidates)
    chosen = []
    if n_wanted <= 0 or not pool:
        return chosen
    for k in range(1, n_wanted + 1):
        if not pool:
            break
        target = lo + (hi - lo) * k / (n_wanted + 1)
        best = min(pool, key=lambda c: abs(key(c) - target))
        pool.remove(best)
        chosen.append(best)
    return sorted(chosen, key=key)


def clear_gaps(bars, axis):
    """Clear distances between consecutive bars of a face.

    A bar the transverse steel does not hold is simply not in `bars`: the gap
    runs past it, from one restrained bar to the next, which is what arching
    between laterally supported bars means in Mander's model.
    """
    ordered = sorted(bars, key=lambda b: getattr(b, axis))
    return [(a, b, getattr(b, axis) - getattr(a, axis) - (a.dbl + b.dbl) / 2.0)
            for a, b in zip(ordered, ordered[1:])]


def restrained_layout(MLR, B, H, clb, ncx, ncy, bar_x=None):
    """Where the bars are, which ones the transverse steel holds, and the gaps.

    Returns a dict with

      faces        'top', 'bottom', 'left', 'right' -> the Bar objects on that
                   face, in order, each flagged restrained or not;
      gaps         the same keys -> [(bar, bar, clear distance)] between
                   consecutive *restrained* bars;
      wi           every clear distance, as one array, in face order;
      tie_x        x of the intermediate legs parallel to H that could be
                   placed, tie_y the depths of those parallel to B;
      ncy_placed   legs that actually hold a bar, 2 + len(tie_x), and
      ncx_placed   2 + len(tie_y), to compare against what was requested;
      single_layer True when the MLR defines no perimeter (see below).

    A single reinforcement layer is a degenerate case: top and bottom face
    coincide and the section has no side face, so its gaps are counted once
    and no side gap exists. The consistency checks report it as an error - it
    is not a section a confinement model can describe - but the value returned
    here stays defined so the preview can still draw what was typed.
    """
    layers = section_layers(MLR, B, clb, bar_x)
    empty = {'faces': {k: [] for k in ('top', 'bottom', 'left', 'right')},
             'gaps': {k: [] for k in ('top', 'bottom', 'left', 'right')},
             'wi': np.array([]), 'tie_x': [], 'tie_y': [],
             'ncx_placed': 0, 'ncy_placed': 0, 'single_layer': False}
    if not layers:
        return empty

    n_legs_tb = max(int(ncy), 2)      # legs parallel to H -> top/bottom faces
    n_legs_side = max(int(ncx), 2)    # legs parallel to B -> side faces
    single_layer = len(layers) == 1

    # --- the bars on each face ---------------------------------------------
    top_layer, bottom_layer = layers[0], layers[-1]
    top = [Bar(x, top_layer['depth'], top_layer['dbl']) for x in top_layer['x']]
    bottom = ([] if single_layer else
              [Bar(x, bottom_layer['depth'], bottom_layer['dbl'])
               for x in bottom_layer['x']])

    left, right = [], []
    for layer in layers:
        if not layer['x']:
            continue
        tol = clb + layer['dbl'] / 2.0 + FACE_TOL_DB * layer['dbl']
        if layer['x'][0] <= tol:
            left.append(Bar(layer['x'][0], layer['depth'], layer['dbl']))
        if layer['x'][-1] >= B - tol:
            right.append(Bar(layer['x'][-1], layer['depth'], layer['dbl']))
    if single_layer:
        left, right = [], []

    # --- the perimeter hoop holds the corners ------------------------------
    for face in (top, bottom, left, right):
        if face:
            face[0].restrained = True
            face[-1].restrained = True

    # --- intermediate legs parallel to H: they need a bar on both faces -----
    tie_x = []
    if top and bottom and n_legs_tb > 2:
        pairs = []
        free_bottom = list(bottom[1:-1])
        for bar_t in top[1:-1]:
            for bar_b in free_bottom:
                if abs(bar_t.x - bar_b.x) <= (bar_t.dbl + bar_b.dbl) / 2.0:
                    pairs.append((bar_t, bar_b))
                    free_bottom.remove(bar_b)
                    break
        chosen = _pick_uniform(pairs, top[0].x, top[-1].x, n_legs_tb - 2,
                               key=lambda p: (p[0].x + p[1].x) / 2.0)
        for bar_t, bar_b in chosen:
            bar_t.restrained = True
            bar_b.restrained = True
            tie_x.append((bar_t.x + bar_b.x) / 2.0)

    # --- intermediate legs parallel to B: they need a layer reaching both ---
    tie_y = []
    if left and right and n_legs_side > 2:
        by_depth = {}
        for bar in left[1:-1]:
            by_depth.setdefault(round(bar.y, 6), [None, None])[0] = bar
        for bar in right[1:-1]:
            by_depth.setdefault(round(bar.y, 6), [None, None])[1] = bar
        pairs = [tuple(v) for v in by_depth.values() if v[0] is not None and v[1] is not None]
        chosen = _pick_uniform(pairs, left[0].y, left[-1].y, n_legs_side - 2,
                               key=lambda p: p[0].y)
        for bar_l, bar_r in chosen:
            bar_l.restrained = True
            bar_r.restrained = True
            tie_y.append(bar_l.y)

    # --- the clear distances ------------------------------------------------
    faces = {'top': top, 'bottom': bottom, 'left': left, 'right': right}
    axis = {'top': 'x', 'bottom': 'x', 'left': 'y', 'right': 'y'}
    gaps, wi = {}, []
    for name, bars in faces.items():
        held = [b for b in bars if b.restrained]
        gaps[name] = clear_gaps(held, axis[name]) if len(held) > 1 else []
        wi.extend(g[2] for g in gaps[name])

    return {'faces': faces, 'gaps': gaps, 'wi': np.array(wi, dtype=float),
            'tie_x': sorted(tie_x), 'tie_y': sorted(tie_y),
            'ncy_placed': 2 + len(tie_x), 'ncx_placed': 2 + len(tie_y),
            'single_layer': single_layer}


def wi_mander(MLR, B, H, clb, ncx, ncy, bar_x=None):
    """Clear distances between RESTRAINED longitudinal bars, for Mander's ke.

    Parameters
    ----------
    MLR : array-like, shape (n_layers, 3)
        Longitudinal reinforcement layers, [depth from top, n bars, diameter].
        Sorted by depth internally, so callers need not pre-sort.
    B, H, clb : float
        Section width, height and clear cover to the longitudinal bars [mm].
    ncx, ncy : int
        Transverse legs parallel to B and to H. Values below 2 are treated as
        2: a closed perimeter hoop always restrains the corner bars.
    bar_x : list of lists, optional
        Explicit x coordinates per MLR row for a custom layout; the uniform
        distribution is used where it is absent.

    Returns
    -------
    numpy.ndarray
        The clear distances of the top, bottom, left and right face, in that
        order. Only their sum of squares enters ke, so the order is a
        convention; the count is not, and it follows the bars that are held,
        which may be fewer than the declared legs.

    Notes
    -----
    Where the declared legs *can* all be placed - the usual case of uniformly
    spaced bars with matching counts on opposite faces - this reproduces the
    uniform-spacing calculation it replaces exactly. It departs from it only
    where the layout cannot host the legs that were declared, or where the
    bars are not uniformly spaced, and always towards a larger sum of squares,
    that is towards less confinement.
    """
    return restrained_layout(MLR, B, H, clb, ncx, ncy, bar_x)['wi']
