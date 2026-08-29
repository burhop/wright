# Data Model: Browser Program Status

## ProgramStatusBundle

One immutable, size-bounded projection delivered atomically.

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Exact supported contract, initially `1.0.0` |
| `bundle_id` | SHA-256 | Canonical digest of `source + dashboard + supplement` |
| `generated_at` | UTC timestamp | Publisher observation only; excluded from identity |
| `source` | SourceIdentity | Exact committed and validator identities |
| `dashboard` | EPP-F01 dashboard | Embedded unchanged and valid against the EPP-F01 schema |
| `supplement` | BrowserSupplement | History, catalog, governed use cases, test history, benchmark context, work, governance disclosures, and evidence index only |

Validation recomputes `bundle_id`, verifies source and dashboard binding, and rejects unknown fields, unsafe paths, excessive counts, unsupported versions, or any attempt to restate/override dashboard truth in the supplement.

## SourceIdentity

Exact 40-character `commit`, `tree`, and `program_tree`; canonical snapshot path; raw snapshot SHA-256; raw-verification mode/evidence; canonical dashboard-object SHA-256; source-catalog path/digest; passing validation transition; and validation verdict. `snapshot_raw_sha256` binds the exact committed Git-blob bytes, not working-tree bytes, and `raw_identity_verification=publisher_git_blob_attested` states the only component that possesses those bytes performed that check. Source-free runtime validates the attestation's exact evidence relation but does not falsely claim to recompute absent raw bytes. `dashboard_canonical_sha256` binds the parsed object embedded as `dashboard`, serialized as UTF-8 JSON with recursively sorted keys, no insignificant whitespace, separators `,` and `:`, and non-ASCII characters preserved; publisher, runtime, and browser recompute it independently.

## SourceCatalog

`program-status-source-catalog.json` is validated by its own closed schema and bound by exact path/digest in `SourceIdentity`. It contains the complete publisher allowlist: exact paths or closed append-only filename grammars, accepted schema IDs, parser contract IDs, selection rules, projection targets, and total precedence. The publisher rejects any input or projection route outside the catalog. Dashboard truth wins for the fields captured at its source commit; validated current program state wins only for the sole current action and current work context; any other conflict rejects publication.

## Authoritative Dashboard

The `dashboard` field conforms to `specs/076-control-plane-validator/contracts/dashboard.schema.json` without translation. It therefore preserves independently:

- canonical status vocabulary (`not_started`, `in_progress`, `passed`, `blocked`, `failed`, `stale`);
- gate status, classification, reason code, evidence, and boolean freshness;
- all four readiness areas and exact gate numerators/denominators;
- every benchmark population, tier, deficit, attempt, and cutoff;
- release-candidate, release-approval, release-eligibility, release-formula, and the next-action field recorded at that dashboard's source commit.

The supplement cannot shadow readiness, benchmark counts, or release truth. The dashboard `next_action` is immutable historical snapshot context, while `work.current_next_action` is the sole current program action derived from the validated current program state and lifecycle policy. Lifecycle, lease, delivery, benchmark context, correction, risk, decision, and finding details are separately derived through the source catalog into the typed non-authoritative supplement below.

## BrowserSupplement

- `history`: bounded `MetricSeries` records.
- `customer_catalog`: exact proposed-story summary, never benchmark authority.
- `use_cases`: canonical all-use-case and 100-process-subset funnels derived from the governed use-case registry.
- `test_history`: canonical committed test checkpoints with exact suite/source provenance and unavailable categories preserved.
- `benchmark_context`: typed current phase, hold state/reason, dependency states, authorization state, non-governing next qualifying action, and evidence; it never restates the qualified count.
- `work`: current milestone, active feature, lease identity, feature-local tasks/checkpoints, blockers, the sole `current_next_action`, and exactly two ordered delivery lanes.
- `governance`: bounded correction, finding, risk, decision, independent-verification, WIP/repair/push-limit, and flow summaries derived from committed evidence.
- `evidence_index`: internal browser detail records for every linked evidence identity.

## GovernanceSupplement

This is a display projection, never an authority source. It contains bounded arrays of:

- `corrections`: correction profile identity/path/digest/class/authority, approval identity, exact expected/verified claim-ID sets, total/resolved/unresolved finding-ID sets, verification-ID set, subject/time, and evidence references;
- `findings`: stable ID, status, severity, bounded summary, blocking outcome, opened/resolved time, nullable resolving correction and verification IDs, recovery, and evidence;
- `risks` and `decisions`: stable ID, status, severity where applicable, owner, overdue/blocking flags, bounded summary, and evidence;
- `verification`: stable ID, author, verifier, required independence, exact subject, verdict, blocking outcome, finding/correction ID sets, time, and evidence;
- `limits`: WIP maximum, repair maximum, and nullable push maximum; and
- `flow`: active-feature/lease, roadmap-blocker, and open-P0 risk/decision counts.

