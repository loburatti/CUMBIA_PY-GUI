"""
CUMBIA_PY 0.3 - Advanced GUI Launcher
CustomTkinter interface with interactive section editor.
"""
import os
import sys
import json
import math
import tempfile
import shutil
import webbrowser
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import numpy as np

# PyInstaller: analysis scripts import these at runtime via exec(),
# so we import them here to ensure they are bundled.
import pandas                                    # noqa: F401
import openpyxl                                  # noqa: F401
import matplotlib                                # noqa: F401
import matplotlib.pyplot                         # noqa: F401
import matplotlib.backends.backend_pdf           # noqa: F401
import matplotlib.backends.backend_agg           # noqa: F401
import matplotlib.patches                        # noqa: F401


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


# ==========================================================================
# Tooltip descriptions for every parameter
# ==========================================================================
TIPS = {
    'name':          'Prefisso per i file di output (Excel, PDF, PNG)',
    'interaction':   'Esegui analisi di interazione carico assiale - momento (diagramma M-P)',
    'hinge_method':  'pck = Priestley et al. (2007)\nmodified_lpr = Goodnight et al. (2016)',
    'D':             'Diametro esterno della sezione circolare',
    'H':             'Altezza della sezione (perpendicolare all\'asse di flessione)',
    'B':             'Larghezza della sezione',
    'clb':           'Copriferro netto: distanza dal bordo esterno\nalla superficie delle barre longitudinali',
    'L':             'Lunghezza libera del membro strutturale',
    'bending':       'single = mensola (cantilever)\ndouble = doppio incastro (fixed-fixed)',
    'ductilitymode': 'Modalita di carico per il fattore di degrado\na taglio UCSD (uniaxial o biaxial)',
    'p_delta':       'Includi effetti P-Delta approssimati\n(sottrazione momento ribaltamento geometrico)',
    'confined':      'Modello costitutivo calcestruzzo confinato:\nmc = Mander confinato, mclw = Mander lightweight',
    'unconfined':    'Modello costitutivo calcestruzzo non confinato:\nmu = Mander non confinato, mulw = lightweight',
    'rebar':         'Modello costitutivo acciaio:\nra = Raynor, ks = King',
    'nbl':           'Numero totale di barre longitudinali\ndistribuite uniformemente sulla sezione circolare',
    'Dbl':           'Diametro delle barre longitudinali (circolare)',
    'Dh':            'Diametro dell\'armatura trasversale (spirali/cerchi)',
    'type_reinf':    'Tipo di armatura trasversale:\nspirals = spirale continua\nhoops = cerchi chiusi',
    's':             'Passo (interasse) dell\'armatura trasversale',
    'P_kN':          'Carico assiale applicato\n+ = compressione, - = trazione',
    'fpc':           'Resistenza a compressione cilindrica del calcestruzzo (f\'c)',
    'Ec':            'Modulo elastico del calcestruzzo\n0 = calcolo automatico: 5000 * sqrt(f\'c)',
    'eco':           'Deformazione al picco del calcestruzzo non confinato\n(0.002 normale, 0.004 lightweight)',
    'esm':           'Deformazione massima dell\'acciaio trasversale\n(tipicamente 0.10 - 0.15)',
    'espall':        'Deformazione massima del calcestruzzo non confinato\n(deformazione di spalling)',
    'fy':            'Tensione di snervamento dell\'acciaio longitudinale',
    'fyh':           'Tensione di snervamento dell\'acciaio trasversale',
    'Es':            'Modulo elastico dell\'acciaio',
    'fsu':           'Tensione ultima dell\'acciaio longitudinale',
    'esh':           'Deformazione all\'inizio dell\'incrudimento',
    'esu':           'Deformazione ultima dell\'acciaio',
    'Ey':            'Pendenza del plateau di snervamento (modello Raynor)',
    'C1':            'Parametro curvatura incrudimento (modello Raynor)',
    'csid':          'Limite deformazione calcestruzzo per\nil diagramma di interazione (yield surface)',
    'ssid':          'Limite deformazione acciaio per\nil diagramma di interazione (yield surface)',
    'ecser':         'Limite deformazione calcestruzzo a compressione\nper lo stato limite di servizio',
    'esser':         'Limite deformazione acciaio a trazione\nper lo stato limite di servizio',
    'ecdam':         'Limite deformazione calcestruzzo per damage control\ntwth = 2/3 della deformazione ultima, oppure valore numerico',
    'esdam':         'Limite deformazione acciaio a trazione\nper damage control',
    'temp':          'Temperatura del campione [°C]\n(influenza la resistenza a trazione se < 0)',
    'kLsp':          'Costante di strain penetration\n(0.022 a temperatura ambiente, 0.011 a -40°C)',
    'itermax':       'Numero massimo di iterazioni per la ricerca\ndell\'asse neutro',
    'ncl':           'Numero di strati di discretizzazione del calcestruzzo',
    'tolerance':     'Moltiplicatore di tolleranza per l\'equilibrio delle forze\n(tol = tolerance * Area * f\'c)',
    'dels':          'Incremento di deformazione (delta strain)\nper l\'analisi sezionale',
    'auto_generate_MLR': 'Attivo: layout periferico uniforme auto-generato\nDisattivo: matrice MLR personalizzata',
    'n_top_bot':     'Numero di barre sulla faccia superiore\n(e uguale sulla inferiore)',
    'n_side':        'Numero di barre su ciascun lato\n(esclusi gli angoli)',
    'Dbl_auto':      'Diametro di tutte le barre longitudinali\n(layout automatico)',
    'dv':            'Diametro dell\'armatura trasversale (staffe)',
    'ncx':           'Numero di bracci in direzione X\n(paralleli a B, confinamento)',
    'ncy':           'Numero di bracci in direzione Y\n(paralleli a H, resistenza a taglio)',
    'wi_input':      'Distanze libere tra barre longitudinali periferiche.\n[0] = calcolo automatico',
}

# ==========================================================================
# Parameter schemas:  (key, label, default, widget, options, unit)
# ==========================================================================

