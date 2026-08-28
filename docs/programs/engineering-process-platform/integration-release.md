# Branching, Integration, Testing, Compatibility, Release, and Rollback

## V8 non-authority

Planning or implementing the closed V8 repair cannot authorize push, PR, merge, dev integration, publication, or release. It cannot refresh candidate/delivery evidence or make any readiness area green. T066 remains outside V8 and requires a separate disposition of the recorded roadmap-policy regression before an unchanged candidate can be independently verified.

This contract incorporates Wright's current contributor and release runbooks. Those scripts/docs remain the source of truth; this file adds program-specific evidence requirements and never weakens them.

## Branch and worktree lifecycle

1. Select only a dependency-eligible roadmap item with current human authority and no active mutating lease.
2. Record the current local/remote `dev` subject. If fetching/reconciling requires external authority, obtain it; a stale baseline cannot become PR-ready.
3. Create a clean isolated worktree and lease. The feature branch is created once through `speckit-specify`'s mandatory `speckit-git-feature` pre-hook.
4. Keep one reviewable outcome. Do not mix unrelated work or prototype implementation. No shared writable worktree.
5. Commit only allowlisted reviewed paths. Automatic `git add .`/bulk commit hooks are forbidden. Inspect untracked/generated/binary/private/credential material, `git status --short`, staged diff, and `git diff --check` before every commit.
6. Do not force-push, rewrite/delete protected refs, push directly to `dev`, or merge/cherry-pick the prototype.

## Push and PR contract

Before every push to a branch with a PR targeting `dev`:

- reread `docs/contributing/dev-push-runbook.md`;
- confirm one reviewable outcome and exact expected diff;
- run `scripts/check-dev-push.ps1` on Windows or `.sh` on Unix at the exact HEAD;
- run required leak/secret/private-output checks for the changed slice;
- obtain external-write authority unless the exact feature charter already grants it;
- record command/environment/duration/result and pushed SHA.

All CI jobs for one pushed commit must reach terminal state before a replacement push. Collect every failing job and first actionable error; classify it. A rerun requires transient evidence. After two failed pushes for the same stable cause, stop pushing, build a deterministic reproducer, and make one consolidated correction.

The PR description binds user outcome, exact spec/plan/tasks/analysis approval, evidence, compatibility/rollback, benchmark delta, risks/decisions, screenshots/video for UI, and limitations. A later commit invalidates prior exact-tree author/independent verification and gates as applicable.

## Feature to `dev`

Before merge:

1. reconcile current `origin/dev` on the feature branch;
2. run `scripts/check-dev-merge.ps1`/`.sh` on the developed OS;
3. document only genuine host-unavailable gates as non-supporting; a failure cannot be documented away;
4. require current CI, review, independent verification, merge authorization and no blocking P0;
5. merge through the PR; never direct-push `dev`.

Integration is not feature completion. On the exact merged `dev` commit, build/deploy the development image, pass service health and the changed user-journey browser smoke, and record image/commit digest plus rollback subject. Restore the durable program context pointer, release the lease, update roadmap/state/risks/decisions/gates and regenerate the dashboard.

## Testing and verification pyramid

Run the smallest causal checks first:

1. schema/static/lint/format and pure validators/reducers/compilers;
2. focused unit/component tests for touched contracts and all feature UX/failure states;
3. deterministic boundary contracts for models/MCP/approvals/artifacts/cancellation/security;
4. focused mocked browser journeys for cross-component behavior;
5. local/system E2E and artifact verification;
6. opt-in clean integration/platform/application evidence only when authorized;
7. diff-aware push gate, then full merge gate.

Every result records exact subject, environment, duration, skipped/not-tested classifications and original failures. Isolated reruns do not erase concurrency/test-isolation failures. Task checkboxes and `speckit-checklist` are not executable verification.

For engineering MCP server validation, follow `docs/mcp-catalog/mcp-server-testing-process.md`: clean selected-server environment, install only its requirements, initialize/tools/list, safe backend probe, Wright gateway proxy, redacted evidence, cleanup, and no MCP-specific host software in Wright's base image/runtime extra for catalog optics. Partial/failed/safety-blocked/unavailable/not-tested never become full pass.

## Compatibility contract

Any feature touching a persisted/public definition, run/step/event/artifact record, API, CLI, manager profile, dashboard/benchmark schema or integration declares before implementation approval:

