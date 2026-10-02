# Selected-provider qualification progress — T043

**Date:** 1 October 2026. **Status:** partial; remaining qualification and full
engineering runs are pending. No public catalog entry is promoted.

Fresh isolated probes exercised existing independent providers through actual
stdio and native `GatewayService`, using controlled catalog/workspace ports.
These are backend probes, not the Hermes-facing `wrightgateway` proxy or complete
engineering processes. The selected native hosts and retained OASiS dependency
image are explicitly recorded; this is not a fresh clean-base installation claim.
Safe summaries and raw-record hashes are in
`artifacts/process-interfaces/083/20261001-engineering-readers/provider-probes.json`.

| Provider | Selected runtime and probe | Observed result |
|---|---|---|
| Existing Blender MCP | Upstream `5f8ddaf6e987c4aa0c3467fcc548838b28f64477`; Blender 4.5.10 LTS; fresh hidden factory profile/addon on private port 19983 | 28 tools; actual scene and owned 10×8×6 geometry/STL; recovery saved and native owner closed. |
| AgentCAD | 0.6.0 with NumPy 2.5.2/build123d 0.10.0; version-checked existing Windows preload bootstrap; resolved Python 3.12.11 | 11 tools; actual tiny 2×3×4 CAD and STEP/source/meta output. |
| Independent slicing MCP | Upstream `7b50d0288fb7b91af8af422b96c4df4db0f1110c`; selected portable CLI 2.8.2.61; dotenv disabled; only loopback dummy printer configuration | 11 tools; actual offline direct/gateway sliced 3MF. No printer tool or real printer connection. |
| OASiS | Upstream `7c184d5b7ca5cda6086f3912d1c7923c58307780`; retained selected dependency image SHA `49ad6b866d93cf85fa4c82c175241be5e0e7c17239773c658e550b50e0580f8d` | 17 tools; fresh network-disabled container, one isolated mount, actual fixed-temperature/Robin conduction and CSV/VTU. Native `critic_approved=false` retained. |

The OASiS container `wright-083-oasis-t043-001` was verified by ID/feature label
and stopped after probing. Existing campaign containers/processes were untouched.
Blender used the existing native application lifecycle owner, fresh exclusive
lease/document, hashed recovery and identity-checked close. MCP stdio owners were
stopped after each probe.

## Problems and bounded corrections

**AgentCAD startup:** initial offline dependency resolution consumed the startup
deadline. The second attempt used the already-resolved, explicitly version-checked
interpreter and passed. The raw second record mistakenly names an old source URL;
the correct catalog source is `https://github.com/jdilla1277/agentcad`. Its original
record is retained with that metadata limitation; no historical evidence rewritten.

**Slicer presets:** leaf JSON preset inheritance was not resolved by the external
provider. Its first file used PLA, density zero, two walls, 20% infill and no
supports despite PETG preset filenames. That file is only backend probe evidence.
Complete existing prerequisite flat JSON was copied as configuration data into
a fresh isolated provider root. No profile resolver, vendor protocol or execution
wrapper was added to Wright. The actual third-attempt sliced settings are PETG,
density 1.28, four walls, 35% infill, 0.2 mm layers and supports enabled. Both direct
and gateway routes passed exact configuration comparison. The intervening second
attempt could not spawn its cached base interpreter inside the sandbox; the
authorized selected-runtime retry passed. Failed roots were preserved.

**Remaining qualification:** complete the normal agent-facing gateway proxy and
selected-host/clean-container provenance checks before checking T043. Catalogue
promotion, public setup recipe changes, physical dispatch, campaign execution and
engineering acceptance are outside this checkpoint. T045–T047 will use original
assignment geometry, meaningful handoffs and exact 082 checks rather than these
small qualification artifacts.
