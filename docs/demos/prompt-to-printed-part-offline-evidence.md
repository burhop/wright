# Prompt to printed part: isolated offline evidence

Recorded 2026-09-24/25 on `codex/prompt-to-3d-printed-part-demo`. This is a
source-checkout diagnostic, separate from the 30-example generation campaign.
The Bambu P1S was not queried, connected to, or used.

## What ran

- Workspace: `C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/wright-print-demo-workspaces/offline-part-run`
- Wright run: `34662b2e01054050a96612e8d38fe0a7`, saved source `workflows/offline-tool-chain-75805aefad34.workflow.wflow`, status `completed`.
- The isolated diagnostic used an explicitly authored 50 mm overhanging wall hook through the guarded `blender-mcp-ahujasid/execute_blender_code` tool. It then ran `wright-printed-part-mesh-repair/repair_model_file` and `wright-printed-part-slicer/slice_model_file` in the ordinary Wright workflow executor. This proves the engineering tool chain and artifact handoffs. It does **not** prove that the unavailable model translated a user prompt or image into geometry.
- The run record under `runs/offline-tool-chain-75805aefad34/20260925T004019Z-04bc22a8a971.json` records the source STL digest on the repair step and the repaired STL digest on the slicer step, each tied to the producer's named output port. The fixed wrappers independently confined those file paths to the same attempt.

Artifacts under `campaign/printed-replacement-part-01/demo-75805aefad34/artifacts/` in that workspace:

| Artifact | Observed result |
| --- | --- |
| `source_mesh.stl` | 1,784 bytes; 34 triangles |
| `repaired_mesh.stl` | 1,784 bytes; 34 triangles; same SHA-256 as source after the fixed repair checks |
| `mesh-preview.png` | 542,079 bytes; actual Blender geometry preview |
| `slice_package.gcode.3mf` | 697,676 bytes; SHA-256 `8b87f6b87b5d4510e23b24a3def25aa93fdd8e6f18c7720f0a594308c3ca2cee`; ZIP member `Metadata/plate_1.gcode` is 2,736,836 bytes |
| `support-preview.svg` | 927,162 bytes; actual G-code projection |
| `slice-evidence.json` | `simulation=false`, `exit_code=0`, 21,535 positive-extrusion moves, 6,551 support moves, supports enabled, printer connected false |
| `machine-profile.json`, `filament-profile.json`, `process-profile.json` | Actual resolved P1S 0.4 mm, PETG HF, and supported slicing profiles |

The served UI was entered through the workspace **Workflows** control. Headless
Chromium loaded the actual repaired STL into a rotatable canvas, loaded and
zoomed the actual support SVG, exposed the package download, and showed
**Print on P1S** disabled. There were no page errors. Screenshot:
`.local-run/print-demo-offline/review.png`. The browser check substituted the
completed diagnostic run response at the prepare/run HTTP boundary because
the model-backed user flow is unavailable; file downloads and previews came
from Wright's real workspace API. The review panel also exposed the named
source STL, repaired STL, 3MF, slice evidence, and full plate preview downloads.

## Remaining offline blocker

Prompt-only, image-only, and combined requests each prepared valid saved
workflows with the appropriate prompt/image references. A prompt-only run
returned HTTP 503 `model_unavailable`: "Hermes AI is not configured." The
local Hermes endpoint returned HTTP 401 without its gateway key. Automatic
approval review rejected a credential-bearing probe to the separately
configured model endpoint because the destination and use of `OPENAI_API_KEY`
were not confirmed. No credential was transmitted in that probe. Model-backed
geometry generation and a real UI request through all stages therefore remain
unverified.

## Checks for printer day

After model access and an actual prompt/image run are verified, confirm the
P1S identity and idle status, PETG HF AMS slot/material mapping, plate and
support review, exact 3MF transfer and one-shot dispatch, printer progress and
remaining time, and LAN camera streaming. Only then enable
`WRIGHT_PRINT_DEMO_PRINTER_ENABLED=1` in the API process.
