# Independent Readiness Gates

## Gate computation

Each gate is `not_started`, `in_progress`, `passed`, `blocked`, `failed`, or `stale`. `skipped`, `partial`, `unsupported`, `unavailable`, and `not_tested` are evidence classifications, never passing statuses. A gate passes only when all required assertions point to current evidence for the exact candidate subject.

Overall release eligibility is:

```text
PRODUCT_READY
AND BENCHMARK_READY
AND COMMERCIAL_READY
AND PROGRAM_HEALTHY
AND HUMAN_RELEASE_APPROVAL
```

No percentage, test count, process count, severity average, or executive override can compensate for a failed independent area. Exceptions must be explicit, time-bounded decision records, and a P0 exception remains release-blocking.

## Product capability gates

| ID | Required capability | Passing evidence |
|---|---|---|
| `PROD-01` | Canonical process semantics | One versioned definition projects consistently to code/text, diagram, UI, CLI, and headless paths; invalid edits preserve the last valid version; definition and immutable run state are separate. |
| `PROD-02` | Engineer-readable UX | Before the affected feature is implementation-approved, freeze a digest-bound moderated protocol with representative roles/tasks, an equivalent baseline where making a comparative claim, minimum independent sample, completion/error/recovery/comprehension thresholds, scale/focus scenarios, accessibility criteria, and rejection of coached/duplicate/incomplete trials. Current evidence must meet those frozen thresholds and cover empty/loading/blocked/failure/cancel/reconnect/stale/recovery, keyboard, narrow viewport, 200% zoom, and reduced motion. |
| `PROD-03` | Truthful execution modes and provenance | Validate-only, fixture, unconnected, and live modes are unmistakable in UI/history/export/dashboard; current-run evidence alone drives findings; no fixture-specific semantic result is applied to arbitrary input. |
| `PROD-04` | Layered failure and recovery | Definition, preflight, semantic needs-input, mapping/schema, approval, execution, outcome, and cleanup are distinct; dependents report why they did not run; each non-success has a bounded recovery or explicit external intervention. |
| `PROD-05` | Inspectable liveness and control | Durable run/step IDs and registered/connected/first-event/first-output/terminal timestamps; activity, elapsed/last activity, cancellation, boundary and total deadlines, reconnect reconciliation, bounded cleanup, and typed terminal causes. |
| `PROD-06` | Exact governed authority | Provider/model/tool/schema/application identity is exact and reviewable; bindings are revalidated; application-backed execution proves authoritative identity/exclusivity; hard no-tools claims have executor evidence; approvals and revocation are enforced. |
| `PROD-07` | Inspectable and actionable results | Every executable step exposes bounded inputs, readable output, exact data/evidence, redaction/truncation, provenance, and recovery; successful runs expose usable output references with lifetime, ownership, allowed actions, expiry, and cleanup. |
| `PROD-08` | Generic architecture | Static/dependency review proves no benchmark-case, domain, vendor, tool-name, or file-format dispatch in generic orchestration; renderer and syntax choices are ADR-backed and replaceable where required. |
| `PROD-09` | Security, privacy, and safety | Threat/authority model, secret and proprietary-data boundary, egress destinations/categories, telemetry opt-in, redaction, resource limits, cleanup, and no physical/production mutation without explicit authority. |
| `PROD-10` | Quality and compatibility | Focused/full tests, human evidence, current public/durable contract schemas, migrations, previous-stable reading, restart/offline/update/rollback/uninstall behavior, and historical-state tests pass for the exact candidate. |
| `PROD-11` | Documentation and supportability | User/operator/developer docs, limitations, recovery, support diagnostics, and known-issue paths match the candidate and contain no unsupported claims. |

Every product feature must declare which `PROD-*` gates it changes and provide explicit evidence or `not_applicable` rationale approved in its charter.

## Benchmark readiness gates

| ID | Required capability | Passing evidence |
|---|---|---|
| `BENCH-01` | Governed sampling and distinctness | Exactly 100 current counted process identities satisfy the approved primary/cross-coverage matrix; equivalence-family and duplicate review prevents variants inflating count. |
| `BENCH-02` | Qualified manifests | Every counted process has source/provenance/license/safety review, stable revision, user outcome, actors, preconditions, exact inputs/outputs, capability graph, time/resource budget, cleanup, failure injections, and supported qualification level. |
| `BENCH-03` | Valid oracles and artifacts | Every required output has an independent oracle with units/tolerances/assertion version and producer trace; existence, transport success, screenshots, or syntactic parse alone never establish engineering correctness. |
| `BENCH-04` | Reproducible execution | All 100 pass T0 manifest and T1 deterministic qualification at the exact candidate; declared T2/T3 subsets pass on their exact environments; failures/skips/stale evidence remain in denominator. |
| `BENCH-05` | Holdout and anti-overfitting | 60 `development`, 20 `frozen_qualification`, and 20 `blind_holdout` cases obey access rules; candidate freezes before holdout; case/domain dispatch review and perturbation/metamorphic checks pass. |
| `BENCH-06` | Coverage and failure behavior | Coverage quotas, multi-step structure, feedback/approval, offline/live/provider/platform mix, and required failure-injection/recovery classes meet the matrix without prohibited substitution. |
| `BENCH-07` | Independent qualification and freshness | Qualifier is independent of the candidate implementation for claimed gates; source/runtime/oracle/environment digests and maximum ages are current; changed subjects invalidate evidence. |
| `BENCH-08` | Truthful reporting | Dashboard shows numerator/denominator, failed/blocked/skipped/stale/not-tested counts, levels, evidence age, and last success; `100/100` never implies product/commercial/program readiness. |

