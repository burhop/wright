# Implementation Plan: CodeQL Security Hardening

**Branch**: `051-codeql-hardening` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/051-codeql-hardening/spec.md`

## Summary

Resolve the 12 production CodeQL findings in the supplied 14-alert baseline by making Wright's network, filesystem, parser, package, browser-content, and error-response trust boundaries explicit and regression-tested. Preserve intentional local Hermes and local-LLM health probes by validating and pinning permitted destinations, move path authority into the owning workspace/data-vault packages, replace ambiguous regex/string checks with structural parsers, and emit generic traceable client failures while retaining full protected logs. Prove or clearly rewrite the SPA containment finding, classify the synthetic mocked test URL correctly, run both merge gates, and merge only the verified feature into `dev`.

## Technical Context

**Language/Version**: Python 3.11-3.14 for API and packages; TypeScript 5 with React 19 for viewer services

**Primary Dependencies**: FastAPI, Pydantic, httpx 0.28.x/httpcore 1.0.x, Python `ipaddress`/`socket`/`pathlib`, structlog/OpenTelemetry, existing `agent_adapters`, `data_vault`, `workspace_service`, and `tool_registry` packages; browser DOM and `URLSearchParams`

**Storage**: Existing SQLite workspace registry and configured filesystem vault/workspace roots; no schema migration

**Testing**: pytest/pytest-asyncio with mocked DNS and HTTP transports, Vitest/jsdom, existing full Python/frontend suites, GitHub CodeQL, `scripts/check-dev-merge.sh`, and `scripts/check-prod-merge.sh`

**Target Platform**: Native Windows 11, Ubuntu 22.04/24.04, macOS Sonoma 14+, and existing Docker Linux runtime; symlink tests conditionally skip only where the host cannot create a link

**Project Type**: Modular Python web service and TypeScript web application in a monorepo

**Performance Goals**: Title and glob parsing remain linear in input length; a health probe has at most two logical candidates, three redirects per candidate, eight DNS answers per resolution, and a bounded ten-second total budget

**Constraints**: Preserve loopback Hermes and explicitly configured local LLM targets; never use ambient proxies for the probe; no raw exception or response body reaches clients; no dependency, scanner configuration, Hermes source, MCP, unrelated product, or `main` change

**Scale/Scope**: Exactly alerts #2, #3, #4, #5, #7, #8, #10, #12, #13, #24, #25, #27, #28, and #29 and their focused bypass regressions

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- **Modular FastAPI boundaries**: Pass. Outbound probe policy lives in `agent_adapters`; vault containment lives in `data_vault`; workspace authorization lives in `workspace_service`; routes only validate transport data and map package results.
- **Offline-first**: Pass. No new cloud dependency is introduced, and all regressions mock DNS/network access.
- **Production distributions**: Pass. Package contents do not change their public distribution roles, and both native/Docker release gates remain mandatory.
- **Docker thick base**: Pass. No image or MCP host software changes are planned.
- **Native runtime isolation**: Pass. Security helpers are application modules inside the existing distribution and do not enter an agent-manager process.
- **Agent abstraction**: Pass. The probe policy is provider-neutral and contains no Hermes-specific code; loopback is a destination class, not a manager branch.
- **Embedded state and file vault**: Pass. The existing SQLite registry authorizes registered workspaces and the data-vault package owns canonical file containment.
- **Security and identity**: Pass. Existing control-plane authentication remains; outbound destination, path, parser, package, browser origin, and error-disclosure boundaries are strengthened.
- **Engineering protocol**: Pass. No engineering/MCP tool behavior changes.
- **Testing pyramid**: Pass. Focused unit/API/DOM regressions precede implementation and existing integration/system gates remain intact.
- **Observability**: Pass. Full failures remain in structured logs and clients receive the correlated trace identifier.
- **Phase and branch discipline**: Pass. Spec Kit created `051-codeql-hardening` from clean synchronized `dev`; the operator explicitly authorized all phases and the feature-to-`dev` merge but withheld a `main` merge.

## Project Structure

### Documentation (this feature)

```text
specs/051-codeql-hardening/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- security-boundary-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/src/api/
|-- main.py                              # safe proxy errors and SPA asset lookup
`-- routers/
    |-- agent.py                         # bounded title parsing, authorized session paths, safe SSE errors
    |-- setup.py                         # thin health-probe endpoint mapping
    `-- vault.py                         # thin data-vault delegation

apps/api/tests/
|-- test_agent_security.py
|-- test_agent_stream_progress.py
|-- test_main_security.py
|-- test_setup_api.py
`-- test_vault_security.py

packages/agent_adapters/
|-- src/agent_adapters/health_probe.py   # URL/DNS/address/redirect/pinning policy
`-- tests/test_health_probe_security.py

packages/data_vault/
|-- src/data_vault/file_vault.py         # generated storage keys and canonical containment
`-- tests/test_file_vault.py

packages/workspace_service/
|-- src/workspace_service/service.py     # registered-or-managed session workspace authorization
`-- tests/test_workspace_service.py

packages/tool_registry/
|-- src/tool_registry/version_check.py   # structural VCS parsing and package validation
`-- tests/test_version_check.py

apps/web/src/services/viewer-panel/
|-- registry.ts                          # total glob escaping
|-- providers/
|   |-- iframe-provider.ts               # root-relative same-origin content URL
|   `-- pdf-provider.ts                  # root-relative same-origin content URL
`-- __tests__/
    |-- registry.test.ts
    `-- providers.test.ts
```

**Structure Decision**: Keep each security rule in the package that owns the authority it protects. API changes stay transport-thin, frontend changes remain inside viewer services, and focused tests sit beside the owning layer. No new package or dependency is required.

## Implementation Sequence

1. Add failing unit/API/DOM regressions for every alert and required bypass category.
2. Implement the outbound probe policy with strict URL parsing, address classification, explicit local-origin authority, DNS pinning, bounded manual redirects, proxy isolation, and sanitized results; delegate to it from the setup route.
3. Add data-vault generated keys/canonical containment and workspace-service registered-or-managed authorization; remove request-selected filesystem creation from API routes.
4. Replace title and glob regex behavior with bounded one-pass parsers and add manager-specific package/VCS validation before network or subprocess use.
5. Replace raw proxy/chat exception output with generic trace-bearing messages and preserve structured exception logs.
6. Make SPA containment explicit with canonical relative-path proof and make iframe/PDF sources root-relative while preserving sandbox behavior.
7. Run focused tests, format/lint/type checks, full dev gate, PR CodeQL/CI, merge to `dev`, final-dev CI and alert disposition verification, then the production-readiness gate without changing `main`.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/security-boundary-contract.md](contracts/security-boundary-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All Constitution v3.0.0 gates remain passing. The design places business rules in existing owning packages, preserves offline/local operation and manager neutrality, retains structured trace correlation, adds tests at the correct layers, and leaves all distribution gates intact.

## Complexity Tracking

No constitution violation or exceptional complexity is required. DNS pinning uses the already installed HTTP stack's Host/SNI request contract and is isolated behind focused compatibility tests.
