# GPT-5.6 Plan Implementation Status

**Baseline**: `edaded4f88051fe79456ddba1ce0d0859117b8d6`  
**Branch**: `codex/042-security-control-plane-and-workspace-confinement`  
**Feature**: 042 — Security Control Plane and Workspace Confinement  
**State**: in progress  
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

## Migration and rollback

The intended authentication compatibility rollback is
`WRIGHT_AUTH_MODE=compat` for local-only use during one migration release.
Unsafe path behavior has no rollback switch; legacy scratch files must be moved
under each workspace's `.wright/tmp` directory.

## Exact next action

Add executable SEC-01 and SEC-02 regression tests, then implement the shared
authentication/origin and workspace-path capabilities until those tests pass.
