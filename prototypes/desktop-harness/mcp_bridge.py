"""Local MCP transport to one authenticated prototype Wright API.

No executor, model client, generic HTTP proxy, credentials in tool results,
or automatic retries. The API's existing services own all workflow behavior.
"""

import argparse
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4
from pydantic import TypeAdapter
import anyio
from core.desktop_reasoning import DesktopActionReply
from core.process_validation import Identifier

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


class WrightDesktopClient:
    def __init__(self, state):
        self.state = Path(state).resolve(strict=True)
        preview = json.loads((self.state / "preview.json").read_text())
        url = preview["api_url"]
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path:
            raise ValueError("This prototype connects only to its loopback Wright API")
        self.binding = json.loads((self.state / "desktop-binding.json").read_text())
        versions = json.loads((self.state / "desktop-versions.json").read_text())
        current_transport = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if versions["files"]["transport"] != current_transport:
            raise ValueError(
                "The pinned MCP bridge changed; requalify before connecting"
            )
        self.client_id = str(uuid4())
        token_file = self.state / ".preview-api-token"
        if token_file.is_symlink() or token_file.stat().st_mode & 0o077:
            raise ValueError(
                "Prototype API credential must be private and not a symlink"
            )
        self.http = httpx.AsyncClient(
            base_url=url,
            headers={"Authorization": "Bearer " + token_file.read_text()},
            trust_env=False,
            follow_redirects=False,
            timeout=15,
        )

    async def call(self, method, path, **options):
        try:
            response = await self.http.request(method, path, **options)
        except httpx.HTTPError as error:
            raise RuntimeError(
                "Wright transport stopped; a write outcome may be uncertain. Reconcile before retrying."
            ) from error
        if "application/json" not in response.headers.get("content-type", ""):
            raise RuntimeError(
                "Wright returned a non-JSON response; reconcile this request instead of retrying a write."
            )
        if not response.is_success:
            document = response.json()
            detail = document.get(
                "detail", document.get("message", "Wright rejected this request")
            )
            raise ValueError(
                f"Wright rejected request ({response.status_code}): {detail}"
            )
        return response.json()

    async def scope(self, workspace_id, session_id):
        TypeAdapter(Identifier).validate_python(workspace_id)
        TypeAdapter(Identifier).validate_python(session_id)
        await self.call(
            "GET",
            "/api/desktop/workspaces/" + workspace_id,
            params={"session_id": session_id},
        )


@asynccontextmanager
async def connection_lifespan(client):
    payload = {"client_id": client.client_id, "binding": client.binding}
    established = False
    try:
        receipt = await client.call("POST", "/api/desktop/connect", json=payload)
        established = True
        interval = receipt.get("heartbeat_interval_seconds")
        lease = receipt.get("connection_lease_seconds")
        if (
            type(interval) is not int
            or type(lease) is not int
            or not 0 < interval < lease <= 60
        ):
            raise ValueError(
                "Wright returned an invalid connection lease; no lifecycle defaults were substituted"
            )

        async def pulse():
            while True:
                await anyio.sleep(interval)
                await client.call("POST", "/api/desktop/heartbeat", json=payload)

        async with anyio.create_task_group() as group:
            group.start_soon(pulse)
            try:
                yield {}
            finally:
                group.cancel_scope.cancel()
    finally:
        with anyio.CancelScope(shield=True):
            try:
                if established:
                    await client.call("POST", "/api/desktop/disconnect", json=payload)
            finally:
                await client.http.aclose()