The publisher copies or derives these fields only through the digest-bound source catalog. Runtime relational validation requires every evidence reference to resolve to exactly one matching `evidence_index` entry; every correction claim/finding/verification relation must be closed, reciprocal, and countable from IDs rather than trusted aggregate numbers.

## StructuredAction

Fields: stable `id`, `label`, `purpose` (`current_program_action`, `metric_guidance`, `lane_next_action`, `benchmark_qualifying_action`), `eligibility` (`eligible`, `blocked`, `requires_approval`, `unavailable`), `authority_state` (`authorized`, `not_authorized`, `not_required`, `stale`, `unavailable`), `requires_human_approval`, nullable blocker, and evidence references.

Rules: display text never grants authority. `eligible` requires no human approval, authority `authorized` or `not_required`, and a null blocker. `blocked` requires no human approval and a non-null blocker. `requires_approval` requires human approval, non-current authority (`not_authorized`, `stale`, or `unavailable`), and a non-null blocker. `unavailable` requires unavailable authority, no claimed approval, and a non-null blocker. Only an eligible `current_program_action` may be rendered as the program's executable next action; all other purposes remain contextual guidance.

## MetricSeries and CheckpointObservation

Every series has a fixed ID-to-semantics mapping:

| ID | Unit / numerator | Inclusion rule | Source class |
| --- | --- | --- | --- |
| `customer_capability` | accepted customer scenarios | Count distinct customer-facing scenarios with exact committed acceptance evidence | `product_acceptance` |
| `quality` | passing required checks / required checks | Snapshot of required candidate checks; skipped/partial do not pass | `test_evidence` |
| `process_automation` | demonstrated lifecycle capabilities | Count distinct contracted lifecycle capabilities with committed demonstrations | `automation_capability` |
| `governance` | passing program-health gates / required gates | Use the authoritative program-health gate population | `program_gate` |
| four readiness IDs | passing gates / required gates | Use the matching authoritative area population | `readiness_gate` |
| `benchmark_qualified` | qualified processes / 100 | Use governed qualification evidence only | `benchmark_qualification` |
| `feature_tasks` | completed tasks / tasks in named feature | Count exact task IDs for one feature; never whole program | `feature_task` |
| `integration_delivery` | completed integration gates / 8 | Count ordered frozen/push/PR/CI/sync/merge/deploy gates | `integration_gate` |

`MetricSeries` fields include fixed unit, counting-rule ID, source class, availability, decision use, limitation, purpose-labeled structured metric guidance, deterministic latest change, omission count/reason, and observations. Metric guidance is never the current program action.

Each observation has exact commit, transition/parent identity, time, value and optional denominator, label, matching source class, required change explanation (nullable only for the first point), and evidence references. Append-only transition/commit-parent order is causal; timestamp is display metadata. Missing identities/times are omitted and counted, never inferred.

## CatalogSummary

Fields: `proposed_total`, source path/digest, and exactly these derived maturity counts: `fully_defined`, `ready_to_specify`, `shaped`, `candidate`, `discovery_shaped`, `discovery`, and `discovery_separate_t4_authority_required`.

Rules: counts sum to total; all labels remain proposed; no value contributes to benchmark qualification.

## BenchmarkContext

Fields: phase, hold state and nullable/required hold reason, identified dependency records with status/blocking/evidence, authorization state, one `benchmark_qualifying_action`, and evidence. It is required even when the qualified count is zero and never repeats or changes the dashboard's governed numerator/denominator. If dashboard state, context, dependencies, and action disagree, publication fails.

## Work and DeliveryLane

Work includes an optional safe projection of the exact program-state lease: `feature_id`, `branch`, `worktree_id`, `dev_baseline`, `worktree_start`, `holder_role`, `lease_mode`, `lease_revision`, acquisition/expiry times, allowed paths, path restrictions, allowed actions, and bounded recovery state. It never exposes an absolute worktree path. Work also contains one feature-local task population, causal checkpoints, blockers, and exactly one `current_next_action` sourced from the validated current program state.

`program_tasks` is derived only from task files listed by `WorkRegistry.task_sources` and contains completed, total, remaining, registered source paths, and roadmap item IDs not yet decomposed. `tasks` remains the active-feature subset. `active_assignments` contains only committed, lease-compatible records with stable agent ID, exact task ID/title/state, branch, safe worktree ID or lane, outcome-oriented purpose, time, and evidence. No valid record means unavailable; process activity is never an input.

Lanes are exactly two closed records in order: `integration`, then `continued_development`. Common fields include exclusive branch, milestone, capability, blocker, structured action, time, and evidence. The integration schema alone admits target, frozen/pushed identity/time, PR, phase, check counts, CI failure, sync, merge gate, and bounded events. The continued-development schema admits only its exact base and authority state; integration-only properties are rejected rather than accepted as null.

## GovernedUseCases

