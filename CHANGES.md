# CUMBIA_PY 0.3 — Changes from original code

This version is derived from [CUMBIA_PY by Luis Montejo](https://github.com/LuisMontejo/CUMBIA_PY), released under the MIT License.

Below is a summary of the modifications introduced by Lorenzo Buratti.

---

## 1. Confinement model: wi calculation (CUMBIA_RECT.py)

**Problem:** The original automatic wi calculation computed clear distances between *all* peripheral longitudinal bars, regardless of whether they were actually restrained by transverse reinforcement. This is inconsistent with the Mander confinement model, which requires wi values between *restrained* bars only (i.e., those tied by stirrup corners or crossties).

**Fix:** The auto-calculation now uses `ncx` and `ncy` (number of stirrup legs) to determine how many bars are restrained on each face. Clear distances are computed between restrained bars only, uniformly distributed across the net width (`Bnet = B - 2*clb`) and net height (`Hnet = H - 2*clb`).

**Files changed:** `CUMBIA_RECT.py` — wi calculation block (auto mode when `wi_input = [0]`).

---

## 2. Buckling models: correct variable usage (CUMBIA_RECT.py)

**Problem:** Two buckling prediction models used incorrect variables:

- **Goodnight et al. (2015)** — Both the strain-based and drift-based formulas used `rho_y` (transverse steel ratio in Y-direction only) instead of the average transverse steel ratio across both directions.
- **Moyer & Kowalsky** — The formula used `dbl_max` (maximum bar diameter in the section) instead of the bar diameter at the extreme fiber, which is the bar most susceptible to buckling.

**Fix:**
- Goodnight strain model: `rho_y` replaced with `TransvSteelRatioAverage` in the `es_bb` formula.
- Goodnight drift model: `rho_y` replaced with `TransvSteelRatioAverage` in the `drift_bb_pct` formula.
- Moyer & Kowalsky: `dbl_max` replaced with `dbl_extreme` (= `min(dbl_layer[0], dbl_layer[-1])`) in the `escc` and `rotb` formulas.
- Added `dbl_extreme` variable: the smaller diameter between top and bottom layer bars.

**Files changed:** `CUMBIA_RECT.py` — buckling assessment section.

---

## 3. Graphical User Interface (main.py — new file)

A complete GUI built with CustomTkinter, providing:

- **Tabbed interface** for circular and rectangular sections
- **Interactive section preview** with live update as parameters change
- **MLR editor** for rectangular sections (auto-generate or manual layer-by-layer input)
- **Visual wi display** showing both bar-to-bar gaps and Mander restrained-bar gaps
- **Stirrup/crosstie editor** with ncx, ncy controls
- **Save/Load** of input parameters as JSON
- **Automatic output** to user-chosen folder with PDF report auto-open
- **Dark/Light theme** toggle
- **About dialog** with credits and link to original repository
- **Tooltip help** on every parameter

**Files added:** `main.py`

---

## 4. PyInstaller packaging

The application is bundled as a standalone Windows executable via PyInstaller, including all dependencies (numpy, scipy, pandas, matplotlib, customtkinter, openpyxl) and data files (analysis scripts, logo, user guide, license).

**Files added:** `CUMBIA_PY.spec`

---

## 5. Bug fixes and test suite (0.3.1)

### 5.1 Circular section crashed with `interaction = 'n'`

**Problem:** In `CUMBIA_CIR.py` the variable `PTid` (tension yield load) is
only defined inside the `if interaction.lower() == 'y':` block, but the summary
report referenced it unconditionally. Running a circular section with the
interaction diagram disabled therefore failed with
`NameError: name 'PTid' is not defined` — after the whole analysis had already
been computed. `CUMBIA_RECT.py` already guarded the same block correctly.

**Fix:** The `Tension Yield` / `Compression Yield` / `Moment Yield` report lines
are now inside the same `interaction == 'y'` guard used by `CUMBIA_RECT.py`.
Output for `interaction = 'y'` is unchanged.

**Files changed:** `CUMBIA_CIR.py`.

### 5.2 PDF report could not be opened outside Windows

**Problem:** `main.py` used `os.startfile()`, which exists only on Windows. On
macOS and Linux a successful analysis ended with an `AttributeError` dialog.

**Fix:** New `open_with_default_app()` helper dispatches on `sys.platform`
(`os.startfile` / `open` / `xdg-open`) and never raises, so a missing viewer
can no longer mask a successful run.

**Files changed:** `main.py`.

### 5.3 Invalid escape sequences in plot labels

**Problem:** Six matplotlib labels used `'$\mu$'` in non-raw strings, emitting
`DeprecationWarning: invalid escape sequence` and heading for a `SyntaxError`
in a future Python release.

**Fix:** Those labels are now raw strings.

**Files changed:** `CUMBIA_CIR.py`, `CUMBIA_RECT.py`.

### 5.4 Input validation and untranslated strings

**Problem:** A malformed number in a GUI field was silently kept as a string
and surfaced much later as an obscure numpy error naming nothing the user could
recognise. Several UI strings (including a hardcoded Italian `wi (manuale)`)
bypassed the translation layer.

**Fix:** `_collect_params` now parses every field the schema declares numeric
and raises an error naming the offending field and its value; the numeric key
set is derived from the schema itself so it cannot drift from the form. All
remaining user-facing strings go through `T()`, with 14 new keys in both
languages.

**Files changed:** `main.py`, `i18n.py`.

### 5.5 Test suite

**Added:** a pytest suite (115 tests) under `tests/`, plus `pytest.ini`,
`requirements-dev.txt` and a GitHub Actions workflow running on Python 3.10
and 3.12.

| File | Covers |
|------|--------|
| `test_material_models.py` | branch behaviour of each stress-strain law, Mander confinement algebra, error paths |
| `test_wi_consistency.py` | the GUI and the engine must compute identical wi — the logic is duplicated in both |
| `test_regression_golden.py` | full-run regression against recorded results in `tests/golden/` |
| `test_parametric_smoke.py` | every material model, bending mode, hinge method, P-Delta and interaction option the GUI offers |
| `test_gui_and_i18n.py` | translation parity, schema integrity, input validation, Save/Load round-trip |

The GUI tests import `main.py` headlessly through `tests/_stubs.py`, so no
display or Tk installation is required.

---

## 6. wi calculation: a single implementation (0.3.2)

### 6.1 The formula was written three times

**Problem:** The Mander restrained-bar spacing was computed by three separate
copies of the same formula:

* `main.py::CumbiaApp._compute_wi_mander` — the values the GUI sends to the engine;
* `main.py::SectionCanvas._draw_rect` — the values drawn as red arrows in the
  section preview;
* `CUMBIA_RECT.py` — the `wi_input == [0]` automatic branch used in script mode.

They agreed numerically, but nothing enforced it: an edit to any one of them
would have made the GUI display, the GUI analysis and the script analysis
disagree about the same section, silently.

**Fix:** The calculation now lives once, in `material_models.wi_mander()`, and
all three call it. Verified equivalent to the previous code over 576
combinations of layout, geometry and leg count — the numbers are unchanged.
`material_models.py` was chosen as its home because both engines already
import it and it is already listed in `CUMBIA_PY.spec`.

The shared function also sorts the layer matrix by depth, which the engine did
and the GUI did not. For an ordered MLR — everything the GUI itself produces —
this changes nothing.

**Files changed:** `material_models.py`, `main.py`, `CUMBIA_RECT.py`.

### 6.2 Stale wi_input default in script mode

**Problem:** `CUMBIA_RECT.py` shipped `wi_input = [272, 272, 172, 172]` while
its default section is B=300, H=400, clb=40. The net core width is 220 mm, so
272 mm is not a distance that fits in the section. The values were the
automatic ones, rounded, with the B-face and H-face entries swapped. Because
ke depends only on sum(wi**2) the swap was harmless, but the rounding meant
script mode and GUI mode analysed the same section with different confinement.

**Fix:** The default is now `wi_input = [0]`, which selects the automatic
calculation — the same values the GUI computes.

**Effect on the shipped example** (rectangular defaults):

| | old (`[272, 272, 172, 172]`) | new (auto) |
|---|---|---|
| wi [mm] | 272, 272, 172, 172 | 169.2, 169.2, 269.2, 269.2 |
| Mn [kN-m] | 404.389 | 404.446 |
| ecu | 0.03330 | 0.03320 |
| Displacement ductility | 13.53 | 12.90 |

Users who supply their own `wi_input` are unaffected, as is every GUI run: the
GUI has always passed wi explicitly.

**Files changed:** `CUMBIA_RECT.py`, `tests/golden/rectangular_default.json`.

### 6.3 Tests

`tests/test_wi_consistency.py` gained guards that the GUI, the engine and the
drawing all resolve to `material_models.wi_mander`, that the formula appears in
no other source file, that the GUI returns JSON-serialisable floats, and that
the engine default really does take the automatic path.

---

## 7. Graphical fixes (0.3.3)

### 7.1 Force axis left unlabelled under high axial load

**Problem:** The force-displacement figures label the left axis in kN and the
right axis as F/P, and forced both onto shared tick positions using a step
hardcoded at 0.4 in ratio units:

```python
fp_ratio_max = int(np.ceil(ylim / abs(P_kN) * 10))
desired_fp_ticks = np.array([i/10 for i in range(0, fp_ratio_max + 1, 4)])
```

With `fp_ratio_max <= 3` that range yields `[0]` alone, so every tick above
the origin fell outside the plotted range and the axis came out blank apart
from the zero. The condition is `ylim <= 0.3 * |P_kN|`: any member whose axial
load exceeds roughly 3.3 times the force scale. It affected both engines
equally — it was reported on a circular section only because the repository
defaults (P = 2000 kN) happen to fall on the working side of the threshold.

**Fix:** New `plot_utils.ratio_ticks()` picks a round step (1, 2, 2.5 or 5
times a power of ten) sized so that four to six ticks land inside the axis,
whatever the ratio between the force scale and the axial load. Both engines
call it, so the logic is not duplicated.

**Files changed:** `plot_utils.py` (new), `CUMBIA_CIR.py`, `CUMBIA_RECT.py`,
`CUMBIA_PY.spec` (the new module must be bundled, since the engines are
executed from the bundle), `.github/workflows/build-windows.yml`.

### 7.2 Unreadable labels in the section preview

**Problem:** The dimension callouts and the wi values were drawn at 7-8 pt,
too small to read on a large display.

**Fix:** Raised to 9-10 pt and collected into named constants on
`SectionCanvas` (`F_DIM`, `F_DIM_SM`, `F_INFO`, `F_WI`, `F_WI_CONF`) so the
sizes can be adjusted in one place instead of at eleven call sites.

**Files changed:** `main.py`.

### 7.3 Unreadable parameter tooltips

**Problem:** The hover help was 9 pt, wrapped at 320 px.

**Fix:** 11 pt, wrapped at 420 px, with a little more padding.

**Files changed:** `main.py`.

### 7.4 Tests

`tests/test_plot_axes.py` covers the tick helper and, more usefully, runs the
engines at several axial loads and asserts the force axis of the real figures
carries more than one tick, with the left and right axes aligned. Verified to
fail against the previous formula.
