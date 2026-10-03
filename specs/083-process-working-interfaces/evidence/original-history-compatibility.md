# Original pumpkin history compatibility

**Date:** 3 October 2026. **Scope:** three original prototype formats on an
isolated current installed native build. T048/T049 remain incomplete.

## User journey and ownership

An existing result link opens its exact recorded workflow/run in Wright's
workspace. The shared historical reader delegates to the canonical recorder,
exposes original result/error identities and permits no execution actions.
Users can return to the same editor, reopen the result and inspect its exact
recorder/artifact in workspace file tabs. No vendor adapter or history-specific
executor is added. Existing source journal checks retain their authority.

The records are the user's actual original pumpkin attempts, read from the
original offline-part workspace and copied into a fresh isolated proof root:

| Original case | Recorded run | Recorded state | Exact retained results |
| --- | --- | --- | --- |
| Failed CE | `997873e33f2143ac90d6bfb9fe02c2e2` | failed; partial results without final result object | 3 |
| PETG | `55f5dbe635a1444e8229314b959f665c` | completed preparation | 16 |
| PLA | `52e77c29cce9456b8f38788f637b7ece` | completed preparation | 16 |

Preparation completion does not establish printer acceptance, physical execution
or engineering acceptance. Missing recorded revisions remain labelled missing;
the UI does not invent them or expose obsolete device controls.

## Current installed artifact

Current source checkpoint `8ea2383b` supplied the package and fresh frontend,
staged away from the repository's packaged assets and existing served builds.
The root wheel passed the repository's native distribution inspector.

- Wheel: `wright_engineering-0.1.9-py3-none-any.whl`.
- SHA-256: `ae0fe0e6554488e29a44588fb7026a3a4a4641883e63d0830c1776690111e691`.
- Frontend manifest: `ea6590bd0ef9c15f1a039bae6672b38c0ea59cee4ed906ed787d310a65820342`.
- All sixteen installed frontend assets match manifest size/digest. Public
  client/kit and fixed runtime bytes match current source.
- Owning API/core/storage/agent/workspace/registry/native modules load from the
  dedicated installed environment; retired prototype modules are not importable.
- Cached third-party dependencies are reused without checkout editable pointers
  or dependency downloads. Compiler and model are unavailable, provider autostart
  is disabled and credentials/configuration are fixture-local.

## Observed behavior and tests

Sixteen browser checks pass through the normal Workflows entry: exact histories,
original failure, 3/16/16 result identities, exact artifact-link counts, editor
return, result reopen, all three recorder file tabs and selected PETG/PLA JSON
artifact tabs. One browser page is retained; no external window is opened.
The final diagnostics have zero unexpected failed responses and zero page errors.
Three expected `/api/agent/models` 503 responses and associated console messages
are disclosed because this fixture has no model service.

API checks independently verify each exact source/run/result set, read-only
state and empty permitted actions. Eight retired demo URLs return HTTP 410
`PROTOTYPE_RETIRED`. No process start, review response or provider action occurs.
All 48 original and copied source/run/artifact/journal files and five durable
UI/authoring/continuation tables remain unchanged. Protected campaign/context
and preserved prototype archives also pass their existing byte checks.

Three added controlled original-recorder-shape cases cover a failed partial-only
record and completed results with either top-level or final-result run identity.
The legacy/exact-recorder suites pass **39 tests**, with no failures/errors/skips.
These controlled tests complement, rather than replace, the real original data
and installed-browser proof. The first setup attempt lacked its temporary parent
directory and produced 39 setup errors; its log/JUnit is preserved. A fresh owned
test root passes. No product repair was required for these original formats.

## Preserved failures and corrections

Browser 001 passed six checks and stopped on a harness selector that omitted
the existing leading slash in a workspace tab identity. Its diagnostics also
exposed an omitted restored default source in the isolated fixture. Normal
Workflows creation initialized that source, byte-identical to the original;
no original file was written. That fixture event is recorded explicitly.

Browser 002 passed all sixteen visible checks but stopped at the diagnostic
audit: copied sources lacked their committed journals. Wright correctly rejected
unauthenticated source reads with `workflow_source_integrity`. Copying the six
original journal files into the isolated root resolved the fixture omission.
No integrity check was relaxed, database substituted or source/history rewritten.
Fresh browser 003 passes the complete diagnostic-strict journey. All three
walkthrough structures validate and failed reports retain their original bytes.

## Evidence, lifecycle and remaining work

Credential-scanned evidence and its 114-file inventory are under
[original-history-verified](../../../artifacts/process-interfaces/083/20261003-original-history-verified/README.md).
See the [successful walkthrough](../../../artifacts/process-interfaces/083/20261003-original-history-verified/workspace-walkthrough/report.html)
and [checked scope](../../../artifacts/process-interfaces/083/20261003-original-history-verified/checked-scope.json).
Authenticated traces, database contents and raw original recorder payloads stay
private. The owned installed host on port 8038 was stopped and its exact process
handle ended with exit 0; that URL is not advertised as a running service.

This closes the three-original-format compatibility evidence gap. It does not
close T048/T049: active slicing implementation/caller migration, provider
qualification and full replacement/generalization proofs remain outstanding.
Safe repeated runs, broader UI/editor acceptance, affected regressions and the
final full requirement audit also remain open. No physical effect, release,
public catalog promotion or user acceptance is claimed.
