# 100-Process Benchmark Strategy

## Purpose and claim boundary

The benchmark answers a bounded question: for the approved target population and exact candidate/profile, can Wright help users complete 100 distinct, representative engineering-process cases with truthful behavior, independently verified outputs, reproducible evidence, and the declared qualification level?

It does **not** prove universal engineering correctness, production reliability, suitability for an unrepresented industry/application/platform, human professional judgment, commercial supportability, or safety for physical actuation. `100/100` is benchmark evidence only.

The target population and public claim remain explicit P0 decision `DEC-P0-010`. No case may be counted before that decision and the license/provenance policy are approved.

## What counts as one process

A counted process has a stable `process_id`, revision, equivalence family, intended user/role, independently meaningful outcome, lifecycle context, input contract, multi-step capability topology, expected output/artifact contract, failure/recovery behavior, supported profiles, and one or more qualified oracles.

Two cases are variants—not independent processes—when they differ only in cosmetic labels, seed data, parameter values, provider/vendor substitution, file format, or a small topology-preserving change while exercising the same user outcome and oracle. A family contributes at most the approved maximum in the sampling frame. A case counts once in the total even when it occupies multiple cross-coverage cells or profiles.

Revisions preserve identity history. A material change to outcome, inputs, topology, oracle/tolerance, fixture, adapter/tool schema, profile, or attempt policy creates a new revision and invalidates affected evidence. Superseded/retired cases do not remain in the current denominator.

## Sampling and partitions

The proposed collection has exactly 100 current cases and the quotas in [`benchmark-coverage.json`](benchmark-coverage.json). Primary dimensions each assign every case exactly once and sum to 100. Cross-cutting dimensions use minimums/maximums and critical intersections. A collection cannot pass by filling easy cells while leaving a required intersection empty.

Partition assignment occurs before product tuning:

- **60 development cases:** visible for feature development and routine regression.
- **20 frozen qualification cases:** visible to qualifiers but not editable during a candidate evaluation.
- **20 blind holdout cases:** definitions, assets and oracles are outside development-agent visibility under `DEC-P0-009`; Git stores only non-revealing identities/digests/status.
- **At least 10 compatibility/regression sentinels:** tagged across the first two partitions and preserved across releases to detect drift.

A holdout access event is append-only and conforms to [`schemas/holdout-ledger.schema.json`](schemas/holdout-ledger.schema.json). Each chained entry records opaque set/case digests, sequence/prior-entry digest, human custodian and authorization, actor/access event, exact candidate, contamination decision/reason, replacement/reseal evidence and freshness. Exposure to an implementation agent, tuning from a holdout failure, oracle leakage, or unapproved evaluator access marks the affected set `contaminated`; it cannot satisfy a release gate until replaced/resealed under human control.

No benchmark content is generated in this planning phase.

## Qualification tiers

| Tier | Meaning | Proposed coverage |
|---|---|---|
| `T0` | Static manifest, schema, provenance/license, safety, compatibility, oracle and negative-control validation. | All 100 |
| `T1` | Fully deterministic local fixture/mock execution with exact evidence, failures, recovery and artifact assertions. | All 100 |
| `T2` | Clean integration using selected real open-source/local dependencies and safe backend plus Wright gateway probes. | At least 30 |
| `T3` | Explicit opt-in platform/application/cloud/credential/licensed-host evidence on exact hosts. | At least 15, subject to approved claims |
| `T4` | Physical hardware/actuation. | Zero required and prohibited unless separately planned and authorized |

Higher-tier evidence never excuses missing T0/T1. A case counts only at its declared current level. Fixture/contract evidence cannot create a live/platform support claim.

Exact release thresholds, first-attempt policy, per-stratum minimums, repeats, T2/T3 mix and evidence ages are proposed in the coverage matrix but remain subject to digest-bound `DEC-P0-011` before benchmark implementation.

## Process qualification lifecycle

Normal case states:

```text
proposed
-> source_reviewed
-> specified
-> oracle_reviewed
-> fixture_validated
-> pilot_executed
-> independently_reproduced
-> qualified
-> current
```

Exceptional states:

```text
any pre-qualified state -> blocked | rejected
qualified/current -> stale | quarantined | contaminated | retired
stale/quarantined -> new revision at specified -> full requalification
```

Every transition conforms to [`schemas/benchmark-evidence.schema.json`](schemas/benchmark-evidence.schema.json) and names a legal prior/new state edge, prior/new process revision, revision-change class, exact material identities/digests, checks including `not_tested`, outcome/reason, evidence, limitations, independent reviewer, timestamp, stale triggers and recovery. The schema requires every run stage exactly once and in order; an early stop records remaining stages as `not_tested`. `passed` additionally requires all stages, required artifact checks, assertions, negative controls and cleanup to pass. A green narrative or row edit cannot change state.

Required run stages:

```text
planned
-> preflight_passed | blocked_prerequisite
-> running
-> outputs_collected
-> artifacts_verified
-> assertions_evaluated
-> evidence_finalized
-> terminal_classification
```

Terminal classifications are `passed`, `failed_product`, `failed_oracle_or_benchmark`, `failed_infrastructure`, `blocked_prerequisite`, `timed_out`, `cancelled`, and `inconclusive`. They never collapse into a binary value in stored evidence.

## Attempt and repair policy

