import json
from data_vault import upgrade_database

from tool_registry import McpServer
from tool_registry.db import insert_server
from tool_registry.validation_cli import main
from tool_registry.validation_executor import ValidationExecutionUnavailable


def _init_db(path):
    upgrade_database(path)


def test_validation_cli_mock_executor_writes_evidence(tmp_path):
    db_path = tmp_path / "registry.db"
    _init_db(db_path)
    insert_server(
        str(db_path),
        McpServer(
            server_id="mock-cad",
            name="Mock CAD",
            type="stdio",
            command=["uvx", "mock-cad"],
            is_active=False,
            status="inactive",
            created_at=1,
            updated_at=1,
        ),
    )

    exit_code = main(
        [
            "validate",
            "mock-cad",
            "--db-path",
            str(db_path),
            "--executor",
            "mock",
            "--evidence-dir",
            str(tmp_path / "evidence"),
        ]
    )

    evidence_file = tmp_path / "evidence" / "mock-cad-validation.json"
    data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert data["status"] == "passed"
    assert "not clean-container evidence" in data["diagnostics"]


def test_validation_cli_docker_executor_writes_skipped_evidence(tmp_path, monkeypatch):
    class UnavailableDockerExecutor:
        def __init__(self, container: str) -> None:
            self.container = container

        async def execute(self, plan):
            raise ValidationExecutionUnavailable("docker unavailable in test")

    monkeypatch.setattr(
        "tool_registry.validation_cli.DockerCleanContainerExecutor",
        UnavailableDockerExecutor,
    )

    db_path = tmp_path / "registry.db"
    _init_db(db_path)
    insert_server(
        str(db_path),
        McpServer(
            server_id="docker-cad",
            name="Docker CAD",
            type="stdio",
            command=["uvx", "docker-cad"],
            is_active=False,
            status="inactive",
            created_at=1,
            updated_at=1,
        ),
    )

    exit_code = main(
        [
            "validate",
            "docker-cad",
            "--db-path",
            str(db_path),
            "--executor",
            "docker",
            "--container",
            "ubuntu-x64",
            "--evidence-dir",
            str(tmp_path / "evidence"),
        ]
    )

    data = json.loads(
        (tmp_path / "evidence" / "docker-cad-validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 2
    assert data["status"] == "skipped"
    assert data["follow_up_required"] is True
