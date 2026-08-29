# Research: Browser Program Status

## Decision 1: Publish a validated local bundle; do not let the API read Git

**Decision**: A deterministic repository-side CLI validates one committed subject and atomically installs a contracted JSON bundle in Wright's stable data root. The API reads only that installed bundle.

**Rationale**: This preserves EPP-F01 as the authority, keeps routes thin, supports air-gapped packaged runtime without a checkout, and prevents refresh from observing dirty or half-written evidence.

**Alternatives rejected**: API or browser reads `docs/programs` directly (checkout coupling and validation bypass); SQLite projection (unnecessary second mutable state store).

## Decision 2: One digest-bound envelope with atomic replacement

**Decision**: `current.json` contains a schema version, exact source identities, generated timestamp, the exact validated EPP-F01 dashboard object, a supplemental projection, and an identity digest. Source identity carries two non-interchangeable hashes: a repository-publisher attestation over the exact committed Git-blob bytes, with an exact evidence reference, and SHA-256 of the parsed object serialized as UTF-8 JSON with recursively sorted keys, no insignificant whitespace, separators `,` and `:`, and non-ASCII characters preserved. The packaged runtime cannot truthfully recompute absent Git-blob bytes; it validates the attestation/evidence relation and independently recomputes only the canonical dashboard and bundle identities. `bundle_id` hashes canonical `source + dashboard + supplement`; the non-semantic publisher observation time is excluded. Same-directory temp write, flush/fsync, validation, `os.replace`, supported directory sync, and failure-preserves-prior behavior are required.

**Rationale**: A single identity prevents mixed panels and makes conditional GET, rollback, caching, and stale diagnosis precise. The digest is an integrity binding, not a trust grant.

**Alternatives rejected**: Independent panel files permit mixed generations; API-computed status makes identical committed inputs render differently.

## Decision 3: Conditional identity polling, not a runtime Git watcher

**Decision**: The browser polls every five seconds with `If-None-Match`. The standard contributor publisher checks committed identity every two seconds by default in bounded `--watch-committed` mode and republishes only when committed HEAD changes. Its mutable operational heartbeat is served separately from `/api/program-status/publisher` and is excluded from bundle identity. Package install/upgrade atomically supplies the packaged bundle. Production runtime observes only atomic replacement.

**Rationale**: This meets automatic refresh while keeping Git and filesystem watching outside the API. A 304 is cheap and unchanged evidence is not reinterpreted.

**Alternatives rejected**: WebSocket/SSE adds needless lifecycle complexity; full-body polling wastes parsing; polling dirty files violates authority.

## Decision 4: Reuse existing Plotly with semantic fallbacks

**Decision**: Reuse Wright's lazy Plotly renderer and installed dependency. Each graph receives a descriptive label, exact timestamp/commit tooltips, prose interpretation, and an accessible table fallback.

**Rationale**: No dependency change is needed and the fallback keeps metrics usable when visualization fails or color is unavailable.

**Alternatives rejected**: Hand-built SVG repeats accessibility work; a new chart library expands supply-chain scope; graph-only display is inaccessible.

## Decision 5: Histories use exact committed observations

**Decision**: The publisher walks only committed evidence admitted by the digest-bound source catalog. A point is included only when its contracted metric rule, source classification, exact commit, and trustworthy ISO-8601 time exist. Causal ordering comes from the append-only transition/commit-parent chain; timestamp is for display, and lexicographic SHA order is forbidden. Missing data remains explicitly unavailable/omitted.

**Rationale**: This prevents misleading ordinal charts and inferred progress. Metric units are contractual.

**Alternatives rejected**: Git traversal order alone is not a time axis; file modification time is not durable evidence; hand-maintained values create a second authority.

## Decision 6: Separate populations and units

**Decision**: Display `100 proposed customer stories` with derived definition-maturity counts separately from `0/100 qualified benchmark processes`. Feature task charts use `completed tasks / tasks in <feature-id>` and appear beside product, roadmap, and release context.

**Rationale**: Proposed work is not executed evidence, and narrow feature completion must not imply product completion.

## Decision 7: Fail closed while retaining last valid context

**Decision**: Invalid newer data never replaces the active view. The API emits a typed failure and the browser retains its last valid bundle with explicit stale/failed age and recovery guidance. With no prior valid bundle, it shows unavailable values only.

**Rationale**: The operator remains oriented without mistaking stale data for current truth.

## Decision 8: Dedicated authenticated page

**Decision**: Add `/program-status` and a sidebar link. Keep the existing workspace `DashboardPage` unchanged in purpose. Protect the API with Wright's existing local session/security middleware.

**Rationale**: Program governance and workspace operation are distinct user jobs.

## Decision 9: Bounded observability without evidence leakage

**Decision**: Log event name, trace ID, bundle identity, outcome, duration, and failure class as structured fields. Never log evidence bodies, credentials, raw commands, or private paths.

**Rationale**: This supports glass-box diagnosis while honoring the allowlist boundary.

## Decision 10: Preserve the authoritative snapshot; do not remodel it

**Decision**: The bundle embeds the schema-valid EPP-F01 dashboard object unchanged. It relies on that object only for its actual contracted fields: exact source/container relation, release candidate, four readiness areas and gates, benchmark summary, release approval/eligibility/formula, and the historical action recorded when that snapshot was generated. EPP-F01B adds typed non-authoritative histories, benchmark context, catalog summary, structured actions/work lanes, governance disclosures, and internal evidence-detail index. The validated current program state's `work.current_next_action` is the sole current program action; metric, benchmark, and lane actions are labeled guidance. Publisher state remains a separate operational response and is not part of the bundle.

