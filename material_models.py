import numpy as np

def manderconf(Ec, Ast, Dh, clb, s, fpc, fy, eco, esm, espall, section, D, d, b, ncx, ncy, wi, dels, type_reinf):
    sp = s - Dh
    Ash = 0.25 * np.pi * (Dh**2)

    if section.lower() == 'rectangular':
        bc = b - 2*clb + Dh
        dc = d - 2*clb + Dh
        Asx = ncx * Ash
        Asy = ncy * Ash
        Ac = bc * dc
        rocc = Ast / Ac
        rox = Asx / (s * dc)
        roy = Asy / (s * bc)
        ros = rox + roy
        wi_arr = np.array(wi)
        ke = ((1 - np.sum(wi_arr**2) / (6 * bc * dc)) * (1 - sp / (2 * bc)) * (1 - sp / (2 * dc))) / (1 - rocc)
        ro = 0.5 * ros
        fpl = ke * ro * fy

    elif section.lower() == 'circular':
        ds = D - 2*clb + Dh
        ros = 4 * Ash / (ds * s)
        Ac = 0.25 * np.pi * (ds**2)
        rocc = Ast / Ac
        if type_reinf.lower() == 'spirals':
            ke = (1 - sp / (2 * ds)) / (1 - rocc)
        elif type_reinf.lower() == 'hoops':
            ke = ((1 - sp / (2 * ds)) / (1 - rocc))**2
        else:
            raise ValueError("Transverse reinforcement should be 'spirals' or 'hoops'")
        fpl = 0.5 * ke * ros * fy
    else:
        raise ValueError("Section not available")

    # Confined concrete strength formulation
    fpcc = (-1.254 + 2.254 * np.sqrt(1 + 7.94 * fpl / fpc) - 2 * fpl / fpc) * fpc
    ecc = eco * (1 + 5 * (fpcc / fpc - 1))
    Esec = fpcc / ecc
    r = Ec / (Ec - Esec)
    ecu = 1.5 * (0.004 + 1.4 * ros * fy * esm / fpcc)

    ec = np.arange(0, ecu + dels, dels)
    x = (1 / ecc) * ec
    fc = fpcc * x * r / (r - 1 + x**r)

    return ec, fc


def manderun(Ec, Ast, Dh, clb, s, fpc, fyh, eco, esm, espall, section, D, d, b, ncx, ncy, wi, dels):
    ec = np.arange(0, espall + dels, dels)
    Esecu = fpc / eco
    ru = Ec / (Ec - Esecu)
    xu = ec / eco
    fcu = np.zeros_like(ec)

    for i in range(len(ec)):
        if ec[i] < 2 * eco:
            fcu[i] = fpc * xu[i] * ru / (ru - 1 + xu[i]**ru)
        elif 2 * eco <= ec[i] <= espall:
            fcu[i] = fpc * (2 * ru / (ru - 1 + 2**ru)) * (1 - (ec[i] - 2 * eco) / (espall - 2 * eco))
        else:
            fcu[i] = 0

    return ec, fcu


def steelking(Es, fy, fsu, esh, esu, dels):
    r = esu - esh
    m = ((fsu / fy) * ((30 * r + 1)**2) - 60 * r - 1) / (15 * (r**2))
    es = np.arange(0, esu + dels, dels)
    ey = fy / Es
    fs = np.zeros_like(es)

    for i in range(len(es)):
        if es[i] < ey:
            fs[i] = Es * es[i]
        elif ey <= es[i] <= esh:
            fs[i] = fy
        else:
            fs[i] = ((m * (es[i] - esh) + 2) / (60 * (es[i] - esh) + 2) + (es[i] - esh) * (60 - m) / (2 * ((30 * r + 1)**2))) * fy

    return es, fs


def Raynor(Es, fy, fsu, esh, esu, dels, C1, Ey):
    # Using dels/2 prevents floating point overshoot in arange
    es = np.arange(0, esu + dels/2, dels) 
    ey = fy / Es
    fsh = fy + (esh - ey) * Ey
    fs = np.zeros_like(es)

    for i in range(len(es)):
        if es[i] < ey:
            fs[i] = Es * es[i]
        elif ey <= es[i] <= esh:
            fs[i] = fy + (es[i] - ey) * Ey
        else:
            # Clamp the base to 0 to prevent negative scalar power warnings
            base = max(0, esu - es[i])
            fs[i] = fsu - (fsu - fsh) * ((base / (esu - esh))**C1)

    return es, fs

