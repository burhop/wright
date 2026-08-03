# Runner Contract v1

`start(workspace_id, workflow_id, revision) -> run_id | unavailable`; `status(run_id)`; `cancel(run_id)`; `events(run_id, after_sequence)`. Every operation is workspace/generation scoped. Events are bounded, ordered, redacted, and never grant tool authority.
