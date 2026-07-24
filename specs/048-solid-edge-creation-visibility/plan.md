# Implementation Plan: Solid Edge Creation Visibility

**Branch**: `048-solid-edge-creation-visibility` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

## Summary

Make Solid Edge agent sessions creation-only by attaching an immutable `solid_edge_creation_v1` capability profile to the provider-neutral GatewayService session, projecting only an explicit allowlist, and enforcing new-document, confined-output, visible/open-result, and no-unrelated-recovery rules at call time. Extend the existing resumable chat stream with stable phase events and monotonic heartbeats, carry one correlation identity through planning and MCP execution, persist redacted started/terminal timings in the existing gateway audit store, and configure exactly one subprocess owner for Hermes-driven sessions. Validate the bounded 20 mm x 20 mm x 10 mm part workflow on Windows without changing the clean-container catalog process or adding Solid Edge to the Wright image.

## Technical Context

**Language/Version**: Python 3.11-3.14 for Wright services and tests; C#/.NET SolidEdgeMCP is an external local dependency and is not modified by this feature

**Primary Dependencies**: FastAPI/Starlette, Pydantic, official `mcp>=1.27.2,<2` SDK, asyncio, structlog, OpenTelemetry context helpers, httpx, existing `agent_adapters`, `tool_registry`, `workspace_service`, `data_vault`, and `core` path/redaction contracts

**Storage**: Existing SQLite `gateway_audit_events` for append-only redacted diagnostics; bounded in-memory replay buffers for active/recent chat turns; created `.par` artifacts under the explicitly bound workspace

**Testing**: pytest unit/contract/integration tests, fake lifecycle/agent engines, official MCP client list/call probes, isolated Hermes plugin tests, Windows-only live Solid Edge smoke/latency trials, and `scripts/check-dev-merge.sh`

**Target Platform**: Windows 11 x64 workstation with locally installed Solid Edge and SolidEdgeMCP; Wright API/Hermes remain locally hosted and authenticated; Linux/OCI tests cover provider-neutral policy and transport behavior only

**Project Type**: Modular Python monorepo with FastAPI transport adapters, provider-neutral MCP service, optional Hermes integration, and external desktop CAD automation

**Performance Goals**: First meaningful progress within 1 second; heartbeat gaps no greater than 10 seconds; geometry creation begins within 10 seconds in at least 90% of bounded trials; at least 90% of trials complete within 30 seconds; at least 95% of turn time is attributed to named phases

**Constraints**: Creation requests must target a new document and a confined explicit path; the new document remains visible/open; inspection and semantic-inventory tools are absent and denied; one creation call for the simple-part smoke; one subprocess owner; no secrets or payload bodies in diagnostics; no protocol logging on stdout; no Solid Edge software in the base image; no catalog-validation claim from the live Windows smoke

**Scale/Scope**: One Solid Edge creation profile, one active owner per local server, one bounded stream buffer per active/recent chat turn, the existing engineering MCP catalog and GatewayService, four user stories, and a repeatable batch of at least 20 live smoke trials for percentage-based success criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **Modular boundaries**: Pass by design. Creation policy, profile projection, timing aggregation, and progress models live in packages; FastAPI routes only translate authenticated HTTP/SSE requests. Existing partial route-local logic must be moved behind those package services before completion.
- **Offline-first**: Pass. All production behavior uses local Wright, Hermes, SolidEdgeMCP, Solid Edge, SQLite, and workspace files. No cloud service is required.
- **Container strategy**: Pass under the approved roadmap and repository testing-process precedence over the constitution's stale thick-base wording. Solid Edge remains a Windows host dependency and is not added to the Wright image.
- **Agent abstraction**: Pass. Progress and creation policy are expressed through provider-neutral agent/GatewayService contracts; Hermes is one consumer, not the service owner.
- **Embedded state and file vault**: Pass. Diagnostics use existing SQLite storage and artifacts stay under the bound workspace. No server database is introduced.
- **Security and identity**: Pass. Feature 042 authentication and immutable workspace binding remain mandatory; output paths use the existing resolved workspace capability; client prompts and MCP annotations never authorize a call.
- **Engineering protocol**: Pass. Wright continues to proxy the external MCP server through the official SDK and code-driven calls. Solid Edge visibility is a user-facing side effect, not GUI control by the agent.
- **Testing**: Pass. Unit, transport, reconnect, ownership, redaction, and live Windows tests are specified. Clean-container catalog validation remains separate and unchanged.
- **Observability**: Pass. Structured JSON diagnostics, correlation, redaction, and phase timing are required. Full Jaeger/exporter wiring remains Feature 051 and is not falsely claimed here.
- **Phase isolation and branch discipline**: Pass for this planning command. Existing uncommitted implementation is treated as an unverified prototype and must be reconciled against generated tasks; no commit or merge occurs in this workflow.

## Project Structure

### Documentation (this feature)

```text
specs/048-solid-edge-creation-visibility/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- creation-profile-contract.md
|   |-- progress-diagnostics-contract.md
|   `-- runtime-ownership-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/tool_registry/src/tool_registry/
|-- gateway_models.py            # immutable profile/session and diagnostic values
|-- gateway_policy.py            # creation allowlist and call-time invariants
|-- gateway_service.py           # filtered discovery, calls, audit correlation
|-- gateway_diagnostics.py       # active/completed timing aggregation
|-- gateway_adapters.py          # catalog metadata projection
`-- runners/stdio.py             # child-call duration/size diagnostics

packages/agent_adapters/src/agent_adapters/
|-- progress.py                  # phase taxonomy and user-facing CAD labels
`-- models.py                    # streamed progress event contract

