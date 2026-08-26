# CP3H Evidence — Shared UI Execution and Engineer Results

**Status**: Component and build verification passed; live human rerun pending

**Date**: 2026-08-26
**Decision state**: Keep the shared-runner projection; revise diagnostics into typed records

## Ambiguities tested

1. Does the interactive diagram execute the same semantic chain as the
   headless experiment, or merely imitate its states?
2. Can an engineer tell which block is active and inspect every block's result?
3. Can the result view remain understandable without discarding exact output
   and evidence?
4. Should the primary action expose fixture topology or configuration state?

## Failures that changed the design

- The UI and headless experiment initially used different execution paths.
- The AI was asked to construct raw BREP history, and valid JSON still failed
  the application-specific ID contract.
- The toolbar mixed actions with fixture names and error/status sentences.
- The first result inspector was a continuous raw dump of timestamps, errors,
  output, and evidence.

These were boundary failures, not independent cosmetic bugs. They came from
duplicated orchestration, prompt-based application mapping, unstructured error
strings, and a UI that treated internal state as user vocabulary.

## Prototype correction

- One UI-independent runner owns ordering, stopping, step output, and evidence.
- The UI subscribes to that runner and projects the same step records onto the
  diagram, progress monitor, and inspector.
- A shared typed mounting-plate artifact is the AI result in both UI and
  headless paths. A deterministic fixture adapter compiles exact BREP history.
- Wright's current model is automatic; model and thinking selection are an
  optional override.
- Runtime action labels are `Run`, `Running…`, and `Retry`.
- The block result view now leads with status, duration, a bounded result or
  problem summary, and a recommended next step. Exact produced data, IDs,
  timestamps, and evidence are retained in expandable technical sections.

## Verification

- Focused Vitest run: 3 files, 11 tests passed.
- Production web build: TypeScript and Vite build passed.
- Shared-runner component test: all four blocks completed, each progress step
  exposed a result action, and the MCP block's output was inspectable.
- Live headless run: all four blocks passed through current Wright AI and exact
  BREP MCP invocation with three consistent observations.

The remaining live review is intentionally human: refresh the diagnostic page,
run the workflow, inspect each block, and determine whether the new result
hierarchy is understandable at the actual sidebar width.

## Remaining limitations

- Run records are browser-session state, not durable or reconnectable.
- Error data is still primarily a string. The UI can organize it but cannot
  infer a safe field-level remedy without structured diagnostic provenance.
- The BREP adapter is an explicit disposable fixture, not a generic production
  adapter registry.
- Successful BREP mutation proves orchestration, not engineering correctness.
- Cancel, deadlines, retries by stable run identity, and comparison between
  runs remain production requirements.

## Recommendation

**Keep** the shared semantic runner, typed semantic AI output, deterministic
tool adapter seam, automatic Wright model default, stable action vocabulary,
and human-first result hierarchy.

**Revise** runtime failures into typed diagnostics and persist the run/event
record before production implementation.

**Discard** topology-specific primary actions, raw application payloads as the
normal AI contract, and raw JSON/timestamps as the default engineer result UI.
