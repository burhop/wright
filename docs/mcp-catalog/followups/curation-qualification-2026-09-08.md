# Complete lifecycle qualification after the initial curation pass

Owner: Wright catalog maintainers. Next review: 8 October 2026.

The dated report records 74 inventory entries: two scoped technical recommendations,
63 follow-ups, and nine removals from ordinary discovery. This is an initial
shortlist, with explicit coverage gaps. No repeat-use telemetry was available.

Prioritize these bounded tasks:

| Candidate/family | Engineering gap | Required next evidence |
|---|---|---|
| GitHub official MCP | Requirements, engineering changes, tests, release | Dedicated repository/OAuth scope; retrieve a known issue, test result and release through Wright; check link/revision fidelity |
| Atlassian Rovo v2 | Requirements and traceability | Dedicated tenant and new v2 OAuth; flat `tools=all` endpoint; requirement-to-work-item trace and expired-token behavior |
| Partuno | Component sourcing and BOM | Operator-owned DigiKey/Mouser credentials; verify manufacturer part number, availability timestamp, units, quantity breaks and BOM output |
| Grafana official MCP | Test evidence and operations | Pin image digest; read-only service account; retrieve known telemetry and preserve timestamp/unit interpretation |
| MATLAB / Ansys / Rescale | Simulation and analysis | Available licensed test host or dedicated sandbox account; known numerical oracle and artifacts through the gateway |
| Onshape / FreeCAD / KiCad / BREP | Detailed design | Choose by user's host; qualify a small edit/export and inspect the actual artifact, including the existing failure reports |
| Manufacturing and quality candidates | Manufacturing planning and inspection | Verify primary implementation identity before installation; qualify a read-only fixture/inspection workflow without machine actuation |
| WebMCP application | Browser tools | Exact browser/application build, origin/session binding, permission denial, navigation disposal and native registration acceptance |
| MHS preview | Hardware | Obtain the actual specification and supported driver; separate simulation/read-only qualification from physical commissioning |

The initial software recipes need cancellation, failure recovery, version-change,
and additional workflow checks before broader recommendations. Autodesk's
technical pass does not accept service terms on the user's behalf. OpenSCAD's
pass covers a Linux container cube export; it does not prove native CAD setup,
complex geometry, toolpath generation or fabrication.

Review discovery artifacts as untrusted leads. Broad terms return unrelated
travel/recruiting directories as well as engineering tools. `com.entalpa/requirements`,
`io.dotrequirements/dotrequirements`, and `com.supplyslate/sourcing` are research
leads, not verified publishers or installable recommendations. Resolve primary
identity and relevance first. No package commands from Registry responses enter
the execution catalog automatically.

Before expanding the shortlist, run three cross-tool journeys: a mechanical
design change with test evidence; an electronics requirement-to-BOM flow; and an
operations fault traced back to a release. Check identifiers, revisions, units,
permissions, artifact formats and provenance at every handoff. Prefer a useful
portfolio over maximizing server count.
