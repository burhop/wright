# Candidate 036 revision 8: exact observation-file handoff

The saved handle adds one deterministic use of Wright's existing document writer.
Its `content` comes directly from the connected recorded slicer response, without
an AI rewriting/staging step. Inspection and final validation receive the verified
file output; existing textual references and all seven print-review subjects remain.

The test extracts the actual reference step, compiles and executes it with a
synthetic observed operation and the real document publisher in an isolated
SQLite workspace. Success proves exact bytes and output-port attribution; denied
workspace-write permission publishes no file. This does not qualify the real
engineering workflow, grant process review or authorize printer actions.

- Python affected suite: 37 passed (`pytest-final.txt`).
- Editor source roundtrip/layout/contract suite: 13 passed (`vitest-final.txt`).
- Actual compiled editor save/reopen: PASS, exactly one guarded save.
- Storage revision: 8.
- Storage digest: `6fb178e5e5ad1ccbf54d8852a17fd4d4c203866e831459ccf758acffb293e92a`.
- UI resource SHA: `86469620a5ec563923bde8981369aa8aeb3d473feb1387a52838dda6c65ac066`.
- Source comparison proves only two existing input lists changed; the retention
  task and its three connections are new. All other fields remain identical.

Source review found no focused blocker. The reviewer did not execute tests or
observe Windows. The full diagram is a tiny overview: it demonstrates persistence,
not readable controls or usability acceptance. No workflow run, review, engineering
provider call, account change or installed plugin update occurred.

The existing run-path/1 document stage does not support automatic same-run
producer correction. Do not replay an uncertain write or reuse its path. Full
reruns receive new run directories. Inspection/selection code dependencies and
final independent validation remain required before execution. Candidate backend
still predates the new observation option; coherent rebuild remains required.

Private driver and detailed receipts:
`.local-run/experience-review/candidate-036/save-retained-observations.mjs` and
`retained-observation-save-01/`. The driver guards exact revision 7/digest and
allows read/editor-draft/save/history only. Earlier test startup stalled in the
sandbox and was interrupted; final isolated tests ran outside it. An initial
Vitest invocation used the wrong working directory; the final command uses
`apps/web` and passes. No gate or Windows claim follows from those attempts.
