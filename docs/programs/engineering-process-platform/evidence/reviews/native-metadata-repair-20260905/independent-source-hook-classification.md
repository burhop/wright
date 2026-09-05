# Independent public source-hook digest classification

Result: the sole reported `generic-api-key` match is a reproducible SHA-256 of public test source, not a credential. A key-only rename from `auth_addition_lf_sha256` to `source_hook_lf_sha256` accurately describes the value and passes the unchanged pinned scanner. No source behavior, test assertions, scanner configuration, or exemptions changed.

The original finding fingerprint is:

`ea9ad2680fe0b92b9388025162d6fd2eaccce2e4:docs/programs/engineering-process-platform/evidence/reviews/native-docker-40ebc645/live-case-map.json.txt:generic-api-key:10`

The retained adapted test's raw and LF-normalized hashes match its recorded metadata. Its 421-byte LF source hook has digest `f62195c547fae4fc4164f3d8d7bb7b7ac924acb4566a7fdb4fb7ae1c28d38277`. The hook uses an environment-variable reference, contains no credential value, and invokes the existing Unlock form. Removing exactly that hook reconstructs `tests/ui-integration/native-process-live.spec.ts` from tested source `40ebc645ddb641503706dcb3a7d9c84a2b685359` byte for byte, SHA-256 `9120973e6e80f6ad700058a758d5b02ff0d0911a440acd375ae517734949fcff`.

Three fresh, one-commit scratch repositories preserve the exact evidence path and exact configuration from `ea9ad268`. The scanner image is cached Gitleaks v8.30.1, immutable ID `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`. All runs use Git mode, `--pull never --network none`, and redacted logs/reports. Configuration SHA-256 is `69e8c7d0923eead407b001d035547fdf48aea1a3cbc9333273615cebbd0fbf00`.

| Scratch case | Exit | Findings |
| --- | ---: | ---: |
| Original exact mapping bytes | 1 | 1, same rule/path/line |
| Only rename the source-hook digest key | 0 | 0 |
| Renamed mapping plus two synthetic public controls under adjacent credential-like keys | 1 | 2, both controls detected |

Observed scanner window: 2026-09-05T06:54:41.217858Z through 06:54:45.245759Z. These are bounded fixture scans, not a replacement for the required complete candidate history scan.

`renamed-map.json.txt` is the ready key-only proposal. Its SHA-256 is `a586bc540e21556f747d9524341662ceb21d566ce7742defb62dff5173494c96`; original map SHA-256 is `44bef130d1cf5d62676efe802aa9981c58f4b82dcc622f7d9dba1fde8ed5f67d`.

The original failed push-gate log and observation were copied without changes to this scratch directory. Log SHA-256 remains `6554016d2a2d5cf925389718b2f99f71be1f9b5cb46900709bf3edac28de63ad` (83,964 bytes); observation SHA-256 is `2aa26316037795dbbe46874ee1878b1d1c4016eb4ed37ce69c3023e217e91f7b` (645 bytes). The original gate remains a failure; this correction does not retroactively change its result.

Reproduction and complete bounded evidence are in `probe.py`, `source-proof.json`, `source-hook-lf.ts`, `scanner-results.json`, and the three redacted scanner reports/logs. No parent files or original evidence were modified. The parent owns unpublished metadata reconstruction and the subsequent required gate.
