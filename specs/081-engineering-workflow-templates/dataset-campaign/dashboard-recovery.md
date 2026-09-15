# Recovery dashboard implementation and acceptance

The live dashboard remains at <http://127.0.0.1:8771/>. It polls the original
`/api/status` projection and the new read-only `/api/diagnostics` every two seconds.
The original four counters and their persisted history are unchanged.

At the September 13, 2026 01:30 UTC served-browser check, the dashboard showed
**30 datasets / 29 accepted pairs / 9 complete output sets / 0 validated sets**,
57 unique accepted runtime attempts across all revisions, the last completion at
21:41:24 UTC, a between-case pause and one historical unresolved owner-missing run.
An accepted attempt count excludes prepared attempts and fixture playback.
A recorded running status does not establish that a worker is alive.

The recovery panel shows each family's current-revision completion count and
explicitly recorded readiness/next action. Expand a scenario for its most recent
current-revision successful and failing stage, error code, inferred failure
category, observed stage/run durations, tokens, queue age and fix age. Missing
measurements remain unknown. A duration ending at the runner's terminal
observation is labeled an upper bound; it is not presented as an exact native
duration. No token-cost estimate is made.

The native panel reads the durable native application repository when available:
application ownership, state, process identity, leases, heartbeat, idle deadline
and cleanup receipt. An absent repository or empty session list does not prove
that native applications are closed. This panel cannot start, adopt, quit or kill
applications. It does not change engineering completion credit.

## Persisted sources and updates

`scripts/engineering_dataset_diagnostics.py` projects the campaign SQLite ledger
and optional runner checkpoints without changing them. Its native database
connection is read-only and never initializes/migrates the native schema.
The existing dashboard launcher supplies defaults through the server CLI:

- `--runner-state`: `.local-run/feature-081-live/campaign-runner-state`
- `--native-database`: `.local-run/feature-081-live/data/wright.db`
- `--recovery-state`: defaults to `<campaign-state>/recovery-state.json`

The optional recovery journal records explicit facts using this shape:

```json
{
  "families": {
    "raspberry-pi-enclosure": {
      "readiness": "diagnostic preparation",
      "next_action": "Prove the retained CAD-to-CFD handoff before a full pilot.",
      "fixes": [
        {"at": "<actual ISO timestamp>", "evidence": "<retained probe receipt>"}
      ]
    }
  },
  "scenarios": {
    "raspberry-pi-enclosure-02": {"queued_at": "<actual queue admission timestamp>"}
  }
}
```

Omit unknown timestamps. Only timestamped fixes with an evidence reference affect
the displayed attempts-since-fix count. The journal records diagnostics; it is
not scheduling or approval authority and cannot reset a repair budget. Root
orchestration updates it atomically after material changes. Native lifecycle
records and runner receipts are read afresh on subsequent polls. The separate
older `workflow_campaign_dashboard.py` projects a different saved-workflow
manifest and is not the server behind port 8771.

## Acceptance evidence

- Forty focused tests passed across
  `tests/test_engineering_dataset_diagnostics.py` and the existing campaign
  bookkeeping tests. Coverage includes accepted-run deduplication, fixture
  exclusion, restart/read-only projection, chronological stage observations,
  unresolved historical owners, explicit fix counting, missing measurements,
  cleanup independence, native private-field exclusion and a torn journal.
- Real headless Chromium against the served URL verified 30 scenario rows,
  10 families, all four history lines and the unchanged four counts. It observed
  polling updates, expanded the Pi failure evidence and native panel, and checked
  desktop/mobile layouts with no JavaScript errors or page-width overflow.
- A browser-local simulated diagnostic HTTP 503 retained the ledger counts and
  showed a stale-diagnostics warning. Removing that simulation restored the panel
  on the next poll. It did not alter the service or campaign data.

The acceptance record and screenshots are retained under
`artifacts/engineering-workflow-datasets/diagnostics/dashboard-recovery-20260913/`:
`acceptance.json`, `dashboard-desktop.png` and `dashboard-mobile.png`. The exact
browser check script is
`.local-run/feature-081-live/check-dashboard-diagnostics.cjs`.
