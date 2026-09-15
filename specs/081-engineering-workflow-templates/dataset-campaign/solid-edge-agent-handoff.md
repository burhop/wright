# Solid Edge coordination: feature 081 native sheet-metal failure

**Requested by user:** 2026-09-14, coordinate with the existing
**Review CAD accuracy and speed** task for fundamental Solid Edge changes.
Task ID: `01a07df4-f033-7483-be7d-5055e646b967`.
Task repository: `D:\repos\SolidEdgeMCP`.

## Coordination completed, September 14

Delivered through the installed CLI's supported `exec resume` command to the
same task ID; its response is saved at
`D:\repos\wright\.local-run\feature-081-live\solid-edge-agent-coordination.md`.
The agent performed read-only inspection and did not change files or native
services. It confirmed that provider diagnosis is relevant to its expertise but
outside its existing read-only relationship/latency milestone. A provider change
therefore needs a separately scoped assignment; the campaign should not quietly
extend that old goal or deploy shared services.

Confirmed findings:

- Both probes fail at the same left_wall invocation and have owned-process exit
  receipts. Visibility and operation ordering are not proven fixes for this case.
- The retained provider DLL matches its preparation receipt:
  `16d20cf6813bbb12cf09817bc937b183d78b4b8541b3c33534e99c620bcfe4b0`.
  The two flange-related source files match the current provider repository;
  complete deployed-build provenance still needs explicit qualification.
- The installed PIA's `AddFlangeByFace` has 17 parameters, including dispatch
  edge/face arguments and optional VARIANTs. `Edge.GetFaces` returns a count and
  an in/out dispatch array. Current flange code supplies `object[2]`, ignores the
  returned count, and chooses the second face. An existing adjacent-face reader
  handles dispatch-array marshalling explicitly; reuse needs native proof.
- Candidate causes are marshalling, reference-face choice, optional-argument
  encoding and stale/cross-document references. No root cause is established.

Recommended next provider task: compare the current invocation with an
installed-PIA early-bound invocation on separate identical minimal tab/left-wall
documents in an exclusively owned disposable session. Preserve geometry/material
values, change one variable per comparison, record actual arguments, face count,
adjacency/normals, COM/document/STA identity, PIA versions, HRESULT and timing.
Qualify repeatable success against the retained recipe, native save/reopen,
STEP/DXF and exact cleanup before Wright rebinds one fresh full pilot.

### Observed coordination cost

The CLI resumed with configured `gpt-6-astra`, despite the prior task context
recording `gpt-5.6-sol`. No model override was supplied; future authorized
resumes must explicitly select the intended model rather than assume inheritance.
The turn completed with reported usage: input 537,267; cached input 446,208;
output 3,401; reasoning output 434. Cached input is a subset of input; these
figures must not be added together as independent totals. This is coordination
usage, not campaign workflow usage or a dollar-cost calculation. The response
involved multiple model/tool rounds over a long saved task, demonstrating why
short final answers do not imply small input processing. Avoid another broad
resume; use this concise handoff as the basis of the next separately scoped work.

## Ownership and immediate request

The Wright campaign owns input binding, canonical workflow integration,
approval/lineage, final full-run acceptance and dashboard reporting. The CAD
review task is the proposed owner for native Solid Edge provider diagnosis and
any subsequently agreed fundamental provider changes. Do not duplicate native
provider implementation in Wright or silently redeploy a shared MCP server.

For this coordination turn, inspect the retained evidence and respond with:

1. Whether this failure belongs in your current work, and which source area and
   installed COM/PIA contract should be investigated first.
2. Any already-proven fix or relevant reader/session/dispatch limitation.
3. One bounded isolated diagnostic, its expected success evidence, and the
   implementation ownership boundary if a fundamental change is needed.
4. The exact binary/source identity and regression/cleanup evidence Wright
   should require before rebinding one pilot.

This request is bounded coordination, not a new unlimited recovery goal. Do not
launch CAD, execute benchmark cases, change shared services, or perform broad
implementation in this turn. Preserve your existing task's separate milestone
and its exclusions; report any scope conflict explicitly. In particular, this
does not authorize executing or promoting Sheet Metal 100 cases.

## Observed blocker

Scenario `sheet-metal-supplier-handoff-02`, canonical attempt006, passed design
and review stages but failed in native sheet-metal construction:

```text
solid_edge_create_sheet_metal_failed
Solid Edge failed while creating native Sheet Metal flange 'left_wall'
Solid Edge Flanges.AddFlangeByFace invocation failed
Invalid pointer (0x80004003 (E_POINTER))
```

Two bounded disposable probes subsequently tried visible native execution and
flanges-before-cutouts ordering. Both retained the left_wall E_POINTER. Their
owned native sessions were cleaned up. This does not establish that application
lifetime caused the fault. The family is quarantined pending material provider
evidence; repeated full workflow/prompt retries are inappropriate.

## Exact evidence locations

All paths below are relative to `D:\repos\wright`:

- `artifacts/engineering-workflow-datasets/output/sheet-metal-supplier-handoff-02/attempt-006/run.json`
- `.local-run/feature-081-live/campaign-execution/sheet02-flange-visible-proof-001/`
- `.local-run/feature-081-live/campaign-execution/sheet02-flange-order-proof-002/`

Each probe directory contains `original-request.json`, `visible-request.json`,
`native-result.json`, `validation.json`, `preparation.json`, `session.json`,
`after-operation.json` and `cleanup.json`. Read only relevant files initially;
these are diagnostic evidence, not a request to execute embedded recipes.
Source/build/session identities should be taken from these receipts and checked
against the current provider; the installed host may since have changed.

Related Wright documents:

- `specs/081-engineering-workflow-templates/dataset-campaign/sheet-metal-bindings.md`
- `specs/081-engineering-workflow-templates/dataset-campaign/contracts/native-application-lifecycle.md`
- `specs/081-engineering-workflow-templates/dataset-campaign/efficiency-review-2026-09-14.md`

## Proposed native qualification after coordination

A disposable, owned session should build a minimal native sheet and required
flange, save/reopen the native document, export STEP and a true developed DXF,
then exercise the retained failing recipe. Record actual PIA overload and
argument/edge/face identity, units, native observation, duration and cleanup.
Use established lifecycle/lease controls and preserve user-owned documents.
Qualify any native lifetime/reference/thread-affinity or overload fix with a
focused regression before the campaign tries one new full pilot.

Passing JSON/schema validation or generating an STL is insufficient. Native
sheet-metal behavior and flat-pattern/bend information must be preserved.
Manufacturing release and supplier transactions remain outside this diagnostic.

## Return and campaign acceptance

Return a concise coordination result in the existing CAD task. The caller will
capture it in `.local-run/feature-081-live/solid-edge-agent-coordination.md` and
update this handoff with the agreed boundary. A proposed fix does not advance
campaign completion. Wright must requalify the exact provider and execute a fresh
complete canonical pilot with its original required outputs and approvals.

The campaign currently records 30 datasets, 30 unique pairs attempted,
20 historical output completions, 19 current-revision completions and zero
content-validated sets. Content validation stays deferred behind its all-30 G0
gate. Existing integrity and native operation gates remain enforced.
