# Local review before the first engineering operation

The first Modelica attempt-002 run reached the runtime but failed before its
requirements review: approval subjects required a generated artifact even when
the review explicitly consumed an uploaded requirements document. No solver
operation ran. The failed run is retained as
`7374a53285b34463bec2dbafb869fbcf`.

The canonical compiler now preserves the external-action review's connected
document references. For a `local_review` only, exact uploaded-file hashes join
the approval subject and file snapshots. They remain input artifacts: they do
not become workflow outputs or increase the output-complete counter. Restoration
derives the same identities from the current canonical inputs before allowing
continuation. Unconnected uploads cannot supply review artifacts. Printer and
supplier actions retain the requirement for produced artifacts.

Application tests exercise a first-step review with zero model calls and zero
outputs, normal integration auto approval, and same-run continuation to a real
written report. Changed input bytes leave the checkpoint pending, and an initial
uploaded file cannot enable a printer transfer. The focused approval,
continuation and external-action suites passed **29 tests**; Ruff passed.

These are runtime regression results. The API restarted between terminal cases
on September12 before batch007; the fix is now loaded. Fresh Modelica01attempt003
passed ordinary preparation with dispatch disabled and is queued for actual
native solver execution. The failed attempt is never replayed, and preparation
does not establish full workflow completion.

Actual campaign verification at17:52–17:53 UTC: Modelica01attempt003 run
`5c116f76169446d8bcdc44c051cfba79` reached the initial uploaded-requirements
checkpoint, received the exact integration auto approval and resumed the same
run. All three native simulation submissions and their three recorded exports
completed. Final selection reporting then failed at the model context boundary;
that separate issue preserves the real native files and gives no full-process
completion credit. The initial-upload review repair is now exercised by actual
campaign engineering operations as well as the focused regression tests.