The committed registry contains bounded stable use-case identities and orthogonal evidence lists for definition, progress, user-visible acceptance, tests, independent verification, and benchmark qualification. The publisher derives all governed use-case counts (`total`, `not_started`, `in_progress`, `implemented`, `independently_verified`, `remaining`) and the 100-process subset (`defined`, `in_progress`, `implemented`, `tested`, `independently_verified`, `benchmark_qualified`).

`implemented` requires exact user-visible acceptance evidence. Code/progress evidence without acceptance remains `in_progress`. Independent verification must be passing and bound to that acceptance subject. Benchmark qualification must reconcile exactly with the authoritative dashboard and can never be derived from definition, implementation, tests, independent review, or the proposed story catalog.

## TestRunLedger and TestHistory

The ledger retains every attempt with exact commit, trustworthy time, suite ID, population ID, category (`unit`, `integration`, `e2e`, or `benchmark`), attempt number, terminal flag, aggregate role, collected-test-identity-set digest, counts, and evidence. A canonical checkpoint selects the latest terminal attempt for each `(commit, suite_id, population_id)`, sums only disjoint `component` populations, and keeps `summary_only` runs for detail without aggregation. Each parametrized case is one framework-collected identity. Counts satisfy `total = passed + failed + skipped + not_run`; pass rate is `passed / (passed + failed)` or unavailable when the denominator is zero. Missing categories and missing historical evidence are unavailable, never inferred as zero.

## EvidenceDetail

Every evidence reference points to an indexed detail with stable ID, catalog-allowlisted canonical repository-relative path, exact digest, bounded support-safe summary, freshness, recovery, and availability. Empty, `.`, `..`, duplicate-separator, and backslash path forms are rejected. The browser always links internally to this detail. Optional exact-commit GitHub URLs are secondary links and pass both closed schema grammar and parsed HTTPS-origin/path validation with no credentials, port, query, or fragment. In packaged/offline operation, absent raw content is labeled unavailable; identity and summary remain usable.

## PublisherStatus (separate operational projection)

Fields: state (`active`, `inactive`, `failed`, `unavailable`), mode (`committed_watch`, `package_install`, `manual`), observed committed identity, last attempt/success, nullable failure code, and recovery. It is read through `/api/program-status/publisher`, not included in `ProgramStatusBundle` or `bundle_id`; operational heartbeat changes therefore cannot create false committed-evidence identities. The standard committed-watch publisher checks every two seconds by default. Publisher state is context, never readiness or authority.

## Runtime relational validation

JSON Schema closes individual shapes; both the `tool_registry` reader and browser decoder additionally reject any bundle where:

- action eligibility, authority state, approval requirement, and blocker are incoherent;
- an action's purpose does not match its containing property, more than one current program action exists, or the displayed current action differs from the validated current program state/lifecycle edge;
- an evidence reference does not resolve to exactly one detail with the same path and digest;
- the publisher raw Git-blob attestation lacks one matching evidence detail, the source-catalog digest fails, or a publisher input/projection route is outside the catalog;
- catalog maturity counts do not sum to `proposed_total=100`;
- benchmark context is missing/incoherent with the dashboard's qualification state, or a zero count lacks typed phase, hold/dependency/authority context and next qualifying action;
- integration and continued-development branches are equal;
- an observation source classification differs from its containing series;
- completed tasks exceed total tasks;
- program or active-feature task totals do not equal their exact registered task sources, remaining arithmetic is wrong, a registered source is duplicated, or a roadmap item is omitted from both registered and undecomposed sets;
- an active assignment does not resolve to one registered task and compatible current lease/branch, contains an absolute worktree path, or lacks exact evidence;
- all-use-case or 100-process counts cannot be derived from orthogonal registry evidence, implementation lacks user-visible acceptance, independent verification is not passing/bound, or benchmark qualification disagrees with the dashboard;
- a canonical test checkpoint uses a non-terminal or non-latest attempt, double-counts a parametrized identity or overlapping population, violates count arithmetic/pass-rate semantics, or substitutes zero for unavailable history; or
- correction expected/verified claim IDs are not a subset/equality-consistent relation, resolved and unresolved finding IDs do not form a disjoint partition, a linked finding/correction/verification is absent or non-reciprocal, a resolved finding lacks a passing independent verification, or a verification verdict conflicts with its blocking outcome; or
- the canonical dashboard or bundle digest fails independent recomputation. Raw Git-blob bytes are verified only by the repository publisher and carried as an explicit attestation, never falsely recomputed by source-free runtime.

## Runtime View State

Client-only states are `loading`, `current`, `stale`, `blocked`, `failed`, `unavailable`, and `unknown`.

```text
no bundle -> loading -> current
current + 304 -> current (same identity)
current + valid changed bundle -> current (atomic swap)
current + invalid/unavailable response -> stale or failed (retain prior bundle)
no bundle + invalid/unavailable response -> unavailable
```

Installed-invalid is an error and never silently falls back to packaged data. Packaged fallback is eligible only when installed data is absent. Client state is never written back to evidence.
