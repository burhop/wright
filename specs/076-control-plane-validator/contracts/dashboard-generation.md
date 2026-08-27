# Dashboard Generation and Provenance Contract

## Subjects

- `S` — committed source input commit. All authoritative inputs are read as Git blobs at `S`.
- `C` — commit containing the generated dashboard. Validation resolves it from explicit `--container`, or infers only `HEAD` when its first parent is `S` and its diff is dashboard-only. It is never embedded in dashboard bytes.
- `R` — exact feature/dev/release candidate evaluated by readiness gates. `R` is independent of `S`/`C`, though evidence in `S` binds it.
- `D` — explicit `--delivery` descendant commit containing passing independent delivery-only evidence about exact `C`; it is never searched for, inferred, or an input to the dashboard generated from `S`.

## Authoritative Input Manifest

The generator enumerates the complete input set from lifecycle-policy path roles. It excludes:

- `dashboard.json`;
- declared temporary or delivery-sidecar files;
- any checkout-only, uncommitted, ignored, or external file.

For each sorted path it records role, Git blob ID, exact blob-byte SHA-256, schema identity, and schema version. It canonicalizes and hashes this manifest. Missing required inputs and undeclared extras fail closed.

Validator identity uses a separate closed source-bundle manifest. At `S`, it contains the tracked regular blob `scripts/validate-engineering-process-program.py` plus every tracked regular `*.py` blob recursively below `scripts/program_control/`, with normalized unique paths, Git blob IDs, exact blob-byte SHA-256 values, and byte lengths in sorted path order. The bundle is limited to 100 files and 2 MiB total. Before a passing verdict, generation, or recomputation, every loaded local validator module must resolve within that bundle, the same paths in runtime `HEAD` must have identical Git blob IDs to `S`, and no dirty, untracked, or ignored bundle path may exist; Git-declared text/EOL checkout representation is recorded but not misclassified as a blob change. Symlinks, submodules, missing/extra entries, duplicate paths, local imports outside the bundle, or runtime/source mismatch fail closed. Both report and dashboard expose the canonical digest and bounded entries. Adding, deleting, importing, or changing any module changes identity; hashing only the thin entrypoint is invalid.

## Generation Sequence

1. Resolve and validate `S`, source tree, and program tree.
2. Load manifest inputs from Git blobs at `S` with strict duplicate-key rejection.
3. Validate schemas, references, canonical/raw digests, lifecycle/history, roadmap, decisions/risks, approvals, WIP, pointer, and lease. If the approved closed committed-identity correction is present, recompute its literal `37/37` target set and derive finding disposition before continuing; an absent approval, partial/extra target, or forbidden-class effect fails closed.
4. Validate the gate catalog and gate evidence for one exact `R`.
5. Derive every required gate and then each independent area.
6. Calculate release eligibility: all four areas passed for `R` and current human release approval bound to `R`.
7. Serialize one candidate dashboard as UTF-8/LF.
8. Write a same-directory temporary file, flush, file-`fsync`, reread, and fully validate it.
9. Atomically replace the target with `os.replace`; perform no fallible validation afterward.

The serialized snapshot is always `candidate_not_evidence`, before and after commit. It cannot know or prove the commit that will contain itself.

For the final feature delivery, freeze implementation candidate `R` before independent verification. The independent verifier validates `R` and commits a schema-valid candidate-verification record in source commit `S`. The coordinator then generates without changing code/source evidence and commits only the dashboard as successor `C`. The independent verifier checks the exact dashboard bytes and `S`/`C` relation, then persists passing delivery-only evidence in descendant `D`. A later validator receives that exact commit through `--delivery D`; no graph search or implicit selection is permitted. `D` is evidence about container `C`, not an input to the snapshot at `S`; a new readiness input after `S` makes the snapshot stale and requires regeneration.

## Committed-Current Delivery Envelope

A validation report may classify delivery as `committed_valid` only when:

- `C` contains its exact bytes;
- `C` has first parent `S`;
- `git diff S..C` changes only declared generated outputs;
- the recorded source commit/tree/program tree match `S`;
- the generator source-bundle manifest/digest and complete input-manifest digest match Git objects at `S`;
- every input remains schema/semantically valid;
- every gate row, including its explicit `fresh` value, every area, and the release result recompute identically;
- explicit `D` contains a `kind=delivery`, `verdict=passed` record authored by `actor.role=independent_verifier` with `actor.independent=true`, bound to exact dashboard bytes and `C`; `D` has first parent `C`, and `C..D` changes only the declared delivery-evidence output.

These facts are stored in the report's external delivery envelope, not inside the dashboard. If any condition changes or cannot be proved, delivery is candidate/stale/failed and the snapshot is not approval authority.

## Four Independent Areas

Order is fixed:

1. `product_readiness`
2. `benchmark_readiness`
3. `commercial_readiness`
4. `program_health`

Every required catalog gate appears exactly once. The catalog's closed evidence-class registry maps every class to expected source schema ID and role; each gate contains stable assertion IDs and required class codes. Evidence contains exactly one same-ID result for each assertion, with evaluator, status, classification, reason, exact artifact identity, class/schema/role, freshness, and verifier identity. The validator requires those identities to match both the registry and resolved SourceArtifact manifest and proves their union covers every required class; relabeling an artifact cannot satisfy a class. A gate is derived as passed only when all required assertions are passed/supporting/fresh/evidence-backed/class-complete for exact `R`, the evaluator matches, and the verifier is independent where policy requires. Missing, extra, duplicate, empty-evidence, unknown/mismatched-class/schema/role, stale, non-supporting, evaluator-mismatched, or independence-mismatched results cannot pass. Every report/dashboard gate row contains `id`, derived `status`, `classification`, `reason_code`, exact `evidence`, and boolean `fresh`. Denominators come from the catalog; aggregate evidence rows are not authority. Area aggregation uses `failed > blocked > stale > in_progress > not_started`, and `passed` only when every required gate passes. No composite or weighted score exists.

The benchmark summary additionally reports target/counted, first-attempt/eventual, T0–T3, failed/blocked/stale/contaminated/not-tested, and coverage/oracle/artifact/partition/freshness deficits. The validator derives them from existing governed benchmark records and rejects coverage quota/intersection/equivalence-family defects, illegal qualification transitions, missing case/oracle/output references, incomplete artifact sets, broken holdout chains or contamination rules, invalid attempt ordinals/history, unsupported tier claims, and stale evidence. Exactly 100 target slots are assigned once by precedence to eventual-passed, failed, blocked, stale, contaminated, or not-tested, so those six counts sum to 100; absent slots and counted cases without terminal evidence are not-tested. First-attempt passed is a subset of eventual passed. Tier counts never exceed counted; T1/T2/T3 require T0, T2/T3 also require T1, and T2 and T3 may overlap. Deficit arrays remain independent checks and cannot be cleared by counter arithmetic. These fields never affect another area's status.

The committed-identity correction is disclosed only under program-health provenance as its ID, exact evidence link, approved profile digest, `37/37` verification result, and unresolved/resolved finding counts. It is never a gate result or alternate authority. Applying it must leave all four area objects, the complete benchmark summary, data cutoff/freshness, release candidate, release approval, and `release_eligible` semantically identical to the same input set with the original findings undisposed. Any difference fails validation.

## Failure Atomicity

Any discovery, read, parse, validation, computation, serialization, write, flush, `fsync`, reread, or replacement failure before the atomic commit point:

- returns nonzero;
- preserves the prior target byte-for-byte;
- deletes the temporary candidate when possible;
- reports bounded failure/staleness in the CLI delivery envelope;
- never edits the prior dashboard to mark it stale.

An interrupted process before replacement has the same recovery contract. A process interruption during the platform's atomic replace may leave either the complete prior or complete candidate file, never a partial file; the next run validates which one exists.

## Seed, Compatibility, and Rollback

The checked-in seed remains `contract_seed_not_evidence`. An output from an unknown generator or unsupported schema is stale. A reader that does not support the exact approved correction profile fails closed rather than ignoring it. Removing/rolling back the validator leaves source evidence untouched, restores the documented manual validation path, returns corrected findings to unresolved, and prevents its generated dashboards from being treated as current.
