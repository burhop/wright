"""Bounded localhost host for Wright's pinned Rivet editor artifact."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class EditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, root: Path, **kwargs) -> None:
        self._root = root
        super().__init__(*args, directory=str(root), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/health":
            body = json.dumps({"status": "ok", "mode": "manual-import-export"}).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        requested = self.path.split("?", 1)[0]
        if requested != "/" and "." not in Path(requested).name:
            self.path = "/index.html"
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "index.html").is_file():
        raise SystemExit("verified Rivet editor entrypoint is unavailable")
    server = ThreadingHTTPServer(
        (args.host, args.port), lambda *a, **kw: EditorHandler(*a, root=root, **kw)
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
