"""Local MCP transport to one authenticated prototype Wright API.

No executor, model client, generic HTTP proxy, credentials in tool results,
or automatic retries. The API's existing services own all workflow behavior.
"""

import argparse
import base64
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal
from importlib.metadata import version
from urllib.parse import quote, urlsplit
from uuid import uuid4
from pydantic import TypeAdapter, ValidationError
import anyio
from core.desktop_reasoning import (
    ENGINEERING_IMAGE_PROFILE,
    DesktopActionReply,
    DesktopReasoningRequest,
    DesktopHarnessBinding,
)
from core.process_validation import Identifier
from core.process_interactions import Reason

import httpx
from native_source_tools import WrightRequestRejected, register_native_source_tools
from desktop_backend import (
    FileUploadRequest, ConnectionControlRequest, LocalConnectionPreviewRequest,
    RecordedRunRequest,
)
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ImageContent, ToolAnnotations


def reasoning_images(request):
    from agent_adapters.desktop_reasoning import desktop_inline_image

    images = []
    for message in request.payload.get("messages", []):
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for index, part in enumerate(content):
            if isinstance(part, dict) and part.get("type") in {
                "image_url",
                "image",
                "input_image",
            }:
                if request.binding.image_input_profile not in {
                    "inline-png-jpeg-v1",
                    ENGINEERING_IMAGE_PROFILE,
                }:
                    raise ValueError("Image handoff profile unavailable")
                if part.get("type") != "image_url" or not isinstance(
                    part.get("image_url"), dict
                ):
                    raise ValueError("Unsupported image handoff shape")
                media, data = desktop_inline_image(
                    part["image_url"].get("url"),
                    profile=request.binding.image_input_profile,
                )
                images.append((content, index, media, data))
    return images