apps/api/src/api/
|-- composition.py               # service/profile/owner construction
|-- config.py                    # explicit MCP runtime-owner configuration
|-- gateway_stdio.py             # stderr diagnostics, stdout protocol only
|-- logging_config.py            # selectable structured-log stream
`-- routers/
    |-- agent.py                 # thin resumable SSE translation
    |-- gateway.py               # thin diagnostics translation
    `-- workspace.py             # passive status behavior

apps/web/src/
|-- services/agent-service.ts    # typed progress/replay parsing
|-- store/sessions.tsx           # ordered progress message state
`-- components/chat/ChatTranscript.tsx # phase/elapsed presentation

apps/web/tests/
`-- ChatTranscript.spec.tsx      # user-visible phase/elapsed states

packages/data_vault/src/data_vault/
`-- gateway_repository.py        # append-only redacted audit reads/writes

hermes-plugin-wright/
|-- bridge.py                    # authenticated Wright API queries
`-- tests/test_bridge.py

tests/
|-- integration/test_solid_edge_creation_profile.py
`-- e2e-live/test_solid_edge_creation_visibility.py
```

**Structure Decision**: Extend Feature 046's provider-neutral GatewayService and existing stream/audit seams. Policy and aggregation stay outside API routes; Hermes receives the same filtered MCP projection as any host. SolidEdgeMCP remains an external dependency with an executable live contract, not a copied Wright implementation.

## Implementation Sequence

1. Characterize the current uncommitted prototype and add failing contracts for profile projection, direct-call denial, new-document arguments, output confinement, replay, timing, redaction, and ownership.
2. Add immutable creation-profile identity to gateway sessions and classify SolidEdgeMCP tools from authoritative server/tool metadata.
3. Implement an explicit creation allowlist and fail-closed call policy; enforce `providerId=solid_edge`, commit/new-document behavior, visible/open completion, explicit confined `outputPath`, and explicit overwrite authorization.
4. Preserve the canonical recipe guidance for a centered rectangle plus `positive_normal` extrusion while keeping prompts advisory and server policy authoritative.
5. Move phase labels, heartbeat scheduling, replay buffering, and terminal fallback behavior into an agent-adapter progress service; keep the API route as an SSE translator.
6. Carry turn/request correlation through GatewayService and child STDIO calls; record started and every terminal outcome with durations, counts, timeouts, and redacted sizes.
7. Move diagnostics aggregation out of the route, add authenticated session-scoped summaries, and prove structured diagnostics use stderr for STDIO processes.
8. Make runtime ownership explicit: Hermes/external ownership disables API startup, reconciliation, and polling side effects while preserving authenticated passive queries.
9. Run fake-provider and MCP transport tests, then perform repeated Windows live smokes with blank and pre-existing documents, failure cases, reconnect, latency attribution, and subprocess-count evidence.
10. Update operator guidance and status evidence, remove generated runtime residue, run all focused suites and the authoritative dev merge gate, and document any genuine live-host limitation.

## Migration and Rollback

- **Session compatibility**: Existing non-Solid-Edge sessions retain the standard profile. A Solid Edge creation session selects `solid_edge_creation_v1` explicitly at composition/host configuration and cannot change profile after opening.
- **Tool visibility**: Inspection tools are hidden from discovery and rejected if called by name. Re-enabling general inspection requires a separately specified future profile, not a feature flag in this release.
- **Artifacts**: No existing document is migrated. Every smoke uses a unique confined output path; immutable created files may be deleted by the operator after evidence capture.
- **Diagnostics**: Reuse the existing audit table and metadata JSON, so no destructive database migration is required. Unknown older metadata remains readable.
- **Runtime ownership**: Default API-owned behavior remains for ordinary deployments. Hermes-driven Solid Edge sessions set the external-owner mode; rollback restores the prior owner setting only after stopping the external process to avoid duplication.
- **Failure**: Invalid recipe, path, overwrite, visibility, profile, authentication, or owner state fails before later calls. No inspection-based recovery is attempted.
- **Code rollback**: Revert the feature as one unit. The prior GatewayService/session/audit schema remains compatible, and no SolidEdgeMCP or Solid Edge installation is changed.
- **Validation boundary**: The Windows live smoke is feature evidence only. Catalog status changes still require `docs/mcp-catalog/mcp-server-testing-process.md` and clean-container evidence.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/creation-profile-contract.md](contracts/creation-profile-contract.md), [contracts/progress-diagnostics-contract.md](contracts/progress-diagnostics-contract.md), [contracts/runtime-ownership-contract.md](contracts/runtime-ownership-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All gates remain passing under the documented roadmap/testing-process precedence. The design makes profile and workspace identity immutable, keeps policy and timing behavior in packages, preserves local authentication and path confinement, uses append-only SQLite evidence, keeps protocol stdout clean, and leaves proprietary host installation outside the container. The live Windows evidence does not weaken or replace clean-container catalog validation.

## Complexity Tracking

No unjustified constitution violations are introduced. The only additional state is an immutable profile on the existing gateway session plus bounded progress/diagnostic views over existing request and audit records.
