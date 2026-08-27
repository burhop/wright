# Dashboard Generation and Provenance Contract

## Subjects

- `S` — committed source input commit. All authoritative inputs are read as Git blobs at `S`.
- `C` — commit containing the generated dashboard. `C` is inferred from Git; it is never embedded as its own identity.
- `R` — exact feature/dev/release candidate evaluated by readiness gates. `R` is independent of `S`/`C`, though evidence in `S` binds it.

## Authoritative Input Manifest

The generator enumerates the complete input set from lifecycle-policy path roles. It excludes:

- `dashboard.json`;
- declared temporary or delivery-sidecar files;
- any checkout-only, uncommitted, ignored, or external file.

For each sorted path it records role, Git blob ID, exact blob-byte SHA-256, schema identity, and schema version. It canonicalizes and hashes this manifest. Missing required inputs and undeclared extras fail closed.

## Generation Sequence

1. Resolve and validate `S`, source tree, and program tree.
2. Load manifest inputs from Git blobs at `S` with strict duplicate-key rejection.
3. Validate schemas, references, canonical/raw digests, lifecycle/history, roadmap, decisions/risks, approvals, WIP, pointer, and lease.
4. Validate the gate catalog and gate evidence for one exact `R`.
5. Derive every required gate and then each independent area.
6. Calculate release eligibility: all four areas passed for `R` and current human release approval bound to `R`.
7. Serialize one candidate dashboard as UTF-8/LF.
8. Write a same-directory temporary file, flush, file-`fsync`, reread, and fully validate it.
9. Atomically replace the target with `os.replace`; perform no fallible validation afterward.

Before commit, the snapshot is `candidate_not_evidence`.

## Committed-Current Relation

A dashboard is `committed_valid` only when:

- `C` contains its exact bytes;
- `C` has first parent `S`;
- `git diff S..C` changes only declared generated outputs;
- the recorded source commit/tree/program tree match `S`;
- the generator digest and complete input-manifest digest match Git objects at `S`;
- every input remains schema/semantically valid;
- every area and release result recomputes identically.

If any condition changes or cannot be proved, delivery is stale/failed and the snapshot is not approval authority.

## Four Independent Areas

Order is fixed:

1. `product_readiness`
2. `benchmark_readiness`
3. `commercial_readiness`
4. `program_health`

Every required catalog gate appears exactly once. Denominators come from the catalog, numerators from current passing gate-evidence rows. Area aggregation uses `failed > blocked > stale > in_progress > not_started`, and `passed` only when every required gate passes. No composite or weighted score exists.

The benchmark summary additionally reports target/counted, first-attempt/eventual, T0–T3, failed/blocked/stale/contaminated/not-tested, and coverage/oracle/artifact/partition/freshness deficits. These fields never affect another area's status.

## Failure Atomicity

Any discovery, read, parse, validation, computation, serialization, write, flush, `fsync`, reread, or replacement failure before the atomic commit point:

- returns nonzero;
- preserves the prior target byte-for-byte;
- deletes the temporary candidate when possible;
- reports bounded failure/staleness in the CLI delivery envelope;
- never edits the prior dashboard to mark it stale.

An interrupted process before replacement has the same recovery contract. A process interruption during the platform's atomic replace may leave either the complete prior or complete candidate file, never a partial file; the next run validates which one exists.

## Seed, Compatibility, and Rollback

The checked-in seed remains `contract_seed_not_evidence`. An output from an unknown generator or unsupported schema is stale. Removing/rolling back the validator leaves source evidence untouched, restores the documented manual validation path, and prevents its generated dashboards from being treated as current.