def manderconflw(Ec, Ast, Dh, clb, s, fpc, fy, eco, esm, espall, section, D, d, b, ncx, ncy, wi, dels, type_reinf):
    sp = s - Dh
    Ash = 0.25 * np.pi * (Dh**2)

    if section.lower() == 'rectangular':
        bc = b - 2*clb + Dh
        dc = d - 2*clb + Dh
        Asx = ncx * Ash
        Asy = ncy * Ash
        Ac = bc * dc
        rocc = Ast / Ac
        rox = Asx / (s * dc)
        roy = Asy / (s * bc)
        ros = rox + roy
        wi_arr = np.array(wi)
        ke = ((1 - np.sum(wi_arr**2) / (6 * bc * dc)) * (1 - sp / (2 * bc)) * (1 - sp / (2 * dc))) / (1 - rocc)
        ro = 0.5 * ros
        fpl = ke * ro * fy
    elif section.lower() == 'circular':
        ds = D - 2*clb + Dh
        ros = 4 * Ash / (ds * s)
        Ac = 0.25 * np.pi * (ds**2)
        rocc = Ast / Ac
        if type_reinf.lower() == 'spirals':
            ke = (1 - sp / (2 * ds)) / (1 - rocc)
        elif type_reinf.lower() == 'hoops':
            ke = ((1 - sp / (2 * ds)) / (1 - rocc))**2
        else:
            raise ValueError("Transverse reinforcement should be 'spirals' or 'hoops'")
        fpl = 0.5 * ke * ros * fy
    else:
        raise ValueError("Section not available")

    # Lightweight confined concrete strength formulation (Kowalsky 2000)
    fpcc = (1 + fpl / (2 * fpc)) * fpc
    ecc = eco * (1 + 5 * (fpcc / fpc - 1))
    Esec = fpcc / ecc
    r = Ec / (Ec - Esec)
    ecu = 1.5 * (0.004 + 1.4 * ros * fy * esm / fpcc)

    ec = np.arange(0, ecu + dels, dels)
    x = (1 / ecc) * ec
    fc = fpcc * x * r / (r - 1 + x**r)

    return ec, fc


def manderunlw(Ec, nbl, Dbl, Dh, clb, s, fpc, fyh, eco, esm, espall, section, D, d, b, ncx, ncy, wi, dels):
    ec = np.arange(0, espall + dels, dels)
    Esecu = fpc / eco
    ru = Ec / (Ec - Esecu)
    xu = ec / eco
    ru2 = Ec / (Ec - 1.8 * fpc / eco)
    fcu = np.zeros_like(ec)

    for i in range(len(ec)):
        if ec[i] < eco:
            fcu[i] = fpc * xu[i] * ru / (ru - 1 + xu[i]**ru)
        elif eco <= ec[i] < 1.3 * eco:
            fcu[i] = fpc * xu[i] * ru2 / (ru2 - 1 + xu[i]**ru2)
        elif 1.3 * eco <= ec[i] <= espall:
            fcu[i] = fpc * (1.3 * ru2 / (ru2 - 1 + 1.3**ru2)) * (1 - (ec[i] - 1.3 * eco) / (espall - 1.3 * eco))
        else:
            fcu[i] = 0

    return ec, fcu

def wi_mander(MLR, B, H, clb, ncx, ncy):
    """Clear distances between RESTRAINED longitudinal bars, for Mander's ke.

    Mander's confinement effectiveness factor sums wi**2 over the clear gaps
    between bars that are actually held by a stirrup corner or a crosstie —
    not over every peripheral bar. The restrained bars are counted from the
    number of transverse legs: ncy legs run perpendicular to the top/bottom
    faces and ncx legs perpendicular to the side faces, so each of those faces
    carries that many restrained bars, spread across the net core dimension.

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

    Returns
    -------
    numpy.ndarray
        2*(ncy-1) top/bottom gaps followed by 2*(ncx-1) side gaps [mm].

    Notes
    -----
    The MLR carries no transverse bar coordinates, so the restrained bars are
    assumed uniformly spaced on each face; only their diameters come from the
    layer data. Both the GUI and CUMBIA_RECT.py call this function, so the two
    entry points cannot drift apart.
    """
    arr = np.atleast_2d(np.asarray(MLR, dtype=float))
    if arr.size == 0:
        return np.array([])

    arr = arr[arr[:, 0].argsort()]
    n_restrained_tb = max(int(ncy), 2)
    n_restrained_side = max(int(ncx), 2)

    Bnet = B - 2 * clb
    Hnet = H - 2 * clb
    avg_dbl_tb = (arr[0, 2] + arr[-1, 2]) / 2
    avg_dbl_side = float(np.mean(arr[:, 2]))

    wi_top = np.full(n_restrained_tb - 1,
                     (Bnet - n_restrained_tb * avg_dbl_tb) / (n_restrained_tb - 1))
    wi_side = np.full(n_restrained_side - 1,
                      (Hnet - n_restrained_side * avg_dbl_side) / (n_restrained_side - 1))

    return np.concatenate((wi_top, wi_top, wi_side, wi_side))


