# Quickstart: Rivet Hermes AI and MCP Execution

This document is the implementation verification recipe. Normal steps use deterministic local doubles; the final live section is opt-in.

## Prerequisites

- Python 3.11+
- Node.js 22 for rebuilding/verifying the pinned Rivet artifacts
- Wright development dependencies installed
- Existing Rivet 2 editor work from feature 066 present on this child branch

## Deterministic verification

```bash
uv run pytest packages/agent_adapters/tests/test_hermes_openai_bridge.py
uv run pytest packages/workspace_service/tests/test_rivet_validation.py packages/workspace_service/tests/test_rivet_runtime_host.py
uv run pytest packages/workspace_service/tests/test_rivet_mcp.py packages/tool_registry/tests/test_gateway_rivet_mcp.py
npm --prefix apps/web test -- --run DirectRivetSurface.spec.tsx
node --test integrations/rivet/runner/tests/runner-contract.test.mjs
```

Run UI and packaging coverage:

```bash
npx playwright test tests/ui-integration/workspace-surfaces/rivet-ai.spec.ts
uv run pytest tests/packaging/test_wheel_contents.py
```

Expected results:

- The editor config selects `wright-hermes` without any OpenAI key prompt.
- A controlled Graph Builder tool response applies a graph and survives save/reload.
- The basic template runs through both canvas service and MCP with the same output.
- Wrong tokens, unsafe slugs/paths, stale revisions, unreviewed revisions, denied capabilities, oversized payloads, and timeouts fail closed.
- No test opens a live subscription connection.

## Manual Wright chat acceptance

Start Wright and Hermes normally. In a workspace with the Rivet MCP enabled, use this prompt:

```text
Use the Rivet workflow MCP. List the available templates, create the Basic Flow template as chat-basic if it does not already exist, validate it, and tell me the exact revision and digest. Do not run it until its current revision is approved.
```

Approve the reported revision through Wright's existing workflow review UI, then send:

```text
Use the Rivet workflow MCP to run the approved chat-basic revision. Report the run ID, terminal state, and bounded outputs.
```

Open `chat-basic` in the Rivet canvas and verify it is the same authoritative document.

## Opt-in live Hermes/Codex smoke

Confirm local Hermes is authenticated and its API server is healthy. Then explicitly enable the live marker:

```bash
WRIGHT_RIVET_LIVE_AI=1 uv run pytest -m rivet_live_ai tests/e2e/test_rivet_hermes_ai_live.py -v
```

The suite makes exactly one Rivet-shaped tool-call interaction and one Wright-chat MCP interaction. Without `WRIGHT_RIVET_LIVE_AI=1`, both skip and no subscription request is made.

## Merge gate

Before merging this feature branch to `dev`:

```bash
bash scripts/check-dev-merge.sh
```

Document any specific host-only limitation rather than silently skipping a gate.

## Implementation verification record

Executed on Windows on 2026-08-05 with Node.js and the project virtual
environment available. Every deterministic command above passed:

- bridge: 12 passed
- validation/runtime host: 7 passed
- MCP/gateway: 6 passed
- canvas component: 8 passed
- runner contract: 3 passed
- mocked Playwright: 12 passed across Chromium, Firefox, WebKit, and desktop
- wheel contents: 2 passed

The expected Vite future-config-loader warning appeared during the component
test; it is unrelated to this feature. No platform-specific test exception was
required.

The repository-wide dev merge gate was invoked on 2026-08-05 but did not reach
a terminal result within the bounded local invocation. Its named live
Playwright stage also requires ports 8000 and 5173 to be free; those ports are
intentionally occupied by the Wright API and Vite processes left running for
the user's feature test and captured canvas image. No merge is being performed.
Before a later merge to `dev`, stop those two test processes and rerun
`bash scripts/check-dev-merge.sh` without a timeout or skip.
