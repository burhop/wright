# Live Status Dashboard Contract

## V9 preservation rule

V9 must not regenerate or edit `dashboard.json`. Its two historical preflight dispositions may affect only the original findings' resolution metadata. The four readiness areas, all gate rows and freshness, benchmark `0/100` populations and deficits, roadmap-policy result, candidate, approvals, delivery, release eligibility, and dashboard bytes must remain identical correction-off/on. V9 does not authorize the browser page or historical graphs; those remain EPP-F01B.

## Historical V8 preservation rule

V8 must not regenerate or edit `dashboard.json`. The existing bytes remain `candidate_not_evidence`; benchmark remains honest `0/100`; product, benchmark, commercial, and program-health projections remain independently derived. Correction recognition and final catalog rebinding may change validator finding disposition only. Any change to an area object, gate row/freshness, benchmark population/deficit, candidate, approval, delivery, release eligibility, or dashboard bytes is a stop.

Finding evidence links presented as traversable artifacts must be repository-relative paths. V8 negative fixtures retain unresolved TR-0050 and gate-catalog examples so this requirement cannot pass vacuously after the known findings are resolved.

## Purpose

The dashboard is a read-only, locally generated projection of committed machine-readable state and immutable evidence. “Live” means it is regenerated when committed program/feature/qualification/release evidence changes and can show freshness; it does not imply remote telemetry, automatic upload, or a manually editable SaaS scorecard.

The canonical snapshot is [`dashboard.json`](dashboard.json), validated by [`schemas/dashboard.schema.json`](schemas/dashboard.schema.json). Source artifacts remain authoritative.

Delivery is intentionally split into two bounded features. `EPP-F01` owns validation, provenance, deterministic snapshot generation and CLI rendering. It does **not** provide a browser page. `EPP-F01B` owns the read-only browser projection of that snapshot after EPP-F01 integrates. Wright's existing workspace landing page (`DashboardPage.tsx`) is not the program-status dashboard and cannot satisfy this requirement without the separately specified EPP-F01B evidence contract. Until EPP-F01B integrates, browser status is explicitly unavailable rather than inferred from `dashboard.json` or the CLI.

The checked-in `dashboard.json` is a schema-valid v2 `candidate_not_evidence` snapshot generated during T040. It records its exact source subject and data cutoff, but it does not self-claim committed-current delivery. Only the T067–T068 external validation envelope may establish `committed_valid`.

## Four independent areas

The dashboard always renders these separate areas in this order:

1. `product_readiness`
2. `benchmark_readiness`
3. `commercial_readiness`
4. `program_health`

Each area has its own status, required/passed gate numerator and denominator, gate IDs/statuses, blockers, evidence links/digests, freshness and last successful qualification. There is no weighted/composite score. Overall release eligibility is true only when every required gate in all four areas passes at the same exact candidate and a current human release approval exists.

Program health also discloses each historical correction independently: profile ID/link/digest, correction class, approved or proposed authority, exact verified/expected claim count, unresolved/resolved finding counts, and last verification subject/time. The committed-identity profile reports `37/37`; the TR-0027 input-origin profile reports `1/1`; the repair-evidence profile reports `2/2` claims plus `2/2` exact cause-ID occurrences and the full TR-0043 digest proof. Disclosure is derived from generated evidence and may not hand-set a gate. Applying any correction must leave the four area objects, benchmark summary, lifecycle/lease, freshness, candidate, approval authority, delivery and release eligibility unchanged; any difference fails the snapshot.

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

Every generated snapshot records the exact source Git commit/tree, program-directory tree, candidate/artifact digests, generation time, data cutoff, generator version, the closed tracked entrypoint-plus-`scripts/program_control/**/*.py` source-bundle manifest/digest, and source artifact digests. Every catalog assertion has one evaluator result; every displayed gate row is derived and carries its own explicit `fresh` value. Area freshness is an aggregate and cannot substitute for assertion/gate freshness. Generated dashboard bytes remain `candidate_not_evidence` even after commit and are never approval authority by themselves. A later evidence change makes a candidate stale and requires regeneration rather than manual editing.

Committed-current delivery is a property of an external validation envelope, not a self-claim in dashboard bytes. Validation resolves container `C` from explicit input or infers only `HEAD` when its first parent is source `S` and the diff is exactly the dashboard. Independent passing delivery evidence is then committed in descendant `D`, and the caller must supply that exact commit through `--delivery`; `D` is never searched for or inferred. The envelope binds `S`, `C`, explicit `D`, exact dashboard bytes, and the dashboard-only `S..C` plus delivery-only `C..D` diffs. Neither `C` nor `D` evidence is embedded in the dashboard, so delivery verification does not trigger endless regeneration.

## Privacy and safety

Dashboard input and output use allowlisted metadata only: stable IDs, states, reason codes, counts, digests, public/approved compatibility profiles and bounded summaries. They exclude prompts, raw engineering inputs/outputs, artifact bodies, credentials/tokens/cookies, private paths/endpoints, commands/arguments, proprietary model features, reusable authority and raw logs.

No data is uploaded automatically. Remote telemetry remains disabled by default and requires a separate explicit policy/approval. Support exports remain local, previewed, redacted, inert and user-controlled.

## Refresh and failure behavior

Generation is transactional: validate all sources, compute all four areas, write a candidate snapshot, validate it, then replace the prior local/generated snapshot. On failure, retain the prior snapshot byte-for-byte but mark delivery stale/failed through the external delivery layer and expose the generation error; never edit the snapshot merely to change its delivery status and never publish a partial green snapshot.

Refresh never launches product runs, benchmark cases, MCPs, models, applications or release actions. It only projects existing evidence.

Operators inspect the concise text report first, then use JSON only for exact evidence traversal. Support-safe exports contain stable codes, counts, commit/tree/digests, repository-relative pointers, freshness, and bounded recovery. They exclude raw logs, prompts, payloads, credentials, absolute paths, private endpoints, authority material, and command arguments. `INPUT_CONTRACT_INVALID` requires source/schema inspection; `OUTPUT_*_FAILED` and `OUTPUT_INTERRUPTED` preserve the prior snapshot; `INTERNAL_VALIDATION_FAILURE` requires an isolated developer reproduction. None authorizes manual status editing.

## Minimum dashboard views

- Browser-accessible overview with four accessible traffic-light areas and the non-compensating release formula.
- Gate detail with evidence subject, age, blocker/recovery and history.
- Roadmap/lease/next-action view with active feature plus completed/total Spec Kit task and checkpoint progress.
- Benchmark coverage/partition/qualification/attempt/oracle/artifact/freshness view that always exposes counted/target progress from `0/100` through `100/100` without implying another readiness area passes.
- Commercial compatibility/release-subject view.
- Program risk/decision/repair/verification view.

All views link to exact evidence and freshness, remain keyboard accessible with non-color status text, usable contrast, narrow/zoomed/reduced-motion behavior, and honest empty, loading, stale, blocked, failed, unavailable and unknown states. The page refreshes automatically only when its committed snapshot/evidence identity changes; refresh never invents status, reads uncommitted author state as authority, or mutates the program.

The browser adapter must verify the snapshot schema and source identity before rendering. A failed refresh preserves the last clearly labeled prior snapshot and exposes staleness/failure; it must never replace it with a partial page or a hand-set green value. The page is a projection, not an approval, transition, next-action grant, or authority source.

EPP-F01B must render all correction disclosures and original/resolved findings without editing them. Automatic refresh occurs only when committed evidence identity changes; a proposed, unauthorized, stale, partial or unsupported correction renders an honest blocker and never changes benchmark progress or another readiness area's color.
