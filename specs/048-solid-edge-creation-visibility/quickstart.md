# Quickstart: Solid Edge Production-Test Stabilization

## 1. Fast contract rehearsal

Use fake agent/lifecycle/provider adapters. No real Solid Edge process,
credentials, Docker, or external installation is needed for this tier.

```powershell
uv run pytest -q `
  packages/tool_registry/tests/test_gateway_policy.py `
  packages/tool_registry/tests/test_gateway_service.py `
  packages/tool_registry/tests/test_lifecycle_adapters.py `
  packages/workspace_service/tests/test_agent_sync.py `
  apps/api/tests/test_agent_stream_progress.py `
  apps/api/tests/test_config.py `
  apps/api/tests/test_gateway_api.py `
  apps/api/tests/test_hermes_sync.py `
  apps/api/tests/test_logging_config.py `
  apps/api/tests/test_workspace_api.py
```

Expected evidence:

- Solid Edge inspection and inventory tools are absent and denied;
- planning is the first event and elapsed heartbeats continue during delay;
- a completed tool does not produce a misleading creation heartbeat;
- external ownership produces no API lifecycle calls;
- workspace rebinding is serialized and failure is actionable; and
- protected bridge requests preserve authentication.

## 2. Hermes bridge rehearsal

Reinstall the local plugin before testing because its wheel uses force-included top-level sources:

```powershell
uv run --project hermes-plugin-wright --reinstall-package hermes-plugin-wright `
  pytest -q hermes-plugin-wright/tests/test_bridge.py
```

Verify that protected Wright requests carry the bearer header and that missing authentication fails without logging the token.

## 3. Local Windows live prerequisites

This operator-invoked tier requires:

- Solid Edge already installed and licensed on the Windows workstation;
- the reviewed local SolidEdgeMCP executable;
- `CADMCP_SOLID_EDGE_ALLOWED_ROOTS` including the selected Wright workspace output directory;
- one configured runtime owner (`external` for Hermes-driven testing);
- Wright API and Hermes using existing local authentication;
- a unique output directory under the active workspace, such as `outputs/solid-edge-smoke/<run-id>/`.

Do not install Solid Edge or SolidEdgeMCP into the Wright base image. Do not update catalog validation status from this live run.

## 4. Blank-session live smoke

1. Start Solid Edge with no active document.
2. Record the owner and SolidEdgeMCP child-process count.
3. Submit a request to create a new 20 mm x 20 mm x 10 mm part at a unique `.par` path.
4. Observe the immediate planning event and phase/elapsed updates.
5. Verify one `cad.create_part_from_recipe` call, zero inspection calls, and no heartbeat gap over 10 seconds.
6. Verify the requested file exists and the new part remains open and visible.
7. Capture the redacted diagnostic summary and timing attribution.

## 5. Pre-existing-document isolation smoke

1. Open a known sacrificial pre-existing part in Solid Edge and record its identity and saved hash outside the agent-visible production tool surface.
2. Submit the same fresh creation request to a different unique output path.
3. Verify a second new document becomes visible/open.
4. Verify the pre-existing document identity, contents/hash, open state, and saved path are unchanged.
5. Verify the agent audit still contains one creation call and zero document/geometry inspection calls.

## 6. Failure and reconnect smokes

Run separate cases for:

- output path outside the workspace;
- existing output without overwrite authorization;
- invalid direction or recipe;
- Solid Edge unavailable during creation;
- stream disconnect during an intentionally delayed phase followed by `GET /api/agent/chat/stream?session_id=<id>&after=<index>`;
- repeated passive UI polling while Hermes owns the child.

Each failure must be actionable, terminal, and free of inspection/recovery calls. Reconnect must replay progress, result/error, and completion in order. Polling must leave the child-process count at one.

## 7. Deferred performance evidence

The original draft proposed at least 20 bounded simple-part trials. That
percentage-based evidence is follow-up work and is not claimed by this merge.
When the follow-up is scheduled, record per trial:

- first-status latency;
- geometry-start latency;
- total duration;
- call count and tool names;
- artifact path and visible/open result;
- subprocess count;
- phase totals and attribution ratio.

Preserve redacted evidence under
`test-results/solid-edge-creation-visibility/`; generated outputs and evidence
scratch data remain ignored and are not release artifacts.

## 8. Repository gates

Run focused format/type/tests first, then the authoritative merge gate:

```powershell
uv run ruff check apps/api packages hermes-plugin-wright
uv run ruff format --check apps/api packages hermes-plugin-wright
uv run pytest -q
& 'D:\Program Files\Git\bin\bash.exe' scripts/check-dev-merge.sh
```

Before any later merge to `dev`, the merge gate must pass or the exact local host limitation must be documented as required by `AGENTS.md`.
