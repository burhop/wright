from __future__ import annotations

import asyncio
import json
import os
import shutil
import sqlite3
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import workspace_service.rivet_runtime_host as runtime_module
from core.workflow_runs import WorkflowRunState
from data_vault import WorkflowRunRepository, upgrade_database
from agent_adapters.hermes_config import HermesApiSettings

from workspace_service.rivet_runtime_host import RivetRuntimeHost
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from workspace_service.workflow_catalog import WorkflowTemplateCatalog
from workspace_service.workflows import WorkspaceWorkflowStore


_PASSTHROUGH_PROJECT = """version: 4
data:
  attachedData: {}
  graphs:
    graph-1:
      metadata:
        id: graph-1
        name: Main
        description: ""
      nodes:
        '[input-node]:graphInput "Input"':
          data:
            id: input
            dataType: string
            useDefaultValueInput: false
          outgoingConnections:
            - data->"Output" output-node/value
          visualData: 0/0/200/null//
        '[output-node]:graphOutput "Output"':
          data:
            id: output
            dataType: string
          visualData: 300/0/200/null//
  metadata:
    id: project-1
    title: Runtime Host
    description: ""
    mainGraphId: graph-1
  plugins: []
"""


class _CaptureLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **values: object) -> None:
        self.events.append((event, values))


def _supervisor() -> ProcessSupervisor:
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_real_runtime_host_executes_inventoried_rivet_graph_and_relays_progress(
    tmp_path, monkeypatch
) -> None:
    captured = _CaptureLogger()
    monkeypatch.setattr(runtime_module, "logger", captured)
    document = WorkspaceWorkflowStore(str(tmp_path)).create(
        "passthrough", _PASSTHROUGH_PROJECT
    )
    progress: list[dict[str, object]] = []
    host = RivetRuntimeHost(
        supervisor=_supervisor(),
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=20,
            cancellation_seconds=2,
        ),
    )

    result = await host.run(
        run_id="runtime-host-contract",
        workspace_id="workspace-1",
        session_id="session-1",
        workspace_dir=str(tmp_path),
        document=document,
        graph="Main",
        inputs={"input": "hello from Wright"},
        progress_callback=progress.append,
    )

    assert result.state == "succeeded"
    assert result.outputs is not None
    assert result.outputs["output"]["value"] == "hello from Wright"
    assert progress
    assert [event["sequence"] for event in progress] == list(
        range(1, len(progress) + 1)
    )
    assert all(event["runId"] == result.run_id for event in progress)
    assert [event for event, _values in captured.events] == ["rivet_runtime_completed"]
    timing = captured.events[0][1]
    assert timing["run_id"] == result.run_id
    assert timing["duration_ms"] == result.duration_ms
    assert timing["event_count"] == len(progress)
    encoded = json.dumps(captured.events)
    assert "hello from Wright" not in encoded
    assert str(tmp_path) not in encoded


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_shared_runner_persists_exact_identity_progress_and_real_outputs(
    tmp_path,
) -> None:
    document = WorkspaceWorkflowStore(str(tmp_path)).create(
        "durable", _PASSTHROUGH_PROJECT
    )
    settings = RunnerSettings(
        enabled=True,
        real_execution_enabled=True,
        run_timeout_seconds=20,
        cancellation_seconds=2,
    )
    supervisor = _supervisor()
    database = tmp_path / "wright.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
    repository = WorkflowRunRepository(str(database))
    runner = WorkspaceWorkflowRunner(
        supervisor=supervisor,
        settings=settings,
        runtime_host=RivetRuntimeHost(supervisor=supervisor, settings=settings),
        run_repository=repository,
        id_factory=lambda: "durable-run",
    )

    started = await runner.start(
        workspace_id="workspace-1",
        session_id="session-1",
        workspace_dir=str(tmp_path),
        slug="durable",
        expected_revision=document.revision,
        expected_digest=document.digest,
        graph="Main",
        inputs={"input": "persist me"},
    )
    assert started.state is WorkflowRunState.RUNNING

    for _ in range(200):
        completed = runner.get(started.run_id)
        if completed.state in {
            WorkflowRunState.SUCCEEDED,
            WorkflowRunState.FAILED,
        }:
            break
        await asyncio.sleep(0.02)

    assert completed.state is WorkflowRunState.SUCCEEDED
    record = repository.get(started.run_id)
    assert record is not None
    assert (record.revision, record.digest, record.graph) == (
        document.revision,
        document.digest,
        "Main",
    )
    assert record.output_summary is not None
    assert record.output_summary["outputs"]["output"] == "persist me"
    events = repository.events(started.run_id)
    assert [event.kind for event in events[:2]] == [
        "inspection-context",
        "queued",
    ]
    assert events[-1].kind == "completed"


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_ai_node_uses_only_ephemeral_bridge_and_keeps_hermes_key_in_host(
    tmp_path,
) -> None:
    observed: dict[str, object] = {}

    class HermesHandler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            observed["authorization"] = self.headers.get("Authorization")
            payload = json.loads(self.rfile.read(length))
            observed["payload"] = payload
            if payload.get("stream") is True:
                chunks = [
                    {
                        "id": "chatcmpl-test",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "controlled-hermes",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant"},
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        "id": "chatcmpl-test",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "controlled-hermes",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": "AI through Hermes"},
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        "id": "chatcmpl-test",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "controlled-hermes",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    },
                ]
                body = (
                    "".join(
                        f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n"
                        for chunk in chunks
                    )
                    + "data: [DONE]\n\n"
                )
                encoded = body.encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            body = json.dumps(
                {
                    "id": "chatcmpl-test",
                    "object": "chat.completion",
                    "created": 1,
                    "model": "controlled-hermes",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "AI through Hermes",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                }
            ).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    hermes = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
    thread = threading.Thread(target=hermes.serve_forever, daemon=True)
    thread.start()
    try:
        project = WorkflowTemplateCatalog().instantiate("basic-flow")
        document = WorkspaceWorkflowStore(str(tmp_path)).create("ai-flow", project)
        settings = RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=20,
            cancellation_seconds=2,
        )
        supervisor = _supervisor()
        host = RivetRuntimeHost(
            supervisor=supervisor,
            settings=settings,
            hermes_settings_resolver=lambda: HermesApiSettings(
                base_url=f"http://127.0.0.1:{hermes.server_port}",
                api_key="test-secret-long-lived-hermes-key",
                source="test",
            ),
        )
        result = await host.run(
            run_id="ai-runtime-contract",
            workspace_id="workspace-1",
            session_id="session-1",
            workspace_dir=str(tmp_path),
            document=document,
            graph="Simple Chat",
            inputs={"input": "Say hello"},
            requirements=("ai",),
        )

        assert result.state == "succeeded"
        assert result.outputs is not None
        assert result.outputs["output"]["value"] == "AI through Hermes"
        assert observed["authorization"] == "Bearer test-secret-long-lived-hermes-key"
        # The bridge accepted the runner's fixed wright-hermes alias and mapped it
        # to Hermes' own local API model name before the long-lived credential hop.
        assert observed["payload"]["model"] == "hermes"
        diagnostics = supervisor.diagnostics(result.runtime_id)
        assert "test-secret-long-lived-hermes-key" not in json.dumps(diagnostics)
        assert "test-secret-long-lived-hermes-key" not in json.dumps(result.outputs)
    finally:
        hermes.shutdown()
        hermes.server_close()
        thread.join(timeout=2)
