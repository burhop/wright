# Native CAD sections

Use this optional diagnostic after an exact CAD export to inspect profiles,
cross-sections, openings and unintended waves. It intersects the native BRep
with declared planes, saves the resulting edge BReps, and plots sampled curves.
It does not intersect a display mesh, modify the source, run another workflow,
choose corrections or approve an engineering result.

The existing Wright runtime remains the owner of accepted process execution,
questions, reviews, evidence and recovery. This is a local example command for a
declared measurement step, not an installed MCP provider or a complete automatic
reconstruction loop. Source hashes, plane definitions and face selections are
dependencies: changing them requires fresh evidence. Portable workflows need the
reader/plotting dependencies and referenced inputs; this example transfers no
live state or authority. The common result view remains usable without a custom UI.

## Input and execution

The manifest supplies all paths, identities, face selections and geometry:

```json
{
  "artifacts": [
    {"id": "candidate", "path": "candidate.step", "sha256": "REPLACE_WITH_EXACT_SHA256"}
  ],
  "sections": [
    {"id": "center", "origin_mm": [0, 0, 0], "normal": [0, 1, 0], "plot_axes": [0, 2]}
  ],
  "samples_per_edge": 33
}
```

Optional `face_indices` are zero-based native import indices. Omit them to use the
whole shape. Paths resolve relative to the manifest. Section locations are
diagnostic choices, not newly measured product dimensions. Use unique IDs and
finite vectors; the output directory must not exist and its parent must exist.

```text
python section_diagnostic.py --input manifest.json --output fresh-evidence
python -m unittest -v test_section_diagnostic.py
```

Qualified locally with Python3.13.5, CadQuery2.8.0/OCP and Matplotlib3.10.8. Use an
isolated environment; configure `MPLCONFIGDIR` and the test temporary directory
inside the chosen local state directory when the host restricts cache/temp writes.
No dependencies are installed by the command. Missing native dependencies prevent
startup; unavailable plotting or failed measurements are explicit incomplete
results. Exit0 means diagnostics completed, not engineering acceptance; exit1
means a persisted incomplete diagnostic, and exit2 is a CLI/output failure.

## Interpretation

The report separates exact source byte identity, derived native section curves,
kernel-reported measurements and finite sampled displays. Each plotted edge uses
the manifest sampling count; edges are not joined across gaps. Empty intersections
are recorded as empty. Failed samples retain unavailable values and errors.
Line segments in the PNG are a display approximation, not a certified continuous
distance or extrema bound. Source units are not independently verified; reported
coordinates use the CAD reader's millimetre convention and normal STEP unit
conversion. No extra scale alignment, fitting, healing or tolerance changes occur.

A valid single face can still have a poor shape. The Windows pilot's continuous
windshield trial was native-valid but showed large waves in independent sections;
it was not substituted for the preserved model. The same helper recovered the
existing qualified pocket fixture's native center-section floor (12mm span,
Z8mm,2mm depth), exterior section and empty outside plane. These are different
existing-workflow artifact compatibility checks, not new physical accuracy or
end-to-end workflow acceptance claims. Analytic box/open-face controls exercise
native intersections, edge serialization, sampling, wrong hashes and no-overwrite.
See `provenance.json` for exact source identities and retained pilot evidence.
