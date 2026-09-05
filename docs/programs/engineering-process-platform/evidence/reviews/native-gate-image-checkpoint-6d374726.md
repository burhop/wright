# Native candidate gate and image checkpoint

Recorded at: 2026-09-05T00:51:31.183826Z by the status reviewer, using the coordinator observations identified below.

Current candidate: `6d374726ad1602754bf7fcfdec1bfdd39937a866`.
Prior gate/image candidate: `eb63344cbebf18d7461fdbdacd7a2224ffe2bfac`.
This is a partial local verification checkpoint, not a passing full gate, final
independent-candidate approval, human study, dev integration or deployment.

## Required local gate

The coordinator ran the required native gate on eb63344c. Its retained log is
`.local-run/dev-merge-gate-eb63344c-native-compatibility-failure.log` in the
implementation checkout. The status reviewer inspected its terminal summaries:

| Executed slice | Observed result |
| --- | --- |
| Program control | 361 passed, 1 skipped |
| Release | 102 passed |
| Native runtime/release compatibility slice | 152 passed, 10 skipped, 1 failed |

The failing assertion was
`tests/native_runtime/test_program_state_compatibility.py::test_packaged_ceiling_tracks_the_complete_program_schema`.
It still required migration version 16 although the implementation and packaged
compatibility metadata correctly declare schema 17. The gate stopped at this
failure; remaining required slices and all skips retain their own obligations.
Existing warning-mode typing output and local pytest-cache permission warnings
were also present. No warning or skip has been recast as a passed check.

The consolidated correction 6d374726 changes five test files: the capability and
model library migration tests, engineering model compatibility test, program
state compatibility test, and program-hardening package-content test. It retains
historical migration scope and checks the complete schema-17 state explicitly.
The coordinator reports 17 affected tests passing after this correction. This
report distinguishes that targeted closure from a complete rerun of the required
gate. No full-gate pass is established at this checkpoint.

## Actual image observation

The eb63344c image was built with exact local image ID
`sha256:9b42a07d3ed4d24eb746daab9a05f5ed5e3a124f51a26c4042178275fa63dbfd`.
The coordinator reports its networked smoke exited 0. Cold startup with networking
disabled failed during dependency synchronization. An isolated correction is in
progress; its candidate and rebuilt image have not been verified by this record.
A successful networked smoke does not establish offline startup or native Docker
acceptance. This local image ID is not a registry manifest digest or dev deployment.

Earlier installed-wheel execution/restart/relocation evidence remains historical
at e4c58d95. It is not promoted into current image, different-version upgrade or
cross-platform evidence. Human study, native dev PR integration, actual deployed
journeys and final milestone acceptance remain pending. Benchmark qualification
remains 0/100; Rivet migration and retirement remain separate future work.

## Review corrections and freshness

The independent editor correction report already retained under
`specs/079-wright-native-authoring/evidence/independent-editor-closure-40826589.md`
closes CR-NATIVE-01/02 at 40826589. Its declared editor source scope matches the
current candidate. The copied governance report closes GOV-NATIVE-01/02/03 at
b3d33812 with the original four independent probes. The copied schema-portability
report accepts b861d2ea after three independent packaging checks. These reports
retain their exact subjects and author/reviewer attribution. They do not provide
a final combined-candidate review verdict.

26 of 32 implementation tasks are checked. Current verification is computed from
actual source coverage: the old combined check is stale after frontend changes.
Do not retain the earlier published 24/32 verified count or promote Q-RUNTIME and
Q-COMBINED without current evidence. Tasks T027–T032 remain pending. The existing
dashboard at http://127.0.0.1:8765/ will be republished by the coordinator after
review/integration of this record; this status work does not publish it.