# =============================================================================
# Buckling model selection
# =============================================================================
# Shared by both engines so the rule cannot drift between rectangular and
# circular reports. The rule itself is a decision aid supplied by CUMBIA_PY:
# neither the CUMBIA Theory and User Guide nor the source publications rank
# the buckling models against each other, so the report states the rule in
# full and the engineer is free to override it.

APPLICABLE = 'applicable'
EXTRAPOLATED = 'extrapolated'
EXCLUDED = 'excluded'


def buckling_recommendation(results, ultimate_Dduct, shear_Dduct=None):
    """Report lines for the recommended buckling onset and governing mechanism.

    `results` is a list of dicts, one per model that produced an onset, with
    keys 'name', 'Dduct', 'displ' and 'status' (one of the three constants
    above). The recommended onset is the lowest among the models that are not
    EXCLUDED: bar buckling is an onset, so the first mechanism to trigger
    governs, and a model is set aside only where it is demonstrably outside
    its domain - never merely because it extrapolates, since ignoring a lower
    prediction on that ground would be the unconservative direction.

    `shear_Dduct` is the displacement ductility at shear failure, or None when
    no shear failure occurs within the analysed range.
    """
    lines = []
    usable = [r for r in results if r['status'] != EXCLUDED]
    best = min(usable, key=lambda r: r['displ']) if usable else None

    # --- which mechanism reaches its limit first -----------------------------
    candidates = [('ultimate deformation capacity', ultimate_Dduct)]
    if shear_Dduct is not None:
        candidates.append(('shear failure', shear_Dduct))
    if best is not None:
        candidates.append(('bar buckling', best['Dduct']))
    governing, gov_duct = min(candidates, key=lambda c: c[1])
    others = sorted((c for c in candidates if c[0] != governing), key=lambda c: c[1])

    lines.append("Recommended bar buckling onset:")
    lines.append("")

    if not results:
        lines.append("  No buckling model predicted an onset within the analysed range.")
        lines.append("")
    elif best is None:
        lines.append("  Every model that produced an onset is outside its domain of validity.")
        lines.append("  No recommended value; see the applicability notes below.")
        lines.append("")
    else:
        body = [f"mu_D = {best['Dduct']:.2f}      Displacement = {best['displ']:.5f} m",
                best['name']]
        # A boxed value is what a hurried reader takes away, so it has to carry
        # the caveat itself when bar buckling is not what limits the member.
        if governing != 'bar buckling':
            body.append(f"NOT GOVERNING - {governing} occurs first at mu_D {gov_duct:.2f}")
        width = 70
        lines.append("  +" + "-" * width + "+")
        for text in body:
            lines.append("  |  " + text.ljust(width - 2) + "|")
        lines.append("  +" + "-" * width + "+")
        lines.append("")

    if results:
        lines.append(f"  {'Model':<34}{'mu_D':>8}{'Displ [m]':>13}   Status")
        for r in results:
            marker = ' <<<' if best is not None and r is best else ''
            lines.append(f"  {r['name']:<34}{r['Dduct']:>8.2f}{r['displ']:>13.5f}   "
                         f"{r['status']}{marker}")
        lines.append("")
        lines.append("  Status   applicable   - the model has a calibration for this section geometry")
        lines.append("           extrapolated - applied outside its calibration geometry or detailing")
        lines.append("           excluded     - demonstrably outside its domain; see the notes below")
        lines.append("")
        lines.append("  Selection rule: the lowest onset among the models that are not excluded.")
        lines.append("  This ranking is supplied by CUMBIA_PY as a decision aid; the source")
        lines.append("  publications do not rank the models against each other.")
        lines.append("")

    lines.append(f"  Governing mechanism: {governing} at mu_D {gov_duct:.2f}"
                 + ("," if others else "."))
    if others:
        lines.append(f"    ahead of {others[0][0]} at mu_D {others[0][1]:.2f}.")
    if shear_Dduct is None:
        lines.append("  No shear failure occurs within the analysed range.")
    lines.append("")

    return lines
