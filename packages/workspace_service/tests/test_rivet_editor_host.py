from __future__ import annotations

import socket
import subprocess
import sys
import time
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
HOST = ROOT / "integrations" / "rivet" / "editor" / "host.py"


def _unused_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _get(url: str) -> tuple[int, bytes]:
    with urlopen(url, timeout=1) as response:  # noqa: S310 - loopback test host
        return response.status, response.read()


def _request(url: str, *, method="GET", headers=None, body: bytes | None = None):
    request = Request(url, data=body, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=2) as response:  # noqa: S310 - loopback only
            return response.status, dict(response.headers), response.read()
    except HTTPError as error:
        return error.code, dict(error.headers), error.read()


class _HermesHandler(BaseHTTPRequestHandler):
    api_key = "upstream-hermes-secret"

    def do_POST(self):  # noqa: N802
        assert self.path == "/v1/chat/completions"
        assert self.headers["Authorization"] == f"Bearer {self.api_key}"
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        assert payload["model"] == "hermes"
        body = json.dumps(
            {
                "id": "upstream",
                "object": "chat.completion",
                "created": 1,
                "model": "private",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello"},
                        "finish_reason": "stop",
                    }
                ],
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


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
        assert health == b'{"status": "ok", "mode": "rivet2-canvas"}'
        route_status, content = _get(f"{base_url}/projects/untitled")
        assert route_status == 200
        assert content == b"<main>Rivet editor</main>"
        assert b"wright-minimal-mode" not in content
        assert b"showOpenFilePicker" not in content
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_editor_host_ai_config_token_security_and_completion_proxy(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "index.html").write_text("<main>Rivet editor</main>", encoding="utf-8")
    hermes = ThreadingHTTPServer(("127.0.0.1", 0), _HermesHandler)
    hermes_thread = threading.Thread(target=hermes.serve_forever, daemon=True)
    hermes_thread.start()
    port = _unused_port()
    env = {
        **os.environ,
        "HERMES_API_BASE_URL": f"http://127.0.0.1:{hermes.server_address[1]}",
        "HERMES_API_KEY": _HermesHandler.api_key,
    }
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
            "--ai-enabled",
            "--ai-request-bytes",
            "1024",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(40):
            try:
                status, _, config_body = _request(f"{base_url}/wright-ai/config")
            except OSError:
                time.sleep(0.05)
                continue
            if status == 200:
                break
        else:
            raise AssertionError("editor AI host did not become ready")
        config = json.loads(config_body)
        assert config["available"] is True
        assert config["provider"] == "custom"
        assert config["model"] == "wright-hermes"
        assert config["baseUrl"] == "/wright-ai/v1"
        assert config["token"]
        assert _HermesHandler.api_key not in config_body.decode()
        assert config_body.decode().count("token") == 1

        payload = json.dumps(
            {
                "model": "wright-hermes",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            }
        ).encode()
        completion_status, headers, completion = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers={
                "X-Rivet-AI-Token": config["token"],
                "Content-Type": "application/json",
            },
            body=payload,
        )
        assert completion_status == 200
        assert headers["Cache-Control"] == "no-store"
        assert json.loads(completion)["model"] == "wright-hermes"
        assert _HermesHandler.api_key not in completion.decode()

        wrong_status, _, wrong = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": "Bearer wrong",
                "Content-Type": "application/json",
            },
            body=payload,
        )
        assert wrong_status == 401
        assert json.loads(wrong)["error"]["code"] == "invalid_token"

        media_status, _, _ = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": f"Bearer {config['token']}",
                "Content-Type": "text/plain",
            },
            body=payload,
        )
        assert media_status == 415

        large_status, _, large = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": f"Bearer {config['token']}",
                "Content-Type": "application/json",
            },
            body=b"{" + b"x" * 2048 + b"}",
        )
        assert large_status == 413
        assert json.loads(large)["error"]["code"] == "invalid_request"

        method_status, _, _ = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="PUT",
        )
        assert method_status == 405
        missing_status, _, _ = _request(f"{base_url}/wright-ai/not-a-route")
        assert missing_status == 404
    finally:
        process.terminate()
        process.wait(timeout=5)
        hermes.shutdown()
        hermes.server_close()


def test_editor_host_renews_expired_browser_token(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "index.html").write_text("<main>Rivet editor</main>", encoding="utf-8")
    port = _unused_port()
    env = {
        **os.environ,
        "HERMES_API_BASE_URL": "http://127.0.0.1:8642",
        "HERMES_API_KEY": "local-hermes-key",
    }
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
            "--ai-enabled",
            "--ai-token-ttl",
            "1",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        for _ in range(40):
            try:
                status, _, first_body = _request(f"{base_url}/wright-ai/config")
                break
            except OSError:
                time.sleep(0.05)
        assert status == 200
        first = json.loads(first_body)
        time.sleep(1.1)
        second_status, _, second_body = _request(f"{base_url}/wright-ai/config")
        second = json.loads(second_body)

        assert second_status == 200
        assert second["available"] is True
        assert second["token"] != first["token"]
        assert second["expiresAt"] != first["expiresAt"]
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_editor_host_keeps_active_ai_token_alive_across_initial_ttl(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "index.html").write_text("<main>Rivet editor</main>", encoding="utf-8")
    hermes = ThreadingHTTPServer(("127.0.0.1", 0), _HermesHandler)
    hermes_thread = threading.Thread(target=hermes.serve_forever, daemon=True)
    hermes_thread.start()
    port = _unused_port()
    env = {
        **os.environ,
        "HERMES_API_BASE_URL": f"http://127.0.0.1:{hermes.server_address[1]}",
        "HERMES_API_KEY": _HermesHandler.api_key,
    }
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
            "--ai-enabled",
            "--ai-token-ttl",
            "1",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    payload = json.dumps(
        {
            "model": "wright-hermes",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        }
    ).encode()
    try:
        for _ in range(40):
            try:
                status, _, config_body = _request(f"{base_url}/wright-ai/config")
                break
            except OSError:
                time.sleep(0.05)
        assert status == 200
        token = json.loads(config_body)["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        time.sleep(0.6)
        first_status, _, _ = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers=headers,
            body=payload,
        )
        time.sleep(0.6)
        second_status, _, _ = _request(
            f"{base_url}/wright-ai/v1/chat/completions",
            method="POST",
            headers=headers,
            body=payload,
        )

        assert first_status == 200
        assert second_status == 200
    finally:
        process.terminate()
        process.wait(timeout=5)
        hermes.shutdown()
        hermes.server_close()


def test_editor_host_reports_ai_unavailable_without_a_browser_secret(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "index.html").write_text("<main>Rivet editor</main>", encoding="utf-8")
    port = _unused_port()
    env = {
        **os.environ,
        "HERMES_API_BASE_URL": "http://127.0.0.1:9",
        "HERMES_API_KEY": "",
    }
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
            "--ai-enabled",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        for _ in range(40):
            try:
                status, _, body = _request(f"{base_url}/wright-ai/config")
                break
            except OSError:
                time.sleep(0.05)
        assert status == 200
        config = json.loads(body)
        assert config == {"available": False, "reason": "hermes_unavailable"}
    finally:
        process.terminate()
        process.wait(timeout=5)