## Commercial readiness gates

| ID | Required capability | Passing evidence |
|---|---|---|
| `COMM-01` | Approved offering posture | Human decision states whether the target is supportable public-alpha evaluation or a production-supported commercial offer, including supported uses/exclusions, support/SLA boundaries, owner, incident/security response, and terms. |
| `COMM-02` | Packaging and supply chain | Clean candidate contents, dependency/license review, notices, SBOM, provenance, attestations, vulnerability policy/exceptions, and immutable artifact manifests pass. |
| `COMM-03` | Privacy and operational safety | Telemetry/egress/retention/deletion/proprietary-data/support-export policies and customer-facing disclosures are approved and tested; support data stays local/inert by default. |
| `COMM-04` | Evidence-backed compatibility | Each claimed platform/architecture/manager/storage profile has current supporting artifact/host evidence; fixture, contract, skipped, stale, or other-platform results are non-supporting. |
| `COMM-05` | Lifecycle, upgrade, and rollback | Clean install/start/status/doctor/use/stop/update/persist/rollback/uninstall/offline and retained-state behavior pass against previous stable and current candidate; rollback targets immutable subjects. |
| `COMM-06` | Documentation and support operations | Onboarding, failure recovery, limitations, compatibility, privacy, backup, rollback, release notes, support owner/triage/contact-path smoke, and known issues are ready. |
| `COMM-07` | Repository and release controls | Branch protection, required checks, protected environments, secret scanning/push protection, registry configuration, and release permissions are verified external evidence, not assumptions. |
| `COMM-08` | Exact-subject release train | Dev deployment, `dev` to `main` production gate, build-once Python/OCI candidates, TestPyPI/PyPI, Hermes/Codex, identical GHCR/Docker Hub digest, published lifecycle on Linux/macOS/Windows, public bounded-retry verification, versioned docs, and GitHub Release last all pass. |

## Program-health gates

| ID | Required capability | Passing evidence |
|---|---|---|
| `PROG-01` | Valid control plane | Schemas parse, references/digests match, roadmap is acyclic, state revision is monotonic, eligibility is derived, and dashboard is generated from source evidence. If a committed-identity correction exists, its exact profile/schema, V4 approval binding, strict ancestry and literal `37/37` Git-object recomputation pass; original findings remain visible and unsupported/partial/extra profiles block. |
| `PROG-02` | Bounded WIP and isolation | One mutating feature lease, isolated worktree/branch, no shared writable worktree, no singleton-pointer conflict, and lease recovery evidence. |
| `PROG-03` | Independent verification | Every integrated feature has a separate verifier on an unchanged exact tree; original failures/skips and findings remain visible. |
| `PROG-04` | Repair and CI discipline | Stable failure causes, bounded local repairs, two-same-cause push stop, deterministic reproducer before further push, and no CI-as-debug loop. |
| `PROG-05` | Risk/decision/change health | No hidden or overdue P0 question/risk/exception; material changes invalidate affected evidence and approvals; decision register is current. DEC-P0-016 and RISK-018 block while the correction profile is proposed or unapproved, and a correction can never act as a readiness, benchmark, authority, or release waiver. |
| `PROG-06` | Delivery flow | Roadmap dependency/WIP metrics, review age, evidence freshness, defect escape, rollback readiness, and token/context efficiency stay within declared thresholds. |
| `PROG-07` | Integration truth | Feature completion includes exact merged `dev` deployment, health, changed-journey smoke, digest, and rollback identity; release completion is not inferred from merge. |

## Feature implementation approval gate

Before `IMPLEMENTATION_AUTHORIZED`, the feature must have:

- complete spec, clarification record, plan/research/data model/contracts/quickstart as applicable;
- requirements-quality checklists with no override;
- dependency-ordered, independently testable tasks including verification, compatibility, rollback, docs, and benchmark delta;
- persisted `speckit-analyze` report with zero critical/high findings and all medium findings dispositioned;
- exact artifact digests and a human approval record;
- no overdue blocking decision/risk and one available mutating lease.

Any subject change invalidates approval and returns to the earliest affected lifecycle state.
