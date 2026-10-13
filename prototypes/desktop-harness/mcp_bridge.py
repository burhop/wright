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
from typing import Any
from importlib.metadata import version
from urllib.parse import urlsplit
from uuid import uuid4
from pydantic import TypeAdapter
import anyio
from core.desktop_reasoning import DesktopActionReply
from core.process_validation import Identifier

import httpx
from native_source_tools import WrightRequestRejected, register_native_source_tools
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

WORKSPACE_PANEL_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wright Workflows</title><style>
:root{color-scheme:dark;--panel-bg:#202020;--panel-fg:#f0f0f0;--panel-muted:#aaa;--panel-line:#414141;--panel-font:system-ui}
*{box-sizing:border-box}body{margin:0;background:var(--panel-bg);color:var(--panel-fg);font:14px/1.5 var(--panel-font)}
main{max-width:760px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;gap:16px;align-items:center}
h1{font-size:21px;margin:0}h2{font-size:16px;margin:0 0 8px}p{margin:8px 0;color:var(--panel-muted)}
section{border:1px solid var(--panel-line);border-radius:10px;padding:18px;margin-top:18px}
button{background:transparent;color:inherit;font:inherit;border:1px solid var(--panel-line);border-radius:7px;padding:7px 12px;cursor:pointer}
button:disabled{opacity:.5;cursor:default}button:focus-visible{outline:2px solid currentColor;outline-offset:3px}
#state{font-size:12px}#notice{overflow-wrap:anywhere}small{color:var(--panel-muted)}
</style></head><body><main>
<header><h1>Workflows</h1><span id="state" role="status">Connecting to host…</span></header>
<p>Your Wright workspace, alongside this conversation.</p>
<section><h2 id="workspace">Choose a workspace</h2><p id="description">Ask this conversation to create or open a Wright workspace.</p></section>
<section><h2>Connection</h2><p id="connection">Waiting for Wright's recorded status.</p>
<small id="model">Desktop model identity is not independently attested.</small></section>
<p id="notice" role="status">Read-only panel prototype. Workflow editing opens in the qualified workspace view.</p>
<button id="refresh" disabled>Refresh status</button>
</main><script>
const byId=id=>document.getElementById(id);
let sequence=0, input={}, ready=false, origin='*';
const requests=new Map();
function request(method,params){return new Promise((resolve,reject)=>{
 const id=++sequence; const timer=setTimeout(()=>{requests.delete(id);reject(new Error('Host response unavailable. Your saved work is unchanged.'));},10000);
 requests.set(id,{resolve,reject,timer});parent.postMessage({jsonrpc:'2.0',id,method,params},origin);
});}
function theme(context){
 if(context?.theme==='light'||context?.theme==='dark')document.documentElement.style.colorScheme=context.theme;
 const vars=context?.styles?.variables||{};
 const mapping={'--color-background-primary':'--panel-bg','--color-text-primary':'--panel-fg','--color-text-secondary':'--panel-muted','--color-border-primary':'--panel-line','--font-sans':'--panel-font'};
 for(const [from,to] of Object.entries(mapping)){const value=vars[from];if(typeof value==='string'&&value.length<160&&!/[;{}@]|url\s*\(/i.test(value))document.documentElement.style.setProperty(to,value);}
}
function render(result){
 const data=result?.structuredContent;
 if(result?.isError||!data||typeof data.connection?.connected!=='boolean'){
  byId('notice').textContent='Wright status is unavailable. Reopen the panel or use the conversation; no action was repeated.';return;
 }
 byId('state').textContent=data.connection.connected?'Connected':'Disconnected';
 byId('connection').textContent=data.connection.connected?'Wright is connected. Workflow readiness is checked separately.':'The desktop connection is unavailable. Saved work remains in Wright.';
 byId('workspace').textContent=data.workspace?.workspace_name||'Choose a workspace';
 byId('description').textContent=data.workspace?'Use this conversation to open or create a workflow in this workspace.':'Ask this conversation to create or open a Wright workspace.';
 byId('model').textContent='Model identity: '+(data.connection.model_identity||'unreported; not independently attested');
 byId('notice').textContent='Read-only panel prototype. Workflow editing opens in the qualified workspace view.';
}
window.addEventListener('message',event=>{
 if(event.source!==parent||(origin!=='*'&&event.origin!==origin))return;
 const message=event.data;if(!message||message.jsonrpc!=='2.0')return;
 if(requests.has(message.id)){origin=event.origin==='null'?'*':event.origin;const pending=requests.get(message.id);clearTimeout(pending.timer);requests.delete(message.id);message.error?pending.reject(new Error('Host rejected the request.')):pending.resolve(message.result);return;}
 if(message.method==='ui/notifications/tool-input')input=message.params?.arguments||{};
 if(message.method==='ui/notifications/tool-result')render(message.params);
 if(message.method==='ui/notifications/host-context-changed')theme(message.params?.hostContext||message.params);
});
byId('refresh').addEventListener('click',async()=>{
 if(!ready)return;byId('refresh').disabled=true;
 try{render(await request('tools/call',{name:'wright_workspace_panel',arguments:input}));}
 catch(error){byId('notice').textContent=error.message;}
 finally{byId('refresh').disabled=false;}
});
request('ui/initialize',{appInfo:{name:'wright-workspace-panel',version:'0.1.0'},appCapabilities:{},protocolVersion:'2026-01-26'})
 .then(result=>{theme(result?.hostContext);ready=true;byId('refresh').disabled=false;parent.postMessage({jsonrpc:'2.0',method:'ui/notifications/initialized',params:{}},origin);})
 .catch(error=>{byId('state').textContent='Host unavailable';byId('notice').textContent=error.message;});
</script></body></html>"""
WORKSPACE_PANEL_URI = (
    "ui://wright/workspace/"
    + hashlib.sha256(WORKSPACE_PANEL_HTML.encode()).hexdigest()
    + ".html"
)


class WrightDesktopClient:
    def __init__(self, state, *, native_editor=False):
        self.state = Path(state).resolve(strict=True)
        preview = json.loads((self.state / "preview.json").read_text())
        url = preview["api_url"]
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path:
            raise ValueError("This prototype connects only to its loopback Wright API")
        self.binding = json.loads((self.state / "desktop-binding.json").read_text())
        versions = json.loads((self.state / "desktop-versions.json").read_text())
        if versions.get("mcp_sdk") != version("mcp"):
            raise ValueError(
                "Pinned MCP SDK version differs; requalify before connecting"
            )
        current_transport = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if versions["files"]["transport"] != current_transport:
            raise ValueError(
                "The pinned MCP bridge changed; requalify before connecting"
            )
        if bool(versions.get("native_editor", False)) != native_editor:
            raise ValueError(
                "Native editor capability differs from the frozen configuration"
            )
        for name, file in (
            ("native_source_tools", "native_source_tools.py"),
            ("native_editor", "native-editor.html"),
        ):
            if (
                name in versions["files"]
                and versions["files"][name]
                != hashlib.sha256(
                    Path(__file__).with_name(file).read_bytes()
                ).hexdigest()
            ):
                raise ValueError(
                    "Pinned native editor bytes changed; requalify before connecting"
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
            raise WrightRequestRejected(
                response.status_code,
                f"Wright rejected request ({response.status_code}): {detail}",
            )
        return response.json()

    async def scope(self, workspace_id, session_id):
        TypeAdapter(Identifier).validate_python(workspace_id)
        TypeAdapter(Identifier).validate_python(session_id)
        return await self.call(
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


def server(client, *, native_editor=False):
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

    @mcp.resource(
        WORKSPACE_PANEL_URI,
        title="Wright Workflows",
        mime_type="text/html;profile=mcp-app",
        meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
    )
    async def workspace_panel_resource() -> str:
        return WORKSPACE_PANEL_HTML

    @mcp.tool(
        title="Wright Workflows",
        annotations=read,
        structured_output=True,
        meta={
            "ui": {
                "resourceUri": WORKSPACE_PANEL_URI,
                "visibility": ["model", "app"],
            },
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    )
    async def wright_workspace_panel(
        workspace_id: str | None = None, session_id: str | None = None
    ) -> dict[str, Any]:
        """Open a read-only Wright panel for an exact workspace, or show connection status before selecting one."""
        if (workspace_id is None) != (session_id is None):
            raise ValueError("Provide the workspace and its session together")
        workspace = None
        if workspace_id is not None:
            workspace = await client.scope(workspace_id, session_id)
        return {
            "connection": await client.call("GET", "/api/desktop/connection"),
            "workspace": workspace,
        }

    @mcp.tool(annotations=read)
    async def wright_connection_status() -> dict:
        """Read connection readiness and honest model/tool qualification limits."""
        return await client.call("GET", "/api/desktop/connection")

    @mcp.tool(annotations=write)
    async def wright_workspace_create(name: str) -> dict:
        """Create a fresh isolated Wright workspace bound to this desktop connection."""
        return await client.call("POST", "/api/desktop/workspaces", json={"name": name})

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["model", "app"]}})
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

    if native_editor:
        html = Path(__file__).with_name("native-editor.html").read_text()
        uri = (
            "ui://wright/workflow/"
            + hashlib.sha256(html.encode()).hexdigest()
            + ".html"
        )

        @mcp.resource(
            uri,
            title="Wright workflow editor",
            mime_type="text/html;profile=mcp-app",
            meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
        )
        async def native_editor_resource() -> str:
            return html

        @mcp.tool(
            title="Open Wright workflow",
            annotations=read,
            structured_output=True,
            meta={
                "ui": {"resourceUri": uri, "visibility": ["model", "app"]},
                "openai/ui": {"entrypoints": [{"type": "thread"}]},
            },
        )
        async def wright_workflow_open(
            workspace_id: str, session_id: str, path: str
        ) -> dict[str, Any]:
            """Open the shared editor for an exact saved workflow. This operation only reads."""
            workspace = await client.scope(workspace_id, session_id)
            document = await client.call(
                "GET",
                "/api/workspace/workflow-sources",
                params={"session_id": session_id, "path": path},
            )
            return {"workspace": workspace, "document": document}

        register_native_source_tools(mcp, client)
    return mcp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--native-editor", action="store_true")
    args = parser.parse_args()
    server(
        WrightDesktopClient(args.state_dir, native_editor=args.native_editor),
        native_editor=args.native_editor,
    ).run(transport="stdio")
