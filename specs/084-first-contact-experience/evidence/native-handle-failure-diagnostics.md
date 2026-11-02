# Installed failed handle run and local diagnostics

The first actual run of accepted handle revision 2 failed during
`define_geometry_basis_printed_handle_084_first`, before MCP execution. This note
records the actual workspace failure/reopen and local support export. It does
not claim the model transport problem is resolved or the engineering job passed.
Root owns the separately retained raw run/events and transport diagnosis.

Exact subject:

- Workspace: `7e720c97-6048-4a50-944f-2376186db36b`.
- Source: `workflows/replacement-drawer-handle.workflow.wflow`.
- Accepted source SHA-256:
  `5f6c02ac4e09c95d49df705dede9ce1b28e96359b4e6095752d704fa5fd30743`.
- Run: `38442f873e6440cab541927b64f97eec`.
- Frozen input snapshot: `inputs-cfbd0aa3adc549ec99972f78cfc72c8c`.
- Input digest:
  `693e5ff42f528a6b9f5b06e081d7b42d1ff22f37bb3149a2671a8aba9925ff33`.
- Diagnostic canonical record digest:
  `sha256:d6b6efc6c5ad1b629933ffb8e446a97ce6c29bb7f9dd300a69b04d18a1c974ee`.

The installed candidate 2 common view displayed **Process needs attention**,
observed state **Failed**, the geometry-basis step, and the owning backend's
message that the model did not return a response. It retained the model-setup
correction, exact run navigation and no-results state. The browser did not click
Run, retry, cancel, review or any provider action.

The existing **Diagnose this run** controls produced a local preview scoped only
by `source_run_id`, with neither scenario-run nor session scope. The preview
displayed recorded status `failed`, exact source/record digests, recorded start
and execution-end times, two allowlisted timing events out of four total events,
and `SOURCE_RUN_FAILED` with inspect-before-retry recovery. It did not invent a
stage duration, price, provider result or live status estimate. Whole-run empty
task identifiers did not trigger the earlier false omitted-metadata warning.

Export remained disabled before confirmation. After explicit confirmation, one
download completed and export became disabled again. The downloaded JSON was
3,632 bytes, SHA-256
`a350a5c54e9ea65cf4e3efc3a90fa01b41d622139fc605554c6119e273bbb426`, with snapshot
digest `sha256:bd2e50d2a39ee0be47ab01c1083c729adf47720f22c83d83c5cb31cd2b94c036`.
Inspection confirmed the exact failed-run scope and expected privacy categories;
the file contains no confirmation token, private workspace paths, raw prompt,
command or raw model error. No upload occurred. The single-use preview authority
was not saved in the capture report.

The following retained captures distinguish successful assertions from harness
limitations:

- `artifacts/first-contact/084/native-handle-failure-006/`: the first preview
  succeeded, then the harness incorrectly expected a bare SHA-256 in the
  diagnostic contract, which correctly uses `sha256:`. No export occurred.
- `artifacts/first-contact/084/native-handle-failure-007/`: actual failed-run
  display, reviewed preview and explicit local download all succeeded. The file
  is `reviewed-support-export.json`; screenshots and a local WebM are retained.
  A subsequent reopen assertion used an unscoped common-view locator that
  matched multiple mounted tabs. The failed overall harness status is retained.
- `artifacts/first-contact/084/native-handle-failed-reopen-008/`: visible-view
  scoped assertions captured both initial open and reopen as `failed`, with the
  same run, input snapshot, source/input digests and cursor 4. The diagnostics
  panel returned to its initial preview state with no retained confirmation or
  export control; no new preview/download occurred. The final cleanup assertion
  expected zero common views after closing the selected tab, but another
  same-run tab remained. Opening a second URL-created tab can legitimately leave
  the other tab; this assertion does not establish a product close defect.

Across these captures, the only mutations were ordinary workspace activation,
two explicit previews (one abandoned after the harness assertion), and one
explicit local export. Reopening did not repeat execution, prepare new inputs,
submit review authority or export automatically. These were native common views,
so no generated-interface presentation lease existed. The failure and exported
diagnostics screenshots were visually inspected. The captures establish the
installed failure/diagnostics behavior; they do not complete the successful
engineering journey or its later correction proof.
