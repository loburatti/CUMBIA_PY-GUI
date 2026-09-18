The confinement clear distances are now read off the bar layout instead of the declared leg count, the section is checked for physical consistency before it is analysed, and a non-uniform bar layout can be described.

## What changes in your results

**Rectangular sections only, and only through Mander's confinement.** `ncx` and `ncy` are untouched — they state the transverse steel area, which a leg contributes whether or not it hooks a longitudinal bar — so `rho_x`, `rho_y`, `rho_s` and all four buckling models are fed exactly what they were fed before. Moment-curvature, the force-displacement backbone, plastic hinge lengths, shear capacity and the deformation limit states are not touched at all. What moves is `sum(wi^2)`, and through it `ke`, `f'cc` and `ecu`.

**A section detailed consistently is unchanged.** Where every declared leg can actually be placed — uniformly spaced bars, matching counts on opposite faces — the new calculation reproduces the old one exactly. The member the previous release was built around (350x350, L = 4000 in double bending, 3+2+3 D16, D8 ties at 200 mm, N = 500 kN) with `ncx = 3` and `ncy = 3` returns the same numbers to the last digit: three reinforcement layers give three restrained bars per side face, three bars per flange give three on the top and bottom, and every leg has a bar to hook.

Declare `ncx = 4` on those same bars and the previous release credited the section with confinement it did not have:

| same column, `ncx = 4` | before | after |
|---|---|---|
| nominal moment | 161.58 kN-m | 161.56 kN-m |
| displacement ductility | 6.35 | 5.83 |
| ultimate displacement | 0.2870 m | 0.2634 m |

`sum(wi^2)` for that section is 98568 mm², whatever leg count is declared, because the bars cannot host more than three restrained per face. The old calculation returned 77575 mm² at `ncx = 4` and 56581 mm² at `ncx = ncy = 4` — the more legs you claimed, the more confinement you were given, with no bar to hang them on.

Of the recorded regression cases, `rectangular_default` and both circular ones are unchanged to the last digit. `rectangular_crossties`, which declares four legs per direction on faces sharing a single intermediate bar position, moves -0.20 % on the nominal moment and -6.31 % on displacement ductility. Every departure is in the same direction: a larger `sum(wi^2)`, that is less confinement.

## Where the confinement was overstated

Release 0.3 made the automatic `wi` depend on the number of transverse legs rather than on every peripheral bar, which was the right correction: Mander's effectiveness factor sums the clear distances between *restrained* bars, not between all of them. But it then assumed those restrained bars existed, evenly spread over the net core, whichever section had been typed in. The leg count and the bar layout never spoke to each other.

The layout that exposed it has two bars on the top face and three on the bottom. Analysed with `ncy = 3`, the report gave four gaps of 111 mm. A crosstie is a straight bar: it can only hook where both faces it spans carry a bar at the same position, so on that section the third leg cannot be placed at all and the real geometry is a single 238 mm gap on each of those faces. Mander's first factor `1 - sum(wi^2)/(6*bc*dc)` falls from 0.838 to 0.686.

`section_geometry.py` now builds that geometry from the reinforcement matrix itself: where each bar sits, which face it belongs to, and which of them a leg can hold. The perimeter hoop restrains the four corners; each intermediate leg is placed on the bar nearest its ideal position among those that can receive it, and a leg with nowhere to go is not placed. `wi` is then the clear distance between consecutive *restrained* bars along each face, so an unrestrained bar is spanned rather than counted — which is what arching between laterally supported bars means.

What the layout can hold is reported next to what was declared, in the preview and in the report, never substituted for it.

## Describing a real bar layout

The reinforcement table takes an optional **x positions** column (`50; 175; 300`), and `CUMBIA_RECT.py` an optional `custom_bar_x`, one entry per layer and `None` where the bars are evenly spaced. That is what makes a non-uniform layout describable: corner bars of one diameter and intermediate bars of another, or a bar placed specifically to receive a crosstie.

Bar positions do not enter the moment-curvature analysis, which reads the layer depth, bar count and diameter only. They decide where a crosstie can hook, and so the `wi`.

The preview draws the legs where they are actually placed, on the bars they hook, instead of at a fraction of the core. A ring marks each restrained bar. Red arrows outside a face are the `wi` that enter `ke`; amber arrows inside a face appear only where a bar is free, so the drawing shows both the bar spacing and the longer distance the confinement has to span.

## Section consistency checks

The engine runs on almost anything: it reads numbers, not a section. The inputs are now read as a detailer would read them, live under the section editor and in the report under *Section consistency checks*, so a run from a script carries them too.

**Errors** block a run and name what is wrong: non-positive dimensions, a cover that leaves no core, a tie spacing not larger than the tie itself, bars outside the cover, bars overlapping in a layer, a single reinforcement layer, and a `sum(wi^2)` that drives Mander's effectiveness factor to zero or below.

**Warnings** cover a section that can be built but is not the one the numbers describe: legs the bar layout cannot hold, clear spacing too tight to place concrete through, a tie spacing beyond the `s <= 6 db` usually required in a plastic hinge region, a layer with nothing against a side face, confinement already eaten by the gaps, and `wi` entered by hand that disagrees with the layout drawn.

**Advice** points at crossties the layout would allow and at a longitudinal steel ratio outside the range columns are usually detailed in.

Nothing is corrected automatically. A check reports, the engineer decides, and the analysis runs on exactly what was entered.

## Readability

The preview callouts and the hover tooltips were hard to read on a large display. The five canvas label sizes go up, the tooltip to 16 pt, and both now go through one helper that applies the interface scaling factor — a `tk.Canvas` draws its own text and a tooltip is a bare `Toplevel`, so neither ever received it. A preview shown in a tall pane scales its callouts with the drawing.

One defect the larger labels made obvious is fixed with them: a layer typed into the reinforcement table out of depth order was drawn as if it were the top or bottom one, producing a negative clear distance between layers and picking up the wrong extreme-fibre bar diameter.

## Testing

The suite is 270 tests, up from 171, running on Python 3.10 and 3.12 on every push. The new ones pin properties rather than numbers: that the restraint geometry reproduces the uniform-spacing formula wherever both descriptions of a section are true at once, that a leg the layout cannot host never improves the confinement, that a crosstie is drawn on a bar or not drawn at all, and that every consistency check is reachable from a section written for it and sayable in both interface languages.

`tests/golden/rectangular_crossties.json` was re-recorded; its diff is the table above. The other three golden files are untouched.

## Download

The attached zip contains a standalone Windows build — no Python installation required. Extract and run `CUMBIA_PY.exe`. Windows SmartScreen will warn on first launch, as the build is not code-signed.

## From source

```bash
pip install -r requirements.txt
python main.py
```
