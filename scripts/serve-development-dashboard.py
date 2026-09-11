"""Add compiled progress charts to an existing loopback-only status dashboard."""

from __future__ import annotations

import argparse
import importlib.util
import sqlite3
import sys
from dashboard_collector import CollectorSupervisor
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--campaign-root", type=Path)
    parser.add_argument("--campaign-module", type=Path)
    parser.add_argument("--collector-config", type=Path)
    args = parser.parse_args()
    # Read a checkpoint using one checkout's package versions. Mixing editable
    # packages from the launcher's checkout breaks native schema imports.
    for package in sorted((args.repo / "packages").glob("*/src")):
        sys.path.insert(0, str(package.resolve()))
    source = Path(__file__).resolve().parents[1]
    metrics = load_module(
        "observational_metrics",
        source / "packages/tool_registry/src/tool_registry/development_metrics.py",
    )
    legacy = load_module("existing_dashboard", args.legacy_root / "server.py")
    legacy.CONTINUATION_REPO = args.repo.resolve()
    assets = args.assets.resolve(strict=True)
    if not (assets / "development-metrics.html").is_file():
        raise SystemExit("Build dashboard assets first")
    store = metrics.DevelopmentMetrics(args.data_root / "program-status")
    campaign = load_module('workflow_campaign_dashboard', args.campaign_module) if args.campaign_module else None

    supervisor = CollectorSupervisor(args.collector_config, source, args.data_root) if args.collector_config else None
    if supervisor:
        supervisor.thread.start()

    class Handler(legacy.Handler):
        def do_GET(self):
            route = urlparse(self.path).path
            if route == '/api/workflow-campaign' and campaign and args.campaign_root:
                try: self.send_json(campaign.read_campaign(args.campaign_root))
                except (OSError, ValueError): self.send_json({'error':'Campaign evidence unavailable'},503)
                return
            if route == "/api/development-health":
                try:
                    self.send_json(supervisor.health(store.read()["events"]) if supervisor else {"status": "unconfigured"})
                except (OSError, ValueError, sqlite3.Error):
                    self.send_json({"status": "unavailable"}, 503)
                return
            if route == "/api/program-status/metrics":
                try:
                    self.send_json(store.read())
                except (OSError, ValueError, sqlite3.Error):
                    self.send_json({"error": "Metrics unavailable"}, 503)
                return
            if route.startswith("/metrics/"):
                target = (assets / unquote(route.removeprefix("/metrics/"))).resolve()
                if not target.is_relative_to(assets) or not target.is_file():
                    self.send_error(404)
                else:
                    self.send_file(target)
                return
            if route in {"", "/", "/index.html"}:
                html = (args.legacy_root / "index.html").read_text(encoding="utf-8")
                html = html.replace("`Live · ${new Date(data.observedAt).toLocaleTimeString()}`", "`Historical status served · ${new Date(data.observedAt).toLocaleTimeString()}`")
                embed = """<aside id="development-health" style="padding:16px;border:1px solid #456" role="status">Checking development collector…</aside>
<script>
async function refreshDevelopmentHealth(){
 const box=document.getElementById('development-health');
 try {const r=await fetch('/api/development-health',{cache:'no-store'});if(!r.ok)throw Error();const d=await r.json();
 box.replaceChildren();
 for(const text of ['Development collection: '+d.status,'Active checkout: '+(d.repository||'unknown'),'Last collection: '+(d.lastCollectedAt?new Date(d.lastCollectedAt).toLocaleString():'unknown'),...(d.sources||[]).map(s=>s.path+': '+(s.modifiedAt?new Date(s.modifiedAt).toLocaleString():'missing')),d.note||'']){const p=document.createElement('div');p.textContent=text;box.appendChild(p);}
 box.style.borderColor=d.status==='current'?'#34d399':'#fb923c';
 }catch{box.textContent='Development collector status unavailable; displayed records may be stale';}
}
refreshDevelopmentHealth();setInterval(refreshDevelopmentHealth,15000);
</script>
<iframe id="development-metrics-frame" title="Development progress over time" src="/metrics/development-metrics.html" style="width:100%;height:1550px;border:0;display:block"></iframe>
<script>window.addEventListener('message',e=>{const f=document.getElementById('development-metrics-frame');if(e.origin===location.origin&&e.source===f.contentWindow&&e.data?.type==='wright-metrics-height'&&Number.isFinite(e.data.height)){f.style.height=Math.max(400,Math.min(10000,e.data.height))+'px';}});</script>"""
                if "</header>" not in html:
                    self.send_error(503)
                    return
                campaign_html = ''
                if campaign and args.campaign_root:
                    try: campaign_html = campaign.render_campaign(campaign.read_campaign(args.campaign_root))
                    except (OSError, ValueError): campaign_html = '<p>Workflow campaign evidence unavailable.</p>'
                body = html.replace("</header>", "</header>" + campaign_html + embed, 1).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

    Handler.cache = legacy.StatusCache(args.repo.resolve())
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    finally:
        if supervisor:
            supervisor.close()


if __name__ == "__main__":
    main()
