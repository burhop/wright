# EPP-F01 Research Decisions

## Scope and Method

The primary writer inspected the approved program contracts, the complete legacy chain through revision 18 / `TR-0017`, the proposed revision-19 amended checkpoint, existing repository tooling, package configuration, tests, and Git-gate scripts. Three bounded read-only agents initially audited repository architecture, contract semantics, and verification strategy; the amended subject receives a new four-lens audit before freeze. All auditors are read-only. Findings below resolve contradictions and expose every material choice that must be included in exact implementation approval.

## R-001 — Repository-local Python CLI

**Decision**: Use a thin `scripts/validate-engineering-process-program.py` entrypoint and importable modules under `scripts/program_control/`. Put tests under `tests/program_control_plane/`.

**Rationale**: This is repository governance, not shipped Wright product runtime. Root packaging excludes scripts/docs/tests from the distribution. Importable modules make deterministic unit testing possible while retaining one documented non-interactive command.

**Alternatives rejected**:

- `src/wright_engineering`: would couple governance tooling to the public product package and release artifact.
- One monolithic script: harder to isolate Git identity, schema, semantic, projection, and atomic-write tests.
- Separate PowerShell and Bash implementations: creates cross-platform semantic drift.

## R-002 — Existing dependency only

**Decision**: Reuse the repository's existing `jsonschema>=4.26,<5` extra and Python standard library. Add or upgrade no dependency. Invoke Git through argument arrays with `shell=False`.

**Rationale**: Current schemas require Draft 2020-12 features including references, composition, conditionals, formats, contains, and uniqueness. A partial standard-library implementation could false-pass. Graph validation is small enough for deterministic DFS/Kahn logic; GitPython and networkx are unnecessary.

**Verification definition**: “Dependency-free verification” means no new package, network, service, container, product runtime, model, benchmark, or proprietary application. Git and the existing locked development environment remain prerequisites.

## R-003 — Committed Git blobs are identity authority

**Decision**: Read committed inputs with Git plumbing and hash the returned blob bytes. Report checkout cleanliness and representation separately.

**Evidence**: At `c46ea627a7403ff3e1ce3db6be3d1baeebebb377`, `core.autocrlf=true`; committed `program-state.json` is 3,224 bytes with SHA-256 `dab12e6d70fbe29a85a6120fd3a7ca2a7d3e7e283db5757672815a253997c9aa`, while the clean checkout representation is 3,295 bytes with a different digest. Git still reports it clean.

**Alternative rejected**: `Path.read_bytes()` as committed identity misclassifies clean Windows line-ending conversion as corruption.

## R-004 — Separate lifecycle domains and event kinds

**Decision requiring material-change approval**: Add `feature_state` to `program-state.json`; add `state_domain` and `event_kind` to transition evidence; publish separate legal graphs for program lifecycle, child-feature lifecycle, failed attempts, and repair checkpoints in `lifecycle-policy.json`.

**Rationale**: Current state records `PROGRAM_ACTIVE`, while TR-0006 through TR-0008 use feature states. An implementation cannot validate their edges from the authoritative snapshot without an undocumented inference. A failed attempt or repair self-loop is evidence, not an ordinary lifecycle advance.

**Compatibility**: Revisions 1–9 remain immutable and are accepted only through `epp-bootstrap-v1-r1-r9`. The later governed planning history is accepted only through the independently closed `epp-bridge-v1-r10-r19`, which enumerates revisions 10–19 and transitions `TR-0009`–`TR-0018`, ends at the amended approval checkpoint, rejects every later v1 record, and permits one approved migration to v2. Future records after that migration must use the new domain/event fields and complete changed-path manifests.

**Alternative rejected**: Inferring child state solely from transition history embeds bootstrap exceptions in code and leaves current state unable to prove its own feature stage.

## R-005 — Complete lease identity