def server(client):
    @asynccontextmanager
    async def lifespan(_):
        async with connection_lifespan(client):
            yield {}

    mcp = FastMCP("wright-desktop-prototype", lifespan=lifespan)
    read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )

    @mcp.tool(annotations=read)
    async def wright_connection_status() -> dict:
        """Read connection readiness and honest model/tool qualification limits."""
        return await client.call("GET", "/api/desktop/connection")

    @mcp.tool(annotations=write)
    async def wright_workspace_create(name: str) -> dict:
        """Create a fresh isolated Wright workspace bound to this desktop connection."""
        return await client.call("POST", "/api/desktop/workspaces", json={"name": name})

    @mcp.tool(annotations=read)
    async def wright_workflow_read(
        workspace_id: str, session_id: str, path: str
    ) -> dict:
        """Read exact saved workflow source and its revision/digest."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            "/api/workspace/workflow-sources",
            params={"session_id": session_id, "path": path},
        )

    @mcp.tool(annotations=write)
    async def wright_workflow_create(
        workspace_id: str, session_id: str, path: str, source: str
    ) -> dict:
        """Save new workflow source through Wright; readiness remains a separate check."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/workspace/workflow-sources",
            json={"session_id": session_id, "path": path, "source": source},
        )

    @mcp.tool(annotations=write)
    async def wright_process_prepare(
        workspace_id: str,
        session_id: str,
        path: str,
        source_digest: str,
        bindings: list[dict],
    ) -> dict:
        """Freeze supplied process inputs through the existing Wright preparation owner."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/workspace/process-interfaces/inputs",
            json={
                "session_id": session_id,
                "path": path,
                "expected_storage_digest": source_digest,
                "bindings": bindings,
            },
        )

    @mcp.tool(annotations=write)
    async def wright_process_start(
        workspace_id: str,
        session_id: str,
        path: str,
        source_digest: str,
        input_snapshot_id: str,
        input_digest: str,
        request_id: str,
        integration_policy_digest: str | None = None,
    ) -> dict:
        """Start once through Wright's durable supervisor; inspect the receipt before any retry."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/workspace/process-interfaces/runs",
            json={
                "session_id": session_id,
                "path": path,
                "expected_storage_digest": source_digest,
                "input_snapshot_id": input_snapshot_id,
                "expected_input_digest": input_digest,
                "request_id": request_id,
                "integration_policy_digest": integration_policy_digest,
            },
        )

    @mcp.tool(annotations=read)
    async def wright_process_read(
        workspace_id: str, session_id: str, path: str, source_digest: str, run_id: str
    ) -> dict:
        """Read this exact durable run's state, results and pending interactions."""
        await client.scope(workspace_id, session_id)
        TypeAdapter(Identifier).validate_python(run_id)
        return await client.call(
            "GET",
            "/api/workspace/process-interfaces/runs/" + run_id,
            params={
                "session_id": session_id,
                "path": path,
                "expected_storage_digest": source_digest,
            },
        )

    @mcp.tool(annotations=write)
    async def wright_process_respond(
        workspace_id: str,
        session_id: str,
        path: str,
        source_digest: str,
        checkpoint_id: str,
        subject_digest: str,
        value: dict,
        request_id: str,
    ) -> dict:
        """Answer a declared input checkpoint and request its qualified same-run continuation."""
        await client.scope(workspace_id, session_id)
        TypeAdapter(Identifier).validate_python(checkpoint_id)
        return await client.call(
            "POST",
            f"/api/workspace/process-interfaces/interactions/{checkpoint_id}/response",
            json={
                "session_id": session_id,
                "path": path,
                "expected_storage_digest": source_digest,
                "subject_digest": subject_digest,
                "value": value,
                "request_id": request_id,
            },
        )

    @mcp.tool(annotations=write)
    async def wright_process_cancel(
        workspace_id: str,
        session_id: str,
        path: str,
        source_digest: str,
        run_id: str,
        request_id: str,
    ) -> dict:
        """Request cancellation through Wright; the receipt distinguishes uncertain effects."""
        await client.scope(workspace_id, session_id)
        TypeAdapter(Identifier).validate_python(run_id)
        return await client.call(
            "POST",
            f"/api/workspace/process-interfaces/runs/{run_id}/cancel",
            json={
                "session_id": session_id,
                "path": path,
                "expected_storage_digest": source_digest,
                "request_id": request_id,
            },
        )

    @mcp.tool(annotations=read)
    async def wright_reasoning_pending(workspace_id: str, session_id: str) -> dict:
        """Read bounded tasks for this workspace. Use their exact saved instructions and schemas."""
        await client.scope(workspace_id, session_id)
        items = await client.call(
            "GET",
            "/api/desktop/reasoning",
            params={"workspace_id": workspace_id, "session_id": session_id},
        )
        return {"tasks": items}

    @mcp.tool(annotations=write)
    async def wright_reasoning_answer(
        workspace_id: str,
        session_id: str,
        request_id: str,
        request_digest: str,
        binding_digest: str,
        response_id: str,
        reply: str,
    ) -> dict:
        """Submit the exact unattended-step JSON as text, without executing tools."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/reasoning/respond",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "response": {
                    "request_id": request_id,
                    "request_digest": request_digest,
                    "binding_digest": binding_digest,
                    "response_id": response_id,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "reply": reply,
                },
            },
        )

    @mcp.tool(annotations=write)
    async def wright_reasoning_action(
        workspace_id: str,
        session_id: str,
        request_id: str,
        request_digest: str,
        binding_digest: str,
        response_id: str,
        decision: DesktopActionReply,
    ) -> dict:
        """Return a bounded action-task decision for Wright to validate and execute.

        This submits an assistant envelope, not a gateway call or permission.
        Use the task's exact advertised tool schema and saved instructions.
        """
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/reasoning/respond",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "response": {
                    "request_id": request_id,
                    "request_digest": request_digest,
                    "binding_digest": binding_digest,
                    "response_id": response_id,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "reply": decision.model_dump(mode="json"),
                },
            },
        )

    return mcp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    server(WrightDesktopClient(args.state_dir)).run(transport="stdio")
