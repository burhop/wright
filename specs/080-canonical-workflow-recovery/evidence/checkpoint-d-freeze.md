# EPP-F02B Checkpoint D Freeze

## Frozen subject

| Identity                       | Value                                                              |
| ------------------------------ | ------------------------------------------------------------------ |
| Commit                         | `b4a7e996f10ec95f7d24185a43fd1401843db66d`                         |
| Git tree                       | `accd9e1f45634865fa52325b64083096994d70f3`                         |
| Program tree                   | `d18a299b50f50dda3058243b8baf0303f1eab1a6`                         |
| Task file Git blob             | `00f0a73611722f1c8331eca3b8accea1b63f4eba`                         |
| Task file raw SHA-256          | `5cb199486883607ba38111f946673eddd7b83846310837f653054a73762b1ce4` |
| Walkthrough status raw SHA-256 | `9d3428ff30b79163eda5ae954d5dc318a05b92b528fa67d3ad64e9597ffc837b` |
| Completed boundary             | T001–T027 checked; T028–T038 unchecked                             |

The immutable transition is `docs/programs/engineering-process-platform/evidence/transitions/TR-0095.json`: `IMPLEMENTATION_AUTHORIZED → BLOCKED`, revision 95 → 96. The prior approvals are stale, not revoked; the mutating lease is closed. EPP-F02B remains a reversible blocked roadmap item until the combined recovery experience is product-reviewed.

## Preserved evidence

The walkthrough at `artifacts/ui-walkthrough/workflow-composer/20260831T211850Z/` contains:

- 11 logical PASS steps;
- 12 raw and 12 annotated screenshot pairs;
- clickable report, progress, status, capture manifest, and trace;
- an empty captured browser-diagnostics list.

This is automated conformance evidence, not a moderated usability result. It proves a renderer-neutral draft model, validation, immutable revisions, compare-and-swap persistence, a closed API/browser boundary, and matching semantic identities. It does not approve the product UI.

## Product finding

The frozen shell is form-, lane-, and text-list dominated. Its graph is visually constrained, block movement is expressed through numeric positions, ports are not primary connection gestures, and execution/AI/output experience is intentionally absent. The evidence therefore remains useful as a technical foundation while T028–T038 are paused to avoid hardening a likely disposable shell.

The frozen prototype at `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d` is a second read-only evidence subject. It demonstrates stronger block/port/canvas direction but does not prove production semantics, direct manipulation, large-graph performance, accessibility, or moderated usability.

## Known evidence limitations

- API debug output recorded repeated `no such table: engineering_workspaces` messages; the walkthrough still completed, but that noise is not a production-quality claim.
- Two visible diagnostic rows appear in evidence although one status narrative describes a single finding.
- No digest manifest or final semantic snapshot was recorded for the old walkthrough.
- The prototype React Flow renderer set nodes and connections non-connectable/non-draggable; it proved rendering and preliminary accessibility/scale only.
- Prototype 25/100-block timings are single-development-run observations, not benchmarks.

These limitations remain visible and motivate, rather than invalidate, the recovery slice.