CIR_PARAMS = [
    ('section', 'Controlli Generali'),
    ('name',          'Nome progetto',                'CUMBIACIR_example', 'entry', None, ''),
    ('interaction',   'Interazione M-P',              'y',    'combo', ['y', 'n'], ''),
    ('hinge_method',  'Metodo cerniera',              'pck',  'combo', ['pck', 'modified_lpr'], ''),
    ('section', 'Geometria Sezione'),
    ('D',   'Diametro D',       1000.0, 'entry', None, 'mm'),
    ('clb', 'Copriferro clb',   50.0,   'entry', None, 'mm'),
    ('section', 'Proprieta Membro'),
    ('L',             'Lunghezza L',        3000.0,    'entry', None, 'mm'),
    ('bending',       'Flessione',          'single',  'combo', ['single', 'double'], ''),
    ('ductilitymode', 'Duttilita',          'biaxial', 'combo', ['uniaxial', 'biaxial'], ''),
    ('p_delta',       'P-Delta',            'y',       'combo', ['y', 'n'], ''),
    ('section', 'Modelli Materiali'),
    ('confined',   'Cls confinato',      'mc', 'combo', ['mc', 'mu', 'mclw'], ''),
    ('unconfined', 'Cls non confinato',  'mu', 'combo', ['mc', 'mu', 'mclw', 'mulw'], ''),
    ('rebar',      'Acciaio',            'ra', 'combo', ['ra', 'ks'], ''),
    ('section', 'Armatura'),
    ('nbl',        'N. barre long.',            22,    'entry', None, ''),
    ('Dbl',        'Diametro barre long.',      25.0,  'entry', None, 'mm'),
    ('Dh',         'Diametro spirali/cerchi',   9.0,   'entry', None, 'mm'),
    ('type_reinf', 'Tipo arm. trasversale',     'spirals', 'combo', ['spirals', 'hoops'], ''),
    ('s',          'Passo arm. trasversale',    120.0,  'entry', None, 'mm'),
    ('section', 'Carichi'),
    ('P_kN', 'Carico assiale P', 2000.0, 'entry', None, 'kN'),
    ('section', 'Calcestruzzo'),
    ('fpc',    "f'c",                     35.0,    'entry', None, 'MPa'),
    ('Ec',     "Ec (0=auto)",             0,       'entry', None, 'MPa'),
    ('eco',    'eco',                     0.002,   'entry', None, ''),
    ('esm',    'esm',                     0.11,    'entry', None, ''),
    ('espall', 'espall',                  0.0064,  'entry', None, ''),
    ('section', 'Acciaio'),
    ('fy',  'fy',         460.0,    'entry', None, 'MPa'),
    ('fyh', 'fyh',        400.0,    'entry', None, 'MPa'),
    ('Es',  'Es',         200000.0, 'entry', None, 'MPa'),
    ('fsu', 'fsu',        620.0,    'entry', None, 'MPa'),
    ('esh', 'esh',        0.008,    'entry', None, ''),
    ('esu', 'esu',        0.12,     'entry', None, ''),
    ('Ey',  'Ey (Raynor)',350.0,    'entry', None, 'MPa'),
    ('C1',  'C1 (Raynor)',3.5,      'entry', None, ''),
    ('section', 'Limiti di Deformazione'),
    ('csid',  'csid',   0.004,  'entry', None, ''),
    ('ssid',  'ssid',   0.015,  'entry', None, ''),
    ('ecser', 'ecser',  0.004,  'entry', None, ''),
    ('esser', 'esser',  0.015,  'entry', None, ''),
    ('ecdam', 'ecdam',  'twth', 'entry', None, ''),
    ('esdam', 'esdam',  0.060,  'entry', None, ''),
    ('section', 'Parametri Ambientali'),
    ('temp', 'Temperatura',  40.0,   'entry', None, 'C'),
    ('kLsp', 'kLsp',         0.022,  'entry', None, ''),
    ('section', 'Parametri Numerici'),
    ('itermax',   'itermax',    1000,    'entry', None, ''),
    ('ncl',       'ncl',        40,      'entry', None, ''),
    ('tolerance', 'tolerance',  0.001,   'entry', None, ''),
    ('dels',      'dels',       0.0001,  'entry', None, ''),
]

RECT_PARAMS = [
    ('section', 'Controlli Generali'),
    ('name',          'Nome progetto',                'CUMBIARECT_example', 'entry', None, ''),
    ('interaction',   'Interazione M-P',              'y',    'combo', ['y', 'n'], ''),
    ('hinge_method',  'Metodo cerniera',              'pck',  'combo', ['pck', 'modified_lpr'], ''),
    ('section', 'Geometria Sezione'),
    ('H',   'Altezza H',        400.0, 'entry', None, 'mm'),
    ('B',   'Larghezza B',      300.0, 'entry', None, 'mm'),
    ('clb', 'Copriferro clb',   40.0,  'entry', None, 'mm'),
    ('section', 'Proprieta Membro'),
    ('L',             'Lunghezza L',        1200.0,    'entry', None, 'mm'),
    ('bending',       'Flessione',          'single',  'combo', ['single', 'double'], ''),
    ('ductilitymode', 'Duttilita',          'biaxial', 'combo', ['uniaxial', 'biaxial'], ''),
    ('p_delta',       'P-Delta',            'n',       'combo', ['y', 'n'], ''),
    ('section', 'Modelli Materiali'),
    ('confined',   'Cls confinato',      'mc', 'combo', ['mc', 'mclw'], ''),
    ('unconfined', 'Cls non confinato',  'mu', 'combo', ['mu', 'mulw', 'mclw'], ''),
    ('rebar',      'Acciaio',            'ra', 'combo', ['ra', 'ks'], ''),
    ('section', 'Carichi'),
    ('P_kN', 'Carico assiale P', 250.0, 'entry', None, 'kN'),
    ('section', 'Calcestruzzo'),
    ('fpc',    "f'c",        28.0,    'entry', None, 'MPa'),
    ('Ec',     "Ec (0=auto)",0,       'entry', None, 'MPa'),
    ('eco',    'eco',        0.002,   'entry', None, ''),
    ('esm',    'esm',        0.12,    'entry', None, ''),
    ('espall', 'espall',     0.0064,  'entry', None, ''),
    ('section', 'Acciaio'),
    ('fy',  'fy',         450.0,    'entry', None, 'MPa'),
    ('fyh', 'fyh',        400.0,    'entry', None, 'MPa'),
    ('Es',  'Es',         200000.0, 'entry', None, 'MPa'),
    ('fsu', 'fsu',         600.0,   'entry', None, 'MPa'),
    ('esh', 'esh',         0.008,   'entry', None, ''),
    ('esu', 'esu',         0.15,    'entry', None, ''),
    ('Ey',  'Ey (Raynor)', 350.0,   'entry', None, 'MPa'),
    ('C1',  'C1 (Raynor)', 3.5,     'entry', None, ''),
    ('section', 'Limiti di Deformazione'),
    ('csid',  'csid',   0.004,  'entry', None, ''),
    ('ssid',  'ssid',   0.015,  'entry', None, ''),
    ('ecser', 'ecser',  0.004,  'entry', None, ''),
    ('esser', 'esser',  0.015,  'entry', None, ''),
    ('ecdam', 'ecdam',  'twth', 'entry', None, ''),
    ('esdam', 'esdam',  0.060,  'entry', None, ''),
    ('section', 'Parametri Ambientali'),
    ('temp', 'Temperatura',  30.0,   'entry', None, 'C'),
    ('kLsp', 'kLsp',         0.022,  'entry', None, ''),
    ('section', 'Parametri Numerici'),
    ('itermax',   'itermax',    1000,    'entry', None, ''),
    ('ncl',       'ncl',        40,      'entry', None, ''),
    ('tolerance', 'tolerance',  0.001,   'entry', None, ''),
    ('dels',      'dels',       0.0001,  'entry', None, ''),
]

INT_KEYS = {'nbl', 'itermax', 'ncl', 'ncx', 'ncy', 'n_top_bot', 'n_side'}