**Rationale**: Dashboard status, classification, reason code, freshness, benchmark populations, approvals, and release fields retain their governed contract. Lifecycle, lease, delivery, correction, risk, decision, and finding details come from separate committed evidence and require an explicit closed projection; pretending they exist in the dashboard would hide an authority gap.

## Decision 11: Evidence navigation is internal-first

**Decision**: Every evidence reference links to exactly one internal detail record containing the same exact path/digest plus bounded summary, freshness, recovery, and availability. Paths are normalized repository-relative segments and reject empty, `.`, `..`, or backslash aliases. An optional exact-commit GitHub URL may be shown only when allowlisted, within the length bound, and both schema-valid and parsed as HTTPS `github.com` with no credentials, port, query, or fragment and with exact owner/repository/action/path segments. Packaged runtime labels raw content unavailable instead of exposing or inventing it.

**Rationale**: This keeps evidence usable offline and without a checkout while preventing raw-body exposure.

## Decision 12: Bind repository inputs and precedence through one exact catalog

**Decision**: `program-status-source-catalog.json`, validated by its closed schema and bound by path/digest in every bundle, is the publisher's complete input boundary. It names each exact file or append-only filename grammar, accepted schema IDs, parser contract, selection rule, projection targets, and precedence. Dashboard fields remain authoritative for their source snapshot; validated current program state is authoritative for the sole current action; unresolved conflicts, unlisted paths, unaccepted schemas, or parser drift reject publication.

**Rationale**: Broad directory roots do not tell an implementer which evidence is authoritative or how conflicts are resolved. A digest-bound catalog makes the choice deterministic without requiring source access in the runtime.

## Resolved Clarifications

- No new dependency is needed.
- No remote service or telemetry is permitted.
- No calendar-duration estimate is a progress metric.
- GitHub URLs and CI fields appear only when present in validated evidence.
- EPP-F01B never edits program state or launches benchmarks, tools, builds, pushes, or releases.

## Linux implementation-readiness baseline

A bounded read-only GB10 pass on clean `origin/dev` commit `b776b1182d5b6ee41364eb40b1bc95bf4eff797c` is preparatory evidence, not an EPP-F01B plan or implementation verdict. It confirmed the intended thin-router, composed-service, authenticated top-level route, existing Plotly fallback, package-data, and program-control seams. Baseline results were:

- `tests/program_control_plane`: 261 passed;
- focused `workspace_service` surface state/security/composition/event slices: 37 passed;
- focused `tool_registry` gateway/provider slices: 25 passed;
- six frontend Plotly/safe-renderer/store/browser-adapter files: 39 passed;
- focused native/package slice: 18 passed, 1 skipped, and 1 repeatable failure in POSIX owned-listener detection; and
- three existing FastAPI surface test groups exceeded bounded Linux caps at named actor/token/scope cases.

The listener failure and API-test hangs are pre-existing baseline risks, not evidence that EPP-F01B caused a regression. Implementation verification must run the EPP-F01B-specific route/service tests independently of those surface groups, rerun the named Linux baselines, and classify any persistence before claiming cross-platform readiness. No implementation may silently weaken or skip those checks merely to make the feature green.

## Decision 13: Register program work; do not discover it from repository or process activity

**Decision**: Add a closed committed work registry listing exact task sources and active assignments. The publisher parses registered task checkboxes to derive program and active-feature totals, reconciles entries with roadmap/current lease, and reports undecomposed roadmap items separately. Agent rows require stable identity, exact task, branch, safe worktree identifier or lane, state, purpose, timestamp, and evidence.

**Rationale**: Repository-wide task discovery would mix historical and unrelated specifications, while operating-system process activity cannot prove assignment or authority. A registry makes the population and omissions inspectable without hand-setting totals.

**Alternatives rejected**: Count every `tasks.md` file (misleading scope); infer work from Codex processes or commentary (uncommitted and non-authoritative); keep feature-only totals (does not answer overall work).

## Decision 14: Model customer delivery as orthogonal evidence stages

**Decision**: Add a governed use-case registry. All-use-case totals and the 100-process subset are derived from exact definition, progress, user-visible acceptance, test, independent-verification, and benchmark-qualification evidence. Acceptance evidence is the minimum for `implemented`; independent verification and benchmark qualification require their own evidence. The proposed 100-story catalog remains separate unless a registry entry explicitly relates it.

**Rationale**: Code completion, customer-visible capability, testing, independent verification, and benchmark qualification answer different questions. Keeping them orthogonal prevents control-plane or planning progress from masquerading as product delivery.

**Alternatives rejected**: Treat a proposed story as a use case (planning becomes delivery); infer implementation from commits (no user outcome); use one maturity score (hides missing gates).

## Decision 15: Use an append-only canonical test ledger

**Decision**: Record exact committed test attempts with commit, time, suite, population, category, framework-collected identity-set digest, result counts, and evidence. Retain reruns, but graph only the latest terminal attempt for each `(commit, suite_id, population_id)`. Parametrized cases count by collected identity; aggregate-only populations are not summed with components; overlapping component populations reject publication. Pass rate is `passed / (passed + failed)` and is unavailable when that denominator is zero.

**Rationale**: This provides honest trends and provenance while preventing reruns, parametrization, and aggregate suites from inflating test totals.

**Alternatives rejected**: Scrape recent console output (not durable); sum every run (double counting); treat skipped/not-run as passes or failures (distorts meaning); render absent categories as zero (false evidence).
