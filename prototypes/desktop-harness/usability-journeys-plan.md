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

- [x] Record source, installed resource/runtime and preservation baseline.
- [x] Reproduce novice journeys with visible outcomes and before screenshots.
- [x] Fix small batches: context/navigation; status/next action; density.
- [x] Regress editing, import/export, preview and Connections.
- [x] Exercise retained completed run and Robot Tracking Diagnosis negative cases.
- [x] Make the existing real-owner browser qualification portable to Windows.
- [ ] Qualify Windows locally where an independent session is available.
- [x] Build, check and install only the named prototype candidate.
- [x] Verify exact installed resources and tools; record native-host limits.
- [x] Run final applicable local checks; make focused local commits.
- [x] Deliver backlog, before/after screenshots, boundary matrix and morning handoff.

Local delivery is recorded in [the qualification note](usability-qualification-20261025.md).
Windows execution remains queued with its independent pilot; no Windows or
native OpenAI host acceptance is inferred from Linux proof.

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