# ==========================================================================
# Tooltip widget
# ==========================================================================
class Tip:
    """Hover tooltip for any widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)

    def _show(self, _event=None):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 4
        y = self.widget.winfo_rooty()
        self.tw = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f'+{x}+{y}')
        tw.wm_attributes('-topmost', True)
        lbl = tk.Label(tw, text=self.text, justify='left',
                       background='#333', foreground='#eee',
                       relief='solid', borderwidth=1,
                       font=('Segoe UI', 9), wraplength=320, padx=6, pady=4)
        lbl.pack()

    def _hide(self, _event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ==========================================================================
# Section Canvas - draws live preview of the cross-section
# ==========================================================================
class SectionCanvas(tk.Canvas):
    """Interactive cross-section preview."""

    # Palette entries: (dark_mode_value, light_mode_value)
    C_BG       = ('#1e1e1e', '#ffffff')
    C_UNCONF   = ('#555555', '#c8c8c8')
    C_CONF     = ('#3a6ea5', '#6495ed')
    C_STIRRUP  = ('#c04040', '#b22222')
    C_BAR      = ('#e0e0e0', '#1a1a1a')
    C_DIM      = ('#aaaaaa', '#555555')
    C_WI       = ('#e8a838', '#d48820')
    C_WI_CONF  = ('#ff4444', '#cc0000')
    C_LEG      = ('#70c070', '#228b22')
    C_TXT      = ('#cccccc', '#333333')

    def __init__(self, parent, **kw):
        kw.setdefault('highlightthickness', 0)
        super().__init__(parent, **kw)
        self._dark = ctk.get_appearance_mode() == 'Dark'
        self.bind('<Configure>', lambda _: self.after_idle(self.request_redraw))
        self._pending = False
        self._params = {}

    def _c(self, pair):
        return pair[0] if self._dark else pair[1]

    def request_redraw(self):
        if not self._pending:
            self._pending = True
            self.after(30, self._do_redraw)

    def _do_redraw(self):
        self._pending = False
        self._dark = ctk.get_appearance_mode() == 'Dark'
        self.configure(bg=self._c(self.C_BG))
        if self._params.get('_type') == 'circular':
            self._draw_circular()
        elif self._params.get('_type') == 'rectangular':
            self._draw_rectangular()

    def update_params(self, params):
        self._params = dict(params)
        self.request_redraw()

    # ---- coordinate helpers ------------------------------------------------
    def _scale_rect(self, H, B, margin=50):
        cw = self.winfo_width() or 400
        ch = self.winfo_height() or 400
        sc = min((cw - 2 * margin) / max(B, 1), (ch - 2 * margin) / max(H, 1))
        ox = (cw - B * sc) / 2
        oy = (ch - H * sc) / 2
        return sc, ox, oy

    # ---- circular ----------------------------------------------------------
    def _draw_circular(self):
        self.delete('all')
        p = self._params
        D   = p.get('D', 1000)
        clb = p.get('clb', 50)
        Dh  = p.get('Dh', 9)
        Dbl = p.get('Dbl', 25)
        nbl = int(p.get('nbl', 22))

        cw = self.winfo_width() or 400
        ch = self.winfo_height() or 400
        margin = 50
        R = D / 2
        sc = min((cw - 2 * margin) / D, (ch - 2 * margin) / D)
        cx, cy = cw / 2, ch / 2

        def xy(xm, ym):
            return cx + xm * sc, cy - ym * sc

        # unconfined
        r_out = R * sc
        self.create_oval(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                         fill=self._c(self.C_UNCONF), outline=self._c(self.C_DIM), width=2)
        # confined core
        Dsp = D - 2 * clb + Dh
        r_core = Dsp / 2 * sc
        self.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                         fill=self._c(self.C_CONF), outline='')
        # stirrup
        self.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                         outline=self._c(self.C_STIRRUP), dash=(6, 4), width=2)
        # bars
        Rbar = R - clb - Dbl / 2
        r_bar = max(3, Dbl / 2 * sc)
        for i in range(nbl):
            theta = 2 * math.pi * i / nbl
            bx = cx + Rbar * sc * math.sin(theta)
            by = cy - Rbar * sc * math.cos(theta)
            self.create_oval(bx - r_bar, by - r_bar, bx + r_bar, by + r_bar,
                             fill=self._c(self.C_BAR), outline='')

        # dimension: D
        self.create_line(cx - r_out, cy + r_out + 18, cx + r_out, cy + r_out + 18,
                         fill=self._c(self.C_DIM), arrow='both', width=1)
        self.create_text(cx, cy + r_out + 28, text=f'D = {D:.0f}',
                         fill=self._c(self.C_TXT), font=('Segoe UI', 9))

    # ---- rectangular -------------------------------------------------------
    def _draw_rectangular(self):
        self.delete('all')
        p = self._params
        H   = p.get('H', 400)
        B   = p.get('B', 300)
        clb = p.get('clb', 40)
        dv  = p.get('dv', 9.5)
        s_v = p.get('s', 120)
        ncx = int(p.get('ncx', 2))
        ncy = int(p.get('ncy', 2))
        mlr = p.get('_mlr', [])
        wi_mander = p.get('_wi_mander', [])

        sc, ox, oy = self._scale_rect(H, B, margin=55)

        def xy(xm, ym):
            return ox + xm * sc, oy + ym * sc

        # 1 - unconfined (outer)
        x0, y0 = xy(0, 0)
        x1, y1 = xy(B, H)
        self.create_rectangle(x0, y0, x1, y1,
                              fill=self._c(self.C_UNCONF), outline=self._c(self.C_DIM), width=2)

        # 2 - confined core
        d_core = clb - dv / 2
        cx0, cy0 = xy(d_core, d_core)
        cx1, cy1 = xy(B - d_core, H - d_core)
        self.create_rectangle(cx0, cy0, cx1, cy1,
                              fill=self._c(self.C_CONF), outline='')

        # 3 - stirrup outline
        self.create_rectangle(cx0, cy0, cx1, cy1,
                              outline=self._c(self.C_STIRRUP), dash=(6, 4), width=2)

        # 4 - stirrup legs
        # ncx = horizontal legs (parallel to B) → draw as horizontal crossties along H
        # ncy = vertical legs (parallel to H) → draw as vertical crossties along B
        Hcore = H - 2 * d_core
        Bcore = B - 2 * d_core
        if ncx > 2:
            for i in range(1, ncx - 1):
                frac = i / (ncx - 1)
                ly = d_core + frac * Hcore
                lx0, ly0 = xy(d_core, ly)
                lx1, ly1 = xy(B - d_core, ly)
                self.create_line(lx0, ly0, lx1, ly1,
                                 fill=self._c(self.C_LEG), width=1, dash=(4, 3))
        if ncy > 2:
            for i in range(1, ncy - 1):
                frac = i / (ncy - 1)
                lx = d_core + frac * Bcore
                lx0, ly0 = xy(lx, d_core)
                lx1, ly1 = xy(lx, H - d_core)
                self.create_line(lx0, ly0, lx1, ly1,
                                 fill=self._c(self.C_LEG), width=1, dash=(4, 3))

        # 5 - longitudinal bars
        bar_positions = []
        for layer in mlr:
            depth, n_bars, diam = float(layer[0]), int(layer[1]), float(layer[2])
            r_bar = max(3, diam / 2 * sc)
            if n_bars == 1:
                xs = [B / 2]
            else:
                edge = clb + diam / 2
                xs = list(np.linspace(edge, B - edge, n_bars))
            for xb in xs:
                bxc, byc = xy(xb, depth)
                self.create_oval(bxc - r_bar, byc - r_bar, bxc + r_bar, byc + r_bar,
                                 fill=self._c(self.C_BAR), outline='')
                bar_positions.append((xb, depth, diam))

        # 6a - wi arrows (orange): gaps between ALL bars
        if len(mlr) > 0:
            top_n = int(mlr[0][1])
            top_diam = float(mlr[0][2])
            if top_n > 1:
                edge = clb + top_diam / 2
                top_xs = list(np.linspace(edge, B - edge, top_n))
                top_gap = (B - 2 * clb - top_n * top_diam) / (top_n - 1)
                for j in range(len(top_xs) - 1):
                    ax0, ay0 = xy(top_xs[j] + top_diam / 2, float(mlr[0][0]))
                    ax1, ay1 = xy(top_xs[j + 1] - top_diam / 2, float(mlr[0][0]))
                    if ax1 > ax0 + 8:
                        self.create_line(ax0, ay0 - 4, ax1, ay1 - 4,
                                         fill=self._c(self.C_WI), arrow='both', width=1)
                        self.create_text((ax0 + ax1) / 2, ay0 - 14,
                                         text=f'{top_gap:.0f}',
                                         fill=self._c(self.C_WI), font=('Segoe UI', 7))

            for j in range(len(mlr) - 1):
                dep0, _, d0 = float(mlr[j][0]), int(mlr[j][1]), float(mlr[j][2])
                dep1, _, d1 = float(mlr[j + 1][0]), int(mlr[j + 1][1]), float(mlr[j + 1][2])
                side_gap = dep1 - dep0 - (d0 + d1) / 2
                ax0, ay0 = xy(B + 8 / sc, dep0 + d0 / 2)
                ax1, ay1 = xy(B + 8 / sc, dep1 - d1 / 2)
                if ay1 > ay0 + 8:
                    self.create_line(ax0, ay0, ax1, ay1,
                                     fill=self._c(self.C_WI), arrow='both', width=1)
                    self.create_text(ax0 + 16, (ay0 + ay1) / 2,
                                     text=f'{side_gap:.0f}',
                                     fill=self._c(self.C_WI), font=('Segoe UI', 7))

        # 6b - wi Mander arrows (red): gaps between RESTRAINED bars only
        if len(mlr) > 0:
            Bnet = B - 2 * clb
            Hnet = H - 2 * clb
            n_tb = max(ncy, 2)
            n_sd = max(ncx, 2)
            avg_dbl_tb = (float(mlr[0][2]) + float(mlr[-1][2])) / 2
            avg_dbl_side = sum(float(r[2]) for r in mlr) / len(mlr)

            # top face restrained bars
            if n_tb > 1:
                wi_conf_tb = (Bnet - n_tb * avg_dbl_tb) / (n_tb - 1)
                edge_r = clb + avg_dbl_tb / 2
                xs_r = list(np.linspace(edge_r, B - edge_r, n_tb))
                top_depth = float(mlr[0][0])
                for j in range(len(xs_r) - 1):
                    ax0, ay0 = xy(xs_r[j] + avg_dbl_tb / 2, top_depth)
                    ax1, ay1 = xy(xs_r[j + 1] - avg_dbl_tb / 2, top_depth)
                    if ax1 > ax0 + 8:
                        self.create_line(ax0, ay0 + 8, ax1, ay1 + 8,
                                         fill=self._c(self.C_WI_CONF), arrow='both', width=1)
                        self.create_text((ax0 + ax1) / 2, ay0 + 18,
                                         text=f'{wi_conf_tb:.0f}',
                                         fill=self._c(self.C_WI_CONF), font=('Segoe UI', 7, 'bold'))

            # left side restrained bars
            if n_sd > 1:
                wi_conf_sd = (Hnet - n_sd * avg_dbl_side) / (n_sd - 1)
                edge_v = clb + avg_dbl_side / 2
                ys_r = list(np.linspace(edge_v, H - edge_v, n_sd))
                for j in range(len(ys_r) - 1):
                    ax0, ay0 = xy(-20 / sc, ys_r[j] + avg_dbl_side / 2)
                    ax1, ay1 = xy(-20 / sc, ys_r[j + 1] - avg_dbl_side / 2)
                    if ay1 > ay0 + 8:
                        self.create_line(ax0, ay0, ax1, ay1,
                                         fill=self._c(self.C_WI_CONF), arrow='both', width=1)
                        self.create_text(ax0 - 14, (ay0 + ay1) / 2,
                                         text=f'{wi_conf_sd:.0f}',
                                         fill=self._c(self.C_WI_CONF), font=('Segoe UI', 7, 'bold'),
                                         angle=90)

        # 7 - dimension labels
        # H (left)
        hx0, hy0 = xy(-40 / sc, 0)
        hx1, hy1 = xy(-40 / sc, H)
        self.create_line(hx0, hy0, hx1, hy1, fill=self._c(self.C_DIM), arrow='both', width=1)
        self.create_text(hx0 - 14, (hy0 + hy1) / 2, text=f'H={H:.0f}',
                         fill=self._c(self.C_TXT), font=('Segoe UI', 8), angle=90)
        # B (bottom)
        bx0, by0 = xy(0, H + 12 / sc)
        bx1, by1 = xy(B, H + 12 / sc)
        self.create_line(bx0, by0, bx1, by1, fill=self._c(self.C_DIM), arrow='both', width=1)
        self.create_text((bx0 + bx1) / 2, by0 + 12, text=f'B={B:.0f}',
                         fill=self._c(self.C_TXT), font=('Segoe UI', 8))
        # clb
        clb_x, clb_y = xy(clb, 6 / sc)
        self.create_line(xy(0, 6 / sc)[0], clb_y, clb_x, clb_y,
                         fill=self._c(self.C_DIM), width=1)
        self.create_text(clb_x + 4, clb_y, text=f'clb={clb:.0f}', anchor='w',
                         fill=self._c(self.C_TXT), font=('Segoe UI', 7))

        # ncx / ncy label
        info_x, info_y = xy(B / 2, H / 2)
        self.create_text(info_x, info_y, text=f'ncx={ncx}  ncy={ncy}\ns={s_v:.0f}',
                         fill=self._c(self.C_TXT), font=('Segoe UI', 8, 'bold'), justify='center')


# ==========================================================================
# MLR Table Editor  (rectangular only)
# ==========================================================================
class MLREditor(ctk.CTkFrame):
    """Editable table for the reinforcement layer matrix."""

    def __init__(self, parent, on_change=None, **kw):
        super().__init__(parent, **kw)
        self._on_change = on_change
        self._rows = []

        # Header
        hdr = ctk.CTkFrame(self, fg_color='transparent')
        hdr.pack(fill='x', padx=2, pady=(4, 0))
        for i, (txt, w) in enumerate([('Prof. [mm]', 80), ('N. barre', 70), ('Diam [mm]', 80)]):
            ctk.CTkLabel(hdr, text=txt, width=w, font=('Segoe UI', 11, 'bold')).grid(row=0, column=i, padx=2)

        self._table_frame = ctk.CTkFrame(self, fg_color='transparent')
        self._table_frame.pack(fill='x', padx=2)

        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=2, pady=4)
        ctk.CTkButton(btn_frame, text='+ Aggiungi strato', width=130, height=28,
                      command=self._add_row).pack(side='left', padx=2)
        ctk.CTkButton(btn_frame, text='- Rimuovi ultimo', width=130, height=28,
                      fg_color='#8b0000', hover_color='#a52a2a',
                      command=self._remove_row).pack(side='left', padx=2)

        self._init_default()

    def _init_default(self):
        defaults = [(52.7, 3, 25.4), (102.0, 2, 22.2), (200.0, 2, 19.0), (349.0, 3, 22.2)]
        for d, n, dia in defaults:
            self._add_row(d, n, dia)

    def _add_row(self, depth=0.0, n_bars=2, diam=25.4):
        row_frame = ctk.CTkFrame(self._table_frame, fg_color='transparent')
        idx = len(self._rows)
        row_frame.pack(fill='x', pady=1)

        v_depth = tk.StringVar(value=f'{depth}')
        v_nbars = tk.StringVar(value=f'{int(n_bars)}')
        v_diam  = tk.StringVar(value=f'{diam}')

        for v, w in [(v_depth, 80), (v_nbars, 70), (v_diam, 80)]:
            e = ctk.CTkEntry(row_frame, textvariable=v, width=w, height=26)
            e.pack(side='left', padx=2)
            v.trace_add('write', lambda *_: self._fire_change())

        self._rows.append((row_frame, v_depth, v_nbars, v_diam))
        self._fire_change()

    def _remove_row(self):
        if len(self._rows) > 1:
            frame, *_ = self._rows.pop()
            frame.destroy()
            self._fire_change()

    def _fire_change(self):
        if self._on_change:
            self._on_change()

    def get_mlr(self):
        result = []
        for _, vd, vn, vdia in self._rows:
            try:
                result.append([float(vd.get()), int(float(vn.get())), float(vdia.get())])
            except ValueError:
                pass
        return result

    def set_mlr(self, mlr_list):
        for frame, *_ in self._rows:
            frame.destroy()
        self._rows.clear()
        for row in mlr_list:
            self._add_row(row[0], row[1], row[2])


# ==========================================================================
# Main Application
# ==========================================================================
class CumbiaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('CUMBIA_PY 0.3')
        self.geometry('1200x820')
        self.minsize(900, 600)

        ctk.set_appearance_mode('dark')
        ctk.set_default_color_theme('blue')

        self._vars_cir = {}
        self._vars_rect = {}
        self._running = False

        self._build_ui()

    # ---- top-level layout -------------------------------------------------
    def _build_ui(self):
        # Title bar
        title_bar = ctk.CTkFrame(self, height=44, corner_radius=0)
        title_bar.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(title_bar, text='  CUMBIA_PY 0.3', font=('Segoe UI', 16, 'bold')).pack(side='left', padx=10)
        ctk.CTkLabel(title_bar, text='Analysis of Reinforced Concrete Members',
                     font=('Segoe UI', 11)).pack(side='left', padx=6)

        self._theme_switch = ctk.CTkSwitch(title_bar, text='Dark', command=self._toggle_theme,
                                           width=50, height=22)
        self._theme_switch.select()
        self._theme_switch.pack(side='right', padx=14)

        ctk.CTkButton(title_bar, text='About', width=60, height=26,
                      fg_color='transparent', border_width=1,
                      command=self._show_about).pack(side='right', padx=(0, 6))

        # Tabs
        self._tabs = ctk.CTkTabview(self, anchor='nw')
        self._tabs.pack(fill='both', expand=True, padx=8, pady=(4, 2))
        self._tabs.add('Sezione Circolare')
        self._tabs.add('Sezione Rettangolare')

        self._build_cir_tab()
        self._build_rect_tab()

        # Bottom bar
        bot = ctk.CTkFrame(self, height=42)
        bot.pack(fill='x', padx=8, pady=(2, 6))
        ctk.CTkLabel(bot, text='Output:').pack(side='left', padx=(6, 2))
        self._output_dir = ctk.CTkEntry(bot, width=340,
                                        placeholder_text='Cartella principale di output')
        self._output_dir.insert(0, os.path.join(os.path.expanduser('~'), 'Desktop'))
        self._output_dir.pack(side='left', padx=4)
        ctk.CTkButton(bot, text='Sfoglia', width=70, command=self._browse).pack(side='left', padx=2)
        ctk.CTkButton(bot, text='Carica', width=70,
                      command=self._load_params).pack(side='left', padx=2)
        self._run_btn = ctk.CTkButton(bot, text='  ESEGUI ANALISI  ', width=180, height=34,
                                      font=('Segoe UI', 13, 'bold'), command=self._run)
        self._run_btn.pack(side='right', padx=10)

        self._status = ctk.CTkLabel(self, text='Pronto.', anchor='w', height=22,
                                    font=('Segoe UI', 10))
        self._status.pack(fill='x', padx=10, pady=(0, 4))

    # ---- theme toggle -----------------------------------------------------
    def _toggle_theme(self):
        mode = 'dark' if self._theme_switch.get() else 'light'
        ctk.set_appearance_mode(mode)
        self._theme_switch.configure(text='Dark' if mode == 'dark' else 'Light')
        self._cir_canvas.request_redraw()
        self._rect_canvas.request_redraw()

    # ---- About dialog -----------------------------------------------------
    def _show_about(self):
        win = ctk.CTkToplevel(self)
        win.title('About CUMBIA_PY')
        win.geometry('480x420')
        win.resizable(False, False)
        win.grab_set()
        win.after(10, win.focus_force)

        try:
            from PIL import Image
            logo_img = ctk.CTkImage(Image.open(resource_path('logo.png')),
                                    size=(80, 80))
            ctk.CTkLabel(win, image=logo_img, text='').pack(pady=(18, 6))
        except Exception:
            pass

        ctk.CTkLabel(win, text='CUMBIA_PY', font=('Segoe UI', 20, 'bold')).pack()
        ctk.CTkLabel(win, text='Version 0.3', font=('Segoe UI', 12)).pack(pady=(0, 10))

        ctk.CTkLabel(win, text='Moment-Curvature, Force-Displacement\n'
                               'and Interaction Analysis of RC Members',
                     font=('Segoe UI', 11), justify='center').pack(pady=(0, 12))

        credits = ctk.CTkFrame(win, fg_color='transparent')
        credits.pack(pady=(0, 8))

        ctk.CTkLabel(credits, text='Original analysis engine:',
                     font=('Segoe UI', 10), text_color='gray').pack()
        link_orig = ctk.CTkLabel(credits,
                                 text='CUMBIA_PY by Luis Montejo (MIT License)',
                                 font=('Segoe UI', 11, 'underline'),
                                 text_color=('#1a6dd4', '#5ba3f5'), cursor='hand2')
        link_orig.pack()
        link_orig.bind('<Button-1>',
                       lambda _: webbrowser.open('https://github.com/LuisMontejo/CUMBIA_PY'))

        ctk.CTkLabel(credits, text='', height=6).pack()

        ctk.CTkLabel(credits, text='GUI, enhancements, and distribution:',
                     font=('Segoe UI', 10), text_color='gray').pack()
        ctk.CTkLabel(credits, text='Lorenzo Buratti',
                     font=('Segoe UI', 11, 'bold')).pack()

        ctk.CTkLabel(win, text='Released under the MIT License',
                     font=('Segoe UI', 10), text_color='gray').pack(pady=(8, 4))

        ctk.CTkButton(win, text='Chiudi', width=100, command=win.destroy).pack(pady=(6, 14))

    # ---- Circular tab -----------------------------------------------------
    def _build_cir_tab(self):
        tab = self._tabs.tab('Sezione Circolare')
        pane = ctk.CTkFrame(tab)
        pane.pack(fill='both', expand=True)
        pane.columnconfigure(1, weight=1)
        pane.rowconfigure(0, weight=1)

        # left: param form
        left = ctk.CTkScrollableFrame(pane, width=380, label_text='Parametri')
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        self._build_param_form(left, CIR_PARAMS, self._vars_cir)

        # right: canvas preview
        right = ctk.CTkFrame(pane)
        right.grid(row=0, column=1, sticky='nsew')
        ctk.CTkLabel(right, text='Anteprima Sezione', font=('Segoe UI', 12, 'bold')).pack(pady=(6, 2))
        self._cir_canvas = SectionCanvas(right, width=400, height=400)
        self._cir_canvas.pack(fill='both', expand=True, padx=10, pady=6)

        self._refresh_cir_canvas()

    # ---- Rectangular tab --------------------------------------------------
    def _build_rect_tab(self):
        tab = self._tabs.tab('Sezione Rettangolare')
        pane = ctk.CTkFrame(tab)
        pane.pack(fill='both', expand=True)
        pane.columnconfigure(1, weight=1)
        pane.rowconfigure(0, weight=1)

        # left: param form
        left = ctk.CTkScrollableFrame(pane, width=380, label_text='Parametri')
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        self._build_param_form(left, RECT_PARAMS, self._vars_rect)

        # right: editor
        right = ctk.CTkFrame(pane)
        right.grid(row=0, column=1, sticky='nsew')
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        # canvas
        canvas_frame = ctk.CTkFrame(right)
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=4, pady=(4, 2))
        ctk.CTkLabel(canvas_frame, text='Editor Sezione', font=('Segoe UI', 12, 'bold')).pack(pady=(4, 0))
        self._rect_canvas = SectionCanvas(canvas_frame, width=420, height=340)
        self._rect_canvas.pack(fill='both', expand=True, padx=6, pady=4)

        # bottom editor panel
        editor = ctk.CTkFrame(right)
        editor.grid(row=1, column=0, sticky='nsew', padx=4, pady=(2, 4))
        editor.columnconfigure(0, weight=1)
        editor.columnconfigure(1, weight=1)

        # MLR table
        mlr_frame = ctk.CTkFrame(editor)
        mlr_frame.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        ctk.CTkLabel(mlr_frame, text='Armatura Longitudinale (MLR)',
                     font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))

        self._auto_var = ctk.CTkSwitch(mlr_frame, text='Layout automatico',
                                       command=self._toggle_auto_mlr)
        self._auto_var.select()
        self._auto_var.pack(anchor='w', padx=6, pady=2)

        # auto fields
        self._auto_frame = ctk.CTkFrame(mlr_frame, fg_color='transparent')
        self._auto_frame.pack(fill='x', padx=6, pady=2)

        self._v_n_top_bot = tk.StringVar(value='4')
        self._v_n_side = tk.StringVar(value='2')
        self._v_Dbl_auto = tk.StringVar(value='25.4')

        for lbl, var, tip_key in [('N. barre sup/inf:', self._v_n_top_bot, 'n_top_bot'),
                                   ('N. barre per lato:', self._v_n_side, 'n_side'),
                                   ('Diametro barre:', self._v_Dbl_auto, 'Dbl_auto')]:
            row = ctk.CTkFrame(self._auto_frame, fg_color='transparent')
            row.pack(fill='x', pady=1)
            l = ctk.CTkLabel(row, text=lbl, width=130)
            l.pack(side='left')
            Tip(l, TIPS.get(tip_key, ''))
            e = ctk.CTkEntry(row, textvariable=var, width=70, height=26)
            e.pack(side='left', padx=4)
            var.trace_add('write', lambda *_: self._refresh_rect_canvas())

        # custom MLR editor
        self._mlr_editor = MLREditor(mlr_frame, on_change=self._refresh_rect_canvas)
        self._mlr_editor.pack(fill='both', expand=True, padx=4, pady=2)
        self._mlr_editor.pack_forget()

        # stirrup / wi controls
        sw_frame = ctk.CTkFrame(editor)
        sw_frame.grid(row=0, column=1, sticky='nsew', padx=4, pady=4)
        ctk.CTkLabel(sw_frame, text='Armatura Trasversale',
                     font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))

        self._v_dv  = tk.StringVar(value='9.5')
        self._v_s   = tk.StringVar(value='120')
        self._v_ncx = tk.StringVar(value='2')
        self._v_ncy = tk.StringVar(value='2')

        for lbl, var, tip_key in [('Diam. staffe dv:', self._v_dv, 'dv'),
                                   ('Passo s:', self._v_s, 's'),
                                   ('Bracci ncx:', self._v_ncx, 'ncx'),
                                   ('Bracci ncy:', self._v_ncy, 'ncy')]:
            row = ctk.CTkFrame(sw_frame, fg_color='transparent')
            row.pack(fill='x', padx=6, pady=1)
            l = ctk.CTkLabel(row, text=lbl, width=110)
            l.pack(side='left')
            Tip(l, TIPS.get(tip_key, ''))
            e = ctk.CTkEntry(row, textvariable=var, width=70, height=26)
            e.pack(side='left', padx=4)
            var.trace_add('write', lambda *_: self._refresh_rect_canvas())

        ctk.CTkLabel(sw_frame, text='Distanze libere wi',
                     font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=6, pady=(10, 0))
        self._wi_auto = ctk.CTkSwitch(sw_frame, text='Auto', command=self._toggle_wi_auto)
        self._wi_auto.select()
        self._wi_auto.pack(anchor='w', padx=6, pady=2)
        self._v_wi = tk.StringVar(value='')
        self._wi_entry = ctk.CTkEntry(sw_frame, textvariable=self._v_wi, width=200, height=26,
                                      placeholder_text='valori separati da virgola',
                                      state='disabled')
        self._wi_entry.pack(anchor='w', padx=6, pady=2)
        Tip(self._wi_entry, TIPS.get('wi_input', ''))
        self._v_wi.trace_add('write', lambda *_: self._refresh_rect_canvas())

        self._wi_display = ctk.CTkLabel(sw_frame, text='wi = []', anchor='w',
                                        font=('Consolas', 9))
        self._wi_display.pack(anchor='w', padx=6, pady=2)

        self._refresh_rect_canvas()

    # ---- toggle auto/custom MLR -------------------------------------------
    def _toggle_auto_mlr(self):
        if self._auto_var.get():
            self._auto_frame.pack(fill='x', padx=6, pady=2)
            self._mlr_editor.pack_forget()
        else:
            self._auto_frame.pack_forget()
            self._mlr_editor.pack(fill='both', expand=True, padx=4, pady=2)
            self._mlr_editor.set_mlr(self._compute_auto_mlr())
        self._refresh_rect_canvas()

    # ---- wi auto toggle ---------------------------------------------------
    def _toggle_wi_auto(self):
        if self._wi_auto.get():
            self._wi_entry.configure(state='disabled')
        else:
            self._wi_entry.configure(state='normal')
        self._refresh_rect_canvas()

    # ---- compute auto MLR from n_top_bot, n_side, Dbl_auto ---------------
    def _compute_auto_mlr(self):
        try:
            H = float(self._vars_rect.get('H', tk.StringVar(value='400')).get())
            clb = float(self._vars_rect.get('clb', tk.StringVar(value='40')).get())
            n_tb = int(float(self._v_n_top_bot.get()))
            n_s  = int(float(self._v_n_side.get()))
            dbl  = float(self._v_Dbl_auto.get())
        except (ValueError, AttributeError):
            return [[52.7, 3, 25.4]]

        top_d = clb + dbl / 2
        bot_d = H - clb - dbl / 2
        layers = [[top_d, n_tb, dbl]]
        if n_s > 0:
            spacing = (bot_d - top_d) / (n_s + 1)
            for i in range(1, n_s + 1):
                layers.append([top_d + i * spacing, 2, dbl])
        layers.append([bot_d, n_tb, dbl])
        return layers

    # ---- compute wi from MLR (auto) ----------------------------------------
    def _compute_wi(self, mlr):
        """Wi between ALL bars (for display arrows showing bar positions)."""
        try:
            B = float(self._vars_rect.get('B', tk.StringVar(value='300')).get())
            clb = float(self._vars_rect.get('clb', tk.StringVar(value='40')).get())
        except (ValueError, AttributeError):
            return []

        if len(mlr) == 0:
            return []

        wi = []

        top_n = int(mlr[0][1])
        top_d = mlr[0][2]
        if top_n > 1:
            gap = (B - 2 * clb - top_n * top_d) / (top_n - 1)
            wi.extend([gap] * (top_n - 1))

        for j in range(len(mlr) - 1):
            gap = mlr[j + 1][0] - mlr[j][0] - (mlr[j][2] + mlr[j + 1][2]) / 2
            wi.append(gap)

        bot_n = int(mlr[-1][1])
        bot_d = mlr[-1][2]
        if bot_n > 1:
            gap = (B - 2 * clb - bot_n * bot_d) / (bot_n - 1)
            wi.extend([gap] * (bot_n - 1))

        for j in range(len(mlr) - 1):
            gap = mlr[j + 1][0] - mlr[j][0] - (mlr[j][2] + mlr[j + 1][2]) / 2
            wi.append(gap)

        return wi

    def _compute_wi_mander(self, mlr):
        """Wi between RESTRAINED bars only (for Mander confinement model)."""
        try:
            B = float(self._vars_rect.get('B', tk.StringVar(value='300')).get())
            H = float(self._vars_rect.get('H', tk.StringVar(value='400')).get())
            clb = float(self._vars_rect.get('clb', tk.StringVar(value='40')).get())
            ncx = int(float(self._v_ncx.get()))
            ncy = int(float(self._v_ncy.get()))
        except (ValueError, AttributeError):
            return []

        if len(mlr) == 0:
            return []

        Bnet = B - 2 * clb
        Hnet = H - 2 * clb
        n_tb = max(ncy, 2)
        n_sd = max(ncx, 2)

        avg_dbl_tb = (mlr[0][2] + mlr[-1][2]) / 2
        avg_dbl_side = sum(r[2] for r in mlr) / len(mlr)

        wi = []
        tb_gap = (Bnet - n_tb * avg_dbl_tb) / max(n_tb - 1, 1)
        wi.extend([tb_gap] * (n_tb - 1))
        wi.extend([tb_gap] * (n_tb - 1))

        sd_gap = (Hnet - n_sd * avg_dbl_side) / max(n_sd - 1, 1)
        wi.extend([sd_gap] * (n_sd - 1))
        wi.extend([sd_gap] * (n_sd - 1))

        return wi

    # ---- refresh canvases -------------------------------------------------
    def _refresh_cir_canvas(self, *_):
        try:
            p = {'_type': 'circular'}
            for key, var in self._vars_cir.items():
                try:
                    p[key] = float(var.get())
                except ValueError:
                    p[key] = var.get()
            self._cir_canvas.update_params(p)
        except Exception:
            pass

    def _refresh_rect_canvas(self, *_):
        try:
            p = {'_type': 'rectangular'}
            for key, var in self._vars_rect.items():
                try:
                    p[key] = float(var.get())
                except ValueError:
                    p[key] = var.get()

            # stirrup params
            try: p['dv'] = float(self._v_dv.get())
            except ValueError: pass
            try: p['s'] = float(self._v_s.get())
            except ValueError: pass
            try: p['ncx'] = int(float(self._v_ncx.get()))
            except ValueError: pass
            try: p['ncy'] = int(float(self._v_ncy.get()))
            except ValueError: pass

            # MLR
            if self._auto_var.get():
                mlr = self._compute_auto_mlr()
            else:
                mlr = self._mlr_editor.get_mlr()
            p['_mlr'] = mlr

            # wi
            if self._wi_auto.get():
                wi_display = self._compute_wi(mlr)
                wi_mander = self._compute_wi_mander(mlr)
                self._wi_display.configure(
                    text=f'wi Mander = [{", ".join(f"{v:.0f}" for v in wi_mander)}]')
            else:
                try:
                    wi_mander = [float(x.strip()) for x in self._v_wi.get().split(',') if x.strip()]
                except ValueError:
                    wi_mander = []
                wi_display = wi_mander
                self._wi_display.configure(
                    text=f'wi (manuale) = [{", ".join(f"{v:.0f}" for v in wi_mander)}]')
            p['_wi'] = wi_display
            p['_wi_mander'] = wi_mander

            self._rect_canvas.update_params(p)
        except Exception:
            pass

    # ---- build generic parameter form -------------------------------------
    def _build_param_form(self, parent, schema, var_dict):
        for item in schema:
            if item[0] == 'section':
                ctk.CTkLabel(parent, text=item[1], font=('Segoe UI', 12, 'bold'),
                             anchor='w').pack(fill='x', padx=4, pady=(10, 2))
                continue

            key, label, default, wtype, options, unit = item

            row = ctk.CTkFrame(parent, fg_color='transparent')
            row.pack(fill='x', padx=4, pady=1)

            lbl = ctk.CTkLabel(row, text=label, width=160, anchor='w')
            lbl.pack(side='left')
            if key in TIPS:
                Tip(lbl, TIPS[key])

            if wtype == 'combo':
                var = tk.StringVar(value=str(default))
                cb = ctk.CTkComboBox(row, variable=var, values=options, width=130, height=26,
                                     state='readonly')
                cb.pack(side='left', padx=4)
            else:
                var = tk.StringVar(value=str(default))
                ctk.CTkEntry(row, textvariable=var, width=130, height=26).pack(side='left', padx=4)

            if unit:
                ctk.CTkLabel(row, text=unit, width=40).pack(side='left')

            var_dict[key] = var

            if key in ('D', 'clb', 'Dh', 'nbl', 'Dbl'):
                var.trace_add('write', lambda *_, s=key: self._refresh_cir_canvas())
            if key in ('H', 'B', 'clb'):
                var.trace_add('write', lambda *_, s=key: self._refresh_rect_canvas())

    # ---- browse output dir ------------------------------------------------
    def _browse(self):
        d = ctk.filedialog.askdirectory(initialdir=self._output_dir.get())
        if d:
            self._output_dir.delete(0, 'end')
            self._output_dir.insert(0, d)

    # ---- collect all params into dict -------------------------------------
    def _collect_params(self, section_type):
        src = self._vars_cir if section_type == 'circular' else self._vars_rect
        params = {}

        for key, var in src.items():
            raw = var.get().strip()
            if key == 'ecdam':
                params[key] = 'twth' if raw.lower() == 'twth' else float(raw)
                continue
            try:
                val = float(raw)
                params[key] = int(val) if key in INT_KEYS else val
            except ValueError:
                params[key] = raw

        if params.get('Ec', 0) == 0:
            params['Ec'] = 5000 * (params.get('fpc', 35) ** 0.5)

        if section_type == 'rectangular':
            params['dv'] = float(self._v_dv.get())
            params['s'] = float(self._v_s.get())
            params['ncx'] = int(float(self._v_ncx.get()))
            params['ncy'] = int(float(self._v_ncy.get()))

            is_auto = bool(self._auto_var.get())
            params['auto_generate_MLR'] = is_auto

            if is_auto:
                params['n_top_bot'] = int(float(self._v_n_top_bot.get()))
                params['n_side'] = int(float(self._v_n_side.get()))
                params['Dbl_auto'] = float(self._v_Dbl_auto.get())
            else:
                params['auto_generate_MLR'] = False
                params['custom_MLR'] = self._mlr_editor.get_mlr()

            if self._wi_auto.get():
                mlr = self._compute_auto_mlr() if is_auto else self._mlr_editor.get_mlr()
                params['wi_input'] = self._compute_wi_mander(mlr)
            else:
                params['wi_input'] = [float(x.strip()) for x in self._v_wi.get().split(',') if x.strip()]

        return params

    # ---- save input parameters to JSON file ---------------------------------
    def _save_input_file(self, output_dir, section_type, params, run_name):
        save_data = {
            '_section_type': section_type,
            '_app_version': '0.3',
        }
        save_data.update(params)
        path = os.path.join(output_dir, f'{run_name}_input.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        return path

    # ---- load parameters from saved JSON file --------------------------------
    def _load_params(self):
        path = ctk.filedialog.askopenfilename(
            title='Carica parametri',
            filetypes=[('CUMBIA Input', '*_input.json'), ('JSON', '*.json')],
            initialdir=self._output_dir.get(),
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror('Errore', f'Impossibile leggere il file:\n{e}')
            return

        section_type = data.pop('_section_type', 'circular')
        data.pop('_app_version', None)

        if section_type == 'circular':
            self._tabs.set('Sezione Circolare')
            self._apply_params(data, self._vars_cir)
        else:
            self._tabs.set('Sezione Rettangolare')
            self._apply_params(data, self._vars_rect)
            self._apply_rect_editor_params(data)

        self._status.configure(text=f'Parametri caricati da: {os.path.basename(os.path.dirname(path))}')

    def _apply_params(self, data, var_dict):
        for key, var in var_dict.items():
            if key in data:
                var.set(str(data[key]))

    def _apply_rect_editor_params(self, data):
        if 'dv' in data:
            self._v_dv.set(str(data['dv']))
        if 's' in data:
            self._v_s.set(str(data['s']))
        if 'ncx' in data:
            self._v_ncx.set(str(data['ncx']))
        if 'ncy' in data:
            self._v_ncy.set(str(data['ncy']))

        is_auto = data.get('auto_generate_MLR', True)
        if is_auto:
            if not self._auto_var.get():
                self._auto_var.select()
                self._toggle_auto_mlr()
            if 'n_top_bot' in data:
                self._v_n_top_bot.set(str(data['n_top_bot']))
            if 'n_side' in data:
                self._v_n_side.set(str(data['n_side']))
            if 'Dbl_auto' in data:
                self._v_Dbl_auto.set(str(data['Dbl_auto']))
        else:
            if self._auto_var.get():
                self._auto_var.deselect()
                self._toggle_auto_mlr()
            if 'custom_MLR' in data:
                self._mlr_editor.set_mlr(data['custom_MLR'])

        wi_input = data.get('wi_input', [0])
        if wi_input == [0] or wi_input == 0:
            if not self._wi_auto.get():
                self._wi_auto.select()
                self._toggle_wi_auto()
        else:
            if self._wi_auto.get():
                self._wi_auto.deselect()
                self._toggle_wi_auto()
            self._v_wi.set(','.join(str(v) for v in wi_input))

        self._refresh_rect_canvas()

    # ---- run analysis -----------------------------------------------------
    def _run(self):
        if self._running:
            return

        tab_name = self._tabs.get()
        section_type = 'circular' if 'Circolare' in tab_name else 'rectangular'

        try:
            params = self._collect_params(section_type)
        except Exception as e:
            messagebox.showerror('Errore parametri', f'Errore nella lettura dei parametri:\n{e}')
            return

        # "Save as" dialog: ask subfolder name
        dialog = ctk.CTkInputDialog(
            text='Nome cartella di salvataggio:',
            title='Salva con nome',
        )
        dialog.geometry('380x180')
        subfolder = dialog.get_input()
        if not subfolder:
            return
        subfolder = subfolder.strip()
        if not subfolder:
            return

        # Build the output name: CUMBIACIR_pil1 or CUMBIARECT_pil1
        prefix = 'CUMBIACIR' if section_type == 'circular' else 'CUMBIARECT'
        run_name = f'{prefix}_{subfolder}'
        params['name'] = run_name

        base_dir = self._output_dir.get()
        output_dir = os.path.join(base_dir, subfolder)
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror('Errore', f'Impossibile creare la cartella:\n{e}')
            return

        script_name = 'CUMBIA_CIR.py' if section_type == 'circular' else 'CUMBIA_RECT.py'
        script_path = resource_path(script_name)
        if not os.path.isfile(script_path):
            messagebox.showerror('Errore', f'Script non trovato:\n{script_path}')
            return

        # copy logo to output dir
        logo_src = resource_path('logo.png')
        logo_dst = os.path.join(output_dir, 'logo.png')
        if os.path.isfile(logo_src) and not os.path.isfile(logo_dst):
            try:
                shutil.copy2(logo_src, logo_dst)
            except Exception:
                pass

        # save input parameters
        try:
            self._save_input_file(output_dir, section_type, params, run_name)
        except Exception:
            pass

        self._running = True
        self._run_btn.configure(state='disabled')
        self._status.configure(text='Analisi in corso... attendere.')
        self.update_idletasks()

        import matplotlib
        matplotlib.use('Agg')

        param_fd, param_path = tempfile.mkstemp(suffix='.json', prefix='cumbia_')
        try:
            with os.fdopen(param_fd, 'w') as f:
                json.dump(params, f)

            original_dir = os.getcwd()
            original_env = os.environ.get('CUMBIA_PARAMS', '')

            os.chdir(output_dir)
            os.environ['CUMBIA_PARAMS'] = param_path

            mm_dir = resource_path('')
            if mm_dir not in sys.path:
                sys.path.insert(0, mm_dir)

            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()

            ns = {'__builtins__': __builtins__, '__name__': '__main__', '__file__': script_path}
            exec(compile(code, script_path, 'exec'), ns)

            # open PDF report
            pdf_file = os.path.join(output_dir, f'{run_name}_Full_Report.pdf')
            if os.path.isfile(pdf_file):
                os.startfile(pdf_file)

            self._status.configure(text=f'Completato! File salvati in: {output_dir}')
            messagebox.showinfo('Completato',
                                f'Analisi completata!\n\nFile salvati in:\n{output_dir}')
        except Exception as e:
            self._status.configure(text='Errore durante l\'analisi.')
            messagebox.showerror('Errore', f'{type(e).__name__}: {e}')
        finally:
            os.chdir(original_dir)
            if original_env:
                os.environ['CUMBIA_PARAMS'] = original_env
            elif 'CUMBIA_PARAMS' in os.environ:
                del os.environ['CUMBIA_PARAMS']
            try:
                os.remove(param_path)
            except Exception:
                pass
            self._running = False
            self._run_btn.configure(state='normal')


# ==========================================================================
if __name__ == '__main__':
    app = CumbiaApp()
    app.mainloop()