**Decision requiring material-change approval**: Replace ambiguous `base_commit` semantics with both `dev_baseline_commit/tree` and `worktree_start_commit/tree`; add stable non-private `worktree_id`, `lease_mode`, `allowed_actions`, and recovery/audit fields. Branch and Spec Kit directory numbers remain independent identifiers.

**Rationale**: The approved operating contract requires these fields. The current lease names the dev baseline while the worktree actually began from an approved overlay commit, and paths alone cannot prove planning-versus-implementation authority.

## R-006 — Non-circular dashboard provenance

**Decision requiring material-change approval**:

1. Commit authoritative source inputs as commit `S`.
2. Enumerate a sorted, complete authoritative-input manifest at `S`, excluding `dashboard.json` and declared delivery sidecars; record each Git-blob digest and the canonical manifest digest.
3. Enumerate the closed generator bundle—the tracked regular entrypoint plus every tracked regular `*.py` blob recursively under `scripts/program_control/`—in a normalized, unique, path-sorted manifest capped at 100 files and 2 MiB; reject local imports outside that bundle, and record its canonical digest and entries together with `S`, repository tree, program tree, and input-manifest digest.
4. The validation command accepts optional `--container <commit-ish>`. When omitted, infer only `HEAD`, only if its first parent is `S` and `S..HEAD` changes exactly the declared generated outputs. It separately accepts optional `--delivery <commit-ish>` as the only resolution for `D`; `--delivery` requires resolved `C`, and no descendant search or inference is allowed. Otherwise the missing subject is unresolved and no committed-current claim is possible.
5. Record a separate exact release candidate `R`; all gate evidence and human release approval must bind the same `R`.
6. Generated dashboard bytes always say `candidate_not_evidence`, whether uncommitted or contained in `C`. Only the external validation delivery envelope may say `committed_valid` after passing evidence from an independent verifier in explicit descendant `D` binds exact dashboard bytes and proves the `S`/`C` and `C`/`D` allowlisted relations.

**Rationale**: A dashboard cannot contain the identity of a program tree that contains its own final bytes. Source/container separation removes the fixed-point problem and permits exact validation.

**Alternatives rejected**:

- Excluding only the dashboard while claiming the containing commit: still leaves the source/container relationship unstated.
- Embedding `C`: self-referential and impossible without a digest fixed point.
- Trusting the current dashboard's hand-entered source fields: dashboard is a projection, not evidence.

## R-007 — Machine gate catalog and evidence

**Decision requiring material-change approval**: Add a closed `gate-catalog.json` defining every gate and its area, requiredness, evaluator, evidence policy, and freshness policy. Add `gate-evidence.json` containing assertion rows bound to one exact release candidate and evidence subjects. Markdown must agree with the catalog but is never parsed as authority.

**Aggregation**:

- A required gate passes only when its evidence row is current and passed.
- Every required catalog gate appears exactly once in a committed-valid dashboard.
- Area status is `passed` only when all required gates pass; otherwise precedence is `failed > blocked > stale > in_progress > not_started`.
- `skipped`, `partial`, `unsupported`, `unavailable`, `contaminated`, `inconclusive`, and `not_tested` never pass.
- `passed_gates` counts passed required rows; `required_gates` equals catalog membership, not a hand-set number.
- The benchmark area derives counts and deficits from governed benchmark metadata only; 100 terminal successes cannot affect any other area.

**Alternative rejected**: Parsing `gates.md` is formatting-sensitive and cannot supply typed freshness, exact candidate identity, or assertion evidence.

## R-008 — Approval freshness and revocation

**Decision requiring material-change approval**:

- Validate every historical approval's exact commit/tree/program-tree/manifest against Git objects.
- Require the current source to descend from the commit containing the approval record.
- Classify program artifacts as immutable policy, mutable operational state, append-only evidence, or generated projection.
- Any immutable-policy change requires a new append-only `material_change` approval bound to the change subject.
- Record revocation/supersession as append-only events, never by editing the original approval.
- Treat `approved_with_conditions` as blocking autonomous progress until each condition has a machine-verifiable record.
- Encode the EPP-F01 entry authority as two approved records—`material_change` and `feature_implementation`—bound to the same exact artifact subject and cross-referenced as one approval bundle; do not overload the v1 singular `scope` field.

