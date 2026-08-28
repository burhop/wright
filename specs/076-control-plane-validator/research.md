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

## R-016 — Closed committed-identity correction (proposed DEC-P0-016)

**Decision requiring exact V4 approval**: Preserve TR-0023 through TR-0025 and state revisions 1–26 byte-for-byte. Add the single closed profile `COR-EPP-F01-US1-COMMITTED-IDENTITY-001`, whose literal target set contains six transition output-digest pointers plus 31 occurrences of the commit-ID-as-tree factual defect across the 26 state records. Bind every target to its introducing commit/tree, Git blob, raw SHA-256, exact pointer, and canonical state digest where applicable. The wrong recorded tree `255f2424ff11a9300f31b7a5506279d63d149e8f` resolves only by reading commit `ad162cca048ad23d848673ec4f49f588dcc77aff`'s tree object, `e6a7553036a505003a959eebd0efd3e1683c431a`.

The profile is a factual-metadata disposition, not a virtual rewrite or generic exception. Validation must recompute `37/37`, require every target container to be a strict ancestor of the correction-containing commit, retain each original finding with `resolution_status=resolved` and the correction reference, and reject additions, omissions, substitutions, wildcards, ranges, same/future/circular targets, or corrections of corrections. It cannot target or affect state digests/revisions, lifecycle edges, changed-path manifests, approvals, authority, readiness/gate evidence, benchmark/release evidence, candidates, freshness, or the correction record itself. Older validators fail closed.

**Commercial and benchmark non-interference**: Applying the profile changes only program-health reporting of these exact factual findings. Product readiness, benchmark readiness and all 0–100 counters, commercial readiness, program-health gate inputs other than the correction disclosure, freshness, candidate identity, approval status, release eligibility, and rollback obligations remain byte-for-byte/semantically unchanged. PROG-01 and PROG-05 remain blocked until DEC-P0-016 and the exact profile digest are approved and validator evidence proves the constraints.

**Alternatives rejected**: rewriting immutable evidence; weakening Git-blob identity; accepting a generic correction grammar; treating a commit object ID as its tree ID; hiding original findings; or allowing a correction to make any readiness or release obligation green.

## Independent Audit Synthesis

| Audit | Confirmed strengths | Material omission found | Resolution |
|---|---|---|---|
| Engineering usability | Stable codes and one report model | Correction state and exact pointer were not visible; recovery docs could imply rewriting | Add resolution fields, exact pointer/correction ID, honest unresolved/resolved states, and a known-history recovery journey |
| Architecture | Git-object identity remains authoritative | The wrong tree claim occurs 31 times, not once; v2 authority could not encode planning-only approval | Close the literal 37-claim set and add a closed planning/re-analysis authority variant |
| Commercial/release | Four readiness areas and release approval remain independent | A correction could be mistaken for a waiver or green signal | DEC-P0-016, PROG-01/PROG-05 disclosure, old-reader fail-closed, and zero readiness/release effect |
| Benchmark quality | Existing benchmark invariants are separate | A permissive profile could touch counts, qualification, coverage, or freshness | Explicitly forbid all benchmark/readiness targets and prove projection equality before/after correction |

No audit recommended product implementation, benchmark generation/execution, dependency changes, or external activity.

## Remaining Material Questions

## R-017 — One closed TR-0027 input-origin correction (proposed DEC-P0-017)

**Evidence**: `git log --diff-filter=A` proves both TR-0027 and `APR-EPP-F01-REPAIR-PLANNING-001.json` were introduced by commit `88481d57f1258f59f303f507eafc4e352569bc11`. The approval is absent at TR-0027's declared source `c3012733d358dbbeb4821a2fbf5449d6d1b12c47`. TR-0027's immutable `/inputs/3` therefore describes container-added planning authority as a source input.

**Decision requiring exact V5 approval**: Preserve TR-0027 and the approval bytes. Admit only `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001`, binding one pointer, both raw SHA-256 values and Git blobs, the declared source, unique container/tree, source absence, container presence, and the unchanged two-path manifest. Retain the original finding and classify only its origin disposition as resolved.

**Rejected alternatives**: rewriting TR-0027; treating every container-added artifact as an input; ignoring all input-origin failures; extending the 37-claim correction; accepting a path or commit range; or letting the correction influence authority, readiness, benchmark, candidate, freshness, delivery, or release results.

**Compatibility and recovery**: Unsupported readers fail closed. Any identity, pointer, origin, target-set, manifest or V5 approval mismatch leaves the finding unresolved. Rollback removes the disposition behavior without changing history.

`DEC-P0-013`, `DEC-P0-014`, `DEC-P0-016`, and `DEC-P0-017` are decided. The V5 subject governed the completed T024–T041 work; it is historical authority and cannot authorize a new correction or a T066 retry.

## R-018 — Closed two-claim repair-evidence correction (proposed DEC-P0-018)

**Evidence**: Exact Git-object inspection found two defects in immutable repair evidence produced after the first T066 candidate. State revisions 45 and 46 each record `CANDIDATE_RUFF_FORMAT_DRIFT` at `/active_mutating_lease/recovery/active_cause_id`, although the governing identifier grammar permits only uppercase letters, digits, and hyphens. TR-0044 records a 63-character value at `/inputs/1/sha256`; rehashing the exact TR-0043 blob yields `24c6f2833bf06f74f25e93f0c7e7158e5d659bfbdbd1fb2a6015553bf874fcfe`.

