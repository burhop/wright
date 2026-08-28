# Implementation Plan: Control-Plane Validator and Governed Readiness Snapshot

**Branch**: `077-control-plane-validator` | **Date**: 2026-08-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/076-control-plane-validator/spec.md`

## Summary

Build an offline, repository-local Python CLI that reads the Engineering Process Platform control plane from exact committed Git blobs, validates its JSON schemas and cross-artifact semantics, derives one bounded next action, and transactionally generates one canonical machine snapshot with four independent readiness areas. The design adds machine-readable lifecycle, gate, and gate-evidence contracts because those rules currently exist only in prose. It preserves revisions 1–9 through the original frozen bootstrap profile and revisions 10–19 through a second closed, enumerated, digest-bound bridge ending at this amended approval checkpoint; no later v1 record is compatible. EPP-F01 does not add a browser route or frontend page; the required read-only browser projection is dependency-ordered EPP-F01B. V8 execution is interrupted; V9 planning is limited to two exact immutable preflight findings and is blocked pending a replacement exact approval bundle.

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
| UI and testing | No product UI is added. Human terminal output and the JSON snapshot have explicit empty, stale, blocked, failure, evidence-inspection, and recovery behavior. Browser presentation and its constitution-mandated component/integration tests belong to EPP-F01B. | Pass |
| Observability and tracing | This offline governance command does not process user requests or product execution. Stable bounded findings replace raw logging; no remote telemetry is introduced. | Pass |
| Autonomous workflow | Planning is isolated on the feature branch, implementation is blocked pending exact human approval, and later integration remains separately gated. | Pass |

Post-design re-check: the proposed contracts remain local, typed, offline, compatible, testable, and approval-gated. No constitutional exception or complexity waiver is required.

## Design Decisions and Approval Boundary

The following material contract decisions are part of the exact implementation-approval subject. They are not silently assumed:

0. Keep this feature bounded to validator, machine snapshot, provenance and CLI behavior. The browser-accessible program-status page is EPP-F01B, depends on EPP-F01, blocks EPP-F02, and requires a separate Spec Kit subject and implementation approval.

1. Add separate program and child-feature lifecycle domains, an explicit `feature_state`, and event kinds for lifecycle transitions, failed attempts, and repair checkpoints.
2. Expand leases to distinguish the `dev` baseline from the actual worktree start subject and to record stable worktree identity, mode, allowed actions, and recovery/audit status.
3. Define a non-circular dashboard source/container/delivery relation: source commit `S`, a complete authoritative-input manifest excluding generated outputs, a dashboard-only successor commit `C`, and an explicitly supplied delivery-evidence commit `D`; record a separate release-candidate subject `R`. `validate --container <commit-ish>` resolves `C` explicitly; without it, only `HEAD` may be inferred, and only when its first parent is `S` and `S..HEAD` changes exactly the declared generated output set. `validate --delivery <commit-ish>` is the only way to resolve `D`, requires resolved `C`, and never searches or infers a descendant.
4. Add machine-readable gate catalog, gate-evidence, lifecycle-policy, validation-report, dashboard, and verification-evidence contracts. Markdown is explanatory, never parser authority.
5. Make approval freshness and revocation append-only. Historical approvals validate their historical subjects; material policy changes need a new `material_change` approval; `approved_with_conditions` blocks autonomous progression until conditions are machine-verifiable. The implementation entry gate is an approval bundle containing separate `material_change` and `feature_implementation` records bound to the same exact subject because the v1 approval schema encodes one scope per record.
6. Preserve transition revisions 1–9 through `epp-bootstrap-v1-r1-r9` and revisions 10–19/transitions `TR-0009`–`TR-0018` through `epp-bridge-v1-r10-r19`. The first profile names the bridge as its one closed-profile successor; both enumerate unique archive/transition paths, exact raw state digests, canonical state digests, and contiguous edges rather than authorizing an open range. Transitions through `TR-0017` embed exact raw SHA-256. To avoid a `TR-0018`↔profile hash cycle, terminal `TR-0018` alone uses `raw_sha256_rule=checkpoint_commit_blob` with null embedded hash; the later exact material-change approval subject binds the commit containing both blobs, and validation resolves/rehashes `TR-0018` there. The bridge fixture remains immutable with null `checkpoint_commit`, accepts no new v1 record, ends at `IMPLEMENTATION_APPROVAL_PENDING`, and permits exactly one v1-to-v2 migration. Do not rewrite history or patch the approved profile with its own commit.
7. Accept only explicitly declared compatible schema versions. Unknown majors and undeclared newer minors fail closed.
8. Identify the validator by the canonical digest of the closed, bounded, path-sorted tracked entrypoint-plus-`scripts/program_control/**/*.py` bundle, reject local imports outside it, and test add/delete/change—not by one entrypoint blob. Use one gate-row shape with an explicit per-gate `fresh` value in both validation report and dashboard.
9. Keep the bytes generated from `S` permanently labeled `candidate_not_evidence`. A `committed_valid` result exists only in the validation delivery envelope after passing evidence from an independent verifier in explicit descendant `D` proves exact dashboard bytes, the `S`/`C` first-parent and diff relation, and a delivery-only `C..D` change. Neither `C` nor `D` is embedded in the dashboard.
10. Add one closed correction profile, `COR-EPP-F01-US1-COMMITTED-IDENTITY-001`, for the stable committed-identity cause discovered at revision 27. It enumerates a literal 37-claim set: six v2 transition output-digest pointers and 31 wrong-tree pointers in immutable state revisions 1–26. Each target is bound to exact Git identities and is a strict ancestor of the correction-containing commit. The profile is append-only factual disposition, never a rewrite, waiver, wildcard, readiness input, approval, or generic override. It becomes effective only when exact V4 material-change and implementation approvals accept DEC-P0-016 and bind the frozen profile digest. Older validators fail closed. This amendment adds one task, bringing the plan to 69 tasks while preserving all historical task IDs.
11. Add a second, independent closed profile, `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001`, for one defect only: TR-0027 `/inputs/3` labels the planning approval as a source input although Git proves the approval first appears with TR-0027 in container `88481d57`. The validator may dispose that visible finding only after proving source absence, exact container introduction and exact blobs. No general “container input” rule is permitted. This V5 amendment changes pending T024/T026/T030/T031 but adds no task, keeps 69 total, preserves T069 and both correction records independently, and requires new same-subject approvals accepting DEC-P0-017 before implementation resumes.
12. Historical V7 added the third closed profile, `COR-EPP-F01-REPAIR-EVIDENCE-001`, for exactly two repair-evidence claims. T070–T071 are complete under exact V7 approval; T072 failed closed. V7 cannot authorize a retry or any new correction.
13. V8 is a closed T072 checkpoint correction, not a new feature or general waiver. Add exactly three historical claims: the two TR-0047 output-digest pointers and the TR-0050 event-domain tuple. Add direct-current work for only the final gate-catalog/evidence rebind and the two evidence-walkthrough causes. T073–T076 are test-first, implementation, direct-current repair, and non-interference/verification tasks. No lifecycle policy edge or event rule is broadened. The separately failing roadmap-policy inversion test is recorded as an excluded P0 question and prevents T066 after V8 until separately authorized.
14. V9 is a second closed preflight correction, not continuation of V8 implementation. It has exactly two claims: externally bind one exact immutable schema-less V8 discovery blob to one exact-value schema, and disposition only TR-0051's complete 35-path manifest whose self path was appended rather than canonically sorted. Planning replaces the stale V8 approval action with the V9 approval action; that is gate selection, not validator correction behavior. T077–T080 are the entire possible V9 lease and must preserve the frozen V9 policy bytes. The validator must recompute Git object identities and container changed paths, reject every other schema-less artifact or manifest deviation, retain both findings, and prove full projection non-interference. V9 cannot execute T073–T076, fix the roadmap-policy inversion, or reactivate the V8 lease.

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
│   ├── committed-identity-correction.schema.json
│   ├── transition-input-correction.schema.json
│   ├── repair-evidence-correction.schema.json
│   ├── dashboard-generation.md
│   ├── gate-catalog.schema.json
│   ├── gate-evidence.schema.json
│   ├── legacy-compatibility-profile.json
│   ├── legacy-compatibility-profile.schema.json
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
    ├── committed-identity-correction.schema.json
    ├── transition-input-correction.schema.json
    ├── repair-evidence-correction.schema.json
    ├── gate-catalog.schema.json
    ├── gate-evidence.schema.json
    ├── legacy-compatibility-profile.schema.json
    ├── lifecycle-policy.schema.json
    ├── program-state.schema.json
    ├── transition-evidence.schema.json
    ├── validation-report.schema.json
    └── verification-evidence.schema.json
```

