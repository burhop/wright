# Jig native execution and model-context repair

Jig02 attempt008, run `45d02124c25e4f46b7a8924dc5b36881`, successfully
created its native jig before the model's next decision failed. Its generation
task started with 24,075 prompt characters and retained these actual tool
observations:

| Tool | Native text characters | Runtime observation envelope bytes |
| --- | ---: | ---: |
| run | 4,497 | 11,037 |
| inspect | 8,353 | 18,773 |
| export | 634 | 1,581 |
| measure | 56,846 | 127,601 |

The measurement requested features with a 200-item limit. Replaying the exact
saved responses and actual tool schemas through the real bridge reproduced
`workflow_context_limit`. Before measurement, the largest translated text
part was already 65,104 characters, near Hermes' 65,536-character per-item
limit. The bridge correctly refused the next request without truncating
evidence or contacting a model. The STEP, STL, DXF and lineage files remain
preserved under the failed attempt.

Future definitions keep the same eight-stage sequence, original three task
IDs, two original edges, design review and independent geometry inspection.
The original `generate_jig` task now directly calls AgentCAD `run` once with
the exact authored script, project directory and fixed execution options.
Wright records its entire native response and requires STEP, STL, DXF and
lineage files. It no longer constructs an AI decision context containing
redundant general-purpose inspection and measurement responses after this
native call.

The independent inspection source remains a separate authoring stage. It must
reopen the actual jig, extract hole/seat/pocket geometry, compare the supplied
datum-transformed coordinates and clearances, calculate keepout intersections,
and retain measured failures and unresolved stackup information. The original
`check_alignment` task directly runs that source and requires
`dimension-report.json`. The final observation task still reads the complete
report and lineage, plus metadata for all three model/drawing files. No
geometric checks or required deliverables were replaced with summaries.

Both authoring stages also inherit the shared AgentCAD source-path correction:
`__file__` is the runner's `<script>` placeholder, so source provenance uses
the exact explicit staged `SOURCE_PATH`. Their explicit `OUTPUT_DIR` and
`PROJECT_DIR` match the actual direct-call arguments. All three jig graphs
and all three Pi graphs passed the focused compilation/source-contract tests;
fourteen tests and Ruff passed. The saved-observation bridge regression ran
offline with zero model or native calls.

Fresh attempt009 was staged and enrolled for all three jig scenarios. Each
has eight stages, eight current grant tool pins, ten exact input files, eight
human-input mapping rows and seven expected source/engineering files. Ordinary
authorization/preparation passed using a lifecycle that cannot start a
provider. Only the three isolated native project-initialization prerequisites
ran. All declared workflow outputs were absent and no new workflow run existed
at handoff. All 425 prior files and 24 prior policies were unchanged; all 214
advertised tool pins matched before and after staging.

Evidence is under `.local-run/feature-081-live/campaign-execution/`:
`jig008-context-diagnosis.json`, `jig009-staging-verification.json`,
`jig009-normal-preparation.json`, and replacement manifest
`jig-attempt-009.json` (SHA256
`b63ee1ce59c36c36123454a3b48f7969f86698354e08b62db65f0042443cbe89`).

No workflow, CAD kernel, solver or worker was dispatched during this repair.

## Final file-observation follow-up

Jig03 attempt009 completed both direct native tasks and sealed the required
engineering files. Its final file-inspection task then failed after its first
32,768-byte read of the 35,692-byte dimension report. The initial task prompt
was 13,324 characters: 680 characters of inspection instructions plus native
response reference blocks of 5,626 and 6,996 characters. The first file read
returned 36,332 characters of structured/text observation metadata and page
content. No subsequent model request was sent.

The final inspection task now has no native-response item inputs. Its existing
order dependency still requires both native tasks to finish, and all five
file checks remain. Removing the bindings alone did not make a 32 KiB page
fit the unchanged bridge, so the existing pagination now explicitly requests
at most 8 KiB per page and follows `nextOffsetBytes` until each file is complete.

The regression fixtures contain the exact failed observation, original prompt,
and full unvalidated report/lineage bytes, labeled as transport-test evidence.
Tests use the real confined file inspector with private unit-test permits and
the real model bridge, without provider or model calls. They reproduce the
old failure and verify all seven pages across both files, totaling 45,342
bytes, reconstruct to identical hashes. Every complete latest page survives
the reversible transcript encoding. For all three offline attempt010 graphs,
the maximum transported text part is 58,637 characters, below 65,536. Fourteen
focused tests and Ruff pass.

`campaign-execution/jig-attempt-010-offline-candidates.json` records three
**offline, non-executable candidates**, SHA256
`f2995a4ebe860f490c700ad88f0556543c46b52727c99371d403db6f9810c26f`.
They use a disposable D-drive workspace and require normal live template
instantiation, current pin verification and enrollment after the active batch
is idle. No live workspace, run, policy or engineering artifact was modified;
no API, native initialization, CAD or workflow call occurred in this follow-up.
