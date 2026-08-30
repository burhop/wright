# Implementation Plan: Canonical Process Definition and Read-Only Engineer View

**Branch**: `codex/078-process-definition-view` | **Date**: 2026-08-30 | **Spec**: [spec.md](spec.md)

## Summary

Ship the smallest customer-visible EPP product increment: one bundled immutable sample product-definition process rendered at a stable Wright browser route as complete accessible text plus a matching lightweight diagram. A bounded reader validates canonical JSON, exact content identity, and all cross-references before the API returns data. The feature is read-only, offline, additive, dependency-free, removable, and incapable of execution or persistence.

## Technical Context

**Language/Version**: Python 3.11–3.14; TypeScript 5.x / React 19

**Primary Dependencies**: Existing FastAPI, Pydantic, `jsonschema`, React, React Router, Vitest, and Playwright only; no new dependency

**Storage**: Immutable packaged JSON/schema under `src/wright_engineering/static/process-definitions/`; no database or migration

**Testing**: pytest reader/API/packaging/native-runtime/non-interference; Vitest component/service; mocked Playwright journey; Wright push and merge gates

**Target Platform**: Installed native Wright on supported Windows/Linux/macOS paths; Docker-specific product verification is deferred

**Project Type**: Existing modular monorepo FastAPI and React web application

**Performance Goals**: Observe whether the valid bundled definition returns and renders within 500 ms p95 across 20 serial measured observations after one warm-up on an otherwise idle declared local test host; record all observations and calculate nearest-rank p95. This scheduler-sensitive timing is diagnostic, not a feature gate; deterministic correctness, bounded input, and functional timeouts remain blocking.

**Constraints**: Offline; read-only; maximum 1 MiB; reject invalid/unsupported/mismatched content before response; no cloud, LLM, MCP, database, renderer dependency, or benchmark execution

**Scale/Scope**: One sample, one API read endpoint, one browser route, three user stories, and no more than 20 tasks

## Constitution Check

*GATE: Passed before research and rechecked after contracts.*

- API routing contains no business logic; validation/reading stays in `tool_registry`. PASS.
- Packaged source works offline without a source checkout, database, or network and is covered by wheel/native packaging tests. PASS.
- Existing engineer/admin read authorization is reused; validation fails closed; no credentials are exposed. PASS.
- No agent, manager, MCP tool, execution authority, server database, or migration is introduced. PASS.
- Component states, mocked page journey, installed smoke, stable test IDs, keyboard, zoom, narrow viewport, non-color, and reduced-motion coverage satisfy the UI pyramid. PASS.
- Existing request traces and support-safe errors are preserved. PASS.
- Planning remains isolated until exact human approval of the read-only boundary amendment plus `material_change` and `feature_implementation`; editable representation and Apply remain deferred under `DEC-P0-002`. PASS.
- Post-contract recheck finds no constitutional exception. PASS.

## Architecture and Boundaries

1. `process-definition.schema.json` is the closed read-only interchange contract. `content_sha256` uses `wright-process-json-v1`: parse strict UTF-8 JSON with no BOM, duplicate keys, non-finite values, non-integer numbers, negative-zero number tokens, or unpaired surrogates; require every key and string value already in NFC; remove only the root `content_sha256`; sort object keys by their UTF-8 byte sequences; preserve array order; serialize integers in minimal base-10 form; emit UTF-8 without escaping non-ASCII, `/`, U+2028, or U+2029; escape `"`, `\\`, and the five short controls `\b\t\n\f\r`, and encode every other U+0000–U+001F control as lowercase `\u00xx`; use `,`/`:` separators and no extra whitespace; then SHA-256 the bytes. Cross-language ASCII, NFC Unicode, control-character, ordering, and rejection vectors freeze this algorithm.
2. `ProcessDefinitionReader` reads bounded installed bytes first and packaged fallback only when installed content is absent; it validates strict JSON, version, digest, uniqueness, and references before returning immutable bytes.
3. FastAPI exposes authenticated `GET /api/process-definitions/{process_id}` with ETag and closed unavailable, invalid, incompatible, and identity-mismatch errors.
4. The React page derives complete text and a secondary SVG/HTML diagram from the same response; no second representation or editing surface exists.
5. One removable feature boundary controls navigation/route exposure. Existing workspace and Rivet routes remain unchanged.
6. Prototype branch artifacts remain read-only evidence and are not imported or copied wholesale.

