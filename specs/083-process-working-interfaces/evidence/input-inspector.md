# Input declaration inspector — intermediate checkpoint

Recorded 2026-10-01 on `codex/083-process-working-interfaces`, parent `3ed26700`.
This is partial T027 work, paused at the user's request. T027 remains unchecked.

## Implemented

The existing input inspector now edits versioned input schemas, explicit defaults,
units and retained provider-option configuration through the editor's accepted
command protocol. These are process declarations; they do not mutate an existing
run's input snapshot. Removing metadata is an explicit choice to use inferred
input shape. Existing direct text/file input controls remain available.

A new **User input step** template is an Engineer step with an evidence input and
one structured-response output. Its inspector edits instructions and response
schema together while preserving exact ports and connected evidence. Creation is
a saveable draft with no invented user question, response or engineering default.
Runtime compilation still requires a complete declaration and valid dependencies.
Read-only, active-run and unapplied-source restrictions use the existing editor
guards. No additional executor or runtime authority was introduced.

Nested declaration objects use the existing retained-object envelope, with sorted
serialization and cold source round-trip checks. Corrupt envelopes and wrong
declaration scope are rejected without changing accepted state. Declarations are
bounded to 64 KiB and 24 levels in the inspector; the backend remains responsible
for supported schema, provider options, input values and readiness.

## Verification

The [checked-scope manifest](../../../artifacts/process-interfaces/083/20261001-t027-declarations/checked-scope.json)
records code and report hashes and the preserved baseline.

- **146 tests pass**, zero failures/pending, across six editor modules: command
  system, authoring objects, source parser, integrated editor, declaration helpers
  and the new inspector components. New cases exercise explicit apply/removal,
  normal command acceptance, explicit zero defaults, schema/port identity,
  read-only controls, draft creation, malformed/oversized/deep declarations,
  corrupt retained objects and cold source reconstruction.
- App TypeScript passes. Focused ESLint exits successfully with one existing
  `presentedRun` hook-dependency warning in the integrated editor.
- A fresh production Vite build passes; it does not start a UI service.

These are synthetic source/component checks. No new served-browser inspector
acceptance, actual generated-source backend compiler interoperability, live model,
engineering MCP, physical action or user acceptance is claimed. Earlier browser
evidence proves its previously recorded scope only.

## Preliminary corrections

Initial checks found a duplicate `stableValue` import that changed comparison
behavior, a draft step rejected for empty instructions, and missing identifiers
on the new controls. Those issues were corrected. New test harnesses initially
used an unrelated starter layout; they now use the existing layout hydration
function. A remaining assertion compared JSON key order instead of the retained
object; it was corrected to compare parsed values. Final tests were rerun after
the changes, including added corruption containment.

## Resume here

1. Verify editing/applying/undo/redo/save/reopen through the normal workspace
   Workflow entry, including a new draft user-input step.
2. Compile the actual saved source through the Python compiler and check readiness
   and evidence dependencies, rather than treating a browser fixture as authority.
3. Complete T027 and the two-checkpoint UI recovery and outstanding editor
   regressions in T021/T028.
4. Continue M3: the prepared coding-agent role and actual default-model generation,
   isolated preview, save/update/rollback and reusable interfaces through Wright.

No background service was started during this checkpoint. All four owned final
test/type/lint/build process handles reported terminal exit code zero before the
requested pause. Protected prototype/campaign files and mixed API deltas remain
preserved; nothing was pushed, merged, released or sent to hardware.
