# Engineering Model Library Requirements Quality Checklist

**Purpose**: Review whether Loop 071 requirements are complete, unambiguous, measurable, safe, recoverable, and usable before task generation
**Created**: 2026-08-13
**Feature**: [spec.md](../spec.md)

## Identity, discovery, and evidence

- [x] CHK001 Are model, package, variant, artifact, runtime, vector, installation, and binding identities independently specified so evidence cannot transfer accidentally? [Completeness, Spec §FR-003–FR-006]
- [x] CHK002 Is immutable source resolution distinguished clearly from mutable discovery aliases and confirmation invalidation? [Clarity, Spec §FR-009–FR-010]
- [x] CHK003 Are source, license, artifact, runtime, compatibility, security, and test evidence freshness states explicitly distinguishable? [Completeness, Spec §FR-007]
- [x] CHK004 Are approved, needs-review, gated/external-action, incompatible, deprecated, withdrawn, and blocked meanings defined consistently with install eligibility? [Consistency, Spec §FR-005]
- [x] CHK005 Are package and variant task contracts required to state units, coordinate conventions, label order, and confidence semantics wherever material? [Coverage, Spec §FR-003, Edge Cases]
- [x] CHK006 Are model usefulness, maturity, intended use, limitations, platform, hardware, runtime, size, and trust requirements sufficient for a two-minute no-download decision? [Measurability, Spec §FR-002, SC-001]
- [x] CHK007 Is the first-catalog requirement explicit about both a generated Wright fixture and a specifically reviewed external revision without treating metadata as approval? [Clarity, Spec §FR-006, Clarifications]

## Source, license, and credential boundaries

- [x] CHK008 Are exact paths, per-file and aggregate byte ceilings, digests, media types, roles, source revisions, and approved origins mandatory before acquisition? [Completeness, Spec §FR-003, FR-009–FR-011]
- [x] CHK009 Are requirements explicit that Wright never requests gated access, accepts terms, purchases service, or discloses identity on a user's behalf? [Boundary, Clarifications, Out of Scope]
- [x] CHK010 Are fine-grained token references restricted to fresh user-authorized plans and excluded from model files, runtimes, logs, evidence, and exports? [Security, Spec §FR-012, Clarifications]
- [x] CHK011 Are license expression, authoritative evidence, attribution, acceptance state, revision changes, and redistribution policy all required independently? [Completeness, Spec §FR-003, FR-013]
- [x] CHK012 Are missing, changed, custom, contradictory, or action-requiring license cases specified as blockers rather than inferred approval? [Exception Coverage, Spec §FR-005, FR-013]
- [x] CHK013 Are redirect host/transport changes and credential-forwarding rules addressed before source authority can change? [Security, Edge Cases, Spec §FR-011–FR-012]

## Artifact and format safety

- [x] CHK014 Are absolute/traversing/duplicate normalized paths, links, executable bits, nested archives, undeclared files, and excess expansion explicitly rejected for online and offline paths? [Coverage, Spec §FR-011, Edge Cases]
- [x] CHK015 Are pickle, joblib, source, native libraries, scripts, macros, plugins, and remote code unambiguously outside approved model-data formats? [Clarity, Spec §FR-014]
- [x] CHK016 Are safe-format claims variant-specific and coupled to parser/runtime/resource review rather than extension alone? [Consistency, Spec §FR-004, FR-014]
- [x] CHK017 Are truncation, length-equal wrong content, excess response bytes, corrupt cache, concurrent writers, and disk exhaustion all covered? [Exception Coverage, Spec §FR-011, Edge Cases]
- [x] CHK018 Are staging, verified content, active installation, quarantine, and export states distinguished so partial bytes cannot appear ready? [Clarity, Spec §FR-015–FR-017, SC-005]
- [x] CHK019 Are deduplication and cache reuse requirements consistent with private/gated access scope and package/workspace references? [Consistency, Spec §FR-016, Clarifications]
- [x] CHK020 Are resume requirements tied to immutable representation validators and safe restart behavior rather than byte count alone? [Recovery Coverage, Spec §FR-011, Edge Cases]

## Runtime, resources, and gateway authority

