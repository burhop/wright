"""Installed native API proof, reused by the existing wheel-content build.

The subprocesses use one extracted candidate with real API lifespan, SQLite,
runtime, and artifact storage. Restart and package relocation are covered;
different-version installer updates and Docker remain separate evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXAMPLES = {"concept-brief", "mass-check", "package-review"}
EXPECTED_BRIEF = b"Design a desk bracket.\nMaximum mass: 200 g."


def test_native_package_contract_matches_readable_schema_and_examples() -> None:
    from importlib.resources import files

    from core.native_process import validate_definition
    from data_vault.migrations import schema_bounds

    packaged = files("wright_engineering")
    compatibility = json.loads(packaged.joinpath("compatibility.json").read_text())
    minimum, maximum = schema_bounds()
    assert compatibility["data_schema"] == {"min": minimum, "max": maximum}
    examples = packaged.joinpath("static/native-processes")
    for name in EXAMPLES:
        document = json.loads(examples.joinpath(f"{name}.json").read_text())
        assert validate_definition(document).process_id == name


def verify_installed_native_lifecycle(installed: Path, scratch: Path) -> None:
    """Exercise the already-built wheel without building another distribution."""
    scratch.mkdir(parents=True)
    probe = scratch / "installed_native_probe.py"
    shutil.copyfile(__file__, probe)
    state = scratch / "wright-home"
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("WRIGHT_TESTING", None)
    environment.update(
        HERMES_API_BASE_URL="http://127.0.0.1:1",
        HERMES_API_KEY="",
        API_SERVER_KEY="",
        HERMES_CONFIG_PATH=str(scratch / "absent-hermes-config.yaml"),
        HERMES_ENV_PATH=str(scratch / "absent-hermes.env"),
        WRIGHT_API_MCP_AUTOSTART="0",
        WRIGHT_REMOTE_TELEMETRY_ENABLED="0",
        WRIGHT_AUTH_MODE="enforced",
        WRIGHT_API_TOKEN="native-installed-test-token",
        WRIGHT_SECRETS_PATH=str(state / "data" / "test-secrets.json"),
    )
    observations = []
    for phase in ("create", "restart", "package-replacement"):
        package = installed
        if phase == "package-replacement":
            package = scratch / "replacement-package"
            shutil.copytree(installed, package)
        completed = subprocess.run(
            [sys.executable, "-I", str(probe), str(package), str(state), phase],
            cwd=scratch,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        observations.append(json.loads(completed.stdout.splitlines()[-1]))
    assert {item["phase"] for item in observations} == {
        "create",
        "restart",
        "package-replacement",
    }
    assert len({item["pid"] for item in observations}) == 3
    assert len({item["artifact_sha256"] for item in observations}) == 1
    (scratch / "native-installed-evidence.json").write_text(
        json.dumps(observations, indent=2) + "\n", encoding="utf-8"
    )


def _installed_probe(installed: Path, state: Path, phase: str) -> None:
    import ipaddress
    import socket
    from importlib.resources import files

    installed = installed.resolve()
    sys.path.insert(0, str(installed))

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Installed native API attempted network access")

    original_connect = socket.socket.connect

    def local_connect(connection, address):
        # Windows event loops implement their wakeup socketpair over loopback.
        # HTTP clients still cannot open connections through create_connection.
        if isinstance(address, tuple) and ipaddress.ip_address(address[0]).is_loopback:
            return original_connect(connection, address)
        return deny_network()

    socket.create_connection = deny_network
    socket.socket.connect = local_connect

    from wright_engineering.runtime.layout import NativeLayout
    from wright_engineering.runtime.server import prepare_runtime_environment

    layout = NativeLayout.from_wright_home(state)
    prepare_runtime_environment(layout)
    # Unrelated optional surface/agent transports are not part of this native run.
    os.environ["WRIGHT_SURFACES_ENABLED"] = "0"
    os.environ["WRIGHT_SURFACES_LIVE_APPS_ENABLED"] = "0"

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    from fastapi.testclient import TestClient
    from api.main import app
    from core.native_process import language_contract
    from data_vault import upgrade_database
    from data_vault.migrations import schema_bounds
    from data_vault.secret_provider import FileSecretProvider
    from data_vault.workspace_repository import WorkspaceRepository

    compatibility = json.loads(
        files("wright_engineering").joinpath("compatibility.json").read_text()
    )
    minimum, maximum = schema_bounds()
    assert compatibility["data_schema"] == {"min": minimum, "max": maximum}

    workspace = layout.workspaces / "native-packaging"
    database = layout.data / "wright.db"
    baseline_path = layout.data / "native-packaging-baseline.json"
    if phase == "create":
        workspace.mkdir(parents=True)
        upgrade_database(database)
        WorkspaceRepository(
            str(database), secrets=FileSecretProvider(layout.data / "test-secrets.json")
        ).create("packaged-workspace", "packaged-session", str(workspace))

    params = {"session_id": "packaged-session"}
    base = "/api/native-processes"
    try:
        with TestClient(
            app,
            base_url="http://127.0.0.1",
            headers={"Authorization": "Bearer native-installed-test-token"},
        ) as client:
            response = client.get(base + "/contract", params=params)
            assert response.status_code == 200, response.text
            assert response.json() == language_contract()
            listed = client.get(base + "/examples")
            assert listed.status_code == 200, listed.text
            examples = {item["id"]: item for item in listed.json()["examples"]}
            assert set(examples) == EXAMPLES
            for name in EXAMPLES:
                packaged = json.loads(
                    files("wright_engineering")
                    .joinpath(f"static/native-processes/{name}.json")
                    .read_text()
                )
                assert examples[name]["definition"] == packaged

            if phase == "create":
                response = client.post(
                    base,
                    params=params,
                    json={
                        "definition": examples["concept-brief"]["definition"],
                        "presentation": {},
                        "request_id": "packaged-save",
                    },
                )
                assert response.status_code == 201, response.text
                saved = response.json()
                run_request = {
                    "expected_token": saved["token"],
                    "request_id": "packaged-run",
                    "bindings": {},
                    "derived_from_run_id": None,
                    "timeout_seconds": 10,
                }
                submitted = client.post(
                    base + "/concept-brief/runs",
                    params=params,
                    json=run_request,
                    headers={"X-Trace-Id": "packaged-native-run"},
                )
                assert submitted.status_code == 202, submitted.text
                run_id = submitted.json()["run_id"]
                deadline = time.monotonic() + 10
                while True:
                    inspected = client.get(base + f"/runs/{run_id}", params=params)
                    assert inspected.status_code == 200, inspected.text
                    run = inspected.json()
                    if run["state"] not in {"queued", "running"}:
                        break
                    assert time.monotonic() < deadline, (
                        "Installed native run missed deadline"
                    )
                    time.sleep(0.02)
                assert run["state"] == "succeeded", run
                assert all(step["state"] == "succeeded" for step in run["steps"])
                assert run["trace_id"] == "packaged-native-run"
                assert len(run["artifacts"]) == 1
                baseline = {"saved": saved, "run": run, "run_request": run_request}
            else:
                baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
                run = baseline["run"]
                run_id = run["run_id"]
                response = client.get(base + "/concept-brief", params=params)
                assert response.status_code == 200, response.text
                assert response.json() == baseline["saved"]
                response = client.get(base + f"/runs/{run_id}", params=params)
                assert response.status_code == 200, response.text
                assert response.json() == run
                replay = client.post(
                    base + "/concept-brief/runs",
                    params=params,
                    json=baseline["run_request"],
                )
                assert replay.status_code == 202, replay.text
                assert replay.json()["run_id"] == run_id
                history = client.get(base + "/concept-brief/runs", params=params)
                assert history.status_code == 200, history.text
                assert [item["run_id"] for item in history.json()["runs"]] == [run_id]

            artifact = run["artifacts"][0]
            response = client.get(
                base + f"/runs/{run_id}/artifacts/{artifact['artifact_id']}",
                params=params,
            )
            assert response.status_code == 200, response.text
            assert response.content == EXPECTED_BRIEF
            digest = hashlib.sha256(response.content).hexdigest()
            assert (
                digest
                == artifact["content_digest"]
                == response.headers["X-Content-SHA256"]
            )
            assert artifact["size"] == len(EXPECTED_BRIEF)
            assert artifact["provenance"] and artifact["step_id"] == "brief-file"
            events = client.get(base + f"/runs/{run_id}/events", params=params)
            assert events.status_code == 200, events.text
            if phase == "create":
                baseline["events"] = events.json()
                baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            else:
                assert events.json() == baseline["events"]

        # Any repository fallback import would invalidate the installed proof.
        prefixes = {
            "api",
            "core",
            "data_vault",
            "tool_registry",
            "workspace_service",
            "agent_adapters",
            "model_registry",
            "wright",
            "wright_engineering",
        }
        origins = []
        for name, module in tuple(sys.modules.items()):
            origin = getattr(module, "__file__", None)
            if name.split(".")[0] in prefixes and origin:
                assert Path(origin).resolve().is_relative_to(installed), (name, origin)
                origins.append(name)
        spans = exporter.get_finished_spans()
        assert any(span.name == "native.artifact.read" for span in spans)
        if phase == "create":
            execution = [span for span in spans if span.name == "native.run.execute"]
            assert len(execution) == 1
            assert any(
                span.name == "native.artifact.promote"
                and span.context.trace_id == execution[0].context.trace_id
                for span in spans
            )
        print(
            json.dumps(
                {
                    "phase": phase,
                    "pid": os.getpid(),
                    "installed": str(installed),
                    "wright_modules_checked": len(origins),
                    "artifact_sha256": digest,
                    "run_id": run_id,
                    "offline": True,
                    "native_span_count": sum(
                        span.name.startswith("native.") for span in spans
                    ),
                }
            )
        )
    finally:
        provider.shutdown()


if __name__ == "__main__":
    _installed_probe(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
