"""
Internationalization support for CUMBIA_PY GUI.
Default language: English. Italian available as secondary option.
"""
import os
import json

_lang = 'en'

_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'cumbia_settings.json')


def _load_preference():
    global _lang
    try:
        with open(_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            lang = data.get('lang', 'en')
            if lang in ('en', 'it'):
                _lang = lang
    except Exception:
        pass


def save_preference(lang):
    global _lang
    if lang in ('en', 'it'):
        _lang = lang
    try:
        data = {}
        if os.path.isfile(_CONFIG_FILE):
            with open(_CONFIG_FILE, 'r') as f:
                data = json.load(f)
        data['lang'] = _lang
        with open(_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_lang():
    return _lang


def set_lang(lang):
    global _lang
    if lang in ('en', 'it'):
        _lang = lang


def T(key):
    """Translate a string key to the current language."""
    strings = _STRINGS.get(_lang, _STRINGS['en'])
    return strings.get(key, _STRINGS['en'].get(key, key))


def get_tips():
    """Return the tooltip dictionary for the current language."""
    return _TIPS_EN if _lang == 'en' else _TIPS_IT


# ======================================================================
# UI strings
# ======================================================================
_STRINGS = {
    'en': {
        # Tabs
        'tab_circular':       'Circular Section',
        'tab_rectangular':    'Rectangular Section',

        # Section headers (param form)
        'sect_general':       'General Controls',
        'sect_geometry':      'Section Geometry',
        'sect_member':        'Member Properties',
        'sect_materials':     'Material Models',
        'sect_reinforcement': 'Reinforcement',
        'sect_loads':         'Loads',
        'sect_concrete':      'Concrete',
        'sect_steel':         'Steel',
        'sect_strain_limits': 'Strain Limits',
        'sect_environmental': 'Environmental Parameters',
        'sect_numerical':     'Numerical Parameters',

        # Parameter labels — circular
        'lbl_name':           'Project name',
        'lbl_interaction':    'M-P Interaction',
        'lbl_hinge_method':   'Hinge method',
        'lbl_D':              'Diameter D',
        'lbl_clb':            'Cover clb',
        'lbl_L':              'Length L',
        'lbl_bending':        'Bending',
        'lbl_ductilitymode':  'Ductility',
        'lbl_p_delta':        'P-Delta',
        'lbl_confined':       'Confined concrete',
        'lbl_unconfined':     'Unconfined concrete',
        'lbl_rebar':          'Steel',
        'lbl_nbl':            'N. long. bars',
        'lbl_Dbl':            'Long. bar diameter',
        'lbl_Dh':             'Spiral/hoop diam.',
        'lbl_type_reinf':     'Transv. reinf. type',
        'lbl_s':              'Transv. spacing',
        'lbl_P_kN':           'Axial load P',
        'lbl_temp':           'Temperature',

        # Parameter labels — rectangular
        'lbl_H':              'Height H',
        'lbl_B':              'Width B',

        # Canvas / editor titles
        'parameters':         'Parameters',
        'section_preview':    'Section Preview',
        'section_editor':     'Section Editor',

        # MLR editor
        'longitudinal_mlr':   'Longitudinal Reinforcement (MLR)',
        'auto_layout':        'Auto layout',
        'n_bars_top_bot':     'N. bars top/bot:',
        'n_bars_per_side':    'N. bars per side:',
        'bar_diameter':       'Bar diameter:',
        'add_layer':          '+ Add layer',
        'remove_last':        '- Remove last',
        'mlr_depth':          'Depth [mm]',
        'mlr_nbars':          'N. bars',
        'mlr_diam':           'Diam [mm]',

        # Transverse reinforcement
        'transverse_reinf':   'Transverse Reinforcement',
        'stirrup_diam':       'Stirrup diam. dv:',
        'spacing_s':          'Spacing s:',
        'legs_ncx':           'Legs ncx:',
        'legs_ncy':           'Legs ncy:',

        # wi
        'clear_dist_wi':      'Clear distances wi',
        'comma_separated':    'comma-separated values',

        # Bottom bar
        'output':             'Output:',
        'output_placeholder': 'Main output folder',
        'browse':             'Browse',
        'load':               'Load',
        'run_analysis':       '  RUN ANALYSIS  ',

        # Status bar
        'ready':              'Ready.',
        'running':            'Analysis running... please wait.',
        'completed_status':   'Completed! Files saved to: ',
        'error_status':       'Error during analysis.',
        'params_loaded':      'Parameters loaded from: ',

        # Dialogs
        'about_title':        'About CUMBIA_PY',
        'close':              'Close',
        'load_params_title':  'Load parameters',
        'save_folder_prompt': 'Output folder name:',
        'save_as_title':      'Save as',

        # Messages
        'error':              'Error',
        'param_error':        'Parameter error',
        'completed':          'Completed',
        'msg_completed':      'Analysis completed!\n\nFiles saved to:\n',
        'msg_read_error':     'Cannot read file:\n',
        'msg_param_error':    'Error reading parameters:\n',
        'msg_folder_error':   'Cannot create folder:\n',
        'msg_script_missing': 'Script not found:\n',
        'msg_restart':        'Please restart the application\nfor the language change to take effect.',
        'language_changed':   'Language',
    },

    'it': {
        # Tabs
        'tab_circular':       'Sezione Circolare',
        'tab_rectangular':    'Sezione Rettangolare',

        # Section headers
        'sect_general':       'Controlli Generali',
        'sect_geometry':      'Geometria Sezione',
        'sect_member':        'Proprieta Membro',
        'sect_materials':     'Modelli Materiali',
        'sect_reinforcement': 'Armatura',
        'sect_loads':         'Carichi',
        'sect_concrete':      'Calcestruzzo',
        'sect_steel':         'Acciaio',
        'sect_strain_limits': 'Limiti di Deformazione',
        'sect_environmental': 'Parametri Ambientali',
        'sect_numerical':     'Parametri Numerici',

        # Parameter labels — circular
        'lbl_name':           'Nome progetto',
        'lbl_interaction':    'Interazione M-P',
        'lbl_hinge_method':   'Metodo cerniera',
        'lbl_D':              'Diametro D',
        'lbl_clb':            'Copriferro clb',
        'lbl_L':              'Lunghezza L',
        'lbl_bending':        'Flessione',
        'lbl_ductilitymode':  'Duttilita',
        'lbl_p_delta':        'P-Delta',
        'lbl_confined':       'Cls confinato',
        'lbl_unconfined':     'Cls non confinato',
        'lbl_rebar':          'Acciaio',
        'lbl_nbl':            'N. barre long.',
        'lbl_Dbl':            'Diametro barre long.',
        'lbl_Dh':             'Diametro spirali/cerchi',
        'lbl_type_reinf':     'Tipo arm. trasversale',
        'lbl_s':              'Passo arm. trasversale',
        'lbl_P_kN':           'Carico assiale P',
        'lbl_temp':           'Temperatura',

        # Parameter labels — rectangular
        'lbl_H':              'Altezza H',
        'lbl_B':              'Larghezza B',

        # Canvas / editor titles
        'parameters':         'Parametri',
        'section_preview':    'Anteprima Sezione',
        'section_editor':     'Editor Sezione',

        # MLR editor
        'longitudinal_mlr':   'Armatura Longitudinale (MLR)',
        'auto_layout':        'Layout automatico',
        'n_bars_top_bot':     'N. barre sup/inf:',
        'n_bars_per_side':    'N. barre per lato:',
        'bar_diameter':       'Diametro barre:',
        'add_layer':          '+ Aggiungi strato',
        'remove_last':        '- Rimuovi ultimo',
        'mlr_depth':          'Prof. [mm]',
        'mlr_nbars':          'N. barre',
        'mlr_diam':           'Diam [mm]',

        # Transverse reinforcement
        'transverse_reinf':   'Armatura Trasversale',
        'stirrup_diam':       'Diam. staffe dv:',
        'spacing_s':          'Passo s:',
        'legs_ncx':           'Bracci ncx:',
        'legs_ncy':           'Bracci ncy:',

        # wi
        'clear_dist_wi':      'Distanze libere wi',
        'comma_separated':    'valori separati da virgola',

        # Bottom bar
        'output':             'Output:',
        'output_placeholder': 'Cartella principale di output',
        'browse':             'Sfoglia',
        'load':               'Carica',
        'run_analysis':       '  ESEGUI ANALISI  ',

        # Status bar
        'ready':              'Pronto.',
        'running':            'Analisi in corso... attendere.',
        'completed_status':   'Completato! File salvati in: ',
        'error_status':       "Errore durante l'analisi.",
        'params_loaded':      'Parametri caricati da: ',

        # Dialogs
        'about_title':        'About CUMBIA_PY',
        'close':              'Chiudi',
        'load_params_title':  'Carica parametri',
        'save_folder_prompt': 'Nome cartella di salvataggio:',
        'save_as_title':      'Salva con nome',

        # Messages
        'error':              'Errore',
        'param_error':        'Errore parametri',
        'completed':          'Completato',
        'msg_completed':      'Analisi completata!\n\nFile salvati in:\n',
        'msg_read_error':     'Impossibile leggere il file:\n',
        'msg_param_error':    'Errore nella lettura dei parametri:\n',
        'msg_folder_error':   'Impossibile creare la cartella:\n',
        'msg_script_missing': 'Script non trovato:\n',
        'msg_restart':        "Riavvia l'applicazione\nper applicare il cambio di lingua.",
        'language_changed':   'Lingua',
    },
}


# ======================================================================
# Tooltips — English
# ======================================================================
_TIPS_EN = {
    'name':          'Output file prefix (Excel, PDF, PNG)',
    'interaction':   'Perform axial load - moment interaction analysis (M-P diagram)',
    'hinge_method':  'pck = Priestley et al. (2007)\nmodified_lpr = Goodnight et al. (2016)',
    'D':             'Outer diameter of the circular section',
    'H':             'Section depth (perpendicular to the bending axis)',
    'B':             'Section width',
    'clb':           'Clear cover: distance from the external surface\nto the longitudinal bar surface',
    'L':             'Free length of the structural member',
    'bending':       'single = cantilever\ndouble = fixed-fixed',
    'ductilitymode': 'Loading mode for the UCSD shear\ndegradation factor (uniaxial or biaxial)',
    'p_delta':       'Include approximate P-Delta effects\n(geometric overturning moment subtraction)',
    'confined':      'Confined concrete constitutive model:\nmc = Mander confined, mclw = Mander lightweight',
    'unconfined':    'Unconfined concrete constitutive model:\nmu = Mander unconfined, mulw = lightweight',
    'rebar':         'Steel constitutive model:\nra = Raynor, ks = King',
    'nbl':           'Total number of longitudinal bars\nuniformly distributed on the circular section',
    'Dbl':           'Longitudinal bar diameter (circular)',
    'Dh':            'Transverse reinforcement diameter (spirals/hoops)',
    'type_reinf':    'Transverse reinforcement type:\nspirals = continuous spiral\nhoops = closed hoops',
    's':             'Transverse reinforcement spacing (center-to-center)',
    'P_kN':          'Applied axial load\n+ = compression, - = tension',
    'fpc':           "Cylindrical concrete compressive strength (f'c)",
    'Ec':            "Concrete elastic modulus\n0 = auto-calculate: 5000 * sqrt(f'c)",
    'eco':           'Peak strain of unconfined concrete\n(0.002 normal, 0.004 lightweight)',
    'esm':           'Maximum transverse steel strain\n(typically 0.10 - 0.15)',
    'espall':        'Maximum unconfined concrete strain\n(spalling strain)',
    'fy':            'Longitudinal steel yield strength',
    'fyh':           'Transverse steel yield strength',
    'Es':            'Steel elastic modulus',
    'fsu':           'Longitudinal steel ultimate strength',
    'esh':           'Strain at onset of strain hardening',
    'esu':           'Steel ultimate strain',
    'Ey':            'Yield plateau slope (Raynor model)',
    'C1':            'Strain hardening curvature parameter (Raynor model)',
    'csid':          'Concrete strain limit for\nthe interaction diagram (yield surface)',
    'ssid':          'Steel strain limit for\nthe interaction diagram (yield surface)',
    'ecser':         'Concrete compressive strain limit\nfor the serviceability limit state',
    'esser':         'Steel tensile strain limit\nfor the serviceability limit state',
    'ecdam':         'Concrete strain limit for damage control\ntwth = 2/3 of ultimate strain, or numeric value',
    'esdam':         'Steel tensile strain limit\nfor damage control',
    'temp':          'Specimen temperature [°C]\n(affects tensile strength if < 0)',
    'kLsp':          'Strain penetration constant\n(0.022 at room temperature, 0.011 at -40°C)',
    'itermax':       'Maximum number of iterations for\nneutral axis search',
    'ncl':           'Number of concrete discretization layers',
    'tolerance':     "Force equilibrium tolerance multiplier\n(tol = tolerance * Area * f'c)",
    'dels':          'Strain increment (delta strain)\nfor the sectional analysis',
    'auto_generate_MLR': 'On: auto-generated uniform peripheral layout\nOff: custom MLR matrix',
    'n_top_bot':     'Number of bars on the top face\n(and equal on the bottom face)',
    'n_side':        'Number of bars on each side\n(excluding corners)',
    'Dbl_auto':      'Diameter of all longitudinal bars\n(auto layout)',
    'dv':            'Transverse reinforcement diameter (stirrups)',
    'ncx':           'Number of legs in X direction\n(parallel to B, confinement)',
    'ncy':           'Number of legs in Y direction\n(parallel to H, shear resistance)',
    'wi_input':      'Clear distances between peripheral longitudinal bars.\n[0] = automatic calculation',
}


# ======================================================================
# Tooltips — Italian
# ======================================================================
_TIPS_IT = {
    'name':          'Prefisso per i file di output (Excel, PDF, PNG)',
    'interaction':   'Esegui analisi di interazione carico assiale - momento (diagramma M-P)',
    'hinge_method':  'pck = Priestley et al. (2007)\nmodified_lpr = Goodnight et al. (2016)',
    'D':             'Diametro esterno della sezione circolare',
    'H':             "Altezza della sezione (perpendicolare all'asse di flessione)",
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
    'Dh':            "Diametro dell'armatura trasversale (spirali/cerchi)",
    'type_reinf':    'Tipo di armatura trasversale:\nspirals = spirale continua\nhoops = cerchi chiusi',
    's':             "Passo (interasse) dell'armatura trasversale",
    'P_kN':          'Carico assiale applicato\n+ = compressione, - = trazione',
    'fpc':           "Resistenza a compressione cilindrica del calcestruzzo (f'c)",
    'Ec':            "Modulo elastico del calcestruzzo\n0 = calcolo automatico: 5000 * sqrt(f'c)",
    'eco':           'Deformazione al picco del calcestruzzo non confinato\n(0.002 normale, 0.004 lightweight)',
    'esm':           "Deformazione massima dell'acciaio trasversale\n(tipicamente 0.10 - 0.15)",
    'espall':        'Deformazione massima del calcestruzzo non confinato\n(deformazione di spalling)',
    'fy':            "Tensione di snervamento dell'acciaio longitudinale",
    'fyh':           "Tensione di snervamento dell'acciaio trasversale",
    'Es':            "Modulo elastico dell'acciaio",
    'fsu':           "Tensione ultima dell'acciaio longitudinale",
    'esh':           "Deformazione all'inizio dell'incrudimento",
    'esu':           "Deformazione ultima dell'acciaio",
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
    'itermax':       "Numero massimo di iterazioni per la ricerca\ndell'asse neutro",
    'ncl':           'Numero di strati di discretizzazione del calcestruzzo',
    'tolerance':     "Moltiplicatore di tolleranza per l'equilibrio delle forze\n(tol = tolerance * Area * f'c)",
    'dels':          'Incremento di deformazione (delta strain)\nper l\'analisi sezionale',
    'auto_generate_MLR': 'Attivo: layout periferico uniforme auto-generato\nDisattivo: matrice MLR personalizzata',
    'n_top_bot':     'Numero di barre sulla faccia superiore\n(e uguale sulla inferiore)',
    'n_side':        'Numero di barre su ciascun lato\n(esclusi gli angoli)',
    'Dbl_auto':      'Diametro di tutte le barre longitudinali\n(layout automatico)',
    'dv':            "Diametro dell'armatura trasversale (staffe)",
    'ncx':           'Numero di bracci in direzione X\n(paralleli a B, confinamento)',
    'ncy':           'Numero di bracci in direzione Y\n(paralleli a H, resistenza a taglio)',
    'wi_input':      'Distanze libere tra barre longitudinali periferiche.\n[0] = calcolo automatico',
}


# Load language preference on import
_load_preference()
