# GPT-5.6 Plan Implementation Status

**Baseline**: `edaded4f88051fe79456ddba1ce0d0859117b8d6`  
**Branch**: `codex/042-security-control-plane-and-workspace-confinement`  
**Feature**: 042 — Security Control Plane and Workspace Confinement  
**State**: review-ready — Feature 042 acceptance and dev merge gate passed
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

| Finding | State at baseline | Feature 042 disposition |
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

Review the local Feature 042 checkpoint on
`codex/042-security-control-plane-and-workspace-confinement`. With separate
authorization, push it and merge it through the normal feature-to-dev process.
Do not start Feature 043 in this unreviewed change.
