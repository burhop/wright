# Workspace Application Contract

## Public compatibility

Feature 045 preserves all existing authenticated workspace HTTP paths, request fields, response fields, status categories, and visible effects. It adds no required client field and performs no data migration.

## Application boundary

Each operation accepts a typed command containing explicit workspace or session identity and returns a typed result or raises a typed application error. It has no HTTP types and selects no global database, workspace, provider, runner, or notification sink.

Required operation groups:

- lifecycle: create, get, list, update, delete, activate, session list/create/select/update;
- files: tree/list, content/preview/download, create, write, move, delete, backup list/create/delete/restore, execute;
- version control: status, diff, revert, commit, history, push, pull, branch, merge;
- context/config: load/save context, get/update settings, credential status, agent materialization;
- tools: list/toggle selections and status assembly.

## Blocking-work behavior

Filesystem, database, Git, process, and provider work invoked from async operations runs through the injected bounded executor. Every call has a finite deadline; caller cancellation propagates; timeout/cancellation cannot be reported as success. The executor has bounded capacity and an awaitable shutdown.

## Error contract

Application errors use these stable categories:

| Code | Meaning | Transport compatibility |
| --- | --- | --- |
| `not_found` | Workspace/session/file/resource absent | Existing not-found status |
| `invalid_input` | Malformed or unsupported request | Existing client-error status |
| `conflict` | Lock, merge, duplicate, or concurrent conflict | Existing conflict/client-error status |
| `forbidden_path` | Confinement rejects a path | Existing forbidden/client-error status |
| `dependency_unavailable` | Required local executable/provider unavailable | Existing service/internal-error status |
| `timeout` | Deadline exceeded | Gateway-timeout status |
| `cancelled` | Caller or shutdown cancelled work | Cancellation propagated; no false success |
| `internal` | Unexpected safe failure | Existing internal-error status with redaction |

## Notification consistency

After a durable mutation, the use case publishes an explicit scoped notification. Delivery failure is logged as a redacted warning and does not roll back the completed mutation. Routes never import one another to trigger notification.

## Security invariants

- Every file capability preserves resolved containment and no-follow checks.
- Workspace/session identity is explicit; recent activity is never authorization.
- Credentials remain references and never enter URLs, argv, responses, or logs.
- Raw subprocess commands/output are redacted before diagnostic exposure.
- Schema lifecycle completes before repositories/use cases are constructed.

## Compatibility adapters

A retained legacy callable must contain only input adaptation and delegation to one application operation. Its documentation names current callers and a one-release removal condition. New callers are rejected by the fitness suite.
