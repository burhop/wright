"""Installed, read-only static bundle runtime for Wright-managed process UIs.

Only the surface owner launches this fixed module with a verified vault identity.
It serves no source, manifest, workspace file, process command or user-selected
path. The reserved process bridge belongs to the authenticated preview proxy.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from urllib.parse import urlsplit

from data_vault.process_ui_artifacts import ImmutableFileSet


STATIC_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' blob:; font-src 'self'; connect-src 'self'; "
    "worker-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
)
_TYPES = {
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_INDEX = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="referrer" content="no-referrer"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wright process interface</title><link rel="stylesheet" href="/style.css">
</head><body><p id="wright-process-connection" role="status">Connecting to Wright...</p>
<main id="wright-process-ui" aria-live="polite">Opening process interface...</main>
<script type="module" src="/wright-runtime.js"></script></body></html>"""

# The presentation-bound client factory is part of the fixed compiled host entry,
# never model source. Bridge context and permission are derived on the server.
_RUNTIME = b"""const root = document.getElementById('wright-process-ui');
const connection = document.getElementById('wright-process-connection');
const observer = new AbortController();
let dispose, context, host, mounted = false;
const themeKeys = new Set(['--color-neutral','--color-surface','--color-surface-elevated','--color-surface-subtle',
  '--color-primary','--color-secondary','--color-accent','--color-border','--color-success','--color-warning',
  '--color-error','--color-text-muted','--font-size-md','--space-md','--space-lg','--radius-md']);
const signalHost = (type, extra = {}) => {
  if (!host || !context) throw new Error('The Wright workspace connection is unavailable.');
  window.parent.postMessage({schema_version:'wright.process-host/1', type, nonce:host.nonce,
    presentation_id:context.presentation_id, generation:context.generation, ...extra}, host.origin);
};
const receiveHost = event => {
  const value = event.data;
  if (!mounted || !context || event.source !== window.parent || window.parent === window ||
      !value || typeof value !== 'object' || Array.isArray(value) ||
      value.schema_version !== 'wright.process-host/1' ||
      value.presentation_id !== context.presentation_id || value.generation !== context.generation ||
      typeof value.nonce !== 'string' || !/^[a-z0-9-]{36}$/i.test(value.nonce) ||
      !['hello','theme'].includes(value.type) ||
      Object.keys(value).some(key => !['schema_version','type','nonce','presentation_id','generation','tokens'].includes(key))) return;
  try {
    const origin = new URL(event.origin);
    if (!['http:','https:'].includes(origin.protocol) || origin.origin !== event.origin) return;
  } catch { return; }
  if (host && (host.origin !== event.origin || host.nonce !== value.nonce)) return;
  if (!host && value.type !== 'hello') return;
  host = {origin:event.origin, nonce:value.nonce};
  if (value.tokens && typeof value.tokens === 'object' && !Array.isArray(value.tokens)) {
    for (const [key, token] of Object.entries(value.tokens)) {
      if (themeKeys.has(key) && typeof token === 'string' && token.length <= 128 && !/[;{}@]|url\\s*\\(/i.test(token))
        document.documentElement.style.setProperty(key, token);
    }
  }
  if (value.type === 'hello') signalHost('ready');
};
window.addEventListener('message', receiveHost);
try {
  const response = await fetch('/__wright/process/context', {credentials:'same-origin', cache:'no-store'});
  if (!response.ok) throw new Error('The presentation context is unavailable.');
  context = await response.json();
  const app = await import('/app.js');
  if (typeof app.createPresentationClient !== 'function' || typeof app.mount !== 'function')
    throw new Error('The saved interface needs a compatible host.');
  const client = app.createPresentationClient(context, {
    onRunStarted: receipt => signalHost('started', {request_id:receipt.request_id}),
    navigate: resolution => signalHost('navigate', {target:resolution.target})
  });
  const snapshot = await client.getSnapshot();
  dispose = app.mount(root, {client, snapshot, readOnly:context.read_only});
  if (typeof dispose !== 'function' || typeof dispose.update !== 'function')
    throw new Error('The saved interface needs a compatible host.');
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  if (context.read_only) {
    const loaded = await fetch('/__wright/process/loaded', {
      method:'POST', credentials:'same-origin', cache:'no-store',
      headers:{'content-type':'application/json'},
      body:JSON.stringify({schema_version:'wright.process-presentation-loaded/1'})
    });
    if (!loaded.ok) throw new Error('The preview could not be confirmed.');
  }
  mounted = true;
  connection.textContent = context.read_only ? 'Preview - process controls are read-only.' : 'Connected to Wright.';
  if (context.run_id) {
    void (async () => {
      try {
        for await (const update of client.follow({runId:context.run_id, signal:observer.signal})) {
          if (update.type === 'snapshot') dispose.update(update.snapshot);
          else if (update.type === 'connection')
            connection.textContent = update.state === 'connected' ? 'Connected to Wright.' : 'Reconnecting to Wright...';
          else if (update.type === 'reconciliation') connection.textContent = update.reason.message;
        }
      } catch {
        if (!observer.signal.aborted) connection.textContent = 'Progress disconnected. Reopen this run in Wright to reconcile its current state.';
      }
    })();
  }
} catch (error) {
  observer.abort();
  if (dispose) { dispose(); dispose = undefined; }
  connection.textContent = 'Connection unavailable.';
  root.replaceChildren();
  const title = document.createElement('h2'); title.textContent = 'Interface unavailable';
  const reason = document.createElement('p');
  reason.textContent = 'Return to Wright and use the common working view or reopen this saved interface.';
  root.append(title, reason);
}
window.addEventListener('pagehide', () => {
  mounted = false; window.removeEventListener('message', receiveHost);
  observer.abort(); if (dispose) dispose();
}, {once:true});
"""


