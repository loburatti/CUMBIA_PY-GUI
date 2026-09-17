Corrections to the bar buckling models, verified against the original MATLAB release, and a recommended onset in the report.

## What changes in your results

**Analyses in double bending produce different buckling onsets.** Two of the four models were being fed the wrong quantities; the corrections move their predictions and, in some members, make a prediction appear where none was reported before. Single bending (cantilever) analyses are unaffected by the larger of the two fixes. Moment-curvature, the force-displacement backbone, plastic hinge lengths, shear capacity and the deformation limit states are untouched throughout — every fix below is confined to the buckling post-processing.

On the member that prompted this release — 350x350, L = 4000 in double bending, 3+2+3 D16, D8 ties at 200 mm, N = 500 kN — the displacement ductility at the onset of buckling moves like this:

| model | before | after |
|---|---|---|
| Moyer-Kowalsky | 1.07 | 1.20 |
| Goodnight drift-based | *off the curve* | 4.19 |
| Goodnight strain-based | 3.88 | 4.70 |
| Berry-Eberhard | 4.82 | 4.82 |

## Fixes

All four models were re-derived from the original MATLAB release and the *CUMBIA Theory and User Guide*. Moyer-Kowalsky and Berry-Eberhard turned out to be faithful ports — coefficients, signs and the use of the shear span all match. The defects were in the two Goodnight models, which exist only in the Python port and were never part of the peer-reviewed MATLAB release, plus one detail inherited from the MATLAB itself.

**The Goodnight drift model used the member length as its aspect ratio.** The aspect ratio in CUMBIA is the shear span over the depth; Berry-Eberhard uses it correctly two lines above, and the shear model halves the length in double bending. Only this line did not. The result was a member that contradicted itself: a fixed-fixed column of length L and the cantilever of length L/2 it is equivalent to — the same physical column, and drift ratio is the same quantity in both idealisations — returned 6.41 % and 3.84 %. Since the model was calibrated on cantilevers, the double-bending branch was brought back to the single-bending one. Cantilevers are unaffected, and because both scripts ship with single bending, no shipped example ever exercised the broken branch.

**Both Goodnight models were fed half the transverse reinforcement ratio.** Their `rho_s` is the volumetric ratio; the rectangular engine passed the average of the two directions, while Berry-Eberhard on the adjacent line spelled the same quantity correctly. One definition now feeds all three, so they cannot drift apart again. Circular sections were already correct.

**The Moyer-Kowalsky growth strain did not vanish at curvature ductility 1.** The Theory Guide requires zero there, interpolating linearly to its value at curvature ductility 4; the code followed a line through the origin instead, leaving a step and biasing the whole range in between — exactly where the crossing falls on poorly detailed sections. This is a deliberate departure from the MATLAB in favour of the documented model.

**Report units.** `Curvature at Buckling` was labelled `m` instead of `1/m`, and `Moment for Buckling` `kN` instead of `kN-m`, in the Moyer-Kowalsky and Berry-Eberhard blocks of both engines.

## Model applicability

The Moyer-Kowalsky critical strain collapses as the tie spacing grows — at `s/db = 12.5` it falls to 0.0054, predicting buckling almost at yield — and nothing in the report said so. The report now carries an applicability notes block, printed only when a note applies: a tie spacing outside the range the model was calibrated on, an allowable strain that turns negative, and, on rectangular sections, the extrapolation involved in applying a circular-column calibration to a rectangular core.

## Recommended onset and governing mechanism

The report listed the four models side by side and left the reader to choose. Each model that produces an onset is now classified against its own calibration — applicable, extrapolated, or excluded — and the lowest onset among those not excluded is highlighted as the recommended value.

Berry-Eberhard is the only model with a native rectangular calibration, so on a rectangular section the others are marked as extrapolated; on a circular section all three are native. Moyer-Kowalsky is excluded wherever `s/db > 8`.

A recommended onset means nothing on a member that fails in shear first, so the block also compares it against the shear failure displacement and the ultimate deformation capacity and names which of the three actually limits the member. When bar buckling is not the governing mechanism, the caveat is printed inside the highlighted box.

Neither the Theory Guide nor the source publications rank the models against each other, so this ranking is supplied by CUMBIA_PY as a decision aid and the report prints the rule in full. It is meant to be overridden where judgement requires. The figures are unchanged.

## Testing

The suite is now 171 tests, up from 152, running on Python 3.10 and 3.12 on every push. The nineteen new ones pin invariants rather than numbers: that the drift limit is the same whether a column is idealised as a cantilever or as a fixed-fixed member, that every model written in terms of `rho_s` is fed the same `rho_s`, that the growth strain matches the published interpolation, and that an excluded model never becomes the recommended value even when it is the lowest. Each was checked to fail when its fix is reverted.

The golden regression files record no buckling output, so none needed regenerating and the 152 previous tests pass unchanged.

## Download

The attached zip contains a standalone Windows build — no Python installation required. Extract and run `CUMBIA_PY.exe`. Windows SmartScreen will warn on first launch, as the build is not code-signed.

## From source

```bash
pip install -r requirements.txt
python main.py
```
