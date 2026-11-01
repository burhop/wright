# Isolated installed-runtime candidate 036

29 October 2026. This is intermediate local qualification, not installed-plugin
or Windows acceptance. The approved workspace-first story is unchanged.

## Exact composition

- Prototype launcher, bridge and UI source: `0ecf3acc5c8649b1aa18ef0033779baf4880ecf4`.
- Built wheel/runtime source: `2d2e012a4176b4d0c0656670db12552b5bac9d1c`.
- The only implementation difference is the prototype preview launcher. Runtime
  packages and compiled native UI are unchanged between those commits.
- Wheel SHA-256: `853d8fc481ee247faff3ee7e6ebd17d963ec49eda755305c72a549d4559f7a13`.
- Native UI SHA-256: `3e80402bce3890e6ccf7e6abec352bec95ac767f332a85c8746d533a5ae3bf59`.
- 61 frozen runtime packages pass dependency compatibility checking. Python 3.13.12,
  FastAPI 0.162.0, MCP 1.30.0. The complete private package manifest is retained.

## Observed results

| Check | Result | Scope |
|---|---|---|
| Wheel/sdist native packaging validation | PASS | Exact built artifacts |
| Fresh database startup | PASS | Separate loopback service and empty state |
| Home/API routing | PASS after correction | Original installed-wheel reproduction returned HTML for desktop GET requests |
| Focused routing and bridge regression | PASS | 32 tests; routing regression also run in candidate environment |
| MCP connection and resource | PASS | 59 registrations, exact resource hash, app-only file-handler visibility |
| Workspace creation and workflow save | PASS | Real model-visible MCP tools, isolated storage |
| Disconnect/new connection/reopen | PASS | Same workspace, source digest and saved revision |
| Workspace/editor rendering | PASS within stated scope | Actual compiled UI and installed backend; Chromium simulated host at 1100 and 480 px |
| Engineering execution, reviews, rerun | NOT TESTED by this check | Draft bindings remain unqualified; no run started |
| Windows native panel/download/chat restoration | UNVERIFIED | No actual Windows observation |

The initial browser harness incorrectly sent a workflow path with Home, producing
an honest missing-context error. Its next attempt omitted native-file capability
advertisement and displayed the existing fallback. Both failures are preserved
privately. Correcting the simulated host's arguments and capability advertisement
required no product changes. Final rendering recorded no page errors/tool denials.
This check does not exercise native tab opening or claim host capabilities exist
on a particular Windows installation.

Screenshots were inspected: the narrow workspace file-kind label wraps awkwardly;
retain this as a UI-batch correction. File titles remain searchable and the full
name is an accessible button label. Source/Diagram switching preserved the actual
accepted source. This is not independent task-only usability acceptance.

Private reproduction scripts/logs and full dependency pins are in
`.local-run/experience-review/candidate-036/`. The original installed 0.33 plugin,
backend030, credentials, historical workspaces/runs and Windows pilot were not
modified. No credentials were copied into this fresh candidate.
