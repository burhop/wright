from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from tool_registry.model_library_port import EngineeringModelPortError
from workspace_service import EngineeringModelService


pytestmark = pytest.mark.external_model
ROOT = Path(__file__).resolve().parents[2]


def _input(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"Set {name} for the explicit local Chatter qualification probe")
    path = Path(value).resolve()
    if not path.exists() or path == ROOT or ROOT in path.parents:
        pytest.fail(f"{name} must identify reviewed input outside the Wright checkout")
    return path


@pytest.mark.asyncio
async def test_exact_local_chatter_qualification_lifecycle(tmp_path) -> None:
    if os.environ.get("WRIGHT_CHATTER_QUALIFY") != "1":
        pytest.skip("Set WRIGHT_CHATTER_QUALIFY=1 to authorize local qualification")
    source = _input("WRIGHT_CHATTER_SOURCE")
    data_vault_source = _input("WRIGHT_CHATTER_DATA_VAULT_SOURCE")
    dataset = _input("WRIGHT_CHATTER_DATASET2")
    reference_evidence = _input("WRIGHT_CHATTER_REFERENCE_EVIDENCE")
    environment_lock = _input("WRIGHT_CHATTER_ENVIRONMENT_LOCK")
    output = tmp_path / "qualification-output"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/qualification/qualify-chatter-model.py"),
            "--source",
            str(source),
            "--data-vault-source",
            str(data_vault_source),
            "--dataset",
            str(dataset),
            "--reference-evidence",
            str(reference_evidence),
            "--environment-lock",
            str(environment_lock),
            "--output",
            str(output),
            "--acknowledge-internal-only",
            "I-UNDERSTAND-NO-REDISTRIBUTION",
        ],
        cwd=ROOT,
        check=True,
        env={
            key: value
            for key, value in os.environ.items()
            if key.lower()
            not in {"http_proxy", "https_proxy", "all_proxy", "aws_profile"}
        },
        timeout=600,
    )
    archive = output / "wright-chatter-local.wright-model.zip"
    assert archive.is_file()

    database = tmp_path / "chatter-state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-chatter', 'session-chatter', ?, 1, 1)""",
            (str(tmp_path),),
        )
    store = ModelArtifactStore(tmp_path / "model-data")
    service = EngineeringModelService(
        repository=ModelRepository(str(database)), artifact_store=store
    )
    plan = service.create_import_plan(
        archive=archive.read_bytes(), principal_id="engineer-chatter"
    )
    assert plan["state"] == "confirmable"
    installed = service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-chatter",
        plan_digest=plan["plan_digest"],
        trace_id="trace-chatter-import",
    )
    installation_id = installed["result"]["installation_id"]
    tested = await service.run_standard_test(
        installation_id,
        principal_id="engineer-chatter",
        trace_id="trace-chatter-test",
    )
    assert tested["installation_state"] == "ready"
    binding = service.create_workspace_binding(
        installation_id,
        task_id="screen_chatter_candidates",
        workspace_id="workspace-chatter",
        principal_id="engineer-chatter",
    )
    package, variant = service._installation_package(
        service.repository.get_installation(installation_id)
    )
    response = await service.invoke_model_capability(
        principal_id="engineer-chatter",
        workspace_id="workspace-chatter",
        session_id="session-chatter",
        request_id="request-chatter",
        trace_id="trace-chatter-infer",
        tool_name=binding["tool_name"],
        binding_digest=binding["binding_digest"],
        arguments=variant.test_vectors[0].input,
        approval_context={},
        progress_callback=None,
    )
    assert (
        response["structuredContent"]["model_evidence"]["model_id"] == package.model_id
    )

    with pytest.raises(EngineeringModelPortError):
        service.create_plan(
            operation_kind="export",
            installation_id=installation_id,
            principal_id="engineer-chatter",
        )
    service.set_workspace_binding_state(
        binding["binding_id"],
        state="disabled",
        workspace_id="workspace-chatter",
        principal_id="engineer-chatter",
    )
    for kind in ("disable", "uninstall", "purge"):
        maintenance = service.create_plan(
            operation_kind=kind,
            installation_id=installation_id,
            principal_id="engineer-chatter",
        )
        result = service.confirm_plan(
            maintenance["plan_id"],
            principal_id="engineer-chatter",
            plan_digest=maintenance["plan_digest"],
            trace_id=f"trace-chatter-{kind}",
        )
        assert result["state"] == "succeeded"
    assert not tuple((store.root / "runtime-scratch").glob("runtime-*"))
