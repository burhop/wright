"""Deterministic stdlib fixture whose counter is shared by every presentation."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock


class State:
    value = 0
    lock = Lock()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path == "/health":
            self._send(200, b'{"status":"ready"}', "application/json")
            return
        if self.path == "/api/state":
            with State.lock:
                body = json.dumps({"value": State.value}).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if self.path != "/":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        body = b"""<!doctype html><html><body>
        <h1>Shareable app</h1>
        <button id='increment'>Increment shared count</button>
        <output id='count' aria-live='polite'>loading</output>
        <script>
        const output = document.querySelector('#count');
        async function refresh(){output.textContent=String((await (await fetch('/api/state')).json()).value)}
        document.querySelector('#increment').addEventListener('click',async()=>{await fetch('/api/state',{method:'POST'});await refresh()});
        refresh();
        </script></body></html>"""
        self._send(200, body, "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path != "/api/state":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        with State.lock:
            State.value += 1
            body = json.dumps({"value": State.value}).encode("utf-8")
        self._send(200, body, "application/json")

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    options = parser.parse_args()
    ThreadingHTTPServer((options.host, options.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
