# Workflow UI integration handoff

Updated 2026-09-05 following recovery of the later graphical editor.

## Continue the existing design

The latest located implementation of the user's refined graphical editor is
`codex/080-canonical-workflow-recovery`, commit `87706742` (documentation), with
frontend implementation in `4cfab9ba` and corrections through `629de4f2`.
Backend configuration discovery was corrected in `af069122`.
The local checkout is `.local-run/epp-f02b-writer/wright`.
Read its `specs/080-canonical-workflow-recovery/plan.md`, `north-star.md`, and
image-redesign delivery evidence before proposing another editor replacement.
Its September 2 image-led amendment supersedes the earlier simpler editor
direction. This is the recovered design baseline; it is not a claim of new
user acceptance or complete production execution.

Key implementation files under that checkout's `apps/web/src`:

- `components/chat/WorkspacePanel.tsx`: workspace Workflows entry and tab hosting.
- `prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`: integrated editor.
- `prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx`: live node dragging
  and socket connections. The directory name does not mean this is the frozen
  August prototype.
- `prototypes/workflow-recovery/command-system.ts`: accepted editing commands.

The `codex/081-native-workspace-replacement` UI served on port 5188 is a different,
less capable editor. Do not use its recent commit date or working runtime as
evidence that it supersedes the refined graphical UI. Preserve its runtime work
and user data while integrating capabilities into the established editor.

## Integration contract

The process language is the semantic source of truth. The diagram, contextual
inspector, and reviewed AI changes must operate on the same accepted definition.
Layout positions are separate presentation state; execution records describe the
definition that actually ran. Invalid source drafts must not replace accepted
state. Saving and reopening must preserve source and compatible layout.

The recovered editor uses canonical workflow/source services and visible `.wflow`
files. The newer native runtime uses a different native-process model. Their
integration remains open. Map supported blocks, ports, validation, revisions and
execution capabilities explicitly before implementing an adapter. Do not hide
unsupported semantics, introduce a second authoring authority, or replace the UI
to avoid that integration work.

The recovered editor's Example suggestion and Simulate actions are fixed local
examples. Newly authored templates remain unbound drafts. Their visible success
does not prove live model generation, MCP execution or native-runtime integration.

## Required evidence before claiming UI readiness

1. Record branch, commit, checkout, frontend URL, API target, workspace, enabled
   feature flags, and the screenshots used as the design reference. Verify what
   the browser actually loads, not merely the source in the current directory.
2. Enter from a normal workspace using Workflow/Workflows. Verify this opens the
   established canvas and does not launch Rivet or send the user to a detached
   form. Preserve file tabs and workspace context.
3. Exercise object creation/configuration, live dragging, exact port connection
   and mismatch rejection, pan/zoom, Diagram/Source views, invalid source
   containment, Undo/Redo, and Save/reopen including positions. Exercise conflicts
   when persistence changes.
4. Compare current screenshots with the latest user-reviewed design at realistic
   viewport sizes. A canvas must dominate the workspace; controls must remain
   reachable. Do not substitute passing unit tests for this comparison.
5. State backend implemented, UI integrated, browser verified, and user accepted
   separately in completion reports and the existing dashboard. Associate each
   claim with its build and evidence. User accepted requires actual user feedback;
   agent verification cannot set it. Keep simulated execution visibly separate.

These checks apply to workflow-facing integration changes, not every unrelated
edit. Reuse the existing browser acceptance harness instead of repeatedly
inventing tests or requiring the user to rediscover regressions.

## Current local recovery

The preserved editor was restarted at
http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51?workflow=canonical
with its API on port 8018 and existing workspace database.
The local restart script is `.local-run/ui-recovery-current/start.ps1`;
`session.json` alongside it records the launched processes. It refuses occupied
ports rather than terminating unrelated services. Port 8765 remains the separate
implementation dashboard.

Fresh acceptance evidence in the recovered checkout:
`artifacts/ui-walkthrough/image-redesign/20260905T145418Z-restored-editor-20260905/`.
All 32 existing functional/responsive checks passed, including live drag,
source/layout save and reopen, conflict handling and actual 200% browser zoom.
The report validator passed. This establishes recovered authoring behavior,
not completion of the outstanding native-runtime integration.

A separate fresh-browser run entered the plain workspace URL and clicked its
Workflows activity-bar control before exercising the editor shell. All four
checks and the report validator passed:
`artifacts/ui-walkthrough/image-redesign/20260905T145813Z-restored-workspace-entry/`.


## September 6 individual-block candidate

The same 080 working tree now contains the locally verified individual-block milestone. Preserve its direct input editors, AI prompt options, single-server AI MCP task, advanced exact MCP calls, and durable run diagnostics. New workflow starts empty. Run state is separate from the canonical workspace definition; completed badges clear from the canvas.

The app remains on port 5227, API on 8018, and existing implementation dashboard on 8765. Five saved examples are in Wright workflow evidence. See `.local-run/epp-f02b-writer/wright/specs/080-canonical-workflow-recovery/evidence/block-interoperability-20260906.md` for exact names, limits and live browser reports. Local checks passed; user acceptance and the consolidated CI/dev batch remain pending. This is not a new reviewed release or a reason to substitute another editor.