**Rationale**: Comparing today's entire program tree to the original approved tree makes intended operational progress stale; merely proving the historical subject exists misses later policy changes.

## R-009 — Schema compatibility

**Decision**: Maintain an explicit compatibility table. `1.0` is supported where declared. Unknown major versions produce `SCHEMA_MAJOR_UNSUPPORTED`; an undeclared newer minor produces `SCHEMA_MINOR_UNSUPPORTED`. Prior snapshots are accepted only when named by one of the two closed compatibility profiles and covered by exact fixtures. The second profile is not an open range: it lists revisions 10–19, transitions `TR-0009`–`TR-0018`, every canonical prior/new state digest, the terminal approval-pending state, and a single allowed v2 successor.

**Alternative rejected**: Accepting any `1.x` because the major matches is unsafe while schemas use exact constants and no ignored-field semantics exist.

## R-010 — Deterministic report and privacy

**Decision**: One in-memory validation report is the source for both terminal and JSON rendering. Findings use stable codes and deterministic sorting. Outputs are constructed from allowlisted metadata; raw source values and raw exception text are forbidden.

**Boundaries**: Repository-relative paths only; normalize against the program root, permit repository escape only for declared in-repository feature artifacts, reject absolute paths, repository escape, and unsafe symlink traversal.

## R-011 — Transactional dashboard write

**Decision**: Persist only canonical JSON. Write UTF-8/LF bytes to a same-directory temporary file, flush, file-`fsync`, reread and schema/semantic validate the candidate, then `os.replace`. Perform no fallible validation after replace. Remove temporary residue on every pre-commit failure.

**Failure contract**: Preserve the prior snapshot byte-for-byte and return a bounded delivery envelope declaring failure/staleness. Do not rewrite the prior dashboard merely to mark it stale.

**Alternative rejected**: Coordinating JSON and Markdown as two durable outputs cannot provide cross-file atomicity. Terminal text is rendered from the same report instead.

## R-012 — Roadmap, WIP, and next-action semantics

**Decision**:

- Only `complete` satisfies a dependency; `integrated` remains insufficient until dev deployment verification.
- A blocking decision clears only when `status=decided`, its record exists, and bound evidence validates.
- Eligibility requires complete dependencies, no due blocking decision/risk, no stop condition, and current authority.
- Choose the lowest numeric priority; an equal-priority tie fails closed.
- Exactly one active roadmap item, current feature pointer, mutating lease, branch, worktree identity, and feature state must agree.
- No valid next action is emitted on any authority or semantic failure.

## R-013 — Verification and Wright gate integration

**Decision**: Use compact temporary Git repositories from a fixture factory and one mutation per parameterized negative case. Duplicate keys are injected at raw-byte level. A fixed clock and shuffled discovery/insertion order prove determinism.

Add focused routing for program docs, implementation modules, and tests to `check-dev-push.sh`; include modules in Ruff/format/MyPy paths and focused tests early in dev-merge/CI. Extend gate-process tests so routing cannot drift. Existing PowerShell wrappers delegate to Bash and need no duplicate validator logic.

Every persisted foundation, story, rollback, diff-audit, candidate, independent-candidate, and dashboard-delivery result uses the versioned verification-evidence contract. The verifier validates frozen candidate `R` and commits candidate evidence in source `S`; the coordinator creates dashboard-only successor `C`; the verifier then checks `C` and persists a passing delivery-only record in descendant `D`. A later validation receives exact `D` explicitly; it never searches for or infers a descendant. `D` does not retroactively become an input to the snapshot at `S`; any new readiness evidence does. This sequencing preserves independent-verifier identity without an endless verify/regenerate cycle.

