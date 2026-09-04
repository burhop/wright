"""Actual native API/HTTP-CLI parity over isolated SQLite and local computation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from api.composition import build_native_process_service
from api.middleware.tracing import TracingMiddleware
from api.routers.native_process import router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings
from data_vault import GatewayRepository, upgrade_database
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository
from tool_registry.gateway_adapters import (
    DatabaseGatewayAudit,
    DatabaseGatewayCatalog,
    DatabaseGatewayWorkspace,
    EngineGatewayLifecycle,
)
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.manager import McpEngine
from workspace_service.native_process_cli import main as cli_main
from workspace_service.service import WorkspaceService
from workspace_service.workspace_path import WorkspacePath
from workspace_service.native_process_runtime import NativeRuntime

BASE = "/api/native-processes"
SESSION = {"session_id": "session-one"}
AUTH = {"Authorization": "Bearer native-api-test-token"}
ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "src/wright_engineering/static/native-processes"


@pytest.fixture
def execution(tmp_path):
    db = str(tmp_path / "state.db")
    upgrade_database(db)
    workspaces = WorkspaceRepository(
        db, secrets=FileSecretProvider(tmp_path / "secrets.json")
    )
    for identity in ("one", "two"):
        folder = tmp_path / identity
        folder.mkdir()
        workspaces.create(
            identity, "session-" + identity, str(folder), workspace_name=identity
        )
    managed = WorkspaceService(
        db,
        parent_dir_provider=lambda: str(tmp_path),
        protected_roots_provider=lambda: (str(tmp_path / "application"),),
    )
    repository = GatewayRepository(db)
    gateway = GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=DatabaseGatewayCatalog(db),
        lifecycle=EngineGatewayLifecycle(McpEngine(db)),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
    )
    service = build_native_process_service(db, gateway, managed)
    return service, gateway, tmp_path / "one"


def app_for(execution):
    service, gateway, _ = execution

    @asynccontextmanager
    async def lifespan(app):
        await service.startup()
        try:
            yield
        finally:
            await service.close()
            await gateway.shutdown()

    app = FastAPI(lifespan=lifespan)
    app.state.native_process_service = service
    app.state.gateway_service = gateway
    app.state.security_settings = SecuritySettings(
        "enforced", "native-api-test-token", ("http://localhost:5173",), "127.0.0.1"
    )
    app.add_middleware(ControlPlaneSecurityMiddleware)
    app.add_middleware(TracingMiddleware)
    app.include_router(router, prefix=BASE)
    return app


def document(name="concept-brief"):
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def save(client, data):
    response = client.post(
        BASE,
        params=SESSION,
        json={
            "definition": data,
            "presentation": {},
            "request_id": "save-" + uuid.uuid4().hex,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def submission(saved, request_id=None):
    return {
        "expected_token": saved["token"],
        "request_id": request_id or "run-" + uuid.uuid4().hex,
        "bindings": {},
        "timeout_seconds": 60,
        "derived_from_run_id": None,
    }


def wait_run(client, run_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(f"{BASE}/runs/{run_id}", params=SESSION)
        assert response.status_code == 200, response.text
        result = response.json()
        if result["state"] not in {"queued", "running"}:
            return result
        time.sleep(0.01)
    pytest.fail("Native API run did not reach terminal state")


@pytest.mark.parametrize("name", ["concept-brief", "mass-check", "package-review"])
def test_actual_api_examples_produce_frozen_bytes_and_scoped_evidence(execution, name):
    service, _, _ = execution
    with TestClient(app_for(execution), headers=AUTH) as client:
        saved = save(client, document(name))
        created = client.post(
            f"{BASE}/{saved['definition']['id']}/runs",
            params=SESSION,
            json=submission(saved),
            headers={"X-Trace-Id": "api-runtime-trace"},
        )
        assert created.status_code == 202, created.text
        run_id = created.json()["run_id"]
        result = wait_run(client, run_id)
        assert result["state"] == "succeeded", result["reason"]
        assert result["snapshot"]["definition"] == saved["definition"]
        oracle = next(
            item
            for item in json.loads((EXAMPLES / "oracles.json").read_text())["cases"]
            if item["id"] == name
        )
        artifact = next(
            item
            for item in result["artifacts"]
            if item["filename"] == oracle["artifact"]
        )
        path = f"{BASE}/runs/{run_id}/artifacts/{artifact['artifact_id']}"
        response = client.get(path, params=SESSION)
        assert response.content == oracle["expected_text"].encode()
        assert (
            response.headers["X-Content-SHA256"]
            == hashlib.sha256(response.content).hexdigest()
            == artifact["content_digest"]
        )
        assert response.headers["Content-Disposition"].startswith("attachment;")
        assert response.headers["Cache-Control"] == "no-store"
        assert client.get(path, params={"session_id": "session-two"}).status_code == 404
        events = client.get(f"{BASE}/runs/{run_id}/events", params=SESSION).json()[
            "events"
        ]
        assert {event["trace_id"] for event in events} == {"api-runtime-trace"}
        assert events[-1]["kind"] == "run.succeeded"
        history = client.get(
            f"{BASE}/{saved['definition']['id']}/runs", params=SESSION
        ).json()
        assert history["runs"][0]["run_id"] == run_id
        assert service.inspect_run("session-one", run_id) == result


def test_exact_run_retry_precedes_current_token_and_readiness(execution):
    service, _, _ = execution
    with TestClient(app_for(execution), headers=AUTH) as client:
        saved = save(client, document())
        route = f"{BASE}/{saved['definition']['id']}/runs"
        payload = submission(saved, "same-run-request")
        first = client.post(route, params=SESSION, json=payload)
        result = wait_run(client, first.json()["run_id"])
        original_events = service.run_events("session-one", result["run_id"])
        changed = document()
        changed["steps"][0]["config"] = {}
        updated = client.put(
            f"{BASE}/{changed['id']}",
            params=SESSION,
            json={
                "definition": changed,
                "presentation": {},
                "expected_token": saved["token"],
                "request_id": "make-unready",
            },
        )
        assert updated.status_code == 200
        replay = client.post(route, params=SESSION, json=payload)
        assert replay.status_code == 202 and replay.json() == first.json()
        assert service.run_events("session-one", result["run_id"]) == original_events
        reused = client.post(
            route, params=SESSION, json={**payload, "timeout_seconds": 61}
        )
        assert (
            reused.status_code == 409
            and reused.json()["code"] == "NATIVE_REQUEST_REUSED"
        )
        stale = client.post(
            route, params=SESSION, json={**payload, "request_id": "fresh-stale"}
        )
        assert stale.status_code == 409 and stale.json()["code"] == "NATIVE_CONFLICT"
        unready = client.post(
            route,
            params=SESSION,
            json={
                **payload,
                "request_id": "fresh-unready",
                "expected_token": updated.json()["token"],
            },
        )
        assert (
            unready.status_code == 422 and unready.json()["code"] == "NATIVE_NOT_READY"
        )
        assert service.run_history("session-one", changed["id"])["runs"] == [
            service.repository.summary("one", result["run_id"])
        ]


def test_cli_check_run_inspect_cancel_uses_identical_api(
    execution, monkeypatch, capsys
):
    monkeypatch.setenv("WRIGHT_API_TOKEN", "native-api-test-token")
    with TestClient(app_for(execution), headers=AUTH) as client:
        saved = save(client, document("mass-check"))
        args = ["--base-url", "http://testserver", "--session-id", "session-one"]
        assert (
            cli_main(args + ["check", str(EXAMPLES / "mass-check.json")], client=client)
            == 0
        )
        stdout = capsys.readouterr().out
        checked = next(
            json.loads(line)
            for line in reversed(stdout.splitlines())
            if line.startswith("{") and '"ready"' in line
        )
        assert (
            checked
            == client.post(
                BASE + "/check",
                params=SESSION,
                json={"definition": saved["definition"], "bindings": {}},
            ).json()
        )
        assert (
            cli_main(
                args
                + [
                    "run",
                    saved["definition"]["id"],
                    "--expected-token",
                    saved["token"],
                    "--request-id",
                    "headless-parity",
                ],
                client=client,
            )
            == 0
        )
        stdout = capsys.readouterr().out
        submitted = next(
            json.loads(line)
            for line in reversed(stdout.splitlines())
            if line.startswith("{") and '"run_id"' in line
        )
        result = wait_run(client, submitted["run_id"])
        assert result["state"] == "succeeded"
        assert cli_main(args + ["inspect", submitted["run_id"]], client=client) == 0
        inspected = next(
            json.loads(line)
            for line in reversed(capsys.readouterr().out.splitlines())
            if line.startswith("{") and '"snapshot"' in line
        )
        assert inspected == result
        assert cli_main(args + ["cancel", submitted["run_id"]], client=client) == 0
        cancelled = next(
            json.loads(line)
            for line in reversed(capsys.readouterr().out.splitlines())
            if line.startswith("{") and '"run_id"' in line
        )
        assert cancelled["state"] == "succeeded"


@pytest.mark.asyncio
async def test_submitted_run_survives_http_client_disconnect(execution, monkeypatch):
    service, gateway, _ = execution
    app = app_for(execution)
    await service.startup()
    entered, release = threading.Event(), threading.Event()
    original = service.runtime._local_operation

    def pause(*args):
        entered.set()
        assert release.wait(3)
        return original(*args)

    monkeypatch.setattr(service.runtime, "_local_operation", pause)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="http://testserver",
            headers=AUTH,
        ) as client:
            created = await client.post(
                BASE,
                params=SESSION,
                json={
                    "definition": document(),
                    "presentation": {},
                    "request_id": "disconnected-save",
                },
            )
            saved = created.json()
            response = await client.post(
                f"{BASE}/{saved['definition']['id']}/runs",
                params=SESSION,
                json=submission(saved),
            )
            assert response.status_code == 202, response.text
            run_id = response.json()["run_id"]
            assert await asyncio.to_thread(entered.wait, 2)
        # The requesting HTTP client is gone; the application still owns the run.
        release.set()
        async with asyncio.timeout(5):
            while service.inspect_run("session-one", run_id)["state"] in {
                "queued",
                "running",
            }:
                await asyncio.sleep(0.01)
        assert service.inspect_run("session-one", run_id)["state"] == "succeeded"
    finally:
        release.set()
        await service.close()
        await gateway.shutdown()


@pytest.mark.asyncio
async def test_cancelled_startup_is_drained_before_owner_release(
    execution, monkeypatch
):
    service, gateway, _ = execution
    entered, release = threading.Event(), threading.Event()
    original = service.repository.interrupt_abandoned

    def paused_interrupt():
        entered.set()
        assert release.wait(5)
        return original()

    monkeypatch.setattr(service.repository, "interrupt_abandoned", paused_interrupt)
    startup = asyncio.create_task(service.startup())
    contender = NativeRuntime(service.repository, service.scope)
    closing = None
    try:
        assert await asyncio.to_thread(entered.wait, 3)
        startup.cancel()
        with pytest.raises(asyncio.CancelledError):
            await startup
        closing = asyncio.create_task(service.close())
        await asyncio.sleep(0.02)
        assert not closing.done(), "Close must drain the still-running startup worker"
        release.set()
        await asyncio.wait_for(closing, 3)
        assert service.runtime._owner is None
        assert not service._workers
        contender.ensure_owner()
    finally:
        release.set()
        if closing is not None:
            await closing
        await service.close()
        await contender.close()
        await gateway.shutdown()


def test_actual_cross_origin_artifact_exposes_verifiable_digest(execution):
    from api import main

    app = app_for(execution)
    configuration = next(
        row for row in main.app.user_middleware if row.cls is CORSMiddleware
    )
    app.add_middleware(configuration.cls, **configuration.kwargs)
    with TestClient(app, headers=AUTH) as client:
        saved = save(client, document())
        created = client.post(
            f"{BASE}/{saved['definition']['id']}/runs",
            params=SESSION,
            json=submission(saved),
        ).json()
        run = wait_run(client, created["run_id"])
        artifact = run["artifacts"][0]
        response = client.get(
            f"{BASE}/runs/{run['run_id']}/artifacts/{artifact['artifact_id']}",
            params=SESSION,
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
        )
        assert response.headers["X-Content-SHA256"] == artifact["content_digest"]
        exposed = {
            value.strip().lower()
            for value in response.headers.get(
                "Access-Control-Expose-Headers", ""
            ).split(",")
        }
        assert "x-content-sha256" in exposed


def test_artifact_tampering_and_route_limits_return_frozen_errors(execution):
    service, _, workspace = execution
    with TestClient(app_for(execution), headers=AUTH) as client:
        saved = save(client, document())
        created = client.post(
            f"{BASE}/{saved['definition']['id']}/runs",
            params=SESSION,
            json=submission(saved),
        ).json()
        result = wait_run(client, created["run_id"])
        artifact = result["artifacts"][0]
        record = service.repository.artifact(
            "one", result["run_id"], artifact["artifact_id"]
        )
        (workspace / record["storage_key"]).write_bytes(b"tampered")
        response = client.get(
            f"{BASE}/runs/{result['run_id']}/artifacts/{artifact['artifact_id']}",
            params=SESSION,
        )
        assert (
            response.status_code == 409
            and response.json()["code"] == "NATIVE_ARTIFACT_INVALID"
        )
        for suffix, params in [
            ("/events", {**SESSION, "limit": 201}),
            ("", {"session_id": "session-two"}),
        ]:
            response = client.get(
                f"{BASE}/runs/{result['run_id']}" + suffix, params=params
            )
            assert response.status_code in {400, 404}
        response = client.post(
            f"{BASE}/runs/{result['run_id']}/cancel",
            params=SESSION,
            content=" " * (64 * 1024 + 1),
        )
        assert response.status_code == 413
        response = client.post(
            f"{BASE}/runs/{result['run_id']}/cancel",
            params=SESSION,
            json={"surprise": True},
        )
        assert response.status_code == 400
        assert client.get(BASE + "/bindings", params=SESSION).json() == {"bindings": []}


def test_running_cancel_is_terminal_and_retains_no_late_output(execution, monkeypatch):
    service, _, _ = execution
    entered, release = threading.Event(), threading.Event()
    original = service.runtime._local_operation

    def paused(*args):
        entered.set()
        assert release.wait(3)
        return original(*args)

    monkeypatch.setattr(service.runtime, "_local_operation", paused)
    with TestClient(app_for(execution), headers=AUTH) as client:
        saved = save(client, document())
        created = client.post(
            f"{BASE}/{saved['definition']['id']}/runs",
            params=SESSION,
            json=submission(saved),
        ).json()
        assert entered.wait(2)
        try:
            cancelled = client.post(
                f"{BASE}/runs/{created['run_id']}/cancel", params=SESSION
            )
            assert (
                cancelled.status_code == 200
                and cancelled.json()["state"] == "cancelled"
            )
            assert wait_run(client, created["run_id"])["artifacts"] == []
        finally:
            release.set()


def test_binding_discovery_check_and_denied_submission_use_current_gateway_policy(
    execution,
):
    from core.native_process import language_contract
    from tool_registry.db import insert_server, insert_tools, update_server
    from tool_registry.models import McpServer, McpTool

    service, gateway, _ = execution
    db = service.repository.db_path
    insert_server(
        db,
        McpServer(
            server_id="api-contract-tool",
            name="api-contract-tool",
            type="stdio",
            command=["never-started-test-fixture"],
            is_installed=True,
            is_active=False,
            status="inactive",
            created_at=1,
            updated_at=1,
        ),
    )
    insert_tools(
        db,
        [
            McpTool(
                tool_id="api-tool-id",
                server_id="api-contract-tool",
                name="measure",
                description="Discovery-only contract fixture",
                input_schema={
                    "type": "object",
                    "properties": {"value": {"type": "number", "minimum": 0.25}},
                },
                output_schema=None,
                is_enabled=True,
                created_at=1,
            )
        ],
    )
    data = {
        "format": "wright-native-process",
        "schema_version": "1.0.0",
        "id": "binding-process",
        "title": "Actual gateway policy preflight",
        "steps": [],
        "ports": [],
        "connections": [],
        "outputs": [],
    }
    for identity, operation, config in [
        ("argument-source", "text.input@1", {"value": '{"value":0.5}'}),
        ("measure-step", "mcp.call@1", {}),
    ]:
        data["steps"].append(
            {
                "id": identity,
                "title": identity,
                "operation": operation,
                "config": config,
            }
        )
        descriptor = next(
            item
            for item in language_contract()["operations"]
            if item["id"] == operation
        )
        for direction in ("input", "output"):
            for port in descriptor[direction + "s"]:
                data["ports"].append(
                    {
                        **port,
                        "id": identity + "-" + port["key"],
                        "step_id": identity,
                        "direction": direction,
                        "label": port["key"],
                    }
                )
    data["connections"] = [
        {
            "id": "argument-edge",
            "source_port_id": "argument-source-value",
            "target_port_id": "measure-step-arguments",
        }
    ]
    with TestClient(app_for(execution), headers=AUTH) as client:
        descriptor = client.get(BASE + "/bindings", params=SESSION).json()["bindings"][
            0
        ]
        assert descriptor["input_schema"]["properties"]["value"]["minimum"] == 0.25
        binding = {
            key: descriptor[key]
            for key in (
                "server_id",
                "tool_name",
                "input_schema_digest",
                "output_schema_digest",
            )
        }
        bindings = {"measure-step": binding}
        checked = client.post(
            BASE + "/check",
            params=SESSION,
            json={"definition": data, "bindings": bindings},
        )
        assert checked.status_code == 200 and checked.json()["ready"], checked.text
        saved = save(client, data)
        update_server(
            db,
            "api-contract-tool",
            {"risk_level": "high", "approval_gates": ["physical-action"]},
        )
        denied = client.post(
            f"{BASE}/{data['id']}/runs",
            params=SESSION,
            json={**submission(saved), "bindings": bindings},
        )
        assert denied.status_code == 403 and denied.json()["code"] == "NATIVE_DENIED"
        assert any(
            item["step_id"] == "measure-step" and item["code"] == "MCP_DENIED"
            for item in denied.json()["findings"]
        )
        assert service.run_history("session-one", data["id"])["runs"] == []
        assert gateway.lifecycle.engine.lifecycle.live_runner_count() == 0


@pytest.mark.asyncio
async def test_scope_is_revalidated_after_async_preflight_before_commit(
    execution, monkeypatch
):
    service, gateway, workspace = execution
    await service.startup()
    try:
        saved = service.save_document(
            "session-one",
            document(),
            {},
            request_id="scope-save",
            expected_token=None,
            trace_id="scope-save",
        )
        original = service._prepare_run

        def shifted(*args):
            result = original(*args)
            service.scope = lambda session: ("two", WorkspacePath(workspace))
            return result

        monkeypatch.setattr(service, "_prepare_run", shifted)
        from workspace_service.native_process_service import NativeServiceError

        with pytest.raises(NativeServiceError) as error:
            await service.start_run(
                "session-one",
                saved["definition"]["id"],
                **submission(saved),
                actor="admin",
                trace_id="scope-run",
            )
        assert error.value.code == "NATIVE_DENIED"
        assert (
            service.repository.history("one", saved["definition"]["id"])["runs"] == []
        )
    finally:
        await service.close()
        await gateway.shutdown()


@pytest.mark.asyncio
async def test_startup_owner_sweep_preserves_indexed_evidence_and_precedes_enqueue(
    execution, monkeypatch
):
    service, gateway, workspace = execution
    await service.startup()
    try:
        saved = service.save_document(
            "session-one",
            document(),
            {},
            request_id="reconcile-save",
            expected_token=None,
            trace_id="reconcile-save",
        )
        submitted = await service.start_run(
            "session-one",
            saved["definition"]["id"],
            **submission(saved),
            actor="admin",
            trace_id="reconcile-run",
        )
        async with asyncio.timeout(5):
            while service.inspect_run("session-one", submitted["run_id"])["state"] in {
                "queued",
                "running",
            }:
                await asyncio.sleep(0.01)
        retained = service.inspect_run("session-one", submitted["run_id"])["artifacts"][
            0
        ]
        store = NativeArtifactStore(WorkspacePath(workspace))
        orphan = store.promote(
            submitted["run_id"],
            b"orphan",
            filename="orphan.txt",
            port_id="unused-port",
            provenance={},
        )
        await service.close()
        from workspace_service.native_process_service import NativeProcessService
        from workspace_service.native_process_runtime import NativeRuntime
        from workspace_service.native_process_mcp import NativeMcpAdapter

        replacement = NativeProcessService(
            service.repository, service.workspace_resolver, service.examples_root
        )
        replacement.configure_execution(
            NativeRuntime(service.repository, replacement.scope),
            NativeMcpAdapter(gateway, service.workspace_resolver),
        )
        original_reconcile = NativeArtifactStore.reconcile

        def checked_reconcile(self, keys):
            assert (
                replacement.runtime._owner is not None
                and not replacement.runtime._tasks
            )
            return original_reconcile(self, keys)

        monkeypatch.setattr(NativeArtifactStore, "reconcile", checked_reconcile)
        try:
            report = await replacement.startup()
            assert report == {"removed": 1, "residue": []}
            assert not (workspace / orphan["storage_key"]).exists()
            record, content = replacement.run_artifact(
                "session-one", submitted["run_id"], retained["artifact_id"]
            )
            assert hashlib.sha256(content).hexdigest() == record["content_digest"]
        finally:
            await replacement.close()
    finally:
        await service.close()
        await gateway.shutdown()
