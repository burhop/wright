# Desktop usability qualification

Submitted goal: 25 October 2026. Experimental, local work only; no push,
merge, publication or engineering execution. Baseline: merged PR171,
`1514ea25`; installed named prototype is independently inspected.

## User journey and ownership

Open a workspace, find/name/edit a workflow, understand saved versus draft
state, inspect an existing run and its actual results, return to its producing
step, inspect files and understand connection readiness. The shared editor,
source/draft services, process client, recorder, gateway and storage remain
owners. This work changes presentation and qualification, not execution,
instructions, permission grants or recovery authority (V1–V7).

Keep workspace/session/path/run/source identities exact. Genuine source
mismatches detach evidence; missing context must not invent one. No UI action
or test fixture can confer process approval. Reopening reconciles state and
does not replay effects. Shared canvas behavior and common-view fallback stay.

## Tasks

- [ ] Record source, installed resource/runtime and preservation baseline.
- [ ] Reproduce novice journeys with visible outcomes and before screenshots.
- [ ] Fix small batches: context/navigation; status/next action; density.
- [ ] Regress editing, import/export, preview and Connections.
- [ ] Exercise retained completed run and Robot Tracking Diagnosis negative cases.
- [ ] Make the existing real-owner browser qualification portable to Windows.
- [ ] Qualify Windows locally where an independent session is available.
- [ ] Build, check and install only the named prototype candidate.
- [ ] Verify exact installed resources and tools; record native-host limits.
- [ ] Run final applicable local checks; make focused local commits.
- [ ] Deliver backlog, before/after screenshots, boundary matrix and morning handoff.

## Testing decisions

Reuse existing native acceptance scripts with actual built HTML and real MCP
owners. Assert text, focus, viewport intersection, exact identities and
downloaded bytes, not only control existence. Only disposable authoring/import/
upload assets may be written. Historical engineering records remain untouched.

Windows browser/MCP qualification is distinct from actual desktop-host proof.
OpenAI Computer Use documentation explicitly excludes automating the OpenAI
application itself. Do not evade this with alternative automation or private
host debugging. Time-box host-interface research; record unobserved host panel,
file delivery and chat restoration separately rather than blocking shared work.
No new testing framework, executor, auth abstraction or editor replacement.

Private evidence and usability backlog: `.local-run/usability-20261025/`.
Agent verification is not human acceptance; social screenshots stay unpublished
and clearly state whether their host is simulated.
