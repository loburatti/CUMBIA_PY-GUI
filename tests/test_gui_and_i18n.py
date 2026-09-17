"""Level 5 - GUI-side logic that does not need a display.

Covers the translation layer, the parameter schemas, the numeric validation
added to _collect_params, and the JSON round-trip used by Save/Load.
"""
import ast
import json
import os

import pytest

from tests.conftest import REPO_ROOT

import i18n


# ------------------------------------------------------------------ i18n ----
def _string_tables():
    tree = ast.parse(open(os.path.join(REPO_ROOT, 'i18n.py'),
                          encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ('_STRINGS', '_TIPS_EN', '_TIPS_IT')):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


def test_english_and_italian_define_the_same_keys():
    strings = _string_tables()['_STRINGS']
    en, it = set(strings['en']), set(strings['it'])
    assert en - it == set(), f'missing Italian translations: {sorted(en - it)}'
    assert it - en == set(), f'missing English translations: {sorted(it - en)}'


def test_tooltips_cover_both_languages():
    tables = _string_tables()
    en, it = set(tables['_TIPS_EN']), set(tables['_TIPS_IT'])
    assert en == it, f'tooltip mismatch: {sorted(en ^ it)}'


def test_no_translation_is_empty():
    for lang, table in _string_tables()['_STRINGS'].items():
        blank = [k for k, v in table.items() if not str(v).strip()]
        assert not blank, f'{lang}: empty strings for {blank}'


def test_every_translation_key_used_in_main_exists(gui):
    """A T('...') call with no entry silently renders the raw key in the UI."""
    import re
    src = open(os.path.join(REPO_ROOT, 'main.py'), encoding='utf-8').read()
    used = set(re.findall(r"T\(\s*['\"]([A-Za-z0-9_]+)['\"]\s*\)", src))
    defined = set(_string_tables()['_STRINGS']['en'])
    # schema labels may be literal display text rather than keys
    schema_labels = {row[1] for row in gui.CIR_PARAMS + gui.RECT_PARAMS}
    missing = {k for k in used - defined if k not in schema_labels}
    assert not missing, f'T() keys with no translation: {sorted(missing)}'


def test_T_falls_back_to_english_then_to_the_key():
    original = i18n.get_lang()
    try:
        i18n.set_lang('it')
        assert i18n.T('completed') != 'completed'
        assert i18n.T('a_key_that_does_not_exist') == 'a_key_that_does_not_exist'
    finally:
        i18n.set_lang(original)


def test_set_lang_ignores_unsupported_languages():
    original = i18n.get_lang()
    try:
        i18n.set_lang('en')
        i18n.set_lang('de')
        assert i18n.get_lang() == 'en'
    finally:
        i18n.set_lang(original)


# --------------------------------------------------------------- schemas ----
def test_schema_rows_are_well_formed(gui):
    for name, schema in (('CIR', gui.CIR_PARAMS), ('RECT', gui.RECT_PARAMS)):
        for row in schema:
            if row[0] == 'section':
                assert len(row) == 2, f'{name}: bad section row {row}'
                continue
            assert len(row) == 6, f'{name}: bad parameter row {row}'
            key, label, default, widget, options, unit = row
            assert widget in ('entry', 'combo'), f'{name}/{key}: {widget}'
            if widget == 'combo':
                assert options, f'{name}/{key}: combo with no options'
                assert default in options, (
                    f'{name}/{key}: default {default!r} not in {options}')
            else:
                assert options is None


def test_no_duplicate_keys_in_a_schema(gui):
    for name, schema in (('CIR', gui.CIR_PARAMS), ('RECT', gui.RECT_PARAMS)):
        keys = [r[0] for r in schema if r[0] != 'section']
        assert len(keys) == len(set(keys)), f'{name}: duplicated keys'


def test_numeric_key_sets_exclude_free_text_fields(gui):
    for numeric in (gui.CIR_NUMERIC_KEYS, gui.RECT_NUMERIC_KEYS):
        assert 'name' not in numeric, 'the output name is free text'
        assert 'ecdam' not in numeric, "ecdam also accepts 'twth'"
        assert 'bending' not in numeric
        assert 'fpc' in numeric and 'L' in numeric


def test_int_keys_are_declared_numeric(gui):
    both = gui.CIR_NUMERIC_KEYS | gui.RECT_NUMERIC_KEYS
    schema_ints = {k for k in gui.INT_KEYS
                   if k in {r[0] for r in gui.CIR_PARAMS + gui.RECT_PARAMS}}
    assert schema_ints <= both


def test_combo_options_match_what_the_engines_accept(gui):
    """Every material model offered in the GUI must exist in material_models."""
    import material_models as mm
    known = {'mc', 'mu', 'mclw', 'mulw'}
    for schema in (gui.CIR_PARAMS, gui.RECT_PARAMS):
        for row in schema:
            if row[0] in ('confined', 'unconfined'):
                assert set(row[4]) <= known, f'{row[0]}: unknown model in {row[4]}'
    assert hasattr(mm, 'manderconf') and hasattr(mm, 'manderconflw')
    assert hasattr(mm, 'manderun') and hasattr(mm, 'manderunlw')


# ------------------------------------------------------------ validation ----
class _V:
    """Stand-in for a tk.StringVar. Entry widgets always hold text, so values
    are stringified — except booleans, which back switches and must stay
    boolean: str(False) is the truthy string 'False' and would silently flip
    every `if self._wi_auto.get()` to the opposite branch."""

    def __init__(self, value):
        self._v = value if isinstance(value, bool) else str(value)

    def get(self):
        return self._v


def _app_with(gui, section, overrides=None, wi_auto=False, mlr_auto=True):
    """Minimal stand-in exposing what _collect_params reads."""
    schema = gui.CIR_PARAMS if section == 'circular' else gui.RECT_PARAMS
    values = {row[0]: _V(row[2]) for row in schema if row[0] != 'section'}
    values.update({k: _V(v) for k, v in (overrides or {}).items()})

    app = gui.CumbiaApp.__new__(gui.CumbiaApp)
    app._vars_cir = values if section == 'circular' else {}
    app._vars_rect = values if section == 'rectangular' else {}
    app._v_dv, app._v_s = _V(9.5), _V(120)
    app._v_ncx, app._v_ncy = _V(2), _V(2)
    app._v_n_top_bot, app._v_n_side, app._v_Dbl_auto = _V(4), _V(2), _V(25.4)
    app._v_wi = _V('169.2, 169.2, 269.2, 269.2')
    app._auto_var, app._wi_auto = _V(mlr_auto), _V(wi_auto)
    return app


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
def test_defaults_collect_cleanly(gui, section):
    params = gui.CumbiaApp._collect_params(_app_with(gui, section), section)
    assert isinstance(params['fpc'], float)
    assert isinstance(params['ncl'], int)
    assert params['Ec'] > 0, 'Ec = 0 must be replaced by the 5000*sqrt(fpc) default'


@pytest.mark.parametrize('section', ['circular', 'rectangular'])
def test_a_non_numeric_entry_names_the_offending_field(gui, section):
    """Before validation this became a string and blew up much later,
    deep inside numpy, with a message naming nothing the user recognises."""
    app = _app_with(gui, section, {'fpc': 'abc'})
    with pytest.raises(ValueError) as err:
        gui.CumbiaApp._collect_params(app, section)
    assert "f'c" in str(err.value)
    assert 'abc' in str(err.value)


@pytest.mark.parametrize('bad', ['', '12,5', 'nan', '3.4.5'])
def test_malformed_numbers_are_rejected(gui, bad):
    app = _app_with(gui, 'rectangular', {'L': bad})
    with pytest.raises(ValueError):
        gui.CumbiaApp._collect_params(app, 'rectangular')


def test_ecdam_still_accepts_the_twth_keyword(gui):
    app = _app_with(gui, 'rectangular', {'ecdam': 'twth'})
    assert gui.CumbiaApp._collect_params(app, 'rectangular')['ecdam'] == 'twth'

    app = _app_with(gui, 'rectangular', {'ecdam': '0.018'})
    assert gui.CumbiaApp._collect_params(app, 'rectangular')['ecdam'] == pytest.approx(0.018)


def test_free_text_fields_survive_validation(gui):
    app = _app_with(gui, 'circular', {'name': 'pila_A1', 'bending': 'double'})
    params = gui.CumbiaApp._collect_params(app, 'circular')
    assert params['name'] == 'pila_A1'
    assert params['bending'] == 'double'


# ----------------------------------------------------------- persistence ----
def test_saved_parameters_survive_a_json_round_trip(gui, tmp_path):
    app = _app_with(gui, 'rectangular')
    params = gui.CumbiaApp._collect_params(app, 'rectangular')
    path = gui.CumbiaApp._save_input_file(
        app, str(tmp_path), 'rectangular', params, 'CUMBIARECT_test')

    assert os.path.isfile(path)
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    assert data['_section_type'] == 'rectangular'
    assert '_app_version' in data
    for key, value in params.items():
        assert data[key] == value, f'{key} did not round-trip'


def test_saved_parameters_are_accepted_by_the_engine(gui, tmp_path):
    """The Save/Load format must be exactly what CUMBIA_PARAMS expects."""
    from tests.conftest import run_engine

    app = _app_with(gui, 'rectangular')
    params = gui.CumbiaApp._collect_params(app, 'rectangular')
    params['name'] = 'roundtrip'
    params['interaction'] = 'n'
    ns = run_engine('rectangular', params)
    assert ns['Mn'] > 0
    assert ns['fpc'] == pytest.approx(params['fpc'])
    assert ns['B'] == pytest.approx(params['B'])


def test_open_with_default_app_never_raises(gui, tmp_path):
    """A missing viewer must not turn a successful analysis into an error."""
    missing = tmp_path / 'nope.pdf'
    assert gui.open_with_default_app(str(missing)) in (True, False)


@pytest.mark.parametrize('wi_auto', [False, True])
def test_both_wi_modes_produce_a_usable_wi_input(gui, wi_auto):
    """Manual entry and the Auto switch must both yield numeric wi_input.

    The Auto branch reaches _compute_wi_mander, which is also the path that
    used to build a throwaway tk.StringVar and fail without a root window.
    """
    app = _app_with(gui, 'rectangular', wi_auto=wi_auto)
    params = gui.CumbiaApp._collect_params(app, 'rectangular')
    wi = params['wi_input']
    assert wi, 'no wi produced'
    assert all(isinstance(v, float) for v in wi)
    assert all(v > 0 for v in wi)
    json.dumps(params)


def test_reading_a_field_does_not_need_a_tk_root(gui):
    """_rect_value must not construct a Tk variable for its fallback."""
    app = _app_with(gui, 'rectangular')
    assert float(gui.CumbiaApp._rect_value(app, 'B', '999')) == 300.0
    assert gui.CumbiaApp._rect_value(app, 'not_a_field', '42') == '42'


def test_gui_logic_never_constructs_a_tk_variable(gui, monkeypatch):
    """Reproduces the CI failure mode: a real tkinter with no display.

    There, importing tkinter succeeds but every tk.StringVar() raises
    "Too early to create variable: no default root window". None of the
    pure-logic paths may construct one, so they are exercised here with a
    StringVar that always raises.
    """
    def _explode(*args, **kwargs):
        raise RuntimeError(
            'Too early to create variable: no default root window')

    monkeypatch.setattr(gui.tk, 'StringVar', _explode)

    mlr = [[52.7, 4, 25.4], [347.3, 4, 25.4]]
    app = _app_with(gui, 'rectangular', wi_auto=True)

    assert gui.CumbiaApp._rect_value(app, 'B', '300') == '300.0'
    assert gui.CumbiaApp._compute_auto_mlr(app)
    assert gui.CumbiaApp._compute_wi(app, mlr)
    assert gui.CumbiaApp._compute_wi_mander(app, mlr)
    assert gui.CumbiaApp._collect_params(app, 'rectangular')['wi_input']


# ------------------------------------------------------------- versioning ----
VERSION = '0.3.4'


def test_every_version_string_agrees():
    """The version appears in several places and drifted once already: the
    app said 0.3 while the repository was releasing 0.3.2, so saved input
    files could not tell the two apart."""
    import re

    main_src = open(os.path.join(REPO_ROOT, 'main.py'), encoding='utf-8').read()
    found = set(re.findall(r'CUMBIA_PY (\d+\.\d+(?:\.\d+)?)', main_src))
    assert found == {VERSION}, f'main.py advertises {sorted(found)}'

    app_version = re.search(r"'_app_version':\s*'([^']+)'", main_src)
    assert app_version and app_version.group(1) == VERSION, (
        '_app_version written into saved parameter files is out of step')

    for lang, table in _string_tables()['_STRINGS'].items():
        assert VERSION in table['about_version'], (
            f"{lang}: About dialog shows {table['about_version']!r}")


# ----------------------------------------------------- preview label sizes ----
def test_preview_labels_are_large_enough(gui):
    """The preview labels started at 7-8 pt and were reported unreadable
    twice. Pin a floor so they cannot quietly shrink again."""
    canvas = gui.SectionCanvas
    sizes = {name: getattr(canvas, name) for name in
             ('S_DIM', 'S_DIM_SM', 'S_INFO', 'S_WI', 'S_WI_CONF')}
    for name, size in sizes.items():
        assert isinstance(size, int), f'{name} is not a point size'
        assert size >= 11, f'{name} is {size} pt — too small to read'


def test_preview_font_helper_survives_a_missing_scaling_factor(gui):
    """_font reads CustomTkinter's scaling; it must never raise or shrink
    the label if that lookup fails."""
    inst = gui.SectionCanvas.__new__(gui.SectionCanvas)
    for bold in (False, True):
        family, size, *rest = gui.SectionCanvas._font(
            inst, gui.SectionCanvas.S_DIM, bold=bold)
        assert family == 'Segoe UI'
        assert size >= gui.SectionCanvas.S_DIM, 'scaling must not shrink text'
        assert rest == (['bold'] if bold else [])


def test_preview_font_helper_applies_the_scaling_factor(gui, monkeypatch):
    inst = gui.SectionCanvas.__new__(gui.SectionCanvas)

    class _Tracker:
        @staticmethod
        def get_widget_scaling(_widget):
            return 1.5

    monkeypatch.setattr(gui.ctk, 'ScalingTracker', _Tracker, raising=False)
    _, size = gui.SectionCanvas._font(inst, 10)
    assert size == 15


def test_tooltip_text_is_large_enough(gui):
    """The hover help is read at a glance, so it may not be smaller than the
    interface around it."""
    assert gui.Tip.SIZE >= 14, f'tooltip is {gui.Tip.SIZE} pt - too small'


def test_tooltip_font_follows_the_interface_scaling(gui, monkeypatch):
    """A tooltip is a bare tk.Toplevel, outside CustomTkinter's scaling."""
    class _Tracker:
        @staticmethod
        def get_widget_scaling(_widget):
            return 1.5

    monkeypatch.setattr(gui.ctk, 'ScalingTracker', _Tracker, raising=False)
    assert gui.scaled_font_size(None, 10) == 15


def test_preview_labels_are_large_enough(gui):
    """Every callout drawn on the preview canvas, at its declared size."""
    canvas = gui.SectionCanvas
    for name in ('S_DIM', 'S_DIM_SM', 'S_INFO', 'S_WI', 'S_WI_CONF'):
        assert getattr(canvas, name) >= 14, f'{name} is too small to read'


def test_preview_labels_grow_with_a_taller_pane(gui):
    """A preview shown in a tall pane scales its labels with the drawing."""
    canvas = gui.SectionCanvas
    inst = canvas.__new__(canvas)
    inst.winfo_height = lambda: canvas.CANVAS_REF_H * 3
    _, big = canvas._font(inst, 10)
    inst.winfo_height = lambda: canvas.CANVAS_REF_H
    _, ref = canvas._font(inst, 10)
    inst.winfo_height = lambda: canvas.CANVAS_REF_H // 4
    _, small = canvas._font(inst, 10)
    assert big > ref, 'a taller pane must grow the labels'
    assert big <= round(10 * canvas.CANVAS_ZOOM_MAX), 'the zoom must stay bounded'
    assert small == ref, 'a short pane must never shrink them'
