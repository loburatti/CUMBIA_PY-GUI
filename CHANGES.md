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
