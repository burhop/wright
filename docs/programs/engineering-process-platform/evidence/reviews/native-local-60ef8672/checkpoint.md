# Native local checkpoint at candidate 60ef8672

Attachment note: this report preserves the original preparation observation. The two browser JSON attachments are now clearly labeled review projections omitting only five non-secret revision fingerprints; original captures remain unchanged locally. Consult `attachment-format.md` and `projection-manifest.json.txt` for final filenames and exact original/projection identities. The terminal full-gate result is recorded separately in `full-local-gate.md`.

Candidate: `60ef8672f1f61c2f4942e618638ec8901e9aa9a0`; tree: `7b5747eb5cf79f8193c8561eea70dc813c4eaa50`. This checkpoint was prepared while the complete merge-gate rerun was still running. It records already observed local work, not a final gate verdict, frozen-candidate approval, human study, CI result or dev deployment.

## Completed local Docker and browser observations

The Docker source was `c7f1f218007e35dd2447329789ee95c91740ae4a`, tree `39a3e9b1c1aeca09667d4e7c6c37ba002e47f11c`. Its source was clean before and after execution. One Linux amd64 image build completed with exit 0. The immutable image/manifest-list identity was `sha256:455f0a756e098042dd34aca472875987cedd6708b3ada28949140625128748c8`; platform manifest was `sha256:da8c4c990f284173d5399055dfbe053a64e105908fa898c939d3039beb569cbb`. Revision/version labels were checked.

The normal image smoke, separate schema probe and actual native HTTP workflow each exited 0 with networking disabled. They used the normal entrypoint and supervisor, with no dependency-sync diagnostic override. Both services ran; health and Wright-to-Hermes connection were observed. The authoritative packaged schema was discovered with no runtime specs tree; 12 operations were published. All three development examples saved, reopened and executed. Four artifacts were verified against frozen final bytes, size, SHA-256 and provenance. The disposable container restarted; run snapshots, events, idempotent retry and singular history were retained. The proof container was stopped afterward. This closes the previously reproduced cold-offline-startup defect on this image.

These are local Linux amd64 Docker Desktop observations. The smoke's historical backup/restore message is not a fresh backup/restore test. No different-version update, other OS, credentialed provider, engineering MCP catalog qualification, registry publication or dev deployment is inferred. `docker-result-c7f1f218.json` and retained probe logs record the precise scope. `docker-original-manifest-c7f1f218.json` identifies the original external evidence collection; the selected files copied alongside this report have a separate manifest. All twelve original manifest hashes were checked during preparation without rerunning Docker.

The coordinator restarted the actual API on c7 and ran:

```text
PLAYWRIGHT_INCLUDE_LIVE=1 PLAYWRIGHT_BASE_URL=http://127.0.0.1:5188 WRIGHT_NATIVE_LIVE_SESSION=native-validation-session WRIGHT_PLAYWRIGHT_OUTPUT_DIR=.local-run/native-live-c7f1f218 node node_modules/@playwright/test/cli.js test tests/ui-integration/native-process-live.spec.ts --project=chromium --workers=1
```

Both live Chromium tests passed in 25.5 seconds (completed session 73365). The retained `.last-run.json` reports `passed` with no failed tests. The example-run JSON contains successful concept-brief and package-review runs; the separate recovery JSON contains the original successful mass-check run, its deliberately failed variant and successful correction. Together the files cover all three examples. The recovery JSON explicitly records `mockedRequests: false`. The screenshot and original JSON files are copied without modification. These are two automated real-server tests, not two human study participants or a complete cross-browser acceptance matrix.

All declared milestone quality scopes are identical between c7 and candidate 60. The only intervening change is `tests/program_control_plane/test_evidence_walkthrough.py`, which distinguishes repository HTTP(S) links from local filesystem links. The original c7 tested commit remains the evidence identity; it is not relabeled as a run on 60.

## Independent technical and artifact review

The copied independent report is authored by `native_candidate_review`, who did not author the implementation. It records no remaining actionable P1/P2 from the accumulated technical review on candidate 60 and preserves the scope of preceding editor, runtime/API, MCP, telemetry, governance, Docker, migration and schema closures. It is not the final schema-conforming independent approval record.

The retained read-only archive probe passed on the current artifacts: all 13 frontend manifest entries and six generated chunk references resolve; committed static assets match the wheel and sdist exactly. Runtime dependency metadata and the committed lock identity match. All 669 expected wheel source/resource files and 672 sdist source/resource/config files match the candidate with ordinary CRLF/LF normalization; generated frontend bytes were compared without normalization.

The fresh wheel SHA-256 is `4b6062dc9746a1f43827a18bdd17cb67dbed4be0fb4071d8565b06cb50bab37d` (16,185,904 bytes). The fresh sdist SHA-256 is `63652e7efe45f7c721cb1629c773d313b3792a280d517199fb7b8be673250d62` (15,788,017 bytes). Earlier artifact digests continue to describe their original builds. The independent review did not repeat builds, installs, Docker, browser or full suites.

## Failure history and outstanding work

Earlier evidence remains unchanged. The retained failure index records hashes and terminal failure lines for these completed attempts:

| Attempt | Observed failure | Correction/closure boundary |
| --- | --- | --- |
| eb63344c | Native compatibility ceiling expected schema 16; 152 passed, 10 skipped, 1 failed | Consolidated migration test corrections at 6d374726 passed the affected 17 checks; original failing attempt remains retained. |
| 53ec6694 | Model repository migration-count assertion; 125 passed, 1 skipped, 1 failed in that package | Test expectation advances to current schema 17; independent resource/fixture and assembled-candidate reviews retain the closure. |
| c7f1f218 | Local-link test treated the canonical repository URL as a filesystem path; 360 passed, 1 skipped, 1 failed | 60ef8672 excludes HTTP(S) URLs from that explicitly local-link assertion and retains unresolved-local-link rejection. |
| 60ef8672, reused test store | Workspace API token-presence expectation; 446 passed, 1 skipped, 1 failed | Coordinator's presence-only investigation identified an old fake test token; a fresh-store focused run passed without source edits. The new complete gate uses a fresh GUID-scoped secrets file. |

The earlier missing-evidence fixture failure is corrected at parent `27b676a5`, preserving no verification/integration credit and rejection of missing, extra or wrong-identity attestations. The strict-docs link failure is corrected at `90c8a32f`, using the canonical repository dev plan URL. Earlier independent reviewer findings and their original probes remain in their existing reports; this checkpoint does not overwrite their results.

At preparation, the repeated complete gate on unchanged candidate 60 had no terminal verdict. Its partial suite output and the fresh-store focused pass do not constitute a complete gate pass. Required fast push/merge checks, terminal CI, final frozen-candidate review, human usability, actual dev deployment and final reporting remain pending. T027–T032 remain unchecked. Implementation is 26/32; the existing current-source verification projection is 0/32 and integration is 0/30, with two integration exemptions. The three examples remain development examples; benchmark qualification remains 0/100 and Rivet migration/retirement remains separately tracked.
