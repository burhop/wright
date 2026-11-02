# Handle setup UI — controlled verification

Date: 2026-10-23. Scope: T007 frontend implementation and controlled component
tests. Installed browser verification, native tool qualification and engineering
acceptance remain separate; this note claims none of them.

The normal workspace workflow editor offers **Set up this job** for an unchanged
`replacement-drawer-handle` starter. Offline exploration remains separate. Dirty
edits disable setup, and accepted semantic revisions use ordinary readiness
without offering starter replacement. Setup operates on the exact existing
workspace, source path, storage revision and digest.

Opening setup requests available matching tools and lists existing workspace
JSON files. It does not execute engineering tools or call a model. Users select geometry,
slicing and inspection tools plus four exact profiles. The managed workspace
path is read-only because this versioned recipe requires the same absolute path
in each provider. Missing capabilities and unknown native qualification remain
visible. The fixed P1S/PETG requirements and the original/Orca process profile
distinction remain explicit; there is no new upload mechanism.

**Prepare setup proposal** requests an inspectable source and dependency
manifest. The form shows the proposed changes, limitations, exact file hashes
and sizes, and saved/proposed source. A separate acknowledgement enables
**Accept prepared revision**. Acceptance sends only the proposal identity and
original source CAS preconditions. The backend owns preparation, dependency
closure, recipe/tool identity, source acceptance and later execution authority.

Changing a selection, source or workspace invalidates the reviewed proposal.
Stale asynchronous responses are discarded. A failed or unmatchable acceptance
is not retried automatically. Successful acceptance returns the exact saved
revision to the same editor; the user then opens the working view for current
input, tool, model and authority checks. No run, review, enrollment or dispatch
is granted by setup.

Verification:

- Final affected service, dialog and workspace-entry tests: **47 passed in
  5.32 s**. They cover explicit actions, exact scope, dirty edits, revised-source
  behavior, missing tools, proposal invalidation, stale context, CAS refusal,
  recipe mismatch and no automatic execution.
- The unchanged template dialog's preceding **9 passing tests** retain the
  normal offline exploration/create path: **56 unique tests** for this slice.
- Application TypeScript check, focused ESLint on seven TS/TSX files, Prettier
  on all eight owned frontend files, and tracked diff checks passed.

Owned frontend files are `services/printed-handle-setup.ts` and its test;
`prototypes/workflow-recovery/PrintedHandleSetupDialog.tsx`, its test and
`printed-handle-setup.css`; `components/pages/WorkflowRecoveryPage.tsx` and its
test; and `prototypes/workflow-recovery/EngineeringTemplateDialog.tsx`, all under
`apps/web/src/`. No native assembly, installation, runtime mutation or commit was
performed by this subtask. Backend setup and manual local simulation have
separate implementation/review evidence.