- [x] CHK021 Is model installation explicitly unable to install runtimes, frameworks, drivers, compilers, services, containers, or global settings? [Boundary, Spec §FR-018, Clarifications]
- [x] CHK022 Are runtime adapter identity, version, contract, format/task support, platform/provider compatibility, health, and conformance evidence all required? [Completeness, Spec §FR-019]
- [x] CHK023 Are CPU, RAM, disk, GPU/VRAM, driver/provider, load/inference time, concurrency, and output ceilings measurable before execution? [Measurability, Spec §FR-008, FR-020]
- [x] CHK024 Are typed input/output validation, non-finite output, malformed schemas, oversize output, hang, crash, and cleanup residue requirements complete? [Exception Coverage, Spec §FR-020–FR-022, Edge Cases]
- [x] CHK025 Is cancellation defined as winning over late output with bounded escalation, unload, process cleanup, and truthful residue? [Clarity, Spec §FR-022, Acceptance Story 3]
- [x] CHK026 Are mandatory real test-vector identities and evidence required before readiness and enablement rather than process success? [Acceptance Quality, Spec §FR-021, Clarifications, SC-006]
- [x] CHK027 Is direct manager/Rivet-to-runtime access prohibited while typed workspace-gateway discovery and call behavior remain explicit? [Authority, Spec §FR-023–FR-025]
- [x] CHK028 Are cross-workspace, stale binding, unreviewed workflow, disabled installation, policy denial, and direct-runtime attempts all specified to fail closed? [Security Coverage, Spec §FR-023–FR-025, SC-007]

## Lifecycle, references, and recovery

- [x] CHK029 Are confirmed plan identity, expiry, principal binding, exact effects, prompts, rollback, cleanup, and invalidation conditions objectively specified? [Completeness, Spec §FR-009–FR-010]
- [x] CHK030 Are durable operation transitions, idempotency, restart reconciliation, progress, cancellation, failure, and terminal immutability defined? [Recovery Coverage, Spec §FR-015, FR-026]
- [x] CHK031 Are update comparisons required to cover license, artifacts, runtime, schemas, units, resources, vectors, limitations, and redistribution? [Completeness, Spec §FR-027]
- [x] CHK032 Is failed update behavior unambiguous that the prior healthy revision remains active and reusable? [Acceptance Quality, Spec §FR-028, SC-008]
- [x] CHK033 Are disable, uninstall, content retention, purge, and cache cleanup meanings distinguished consistently? [Clarity, Spec §FR-029–FR-031, Clarifications]
- [x] CHK034 Are every durable reference class and active lease addressed before content deletion can be permitted? [Safety Coverage, Spec §FR-030–FR-031, SC-009]
- [x] CHK035 Are export/import requirements symmetric for validation while excluding secrets, authority, host paths, private metadata, and non-redistributable bytes? [Consistency, Spec §FR-032–FR-033]

## UX, compatibility, and extensibility

- [x] CHK036 Is the engineering-model library explicitly separated from conversational model setup while preserving existing setup behavior? [Scope, Spec §FR-001, FR-039]
- [x] CHK037 Are offline, loading, blocked, planning, transferring, verifying, testing, activating, cancelling, failed, residue, ready, updating, rollback, and removal states all given plain-language status and recovery requirements? [UX Completeness, Spec §FR-034–FR-036]
- [x] CHK038 Are keyboard, focus, announcements, non-color status, narrow-width, zoom, and serious/critical accessibility outcomes measurable across effectful journeys? [Accessibility, Spec §FR-037, NFR-006, SC-011]
- [x] CHK039 Are performance, metadata/evidence/output bounds, offline determinism, secret redaction, normal-gate exclusions, and package-distribution behavior quantified sufficiently? [Non-Functional, Spec §NFR-001–NFR-008, SC-010]
- [x] CHK040 Can a maintainer add a package or adapter through documented versioned contracts/conformance tests without lifecycle-service changes, while unknown versions fail closed? [Extensibility, Spec §FR-040–FR-043, SC-012]

## Notes

- All 40 requirements-quality items pass after clarification and Gate D planning.
- Review depth is formal PR review; primary focus is supply-chain trust plus lifecycle/runtime authority, with UX, recovery, compatibility, and extension boundaries included because they materially affect safety.
