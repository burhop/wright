# Contract: Rivet Integration Slice Delivery

**Owner**: `054-rivet-workflow-integration` umbrella branch

**Applies to**: Every Rivet implementation slice

## Branch Contract

1. A slice starts only after its prerequisites are merged and its parent plan is approved.
2. The maintainer switches to the latest `054-rivet-workflow-integration` and invokes the repository Spec Kit feature workflow with the stable short name from the umbrella roadmap.
3. Spec Kit assigns the next available numeric prefix at start time. Numbers are never pre-reserved.
4. The resulting branch is `<number>-<stable-short-name>` and its feature directory is `specs/<number>-<stable-short-name>/`.
5. Slice pull requests target `054-rivet-workflow-integration`. Direct slice merges to `dev` or `main` are prohibited.
6. Implementation code is committed only on a slice branch. The umbrella branch contains coordination-document changes and merge results from approved slices.

## Required Slice Documents

Every slice owns:

- `spec.md` with independent user journey, acceptance scenarios, edge cases, requirements, entities, and measurable success criteria;
- `checklists/requirements.md` and security/runtime/UX/integration checklists relevant to its risk;
- `research.md` resolving every technical unknown necessary for implementation;
- `plan.md` with technical context, constitution gate, actual source ownership, verification, migration, packaging, and rollback;
- `data-model.md` when the slice creates or changes durable/stateful entities, otherwise an explicit N/A rationale in the plan;
- `contracts/` for every API, event, bridge, file, process, or UI boundary it changes, otherwise an explicit N/A rationale;
- `quickstart.md` proving the independent journey and disabled/absence behavior;
- `tasks.md` generated only after human plan approval;
- Spec Kit analysis results with material findings resolved;
- implementation evidence linking requirements and success criteria to automated/manual results and environment details.

No placeholder document satisfies this contract. Documents marked not applicable must explain why the slice has no corresponding model or boundary.

## Mandatory Specification Fields

In addition to the Spec Kit template, every slice records:

- exact umbrella base commit and prerequisite slice/contracts;
- explicit in-scope and excluded behavior;
- safe behavior when all later slices are absent;
- feature flag name/default and disabled experience;
- migration/data preservation impact;
- optional dependency and offline/package impact;
- security/trust-boundary change;
- rollback/disable procedure;
- targeted test suites, supported-platform claims, and evidence format;
- human plan approval before task generation/implementation.

## Review Gates

### Gate A - Specification quality

- No unresolved clarification or implementation leakage into requirements.
- Independent acceptance test exists.
- Requirements are measurable and traceable.
- Exclusions prevent accidental big-bang scope.

### Gate B - Design approval

- Research resolves implementation-blocking unknowns.
- Contracts and models agree with the spec and upstream umbrella boundaries.
- Constitution passes or an explicit justified exception is approved.
- Migration, rollback, optional-dependency absence, packaging, observability, and security are designed.
- Human approval is recorded before `tasks.md` or implementation.

### Gate C - Task readiness

- Tasks are dependency ordered, independently verifiable, and mapped to requirements/contracts.
- Spec Kit analysis has no unresolved critical/high finding.
- A material design change returns to Gate B.

### Gate D - Merge readiness

- All slice tasks and acceptance scenarios are complete.
- Targeted format/lint/type/unit/contract/integration/security/UI/lifecycle/package checks pass.
- Disabled feature and missing optional dependencies leave Wright healthy.
- Rollback/disable behavior is demonstrated and authored files are preserved.
- Evidence records versions, commit, environment, commands, results, artifacts, and limitations.
- Diff is confined to approved scope and does not rely on unmerged later slices.

## Compatibility and Contract Changes

- A slice consumes earlier contracts through public boundaries and cannot reach into implementation internals to save time.
- Breaking an earlier slice contract requires a new or amended approved spec, migration/compatibility plan, updates to all consumers, and umbrella coordination.
- Experimental spike code cannot silently become production. Productionization occurs in the owning slice with typed contracts, tests, packaging, and rollback.
- Feature flags are not substitutes for authorization or migrations; they provide deploy/rollback control only.

## Merge Evidence Record

Each merged slice adds an umbrella status entry containing:

- numbered branch/spec link and merge commit;
- approved plan/review identity;
- contract/schema versions introduced;
- automated and manual evidence summary;
- supported and unverified environments;
- feature default and enablement instructions;
- migration executed and rollback result;
- known risks/deferred work;
- next slices unblocked.

## Final Umbrella Gate

After all MVP slices and hardening are merged, the umbrella branch must:

- map every umbrella requirement/success criterion to slice evidence;
- prove the integrated reference journey and cross-workspace isolation;
- pass optional-feature absence and offline installed-package tests;
- pass native/Docker claims with recorded evidence;
- run `scripts/check-dev-merge.sh` before any requested merge to `dev`, or document the exact host limitation according to repository policy;
- retain the optional agent-publication slice as explicitly included or deferred, never ambiguous.
