Maintenance release: bug fixes, a test suite, and reproducible Windows builds.

## Fixes

**Circular sections crashed with M-P interaction disabled.** Selecting `interaction = n` failed with `NameError: PTid` *after* the whole analysis had been computed. The variable exists only when the interaction diagram runs, but the summary report referenced it unconditionally.

**The force axis could come out blank.** In the force-displacement figures the tick step was fixed at 0.4·|P|, so whenever the axial load exceeded roughly 3.3 times the force scale every tick above zero fell outside the plotted range and the axis rendered with nothing but the origin. The step now adapts so four to six ticks always land inside the axis.

**The PDF report could not be opened outside Windows.** `os.startfile` exists only on Windows, so a successful run ended in an error dialog on macOS and Linux.

**Invalid escape sequences** in six matplotlib labels — a warning today, a syntax error in a future Python.

**Unreadable preview text.** Dimension callouts and wi values were drawn at 7-8 pt and did not follow the interface scaling, so on a scaled display they were smaller than everything else on screen. Sizes raised and now scaled with the rest of the UI; tooltips enlarged too.

**Input validation.** A malformed number in a form field was kept as text and surfaced much later as an obscure numpy error. Bad input is now reported immediately, naming the field and the value.

**Untranslated strings**, including an Italian label shown in the English interface.

## Confinement calculation

The Mander restrained-bar spacing `wi` was implemented three times — the values sent to the analysis, the arrows in the section preview, and the automatic branch of the rectangular engine. They agreed, but nothing enforced it. The formula now lives in one place, verified equivalent to the previous code over 576 combinations of layout, geometry and leg count, so results are unchanged.

Script mode also shipped a default `wi_input` that did not fit inside its own default section. It now selects the automatic calculation, matching what the GUI computes for the same member. Users supplying their own `wi_input` are unaffected, as is every GUI run.

## Testing and builds

The project now has a test suite — 152 tests covering the material models, the confinement calculation, full-run regression against recorded results, every option the interface offers, and the translation layer. It runs on Python 3.10 and 3.12 on every push.

Windows packages are now built by GitHub Actions on a clean runner rather than on a developer machine, which also keeps local paths out of the published binary.

## Download

The attached zip contains a standalone Windows build — no Python installation required. Extract and run `CUMBIA_PY.exe`. Windows SmartScreen will warn on first launch, as the build is not code-signed.

## From source

```bash
pip install -r requirements.txt
python main.py
```
