"""Headless stubs for tkinter / customtkinter.

main.py builds its widget classes at import time, so importing it requires
tk.Canvas, ctk.CTkFrame and ctk.CTk to exist as classes.

The stubs are installed unconditionally, replacing a real Tk if one is
present. Importable is NOT the same as usable: on a GitHub runner tkinter
imports perfectly well but has no display, so the first tk.StringVar() raises
"Too early to create variable: no default root window". Choosing the stubs
only when the import fails therefore behaves differently on a developer box,
on CI, and in a bare container. Forcing them makes the suite deterministic
everywhere — these tests target the pure logic (schemas, validation, the wi
calculation), never Tk itself.
"""
import sys
import types


class _Var:
    """Stand-in for tk.StringVar / tk.BooleanVar."""

    def __init__(self, master=None, value=None, **kw):
        self._value = '' if value is None else value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class _Widget:
    """Accepts any constructor args and any attribute access."""

    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, name):
        def _noop(*a, **kw):
            return None
        return _noop


def _make_module(name, attrs, widget_names):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    for wname in widget_names:
        setattr(mod, wname, type(wname, (_Widget,), {}))
    return mod


def install():
    """Install the stub tkinter/customtkinter, replacing any real ones.

    Always returns True. Any already-imported real module is dropped from
    sys.modules first, along with `main`, so main.py is re-imported against
    the stubs rather than keeping references to real Tk classes.
    """
    for name in ('main', 'customtkinter', 'tkinter.filedialog',
                 'tkinter.messagebox', 'tkinter'):
        sys.modules.pop(name, None)

    tk = _make_module(
        'tkinter',
        {'StringVar': _Var, 'BooleanVar': _Var, 'IntVar': _Var,
         'DoubleVar': _Var, 'TclError': Exception},
        ['Canvas', 'Frame', 'Toplevel', 'Tk', 'Label', 'Entry', 'Widget'],
    )
    messagebox = _make_module(
        'tkinter.messagebox',
        {'showerror': lambda *a, **kw: None,
         'showinfo': lambda *a, **kw: None,
         'showwarning': lambda *a, **kw: None,
         'askyesno': lambda *a, **kw: True},
        [],
    )
    tk.messagebox = messagebox
    filedialog = _make_module(
        'tkinter.filedialog',
        {'askopenfilename': lambda *a, **kw: '',
         'askdirectory': lambda *a, **kw: ''},
        [],
    )
    tk.filedialog = filedialog

    ctk = _make_module(
        'customtkinter',
        {'StringVar': _Var, 'BooleanVar': _Var, 'IntVar': _Var,
         'DoubleVar': _Var,
         'set_appearance_mode': lambda *a, **kw: None,
         'set_default_color_theme': lambda *a, **kw: None,
         'get_appearance_mode': lambda: 'Dark',
         'filedialog': filedialog},
        ['CTk', 'CTkFrame', 'CTkLabel', 'CTkButton', 'CTkEntry', 'CTkSwitch',
         'CTkCanvas', 'CTkToplevel', 'CTkScrollableFrame', 'CTkTabview',
         'CTkComboBox', 'CTkOptionMenu', 'CTkCheckBox', 'CTkImage',
         'CTkInputDialog', 'CTkFont', 'CTkTextbox', 'CTkSegmentedButton'],
    )

    sys.modules['tkinter'] = tk
    sys.modules['tkinter.messagebox'] = messagebox
    sys.modules['tkinter.filedialog'] = filedialog
    sys.modules['customtkinter'] = ctk
    return True
