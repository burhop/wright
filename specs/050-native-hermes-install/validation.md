# Validation: Native Agent-Manager Installation

**Date**: 2026-07-29
**Branch**: `050-native-hermes-install`
**Status**: Local implementation, exact-candidate lifecycle, development gate,
production gate, feature-branch delivery, and pull-request CI are green. No
merge into `dev` or `main` has been authorized or performed.

## Delivered scope

- Hermes 0.19 installs a thin standard-library Wright adapter through its real
  Git plugin interface.
- The adapter installs and invokes the complete `wright-engineering` artifact
  in a manager-neutral, Wright-owned isolated runtime.
- Codex connects directly to the same Wright MCP runtime without using Hermes
  as an intermediary.
- Docker remains a mandatory, independently tested turnkey distribution.
- OpenClaw is future work. It is not a current adapter, compatibility claim,
  acceptance subject, release-evidence subject, or release blocker.

On Windows, pip creates `wright.exe` inside the managed virtual environment as
the normal console launcher for the `wright` entry point. It is not a separate
application, a hand-authored binary, or another distribution surface.

## Exact native candidate

- Distribution: `wright-engineering==0.1.6`
- Wheel: `wright_engineering-0.1.6-py3-none-any.whl`
- Wheel SHA-256:
  `0c502ae19b7e682fd3770f9a5f47cab7636b8d68a42e78a95e36b486c11455e7`
- Source archive: `wright_engineering-0.1.6.tar.gz`
- Source archive SHA-256:
  `a43b60024e24d35beebe40863759ef6126db4245c5ecbd75f57b93b140315094`
- Runtime-extra lock SHA-256:
  `bfaa6fa619d06a793199e0880e9a2f804e55d76399aa95c72f844026cb36d7af`
- UI manifest SHA-256:
  `2fbbfd478f98e7709435f6d0b7cf4f0c35da8aa3285c77367fbbc6ae7d0f4f22`
- Compatibility metadata SHA-256:
  `929f0d7277b6611a26470b9a03289908a79857e4b9782e2e80ad7ede5848417a`
- Previous-stable fixture:
  `wright_engineering-0.1.6+fixture.1-py3-none-any.whl`
- Previous-stable fixture SHA-256:
  `0265eb1585927398ee5e2a68ba6bf2d8827d4d4232237d1c84967c8f29aa5523`
- Final local Docker subject:
  `wright:test@sha256:d858f76fb5ef8b5aa6377d39124dad7209b6dcba0927aab1725905b2a02f29d0`

The wheel and source archive both contain `wright_engineering`, `api`, `core`,
`agent_adapters`, `tool_registry`, `data_vault`, `workspace_service`, the
prebuilt UI, compatibility metadata, and the locked runtime dependency set.
Both passed archive inspection and isolated clean installation.

## Real manager and lifecycle acceptance

The final consolidated acceptance completed in 352.3 seconds and wrote
`dist/native-manager-lifecycle-017.json`.

| Evidence | Result |
| --- | --- |
| Platform | Windows 11 amd64, Python 3.13.5 |
| Hermes | 0.19.0, real Git adapter protocol `hermes-git-plugin-v1` |
| Adapter identity | `5a2620cf8100c1e2e62adcd1bcfdf0d75f0d22d5` |
| Runtime lifecycle | install, start, status, doctor, update, rollback, stop, uninstall, purge |
| Source isolation | Passed |
| Forbidden executables after adapter installation | None |
| Uninstall/reinstall | User data preserved and reopened |
| Purge | Exact Wright-owned deletion boundary passed |
| Codex | `codex-cli 0.144.1`, direct STDIO profile loaded |
| Hermes intermediary for Codex | False |
| MCP SDK | Protocol `2025-11-25`; initialize/list/safe call passed |
| MCP workspace binding | Passed; three Wright tools discovered |

The full process audit observed Git only for the Hermes adapter operation.
Subsequent Wright bootstrap and lifecycle phases passed their forbidden-tool
audit. The audit may observe the generated `wright.exe` entry-point launcher;
that launcher is the expected installed CLI and is not a forbidden dependency.

Separate production-tail tests also installed, updated, and removed the public
Hermes development plugin through Hermes 0.19.0 successfully.

## Test and release-gate record

