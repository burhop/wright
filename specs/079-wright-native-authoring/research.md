# Design Research

## Native boundaries

Use core for pure values/validation, data-vault for persistence and workspace-service for authorized use cases/runtime. Existing `workflow_runner.py` is Rivet-specific; reuse gateway policy, workspace resolution and traces without its serializer/runtime.

## Storage

`connect_state_db` uses `isolation_level=None`: multi-statement writes need explicit BEGIN IMMEDIATE/rollback. Existing workflow-run transitions read then update without state CAS; native terminal states need conditional updates. Migration reader bounds reject newer database versions even for additive tables. Preserve upgraded DB and verified backup; test honest rejection/forward recovery.

## Values and execution

Choose decimal strings/explicit units, exact port identity, a sequential DAG and registered versioned operations. Failed checks link a correction to a fresh run. Floating-point identity, implicit coercion, expressions and arbitrary cycles are unnecessary complexity for this milestone.

## Dashboard

Extend the current-work supplement and coordinate source/package schemas and strict Python/TypeScript readers. Preserve older bundles. Derive task counts and blockers, remove hardcoded F01/F01B current labels, separate tested-subject coverage from report publication time. Keep immutable readiness snapshots intact.

## Renderer

Use a replaceable React Flow adapter, pin `@xyflow/react` to `12.11.6`. Registry metadata observed September 4: MIT license; React/React DOM peers >=17; integrity `sha512-9XsEJNHjatKYndszKTF/bsU7FOP9dJ6V/EQwzy3oMdtqgBuUq7BjKSwkEo+C7s4qHstHQfwwoHA3E8QfpPxZZQ==`. Official [handles](https://reactflow.dev/learn/customization/handles) and [accessibility](https://reactflow.dev/learn/advanced-use/accessibility) document exact handle identities and keyboard support. Keep attribution and Wright-owned commands, and verify custom accessibility. Audit resolved dependencies/advisories and measure bundle impact before freezing the installed candidate. Never copy prototype code or run an open-ended bakeoff.

## Human evidence

Preregister five independent non-author engineers and trace/edit/save/output/recovery tasks. Automated browser checks and agent reviews cannot substitute. User pilot feedback remains distinct from independent acceptance.
