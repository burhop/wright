# Implementation Plan: Control-Plane Validator and Live Readiness Dashboard

**Branch**: `077-control-plane-validator` | **Date**: 2026-08-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/076-control-plane-validator/spec.md`

## Summary

Build an offline, repository-local Python CLI that reads the Engineering Process Platform control plane from exact committed Git blobs, validates its JSON schemas and cross-artifact semantics, derives one bounded next action, and transactionally generates one canonical dashboard with four independent readiness areas. The design adds machine-readable lifecycle, gate, and gate-evidence contracts because those rules currently exist only in prose; it preserves revisions 1–9 through a frozen bootstrap-compatibility profile instead of rewriting append-only history. Implementation is not authorized by this plan.

## Technical Context

**Language/Version**: Python 3.11 through 3.14, matching the repository support range

**Primary Dependencies**: Python standard library plus the repository's existing `jsonschema>=4.26,<5`; no new or upgraded dependency

**Storage**: Committed Git objects and versioned JSON artifacts; one atomically replaced local `dashboard.json`

**Testing**: pytest with isolated temporary Git repositories, deterministic clocks, single-fault and multi-fault fixtures, and existing Wright Git gates

**Target Platform**: Supported Windows and POSIX developer/CI checkouts with Git available; fully offline

**Project Type**: Repository-governance CLI and machine contracts, excluded from the shipped `wright-engineering` package

**Performance Goals**: Validate and project the current control plane in under 5 seconds on a normal local checkout; deterministic machine output under 1 MiB for the current program; fresh-agent diagnosis under 5 minutes

**Constraints**: Read-only source inspection; committed Git-object bytes are identity authority; no product or benchmark execution; no network or external writes; bounded allowlisted diagnostics; one durable generated artifact; fail closed on unsupported contracts

**Scale/Scope**: Current program plus append-only growth through 100 benchmark cases, 34 readiness gates, bounded feature history, decisions, risks, approvals, and leases

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1 design.*

| Principle | Applicability and evidence | Result |
|---|---|---|
| Architectural foundation | This is repository governance tooling, not a backend API; FastAPI and product package boundaries are not applicable. The importable implementation stays under `scripts/program_control/`, outside `src/wright_engineering`. It is offline-first. | Pass |
| Serving and execution | No runtime, manager adapter, container, MCP server, or distribution behavior changes. | Pass |
| Data storage and RAG | No product data store is introduced. Inputs are committed Git blobs; output is one versioned JSON projection. | Pass |
| Security and identity | No authentication surface is introduced. Output is metadata-allowlisted and tested against secret, payload, endpoint, log, prompt, authority, and absolute-path canaries. | Pass |
| Engineering tooling protocol | The CLI is code-driven and non-interactive; it never requires a GUI or launches an engineering tool. | Pass |
| UI and testing | No product UI is added. Human terminal output and the JSON dashboard have explicit empty, stale, blocked, failure, evidence-inspection, and recovery behavior. | Pass |
| Observability and tracing | This offline governance command does not process user requests or product execution. Stable bounded findings replace raw logging; no remote telemetry is introduced. | Pass |
| Autonomous workflow | Planning is isolated on the feature branch, implementation is blocked pending exact human approval, and later integration remains separately gated. | Pass |

Post-design re-check: the proposed contracts remain local, typed, offline, compatible, testable, and approval-gated. No constitutional exception or complexity waiver is required.

## Design Decisions and Approval Boundary

The following material contract decisions are part of the exact implementation-approval subject. They are not silently assumed:

1. Add separate program and child-feature lifecycle domains, an explicit `feature_state`, and event kinds for lifecycle transitions, failed attempts, and repair checkpoints.
2. Expand leases to distinguish the `dev` baseline from the actual worktree start subject and to record stable worktree identity, mode, allowed actions, and recovery/audit status.
3. Define a non-circular dashboard source/container relation: source commit `S`, a complete authoritative-input manifest excluding generated outputs, and a dashboard-only successor commit `C`; record a separate release-candidate subject `R`.
4. Add machine-readable gate catalog, gate-evidence, lifecycle-policy, validation-report, dashboard, and verification-evidence contracts. Markdown is explanatory, never parser authority.
5. Make approval freshness and revocation append-only. Historical approvals validate their historical subjects; material policy changes need a new `material_change` approval; `approved_with_conditions` blocks autonomous progression until conditions are machine-verifiable. The implementation entry gate is an approval bundle containing separate `material_change` and `feature_implementation` records bound to the same exact subject because the v1 approval schema encodes one scope per record.
6. Preserve transition revisions 1–9 through a closed bootstrap profile anchored to the approved control-plane subject and integrity checkpoint. Do not rewrite history.
7. Accept only explicitly declared compatible schema versions. Unknown majors and undeclared newer minors fail closed.

Research rationale and rejected alternatives are in [research.md](research.md). Exact entities and migrations are in [data-model.md](data-model.md).

## Project Structure

### Documentation (this feature)

```text
specs/076-control-plane-validator/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── dashboard-generation.md
│   ├── gate-catalog.schema.json
│   ├── gate-evidence.schema.json
│   ├── lifecycle-policy.schema.json
│   ├── validation-report.schema.json
│   ├── dashboard.schema.json
│   └── verification-evidence.schema.json
├── checklists/
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── validate-engineering-process-program.py
└── program_control/
    ├── __init__.py
    ├── cli.py
    ├── dashboard.py
    ├── git_subject.py
    ├── json_contracts.py
    └── validation.py

