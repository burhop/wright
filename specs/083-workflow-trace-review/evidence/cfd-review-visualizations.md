# CFD review visualization evidence

Date: 2026-09-17

## Source and scope

The Raspberry Pi enclosure report uses two retained 2200 x 990 PNG figures:

- `raspberry-pi-enclosure-velocity-comparison.png`
- `raspberry-pi-enclosure-temperature-comparison.png`

They were rendered from the actual Variant A and Variant B VTK fields in
`cfd-fields.zip` for `raspberry-pi-enclosure-01/attempt-032`. The rendering
record identifies OpenFOAM 10 `chtMultiRegionFoam`, a horizontal slice at
`z = 22 mm`, and one shared scale per field. The figures are review-time
derivations, not original solver screenshots and not a new simulation.

The report retains and links both `cfd-fields.zip` and `cfd-comparison.json`.
It also preserves the recorded limits: steady-state convergence and engineering
validation were not claimed for this exploratory run.

## Presentation

- Both final enclosure concepts remain interactive offline STL views.
- The airflow and temperature comparisons appear as separate result figures
  with engineering captions.
- Expanding `Verification & results` shows both comparison thumbnails on the
  recorded CFD collection activity.
- Selecting a figure opens its full image, derivation statement, source evidence,
  visualization basis, and downloadable retained PNG.

## Verification

- 44 focused Python tests passed.
- Ruff checks and formatting passed.
- Prettier and `git diff --check` passed.
- The focused offline Playwright visual test passed.
- The all-30 offline report test passed with zero remote requests and page errors.
- Desktop output, expanded-process, and mobile screenshots were visually
  inspected under `/tmp/wright-083-cfd-visual-playwright/`.