**Decision requiring exact V7 approval**: Preserve every historical byte. Admit only `COR-EPP-F01-REPAIR-EVIDENCE-001`, with two ordered claims: one claim enumerating exactly the two invalid cause-ID occurrences and their authoritative hyphenated value, and one claim binding TR-0044's exact pointer to the recomputed TR-0043 digest. Bind each source container to raw SHA-256, Git blob, introducing commit/tree, exact pointer, and canonical state digest when applicable. Require `2/2` claim equality, `2/2` occurrence equality, no new records, original findings retained, and zero effect on lifecycle, authority, readiness, benchmark, candidate, delivery, or release results.

**Rejected alternatives**: rewriting revisions 45–46 or TR-0044; accepting underscores in the stable-cause grammar; padding or prefix-matching a digest; hiding the original findings; creating a generic historical-evidence waiver; extending either prior correction profile; or using this correction as authority to resume verification.

**Compatibility and recovery**: Unsupported readers fail closed. An omitted, added, substituted, relocated, current-state, wildcard, future, or correction-of-correction target leaves validation blocked. Rollback removes only the new disposition behavior; immutable source evidence remains unchanged.

`DEC-P0-018` was accepted by exact V7 approval. T070–T071 completed and T072 failed closed; V7 is now historical and non-replayable. DEC-P0-019 and the separate roadmap-policy inversion test are the current visible P0 matters.

## R-019 — Closed T072 checkpoint-evidence correction (proposed DEC-P0-019)

**Evidence**: At committed subject `0d1a664f19327b0db03eb0b4c2fa4deb1ccd8bc2`, validation has four fatal rows: two TR-0047 output-digest mismatches, one TR-0050 event-rule mismatch, and the gate-evidence/catalog binding mismatch. The walkthrough module has three failing tests but only two stable causes: stale fixed catch-up/state expectations, and non-resolving finding artifact labels. These are six authorized targets in total. A separate roadmap-policy inversion test also fails and is outside that boundary.

**Decision requiring exact V8 approval**: Admit only `COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001` and its ordered `3/3` claims. TR-0047 claims bind exact Git blob bytes; the recorded values are Windows checkout/CRLF hashes and are never accepted as committed identity. The TR-0050 claim changes only historical disposition of `/state_domain` from recorded `feature` to authoritative `repair`, with fixed event kind/states/revisions/identities and exact required-evidence mapping. Do not add a generic lifecycle rule.

The final gate catalog adds one closed V8 correction evidence class; `gate-evidence.json#/catalog_digest` is then rebound once to that final committed catalog blob. All 34 assertion rows and every other field remain equal. Walkthrough repairs derive current BLOCKED/human/no-lease truth and use repository-relative finding paths; isolated negative fixtures prevent vacuous link coverage.

**Benchmark and release non-interference**: Correction-off/on and pre/post-rebind comparisons cover all four complete areas; honest `counted=0,target=100,not_tested=100`; the existing isolated non-empty synthetic fixture; all BENCH rows, deficits and freshness; candidate, approval, roadmap, dashboard bytes, delivery and release eligibility. Synthetic fixtures are local test inputs, not governed cases or benchmark execution.

**Remaining P0 question**: `test_next_action_human_flag_must_match_policy` hard-sets the current policy value instead of its opposite. It is not one of the two walkthrough causes and cannot be changed under V8. Record it, keep T066 blocked, and request separate disposition after V8 if it remains failing.

## R-020 — Closed V9 preflight-evidence correction (proposed DEC-P0-020)

**Evidence**: Clean-subject validation at commit `9f30322859e8039863b47cdcb0e4c8f29354c9dc` exposed `SCHEMA_REFERENCE_MISSING` for the immutable `EPP-F01-V8-discovery.json` blob and `TRANSITION_MANIFEST_MISMATCH` for immutable TR-0051. Git-object inspection proves the discovery blob is `83beafb5fce4decb927f1ff549634ba664dd3a60` with raw SHA-256 `b6def7c089398b083bf9be118b9d428ac0179c001f2b048df0808c335bb9e6f5`. TR-0051 is blob `cd9d7787325e251b8a365280e208eab567a0b662` with raw SHA-256 `27276a83671ca3a82e4981b1da5d0f176a1465ebf397d8d2fc45447fc2438c2a`; its 35 unique paths exactly equal the containing commit's changed-path set, and only its self path differs in position (recorded 34, canonical 9).

**Decision requiring exact V9 approval**: Admit only `COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001`. The first claim uses an exact-value external schema for the one immutable schema-less artifact without editing it or establishing schema inference. The second recognizes only the exact complete TR-0051 set with the exact recorded and canonical manifest digests; it is not a general sort-before-validate rule. Both claims are mandatory, original bytes/findings remain visible, strict ancestry and Git-object recomputation apply, and unsupported readers fail closed.

**Alternatives rejected**: rewriting either historical JSON file; injecting `$schema` into the old blob; sorting TR-0051 in place; accepting any complete unordered manifest; inferring schemas by filename or content; merging V9 with the roadmap-policy defect or unfinished V8 work. Each alternative either rewrites evidence or creates a reusable waiver.

**Execution boundary**: T077–T080 only after fresh same-subject `material_change` and `feature_implementation` approval. T073–T076, the roadmap-policy repair, T066–T068, EPP-F01B, dependencies, benchmarks, external changes, integration, publication, and release remain excluded. The preserved T073 working copy is outside the approval subject and stays stashed.
