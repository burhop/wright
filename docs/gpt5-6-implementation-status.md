# GPT-5.6 Plan Implementation Status

**Baseline**: `49bf248d48ccecbb9216530cf2bed8ea5b072ac3`
**Branch**: `codex/044-state-migrations-and-recovery`
**Feature**: 044 — State Migrations and Recovery
**State**: review-ready — implementation and authoritative merge gate complete
**Updated**: 2026-07-10 America/New_York

## Baseline reconciliation

- Local `dev` and `origin/dev` were identical at the baseline commit.
- Refreshed `origin/main` is five commits ahead by topology; its net content
  delta from `origin/dev` is only the two-line Python publication artifact-path
  correction. That release-only delta is recorded for Feature 047 and is not
  mixed into this security feature.
- Specs 039-041 are present and marked implemented. Spec 040 adds stable
  workspace/session associations but retains a global active gateway context;
  it does not close SEC-01 or SEC-02. Spec 039's publication dependency issue,
  and Spec 041's artifact-identity gaps, remain assigned to later features.

## Finding state

| Finding | State at baseline | Roadmap disposition |
| --- | --- | --- |
| SEC-01 | Open: wildcard CORS, unauthenticated routers and WebSocket | In progress |
| SEC-02 | Open: direct backup joins, global `/tmp`, lexical containment | In progress |
| ISO-01 | Changed by Spec 040 but open for concurrent gateway sessions | Feature 046 |
| SEC-03/04, CTR-01 | Open | Feature 043 |
| DATA-01 | Open | Feature 044 |
| REL-01/PKG-01 | Open; origin/main has only artifact-path correction | Feature 047 |

## Validation ledger

| Command | Result |
| --- | --- |
| `git fetch --prune origin` | Passed; metadata only |
| `git rev-list --left-right --count HEAD...origin/dev` | `0 0` |
| `git rev-list --left-right --count HEAD...origin/main` | `0 5` |
| `uv run pytest -q apps/api/tests/test_security.py apps/api/tests/test_webmcp.py apps/api/tests/test_workspace_api.py packages/core/tests` | Passed: 62 passed, 1 skipped, 1 warning (commit `ac3163d`) |
| Ruff/pytest/MkDocs after the browser-session follow-up | Aborted by operator after 4.9s; do not treat as passed |
| Focused SEC-01/SEC-02 suites | Passed: 56 passed, 1 skipped, 1 warning |
| Agent/security regression suites after test initialization fix | Passed: 13 passed, 1 warning |
| Ruff check and format over API and Python packages | Passed: 115 files formatted; no lint findings |
| ESLint and TypeScript | Passed |
| `npx prettier --check apps/web/` | Failed on 33 untouched files due to CRLF checkout; `--end-of-line auto` passed |
| Python distribution dry run | Passed for `wright-core` and `wright-tool-registry` |
| `uv run pytest -q` | 336 passed, 11 skipped, then suite-order `test_mcp_engine` failed with zero registered mock tools; the test passed in isolation |
| Hermes plugin suite | 80 passed, 1 Windows failure because the test expects one `Popen` while current code starts the gateway and API |
| Frontend unit tests and production build | Passed: 24 files / 99 tests; build passed with existing chunk warning |
| Strict MkDocs build | Passed |
| Manual live Playwright sub-gate | Passed: 38 tests with a loopback compatibility-mode backend |
| `D:\Program Files\Git\bin\bash.exe scripts/check-dev-merge.sh` | Passed end-to-end in 405.7 seconds; no sub-gates skipped. Existing mypy findings remain warning-only under the gate's configured policy. |

## Implemented checkpoints

- Commit `ac3163d` was pushed to
  `origin/codex/042-security-control-plane-and-workspace-confinement`.
- That commit adds the Feature 042 spec/tasks, audit plan and status ledger,
  fail-closed bearer-token middleware, explicit CORS origins, WebSocket
  pre-accept authorization, shared `WorkspacePath`, fixed-format backup IDs,
  workspace-local scratch mapping, symlink/reparse rejection, and focused tests.
- A second, uncommitted follow-up adds an HttpOnly browser-session exchange,
  cookie-aware HTTP/WebSocket authentication, extra WebSocket tests, Docker
  bind/token configuration, and `docs/security/control-plane.md`.
- The second follow-up has been formatted but its combined Ruff, pytest, and
  strict MkDocs command was interrupted before completion. Preserve and verify
  these files before committing; they are intentionally left in the worktree.
- Continuation verification made API test authentication mode deterministic
  before app import and made the merge gate's temporary loopback backend select
  compatibility mode explicitly. Enforced mode remains covered by focused
  security tests.
- Final verification narrowed test initialization to `WRIGHT_AUTH_MODE=compat`
  so package tests do not inherit the API's mock-runner flag, corrected the
  Hermes launch test to identify the API subprocess independently of the
  gateway subprocess, and made the Windows merge gate use the project Python
  runtime and line-ending-portable Prettier validation.

## Migration and rollback

