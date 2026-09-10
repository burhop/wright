# Engineering MCP process readiness

The product release set contains two good-server categories: **Qualified** has
current protocol, backend, Wright gateway, outcome, and cleanup proof;
**Credential ready** has reached the expected authentication boundary and can
ship with guided key, login, or OAuth setup. Credential ready does not imply a
post-login engineering task has passed.

| Process | Real engineering decision | Status | MCP chain | Smallest next proof |
|---|---|---|---|---|
| ECAD BOM sourcing review | Is every released line item available, compliant, and replaceable without violating package/electrical constraints? | Lab-ready | KiCad (Qualified) → Partuno (Credential ready) | Analyze a five-line synthetic BOM using read-only distributor credentials through Wright. |
| Requirements to CAD change control | Does the CAD revision implement the approved requirement and retain traceability? | Lab-ready | Atlassian (Credential ready) → OpenSCAD (Qualified) → GitHub (Credential ready) | Fetch one test requirement and repository file, then run the existing local CAD fixture without external writes. |
| FeatureScript part review | Does generated FeatureScript compile and produce the specified dimensions and mass properties? | Lab-ready | Onshape Labs FeatureScript (Credential ready) → Onshape model workflow (Qualified) | Compile one minimal feature in a disposable test document and verify dimensions through Wright. |
| Simulation submit, monitor, review | Do cloud results agree with a deterministic local baseline inside declared engineering tolerance and budget? | Lab-ready | OASiS (Qualified) → Rescale (Credential ready) | Read one preexisting completed zero-cost job; do not submit paid work. |
| Engineering telemetry triage | Which change or runtime condition explains an engineering automation failure? | Speculative | Grafana (Environment required) → GitHub (Credential ready) | Query one known metric and log stream from a disposable read-only Grafana instance. |

The machine-readable companion, [process-readiness.json](process-readiness.json),
records lifecycle stages, inputs, outputs, handoffs, prerequisites, approval
gates, deterministic oracles, exact evidence, limitations, and the next
qualification for each process.

No new process is labeled immediately runnable. Each combines at least one
newly evaluated server whose post-authentication or host-backed task remains
unproven. Existing all-Qualified fixture chains remain visible on the dashboard
as regression evidence; they should not be presented as production process
validation.
