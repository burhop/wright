# Prompt to printed part: isolated offline evidence

Recorded 2026-09-24/25 on `codex/prompt-to-3d-printed-part-demo`. This is a
source-checkout diagnostic, separate from the 30-example generation campaign.
The initial diagnostic did not contact the P1S. Read the later follow-up below for the local monitoring checks; no print was dispatched.

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

## Initial offline blocker, since resolved

Prompt-only, image-only, and combined requests each prepared valid saved
workflows with the appropriate prompt/image references. A prompt-only run
returned HTTP 503 `model_unavailable`: "Hermes AI is not configured." The
local Hermes endpoint returned HTTP 401 without its gateway key. Automatic
approval review rejected a credential-bearing probe to the separately
configured model endpoint because the destination and use of `OPENAI_API_KEY`
were not confirmed. No credential was transmitted in that probe. Model-backed
geometry generation was unverified at the time of this first diagnostic.

## Orientation and prompt-run follow-up

After reviewing the user's feedback, we identified that the original `support-preview.svg` projected every G-code layer onto a single XY plane, while Bambu's embedded `plate_1.png` was a model thumbnail rather than a support rendering. Both could give an incorrect impression of support geometry. The revised SVG is one labeled G-code layer, chosen from the layer with the most support moves, or the middle layer when no supports were generated. It is a 2D cross-section, not a 3D support model. The UI now shows the exact oriented STL selected for the final 3MF.

An isolated six-orientation audit of the same repaired 50 mm bracket used Bambu Studio 2.8.2.61 and the P1S 0.4 mm / Generic PETG profile. This is the profile matching the observed PETG AMS slot (`GFG99`); the first diagnostic used PETG HF (`GFG02`). For a comparable same-profile baseline, Bambu estimated 62m 50s, 18.86 g, and 6,551 support moves in the original orientation. The selected `x_plus_90` orientation had a 700 mm² bed-contact face, zero support moves, 41m 23s, and 16.32 g. It saved 21m 27s and 2.54 g in the slicer's estimate. The `x_180` orientation used 15.11 g but took 50m 19s; the demo currently chooses the fastest zero-support orientation. The audit artifacts are under `campaign/printed-replacement-part-01/demo-orientation-audit-2/artifacts/` in the isolated workspace, including all candidate STLs, packages, and a selected G-code package. A headless Chromium screenshot of the selected layer is `.local-run/print-demo-offline/orientation-layer.png`.

After the final selection-policy and evidence-command review, a fresh `demo-orientation-audit-4` run selected the same `x_plus_90` orientation and recorded the actual selected Bambu invocation. A separate `demo-default-slice-audit` run used the operation's default single-orientation mode, confirming the other engineering workflows still slice the authored STL once: 62m 50s, 18.86 g, 6,551 support moves for this geometry.

A new prompt-only Wright run then completed through model-driven Blender construction, native mesh repair, and the six-way Bambu slicer MCP stage. Its run ID is `c904390c49194b55b7d54aeb3d7604d2`, saved workflow `workflows/prompt-to-print-8f8b2e4a8e04.workflow.wflow`, and artifacts under `campaign/printed-replacement-part-01/demo-8f8b2e4a8e04/artifacts/`. The prompt specified a 50 × 30 × 30 mm one-piece L bracket. The model's initial guarded Blender call used a disallowed `hasattr(bpy.ops.wm, ...)` check; it recovered, exported a watertight 1,084-byte STL, and the full workflow completed in 97 seconds. The selected as-authored orientation had a 1,500 mm² contact face, zero support moves, estimated 41m 34s and 13.17 g. The candidate comparison also recorded two poor orientations with over 6,300 support moves.

The same prompt-only result was loaded through the served workspace **Workflows** control in headless Chromium. The browser showed the selected STL in its interactive canvas, loaded the labeled layer SVG, displayed 42 rounded minutes / 13.2 g / zero support moves, and kept Print disabled. There were no page errors. Screenshot: `.local-run/print-demo-offline/oriented-review.png`. The browser check substituted this completed run at the prepare/run HTTP boundary; the previews and downloads came from Wright's real workspace API. This check also caught and fixed the JSON evidence response wrapper used by `/files/content`.

An image-only request uploaded that Blender render as `bracket-reference.png`. Wright attached the image bytes as a visual reference and completed workflow `workflows/prompt-to-print-aa10eae37494.workflow.wflow`, run `81fb046cb96440d8b284d7a9999f109d`, with artifacts under `campaign/printed-replacement-part-01/demo-aa10eae37494/artifacts/`. The model inferred unspecified 20 mm depth, 34 mm height, and 4 mm wall thickness from the image, recorded those as assumptions, and exported a watertight STL. Bambu selected a zero-support orientation with a 31m 53s / 9.32 g estimate. These inferred dimensions are not verified engineering measurements.

A combined request used the same uploaded image and explicit 50 × 30 × 30 mm, 6 mm thick dimensions. Wright completed workflow `workflows/prompt-to-print-83ff42a827d1.workflow.wflow`, run `59d6dde20e8247da9fa26414aefc1d64`, with artifacts under `campaign/printed-replacement-part-01/demo-83ff42a827d1/artifacts/`. It exported a watertight STL and zero-support 3MF estimated at 41m 34s / 13.17 g. The workflow instruction was amended to call `bpy.ops.wm.stl_export` directly; this run had no guarded Blender operator-check rejection. All three request forms therefore produced real STL and G-code 3MF artifacts in isolated Wright runs. No physical print or strength/fit assessment has been performed.

