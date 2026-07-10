# GPT-5.6 Plan Implementation Status

**Baseline**: `edaded4f88051fe79456ddba1ce0d0859117b8d6`  
**Branch**: `codex/042-security-control-plane-and-workspace-confinement`  
**Feature**: 042 — Security Control Plane and Workspace Confinement  
**State**: in progress — stopped at operator-requested handoff  
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

## Migration and rollback

The intended authentication compatibility rollback is
`WRIGHT_AUTH_MODE=compat` for local-only use during one migration release.
Unsafe path behavior has no rollback switch; legacy scratch files must be moved
under each workspace's `.wright/tmp` directory.

## Exact next action

Resume in `D:\repos\wright` on
`codex/042-security-control-plane-and-workspace-confinement`. Inspect the
uncommitted browser-session/docs diff, then run Ruff, the focused API/core
security suites, and strict MkDocs. Correct any failures, commit and push the
second checkpoint, then continue Feature 042 with frontend authenticated-session
UX, remaining path-operation coverage, full suites, and
`scripts/check-dev-merge.sh`. Do not start Feature 043.
