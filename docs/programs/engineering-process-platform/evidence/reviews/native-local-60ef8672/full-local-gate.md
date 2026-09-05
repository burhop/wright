# Complete local merge gate on native candidate 60ef8672

Observed 2026-09-05T02:32:37Z. `scripts/check-dev-merge.sh` completed with exit 0 and `Dev merge gate passed.` on candidate `60ef8672f1f61c2f4942e618638ec8901e9aa9a0`, tree `7b5747eb5cf79f8193c8561eea70dc813c4eaa50`. The source checkout was clean before and after the run. This supersedes the running observation in the adjacent checkpoint report without changing its historical text.

The full unchanged authoritative script ran through Git for Windows Bash on Windows, Python 3.13.5, Node 25.2.0, using the isolated `.venv-dev-gate`, API port 18091 and UI port 15191. The task launcher supplied private temporary/data paths outside the checkout, a fresh GUID-named test credential store, and explicit empty Hermes configuration paths. No suite or browser gate was disabled. Its private credential store avoids a confirmed prior-run fake-token residue; the earlier failed run and fresh-store focused pass remain separately recorded.

The retained complete log is `.local-run/dev-merge-gate-60ef8672-passed.log` in the owning native milestone worktree. Its SHA-256 is `3b4758ad651920c3f372d4abfc9898d1608bf8d376500dec850a0c6646ea3040`. Execution session 74393 returned exit 0. These local observations do not represent GitHub CI, another operating system or deployed dev evidence.

## Actual terminal results

Counts below retain the gate's overlapping suites; do not sum them into a unique global test count.

| Stage | Passed | Skipped / deselected |
| --- | ---: | --- |
| Program control | 361 | 1 skipped |
| Release | 102 | 0 |
| Native runtime and release/package compatibility slice | 153 | 10 skipped |
| Coverage slice | 235 | 10 skipped; 85.28% against required 85% |
| Security boundary | 51 | 2 skipped |
| Hardening | 80 | 2 skipped |
| Frontend hardening | 19 | 0 |
| API | 447 | 1 skipped |
| Agent adapters | 111 | 0 |
| Core | 143 | 0 |
| Data vault | 126 | 1 skipped |
| Model registry | 185 | 1 performance case deselected by gate policy |
| Tool registry | 411 | 0 |
| Workspace service | 485 | 9 skipped |
| Remaining root tests | 461 | 39 skipped |
| Hermes plugin | 13 | 0 |
| Complete frontend | 547 | 0; 108 files |
| Playwright configured profiles | 170 | 5 skipped; 5.9 minutes |

Git diff, Ruff/format (646 files), ESLint (zero errors), Prettier, TypeScript, blocking Mypy scope (39 files), distribution metadata, workflow policy, production frontend build, package content/hash checks, both clean package installs/imports and strict MkDocs passed. Broad Mypy remains warning-mode and could not collect duplicate package-local conftest module names; it is not claimed as a passed broad type check. Existing React hook, Vite configuration/chunk-size, deprecation and SQLite resource warnings remain visible in the raw log. No warning threshold was weakened.

The rebuilt wheel SHA-256 is `4b6062dc9746a1f43827a18bdd17cb67dbed4be0fb4071d8565b06cb50bab37d`; source distribution SHA-256 is `63652e7efe45f7c721cb1629c773d313b3792a280d517199fb7b8be673250d62`. Both exactly match the independently inspected archives in the adjacent review. The production frontend build transformed 858 modules. The strict documentation build completed in 3.58 seconds.

## Acceptance and delivery boundaries

Platform, external and opt-in skips are retained, not converted to passing tests. The two native real-server browser cases skipped in the default gate have separate actual c7 execution evidence (2 passed in 25.5 seconds); c7 and 60 have identical production scope. The opt-in real MCP protocol proof has its own earlier actual execution record. Neither automated browser evidence nor an independent technical agent is human usability evidence. Explicit required native acceptance test IDs are recorded separately from the whole-suite counts.

The exact c7 Linux amd64 image passed cold offline startup and actual native workflow/artifact/restart checks as documented alongside this report. No different-version upgrade, fresh full backup/restore, multi-platform container CI, public registry audit or dev deployment is inferred. Prior npm installation output reported four unclassified advisories (two moderate, two high); a fresh npm audit query was rejected by automatic approval review because it may disclose dependency metadata to a public registry. It was not retried or represented as clear.

The complete local merge gate is passed. The required push gate, terminal GitHub CI, final independent frozen-candidate review and actual integrated deployment remain distinct delivery requirements. The standing user goal requires separate publication authorization; the existing dev push workflow publishes container images, so merge must wait for that authorization. Human study and whole-milestone completion remain pending.

The first unpublished author-verification record was rejected for an overlong next-action summary. Its original commit is retained at local evidence ref `refs/codex/evidence/native-author-summary-invalid` (`3ca44cfbc2ad0efcf0ef87898a94a3b6f81687f7`). The summary and dependent record digests were corrected before advancing; validated author record `51754dd8091f51c510d17a155fcc3f9746df9f8c` and frozen record `b85ef464818251972903d6875db72e4198825e36` preserve the same tested implementation candidate. No implementation source or gate result changed.