tests/program_control_plane/
├── conftest.py
├── fixture_builder.py
├── test_atomicity_redaction_and_compatibility.py
├── test_cli.py
├── test_contract_schemas.py
├── test_dashboard_provenance.py
├── test_dashboard_projection.py
├── test_determinism.py
├── test_evidence_walkthrough.py
├── test_git_subject.py
├── test_json_contracts.py
├── test_roadmap_approval_and_lease.py
└── test_transition_chain.py

docs/programs/engineering-process-platform/
├── gate-catalog.json
├── gate-evidence.json
├── lifecycle-policy.json
├── dashboard.json
├── status-dashboard-contract.md
└── schemas/
    ├── dashboard.schema.json
    ├── gate-catalog.schema.json
    ├── gate-evidence.schema.json
    ├── lifecycle-policy.schema.json
    ├── program-state.schema.json
    ├── transition-evidence.schema.json
    ├── validation-report.schema.json
    └── verification-evidence.schema.json
```

**Structure Decision**: A thin executable delegates to an importable repo-local package. This follows existing script patterns, keeps governance code out of the public product distribution, and permits focused tests without subprocess-only coupling. The canonical schema designs in this feature directory are planning contracts; implementation copies the approved forms into the program schema directory.

## Execution Architecture

1. **Resolve subject**: find repository root; record HEAD, tree, worktree status, platform representation, and the requested committed source commit `S` without following untrusted paths.
2. **Load exact inputs**: enumerate an allowlisted authoritative set with `git ls-tree`/`git cat-file`; strict-decode UTF-8 JSON while rejecting duplicate keys; never treat checkout bytes as committed evidence.
3. **Validate contracts**: map each artifact to an explicit compatible schema; validate Draft 2020-12 structure; reject unknown majors and undeclared minors.
4. **Validate semantics**: check normalized safe references, raw and canonical digests, lifecycle/event graphs, revision chain, complete transition manifests, roadmap DAG and eligibility, approvals, P0 due dates, WIP, pointer, and lease identity/scope.
5. **Derive readiness**: evaluate every required gate exactly once from gate evidence for one exact release candidate `R`; aggregate each area independently with precedence `failed > blocked > stale > in_progress > not_started`; calculate release eligibility only from four passed areas plus a current exact-subject human release approval.
6. **Render one report model**: deterministic findings and next action feed both terminal text and versioned machine JSON. Human output cannot diverge from the model.
7. **Commit dashboard locally**: serialize UTF-8/LF, flush and `fsync`, reread and validate temporary bytes, then `os.replace`. A failure before replacement preserves prior bytes; no fallible validation occurs after the commit point.
8. **Verify and deliver without a provenance loop**: freeze implementation candidate `R`; have an independent verifier validate `R` and commit a schema-valid candidate report in source commit `S`; let the coordinator create successor `C` whose `S..C` diff contains only the dashboard; then have the verifier check `C` and persist a delivery-only record in descendant `D`. `D` is container evidence, not an input to the snapshot at `S`; any new readiness input requires regeneration. No author code/source mutation occurs after candidate freeze. Uncommitted candidates remain non-evidence.

## Error, Privacy, and Recovery Contract

- Findings contain stable code, severity, repository-relative artifact, invariant, bounded evidence identity, consequence, and smallest recovery action.
- Findings are sorted by severity, code, normalized artifact, and invariant; safe independent findings are collected in one run.
- Raw JSON values, schema exception values, shell commands/arguments, prompts, logs, credentials, tokens, cookies, private endpoints, artifact bodies, reusable authority, and unapproved absolute paths are never emitted.
- Validation never mutates inputs. Generation may change only its declared target and temporary sibling; failure removes the temporary file and leaves the previous snapshot byte-identical.
- Removing the validator restores the documented manual validation procedure and makes its incompatible snapshots stale; source evidence requires no rollback.

## Verification Strategy

- A frozen valid fixture and the current committed control plane must pass within 5 seconds and produce at most 1 MiB of machine output at current program scale.
- Parameterized raw-byte or semantic single-fault fixtures cover every fail-closed class in FR-003 through FR-009; a multi-fault fixture proves deterministic aggregation.
- Git fixtures prove LF blob identity survives clean CRLF checkout representation, dirty/mixed endings are separate observations, paths with spaces work, and no mutating Git command runs.
- A four-by-status dashboard matrix proves area independence; the 100-terminal-success trap proves other areas and release approval remain independent.
- Atomic failure injection covers candidate validation, write, flush/`fsync`, and replace failures with byte-for-byte prior snapshot preservation and no residue.
- Runtime-built privacy canaries are searched across JSON, terminal output, stdout, and stderr.
- Compatibility fixtures cover the seed snapshot, the bootstrap history profile, every explicitly supported schema version, unsupported major/minor, unknown generator, and removed-validator rollback.
- Every author, story, rollback, candidate, and independent-verifier evidence file validates against the verification-evidence contract and preserves original failures/skips.
- Focused tests run on Windows and Linux/POSIX; semantic verdicts and committed digests must match.
- Wright fast-push routing, merge gates, and CI receive focused program-control coverage and tests that prevent gate-routing drift.

## Delivery and Gate Impact

Primary gates: `PROG-01`, `PROG-02`, `PROG-04`, `PROG-05`, `PROG-06`; supporting dashboard truth for `PROD-10`, `BENCH-08`, and `COMM-07`. Passing EPP-F01 does not pass any product, benchmark, commercial, or release gate by itself.

Implementation approval may authorize only the exact paths listed in the approved task plan. It does not authorize dependencies, product code, benchmark creation/execution, external systems, push, PR, merge, dev integration, publication, or release. Later implementation must stop after author verification and candidate freeze for independent verification, then again for integration approval.

## Complexity Tracking

No constitution violations require justification. The new machine contracts are necessary because lifecycle edges, gate membership/status, freshness, and non-circular dashboard provenance cannot be validated safely from prose or self-referential output.
