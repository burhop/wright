# Validation: Native Hermes Installation

**Date**: 2026-07-28
**Branch**: `050-native-hermes-install`
**Status**: Local implementation and candidate validation are green; production
native release remains blocked by the released Hermes interface.

## Exact candidate identity

- Distribution: `wright-engineering==0.1.5`
- Wheel: `wright_engineering-0.1.5-py3-none-any.whl`
- Wheel SHA-256:
  `8a35f052e62ba12a35d542cef3cec9677094ab7c9cd3dda09a1582135feeb46f`
- Source archive: `wright_engineering-0.1.5.tar.gz`
- Source archive SHA-256:
  `55d72cae8da10b5a02608529935b303526d32ea82641a9861fe04031ab0e4b78`
- Bundled modules in both archives: `wright_engineering`, `api`, `core`,
  `agent_adapters`, `tool_registry`, `data_vault`, and `workspace_service`
- Final local Docker subject:
  `wright:test@sha256:b191cb369db50fa61eacad6c6c11c3a509c7a61829ca5255598724db81847e72`

The native builder inspected both archives, their packaged UI manifest, runtime
extra lock, compatibility metadata, forbidden paths, and private dependency
policy. A clean Windows base-plugin fixture installed the exact wheel above from
an external wheelhouse. It discovered the `wright` command and `pre_remove`
hook with only `wright-engineering`, `packaging`, and `pip` in the Hermes base
environment. The fixture reported source isolation and no forbidden executable.

The first PR package-matrix run exposed a Windows-to-Linux line-ending mismatch
between `icons.svg` and its byte-addressed UI manifest. The builder now
normalizes text assets to LF before hashing, writes the manifest with explicit
LF bytes, and marks the generated tree as non-text in Git. The regression suite
and rebuilt wheel/source archive validate that the recorded manifest hash is the
hash of the exact packaged bytes on every platform.

## Completed validation

| Area | Result |
| --- | --- |
| Spec Kit analyze | 45 functional requirements + 15 success criteria covered by 90 dependency-ordered tasks; no critical/high consistency findings after remediation. |
| Python full suite | `706 passed, 15 skipped`; skips are existing platform/external-fixture conditions, not a native acceptance skip flag. |
| Release/native coverage | `166 passed, 2 skipped`; 85.04% across `scripts.release` and `wright_engineering` with the unchanged 85% floor. |
| Strict native/release typing | Mypy: 32 source files, no issues. |
| Focused native/release contracts | Prior focused run: `195 passed, 2 skipped`; final release suite: 73 passed; final isolated legacy mirror: 9 passed. |
| Provider-neutral MCP/gateway/workspace | `277 passed, 2 skipped`; provider-neutral catalog, transport, rebinding, concurrent-session, and gateway smoke coverage retained. |
| Frontend | Vitest: 25 files / 105 tests passed; TypeScript, ESLint, Prettier, and production Vite build passed. |
| Browser integration | Playwright: 36 passed on dedicated port 4174. Ports 8000 and 5173 were occupied by user applications and were not stopped. |
| Documentation | `mkdocs build --strict` passed. |
| Artifact install | Wheel and source archive both passed isolated build/install/import and archive policy checks. |
| Docker | Exact final image build passed; non-root user, manifest/entrypoint permissions, dependency reconciliation, setup-pending behavior, recovery probes, Wright API, connected agent, and direct Hermes gateway health all passed. |
| Local leak scan | `check-public-alpha-leaks.py --include-untracked` passed. |
| npm audit policy | Existing generated report passed `.github/dependency-audit-policy.json`; its two high-severity notices are covered by the repository policy evaluator. |
| Workflow policy | Pinned/scoped action and native/release workflow policy tests passed. |

## Merge-gate record