class ProcessStaticAssets:
    def __init__(self, vault_directory: Path, inventory_digest: str):
        content = ImmutableFileSet(vault_directory).read(inventory_digest)
        assets = {}
        for name, raw in content.items():
            if not name.startswith("dist/"):
                continue
            path = PurePosixPath(name.removeprefix("dist/"))
            media = _TYPES.get(path.suffix.lower())
            if (
                not media
                or not path.parts
                or any(part in {".", ".."} for part in path.parts)
            ):
                raise ValueError("The bundle contains an unsupported static asset")
            assets["/" + path.as_posix()] = (raw, media)
        if "/app.js" not in assets:
            raise ValueError("The saved bundle has no fixed application entry")
        # Vite may omit a CSS file when no stylesheet is imported.
        assets.setdefault("/style.css", (b"", _TYPES[".css"]))
        assets["/"] = assets["/index.html"] = (_INDEX, "text/html; charset=utf-8")
        assets["/wright-runtime.js"] = (_RUNTIME, _TYPES[".js"])
        assets["/__wright/health"] = (b'{"state":"ready"}', "application/json")
        self.assets = MappingProxyType(assets)

    def response(self, path: str):
        if len(path) > 2048:
            return None
        # URL decoding, directories and alternate path aliases are not accepted.
        # Generated assets use fixed confined logical names, not filesystem URLs.
        if "%" in path or "\\" in path:
            return None
        parts = urlsplit(path)
        if parts.scheme or parts.netloc:
            return None
        return self.assets.get(parts.path)


def static_handler(assets: ProcessStaticAssets):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def do_GET(self):
            self._read(False)

        def do_HEAD(self):
            self._read(True)

        def _read(self, head):
            item = assets.response(self.path)
            raw, media = (
                item
                if item
                else (b"Static asset unavailable.", "text/plain; charset=utf-8")
            )
            self.send_response(200 if item else 404)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Content-Security-Policy", STATIC_CSP)
            self.send_header(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=(), clipboard-read=(), clipboard-write=()",
            )
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            if not head:
                self.wfile.write(raw)

        def log_message(self, *_args):
            # Do not copy presentation query strings into runtime logs.
            pass

    return Handler


def make_static_server(assets, host, port):
    if host != "127.0.0.1" or type(port) is not int or not 0 <= port <= 65_535:
        raise ValueError("The static runtime requires a numeric loopback endpoint")
    return HTTPServer((host, port), static_handler(assets))


def main():
    parser = argparse.ArgumentParser(
        description="Wright-owned static process interface runtime"
    )
    parser.add_argument("--vault-directory", required=True)
    parser.add_argument("--inventory-digest", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.port <= 65_535:
        parser.error("A surface-owner-assigned port is required")
    try:
        assets = ProcessStaticAssets(Path(args.vault_directory), args.inventory_digest)
        with make_static_server(assets, args.host, args.port) as server:
            server.serve_forever(poll_interval=0.25)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        # No physical paths, source bytes or credentials enter launch diagnostics.
        raise SystemExit(
            "The immutable process interface runtime could not start."
        ) from None


if __name__ == "__main__":
    main()
