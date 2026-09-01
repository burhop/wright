# Product / Visual Direction Approval

## Decision

- **Decision**: APPROVED for the exact workspace-owned correction subject below.
- **Reviewer**: requesting user, self-described mechanical engineer; reviewer name not supplied and formal product role not supplied.
- **Human authority source**: the Codex task message beginning “Resume the blocked Wright recovery goal now,” together with the requesting user's subsequent hands-on workspace, vocabulary, density, and interaction corrections in this task.
- **Reviewer timestamp**: not supplied; this record does not invent one.
- **Evidence-record generation time**: `2026-09-01T20:10:20.655Z`.

The requesting user stated that they had reviewed the recovery UI, approved its
product and visual direction, and authorized T051 once the final exact subject
was verified not to materially depart from that experience. Their later review
made the intended direction more precise: workflow authoring belongs inside a
workspace; visible language should use engineering prompts, files, design
documents, models, reports, and company context; the canvas should remain the
primary view without phase/search/header clutter; and compact sockets, cards,
relationships, and component disclosure should preserve detail without putting
all of it on the graph.

This is a direction approval bound to an independently captured exact subject.
It is not represented as a claim that the reviewer executed the final automated
walkthrough, inspected its manifest, or personally performed every documented
control action.

## Exact approved correction subject

- Commit: `38b409bf149a1241cc87cdedd48f83fed16b5050`
- Git tree: `452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6`
- Passing walkthrough: `artifacts/ui-walkthrough/workflow-recovery-usability/20260901T200836Z-continuation-14/`
- Walkthrough manifest SHA-256: `b8764a02ef83dfc52b65714de0cdbb05071feb9c0ebf4f5fde4995a2870cf335`
- Walkthrough result: 24/24 passing steps, 26 raw and 26 annotated screenshots, 59 manifest-bound files, a 65,547,032-byte trace, two expected HTTP responses (initial missing-source 404 and stale-save 409), and zero unexpected console, page, request, or HTTP diagnostics.
- Independent package validation: `Walkthrough artifact structure is valid.`

## Material-equivalence verification

The exact subject retains the approved canvas-first direction while applying the
requesting engineer's corrections rather than broadening into a different
product:

- the workflow is opened only from a real workspace through **Workflows** and is
  stored as one visible `workflows/mounting-bracket.workflow.wflow` source;
- first entry creates and immediately opens the default only when absent;
  re-entry preserves existing source, and later saves use compare-and-swap;
- Diagram, Source, Side by side, inspector, AI review, and the simulated run are
  projections or operations around one accepted definition;
- the nine-step graph begins with three concrete sources—reference images,
  design intent as text/common document, and approved company context—before a
  reviewed design specification, CAD, manufacturing review, and outputs;
- optional groups and bounded search do not decorate this short workflow;
- compact 224 px cards show role, title, run state, and input/output counts;
  small dot sockets retain larger hit targets, edge labels appear on interaction,
  and complete contracts remain in focus/selection/inspector disclosure;
- reusable review detail and stable internal addresses stay behind **Details**;
- live drag precedes a layout-only commit on release, while definition revision
  and semantic digest remain unchanged;
- AI changes remain proposals until review, and run/output evidence stays
  explicitly simulated with honest lineage and demo-fixture limits;
- the fixed-height workbench contains document scrolling at the reviewed desktop
  viewport while allowing bounded internal panels to scroll when needed.

The 24-step exact walkthrough verifies these conditions against the committed
subject. The conditional T051 authorization is therefore satisfied honestly.

## Historical direction baseline

The original exact direction-approval baseline remains preserved:

- Commit: `f9237763d6fa6e9748dfb7b713e753a7fc4b4d17`
- Git tree: `aeca6ab8294dd54112d3e9ac10148537af32b0f0`
- Walkthrough: `artifacts/ui-walkthrough/workflow-recovery/20260901T031913Z-continuation-1/`
- Manifest SHA-256: `f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347`

The prior `c5fb7d8e` / continuation-5 package remains automated formative
correction evidence, not a separate invented reviewer decision.

## Allowed next action and boundaries

The same user authorization permits dependency-ordered, locally safe work
already defined by the approved artifacts. It does **not** authorize push,
merge, publication, release, customer actions, destructive or irreversible
external changes, or a materially different product direction. Production and
customer readiness remain incomplete; T056, T058, and T060 remain open;
EPP-F02B stays `BLOCKED`; EPP-F02C stays proposed and unregistered; and benchmark
readiness remains `0/100`.
