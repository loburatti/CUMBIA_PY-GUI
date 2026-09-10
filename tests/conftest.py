"""Shared fixtures for the CUMBIA_PY test suite.

The two analysis engines (CUMBIA_CIR.py / CUMBIA_RECT.py) are flat scripts,
not importable modules: they read their inputs from module-level assignments,
optionally overridden by a JSON file named in the CUMBIA_PARAMS environment
variable. That is exactly how the GUI drives them (see main.py::_run), so the
tests drive them the same way and assert on the resulting namespace.
"""
import json
import os
import sys
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'golden')

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault('MPLBACKEND', 'Agg')

SCRIPTS = {
    'circular': 'CUMBIA_CIR.py',
    'rectangular': 'CUMBIA_RECT.py',
}


def run_engine(section, params=None, workdir=None):
    """Execute an analysis engine and return its final global namespace.

    Mirrors main.py::_run: parameters are injected through CUMBIA_PARAMS,
    the working directory is switched so output files land in `workdir`.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    script_path = os.path.join(REPO_ROOT, SCRIPTS[section])
    cleanup_dir = None
    if workdir is None:
        cleanup_dir = tempfile.mkdtemp(prefix='cumbia_test_')
        workdir = cleanup_dir

    param_path = None
    if params is not None:
        fd, param_path = tempfile.mkstemp(suffix='.json', prefix='cumbia_params_')
        with os.fdopen(fd, 'w') as fh:
            json.dump(params, fh)

    original_dir = os.getcwd()
    original_env = os.environ.get('CUMBIA_PARAMS')
    try:
        os.chdir(workdir)
        if param_path:
            os.environ['CUMBIA_PARAMS'] = param_path
        else:
            os.environ.pop('CUMBIA_PARAMS', None)

        with open(script_path, encoding='utf-8') as fh:
            code = fh.read()
        ns = {'__name__': '__main__', '__file__': script_path}
        exec(compile(code, script_path, 'exec'), ns)
        return ns
    finally:
        plt.close('all')
        os.chdir(original_dir)
        if original_env is None:
            os.environ.pop('CUMBIA_PARAMS', None)
        else:
            os.environ['CUMBIA_PARAMS'] = original_env
        if param_path:
            try:
                os.remove(param_path)
            except OSError:
                pass
        if cleanup_dir:
            import shutil
            shutil.rmtree(cleanup_dir, ignore_errors=True)


@pytest.fixture(scope='session')
def cir_default():
    """Circular engine run with the repository default inputs."""
    return run_engine('circular')


@pytest.fixture(scope='session')
def rect_default():
    """Rectangular engine run with the repository default inputs."""
    return run_engine('rectangular')


@pytest.fixture(scope='session')
def gui():
    """The GUI module, imported headlessly via stubs when Tk is absent."""
    from tests import _stubs
    _stubs.install()
    import main
    return main


def regen_requested():
    """True when golden files should be rewritten instead of compared."""
    return os.environ.get('CUMBIA_REGEN_GOLDEN') == '1'
