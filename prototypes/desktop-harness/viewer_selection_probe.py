"""Isolated file-dispatch probe; never reads or executes engineering workflows.

Run only as a disposable MCP server. Its three pinned paths are test fixtures,
not workspace documents. The host's file-open acknowledgement and the handler
invocation are separate observations; neither proves visible rendering.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

ROOT = Path("/tmp/wright-viewer-selection-20261031")
FILES = ("control.wflow", "control.workflow.wflow", "control.txt")
DIGEST = "d4a5d071fa2b48345310f7af4f71d7f90fe38b153dd83ba33f9214f8aa50af59"
LOG = ROOT / "handler-invocations.jsonl"
URI = "ui://wright/selection-probe/launcher-v1.html"
VIEWER = "ui://wright/selection-probe/viewer-v1.html"
EXTENSIONS = (
    [".wflow", ".workflow.wflow"]
    if os.getenv("WRIGHT_PROBE_BOTH") == "1"
    else [".wflow"]
)
server = FastMCP("wright-viewer-selection-probe")


class FileInput(BaseModel):
    name: str
    resourceUri: str


def fixtures():
    result = []
    for name in FILES:
        path = ROOT / name
        if (
            path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != DIGEST
        ):
            raise ValueError("Probe fixture missing or changed")
        result.append({"name": name, "path": str(path)})
    return result


LAUNCHER = """<!doctype html><meta charset="utf-8"><title>Viewer selection test</title>
<h2>Viewer selection test</h2><button id="open" disabled>Open three test files</button><p id="status">Connecting…</p>
<script>
let id=0, pending=new Map(), origin='*', files=[], ready=false;
function render(){document.getElementById('open').disabled=!(ready&&files.length===3);document.getElementById('status').textContent=ready&&files.length===3?'Ready':'Connecting…'}
function request(method,params){return new Promise((resolve,reject)=>{let n=++id;let t=setTimeout(()=>{pending.delete(n);reject(Error('timeout'))},10000);pending.set(n,{resolve,reject,t});parent.postMessage({jsonrpc:'2.0',id:n,method,params},origin)})}
window.addEventListener('message',e=>{if(e.source!==parent)return;const m=e.data;if(!m||m.jsonrpc!=='2.0')return;if(m.id&&pending.has(m.id)){const p=pending.get(m.id);clearTimeout(p.t);pending.delete(m.id);origin=e.origin;m.error?p.reject(Error('rejected')):p.resolve(m.result);return}if(m.method==='ui/notifications/tool-result'){files=m.params?.structuredContent?.files||[];render()}});
request('ui/initialize',{protocolVersion:'2026-01-26',appInfo:{name:'wright-selection-probe',version:'1'},appCapabilities:{}}).then(result=>{ready=!!result.hostCapabilities?.experimental?.['openai/files'];render();parent.postMessage({jsonrpc:'2.0',method:'ui/notifications/initialized',params:{}},origin)}).catch(()=>{document.getElementById('status').textContent='Host connection unavailable'});
document.getElementById('open').onclick=async()=>{const outcomes=[];for(const f of files){try{await request('openai/files/open',{path:f.path});outcomes.push(f.name+': acknowledged')}catch(e){outcomes.push(f.name+': not acknowledged')}document.getElementById('status').textContent=outcomes.join(' | ')}if(files.length!==3)document.getElementById('status').textContent='Fixture list unavailable';};
</script>"""


@server.resource(URI, mime_type="text/html;profile=mcp-app")
def launcher_resource():
    return LAUNCHER


@server.resource(VIEWER, mime_type="text/html;profile=mcp-app")
def viewer_resource():
    return "<!doctype html><title>Wright selection probe</title><h1>Wright test viewer</h1>"


@server.tool(
    structured_output=True,
    meta={
        "ui": {"resourceUri": URI, "visibility": ["model", "app"]},
        "openai/ui": {"entrypoints": [{"type": "thread"}]},
    },
)
def wright_selection_probe() -> dict[str, Any]:
    """Open three immutable disposable fixtures; no workflow execution."""
    return {"files": fixtures(), "registration": EXTENSIONS}


@server.tool(
    meta={
        "ui": {"resourceUri": VIEWER, "visibility": ["app"]},
        "openai/ui": {"entrypoints": [{"type": "file", "extensions": EXTENSIONS}]},
    }
)
def wright_selection_probe_file(file: FileInput) -> dict:
    """Record invocation only for the three exact probe names; never read host URIs."""
    if file.name not in FILES:
        raise ValueError("Not a selection probe fixture")
    fd = os.open(
        LOG,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.write(
            fd,
            (
                json.dumps({"event": "handler_invoked", "name": file.name}) + "\n"
            ).encode(),
        )
    finally:
        os.close(fd)
    return {
        "name": file.name,
        "message": "Test handler invoked; visible rendering requires observation.",
    }


if __name__ == "__main__":
    server.run(transport="stdio")
