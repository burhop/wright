# Wright Engineering Capability Program Progress

**Last updated**: 2026-08-12
**Current loop**: 068 - Capability Library and MCP onboarding
**Program state**: Active; Gate E closed; no `main` merge or release authorized.

## Completed foundation

### Dynamic engineering MCP catalog integration

- Integrated the latest `origin/codex/engineering-mcp-dynamic-catalog`, including `80ed3fc` and both GB10 evidence records, with Feature 067's current `dev`.
- Preserved the 69-entry rich catalog, platform selectors, bundle policy, weekly validation workflow, setup recipes, follow-ups, and clean-container evidence.
- Added LF normalization for manifest-hashed Rivet source inputs after the installed-wheel gate exposed Windows line-ending drift.
- Replaced a stale gateway resource assertion that hard-coded the prior 42-entry catalog with an exact canonical-document comparison.
- Full `scripts/check-dev-merge.sh` result: passed. Evidence included 1,434 repository tests passed/52 skipped, 265 web tests passed, strict docs, production web build, 13 Hermes plugin tests, and 130 live Playwright tests passed/1 skipped.
- Feature commits: `2622c2a`, `9d1618a`; validated feature tip `9d1618a`.
- Merged and pushed `dev`: `c6dc90c` (`Merge dynamic engineering MCP catalog`). Local `dev` and `origin/dev` matched after push.
- Deferred external validation: NVIDIA Omniverse needs an NVIDIA/NGC API key; this did not block the catalog foundation.

## Loop 068

### Spec Kit phases

- [x] `speckit-git-feature`: branch `068-capability-library` created from clean `origin/dev` at `c6dc90c`.
- [x] `speckit-specify`: `spec.md` and specification quality checklist completed; all checklist items pass.
- [x] `speckit-clarify`: no critical ambiguity; the program's safest reversible defaults cover scope, roles, trust, lifecycle, error, and recovery behavior.
- [x] `speckit-plan`: research, plan, data model, API/schema/UI contracts, Gate A record, and quickstart drafted.
- [x] `speckit-checklist`: 40 UX, security, compatibility, recovery, and testability requirements-quality checks pass.
- [x] `speckit-tasks`: 119 dependency-ordered tasks with story checkpoints, test-first slices, traceability, hardening, and merge verification.
- [ ] `speckit-analyze` and remediation
- [ ] `speckit-implement`
- [ ] Focused, integration, UI, packaging, docs, and full dev gate
- [ ] Push feature, merge to `dev`, push `dev`, verify synchronization

### Gate A decision

- Selected a Wright-pinned Ed25519 public trust root, canonical signed envelopes, SHA-256 payload binding, monotonic sequence and expiry checks, administrator diff/activation, and transactional active/previous rollback.
- Catalog metadata remains separate from custom records, install/process state, credentials, explicit disablement, and workspace grants.
- Selected a digest-bound exact Install Plan before effects.
- Selected the UI sequence Discover -> Understand -> Add -> Review plan -> Validate -> Use in workspace. Invocation approval remains separate.
- Rollback: activate the prior verified snapshot; packaged catalog remains the immutable recovery root. Storage migration is additive.
- Detailed evidence, alternatives, risks, and rollback: `specs/068-capability-library/contracts/gate-a-decision.md`.

### Research and external validation status

- Official MCP Registry is an ingestion source for Wright's reviewed aggregate, not an online dependency for end-user discovery.
- Supported first import grammars: Claude `mcpServers`, VS Code `servers`/`inputs`, and plain single-server JSON.
- Onshape published the official Onshape Labs FeatureScript MCP on 2026-08-11 with endpoint `https://fs-mcp.labs.onshape.app/mcp`.
- Onshape remains external-live-validation deferred: Wright has not subscribed, accepted App Store terms, supplied credentials, contacted the endpoint, or claimed protocol/tool success.

### Next checkpoint

Run cross-artifact analysis, remediate all high/critical findings, and begin test-first implementation.

## Program guardrails

- No paid usage, license acceptance, external production mutation, user-data deletion, physical actuation, `dev` to `main` merge, or release publication.
- Normal tests use deterministic fixtures, not proprietary apps, paid credentials, GPUs, or hardware.
- `.local-run/`, downloaded repositories, model weights, caches, and build output remain untracked.
