from types import SimpleNamespace

import pytest

from workspace_service.workflow_mcp_source_contracts import (
    AGENTCAD_BUILD123D_010,
    validate_mcp_source_contract,
)
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


def step():
    return SimpleNamespace(
        source_contract=AGENTCAD_BUILD123D_010,
        server_id="agentcad",
        tool_name="agentcad__run",
        title="Generate jig",
        expected_files=(),
    )


def arguments(tmp_path, source):
    project = tmp_path / "agentcad-project"
    project.mkdir(exist_ok=True)
    return {
        "script": str(source.resolve()),
        "output": "pi-comparison",
        "cwd": str(project.resolve()),
        "build_dir": "build",
        "preview": False,
        "view": False,
        "diff": False,
    }


def test_build123d_010_rejects_retained_boolean_property_call_before_dispatch(tmp_path):
    source = tmp_path / "jig-source.py"
    source.write_text(
        "jig = object()\nif not jig.is_valid():\n    raise RuntimeError('invalid')\n",
        encoding="utf-8",
    )

    with pytest.raises(
        WorkflowSourceExecutionError,
        match="line 2 calls build123d is_valid as a function",
    ):
        validate_mcp_source_contract(step(), tmp_path, arguments(tmp_path, source))


def test_build123d_010_accepts_boolean_property_access(tmp_path):
    source = tmp_path / "jig-source.py"
    source.write_text(
        "jig = object()\nif not jig.is_valid:\n    raise RuntimeError('invalid')\n",
        encoding="utf-8",
    )

    receipt = validate_mcp_source_contract(
        step(), tmp_path, arguments(tmp_path, source)
    )
    assert receipt["contract"] == AGENTCAD_BUILD123D_010
    assert receipt["script"] == "jig-source.py"
    assert receipt["script_sha256"]
    assert receipt["headless"] is True


def test_build123d_010_rejects_abstract_shape_cast_before_dispatch(tmp_path):
    source = tmp_path / "bracket-source.py"
    source.write_text(
        "from build123d import Shape\n"
        "result = Shape.cast(splitter.Shape())\n"
        "show_object(result)\n",
        encoding="utf-8",
    )

    with pytest.raises(
        WorkflowSourceExecutionError,
        match=r"line 2 calls abstract build123d Shape\.cast",
    ):
        validate_mcp_source_contract(step(), tmp_path, arguments(tmp_path, source))


def test_build123d_010_accepts_concrete_solid_cast(tmp_path):
    source = tmp_path / "bracket-source.py"
    source.write_text(
        "from build123d import Solid\n"
        "result = Solid.cast(splitter.Shape())\n"
        "show_object(result)\n",
        encoding="utf-8",
    )

    validate_mcp_source_contract(step(), tmp_path, arguments(tmp_path, source))


def test_build123d_010_rejects_hyphen_alias_for_declared_step_output(tmp_path):
    source = tmp_path / "enclosure-source.py"
    source.write_text(
        "suffix = 'a'\npath = f'power-interface-{suffix}.step'\n",
        encoding="utf-8",
    )
    configured = step()
    configured.expected_files = (
        "campaign/pi/artifacts/power_interface-a.step",
        "campaign/pi/artifacts/power_interface-b.step",
    )

    with pytest.raises(
        WorkflowSourceExecutionError,
        match=r"uses 'power-interface-\{\}\.step' instead of the declared",
    ):
        validate_mcp_source_contract(configured, tmp_path, arguments(tmp_path, source))


def test_build123d_010_accepts_declared_step_filename_pattern(tmp_path):
    source = tmp_path / "enclosure-source.py"
    source.write_text(
        "suffix = 'a'\npath = f'power_interface-{suffix}.step'\n",
        encoding="utf-8",
    )
    configured = step()
    configured.expected_files = ("campaign/pi/artifacts/power_interface-a.step",)

    validate_mcp_source_contract(configured, tmp_path, arguments(tmp_path, source))


@pytest.mark.parametrize(
    "patch",
    [
        {"cwd": "relative/project"},
        {"cwd": "../outside"},
        {"build_dir": "../build"},
        {"output": "nested/output"},
        {"preview": True},
        {"view": True},
        {"diff": True},
    ],
)
def test_agentcad_contract_rejects_unsafe_or_interactive_arguments(tmp_path, patch):
    source = tmp_path / "source.py"
    source.write_text("part = object()\n", encoding="utf-8")
    supplied = {**arguments(tmp_path, source), **patch}
    with pytest.raises(WorkflowSourceExecutionError, match="arguments"):
        validate_mcp_source_contract(step(), tmp_path, supplied)