## Product and Verification Gates

- Demonstrate the stable route, input→action→gate→artifact trace, matching text/diagram IDs, one invalid fixture, and feature-disabled compatibility.
- [contracts/prod-02-study.md](contracts/prod-02-study.md) preregisters comparator, claim, sample, tasks, and thresholds before implementation approval; running it is a later verification action.
- Record `BENCH-02` and `BENCH-03` as no-impact/future prerequisites owned by EPP-B01. The EPP-F02 definition is not a benchmark manifest, receives no `PROC-*`/`EPP-PROC-*` identity, and leaves every process-100 funnel count at `0/100`.
- Selected workspace, Rivet, API, packaging, and native-runtime checks pass enabled and disabled; removal leaves no migrated data.
- A verifier distinct from the writer repeats contract, focused test, browser, packaging, and diff checks on the exact candidate.
- Normally one complete candidate push and at most one consolidated correction push after terminal CI classification.

## Execution Resource Strategy

[execution-resource-plan.md](../../docs/programs/engineering-process-platform/execution-resource-plan.md) governs the Windows/GB10 split. Until its benchmark gate passes, Windows remains authoritative. Afterwards, GB10 may run benchmark-proven faster backend tests, validators, Docker builds, packaging, and independent verification in a separate worktree; Windows retains UI/Playwright, Windows-native lifecycle, Microsoft integrations, and final local integration. Never duplicate suites concurrently or share worktree writes.

## Project Structure

```text
specs/078-process-definition-view/{spec.md,plan.md,research.md,data-model.md,quickstart.md,contracts/,checklists/,tasks.md}
packages/tool_registry/src/tool_registry/process_definition.py
packages/tool_registry/tests/test_process_definition.py
apps/api/src/api/{schemas,routers}/process_definition.py
apps/api/src/api/{composition.py,main.py}
apps/api/tests/test_process_definition_api.py
apps/web/src/services/process-definition.ts
apps/web/src/components/process-definition/
apps/web/src/components/pages/ProcessDefinitionPage.tsx
apps/web/src/{App.tsx,components/layout/Sidebar.tsx}
apps/web/src/__tests__/ProcessDefinition*.test.tsx
src/wright_engineering/static/process-definitions/
tests/ui-integration/process-definition.spec.ts
tests/e2e/test_process_definition.py
tests/packaging/test_wheel_contents.py
tests/native_runtime/test_process_definition_lifecycle.py
```

**Structure Decision**: Reuse the proven packaged-reader/API/service/page boundary, with a distinct small process-definition model. The backend owns validation and identity; the browser owns presentation only.

## Delivery Sequence

1. Approve the exact EPP-F02 read-only boundary amendment and local T001–T019 subject; push/PR/dev integration remain separately authorized actions.
2. Implement schema, sample, reader, and negative tests.
3. Add API and closed errors.
4. Add accessible text, derived diagram, and browser tests.
5. Verify packaging, native fallback, non-interference, demonstration, and exact candidate.
6. After separate external-write authorization, run one push gate/candidate push, terminal CI classification, merge gate, PR merge to `dev`, and dev browser verification.

## Gate impact

| Gate | EPP-F02 evidence | Disposition after local candidate |
|---|---|---|
| `PROD-01` | Validated versioned read-only process definition and stable semantic IDs | Incremental evidence only; gate remains non-passing until its full scope passes |
| `PROD-02` | Preregistered five-participant comprehension study | Study execution is later authorization; gate remains non-passing |
| `PROD-08` | ADR 0021, a replaceable renderer with no new dependency, and the T019 proof that the feature adds no domain-, vendor-, or case-specific dispatch | Incremental evidence only |
| `PROD-10` | Focused and full tests plus native, wheel, offline, enabled/disabled, removal, compatibility, and rollback verification | Incremental evidence only |
| `PROD-11` | Page limitations, recovery and support-safe diagnostics, and the human-repeatable quickstart | Incremental evidence only |
| `BENCH-02`, `BENCH-03` | None; EPP-F02 is not a benchmark case or artifact oracle | Not applicable/no impact; all process-100 stages remain `0/100` |

Commercial readiness, benchmark readiness, publication, and release remain unchanged and non-passing.

## Complexity Tracking

No constitutional violations or new architectural layers are introduced.