The intended authentication compatibility rollback is
`WRIGHT_AUTH_MODE=compat` for local-only use during one migration release.
Unsafe path behavior has no rollback switch; legacy scratch files must be moved
under each workspace's `.wright/tmp` directory.

## Exact next action

Review and commit Feature 044, then use the standing operator authorization to
push and merge it to `dev`. Start Feature 045 only from the resulting reviewed
`dev` baseline in a separate feature cycle.

## Feature 043 implementation cycle

- Feature 042 merged to `dev` at `0bceb60`; local and `origin/dev` matched when
  Feature 043 branched.
- Added provider-neutral references, environment/mounted/fallback providers,
  and lock-file plus fsync/replace atomic fallback storage.
- Settings and MCP reads expose status only; Git tokens leave SQLite and use
  askpass rather than URLs or argv.
- Added backup-first, verify-before-delete legacy credential migration and
  explicit restore support with fail-closed startup.
- Redacted MCP protocol/subprocess diagnostics and API log responses.
- Removed sudo/universal keys; default Compose uses narrow volumes, read-only
  rootfs, dropped capabilities, and no-new-privileges; legacy layout is
  migration-only.
- Added atomic merge-only YAML updates preserving unknown provider/MCP entries.

### Feature 043 validation so far

| Command | Result |
| --- | --- |
| Core provider, concurrency, redaction | 7 passed |
| MCP credential compatibility | 33 passed, 1 warning |
| Settings/security | 6 passed |
| Git askpass/redaction | 3 passed |
| MCP protocol/log redaction | 27 passed, 1 warning |
| Secret migration plus workspace/settings regressions | 47 passed, 1 warning |
| Container/workflow contracts | 13 passed |
| Provider merge and Hermes sync | 5 passed |
| Compose render: default, minimal, legacy override | Passed |
| Focused SEC-03/SEC-04/CTR-01 regression suite | 120 passed, 1 warning |
| Seeded-value production scan and shell syntax checks | Passed; removed the remaining legacy default from native Hermes profile setup |
| `D:\Program Files\Git\bin\bash.exe scripts/check-dev-merge.sh` | Passed end-to-end in 317.3 seconds; no sub-gates skipped. Existing mypy findings remain warning-only under the gate policy. |
| `docker info` / image-runtime smoke | Not run: Docker Desktop Linux engine was unavailable (`//./pipe/dockerDesktopLinuxEngine` missing). Static contracts, shell syntax, and Compose renders passed. |

## Feature 044 implementation cycle

- Feature 043 merged to `dev` at `49bf248`; local and `origin/dev` matched when
  Feature 044 branched.
- Replaced API-owned monolithic schema/catalog mutation with data-vault-owned
  numbered, checksummed, per-migration transactions and a durable ledger.
- Added fresh and partial-legacy adoption, integrity/foreign-key preflight and
  postflight, future-version/checksum refusal, stable lifecycle locking, and
  fail-closed API startup before runtime construction.
- Added consistent SQLite snapshots, restricted manifests, digest and schema
  validation, displaced-state recovery, atomic restore, and corrupt-state
  replacement from a verified backup.
- Added internal `wright-db` status, backup, upgrade, and restore operations;
  catalog reconciliation now runs separately and preserves unknown servers.

### Feature 044 validation so far

| Command | Result |
| --- | --- |
| Data-vault migration, interruption, backup/restore, CLI, and state-store suites | 18 passed |
| API startup plus catalog separation/reconciliation | 12 passed |
| Full API and tool-registry suites | 196 passed, 1 warning |
| `scripts/benchmark-database-recovery.py --size-mib 1024 --limit-seconds 300` | Passed on Windows: 1,074,900,992 bytes; backup 11.565s; restore 22.430s; total 33.995s |
| Data-vault and public CLI wheel/sdist build plus clean-install imports | Passed after making the shared build helper select `Scripts/python.exe` on Windows |
| Wheel content/dependency inspection | Data-vault wheel contains migrations, backup, CLI, models, lock, and entry point; public `wright-engineering` wheel has no `Requires-Dist` entries; data-vault is `Private :: Do Not Upload` |
| `uv run pytest -q` | 381 passed, 11 skipped, 1 existing Starlette deprecation warning |
| `scripts/check-public-alpha-leaks.py --include-untracked` | Passed; also corrected three tracked Feature 043 placeholder literals newly visible to the scanner |
| Ruff check/format, strict MkDocs, and `git diff --check` | Passed after formatter reconciliation; MkDocs emitted only existing informational notices |
| First `scripts/check-dev-merge.sh` attempt | All non-browser gates passed; live Playwright had one transient cross-origin `page.evaluate(fetch)` failure in `dashboard-real.spec.ts` |
| Live-test stabilization and reproduction | Replaced the browser-context cross-origin fetch with Playwright request context; isolated live test passed |
| Final `D:\Program Files\Git\bin\bash.exe scripts/check-dev-merge.sh` | Passed end-to-end in 315.4 seconds with no skipped sub-gates; data-vault has zero mypy findings and existing repository findings remain warning-only under gate policy |