**Structure Decision**: A thin executable delegates to an importable repo-local package. This follows existing script patterns, keeps governance code out of the public product distribution, and permits focused tests without subprocess-only coupling. The canonical schema designs in this feature directory are planning contracts; implementation copies the approved forms into the program schema directory.

## Execution Architecture

1. **Resolve subject**: find repository root; record HEAD, tree, worktree status, platform representation, and the requested committed source commit `S` without following untrusted paths. Resolve optional `C` from `--container`; otherwise infer only `HEAD` when its first parent is `S` and the diff is dashboard-only. Resolve `D` only from optional `--delivery`, require resolved `C`, and verify exact first-parent and delivery-only diff rules; never search for or infer `D`. An absent `C` or `D` remains candidate/non-evidence rather than guessed current delivery.
2. **Load exact inputs and bind the executing validator bundle**: enumerate an allowlisted authoritative set with `git ls-tree`/`git cat-file`; strict-decode UTF-8 JSON while rejecting duplicate keys. Define the complete validator source bundle as the tracked regular blob `scripts/validate-engineering-process-program.py` plus all tracked regular `*.py` blobs recursively below `scripts/program_control/` at `S`, normalized, path-unique, sorted, at most 100 files and 2 MiB total. Require every loaded local validator module to resolve inside those roots; require runtime `HEAD` to carry identical blob IDs for every bundle path and no dirty/untracked/ignored bundle path, permitting only declared Git text/EOL checkout representation. Reject symlinks, submodules, missing/extra bundle entries, out-of-bundle local imports, and any runtime/source mismatch before pass, generation, or recomputation; hash the canonical `S` manifest and never treat checkout bytes as committed evidence.
3. **Validate contracts**: map each artifact to an explicit compatible schema; validate Draft 2020-12 structure; reject unknown majors and undeclared minors.
4. **Validate semantics**: check normalized safe references, raw and canonical digests, lifecycle/event graphs, revision chain, complete transition manifests, roadmap DAG and eligibility, approvals, P0 due dates, WIP, pointer, and lease identity/scope. Existing exact V4/V5/V7 profiles retain their closed proofs. V8 requires literal `3/3` equality, Git-blob-byte recomputation, exact TR-0050-only tuple/evidence mapping, final catalog binding, and both walkthrough causes. Every profile retains original findings, has zero readiness/authority effect, and fails closed on any mismatch.
5. **Prove correction non-interference**: deep-compare correction-off/on output for the honest current `0/100` fixture and a non-empty synthetic benchmark fixture. Require equality of the full benchmark area and summary, counts/populations/deficits, coverage/qualification, oracle/artifact, holdout/contamination, attempts/tiers, cutoff/freshness, every readiness status/color, candidate, approval authority and release eligibility. The repair-evidence profile may affect only disposition of its two named findings; it may not make the current state, transition chain, lease, candidate, or delivery evidence authoritative.
6. **Derive readiness**: match every catalog assertion to exactly one same-ID evaluator result for one exact release candidate `R`. The catalog carries a closed evidence-class registry mapping each class to expected schema ID and source role; each evidence reference carries all three, resolves to the same path/digest/schema/role in the authoritative source manifest, and cannot satisfy a class by relabeling another artifact. A gate pass must cover every catalog-required class. A gate passes only when every required assertion is passing, supporting, fresh, evidence-backed, class-complete, evaluator-matched, and independently verified when policy requires; aggregate gate rows are derived and never authoritative inputs. Validate the existing benchmark coverage, qualification-transition, process/oracle/output, artifact-completeness, holdout-ledger, attempt-history, tier, contamination, and freshness invariants before deriving benchmark counters. Aggregate each area independently with precedence `failed > blocked > stale > in_progress > not_started`; calculate release eligibility only from four passed areas plus a current exact-subject human release approval. Validator success is independent of the resulting area/release statuses.
7. **Render one report model**: deterministic findings, shared gate rows including per-gate `fresh`, and next action feed both terminal text and versioned machine JSON. Human output cannot diverge from the model.
8. **Write a dashboard candidate locally**: serialize UTF-8/LF with `generation_status=candidate_not_evidence`, flush and `fsync`, reread and validate temporary bytes, then `os.replace`. A failure before replacement preserves prior bytes; no fallible validation occurs after the commit point.
9. **Verify and deliver without a provenance loop**: freeze implementation candidate `R`; have an independent verifier validate `R` and commit a schema-valid candidate report in source commit `S`; let the coordinator create successor `C` whose first parent is `S` and whose `S..C` diff contains only the dashboard; then have the verifier check `C` and persist a delivery-only record in descendant `D` whose first parent is `C` and whose diff is limited to the declared delivery evidence. The dashboard remains `candidate_not_evidence`; a later validation report may call delivery `committed_valid` only from the external `D` envelope. `D` is not an input to the snapshot at `S`; any new readiness input requires regeneration. No author code/source mutation occurs after candidate freeze.

