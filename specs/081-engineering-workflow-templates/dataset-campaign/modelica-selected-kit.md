# Selected Modelica water-heater kit, 2026-09-12

The local prerequisite is ready. All three actual `water-heater-sizing` template
instances were saved through the ordinary source API and enrolled with scoped
integration grants. This task did not dispatch a canonical workflow. Their
output folders were empty when handed to the campaign runner.

The immutable selected image is
`sha256:e5dc37e5cde7722fa9547962b438548122def738019b85f380f9cb84d4b2bc47`.
The installed demo-only server is `3b419923-923f-4976-ad5e-0dc22640ad9b` and exposes
15 tools. The new kit is **`wright-water-heater-v1@0.1.0`**, under provider identity
`wright-modelica-campaign 0.6.5+wright.1`. Its original source is MIT-licensed
Casys Modelica0.6.5 commit `62e26009a566d15b625493b0c3510bdd14b01c3b`.
The upstream `coffee-machine-v1@0.1.0` kit, model assets and approved bounds remain
unchanged; its350W rejection was verified after installing the derivative.

## Physical and numerical contract

`WrightWaterHeater.mo` retains the upstream water/boiler heat capacitor, thermal
loss conductor, ambient boundary, ideal controlled heat source and hysteretic
thermostat. It adds explicit rated electrical input and heater efficiency:
delivered thermal power equals electrical input times efficiency. Separate
electrical power and integrated electrical energy outputs prevent thermal energy
from being mislabeled as electrical consumption. Inverter losses remain a
separate battery-accounting calculation for the mobile case.

The selected electrical range is350–1800W, vessel capacity90–480J/K, water
mass0.35–1.5kg and heater efficiency0.92–0.94. Heat-loss conductance is0.6–5W/K,
including the original5W/K default and every supplied0.6–2.88W/K case. Other
temperature/hysteresis ranges retain their original bounded definitions.
Water heat capacity remains the explicit fixed4180J/(kg.K) model property.
The actual campaign mapping sets the thermostat centre to the supplied90°C
target and declares its2K hysteresis assumption.

Six server-owned scenarios cover300,600 and700s horizons. Both variants keep
the requested1s output grid. Baseline DASSL uses `maxStepSize=1` and tolerance
`1e-6`; the independently executed refined scenario uses `maxStepSize=0.25` and
tolerance `1e-8`. These values are part of immutable scenario bytes, public
projection hash, manifest and the separate
`wright-modelica-numerical-lowering@1.0.0` identity. Unknown control pairs,
arbitrary flags and unknown kit versions are rejected. The original lowering
remains byte-identical when no selected numerical controls are present.

The OpenModelica compiler itself derives the new parameter schema during the
Docker build. Every runtime kit load checks agreement between those compiler
facts, source SHA and exposed parameters. The exact engine is OpenModelica1.27.0
with Modelica Standard Library4.1.0 and Deno2.9.6.