## R-014 — Closed post-bootstrap v1 bridge (DEC-P0-013)

**Human-approved planning decision**: Retain the bytes and exceptions of `epp-bootstrap-v1-r1-r9` unchanged and add `epp-bridge-v1-r10-r19`. The first profile names the second as its one closed-profile successor beginning at `TR-0009`; this is not open-ended v1 acceptance. The bridge separately enumerates each included state revision and transition through the amended approval checkpoint `TR-0018`, including unique paths, exact raw state/transition SHA-256 values through `TR-0017`, exact canonical state edges, and a sole terminal `checkpoint_commit_blob` rule for `TR-0018`. The terminal raw hash is deliberately null to avoid a profile/transition fixed point; the later approval subject binds the commit from which the validator resolves and hashes both. It accepts no record after revision 19, ends at feature state `IMPLEMENTATION_APPROVAL_PENDING`, and allows exactly one successor: the approved v1-to-v2 migration.

**Checkpoint binding**: The bridge cannot embed the commit that will contain itself. Its `checkpoint_commit` therefore remains null permanently under the closed rule `exact_material_change_approval_subject`; the validator resolves the effective checkpoint commit from the forthcoming digest-bound approval record at validation time and requires that subject to contain the exact profile, state archives, and transition blobs. The approved profile is never patched to insert its own commit. A missing, different, non-ancestor, or byte-mismatched approval subject fails closed.

**Alternatives rejected**: widening r1–r9, accepting arbitrary v1 records, rewriting history, treating later v1 records as v2, or allowing more than one migration successor.

## R-015 — Container, gate-row, generator, and delivery provenance (DEC-P0-014)

**Human-approved planning decision**:

- accept optional explicit `--container`; otherwise infer only `HEAD` under the exact first-parent and dashboard-only diff rule; accept `D` only through explicit `--delivery` with resolved `C` and exact delivery-only first-parent proof;
- use one gate-row contract in report and dashboard, including required boolean `fresh`;
- bind validator identity to a canonical SHA-256 of the closed tracked entrypoint-plus-package source manifest, with normalized unique paths, 100-file/2-MiB bounds, no out-of-bundle local imports, and inspectable entries;
- keep dashboard bytes `candidate_not_evidence`; represent `committed_valid` only in the validation delivery envelope when passing evidence from an independent verifier in explicit descendant `D` binds `S`, `C`, dashboard bytes, and both allowed diffs.

**Alternatives rejected**: silently selecting an arbitrary descendant as `C`, hashing only the entrypoint, inferring gate freshness from area freshness, embedding `C`/`D` evidence in dashboard bytes, or regenerating after every delivery-only record.

## Independent Audit Synthesis

| Audit | Confirmed strengths | Material omission found | Resolution |
|---|---|---|---|
| Repository architecture | Repo-local CLI, existing dependency, modular tests | Markdown-only gate authority | Add gate catalog/evidence contracts |
| Contract semantics | Revisions 1–9 and approval manifest are intact | State-domain ambiguity, incomplete lease, dashboard self-reference, mutable approval semantics | R-004 through R-008; bootstrap profile; approval required |
| Verification strategy | Existing atomic/redaction/Git patterns are reusable | Current atomic tests lack injected failure; docs-only changes can skip validator tests | R-011 and R-013 |

No audit recommended product implementation, benchmark generation/execution, dependency changes, or external activity.

## Remaining Material Questions

`DEC-P0-013` and `DEC-P0-014` are decided for planning by the human direction recorded in ADRs 0013 and 0014. No material design question remains hidden. R-004 through R-008 and R-014 through R-015 alter or complete approved program semantics and therefore remain **implementation-blocking until the human approves the newly frozen exact combined feature/material-change subject**. The bridge fixture's null checkpoint is resolved at validation time only from that exact approval; it is neither mutated nor a coordinator default. Planning, checklist generation, task regeneration, read-only analysis, and bounded audits may continue; implementation may not.
