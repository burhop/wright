# Research: Engineering Capability Program Hardening

## Decision 1: Accept deterministic task evidence now; retain moderated study as follow-up

**Decision**: Completion evidence is a deterministic, human-repeatable first-use
walkthrough plus automated task-completion, recovery, keyboard, reflow, zoom,
and reduced-motion assertions. A moderated study with representative engineers
is explicitly deferred and cannot be represented as completed evidence.

**Rationale**: The repository can reproduce and gate the same journey without
credentials or proprietary applications. This makes regressions actionable and
keeps the claim honest while no external participant panel is available.

**Alternatives considered**: Requiring an external study would block all
independent hardening work; declaring automated tests equivalent to observed
human usability would overstate evidence.

## Decision 2: Use WCAG 2.2 reflow, focus, and status-message behavior

**Decision**: Engineering journeys must remain operable at 320 CSS-pixel width
and 200% zoom without two-dimensional scrolling for ordinary content, expose
status changes programmatically without unexpectedly moving focus, retain a
logical focus order, and provide keyboard access to every recovery action.

**Rationale**: These are durable, testable requirements for dense engineering
interfaces and long operations. They directly address the likely failure modes
in multi-panel capability/model/Rivet screens.

**Alternatives considered**: Desktop-width-only acceptance was rejected because
it hides truncation and focus defects; screenshot-only comparison was rejected
because it does not prove semantics or keyboard operation.

**Primary sources**: [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[Understanding Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow)

## Decision 3: Diagnostics are allowlisted local projections, never copied state

**Decision**: Build a versioned diagnostic snapshot exclusively from explicit
safe projections. Recursively reject/redact sensitive key families and unsafe
free text, cap collection counts/string lengths/export size, retain only stable
reason/provider/schema identities and irreversible digests, and enumerate every
included, omitted, redacted, and truncated category.

**Rationale**: Underlying program state includes credentials, environment
values, prompts, tool arguments, local paths, model features, and proprietary
artifacts. A blacklist over raw logs/state is not a reliable export boundary.

**Alternatives considered**: Zipping logs was rejected as unbounded and
secret-prone. Caller-supplied field selection was rejected because it shifts the
trust decision outside the service. Automatic upload was rejected because it
violates local-first and explicit-consent requirements.

**Primary source**: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

## Decision 4: Preview and export use an expiring, principal-bound, one-use digest grant

**Decision**: Preview returns an immutable snapshot, exact SHA-256 digest,
expiry, category manifest, and opaque confirmation token. Export requires the
same principal/workspace/scope plus token and digest, consumes the grant once,
and returns inert JSON as an attachment. Restart invalidates outstanding grants;
the user must preview again.

**Rationale**: This prevents time-of-check/time-of-use substitution, cross-user
or cross-workspace replay, and silent export. Process-local grants avoid adding
durable authority to the data model and fail safely after restart.

**Alternatives considered**: A reusable download URL was rejected as reusable
authority. Persisting confirmation grants was rejected as unnecessary sensitive
state. Regenerating at export time without a digest was rejected because the
contents could differ from the preview.

## Decision 5: Use existing SQLite transactions and native atomic manifests

**Decision**: Keep catalog/model/workspace/scenario state in current SQLite
migrations and native manifest stores. Seed pre-program state, migrate through
the current schema in one controlled lifecycle, make backups first, and either
commit the complete result or roll back. An older runtime encountering newer
unsupported state preserves and quarantines it with an explicit reason.

**Rationale**: SQLite provides atomic, serializable transactions and recovery
semantics already used by Wright. Native manifests already use temp-file,
`fsync`, and atomic replacement. Extending these boundaries is safer than a new
storage subsystem.

**Alternatives considered**: Rebuilding catalogs/caches on every upgrade was
rejected because it loses user enablement and offline availability. Best-effort
partial migration was rejected because it can make mixed-schema evidence appear
current. Destructive downgrade was rejected.

**Primary sources**: [SQLite transactions](https://www.sqlite.org/lang_transaction.html),
[SQLite atomic commit](https://sqlite.org/atomiccommit.html)

## Decision 6: Docker persistence is an explicit named-volume contract

**Decision**: Validate that every supported Compose profile mounts named volumes
for Wright data, configuration, workspaces, and manager state at the documented
paths; ordinary container replacement and `down` preserve them, while `down -v`
is documented as destructive and never used by automated upgrade tests.

**Rationale**: Docker volumes persist beyond an individual container lifecycle
and are the supported mechanism for durable container state. Static contract
tests run everywhere; an opt-in Docker lifecycle test may strengthen but cannot
silently replace exact-platform evidence.

**Alternatives considered**: Container writable layers were rejected because
replacement loses state. Broad host bind mounts were rejected as platform- and
permission-fragile defaults.

**Primary source**: [Docker volumes](https://docs.docker.com/engine/storage/volumes/)

## Decision 7: A support claim requires exact artifact-bound platform evidence

**Decision**: Evidence records must bind runtime/artifact digest, version, data
schema, platform, architecture, package path, storage profile, and lifecycle
result. Fixture, schema, mocked, skipped, inferred, or another-architecture
evidence remains visible but cannot produce `supported`.

**Rationale**: Platform differences affect native startup, file replacement,
permissions, browser availability, Docker architecture, and rollback. The
existing install matrix already follows evidence-driven claims.

**Alternatives considered**: Claiming support from source-level tests was
rejected. Treating one OS as representative of all architectures was rejected.

## Decision 8: Pin browser evidence to the repository Playwright version

**Decision**: Component tests cover state logic, mocked Playwright covers the
complete page journey across Chromium/Firefox/WebKit where configured, and live
system E2E covers the packaged local API/UI happy path. Browser binaries must
match the repository’s Playwright version.

**Rationale**: Playwright versions are coupled to specific browser revisions;
pinning prevents ambiguous browser evidence. Separating tiers keeps detailed
failure diagnosis fast while retaining a real local system boundary.

**Alternatives considered**: Chromium-only coverage was rejected for the final
cross-browser interaction claim. Live-only E2E was rejected as too slow and
poorly isolated for every component state.

**Primary source**: [Playwright browsers](https://playwright.dev/docs/browsers)

## Decision 9: Correct the packaged compatibility ceiling and guard drift

**Decision**: Raise the shipped compatibility contract from data schema 14 to
the actual current migration level 16 and add a deterministic assertion that
the packaged ceiling equals the migration registry’s current version.

**Rationale**: Loops 071 and 072 added durable schema versions 16 and 15. A
runtime that ships those migrations but rejects their data contradicts its own
lifecycle contract and can break ordinary upgrades.

**Alternatives considered**: Downgrading migrations or ignoring the mismatch
was rejected because current installations already legitimately create this
state. Setting an open-ended ceiling was rejected because older runtimes must
reject unknown newer schemas safely.

## Decision 10: Strengthen the authoritative development gate, rehearse only

**Decision**: Add an early named deterministic hardening suite to
`scripts/check-dev-merge.sh`; keep the existing full Python, web, packaging,
docs, native, security, and Playwright gates. Run release/native rehearsal in
dry-run or test mode only. Do not merge `main`, publish artifacts, or mutate a
registry.

**Rationale**: The project defines the script as merge-gate source of truth.
An early slice makes compatibility/persistence/diagnostic failures obvious,
while the existing complete suite remains authoritative.

**Alternatives considered**: Relying only on the late full-suite pass was
rejected because it obscures the program boundary. Adding production release
steps was rejected because this loop is development hardening only.

**Primary source**: [GitHub Actions matrix jobs](https://docs.github.com/en/actions/get-started/understand-github-actions)