- Every attempt is append-only and remains in the denominator/attempt history.
- First-attempt and eventual results are reported side by side.
- One infrastructure retry is allowed only when frozen criteria identify a transient condition and no candidate/manifest/oracle/fixture/profile bytes change.
- Product, oracle, fixture, policy or environment changes create a new material identity and evaluation tranche.
- No per-case product repair occurs while a blind holdout evaluation is open. A product failure fails that candidate; later work creates a new candidate and follows the custodian's re-evaluation/replacement rule.
- Local feature repair follows the program's two-cycle limit; benchmark policy cannot reset it.
- Timeout, cancellation, blocked prerequisites, unavailable proprietary hosts, and benchmark defects stay visible; none count as pass.

## Oracle governance

Every expected output has an oracle manifest conforming to [`schemas/oracle-manifest.schema.json`](schemas/oracle-manifest.schema.json) and approved under `DEC-P0-007`. Case manifests and run evidence bind it by immutable oracle ID, revision and content digest. Each manifest records:

- applicability/preconditions and authoritative source/standard/reference;
- exact process/input/output identities;
- invariants, units, coordinate system, tolerance and tolerance rationale;
- validator/assertion implementation and version/digest;
- positive controls and negative/mutation controls proving plausible wrong results fail;
- uncertainty, nondeterminism and disagreement rules;
- author and independent reviewer identities;
- quarantine and expiry/stale triggers.

Oracle families may use exact canonical comparison, schema/semantic assertions, geometric/topological invariants, numerical tolerances, metamorphic relations, independent reference tools, or qualified human review. Subjective visual/usability claims require a frozen task/rubric and independent humans; screenshots prove presentation only.

A self-confirming, ambiguous, unreviewed, non-rejecting or stale oracle cannot produce a pass.

## Artifact verification requirements

Terminal success is insufficient. For each required output, evidence must prove as applicable:

1. expected output reference exists and has the declared identity, type/media/format, producer step/call and upstream lineage;
2. bytes are non-empty where required, within size/resource limits, digest-bound, redacted as policy requires, and stored at the declared lifetime;
3. artifact parses/opens/reloads with the declared independent reader or application subject;
4. units, coordinate frames, dimensionality, schemas and version compatibility are correct;
5. engineering invariants/tolerances and negative controls pass;
6. required artifact-to-artifact relationships and manifest contents are consistent;
7. the user-facing view/open/download/open-in-application action is actually available when promised;
8. cleanup/residue, expiry, retention, reauthorization and rollback are truthful;
9. inputs, outputs, limitations, failed/partial results and recovery remain inspectable;
10. an independent verifier validates the exact unchanged candidate/evidence subject.

The run record carries the case's required-output-set digest, an explicit evidence row for every required output, a completeness attestation and artifact/output/assertion cross-references. Semantic validation rejects a mismatched required-output digest, missing case output, mismatched artifact digest/reference, or a claimed complete set with a missing ID. Schema validation additionally prevents a `passed` record when a required output, parse/open check, applicable assertion, negative control or cleanup is non-passing/not-tested, or when required content is empty.

Missing, skipped, unsupported or inconclusive required assertions make the artifact non-passing. An application accepting a command, MCP transport success, a green run, a screenshot, file existence or syntax alone never proves correctness.

## Reproducibility and profiles

Every run binds repository commit/tree and explicit candidate artifact digests. Its closed `material_identities` object names process manifest, workflow definition, input set, fixture, oracle set, assertion bundle, schema bundle, adapter bundle, tool schema, model identity, prompt, policy, runtime and cleanup-policy digests; an approved canonical not-applicable identity is used instead of omitting a dimension. The environment binds OS/architecture/deployment/runtime and version/application and version/plugin/driver/locale/resource/network/credential-class profile, seed and declared nondeterministic fields. Deadlines, cancellation and cleanup/residue remain explicit stage evidence.

Deterministic T1 cases require identical normalized material outcomes across the frozen repeat policy, excluding only declared observations. Nondeterministic/live cases use a pre-approved repeated-trial and tolerance policy; best-run selection is forbidden. Cross-profile evidence may support only the exact observed profiles.

## Metrics and anti-deception rules

Every metric publishes numerator, denominator, eligible/excluded/blocked/inconclusive counts, partition/profile/time cutoff, first-attempt versus eventual semantics, aggregation/weighting, uncertainty, family clustering/effective-sample warning, baseline and material-identity changes.

Prohibited:

- silently changing denominator, quota, threshold, tolerance or attempt policy after results;
- pooling deterministic and live evidence without stratification;
- micro-averages that hide a failing stratum;
- treating blocked/skipped/stale/unsupported as pass or excluding them without a frozen rule;
- retry-until-green or deleting original failures;
- using benchmark success to waive product, commercial or program-health gates.

## Benchmark stop conditions

Stop collection/qualification/release progression when the program plan, sampling frame, threshold, holdout custodian, oracle authority, provenance/license, safety, output lineage, material identity, required evidence or dashboard consistency is absent; when holdout contamination occurs; when an oracle fails controls or reviewers materially disagree; when attempt policy is exceeded; when unexplained reproducibility disagreement occurs; or when benchmark readiness is cited to waive another gate.

## Change control and freshness

Every material case/policy/oracle/profile change records rationale, approver, new revision/digest, invalidated evidence, coverage blast radius, required reruns and dashboard regeneration. Maximum evidence ages and sentinel cadence are frozen before qualification. A source/tool/schema/runtime/oracle/security-policy or environment identity change makes affected evidence stale immediately even if the time window has not expired.