def task_presentation(item, workspace_id, session_id):
    request = DesktopReasoningRequest.model_validate_json(json.dumps(item["request"]))
    if (
        request.workspace_id != workspace_id
        or request.session_id != session_id
        or item["request_digest"] != request.digest
        or item["binding_digest"] != request.binding.digest
    ):
        raise ValueError("Pending request identity differs")
    # Parse a fresh copy: projection never changes the durable request or its digest.
    images = reasoning_images(request)
    references = []
    for ordinal, (content, index, media, data) in enumerate(images):
        reference = {
            "type": "image_reference",
            "image_index": ordinal,
            "media_type": media,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        content[index] = reference
        references.append(reference)
    if not references:
        return item
    return {
        **item,
        "request": request.model_dump(mode="json"),
        "image_references": references,
        "presentation": "image-reference projection; request_digest identifies the original durable request",
    }


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
    def __init__(self, state, *, native_editor=False, native_working_view=False):
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
        if bool(versions.get("native_working_view", False)) != native_working_view:
            raise ValueError(
                "Native working view differs from the frozen configuration"
            )
        for name, file in (
            ("native_source_tools", "native_source_tools.py"),
            ("native_editor", "native-editor.html"),
            ("native_process_tools", "native_process_tools.py"),
        ):
            if (
                (
                    native_working_view
                    and name == "native_process_tools"
                    and name not in versions["files"]
                )
                or name in versions["files"]
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
            reason = None
            process_detail = document.get("details", detail)
            if path.startswith("/api/workspace/process-interfaces/") and isinstance(
                process_detail, dict
            ):
                try:
                    # Only the owning process service's public, redacted contract;
                    # raw provider/HTTP diagnostics remain outside the panel.
                    reason = Reason.model_validate(process_detail.get("reason"))
                except ValidationError:
                    pass
            raise WrightRequestRejected(
                response.status_code,
                f"Wright rejected request ({response.status_code}): {detail}",
                reason=reason,
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


def server(client, *, native_editor=False, native_working_view=False):
    if native_working_view and not native_editor:
        raise ValueError("Native working view requires the native editor resource")

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

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_workspace_create(name: str) -> dict:
        """Create a fresh isolated Wright workspace bound to this desktop connection."""
        return await client.call("POST", "/api/desktop/workspaces", json={"name": name})

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_workspace_list() -> dict[str, Any]:
        """Find this connection's Wright workspaces without activating or rebinding sessions."""
        return await client.call("GET", "/api/desktop/workspaces")

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_connections_list(
        workspace_id: str, session_id: str, search: str = "", cursor: str | None = None
    ) -> dict[str, Any]:
        """Inspect the existing MCP catalog and this workspace's membership. Does not connect or grant tools."""
        from tool_registry.capability_models import CapabilityList

        await client.scope(workspace_id, session_id)
        params = {"search": search, "limit": 50}
        if cursor is not None:
            params["cursor"] = cursor
        catalog = CapabilityList.model_validate(
            await client.call("GET", "/api/mcp/capabilities", params=params)
        )
        return {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "snapshot": catalog.snapshot.model_dump(mode="json"),
            "next_cursor": catalog.next_cursor,
            "total": catalog.total,
            "connections": [
                {
                    "capability_id": item.capability_id,
                    "name": item.name,
                    "description": item.description,
                    "compatibility": item.compatibility.model_dump(mode="json"),
                    "local_validation": (
                        {
                            key: item.local_validation.get(key)
                            for key in (
                                "evidence_id",
                                "state",
                                "observed_at",
                                "reason_codes",
                            )
                        }
                        if item.local_validation is not None
                        else None
                    ),
                    "installed": item.user_state.installed,
                    "active": item.user_state.active,
                    "process_status": item.user_state.process_status,
                    "installed_version": item.user_state.installed_version,
                    "enabled_here": any(
                        scope.get("workspace_id") == workspace_id
                        for scope in item.user_state.enabled_workspaces
                    ),
                    "server_id": item.user_state.server_id,
                    "credentials_missing": any(
                        not configured
                        for configured in item.user_state.credentials_configured.values()
                    ),
                }
                for item in catalog.capabilities
            ],
        }

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_workspace_files(
        workspace_id: str, session_id: str
    ) -> dict[str, Any]:
        """Browse scoped workspace file metadata without reading contents or running files."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            f"/api/desktop/workspaces/{workspace_id}/files",
            params={"session_id": session_id},
        )

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_workspace_file_preview(
        workspace_id: str, session_id: str, path: str
    ) -> dict[str, Any]:
        """Read a bounded workspace text preview. Never executes or edits the file."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            f"/api/desktop/workspaces/{workspace_id}/file-preview",
            params={"session_id": session_id, "path": path},
        )

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_workspace_file_download(
        workspace_id: str, session_id: str, path: str
    ) -> dict[str, Any]:
        """Read exact bounded current-file bytes for an explicit UI download."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            f"/api/desktop/workspaces/{workspace_id}/file-download",
            params={"session_id": session_id, "path": path},
        )

    @mcp.tool(
        annotations=write, structured_output=True, meta={"ui": {"visibility": ["app"]}}
    )
    async def wright_workspace_file_upload(
        request: FileUploadRequest,
    ) -> dict[str, Any]:
        """Stage an explicitly selected input file. No workflow, tool, trust or overwrite authority."""
        try:
            await client.scope(request.workspace_id, request.session_id)
            document = await client.call(
                "POST",
                "/api/desktop/files/upload",
                json=request.model_dump(mode="json"),
            )
        except WrightRequestRejected as failure:
            known = failure.status_code in (400, 401, 403, 404, 409, 422)
            return {
                "ok": False,
                "error": {
                    "outcome_known": known,
                    "message": "Upload was rejected. Check workspace access, file size and filename."
                    if known
                    else "Upload outcome is unconfirmed. Check the saved upload before another attempt.",
                },
            }
        return {"ok": True, "document": document}

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_controls(
        workspace_id: str, session_id: str, capability_id: str, server_id: str
    ) -> dict:
        """Read registered provider/tool state. Shared controls are distinct from workspace grants."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            "/api/desktop/connection-controls",
            params={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "capability_id": capability_id,
                "server_id": server_id,
            },
        )

    @mcp.tool(
        annotations=write, structured_output=True, meta={"ui": {"visibility": ["app"]}}
    )
    async def wright_connection_control(
        request: ConnectionControlRequest,
    ) -> dict[str, Any]:
        """Apply one operator-selected shared provider/tool state change through its existing owner."""
        try:
            await client.scope(request.workspace_id, request.session_id)
            document = await client.call(
                "POST",
                "/api/desktop/connection-controls",
                json=request.model_dump(mode="json", exclude_none=True),
            )
        except WrightRequestRejected as failure:
            known = failure.status_code in (400, 401, 403, 404, 409, 422)
            return {
                "ok": False,
                "error": {
                    "outcome_known": known,
                    "message": "Shared control was rejected. Refresh its current subject and check operator access."
                    if known
                    else "Shared control outcome is not confirmed. Read current provider state before another action.",
                },
            }
        return {"ok": True, "document": document}

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_plan(
        workspace_id: str,
        session_id: str,
        capability_id: str,
        independently_completed_license: bool = False,
    ) -> dict[str, Any]:
        """Prepare a reviewable catalog setup plan. Does not approve, install, authenticate or grant tools."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-plans",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "capability_id": capability_id,
                "independently_completed_license": independently_completed_license,
            },
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_preview(
        workspace_id: str, session_id: str, name: str, url: str
    ) -> dict[str, Any]:
        """Preview a public HTTPS MCP endpoint; no credentials, query or fragment. Does not connect or install."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-imports/preview",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "name": name,
                "url": url,
            },
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_command_preview(
        request: LocalConnectionPreviewRequest,
    ) -> dict[str, Any]:
        """Preview a literal command on the Wright host; no execution, installation, environment or credentials."""
        await client.scope(request.workspace_id, request.session_id)
        return await client.call(
            "POST", "/api/desktop/connection-imports/preview",
            json=request.model_dump(),
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_import_plan(
        workspace_id: str,
        session_id: str,
        preview_token: str,
        draft_id: str,
        draft_digest: str,
        independently_completed_license: bool = False,
    ) -> dict[str, Any]:
        """Save a workspace setup plan from the exact preview. Never approves, installs or grants tools."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-imports/plan",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "preview_token": preview_token,
                "draft_id": draft_id,
                "draft_digest": draft_digest,
                "independently_completed_license": independently_completed_license,
            },
        )

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_plans(
        workspace_id: str, session_id: str, capability_id: str | None = None
    ) -> dict[str, Any]:
        """Find saved setup plans for this workspace, optionally filtered by provider without creating or resuming setup."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            "/api/desktop/connection-plans",
            params={
                "workspace_id": workspace_id,
                "session_id": session_id,
                **(
                    {"capability_id": capability_id}
                    if capability_id is not None
                    else {}
                ),
            },
        )

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_plan_read(
        workspace_id: str, session_id: str, plan_id: str
    ) -> dict[str, Any]:
        """Read the exact saved setup plan without approving or applying it."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "GET",
            "/api/desktop/connection-plans/" + quote(plan_id, safe=""),
            params={"workspace_id": workspace_id, "session_id": session_id},
        )

    @mcp.tool(
        annotations=read, structured_output=False, meta={"ui": {"visibility": ["app"]}}
    )
    async def wright_connection_signin(
        workspace_id: str, session_id: str, plan_id: str
    ) -> CallToolResult:
        """Read operator sign-in presentation. Transient links are app-private, never model content."""
        await client.scope(workspace_id, session_id)
        data = await client.call(
            "GET",
            "/api/desktop/connection-plans/" + quote(plan_id, safe="") + "/signin",
            params={"workspace_id": workspace_id, "session_id": session_id},
        )
        public = {
            key: data[key]
            for key in ("workspace_id", "session_id", "plan_id", "presentation")
        }
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Operator sign-in status read. No login was started.",
                )
            ],
            structuredContent=public,
            _meta={
                "wright/signin": {
                    "authorization_url": data.get("authorization_url"),
                    "callback_uri": data.get("callback_uri"),
                }
            },
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_validate(
        workspace_id: str, session_id: str, plan_id: str, plan_digest: str
    ) -> dict[str, Any]:
        """Explicit operator protocol validation of installed setup; may await sign-in, never grants workflow tools."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-plans/" + quote(plan_id, safe="") + "/validate",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "plan_digest": plan_digest,
            },
            timeout=360,
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_enable(
        workspace_id: str, session_id: str, plan_id: str, plan_digest: str
    ) -> dict[str, Any]:
        """Explicit operator workspace enablement; owner requires current validation, never approves invocation."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-plans/" + quote(plan_id, safe="") + "/enable",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "plan_digest": plan_digest,
            },
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_disable(
        workspace_id: str, session_id: str, capability_id: str, server_id: str
    ) -> dict[str, Any]:
        """Explicit operator removal from this workspace; no provider uninstall or invocation grant."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connections/disable",
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "capability_id": capability_id,
                "server_id": server_id,
            },
        )

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["app"]}})
    async def wright_connection_plan_update(
        workspace_id: str,
        session_id: str,
        plan_id: str,
        plan_digest: str,
        operation: Literal["approve", "apply"],
    ) -> dict[str, Any]:
        """Explicit operator setup approval/application against a reviewed plan digest; never a workflow grant."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/desktop/connection-plans/"
            + quote(plan_id, safe="")
            + "/"
            + operation,
            json={
                "workspace_id": workspace_id,
                "session_id": session_id,
                "plan_digest": plan_digest,
            },
        )

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

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["model", "app"]}})
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

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_workflow_templates(workspace_id: str, session_id: str) -> dict:
        """List existing engineering templates with their actual readiness; never grant or run tools."""
        await client.scope(workspace_id, session_id)
        return await client.call("GET", "/api/workspace/workflow-source-templates")

    @mcp.tool(annotations=write, meta={"ui": {"visibility": ["model", "app"]}})
    async def wright_workflow_template_create(
        workspace_id: str,
        session_id: str,
        template_id: str,
        template_version: str,
        expected_source_digest: str,
        workflow_path: str,
        request_id: str,
    ) -> dict:
        """Create an editable copy through the versioned template owner; not execution or a tool grant."""
        await client.scope(workspace_id, session_id)
        return await client.call(
            "POST",
            "/api/workspace/workflow-source-templates/"
            + quote(template_id, safe="")
            + "/instances",
            json={
                "session_id": session_id,
                "template_version": template_version,
                "expected_source_digest": expected_source_digest,
                "workflow_path": workflow_path,
                "request_id": request_id,
            },
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

    @mcp.tool(annotations=read, structured_output=True)
    async def wright_workflow_history(
        workspace_id: str, session_id: str, path: str
    ) -> dict[str, Any]:
        """Read recent recorded runs for one exact workflow; never start or resume work."""
        await client.scope(workspace_id, session_id)
        document = await client.call(
            "GET",
            "/api/workspace/workflow-sources/runs",
            params={"session_id": session_id, "path": path},
        )
        if (
            document.get("workspace_id") != workspace_id
            or document.get("workflow_path") != path
            or not isinstance(document.get("runs"), list)
            or len(document["runs"]) > 20
        ):
            raise ValueError("Run history scope or bound differs")
        # Home needs recorder identities and state, not embedded result payloads.
        fields = (
            "run_id",
            "path",
            "status",
            "started_at",
            "completed_at",
            "source_digest",
        )
        if any(not isinstance(row, dict) for row in document["runs"]):
            raise ValueError("Run history record is unavailable")
        return {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "workflow_path": path,
            "runs": [{key: row.get(key) for key in fields} for row in document["runs"]],
        }

    @mcp.tool(annotations=read, meta={"ui": {"visibility": ["app"]}})
    async def wright_recorded_run_read(request: RecordedRunRequest) -> dict[str, Any]:
        """Read exact saved run evidence, including older source revisions. Never resumes, reviews or executes."""
        await client.scope(request.workspace_id, request.session_id)
        return await client.call(
            "POST", "/api/desktop/run-records/read", json=request.model_dump(),
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
        return {
            "tasks": [
                task_presentation(item, workspace_id, session_id) for item in items
            ]
        }

    @mcp.tool(annotations=read, structured_output=False)
    async def wright_reasoning_image(
        workspace_id: str,
        session_id: str,
        request_id: str,
        request_digest: str,
        binding_digest: str,
        image_index: int,
    ) -> CallToolResult:
        """Read one exact pending task image as MCP image content; never answer or execute a task."""
        await client.scope(workspace_id, session_id)
        items = await client.call(
            "GET",
            "/api/desktop/reasoning",
            params={"workspace_id": workspace_id, "session_id": session_id},
        )
        matches = [
            item
            for item in items
            if item.get("request", {}).get("request_id") == request_id
        ]
        if len(matches) != 1:
            raise ValueError("Exact pending request unavailable")
        item = matches[0]
        task_presentation(item, workspace_id, session_id)
        request = DesktopReasoningRequest.model_validate_json(
            json.dumps(item["request"])
        )
        if request.binding != DesktopHarnessBinding.model_validate(client.binding):
            raise ValueError("Pending image belongs to another frozen connection")
        if request.digest != request_digest or request.binding.digest != binding_digest:
            raise ValueError("Frozen image request identity differs")
        images = reasoning_images(request)
        if type(image_index) is not int or not 0 <= image_index < len(images):
            raise ValueError("Exact image index unavailable")
        _, _, media, data = images[image_index]
        identity = {
            "request_id": request_id,
            "request_digest": request_digest,
            "binding_digest": binding_digest,
            "image_index": image_index,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "media_type": media,
        }
        return CallToolResult(
            content=[
                TextContent(type="text", text=json.dumps(identity)),
                ImageContent(
                    type="image",
                    mimeType=media,
                    data=base64.b64encode(data).decode("ascii"),
                ),
            ],
            structuredContent=identity,
        )

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
            title="Open Wright",
            annotations=read,
            meta={"ui": {"resourceUri": uri, "visibility": ["model", "app"]}},
        )
        async def wright_home(
            workspace_id: str | None = None, session_id: str | None = None,
        ) -> dict[str, Any]:
            """Open Wright beside this conversation, optionally returning to its exact workspace/session. Read only."""
            if (workspace_id is None) != (session_id is None):
                raise ValueError("Provide the workspace and its session together")
            selection = None
            if workspace_id is not None:
                await client.scope(workspace_id, session_id)
                selection = {"workspace_id": workspace_id, "session_id": session_id}
            return {
                "view": "home",
                **({"selection": selection} if selection is not None else {}),
                **await client.call("GET", "/api/desktop/workspaces"),
            }

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
            return {
                "workspace": workspace,
                "document": document,
                "working_view_enabled": native_working_view,
            }

        register_native_source_tools(mcp, client)
        if native_working_view:
            from native_process_tools import register_native_process_tools

            register_native_process_tools(mcp, client, resource_uri=uri)
    return mcp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--native-editor", action="store_true")
    parser.add_argument("--native-working-view", action="store_true")
    args = parser.parse_args()
    if args.native_working_view and not args.native_editor:
        parser.error("Native working view requires the opt-in native editor")
    server(
        WrightDesktopClient(
            args.state_dir,
            native_editor=args.native_editor,
            native_working_view=args.native_working_view,
        ),
        native_editor=args.native_editor,
        native_working_view=args.native_working_view,
    ).run(transport="stdio")
