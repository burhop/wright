# Interrupted raw-log lifecycle observation

Date: 2026-09-12. This is campaign execution-status evidence, not engineering
content validation or completion qualification.

## Actual defect and read-only verification

The sheet-metal case01 attempt004 run
`672827db9d6e45deaf418f596650234a` lost its final run-file publication when the
workspace volume filled. The normal recent-runs API reports the owner lease as
`interrupted`; the retained canonical JSON still says `running`. A receipt
refreshed solely on raw-file changes therefore remained running indefinitely.

At `2026-09-12T18:17:34.808153+00:00`, a read-only normal API request and the new
matcher verified this exact incident:

- Raw log:
  `runs/campaign-sheet-metal-supplier-handoff-01-attempt-004/20260912T173841Z-102244ee712f.json`.
- Retained raw SHA-256:
  `954dac0f79b712cddfb2cdc6415264cc827bd630d790606511804a52f3f49d70`.
- Both snapshots contain 63 durable events; the API row has no run ID yet.
- The unique log path, source digest, exact start timestamp, workspace and
  canonical `run_started` identity match. The matching mode is
  `log_source_start_run_id_unavailable`.
- The raw bytes remained unchanged. This check exported no receipt and
  dispatched no workflow or engineering operation.

The earlier storage-reconciliation evidence remains in
`.local-run/feature-081-live/campaign-execution/sheet004-storage-reconciliation.json`.
It records 20 completed source retrieval/read calls and 17 retained source files;
no CAD, solver or external handoff had started.

## Implemented behavior

`scripts/run_engineering_dataset_campaign.py` reads the normal local recent-runs
API at most once per 10 seconds during ordinary observation, with a forced read
when its request future finishes. It matches the exact persisted run before
using the API status. A non-null API run ID must match; absent IDs require the
explicit log/source/start binding above. Event count must match the raw snapshot.

`scripts/engineering_dataset_evidence.py`, exporter revision 4, independently
revalidates that observation. Only a raw `running` record with matched API
`interrupted` status becomes an observer receipt with `outcome_unknown`.
Raw log bytes and hashes remain unchanged. Whole-graph, output provenance,
integration identity and actual-start checks continue to apply. An API status
cannot assert failed or completed execution or supply missing terminal events.

The receipt references a hash-addressed, immutable JSON sidecar under its own
`lifecycle/` directory. The sidecar retains a dated minimal API projection and
the raw snapshot identity; it contains no tool arguments, model prompt or
response payload. Meaningful status/identity fingerprints exclude observation
time. Repeated observations retain the prior dated sidecar and receipt, avoiding
timestamp-only dashboard history growth. An unavailable API cannot erase a
previous observation of the same raw bytes. A later exact API `running`
observation can remove the uncertainty projection, while neither status changes
the four achievement counters.

Refreshing an already projected interrupted receipt from unchanged raw bytes
without lifecycle evidence is rejected. A different raw snapshot requires new
matched evidence. Publication checks the raw hash again, including after output
copying. No lifecycle path replays a start, approval, resume or engineering call.

## Focused acceptance evidence

The following command passed 74 tests in 9.08 seconds using isolated temporary
workspaces and SQLite ledgers; Ruff passed for the three changed Python files:

```text
.venv/Scripts/python.exe -m pytest tests/test_engineering_dataset_lifecycle.py tests/test_engineering_dataset_evidence.py tests/test_run_engineering_dataset_campaign.py -q --basetemp=.local-run/feature-081-live/pytest-lifecycle-20260912-b
```

Coverage includes full runner→exporter→persistent observer status/history
transitions, unchanged raw bytes and counters, bounded/forced reads, restart
without replay, and rejection of wrong workspace/run/path/source/start,
ambiguous rows, later event snapshots, no actual start, stale/future dates,
altered raw hashes and fabricated terminal status. Existing artifact,
whole-graph and uncertain-mutation regression suites remain passing.

## Deployment boundary

The batch008 process was not restarted or retroactively changed. Root launched
batch009 using the tested revision; bracket01 started at 18:20:09 UTC.

Following explicit authorization, the historical sheet004 observer receipt was
refreshed at 18:20:54 UTC using only
`Runner.observe(..., force_lifecycle=True)`, its unchanged original manifest and
exact persisted runner state. No `run_case`, start, resume, approval or engineering
request was issued. The old receipt and runner-state bytes were saved before
publication. Raw run records, enrolled sources, grants and queued manifests
remain unchanged.

The actual served dashboard changed sheet004 to `outcome_unknown`. The baseline
was 30/13/2/0 because bracket01 had independently started; all four counters
remained at that baseline. Global history grew from 750 to 751 entries on the
first observation and stayed at 751 on the second. The scenario's history grew
from 138 to 139 and stayed at 139. Receipt and runner-state bytes were identical
after the second observation. Exactly two normal API GETs were made.

Proof and original receipt/state backups are retained under
`.local-run/feature-081-live/campaign-execution/sheet004-lifecycle-refresh-20260912/`.
`verification.json` records the raw/source identities, counters and history
counts. The immutable lifecycle sidecar hash is
`b9a37fd29552874ac2b23cdfd77aeb42e408f21abcf09ef63248a5ac678a7265`;
the refreshed receipt hash is
`6b7ad217c2916d74118144de632b85da2cd9288087c05e8ccb3e937187538cc5`.