| Area | Final result |
| --- | --- |
| Spec Kit analyze | 48 functional requirements and 16 success criteria mapped to 96 dependency-ordered tasks; no unresolved critical/high findings. |
| Strict release/runtime typing | Mypy passed all 32 release/runtime source files. |
| Release contracts | 81 passed. |
| Native/release focused suite | 124 passed, 3 platform/external-fixture skips. |
| Coverage gate | 185 passed, 3 skips; 85.15%, above the required 85%. |
| Full Python regression | 746 tests collected; suite passed. No OpenClaw package or product was installed or invoked; OpenClaw is outside this release scope. |
| Frontend | ESLint, Prettier, TypeScript, 25 Vitest files / 105 tests, and production build passed. |
| Browser integration | Complete Playwright integration suite passed with deterministic settings API coverage. |
| Documentation | `mkdocs build --strict` passed. |
| Security | Public-alpha checks, Gitleaks (250 commits), and TruffleHog passed with zero secrets. |
| Python artifacts | Wheel and sdist inspection, clean installation, and imports passed. |
| Docker | Build, non-root/permission contracts, Hermes dependency reconciliation, recovery, Wright API, connected agent, and direct gateway health passed. |
| Hermes adapter | Local mirror generation/validation and real root install/update/remove passed. |
| Workflow/release policy | Native evidence, no-PR-publication, terminal dependency, and rehearsal checks passed. |
| Pull request #79 | All required checks passed on implementation commit `9ad17f1`, including the GitHub Advanced Security CodeQL gate, both CodeQL language analyses, native platform/lifecycle jobs, Python matrices, Windows tests, frontend/Playwright, OCI build/smoke/scan, docs, dependency review, and leak scan. |

`scripts/check-dev-merge.sh` passed without `SKIP_PLAYWRIGHT` or any native
acceptance skip. `scripts/check-prod-merge.sh` then passed end to end without
skips in 1,050.7 seconds. The production run includes the development gate,
security scans, alpha release check, Docker smoke, Hermes mirror validation,
released-interface capability check, release policy/evidence tests, and real
Hermes root-plugin install/update/remove.

Two release-gate portability defects were found and remediated during the final
run:

1. Git Bash could select the disabled Windows Store `python3.exe` alias for
   host-side Docker assertions. The smoke test now prefers the uv-managed
   project interpreter and has a policy regression test.
2. The production gate depended on optional GNU Make on Windows even though its
   targets only wrapped existing scripts. The authoritative gate now invokes
   the mirror and Hermes lifecycle scripts directly and has a regression test.

Pull-request CI found and verified three additional hosted-runner issues:

1. A Windows-behavior unit test changed global `os.name` on Linux, causing
   `pathlib` to construct unsupported Windows paths. The plugin now exposes a
   module-local platform predicate that the test can patch safely.
2. The real Hermes Git-plugin lifecycle used temporary storage on a different
   Windows volume from `HERMES_HOME`, which exposed Hermes 0.19's cross-volume
   handling of read-only Git pack files. The acceptance harness now provides a
   same-volume manager temporary directory without modifying Hermes.
3. GitHub Advanced Security identified a caller-derived filesystem probe used
   only to distinguish a missing Git executable from a missing workspace root.
   Git availability is now resolved independently and the redundant path probe
   is removed. The workspace-service suite passed with 39 tests and one
   platform skip, and the CodeQL security gate then passed.

The broader repository mypy invocation still reports the pre-existing duplicate
`conftest` module warning in its documented warning-only mode. Strict typing for
the changed release/runtime surface is green. The Vite chunk-size and MkDocs
future-version notices are non-failing upstream advisories.

## Delivery state

- Spec Kit completion audit: complete. Tasks T001-T096 are implemented and
  evidenced.
- Worktree audit: all modified, removed, and added paths belong to the native
  manager installation, its release gates, documentation, or regression tests.
  Generated candidate, lifecycle, mirror, and Docker outputs remain ignored.
- Local feature implementation: complete.
- Exact artifact and real-manager validation: complete.
- Development and production merge gates: complete and green.
- Feature commits and Spec Kit delivery record: committed and pushed on
  `050-native-hermes-install`.
- Pull request #79: open as a draft against `dev`, mergeable, and green. All
  required checks passed on the implementation head; the final Spec Kit-only
  bookkeeping head is also monitored before completion is reported.
- Merge into `dev` or `main`: not authorized and not performed.

The feature branch is ready for review and a separately authorized merge into
`dev`. It must not be described as delivered to `dev`, `main`, or production
until the corresponding merge and downstream release train are separately
authorized and verified.
