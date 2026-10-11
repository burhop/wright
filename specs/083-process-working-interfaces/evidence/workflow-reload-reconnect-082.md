# Refresh and reconnect without losing the saved run

10 October 2026. Current-build acceptance evidence on build43; no product source
change was needed for these cases. PPT work remains deferred.

## What a user can do

- Cancel a browser refresh when a workflow has unsaved edits and keep the exact
  draft in the editor.
- Save and refresh to reopen the last confirmed revision without an unnecessary
  warning. Explicitly accepting the browser's discard warning restores that
  saved revision, and the restored clean tab closes normally.
- See a failed status read or interrupted progress connection, then use
  **Refresh view** to reconcile the same saved engineering run. The status
  connection has a bounded retry count and never starts another job.
- Open the actual saved drawing after reconnecting and reload the same unanswered
  review without submitting a decision or continuing execution.

These behaviors reuse the existing dirty-tab protection, durable process client,
common working view, result reader and backend run owner. They do not introduce
autosave, another state authority, provider reconnection or automatic action replay.

## Browser evidence

[Refresh verification](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-204-workflow-page-refresh-verified/report.html)
has seven steps on a fresh blank workflow through the normal Workflows control.
It records the actual native `beforeunload` dialog twice: first dismissed to keep
the draft, then accepted to discard a different unsaved change. There are exactly
two saves, and the final source contains the last confirmed saved name. Browser
diagnostics are empty. Native browser dialog events are recorded; the page
screenshots show the resulting editor, not a fabricated dialog image.

[The initial recording](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-203-workflow-page-refresh/report.html)
is retained as a recorder failure. The browser correctly showed the warning and
kept the draft, but the recorder waited for the cancelled navigation to finish.
The rerun handles a timeout/abort only after the matching native cancellation
was observed, then checks the exact unsaved draft. Product behavior was unchanged.

[Saved-run reconnection](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-205-recorded-run-reconnect/report.html)
has eight steps on the retained correction study:

1. Enter through Workflows and open the exact saved process/run.
2. Inject one HTTP503 into this browser's snapshot read. Wright shows the error
   and makes explicit refresh available.
3. Restore reads and refresh the same pending review.
4. Inject HTTP503 into progress reads. One initial request plus three retries
   ends with a specific disconnected-status message; no work is restarted.
5. Restore the connection, refresh, open the corrected PDF drawing and reload.

The five failures are controlled browser-only responses. Their five HTTP and
five console diagnostics are expected and retained. The API remained available;
these are not observations of an actual server outage. All eleven successful
snapshots agree on run, source, cursor, pending checkpoint and output identities.
The source run is `3843a8c98e0f40e1a15f90790a33b6b8`; its checkpoint remains
unanswered. No review, continuation, cancellation or execution endpoint was used.
The actual drawing and disconnected-status screenshots were visually inspected.

All three walkthrough reports validate. Three new blank definitions were created
across the recordings. Two were edited only for the isolated refresh test. No
original engineering source was edited or engineering process started.

## Preservation and limits

The audit verifies all54 run records,64 latest full-wheel output files,28 retained
correction-study source/evidence files and both original wheel/thermal sources
remain byte-identical. The corrected source digest and pending-run identity also
match the earlier audit. The served HTML and three entry assets still match
build43. API8067/PID84296 and UI5250/PID69612 are unchanged. The pre-existing Solid
Edge process22448 was left untouched; no CAD application was launched.

Exact observations and checks are recorded in
`.local-run/process-interfaces-083/mechanical-engineering-20261008/recovery-audit-082.json`.
This narrows M3 status/reopen and M4 disconnect/reload coverage. It does not prove
browser-crash draft recovery, an API restart, uncertain side-effect recovery or
physical cancellation. Existing tests and earlier receipts retain those separate
scopes; these cases do not justify repeating successful CAD work.

The full goal remains incomplete. The dock decision and actual swim-lane
integration remain pending. The next product issue is readability of numerical
findings in the existing engineering reader, while retaining exact measurements
and unchanged assessment decisions.