Primary native interfaces: [OpenModelica simulate](https://git.openmodelica.org/Documentation/OpenModelica.Scripting.simulate.html)
and [DASSL maximum internal step](https://openmodelica.org/doc/OpenModelicaUsersGuide/1.18/solving.html).
The selected code and exact hashes are preserved with the original license in
[qualification evidence](../../../../docs/mcp-catalog/evidence/modelica-2026-09-12/selected-kit/qualification.json).

## Real result export and study analysis

`modelica_export_recorded_result` accepts only a dataset ID, attempt ID, an exact
same-prefix request ID and expected immutable manifest digest. It calls the
same full read-only completed-claim/ledger/artifact verification used by the
provider's MCP resources. It exports the fixed ten native CSV/source/schema/
script/log/ledger files into a separately mounted attempt output directory.
Arbitrary paths, source bytes and commands are not inputs. Redirected directories,
symlinks, differing existing outputs and wrong identities are rejected. Exact
repetition verifies existing bytes and never overwrites different evidence.

`modelica_summarize_recorded_study` accepts exact request/digest pairs and the
declared power/loss comparison grid. It rejects missing baselines, duplicate
baselines and changes to unrelated physical inputs. It independently interpolates
the target crossing, integrates electrical/thermal power and ambient losses from
the native CSV samples, and compares those values with stored heat and the native
energy integrators. Refined comparisons require identical physical parameters.
It produces temperature-time, power-comparison and energy-summary CSVs, a native
data SVG plot, the parameter/provenance JSON and a heater-selection Markdown report.

Numerical screening assumptions are explicit in that report:1% energy agreement,
target-time difference at most max(1s,1%), and1% final electrical-energy difference.
These are engineering-process observations, not the campaign's future content
validation suite. The dashboard's validated-data metric stays0.

## Observed qualification

- Five selected authority/analysis Deno tests passed, including unchanged upstream
  bounds, unknown numerical authority, cross-attempt export rejection, independent
  time/energy integration and unreached-target preservation.
- Six real native simulations completed, covering each dataset horizon and both
  solver-control pairs. The350W/90J/K,800W mobile and1800W high-loss examples used
  their supplied mass/capacity/efficiency values. The350W case honestly did not
  reach90°C within300s; no metric or feasible recommendation was invented.
- Complete CSVs were retrieved byte-for-byte with MCP `resources/read` at the
  recorded `casys://modelica/requests/<id>/artifacts/result.csv` URI. Fixed exports
  matched native bytes. Exact completed-request replay produced no additional runs.
- The final study summaries ran on those sealed native results. Wrong manifest
  digests and missing candidate comparisons were rejected before export.
- The exact intended `docker exec ... deno ... --stdio` production command passed
  ordinary Wright `StdioRunner` and `GatewayService` discovery and a real native
  OMC/MSL manifest probe. All15 prefixed tools were present; the production run
  store remained empty.
- A separate unchanged Intel Linux Wright container proxied an actual native solve
  and ten-file export through `GatewayService` to an isolated HTTP sidecar. This
  supplementary probe uses an explicit current2026 stateless HTTP adapter, as the
  ordinary `SseRunner` initialize request is incompatible with that upstream HTTP
  mode. It is not claimed as ordinary HTTP-client compatibility. Production uses
  the verified standard stdio route.

No CAD/Modelica software was added to the Wright base image. The disposable HTTP
qualification sidecar is stopped; its evidence remains. The production sidecar
has no network and mounts only its own run store and the three attempt output
directories. No device, payment, supplier or account action is involved.

## Canonical handoff

Combined execution manifest:
`.local-run/feature-081-live/campaign-execution/modelica-attempt-001.json`.

| Dataset | Required canonical steps | Native comparison |
|---|---:|---|
| water-heater-sizing-01 |9|3 powers, one loss case, selected refined rerun|
| water-heater-sizing-02 |9|3 powers, one loss case, selected refined rerun plus battery accounting|
| water-heater-sizing-03 |25|3 powers ×3 loss cases, selected refined rerun at every loss|

Every original requirement-review, allowed-settings and verification task ID is
retained. Uploaded CSV values become explicit ordinary canonical MCP submit/export
nodes, not a template-specific runtime executor. Selection in the verification
task uses the actual preceding results; no winning power is predetermined.
Case03 uses separate refined-export and study nodes to preserve every required
file under the existing16-files-per-node compiler cap. No requirement or cap was
relaxed. Stable exact request IDs support provider-native readback/idempotency.

The provider retains at most20 native runs. The three complete studies require
at most20 in total:15 power/loss baselines and five selected refinements.
Do not reuse request IDs with changed arguments or silently evict evidence.
Any future additional attempt needs a separately recorded store/mount scope.

The reusable preparation and installation entry points are
`scripts/modelica_campaign/prepare_overlay.py`,
`scripts/install-modelica-campaign-mcp.py`,
`scripts/prepare-modelica-dataset-campaign.py` and
`scripts/enroll-modelica-dataset-campaign.py`. Installation requires the observed
exact-production gateway qualification for the pinned image before registry writes.
