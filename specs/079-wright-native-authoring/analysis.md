# Native Milestone Planning Analysis

Independent read-only Spec Kit review on September 4 found 26 requirements/outcomes nominally covered by 32 tasks (100% nominal coverage; zero unmapped tasks). Nominal coverage did not establish frozen contracts or implementation readiness. Preserve the original findings below; remediation is the coordinator's response until independently rechecked.

| ID | Original severity and finding | Remediation submitted for review |
|---|---|---|
| C1 | Critical: constitution named only adapters/registry despite accepted workspace-service architecture. | Prospective v3.1.0 amendment explicitly describes established core/data-vault/application boundaries under standing architecture authority; plan updated. |
| U1 | High: no complete bounded schema or concrete valid/invalid vectors. | native-process.schema.json, concrete examples, invalid/draft cases, canonical-vectors.json, field/presentation bounds. |
| U2 | High: operation IDs/signatures, units and decimal rules undefined. | Implementation appendix freezes 12 versioned operations, supported units/dimensions, exact decimal bounds and rejection/rounding behavior. Missing config is saveable but not ready; schema and descriptors distinguish required execution config. |
| U3 | High: API paths/envelopes, pagination, scope, errors and idempotency undefined. | Concrete endpoint/error table, body bounds, workspace/auth resolution, retry fingerprints and original-response replay. Language/operation discovery serves the same contract to clients. |
| U4 | High: restart could interrupt another active executor. | One OS-lock-owning coordinator per root; HTTP CLI uses it. Step/terminal/deadline/cancellation/branch rules and disconnected-caller behavior frozen. |
| U5 | High: artifact publication not tied to terminal CAS; retry semantics ambiguous. | Staged/promoted-unindexed/indexed lifecycle; run/step guard, index/event/result in one transaction; crash/race residue and prior successful-step artifacts defined. |
| U6 | High: restore versus forward-recovery alternatives unresolved. | Preserve schema17 root plus verified schema16 backup; predecessor uses separate restored root without later work; compatible build reopens retained newer root. |
| U7 | High: draft human protocol lacked fixtures/instructions/scoring/dropout rules. | human-study.md v1 and study-trace.json freeze H1–H5, start/stop/time/assistance/failure rules, all-started-attempt retention and final candidate criteria. Recruitment pending. |
| I1 | High: early dashboard/authoring PRs appeared blocked by full milestone gates. | Explicit scoped PR acceptance in implementation appendix; full milestone remains cumulative, post-merge tasks exempt from integration denominator with reason. |
| P1 | Medium: parity digests conflicted with embedded run IDs/timestamps. | Deterministic artifact bytes exclude provenance; run-specific identity is separate. |
| M1 | Medium: token/component layers, structured logs and DB/tool traces only implied. | Explicit task mapping in implementation appendix, retaining current constitutional layers and local tracing. |

The user's follow-up explicitly confirms Rivet replacement and the official language for AI and canvas. FR-001/FR-002 and language-authority.md now require common schema/validation/CAS, discovery, round-trip identity and runtime parity. Autonomous AI authoring and legacy conversion/retirement remain separate future capabilities; native milestone delivery must not imply them.

Contract verification observed during authoring: initial fixtures failed uniqueness because input/output ports reused an ID, then because a process/step shared an ID. Corrected both before freezing. Five runnable-or-runtime-negative fixture documents now pass JSON Schema 2020-12, globally unique IDs, endpoint direction/type/cardinality and artifact output checks. Five accepted and nine rejected canonical JSON vectors are frozen. These checks do not claim runtime success, human evidence or implementation conformance.

Independent follow-up review: pending. No task is marked complete solely from this coordinator-authored remediation.
