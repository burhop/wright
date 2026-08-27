# Live Status Dashboard Contract

## Purpose

The dashboard is a read-only, locally generated projection of committed machine-readable state and immutable evidence. “Live” means it is regenerated when committed program/feature/qualification/release evidence changes and can show freshness; it does not imply remote telemetry, automatic upload, or a manually editable SaaS scorecard.

The canonical snapshot is [`dashboard.json`](dashboard.json), validated by [`schemas/dashboard.schema.json`](schemas/dashboard.schema.json). Source artifacts remain authoritative.

The current program schema is the legacy v1 planning/seed contract and still contains historical status vocabulary. Until EPP-F01 implements and migrates the approved v2 contracts, no v1 `committed_valid` dashboard claim is current or newly creatable: the checked-in v1 snapshot is only `contract_seed_not_evidence`. The approved implementation contract is [`../../../specs/076-control-plane-validator/contracts/dashboard.schema.json`](../../../specs/076-control-plane-validator/contracts/dashboard.schema.json), under which dashboard bytes are only seed/candidate and committed-current status belongs to the external validation delivery envelope.

## Four independent areas

The dashboard always renders these separate areas in this order:

1. `product_readiness`
2. `benchmark_readiness`
3. `commercial_readiness`
4. `program_health`

Each area has its own status, required/passed gate numerator and denominator, gate IDs/statuses, blockers, evidence links/digests, freshness and last successful qualification. There is no weighted/composite score. Overall release eligibility is true only when every required gate in all four areas passes at the same exact candidate and a current human release approval exists.

## Truth rules

- Status vocabulary: `not_started`, `in_progress`, `passed`, `blocked`, `failed`, `stale`.
- Evidence classifications such as `skipped`, `partial`, `unsupported`, `unavailable`, `not_tested`, `inconclusive`, and `contaminated` are shown and cannot be mapped to passed.
- Numerator and denominator are mandatory. The denominator includes every required gate/case/profile under the frozen policy.
- Benchmark area also shows counted/target, first-attempt/eventual, T0/T1/T2/T3, failed/blocked/stale/contaminated/not-tested, partition and coverage deficits, oracle/artifact completeness and evidence cutoff.
- Product area shows user outcomes, failure/recovery states, inspectability, accessibility, exact candidate, compatibility and current blocking defects—not test count alone.
- Commercial area shows approved offering posture, exact supported profiles, packaging/supply chain/privacy/support/repository controls and release-train stage—not rehearsal or merge alone.
- Program health shows WIP/lease, roadmap blockers, open/overdue P0 risks/decisions, repair/push bounds, verifier independence, evidence freshness and flow metrics.
- Any source/digest disagreement, failed generation, exceeded evidence age, changed candidate/policy/oracle/environment identity, or unverified external control marks the affected gate/area stale or blocked.
- A dashboard value cannot override source evidence. Hand-setting overall green is invalid.

## Sources

At minimum the generator consumes:

- `program-state.json` and append-only transition evidence;
- `roadmap.json`, decisions, risks and approvals;
- feature manifests and verification/CI/dev-deployment evidence;
- `benchmark-coverage.json`, case/oracle/qualification/run/holdout/change evidence;
- compatibility, packaging, security/privacy, documentation/support and release evidence.

Every generated snapshot records the exact source Git commit/tree, program-directory tree, candidate/artifact digests, generation time, data cutoff, generator version, the closed tracked entrypoint-plus-`scripts/program_control/**/*.py` source-bundle manifest/digest, and source artifact digests. Every catalog assertion has one evaluator result; every displayed gate row is derived and carries its own explicit `fresh` value. Area freshness is an aggregate and cannot substitute for assertion/gate freshness. The checked-in `dashboard.json` begins as `contract_seed_not_evidence` because the generator does not yet exist. Generated dashboard bytes remain `candidate_not_evidence` even after commit and are never approval authority by themselves.

Committed-current delivery is a property of an external validation envelope, not a self-claim in dashboard bytes. Validation resolves container `C` from explicit input or infers only `HEAD` when its first parent is source `S` and the diff is exactly the dashboard. Independent passing delivery evidence is then committed in descendant `D`, and the caller must supply that exact commit through `--delivery`; `D` is never searched for or inferred. The envelope binds `S`, `C`, explicit `D`, exact dashboard bytes, and the dashboard-only `S..C` plus delivery-only `C..D` diffs. Neither `C` nor `D` evidence is embedded in the dashboard, so delivery verification does not trigger endless regeneration.

## Privacy and safety

Dashboard input and output use allowlisted metadata only: stable IDs, states, reason codes, counts, digests, public/approved compatibility profiles and bounded summaries. They exclude prompts, raw engineering inputs/outputs, artifact bodies, credentials/tokens/cookies, private paths/endpoints, commands/arguments, proprietary model features, reusable authority and raw logs.

No data is uploaded automatically. Remote telemetry remains disabled by default and requires a separate explicit policy/approval. Support exports remain local, previewed, redacted, inert and user-controlled.

## Refresh and failure behavior

Generation is transactional: validate all sources, compute all four areas, write a candidate snapshot, validate it, then replace the prior local/generated snapshot. On failure, retain the prior snapshot byte-for-byte but mark delivery stale/failed through the external delivery layer and expose the generation error; never edit the snapshot merely to change its delivery status and never publish a partial green snapshot.

Refresh never launches product runs, benchmark cases, MCPs, models, applications or release actions. It only projects existing evidence.

## Minimum dashboard views

- Overview with four traffic-light areas and release formula.
- Gate detail with evidence subject, age, blocker/recovery and history.
- Roadmap/lease/next-action view.
- Benchmark coverage/partition/qualification/attempt/oracle/artifact/freshness view.
- Commercial compatibility/release-subject view.
- Program risk/decision/repair/verification view.

All views link to exact evidence and remain keyboard accessible, narrow/zoomed/reduced-motion usable, and honest when empty, stale, blocked or unknown.
