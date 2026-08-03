# Operations contract

`GET /api/workspace/workflows?session_id=` lists the workspace catalog and its
review status. `POST /workflows/{slug}/review` accepts `approved` or
`rejected`, a session, and a reviewer. `POST /workflows/{slug}/runs` accepts a
session and starts only an exact approved revision. Status, cancel, and history
use a run ID plus session and reject scope mismatch. All operations return 404
when `WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED` is not explicitly enabled.