- schema/interface version and supported reader/writer ranges;
- unknown-major rejection and additive-minor behavior;
- old-reader/new-writer and new-reader/old-writer expectations;
- migration plan, identity, backup/quarantine and interruption behavior;
- prior stable fixtures and historical-state tests;
- restart/offline/update/persist/rollback/uninstall/reinstall/purge implications;
- deprecation notice/window and supersession mapping;
- rollback subject and what cannot be rolled back safely.

Compatibility claims require exact supporting artifact/host evidence per `specs/073-program-hardening/contracts/compatibility-evidence.schema.json`. Another platform, fixture, contract, installed source checkout, stale or skipped run is visible but non-supporting.

Updates are additive/atomic and keep the current runtime usable until activation succeeds. Rollback never implicitly restores an older database or deletes newer state. If an older runtime cannot read current state, keep the compatible runtime active and record an explicit quarantine/recovery path. Purge remains separate, disclosed, path-bound, reference-safe and human-confirmed.

## Security, privacy, packaging, and documentation

Each shippable feature evaluates package contents, third-party dependencies/licenses/notices, SBOM/provenance/attestation/vulnerability impacts, secrets/proprietary-data/authority scans, telemetry/egress/retention/deletion, support diagnostic allowlists, operator/user docs, known limitations and release notes. No automatic support upload or remote telemetry is introduced by the dashboard/program.

Repository settings such as branch protection, required checks, protected environments, secret scanning/push protection and registries are external evidence. Unchecked items in `docs/admin/github-public-readiness.md` remain blockers; code cannot infer them green.

## `dev` to `main` and production release

Production integration requires separate human authorization. Before merging `dev` to `main`, run `scripts/check-prod-merge.sh`. After the PR merge, compare Git **tree** hashes to confirm `dev`/`main` content synchronization; commit IDs are expected to differ.

Follow `docs/release/release-runbook.md` in exact order:

1. preflight and required CI;
2. build one Python candidate set and one OCI candidate once;
3. validate installs, smoke, scans, SBOM and provenance;
4. publish the same Python files to TestPyPI, verify, approve, then PyPI;
5. verify released Hermes Git adapter identity/provenance and direct Codex profile;
6. promote the tested OCI digest to GHCR and copy the same manifest to Docker Hub;
7. run the published native lifecycle on clean Linux, macOS and Windows plus manager MCP probes;
8. verify public packages/digests/attestations with bounded retry for registry propagation—never rebuild/republish the same version;
9. deploy versioned docs;
10. publish the GitHub Release last.

Missing manager/platform evidence, adapter mismatch, registry failure, digest divergence, public verification or docs leaves the release incomplete. Merge, `main` push and release are three separate gates.

## Release recovery and rollback

Preserve immutable subjects. Never overwrite PyPI files or rebuild an old OCI version. Publish a corrected patch when subject bytes change; yank only for an approved broken/incompatible/vulnerable/prohibited reason. Restore `latest` only to an already verified digest. Docker Hub recovery copies the recorded GHCR digest; it does not rebuild.

The closed committed-identity correction is a compatibility boundary. Dev integration evidence must prove exact V4 approval, `37/37` target verification, original-finding retention, unsupported-reader fail-closed behavior, and unchanged product/benchmark/commercial/program-health area inputs and release eligibility. Rollback to an older validator returns the findings to unresolved and blocks integration/release; it must not silently ignore the profile or materialize corrected historical bytes.

The TR-0027 input-origin correction is a separate compatibility boundary. Dev integration evidence must prove exact V5 approval, `1/1` source-absence/unique-container proof, unchanged manifests, original-finding retention, unsupported-reader fail-closed behavior, and zero authority/readiness/release effect. Rollback returns the finding to unresolved and cannot synthesize source-time authority.

The two-claim repair-evidence correction is a third compatibility boundary. Dev integration evidence must prove exact V7 approval, exact `2/2` claim and two-occurrence cause-ID recomputation, exact TR-0043 blob/digest provenance, original-finding and immutable-byte retention, unsupported-reader fail-closed behavior, and zero lifecycle/lease/authority/readiness/benchmark/candidate/delivery/release effect. Rollback returns both findings to unresolved and cannot make malformed historical values valid or authorize a T066 retry.

Native rollback uses only retained compatible runtimes and the packaged schema bounds. `recovery_required`, residue, incompatible state or identity mismatch is a stop condition. Codex failure does not authorize routing through Hermes or vice versa. Keep the GitHub Release absent/draft until all exact public surfaces and docs verify.
