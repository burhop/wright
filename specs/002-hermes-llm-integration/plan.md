# Implementation Plan: Hermes & LLM Integration

**Branch**: `002-hermes-llm-integration` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-hermes-llm-integration/spec.md`

## Summary

Connect the Wright application to the local Hermes agent by creating a dedicated "wright" Hermes profile, implementing the `BaseAgentEngine` adapter pattern in the `agent_adapters` package, building FastAPI proxy endpoints that forward chat requests to the Hermes WebUI API with SSE streaming, and wiring the React frontend's existing `AgentService` interface to consume real streamed responses. The end goal: type a message in the Wright Agent Chat UI and receive a live response from Hermes.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0 (frontend)

**Primary Dependencies**: FastAPI ≥0.115, httpx (async HTTP client for Hermes proxy), React 19, react-router-dom 7, Vite 8

**Storage**: Hermes manages its own SQLite state.db per profile. Wright stores nothing locally for this feature.

**Testing**: Vitest (component), Playwright (E2E), pytest (backend)

**Target Platform**: Linux local machine (offline-first)

**Project Type**: Web application (monorepo: `apps/api` + `apps/web` + `packages/*`)

**Performance Goals**: First SSE token visible within 3 seconds of agent generation start. Full response within 30 seconds (excluding LLM inference time).

**Constraints**: Offline-capable (graceful degradation when Hermes unavailable). All UI interactions via design tokens. Agent adapter must be hot-swappable per constitution.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | Routes call `BaseAgentEngine` adapter, no Hermes logic in API |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | Adapter in `packages/agent_adapters/`, routes in `apps/api/` |
| 3 | Offline-first mandate | ✅ Pass | UI shows error state when agent unavailable, sessions remain functional |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | `BaseAgentEngine` ABC with `HermesAdapter` concrete class |
| 5 | Zero-server databases | ✅ Pass | Hermes manages its own SQLite; Wright adds no new databases |
| 6 | Local authentication | ⬜ N/A | Auth not in scope for this feature |
| 7 | Template Method for tools | ⬜ N/A | No new engineering tools in this feature |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | Frontend reuses existing components, no new primitives needed |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Component tests + Playwright integration + planned E2E |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | Trace IDs injected at proxy layer, structlog in all backend modules |
| 11 | Phase isolation + branch discipline | ✅ Pass | On `002-hermes-llm-integration` branch, plan before implement |

## Project Structure

### Documentation (this feature)

```text
specs/002-hermes-llm-integration/
├── plan.md                    # This file
├── spec.md                    # Feature specification
├── research.md                # Phase 0 research decisions
├── data-model.md              # Entity model
├── quickstart.md              # Developer setup guide
├── contracts/
│   └── api-contracts.md       # API and service contracts
├── checklists/
│   └── requirements.md        # Spec quality checklist
└── tasks.md                   # Phase 2 tasks (via /speckit-tasks)
```

### Source Code (repository root)

```text
packages/agent_adapters/
├── src/agent_adapters/
│   ├── __init__.py            # Re-export BaseAgentEngine, HermesAdapter
│   ├── base.py                # [NEW] BaseAgentEngine ABC
│   └── hermes.py              # [NEW] HermesAdapter (httpx proxy to Hermes WebUI)

apps/api/
├── src/api/
│   ├── main.py                # [MODIFY] Mount agent router, add httpx dependency
│   ├── config.py              # [NEW] Hermes profile config (base URL, port)
│   └── routers/
│       └── agent.py           # [NEW] /api/agent/* endpoints (chat, sessions, health)

apps/web/
├── src/
│   ├── services/
│   │   ├── agent-service.ts   # [MODIFY] Replace StubAgentService with HermesAgentService
│   │   └── health-service.ts  # [MODIFY] Real HTTP health checks instead of mock
│   └── components/
│       └── chat/
│           └── ChatTranscript.tsx  # [MODIFY] Handle streaming state indicator

scripts/
└── setup-wright-profile.sh    # [NEW] Idempotent Hermes profile creation + WebUI start

tests/
├── ui-integration/            # [MODIFY] Update Playwright tests for real agent
└── e2e/
    └── agent-chat-e2e.spec.ts # [NEW] Tier 3 E2E test: send message → receive response
```

**Structure Decision**: Follows the existing monorepo layout from feature 001. The `agent_adapters` package — which was scaffolded but empty — receives the `BaseAgentEngine` ABC and `HermesAdapter`. The API gets a new router module under `routers/agent.py` to keep route handlers thin. A top-level `scripts/` directory holds the profile setup script.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