## Error, Privacy, and Recovery Contract

- Findings contain stable code, severity, repository-relative artifact, exact JSON pointer when applicable, invariant, bounded evidence identity, consequence, smallest recovery action, resolution status, and correction reference. Original findings remain visible after disposition.
- Findings are sorted by severity, code, normalized artifact, and invariant; safe independent findings are collected in one run.
- Raw JSON values, schema exception values, shell commands/arguments, prompts, logs, credentials, tokens, cookies, private endpoints, artifact bodies, reusable authority, and unapproved absolute paths are never emitted.
- Validation never mutates inputs. Generation may change only its declared target and temporary sibling; failure removes the temporary file and leaves the previous snapshot byte-identical.
- Removing the validator restores the documented manual validation procedure and makes its incompatible snapshots stale; source evidence requires no rollback. A validator that cannot interpret the closed correction profile fails closed rather than treating historical identity failures as passing.

## Verification Strategy

- A frozen valid fixture and the current committed control plane must pass within 5 seconds and produce at most 1 MiB of machine output at current program scale.
- Parameterized raw-byte or semantic single-fault fixtures cover every fail-closed class in FR-003 through FR-009; a multi-fault fixture proves deterministic aggregation.
- Correction fixtures prove the exact six transition claims and exact 26 state rows/31 pointers, canonical state digests, strict ancestry, exact approval binding, `37/37` recomputation, rejection of every addition/omission/substitution/range/wildcard/self/future/correction target, preservation of original findings, and byte-identical readiness/release projections before and after disposition.
- Separate TR-0027 input-origin fixtures prove exact `1/1` source-absence/unique-container introduction and deep equality of the profile's complete benchmark/readiness/candidate/approval/release projection list for both honest `0/100` and non-empty synthetic benchmark inputs.
- Separate repair-evidence fixtures prove exact `2/2` claim identity, exact two-pointer cause-ID occurrence equality, exact TR-0043 digest provenance, preservation of every immutable source blob, rejection of every omitted/added/substituted/relocated/current/wildcard target, and full projection non-interference.
- Git fixtures prove LF blob identity survives clean CRLF checkout representation, dirty/mixed endings are separate observations, paths with spaces work, and no mutating Git command runs.
- A four-by-status dashboard matrix proves area independence; the 100-terminal-success trap proves other areas and release approval remain independent.
- Atomic failure injection covers candidate validation, write, flush/`fsync`, and replace failures with byte-for-byte prior snapshot preservation and no residue.
- Runtime-built privacy canaries are searched across JSON, terminal output, stdout, and stderr.
- Compatibility fixtures cover the seed snapshot, exactly two closed profiles in fixed order, their contiguous/unique revision and transition sets, exact raw state/transition blobs and canonical edges, rejection of all later v1 records, the sole approved v1-to-v2 successor, every explicitly supported schema version, unsupported major/minor, unknown source-bundle generator, and removed-validator rollback.
- Provenance fixtures cover explicit `--container`, constrained `HEAD` inference, explicit-only `--delivery`, every C/D resolution rejection, added/deleted/imported/changed generator modules with unchanged entrypoint, dirty/untracked/ignored helpers, runtime `HEAD` whose bundle differs from explicit `S`, loaded-module paths outside the local bundle, source-bundle count/byte bounds, per-gate freshness parity, independent passing delivery evidence, dashboard bytes that remain candidate-only, and valid/invalid descendant `D` delivery envelopes.
- Benchmark fixtures cover missing/extra/duplicate assertion results; empty-evidence or non-independent passing claims; coverage quota/intersection/equivalence-family defects; illegal qualification transitions; missing process/oracle/output references; artifact incompleteness; holdout chain/contamination; attempt ordinal/history; T0–T3 qualification; freshness; and contradictory summary populations/equations.
- Every author, story, rollback, candidate, and independent-verifier evidence file validates against the verification-evidence contract and preserves original failures/skips.
- Focused tests run on Windows and Linux/POSIX; semantic verdicts and committed digests must match.
- Wright fast-push routing, merge gates, and CI receive focused program-control coverage and tests that prevent gate-routing drift.

## Delivery and Gate Impact

Primary gates: `PROG-01`, `PROG-02`, `PROG-04`, `PROG-05`, `PROG-06`; supporting dashboard truth for `PROD-10`, `BENCH-08`, and `COMM-07`. Passing EPP-F01 does not pass any product, benchmark, commercial, or release gate by itself.

Implementation approval may authorize only the exact paths listed in the approved task plan. It does not authorize dependencies, product code, benchmark creation/execution, external systems, push, PR, merge, dev integration, publication, or release. Later implementation must stop after author verification and candidate freeze for independent verification, then again for integration approval.

## Complexity Tracking

No constitution violations require justification. The new machine contracts are necessary because lifecycle edges, gate membership/status, freshness, and non-circular dashboard provenance cannot be validated safely from prose or self-referential output.
