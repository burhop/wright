# Independent scoped-copy review

Date: 2026-09-12. This review checks copying authority, byte identity and runtime
artifact handling. It does not qualify engineering contents or authorize any
printer, supplier or external operation.

## Findings and resolutions

1. **Duplicate runtime integration wiring.** Copy authority was initialized
   twice, and each call prepared and emitted the authorization audit twice for
   one request ID. The implementation agent removed the duplicated blocks and
   added exact authorization-event counts.
2. **Unbounded identity reads.** The immediate dispatch guard used `read_bytes`
   for source/input identity checks after an earlier bounded policy check. A
   concurrent change could grow a file before that recheck. It now uses the
   existing confined, bounded streaming identity helper; policy source/input
   limits remain unchanged.
3. **Copied-byte integrity failure, reproduced on Windows.** An independent
   writer changed the visible temporary file during the fsync hook, before its
   identity snapshot. The operation returned success with the source hash while
   the destination contained different bytes. The source was unchanged.
   The implementation now creates its Windows temporary file with a native
   read/write handle that denies other writes/deletion through publication,
   hashes the actual copied inode against the authorized source, and verifies
   those bytes **before** the atomic no-overwrite link. Permanent tests inject
   both an independent writer and owner-descriptor corruption; corrupted bytes
   must never reach the publication function.
4. **Windows receipt-path alias, reproduced.** A fixed destination differing
   only in filename case could equal the saved receipt path on disk while
   passing a string inequality check. Resolved filesystem path comparison now
   rejects this collision; the Windows regression passes.

The two independent reproducers are retained in
`.local-run/feature-081-live/campaign-execution/test_copy_temporary_review.py`.
Original failing test evidence used `pytest-copy-independent-review` and
`pytest-copy-alias-review`. These were isolated temporary workspaces only.

## Verified boundaries

- Private permits require the exact native workflow session/principal,
  workspace, argument digest and current unexpired authority, and are single use.
- Current immutable automatic integration grants bind the source definition,
  inputs, exact tool/server/schema and fixed canonical source/destination args.
  Agent-selected/dynamic copy arguments cannot borrow the permit.
- A generated source needs verified current-run `EngineeringResult` evidence,
  matching hash/size and a prior canonical producing step that declared the
  file. The engine installs its own verified results before each step, including
  results authenticated during continuation restoration.
- Source/destination paths remain workspace-confined and inside the enrolled
  attempt where required. Copying never overwrites an existing destination.
  Windows source/ancestor pins and native temporary protection, and POSIX
  directory-descriptor/identity checks, preserve the publication boundaries.
- The copy-time receipt identifies source lineage and marks the new file as a
  mutable working copy, not a published artifact. Only an explicit ordinary
  `expected_files` declaration enters the normal file-verification/artifact
  path. The canonical two-copy regression verifies that an undeclared mutable
  destination is excluded from immutable engineering results.

## Verification and limits

The combined independent probes plus copy/write/inspection regression run
passed **76 tests, 3 skipped** in 18.24 seconds. After moving verification before
publication, the final independent probes plus copy suite passed **41 tests,
1 skipped** in 9.44 seconds:

```text
.venv/Scripts/python.exe -m pytest .local-run/feature-081-live/campaign-execution/test_copy_temporary_review.py packages/workspace_service/tests/test_workflow_integration_file_copy.py -q --tb=short --basetemp=.local-run/feature-081-live/pytest-copy-publication-final
```

Skipped cases require symlink privileges unavailable to this Windows test
account. POSIX publication branches were inspected but not executed in this
independent review. No remaining concrete correctness/authority issue was found
within the reviewed scope.

Static tool hashes were compared against the prior deployed pin record:

| Tool | SHA-256 | Result |
| --- | --- | --- |
| `write_text_document` | `66c045c726240dd539b71339450e63e3056b4cf2c8d30954d407c027a17b0b12` | Unchanged |
| `inspect_file` | `b0c9ce7a52c766833056df2615e0a29e4d11641d639b91174da51c8ac9cc330a` | Unchanged |
| `copy_file` | `3d1eb786a6da2edcd2d42e858432377ffcecafc5450c20d50bac6ba7c18cc791` | New tool |

No live API restart, workflow dispatch, native engineering operation or existing
source/grant mutation occurred during this review. Deployment and fresh case
enrollment remain with the campaign coordinator.
