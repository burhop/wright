# Contract: Rivet Compatibility Go/No-Go Decision

**Owner slice**: `055-rivet-compatibility-spike`

## Decision Preconditions

A decision record is valid only when:

1. Every compatibility question in the umbrella [research](../../054-rivet-workflow-integration/research.md) has a matrix row and evidence reference.
2. The selected baseline satisfies the upstream-baseline contract and has two clean reproduction results.
3. The fixture/evidence contract has all required capability rows, including explicit unsupported/unverified rows.
4. Offline and supply-chain results are complete.
5. The experiment is isolated and cleanup proof confirms no production/user data change.

## Outcomes

### Go

All mandatory criteria are evidenced. The decision identifies the exact baseline, patch status, admissible capabilities, prohibited capabilities, required controls, and owners for `rivet-workspace-persistence`, `rivet-headless-runner`, and `rivet-editor-host-adapters`.

### Conditional-Go

One or more non-mandatory gaps remain, but each has a safe disabled default, explicit later-slice owner, testable acceptance condition, and no ability to weaken workspace confinement, Wright-governed execution, offline operation, license compliance, or production packaging. A material sequence/scope change requires an umbrella-plan amendment and approval.

### No-Go

Any mandatory criterion fails or cannot be reproduced. The decision maps the failure to umbrella requirements, records alternatives considered, and stops production work. It may recommend a different baseline, upstream issue/contribution, a maintained fork proposal, or an alternative product direction, but none proceeds without human approval.

## Required Decision Record

- decision date, author, human approver, source branch/commit;
- selected/rejected baseline identities and evidence digests;
- criterion-by-criterion result;
- full compatibility matrix and risk register;
- source/package/license/security/asset/offline summaries;
- exact patch/fork/update policy;
- required later-slice contracts and feature-default controls;
- rollback/cleanup evidence;
- explicit next action and blocked work.

## Non-Authority Rule

This decision authorizes only the next Spec Kit planning slice. It does not authorize package promotion, release distribution, production feature enablement, direct tool access, user-data migration, or merge to `dev`/`main`.
