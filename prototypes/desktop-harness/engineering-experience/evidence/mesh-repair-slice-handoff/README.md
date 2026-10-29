# Mesh repair → offline slicing prerequisite

The independent Blender provider imported a deliberately duplicate-face 10 × 8 ×
6 mm STL, removed the duplicate during import, retained closed topology and
exported the repaired mesh through an actual Wright GatewayService call. An
independent binary-STL inspection confirms 12 triangles, no nonmanifold edges,
480 mm³ signed-volume magnitude and unchanged dimensions. The defective source
remains unchanged. Its invalid 520 mm³ signed-volume calculation is not a valid
solid measurement.

That exact repaired hash was passed through a second actual gateway call to the
independent offline slicer. Only `slice_model_file` was exposed for that call.
The resulting 3MF passes the existing passive package and mandatory native-PNG
checks, with PETG, 0.20 mm layers, five walls, 40% infill and the P1S 0.4 mm profile.
No printer credentials, network access or physical action were available.

- [Repair measurements and versions](repair-report.json)
- [Exact artifact handoff](handoff.json)
- [Package checks](slice-report.json)
- [Native package preview](native-package-preview.png)
- [Actual guarded provider code](repair.py)

The selected Blender image contains the original Wright image environment, but
its entrypoint was overridden: only native Blender and the independent MCP ran.
No Hermes process or model was used. The disposable container was stopped after
the call; other services and installed plugin settings were unchanged. Provider
source is clean at the recorded revision. A read-only Git identity check initially
rejected ownership; a per-command safe-directory option read its identity without
changing configuration.

This is **not** the replacement handle, a durable process run, orientation-study
qualification, strength acceptance or Windows UI acceptance. It establishes the
actual repair-to-slicer file boundary. The workflow still needs separate repair
and slicing bindings, exact orientation evidence and final applicability checks.
Private requests, responses, audits and full artifacts are retained under
`.local-run/experience-review/mesh-repair-036/`.
