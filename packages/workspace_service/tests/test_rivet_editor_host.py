from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[3]
HOST = ROOT / "integrations" / "rivet" / "editor" / "host.py"


def _unused_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _get(url: str) -> tuple[int, bytes]:
    with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test host
        return response.status, response.read()


def test_editor_host_serves_health_and_spa_routes_from_supplied_root(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "index.html").write_text("<main>Rivet editor</main>", encoding="utf-8")
    port = _unused_port()
    process = subprocess.Popen(
        [
            sys.executable,
            str(HOST),
            "--root",
            str(root),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(20):
            try:
                status, health = _get(f"{base_url}/health")
            except OSError:
                time.sleep(0.05)
                continue
            break
        else:
            raise AssertionError("editor host did not become ready")
        assert status == 200
        assert health == b'{"status": "ok", "mode": "manual-import-export"}'
        route_status, content = _get(f"{base_url}/projects/untitled")
        assert route_status == 200
        assert content == b"<main>Rivet editor</main>"
    finally:
        process.terminate()
        process.wait(timeout=5)
