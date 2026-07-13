# GPT-5.6 Plan Implementation Status

## Feature 047 implementation cycle

- **Baseline**: `b6c6703d05c9333762a073664ae81fd07215ce7d`; local and `origin/dev` matched before branching.
- **Branch**: `codex/047-python-oci-release-train`.
- **Roadmap**: R3.1-R3.7. Features 048-051 remain out of scope.
- **State**: review-ready — implementation, requirement audit, and authoritative dev merge gate complete; exact OCI runtime validation remains delegated to CI because the local Linux engine is unavailable.
- **Artifact topology**: `wright-engineering` is the sole public Python distribution; all internal packages, including the not-yet-thinned Hermes plugin, are `Private :: Do Not Upload`. Docker remains the full appliance; GHCR is canonical and Docker Hub is an optional byte-identical manifest mirror.
- **Python evidence**: final gate wheel is 11,066 bytes and sdist is 12,317 bytes. The sdist contains 10 intentional packaging/source files (public source, README, license, metadata, and Hatch's VCS manifest); no apps, internal packages, specs, workflows, tests, screenshots, sandbox assets, caches, outputs, or secrets. Wheel and sdist independently installed and ran from `C:\tmp` on Python 3.11.14, 3.12.11, 3.13.5, and 3.14.2 with no source-tree/private-package access.
- **Release evidence**: two no-publication rehearsals produced identical SHA-256 `ec25cf8559ce498abb3f984ed6f5bc84f5d2a05978412cd6483959f0e8dd5f5d`; every stage recorded `external_mutation=false`.
- **Workflow evidence**: checksum-verified actionlint 1.7.10 passed every workflow. All third-party Actions are pinned to full upstream commit SHAs. Python publication downloads one recorded candidate through TestPyPI verification and protected PyPI; OCI builds one amd64 candidate, smokes/scans/attests its digest, promotes without rebuilding, optionally mirrors the same manifest, verifies, deploys docs, and publishes GitHub Release last.
- **Supply-chain evidence**: root Docker bases/tools use resolved digests/versions/checksums; Node 24 LTS replaces Node 26 Current; micromamba 2.5.0 archive SHA-256 was independently resolved as `cec496f2299f9ceb5f5e23fc2ccf081fffda0c4bc87a6fdab575bf1e04f103b6`; no `apt-get upgrade` remains. Dependency review, CodeQL, Python/npm audits, private plugin lint/package tests, and an 85% ratcheted release-code coverage gate are configured.
- **Focused validation**: 50 release/legacy contract tests passed with one platform skip before the dependency-policy addition; current Feature 047 suite is 34 passed. Focused mypy passes 14 source files with zero findings. Hermes lint passed and 82 plugin tests passed in 132.53 seconds. npm audit reported zero vulnerabilities. pip-audit reported only `PYSEC-2026-1325` in `ecdsa` with no fixed version; a documented expiring exception ends 2026-09-01 and is enforced by code.
- **Container host limitation**: `docker buildx imagetools inspect` resolved the pinned upstream manifests, but `docker info` cannot connect because `//./pipe/dockerDesktopLinuxEngine` is absent. The exact local Docker build/smoke/scan therefore requires CI or a running Linux engine; Dockerfile policy, checksum, shell, workflow, and smoke contracts pass locally. This is a host limitation, not a claimed image pass.
- **Migration/rollback**: existing 0.1.0 remains immutable. A corrected public artifact uses a later patch only after protected release approval. Identical retries resume; differing hashes/digests require a patch. PyPI corrections may be yanked under documented criteria. OCI immutable version/SHA refs never move; quarantine bad digests and restore mutable aliases only to previously verified digests.
- **External prerequisites**: repository administrators must configure/protect `testpypi`, `pypi`, `release`, and `dockerhub` environments and Trusted Publishers. Feature 047 does not claim these external settings exist and performs no publication.
- **Final merge gate**: `scripts/check-dev-merge.sh` reached its own terminal `Dev merge gate passed.` line. Results include 496 Python passed/12 skipped, 82 Hermes passed, 24 frontend files/99 tests passed, production frontend build, strict MkDocs, focused 87.21% release-code coverage, focused mypy with zero findings, clean wheel/sdist builds and installs, and 38 live Playwright passed. The log contains expected mocked/browser fallback diagnostics but no failed gate.
- **Exact next action**: commit/push/merge Feature 047 under standing authorization while preserving `docs/gpt5-6plan.md`; then start Feature 048 in a new cycle.

## Feature 046 implementation cycle

- **Baseline**: `89466673430023a48795046c2aa41b2ebb77745c`; local and `origin/dev` matched before branching.
- **Branch**: `codex/046-gateway-service-and-mcp-2025-11-25`.
- **Roadmap**: R1.6, R2.3, R2.4, and R4.1–R4.3. Features 047–051 remain out of scope.
- **State**: review-ready — implementation, requirement audit, clean artifact validation, real Codex evidence, and authoritative merge gate complete.
- **Current compatibility evidence**: Codex CLI 0.144.1 on Windows; MCP protocol target 2025-11-25; official stable SDK resolved to `mcp 1.28.1` under `<2`.
- **Closed findings**: official SDK handlers replace hand-written protocol framing; STDIO and authenticated `/mcp` use immutable explicit bindings; transport sessions are unique even when clients share a workspace-agent session; no production caller reads or writes recent/global gateway selection; the one-release REST/SSE and launcher seam defaults off and delegates to `GatewayService`.
- **Implemented checkpoint**: provider-neutral discovery/call/resources/management, conservative schemas and reviewed annotations, append-only redacted audit, protocol cancellation/timeouts, scoped list-change notifications, generation-safe runner lifecycle, 42-entry packaged catalog with dated evidence and byte-identical plugin projection, serialized SDK STDIO, authenticated Origin/DNS-rebinding-protected Streamable HTTP, body/rate/concurrency limits, production API composition, and shutdown/reconciliation.
- **Validation so far**: SDK server 4 passed; real/parallel STDIO 4 passed including partial input and EOF; 100-trial two-session isolation and 100-response/notification stress 2 passed; HTTP authentication/binding/reconnect/limit contracts 4 passed; explicit legacy/workspace regressions 35 passed with 1 unrelated skip; official SDK HTTP plus legacy E2E 2 passed; catalog/plugin parity 48 passed; wheel/sdist resource build passed. The ephemeral real Codex harness passed with `codex-cli 0.144.1`, `gpt-5.6-sol`, Windows x64, and observed `wright__workspace_status` plus exact workspace/session output.
- **Migration/rollback**: migration v4 adds only the append-only `gateway_audit_events` table; existing workspace/session/tool rows remain compatible and catalog aliases retain legacy IDs. Roll back the complete Feature 046 commit/image to Feature 045; no reverse data migration is required. `WRIGHT_LEGACY_GATEWAY=1` is a one-release caller migration aid, not an authorization rollback.
- **Final verification**: final `scripts/check-dev-merge.sh` passed all configured sub-gates without skips in 441 seconds, including 473 Python tests, frontend lint/type/unit/build checks, strict docs and live Playwright. Focused mypy passed 17 Feature 046 production files with zero findings; the gate's repository-wide warning-mode mypy reports only duplicate test `conftest` module discovery. Core/tool-registry wheel and sdist candidates installed and imported successfully in a clean environment. The completion audit proves FR-001–FR-028 and SC-001–SC-009.
- **Remaining risks**: Codex host evidence is Windows x64 only; Linux/macOS Codex compatibility is not claimed. Feature 049 still owns removal of the optional Hermes compatibility seam.
- **Exact next action**: commit and merge Feature 046 to `dev` under standing authorization, preserving the operator-owned `docs/gpt5-6plan.md`; then begin Feature 047 in a new cycle.

**Baseline**: `9fd210802c28f8fccbfb96850ca35200f35b11fb`
**Branch**: `codex/045-package-boundary-and-workspace-use-cases`
**Feature**: 045 — Package Boundaries and Workspace Use Cases
**State**: review-ready — implementation and requirement audit complete
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

Complete Feature 045's manifest-driven boundary enforcement, extract workspace
repositories/adapters/use cases, make API workspace routes transport-only, then
run the authoritative dev merge gate before using the standing push/merge
authorization. Feature 046 remains a separate cycle.

## Feature 045 implementation cycle

- Feature 044 merged to `dev` at `9fd2108`; local and `origin/dev` matched and
  the working tree was clean when Feature 045 branched.
- The current call graph confirms `core.workspace` still owns SQLite, files,
  Git, processes, and reverse `tool_registry` imports; `workspace_service`
  selects concrete agent adapters and direct storage; the workspace router
  still performs file/Git/process work and imports another route for refresh.
- Feature 045 maps to roadmap R2.1 and R2.2. R2.3-R2.6 remain out of scope.
- Spec, plan, research, data model, two contracts, quickstart, tasks, and two
  requirement-quality checklists are complete. Cross-artifact analysis mapped
  all 23 functional requirements and 9 success criteria to 43 tasks with no
  critical ambiguity or coverage gap.
- Added the package-graph manifest, AST/dynamic-import/metadata fitness harness,
  shared domain identifiers/errors/ports, workspace application ports/errors,
  and a bounded executor as the first implementation slice.

### Feature 045 validation so far

| Command | Result |
| --- | --- |
| Package/API regression suite | Passed: 277 passed, 1 skipped, 1 warning |
| Focused mypy over changed boundaries | Passed: 0 issues in 64 files |
| Five-package wheel/sdist build and clean-install imports | Passed |
| Ruff, strict MkDocs, public-alpha leak scan, and `git diff --check` | Passed |
| Full `scripts/check-dev-merge.sh` non-browser sub-gates | Passed; Python reported 412 passed and 11 skipped. Existing broad mypy findings remain warning-only under gate policy. |
| Full live Playwright suite | One existing dashboard test missed its fixed 5-second render timeout under suite load while the API remained healthy; all other live tests passed. |
| Isolated failing `dashboard-real.spec.ts` test with a fresh backend | Passed: 1 test in 8.8 seconds, confirming a suite-load flake rather than a Feature 045 regression |

### Feature 045 migration and rollback

- API contracts and persisted workspace/session data remain compatible; clean
  package-install tests cover the new internal dependency graph.
- Roll back as one feature commit. Restoring only the removed `core` runtime
  modules would recreate the forbidden reverse dependencies.
- Exact next action after merge: begin Feature 046 for session-scoped gateway
  lifecycle and removal of remaining process-global activation state.

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
