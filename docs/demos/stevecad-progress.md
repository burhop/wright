# SteveCAD integration and engineering demonstrations

## Latest evidence — 11 October 2026

The connection milestone is complete. The three engineering demonstrations and
unpublished presentation package remain in progress.

- Both actual heat candidates exist as editable SteveCAD revision 1 documents,
  measured 100 x 40/60 x 2 mm solids with exact exported STEP bytes. Their files
  and provider receipts are in `artifacts/stevecad-demonstrations/heat-spreader/attempt-001/cad/`.
- Accepted thermal process `stevecad-heat-spreader-native-003.workflow.wflow`, run
  `b485b6eee86d4031bb4e654053e63f86`, remains `waiting_human` at its declared model-basis
  review. The current API snapshot is retained in `runtime-native-003/snapshot-at-status.json`.
  No numerical field, sizing acceptance or human approval is claimed. Earlier
  readiness failure and failed basis-recording run remain distinct evidence.
- Normal workspace Workflows navigation opens the exact saved process. Walkthrough
  `artifacts/ui-walkthrough/stevecad-thermal/2026-10-11T1719Z/report.html` passed this
  bounded navigation. Four earlier stopped attempts remain; all five artifact
  structures passed the skill's report validator. This does not establish run/UI
  completion, and the screenshot was captured before run-status reconciliation.
- Casys mesh preflight consumed the exact coupon STEP and produced an actual mesh.
  An unchanged OASiS provider with isolated native prerequisites subsequently
  executed a fresh one-element CalculiX reaction-output fixture through Wright.
  Attempt 002 retained finite DAT-derived displacement/reaction VTU fields and
  balanced the synthetic -1 N load with +1 N support reaction. OASiS reports
  `completed` but `trustworthy_result=false` pending its independent critic.
  Attempt 001's missing-provider-output warning and actual files are retained.
  Neither fixture establishes equipment-mount compliance.
- Four focused heat-preparation tests passed, covering canonical bindings,
  genuine review steps and refusal of changed STEP bytes, wrong units or volume
  inconsistent with the declared solid rectangular idealization.

Next: respond to the pending thermal basis review to continue the same run;
complete structural CAD/analysis and qualify the PCB electrical/mechanical path.
The source/runtime, validator and refined editor remain the existing shared owners.

## Current scope

The user requested a new SteveCAD MCP integration in Wright and three substantial
engineering demonstrations, followed by unpublished social assets. The user
confirmed the proposed structural mount, heat-spreader comparison, and PCB
enclosure portfolio. On 11 October they clarified that adding the new MCP is the
immediate priority. Demonstration execution and social content follow actual
connection and output verification.

## Isolation and baseline

- Branch: `codex/stevecad-engineering-demos`.
- Worktree: `D:/repos/wright/.local-run/stevecad-engineering-demos`.
- Fetched `origin/dev`: `ba2fad68c181165b96b9c15c40b1a1f63c88acb3` (PR 140 merge).
- Git checkout requires per-command `-c core.longpaths=true` on this Windows host.
- Existing checkout, untracked evidence, profiles and protected runs preserved.
- GitHub baseline checks include failures and unfinished jobs. This baseline is
  identified, not certified globally green. Local relevant checks are recorded
  separately. No production release or social publication is authorized.
- GB10 Codex adapter work remains separate. This change adds provider metadata;
  it does not modify model adapters or instruction/execution owners.

## Integration

Official documentation and live public resource discovery establish
`https://stevecad.studio/mcp`, streamable HTTP and account-scoped OAuth. New catalog
metadata reuses existing onboarding, remote transport, secret storage and gateway.
No vendor implementation, local CAD host, new executor or new UI is added.
Native Windows connected using Wright OAuth: STEVE CAD 4.0.10, MCP 2025-11-25,
26 tools, successful `list_skills` and `api_reference` calls. The existing Wright
gateway discovered 26 prefixed tools and proxied `api_reference(Model.box)`.
Catalog checks: **17 passed**. The first stale 81-entry count failure was corrected
to 82; no existing catalog entry or requirement was changed.

An isolated normal Wright API/workspace runs on port 8891 using separate SQLite,
secret storage, workspace directories and source from this branch. SteveCAD is
installed and active there. The existing runtime on port 8884 remains unchanged.
Native Windows created, generated, inspected, exported and read back a new
50 x 30 x 3 mm coupon with four 4.5 mm through holes. SteveCAD reported one solid,
the requested bounds and a volume matching the plate-minus-holes calculation.
The exact STEP and actual inspection image are retained under
`artifacts/stevecad-demonstrations/qualification/native/`.

A fresh neutral Linux amd64 container discovered 26 tools, read the same CAD
document and inspected it through the existing gateway. The current source was
mounted read-only over the base image; no CAD host was installed. This proves
those remote operations, not Linux CAD creation, container workspace UI, solver
validity or a complete installed-distribution qualification. Attempts 001-004
remain distinct from the passing attempt 005. Fresh OAuth state resolved the
connection failure; an SDK-version incompatibility was not established.

The accepted `workflows/stevecad-coupon-readback.workflow.wflow` process completed
through the normal source runtime in the isolated workspace. Its source digest
is `9f2b416a3915b85968dc710ed6e2b963cd62b38a024d22523fdcc7b3101c2cc3`;
run `84559589afc54e12b7eac254ad57bd17` recorded the output
`qualification/source-readback/document.json` with SHA-256
`a28fd2e3487721368cb79b7eea0a0154d6ab7bd92e5960cc102cee27a2f3dd61`.
This is a bounded connection qualification, not a completed engineering demo or
visual acceptance of the workspace UI.

An independently isolated OASiS backend executed a small scikit-fem readiness
probe through this workspace's gateway. The provider returned
`completed_unverified`, `trustworthy_result=false`; its genuine review requirement
remains. This is not structural or thermal compliance evidence.

## Portfolio after connection

1. **Structural equipment mount:** reuse the existing lightweight-equipment-bracket
   assignment and structural profile. SteveCAD produces editable CAD and exact STEP
   revisions. A qualified existing structural/meshing provider consumes that
   geometry for loads, mesh refinement and stress/displacement evidence. Required
   checks cannot be substituted with a render or a provider success message.
2. **Heat-spreader comparison:** reuse the existing conduction sizing process and
   its analytical, heat-balance and mesh-stability checks. SteveCAD produces measured
   candidate geometry; the existing OASiS path consumes exact dimensions linked to
   exported geometry. Dimensional idealization is disclosed; arbitrary STEP
   topology import is not claimed without proof.
3. **PCB enclosure fit:** build on the existing sensor-interface PCB and enclosure
   examples. KiCad supplies an actual constrained board/mechanical envelope;
   SteveCAD builds the housing around it. Required electrical checks and mechanical
   clearances are verified independently. The catalog records a limited KiCad DRC
   path; do not claim full board readiness until a qualified path exists.

Each process retains exact source/input/output identities, digest-bound handoffs,
082 validation and genuine review authority. Missing capabilities block the
affected stage. Geometry, loads or requirements changes invalidate dependent
assessment/drawing/render outputs. Common working views and the refined editor
remain the fallback; new process interfaces are optional and version-bound.

## Outstanding

Preserve the original numerical requirements; qualify the remaining
supporting capabilities; complete the three engineering processes through the normal
workspace; retain attempts and revisions; verify outputs; then create images,
captions, posts and storyboard from actual results. Those engineering outcomes
and social assets remain pending. The reusable goal prompt is saved in
`docs/demos/stevecad-goal-prompt.md`.
