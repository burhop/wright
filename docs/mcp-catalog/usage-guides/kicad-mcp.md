# KiCad MCP: native board reference inspection

Observed 11 October 2026: independent [blwfish/kicad-mcp](https://github.com/blwfish/kicad-mcp),
version 0.18.1, source commit `f754c12e10210a0d40345a06050aae47191d3999`.
Qualified through Wright's authenticated gateway to the isolated
`wright-stevecad-kicad-001` container, KiCad 9.0.2, Python 3.13.5, network disabled.
This is selected-provider evidence, not qualification of every catalog recipe or
host-native installation. No KiCad dependencies were added to Wright's base image.

## Verified engineering contribution

Read the official Raspberry Pi CM5 IO Board revision-2 native PCB to obtain
mounting-hole locations and connector references for a stationary robot
electronics bay. The manufacturer archive and native PCB hashes remain in
`artifacts/stevecad-demonstrations/robot-hardware/references/manifest.json` and the
hardware-reference evidence. Keep these purchased board references separate
from printed parts. The user's physical carrier revision remains unspecified.

1. Inspect the selected provider's actual tool schemas and `usage_guide` output.
   Setup/provenance and selected tools are retained under
   `artifacts/stevecad-demonstrations/qualification/kicad-v0181/`.
2. Place the unmodified manufacturer PCB in the mounted workspace. Native
   Windows paths do not resolve inside the provider container. The verified path
   is `/workspace/hardware-reference/cm5io-rev2/CM5IO.kicad_pcb`.
3. Call `pcb(operation="load", pcb_path=...)`. The real receipt reports `status:
   ok`, 79 footprints and 4670 tracks. This establishes parsing, not electrical
   correctness, a fabrication-ready board or successful CAD export.
4. Call `pcb(operation="get_pad_positions", pcb_path=..., reference="H1")`,
   similarly for H6, H7 and H8. Preserve exact native XY measurements.

| Reference | Native PCB XY, mm | CAD local XY, mm |
|---|---|---|
| H1 | 90, 152 | 11, 8 |
| H6 | 211.5, 83 | 132.5, 77 |
| H7 | 90, 83 | 11, 77 |
| H8 | 211.5, 152 | 132.5, 8 |

The coordinate transform is `X = pcbX - 79`, `Y = 160 - pcbY` for the
160 × 90 mm board outline. The outline comes from passive inspection of the
native Edge.Cuts records; pad coordinates come from actual MCP responses.
`get_pad_positions` does not return drill diameters. The footprint's 2.7 mm
name alone is not a measured diameter. Verify the native drill field or actual
imported geometry before accepting dependent fastener fit.

Read-only receipts:
`artifacts/stevecad-demonstrations/robot-hardware/kicad-reference/cm5io-pcb-load-002.json`
and `cm5io-pad-{h1,h6,h7,h8}.json`. Changing the board/profile invalidates dependent
mounting coordinates, fits and downstream review.

## Observed limitations and bounded recovery

Transport success does not establish backend success. Inspect returned `status`
and errors. A Windows-path attempt returned a backend path error despite
`isError: false`; the declared mounted Linux path succeeded.

`get_constraints` failed on this board because its drawing iterator called
`GetStart` on a `PCB_TARGET`, which lacks that method. The receipt is retained;
this is a suspected provider compatibility defect, not a confirmed reported bug.
Do not modify the manufacturer board, remove its target or silently patch the
provider to make the original observation appear successful. A minimal owned
reproduction and current-contract check are required before an upstream report.
No issue has been submitted.

This selected provider's `export` operations are Gerbers, BOM CSV and thumbnail.
No STEP-export operation was discovered. Do not invent one or describe a local
CLI export as an MCP result. Use a declared reference model/envelope with its
limitations when mechanical export is unavailable. Electrical checking,
fabrication exports and physical connector fit remain unverified here.

Preserve manufacturer attribution/terms. Store exact source hashes and redacted
receipts; do not place gateway credentials in scripts or shared artifacts.
