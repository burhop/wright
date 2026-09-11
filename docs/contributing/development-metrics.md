# Development progress tracking

The standalone development dashboard provides observational charts independent
of the committed program bundle. Its loopback server owns the read-only metrics
and collector-health routes. The structured event store and compiled dashboard
can later feed a customer-facing site without coupling QA collection to Wright's
product UI. Collection does not change readiness, task approvals, benchmark
qualification, or release authority.

## Existing standalone dashboards

For a dashboard served by the earlier standalone `server.py` and `index.html`,
build the same chart component as a production embed:

```powershell
node scripts/build-development-dashboard.mjs
.venv/Scripts/python.exe scripts/serve-development-dashboard.py --legacy-root C:/path/to/existing-dashboard --repo D:/path/to/observed-worktree --assets D:/repos/wright/tmp/development-dashboard/assets --data-root D:/persistent-metrics-data --port 8765
```

The adapter binds only to loopback, retains the original status/evidence routes,
and inserts the charts after the existing header. It serves only compiled assets
under `/metrics/` and observational data at `/api/program-status/metrics`.
Use the same `--data-root` for the collector. This path is independent of the
Docker/native application data directory because the standalone dashboard serves
its own metrics API. Verify on an unused port before replacing the old listener.
The original dashboard files remain unchanged for rollback.

## Start collection

Use the **same data directory as the Wright runtime** (`WRIGHT_DATA_ROOT`, or the
parent of `DATABASE_PATH`). The collector writes
`program-status/development-metrics.sqlite3` there. For a container, the directory
must be a shared mount; a host-only database will not be visible inside it.

From the repository's Python environment:

```powershell
.venv/Scripts/python.exe scripts/track-development-metrics.py --data-root D:/wright-data collect --repository D:/repos/wright --watch
```

Task sources come from the existing work registry. Add current work that is not
yet registered with `--tasks FEATURE=specs/feature/tasks.md`. Collection defaults
to 30 seconds and the browser refreshes every 15 seconds. Ctrl+C records a stopped
collector. Failed collection records a failure and exits so a supervisor can
restart it. Reuse one collector for a repository/data-root pair. It can run next
to the existing committed publisher; neither replaces the other.

Collection imports terminal results from the existing test-run ledger with their
original timestamps and stable run keys. On startup it also backfills task-file
snapshots from each task file's Git history, including merged development
commits. Each file is replayed separately so a commit on another feature does
not introduce an unrelated older task population. These points
use actual commit times and are labeled committed checkpoints; they do not claim
to date individual task execution. Repeated imports are idempotent. Missing task
files before a feature existed are not counted as zero progress. To backfill an
already-running collector, run `history --repository PATH` with the same
`--data-root`. A missing historical feature binding is shown as `unassigned`.

To include usage, add `--session FEATURE=C:/path/to/selected-session.jsonl` (repeat
for additional sessions). The adapter reads coding-session `token_count` events;
it stores only input/output counter deltas, observation time and session identity.
It ignores repeated cumulative counters and negative resets. The first observed
record uses its supplied last-call counters. Prompts, responses, commands and
account quota percentages are not stored. Input includes cached input; output
already includes reasoning output. Do not add those subsets again. These token
counts are **not** a reconstruction of subscription quota consumption or billing.
Do not bind one session to multiple features; use `unassigned` when attribution
is unknown.

## Capture QA and activity during work

Wrap a test/review/integration command to record its start and terminal state.
For pytest, generate a new JUnit filename for each run:

```powershell
.venv/Scripts/python.exe scripts/track-development-metrics.py --data-root D:/wright-data run --repository D:/repos/wright --feature F01 --task T012 --stage testing --suite feature-unit --environment windows-python --junit tmp/feature-unit-attempt-1.xml -- .venv/Scripts/python.exe -m pytest path/to/tests --junitxml=tmp/feature-unit-attempt-1.xml
```

