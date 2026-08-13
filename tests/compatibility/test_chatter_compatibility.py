from __future__ import annotations

from pathlib import Path

import pytest

from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)
from model_registry.runtime import (
    RuntimeFailure,
    RuntimeSupervisor,
    built_in_runtime_registry,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_chatter_runtime_rejects_an_incompatible_host_before_launch(
    tmp_path,
) -> None:
    package = generated_chatter_package()
    paths = {}
    for name, value in chatter_fixture_artifacts(package).items():
        target = tmp_path.joinpath("artifacts", *name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
        paths[name] = target
    supervisor = RuntimeSupervisor(
        built_in_runtime_registry(), scratch_root=tmp_path / "runtime"
    )
    with pytest.raises(RuntimeFailure) as caught:
        await supervisor.start_session(
            adapter_id="wright-chatter-forest-numpy",
            installation_id="installation-chatter",
            artifacts=paths,
            model_format="wright-chatter-forest-npz-1.0",
            task_id="screen_chatter_candidates",
            platform="unsupported-platform",
            architecture="unsupported-architecture",
            execution_provider="cpu",
        )
    assert caught.value.category == "incompatible_provider"
    assert supervisor.active_process_count == 0


def test_generic_rivet_and_gateway_files_do_not_branch_on_chatter_model_identity() -> (
    None
):
    generic_files = (
        "packages/tool_registry/src/tool_registry/gateway_service.py",
        "packages/workspace_service/src/workspace_service/workflow_runner.py",
        "packages/workspace_service/src/workspace_service/rivet_capabilities.py",
        "packages/workspace_service/src/workspace_service/engineering_scenario_service.py",
        "apps/web/src/components/chat/RivetScenarioLibrary.tsx",
        "apps/web/src/components/chat/RivetScenarioReport.tsx",
    )
    forbidden = ("wright-chatter-generated-test", "screen_chatter_candidates")
    for relative in generic_files:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert not any(value in source for value in forbidden), relative


def test_packaged_chatter_workflow_uses_only_static_reviewed_tool_names() -> None:
    workflow = (
        ROOT
        / "packages/workspace_service/src/workspace_service/engineering_scenario_catalog/workflows/chatter-candidate-review.rivet-project"
    ).read_text(encoding="utf-8")
    assert "useToolNameInput: false" in workflow
    assert "useServerUrlInput: false" in workflow
    assert "toolName:" in workflow
