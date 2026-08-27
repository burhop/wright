# First proposed Spec Kit features

These are proposals, not implementation authority. Each becomes a separate numbered feature in its own clean `dev`-based worktree and must traverse the complete state machine. The program is never wrapped in one feature.

## 1. EPP-F01 — Control-plane validator and governed dashboard snapshot

**Independent outcome:** a maintainer or fresh agent can run one local validation command and receive a truthful, evidence-linked machine snapshot of program state, roadmap eligibility, risks/decisions, transition validity, and four separate readiness areas.

**Boundary:** planning/program tooling only; no process-runtime or benchmark collection. Reject cycles, missing references, digest mismatch, stale approvals, impossible transitions, WIP/lease conflicts, hand-set aggregate green, and unknown schema majors.

**Ship/revert:** ships as local repository tooling/docs; removal does not alter product data. It generates governed data and CLI reports but does not itself satisfy the browser-accessible status-page requirement.

## 2. EPP-F01B — Browser program-status dashboard

**Independent outcome:** a maintainer opens a browser-accessible, read-only page that renders the validated committed snapshot with the four independent readiness areas, benchmark qualification progress from `0/100` through `100/100`, the active feature and task/checkpoint progress, blockers, next eligible action, exact evidence links, and freshness.

**Boundary:** presentation only. It consumes the EPP-F01 snapshot and validation envelope, automatically refreshes when committed evidence changes, and never hand-sets status, launches product or benchmark work, mutates evidence, or acts as authority. It includes honest empty, loading, stale, blocked, failed and unavailable states plus keyboard, contrast, narrow viewport, 200% zoom and reduced-motion behavior. Wright's existing workspace landing dashboard is not this program-status surface.

**Ship/revert:** additive browser route and read-only adapter behind an independently removable boundary; removing it leaves the snapshot, evidence and CLI validator intact. It must integrate after EPP-F01 and before EPP-F02 becomes eligible.

## 3. EPP-F02 — Canonical process definition and read-only engineer view

**Independent outcome:** an engineer can open a versioned sample process and understand phases, actions, ports, gates, feedback and expected artifacts in an accessible read-only view; text and diagram use the same stable semantic identities.

**Boundary:** no execution, persistence migration, LLM authoring, MCP invocation, or permanent renderer/syntax decision without ADR. Re-specify from `dev`; do not copy prototype components wholesale. Before implementation approval, pre-register the `PROD-02` moderated protocol, equivalent comparator/claim, independent-sample rule and numeric completion/error/recovery/comprehension/accessibility thresholds; do not derive them after seeing results.

**Ship/revert:** feature flag and additive read path; older Wright workflows remain unchanged; removal leaves no migrated data.

## 4. EPP-F03 — Durable run evidence and layered failure inspector

**Independent outcome:** a deterministic executor creates immutable run/step/activity records and an engineer can inspect mode, inputs, progress, outputs, provenance, exact failure layer, blocked dependents, cancellation/reconnect state, and recovery.

**Boundary:** deterministic/local adapters first; no live MCP mutation. Requires decisions on lifecycle deadlines, output retention, and UI/headless equivalence.

**Ship/revert:** additive schema with declared reader/writer range, migration, previous-stable and rollback evidence; old records remain readable with explicit missing evidence.

## 5. EPP-F04 — Exact MCP binding and schema-aware preflight

**Independent outcome:** an author chooses installed server then exact tool, reviews schema/identity/approval, maps typed inputs, and receives field-level readiness diagnostics before any call.

**Boundary:** binding and validation only; no live invocation. Same path must handle at least three structurally different generic tools and contain zero domain/tool-name/case dispatch.

**Ship/revert:** saved bindings are versioned exact identities; stale/missing declarations fail closed; downgrade/rollback preserves or safely marks unsupported bindings.

Later proposed loops include governed UI/headless execution (`EPP-F05`), the benchmark qualification harness (`EPP-B01`), reviewed text/LLM authoring (`EPP-F06`), commercial hardening (`EPP-C01`), and the 100-process qualification tranche (`EPP-B02`). Their dependencies are authoritative in [`roadmap.json`](roadmap.json).
