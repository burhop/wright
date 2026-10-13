# SteveCAD and supporting-tool qualification

These are technical qualifications. They do not complete the three engineering
demonstrations or establish physical performance, manufacture or human acceptance.

| Evidence | What it proves |
| --- | --- |
| native/04-save-coupon.json, 05-generate-coupon.json | New editable source saved and generated through the actual normal Wright workspace gateway. |
| native/06-inspect-coupon.json and PNG | Actual provider image and measurements of the generated coupon. |
| native/07-export-coupon.json and coupon.step | Actual one-time STEP transfer, exact bytes and digest; the transfer ticket is omitted. |
| native/08-readback-coupon.json | Read-back source and current revision; GUI-editable feature declarations. |
| native/accepted-source.json, coupon-readback.workflow.wflow, durable-run-snapshot.json | Accepted source and completed canonical-runtime readback with recorded output digest. |
| container-001 through container-004 | Distinct incomplete/failed attempts retained; do not count them as passes. |
| container-005/summary.json, tools.json, direct-read-design.json, gateway-inspection.json and PNG | Fresh neutral Linux read-only discovery, direct backend read and policy/audit gateway inspection of the exact coupon. Source overlay and fixture workspace scope are explicit. |
| native/09-oasis-backend-probe.json | Actual scikit-fem readiness calculation through an independently isolated OASiS MCP. Provider result is completed_unverified and its critic remains pending. |
| calculix-native-001/registered.json, install.json, mesh-preflight.json | Upstream Casys 0.8.6 stdio used through normal Wright onboarding/gateway; actual STEP hash, bounds, 4,613 nodes and 2,242 elements. No bracket solve or reaction evidence is established. |
| oasis-native-fea-001/native-reaction-probe.json and fields/ | Native one-element CalculiX fixture executed through normal Wright/OASiS; actual files retained, but provider did not discover supported field outputs. Original completed_unverified warning preserved. |
| oasis-native-fea-002/native-reaction-probe-002.json, fields/ and provenance.json | Fresh fixture exports finite actual DAT-derived U/RF fields as VTU; synthetic -1 N load balances +1 N support reaction. Provider automated checks pass, genuine independent critic pending, trustworthy_result=false. No original bracket analysis or mesh-refinement claim. |

The native coupon is 50 x 30 x 3 mm with four diameter-4.5 through holes.
Reported bounds and volume match that specified geometry. Its STEP SHA-256 is
`3c3ad6cf672bea6639b045403d97190ba0f125f27225e5915112cdc0675400a7`.
The Linux pass proves selected remote operations, not CAD creation on Linux,
container workspace UI, solver validity or complete installed-distribution
qualification. No selected CAD host was installed in the Wright base image.

The SDK comparison hypothesis in attempt 002 was superseded by the follow-up
observation: fresh OAuth state resolved the connection issue with the original
base SDK. Failed attempt 003's child venv dependency problem is separately retained.

Credentials stay in ignored isolated runtime state. Mounted account state is
read-only and copied only into a disposable container's ephemeral storage.
No historical/protected campaign run was resumed or approved.