`scripts/check-dev-merge.sh` was run repeatedly while findings were remediated.
It reached and passed lint, formatting, frontend static checks, strict native
typing, metadata, workflow policy, 85.04% coverage, exact native archive build,
wheel/source clean installs, security boundary tests, and the full 706-test
suite. The final monolithic rerun was terminated by the desktop command host
after 2,012 seconds while pytest's output pipe failed with
`OSError: [Errno 22] Invalid argument`; no assertion failure or gate-owned
process remained. The same final tree then passed the complete quiet Python
suite, frontend suite/build, strict docs, isolated mirror, artifact, and Docker
sub-gates separately.

Two documented local-host accommodations were used:

1. `SKIP_PLAYWRIGHT=1` because active user applications occupied the gate's
   fixed ports 8000 and 5173; the complete Playwright suite passed separately on
   port 4174.
2. `WRIGHT_NATIVE_SKIP_FRONTEND_BUILD=1` because the active Vite process held a
   Rolldown native binary open; a fresh production frontend build passed before
   the exact archive build, while clean `npm ci`/build also passed in the final
   Docker build.

This is the documented local host limitation allowed by `AGENTS.md`; T086 stays
open until GitHub executes the source-of-truth gate without those host
conditions.

## Security checks delegated to CI

The desktop safety boundary refused to mount the repository and Git history
into the third-party Gitleaks/TruffleHog containers. Host copies of those tools
are not installed. It also refused a fresh dependency-metadata query for
`pip-audit`. These checks are not waived: the pull-request safety workflow must
run Gitleaks, TruffleHog, and pip-audit with the repository's expiring exception
policy. T085 remains open until those GitHub checks are green.

## Production blocker evidence

The installed released Hermes reports:

```text
Hermes Agent v0.18.2 (2026.7.7.2)
hermes plugins {install,update,remove,list,enable,disable}
Install plugins from Git repositories
```

Wright's production capability probe fails closed with:

```text
released Hermes does not provide python-distribution-v1; Git-only plugins
cannot satisfy native Wright installation
```

No previous stable public native Wright wheel exists, so the real published
install/update/rollback/uninstall/purge sequence cannot yet be exercised. The
fixture and candidate are not substituted for that production evidence.

## Pull request and CI

Draft PR [#79](https://github.com/burhop/wright/pull/79) targets `dev` and remains
unmerged. The first check run found a Windows-to-Linux UI-manifest byte mismatch.
The second found a hosted-Windows `System32` Docker leak into the clean harness
and a platform-specific mypy reference. Each defect received a focused
regression and was fixed before the next run.

A later terminal rerun exposed a short-lived Windows process sampling race in
the harness: the parent exited between `poll()` and `psutil` descendant
inspection. The audit now tolerates only that process-gone sampling boundary,
retains forbidden-child detection, and has a deterministic regression for the
exact race.

All checks on commit `af203ec` passed on 2026-07-28: Python quality and 85%
coverage, Python 3.11-3.14 wheel/sdist matrices on Linux and Windows, Windows
backend/frontend suites, native base isolation on Linux/Windows/macOS, native
lifecycle and required aggregate, Playwright, frontend quality, docs,
dependency review, leak scan, CodeQL for Python and JavaScript/TypeScript, and
OCI build/smoke/scan. The docs deployment job was correctly skipped for a pull
request. No merge was performed.

## Open task audit

- T023: real subprocess-audited first start awaits the released Hermes package
  interface and a previous stable native artifact.
- T073: released Hermes `python-distribution-v1` capability is absent.
- T084: complete published previous-stable-to-candidate lifecycle is blocked by
  the two facts above.
- T087: production gate intentionally fails the real Hermes capability probe.
- T088: completion audit remains blocked by T023, T073, T084, and T087.
- T089: complete; the Spec Kit commit hook ran, the worktree was verified clean,
  and `050-native-hermes-install` was pushed to origin.
- T090: complete; PR #79 is open against `dev`, all checks are green, and the PR
  remains unmerged.

The feature must not be described as production-native-ready, merged, or
released until every open task is resolved. Docker remains a mandatory,
independently green production installation path.
