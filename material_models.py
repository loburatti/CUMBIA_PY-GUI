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
