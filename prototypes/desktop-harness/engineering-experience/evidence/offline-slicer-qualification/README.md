# Offline slicer prerequisite, 28 October 2026

This is a synthetic 10 mm coupon qualification, not the replacement-handle workflow, a human review, or physical printing.

- Independent MCP: `marctheshark3/bambu-p1s-mcp`, revision `7b50d0288fb7b91af8af422b96c4df4db0f1110c`, package 0.1.0, MCP 1.30.0.
- Native application: official OrcaSlicer 2.4.2 Linux ARM64 AppImage, SHA-256 `e1a07275a25f176626c55a5df39e91bc4476d8c28ee4a3192ff758e29dd5c3ba`.
- Selected image: `sha256:53db8008c407fb236c0fa65f7c3147405428c3a8008603896a971a594b2dda80`; no Wright base-image or host dependency change.
- Runtime: network disabled, read-only root, nonroot, no capabilities, no printer credentials. Only `slice_model_file` exposed in the fixture catalog. Actual GatewayService/StdioRunner; no live enrollment or workflow run.

| Check | Result |
|---|---|
| Official asset digest, startup and 11-tool discovery | PASS |
| Gateway offline slice, actual package and exact profile settings | PASS |
| Existing passive nominal-path reader and evidence hashes | PASS |
| Existing mandatory embedded-PNG check | FAIL: package contains no PNG |
| Complete handle manufacturing preparation | UNVERIFIED |
| Windows or clean Intel-Linux catalog qualification | UNVERIFIED |

The first slice definitively returned `ok:false` because the default Cool Plate did not support PETG, although the MCP envelope was not an error. No output existed. A fresh second attempt explicitly selected Textured PEI Plate and returned `ok:true`; actual package settings verify PETG, P1S, 0.4 mm nozzle, 0.2 mm layers, five walls and 40% infill. These are qualification profiles, not accepted handle production settings.

Whole-file toolpath inspection correctly rejected the startup G380 command. The existing reader then consumed the explicit unique `;VT0` → `; filament end gcode` nominal section, which establishes its own coordinate/unit/extrusion modes. Startup/shutdown semantics are excluded, not interpreted. The original PNG gate remains failing; no preview was fabricated and no requirement removed.

See `inspection-report.json` and `profile-receipt.json`. Private exact inputs, package, failed responses, gateway audit, container recipe and reproducible probes remain in `.local-run/experience-review/slicer-provider-audit/`. The complete source package and original failed attempt are preserved. This is a provider prerequisite, not another executor or universal catalog acceptance.