Read-only P1S LAN status was available, and one camera JPEG was received. The camera feed later stalled during sustained access, so continuous streaming remains unverified. Print dispatch stayed disabled and no upload or print command was sent.

## Round-pumpkin failure and review update (2026-09-26)

The user's first round-pumpkin request completed Blender modeling and mesh repair but failed at the slicer MCP step (`MCP_CALL_FAILED`). The saved `demo-ce662210b77a` repaired STL was closed, but all six axis-aligned orientation candidates failed the slicer's flat-bed-contact check before Bambu Studio ran. The previous UI surfaced the backend code and internal owner text without a useful explanation.

The demo-only repair operation now creates a bounded flat underside when the authored model has too little bed contact, and records the trim and contact area for review. An isolated replay of the failed source STL in Blender 4.5.10 produced a closed, nondegenerate 50 × 50 × 48 mm mesh after a 2 mm trim, with 321.423 mm² plate contact. Bambu Studio 2.8.2.61 then sliced it into a P1S G-code 3MF: 240 layers, 62m 31s estimated, 26.02 g, and 3,614 support moves. Replay files are under `.local-run/pumpkin-flat-base-audit-20260926/`; the user's failed attempt was not altered.

A fresh, unmocked browser run used the same prompt text and pumpkin reference through the served workspace **Workflows** control. Its workflow is `workflows/prompt-to-print-581584611acb.workflow.wflow`, run `1e3e84c64c04478f820b8a7259dfc0b2`, with artifacts under `campaign/printed-replacement-part-01/demo-581584611acb/artifacts/`. It completed Blender MCP, native mesh-repair MCP, and Bambu Studio CLI slicing. This time Blender authored a 220.684 mm² flat underside, so repair did not trim it. Bambu selected the authored orientation and exported a 233-layer 3MF estimated at 67 minutes with 15,073 support moves. The 7 MB `toolpaths.json` carries the selected package hash; the UI rendered its full 3D extrusion stack and support paths, with a layer slider, model/support switches, live stage log, and uploaded-image thumbnail. Headless Chromium reported no page errors. Screenshots: `.local-run/pumpkin-flat-base-audit-20260926/progress-ui.png` and `result-ui.png`.

This run confirms the prior hard failure is resolved and exposes the remaining support use for human review. It does not show that the pumpkin has the lowest feasible support amount or that the part will print successfully. No printer command was sent.

## Dense-pumpkin repair failure (2026-09-26)

A later image-and-prompt attempt, `demo-f2973e6c1083`, failed in mesh repair after Blender produced a 138,936-triangle STL. The source was already one closed, nondegenerate solid with positive volume, but the fixed repair operation had no path to bring an otherwise valid mesh below its 80,000-triangle limit. The user saw `mcp_call_failed` at “Repair, measure, and orient mesh.” The saved failed attempt remains unchanged.

The demo now allows bounded polygon reduction for this case. Replaying the exact source with pinned Blender 4.5.10 reduced it to 79,000 triangles while retaining one closed, nondegenerate solid. The largest measured dimension changed by less than 0.006 mm and the volume by about 0.000034%. It retained 310.329 mm² of flat plate contact without trimming. Pinned Bambu Studio 2.8.2.61 sliced the repaired model into a P1S 3MF, estimated at 56 minutes and 23.86 g, with 2,721 support moves. Replay files are under `.local-run/pumpkin-repair-failure-20260926/`. These are local engineering-stage checks.

A fresh, unmocked served-UI run used the same prompt, uploaded reference image, and 50 mm size field. It saved `workflows/prompt-to-print-fb6b5af2a978.workflow.wflow` and completed run `55f5dbe635a1444e8229314b959f665c`. Blender authored a new 180,960-triangle pumpkin; mesh repair reduced it to 79,000 triangles, preserving one closed solid with a maximum dimension change of 0.000439 mm and 0.003249% volume change. The existing flat underside provided 191.31 mm² bed contact, so repair did not trim it. Bambu selected the authored orientation and exported a G-code 3MF with SHA-256 `137067b3359e1e3e3674e41b7a1911828b2bb9ab3f2b2483c54f0eab7b955335`, estimated at 55m 52s, 23.77 g, and 7,789 support moves. The served review showed the uploaded image, model, 3D layer toolpaths, and polygon-reduction notice; headless Chromium reported no page errors. Screenshots are `.local-run/pumpkin-repair-failure-20260926/progress-ui.png` and `result-ui.png`. No printer command was sent. The support count is a review concern; successful slicing does not establish that this is an optimal support strategy.

The failed form also combined “Width should be about 10 cm” with the separate 50 mm largest-dimension field. The latter controls scale. The form now states that 10 cm requires 100 mm, so the mismatch is visible before another request.

## Checks for printer day

Before a physical print, confirm the P1S identity and idle status, Generic PETG
AMS slot/material mapping, plate and selected orientation review, exact 3MF
transfer and one-shot dispatch, printer progress and remaining time, and LAN
camera streaming. Only then enable
`WRIGHT_PRINT_DEMO_PRINTER_ENABLED=1` in the API process.
