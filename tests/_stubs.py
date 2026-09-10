"""Headless stubs for tkinter / customtkinter.

main.py builds its widget classes at import time, so importing it requires
tk.Canvas, ctk.CTkFrame and ctk.CTk to exist as classes. On a machine with a
real Tk (a developer box, or CI with python3-tk) the real modules are used and
these stubs stay out of the way. Everywhere else the stubs let the *pure*
logic in main.py — parameter schemas, validation, the wi calculation — be
imported and tested without a display.
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
    """Install stub tkinter/customtkinter if the real ones are unavailable.

    Returns True if stubs were installed, False if the real modules exist.
    """
    try:
        import tkinter  # noqa: F401
        import customtkinter  # noqa: F401
        return False
    except Exception:
        pass

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
