# CUMBIA_PY

Moment-Curvature, Force-Displacement and Interaction Analysis of Reinforced Concrete Members.

Based on [CUMBIA_PY by Luis Montejo](https://github.com/LuisMontejo/CUMBIA_PY) (MIT License).  
**Contact (original author):** luis.montejo@upr.edu

---

## Overview

CUMBIA is a comprehensive analytical tool for evaluating the monotonic behavior of reinforced concrete (RC) members with circular or rectangular cross-sections. The program performs rigorous moment-curvature analyses and computes the analytical force-displacement response, providing structural engineers and researchers with a clear evaluation of potential deformation limit states.

The original MATLAB algorithms (`CUMBIACIR.m` and `CUMBIARECT.m`) have been entirely refactored into Python (`CUMBIA_CIR.py` and `CUMBIA_RECT.py`), leveraging open-source libraries such as `numpy`, `pandas`, and `matplotlib`.

## Graphical User Interface

Version 0.3 introduces a complete GUI built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), launched via `main.py`.

<p align="center">
  <img src="logo.png" alt="CUMBIA_PY" width="120">
</p>

### Circular Section
<p align="center">
  <img src="screenshots/gui_circular.png" alt="Circular section tab" width="900">
</p>

### Rectangular Section
<p align="center">
  <img src="screenshots/gui_rectangular.png" alt="Rectangular section tab" width="900">
</p>

**Features:**
- Tabbed interface for circular and rectangular sections
- Interactive cross-section preview with live update
- MLR editor for rectangular sections (auto-generate or manual layer-by-layer input)
- Visual wi display showing both bar-to-bar gaps and Mander restrained-bar gaps
- Stirrup/crosstie editor with ncx, ncy controls
- Save/Load input parameters as JSON
- Automated output to user-chosen folder with PDF report auto-open
- Dark/Light theme toggle
- English/Italian language toggle (click **IT**/**EN** in the title bar; restart required)
- Tooltip help on every parameter

## Modifications from Original Code

This version includes bug fixes and enhancements documented in detail in [CHANGES.md](CHANGES.md). Summary:

### 1. Confinement Model Fix (CUMBIA_RECT.py)
The automatic `wi` calculation now correctly computes clear distances between **restrained bars only** (tied by stirrup corners or crossties), as required by the Mander confinement model. The original code computed distances between all peripheral bars regardless of restraint.

The calculation lives in a single place, `material_models.wi_mander()`, shared by the GUI, the section preview and the analysis script, so the three can no longer disagree. Script mode now defaults to `wi_input = [0]` (automatic), matching what the GUI computes for the same section.

### 2. Buckling Models Fix
All four models were verified against the original MATLAB release and the *CUMBIA Theory and User Guide*. Moyer-Kowalsky and Berry-Eberhard are faithful ports; the defects were in the two Goodnight models, which exist only in the Python port.

- **Goodnight et al., drift-based:** the aspect-ratio term used the full member length instead of the shear span, so a fixed-fixed column and the equivalent cantilever — the same physical column — returned drift limits differing by 67%. Now `LBE/H` (`LBE/D` for circular sections), consistent with Berry-Eberhard and the shear model. Cantilevers are unaffected.
- **Goodnight et al., both models:** fed `rho_s/2` instead of the volumetric transverse ratio. A single `TransvSteelRatioVolumetric` now feeds the Goodnight and Berry-Eberhard formulas alike. Circular sections were already correct.
- **Moyer & Kowalsky:** the growth strain now vanishes at curvature ductility 1 as the guide specifies, instead of following a line through the origin. The critical strain formula uses the extreme fibre bar diameter (`dbl_extreme`).
- **Applicability notes:** the report now flags a tie spacing outside the Moyer-Kowalsky calibration range, an allowable strain that turns negative, and the extrapolation involved in applying the Goodnight models to a rectangular core.

### 3. Theoretical Enhancements (from v0.2)
- **Modified Plastic-Hinge Method:** Goodnight et al. (2016) method with decoupled flexure and strain penetration components
- **Modern Bar Buckling Limits:** Goodnight et al. (2015) strain-based and drift-based models
- **Spiral Yielding Limit State:** automatic calculation for circular sections
- **P-Delta Effects:** dedicated toggle for approximate P-Delta correction
- **Scaled 2D Cross-Section Plotting**
- **Unified Multi-Page PDF Reports** with all figures and formatted summary
- **Native Excel Export** (`.xlsx`)

## Requirements

- Python 3.10+
- numpy
- pandas
- matplotlib
- openpyxl
- customtkinter

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode
```bash
python main.py
```

### Script Mode (no GUI)
Edit the input parameters directly in `CUMBIA_CIR.py` or `CUMBIA_RECT.py` and run:
```bash
python CUMBIA_CIR.py
python CUMBIA_RECT.py
```

## Output

Each analysis produces:
- **Excel workbook** (`_Results.xlsx`) with moment-curvature data, interaction diagram, and summary report
- **Multi-page PDF report** (`_Full_Report.pdf`) with all figures and formatted text
- **Individual PNG figures** (stress-strain, moment-curvature, force-displacement, buckling models, limit states, interaction diagram)

## Testing

The project ships a pytest suite covering the material models, the wi
confinement calculation, end-to-end regression of both engines, every option
the GUI exposes, and the translation layer.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The suite runs both analysis engines many times, so a full run takes a few
minutes. To run one layer only:

```bash
python -m pytest tests/test_material_models.py   # fast unit tests
python -m pytest tests/test_wi_consistency.py    # GUI vs script wi agreement
python -m pytest tests/test_regression_golden.py # numerical regression
```

`tests/test_regression_golden.py` compares full runs against reference results
recorded in `tests/golden/`. After an intentional change to the analysis,
re-record them and review the diff before committing:

```bash
CUMBIA_REGEN_GOLDEN=1 python -m pytest tests/test_regression_golden.py
```

The GUI-logic tests import `main.py` without a display: when Tk is unavailable
they substitute the headless stubs in `tests/_stubs.py`, so the suite runs on a
bare CI runner. Every push is tested on Python 3.10 and 3.12 by
`.github/workflows/tests.yml`.

## Building the Windows bundle

Releases are built by `.github/workflows/build-windows.yml` on a clean
`windows-latest` runner, not on a developer machine. Pushing a `v*` tag builds
the bundle, verifies it, and attaches the zip to the release; the workflow can
also be started by hand from the Actions tab (Run workflow) to produce a test
build without tagging.

Building on a runner is also the safer option for the maintainer: Python
embeds the absolute source path of every module in the compiled bytecode
(`co_filename`), and PyInstaller ships that bytecode. A build made under
`C:\Users\<name>\...` therefore carries that path — and the account name —
into every traceback a user might see. On a runner the embedded path is the
runner's own workspace.

To build locally anyway:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm CUMBIA_PY.spec
```

The result is a folder, `dist/CUMBIA_PY/`, containing `CUMBIA_PY.exe` and its
dependencies — zip that folder to distribute it. It is a portable bundle, not
an installer: users extract and run.

## License

MIT License — see [LICENSE](LICENSE) for details.

**Original analysis engine:** Luis Montejo  
**GUI, enhancements, and distribution:** Lorenzo Buratti
