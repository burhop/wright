# Quickstart: Delivering a Rivet Integration Slice

This guide is for maintainers executing the umbrella plan. It intentionally stops before implementation until the requested human approvals are recorded.

## 1. Review the Umbrella Gate

Read, in order:

1. [spec.md](./spec.md)
2. [plan.md](./plan.md)
3. [research.md](./research.md)
4. [data-model.md](./data-model.md)
5. [slice-delivery-contract.md](./contracts/slice-delivery-contract.md)

Confirm the desired slice's prerequisites are merged into `054-rivet-workflow-integration`. Do not start downstream work from an older sibling branch.

## 2. Start the Slice With Spec Kit

Switch to and update the umbrella branch, then invoke the repository's Spec Kit feature workflow using the stable short name from the roadmap. For example, the first slice uses `rivet-compatibility-spike`.

Spec Kit must choose the next available numeric prefix at that time, producing a branch such as `<next>-rivet-compatibility-spike` and a matching `specs/<next>-rivet-compatibility-spike/` directory. Do not manually reserve all Rivet slice numbers in advance.

Record in the new specification:

- base umbrella commit;
- prerequisite slice versions/contracts;
- exact in-scope user journey;
- exclusions and safe behavior when later slices are absent;
- feature flag/default state;
- migration, packaging, and rollback impact;
- targeted test and evidence requirements.

## 3. Complete Slice Planning

Run the normal Spec Kit lifecycle on the slice branch:

1. Specify and validate requirements.
2. Clarify material ambiguity.
3. Generate requirements plus relevant security/runtime/UX/integration checklists.
4. Generate research, plan, data model where applicable, contracts, and quickstart.
5. Re-check the Wright constitution and the umbrella contracts.
6. Stop for human plan approval.
7. Only after approval, generate tasks and run cross-artifact analysis.
8. Implement and verify the approved tasks.

The slice must not edit another slice's specification to hide an unmet dependency. Contract changes are proposed explicitly and coordinated through the umbrella branch.

## 4. Validate and Merge a Slice

Before a slice pull request targets the umbrella branch:

- bring the latest umbrella changes into the slice;
- run all slice-owned format, lint, type, unit, contract, integration, UI, security, packaging, and lifecycle checks identified in its plan;
- test Wright with the slice disabled and with optional Rivet/Node dependencies absent;
- record platform limitations rather than silently dropping a claim;
- verify rollback/disable behavior and preservation of authored workflow files;
- update implementation evidence and requirement traceability.

After review, merge the slice into `054-rivet-workflow-integration` and update the umbrella roadmap/evidence. Later slices branch from that updated integration state.

## 5. Reach the First User-Operable MVP

The MVP requires these stable short names in dependency order:

1. `rivet-compatibility-spike`
2. `rivet-workspace-persistence`
3. `rivet-headless-runner` and `rivet-editor-host-adapters` (may proceed in parallel after persistence)
4. `rivet-workspace-tab`
5. `rivet-wright-nodes`
6. `rivet-workflow-operations`
7. `rivet-release-hardening`

`rivet-agent-publication` is optional P2 work and is not an MVP prerequisite.

## 6. Integrate to `dev`

When all selected slices and hardening evidence are merged, update the umbrella coordination documents, run the authoritative `scripts/check-dev-merge.sh`, and address failures before requesting the umbrella merge to `dev`. If a local host cannot execute a specific gate, document that exact limitation and obtain the required external evidence; do not treat the limitation as a pass.

Production is still incomplete after a merge to `dev` or `main`. Any later release follows `docs/release/release-runbook.md` through registry, digest, native lifecycle, documentation, and GitHub Release verification.