The original command exit code is preserved. Existing JUnit paths are rejected
to prevent reuse of stale results; a successful command missing its requested
report fails capture. Tests absent from a JUnit file cannot be counted: `not_run`
is unknown, not zero. Reports include a content digest. Keep the report alongside
your usual verification artifacts. The collector never sums reruns or overlapping
suites. The QA chart selects one suite/environment and shows each attempt.

## Record explicit task stages

The `event` command accepts a JSON file with exactly these common fields:
`id` (stable retry key), `at` (timezone-qualified observation time), `kind`,
`feature`, `subject` (commit or explicitly labeled working-tree/run identity),
and `data`. IDs are immutable: identical replay is ignored, conflicting replay
fails. Example:

```json
{
  "id": "F01-T012-review-attempt-1",
  "at": "2026-09-05T10:00:00Z",
  "kind": "task",
  "feature": "F01",
  "subject": "exact-tested-commit",
  "data": {
    "task": "T012",
    "title": "Validate the browser journey",
    "state": "verified",
    "evidence": "artifacts/review-attempt-1.json"
  }
}
```

```powershell
.venv/Scripts/python.exe scripts/track-development-metrics.py --data-root D:/wright-data event tmp/task-event.json
```

Task states are `queued`, `working`, `qa`, `implemented`, `verified`, `integrated`,
`manual_validation`, and `withdrawn`. A checkbox only establishes `implemented`. Verified/integrated
events require an evidence reference but remain observational reports; the
existing independent validation gates establish authority. Removing a task marks
it withdrawn instead of completed; unchecking or revising it reopens its status.

Other `data` shapes (all fields required):

| kind | data fields |
| --- | --- |
| activity | task, stage (implementation/testing/review/integration), status (started/completed/failed/blocked), summary |
| qa | suite, environment, passed, failed, skipped, not_run (integer or null), evidence |
| usage | session, task, input_tokens, output_tokens (nonnegative deltas) |
| snapshot | tasks: array of task, title, checked |
| heartbeat | status (active/stopped/failed) |

Before advancing a batch, reconcile every task and review finding using the
existing gates. An unresolved task stays open; a superseded task needs a recorded
disposition and replacement. The batch chart exposes remaining stages rather than
turning a high checkbox percentage into a completion claim.

## Visual semantics and limits

The default period is 12 hours; 24 hours, 7 days and full returned history share
the same time axis across activity, QA, task progress and token usage. Batch bars
show the latest observed state. Task curves break across observation intervals
over 90 seconds. Missing data is empty, not zero; failed refresh preserves the
last response with an explicit stale indication. Scope changes appear in task
point hover details. Evidence is available in the expandable observation table.

History is durable across collector/browser restarts. API responses are bounded
to the latest 20,000 events or 16 MiB, and explicitly flag truncation; older data
remains in SQLite. Do not interpret a truncated population as complete. No
automatic collection service or scheduler is installed: the delivery session
must start the collector against its runtime data mount and wrap commands/use
events for granular stages. The existing dashboard alone cannot observe commands
executed outside these hooks.


## Active checkout and collector recovery

The standalone server accepts `--collector-config PATH`. It supervises one collector,
restarts it after exit, and exposes `/api/development-health`. A configuration has
`repository` (active checkout), `tasks` (`FEATURE=relative/tasks.md` entries), optional
`sessions` (explicit token-counter inputs), and `evidence` (relative source paths).
The collector uses `--only-tasks` so archived registries in a different checkout cannot
replace historical feature populations. Existing event history is retained.

The server's `--repo` remains the historical status checkout; campaign arguments remain
independent. The header labels historical status separately from development collection.
The health panel reports the last collector observation and individual source modification
times. An active collector does not imply a changed task list or successful QA. Markdown
QA prose is not converted into passing test records. The coordinator must reconcile the
active checklist and retain structured validation evidence.

On this local dashboard, persistent configuration and restart commands are in
`.local-run/development-metrics/collector-config.json` and `start.ps1`. The server must
be running for its supervisor to operate. Source read errors are recorded as failed
heartbeats and retried on the next interval in watch mode.
