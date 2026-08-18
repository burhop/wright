from __future__ import annotations

import subprocess
import stat
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from tool_registry.windows_qualification_executor import (
    ProcessResult,
    QualificationExecutionContext,
    QualificationExecutionError,
    WindowsQualificationExecutor,
    validate_isolated_root,
)
from tool_registry.windows_qualification_recipes import (
    get_windows_qualification_recipe,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "windows_qualification" / "helper_process.py"
)


def _context(tmp_path: Path) -> QualificationExecutionContext:
    root = tmp_path / "windows-mcp-qualification"
    root.mkdir()
    return QualificationExecutionContext(work_root=root, server_id="brep-mcp")


def test_process_launch_never_uses_a_command_shell(tmp_path: Path) -> None:
    calls: list[dict] = []

    def popen(argv, **kwargs):
        calls.append({"argv": argv, **kwargs})
        return subprocess.Popen(argv, **kwargs)

    executor = WindowsQualificationExecutor(popen_factory=popen)
    result = executor._run_process(
        [sys.executable, str(FIXTURE), "clean"],
        cwd=_context(tmp_path).work_root,
        timeout_seconds=5,
        output_limit_bytes=4096,
    )

    assert result.exit_code == 0
    assert calls[0]["shell"] is False
    assert isinstance(calls[0]["argv"], list)


def test_process_output_is_bounded_and_raw_output_is_not_returned(
    tmp_path: Path,
) -> None:
    executor = WindowsQualificationExecutor()
    result = executor._run_process(
        [sys.executable, str(FIXTURE), "oversized-output"],
        cwd=_context(tmp_path).work_root,
        timeout_seconds=5,
        output_limit_bytes=4096,
    )

    assert result.output_bytes > 4096
    assert result.output_truncated is True
    assert len(result.output_digest) == 64
    assert not hasattr(result, "stdout")


def test_stdio_diagnostics_are_discarded_instead_of_persisted() -> None:
    source = Path(
        WindowsQualificationExecutor._probe_stdio_async.__code__.co_filename
    ).read_text(encoding="utf-8")

    assert "open(os.devnull" in source
    assert "StringIO" not in source


def test_brep_probe_is_bound_to_one_reviewed_program() -> None:
    recipe = get_windows_qualification_recipe("brep-mcp")

    arguments = WindowsQualificationExecutor._brep_probe_arguments(recipe)

    assert set(arguments) == {"code", "timeoutMs"}
    assert arguments["timeoutMs"] == 30000
    assert "box(1, 1, 1)" in str(arguments["code"])


def test_probe_failure_does_not_erase_startup_and_protocol_passes() -> None:
    recipe = get_windows_qualification_recipe("brep-mcp")
    tool = SimpleNamespace(
        name="run_program",
        model_dump=lambda **kwargs: {
            "name": "run_program",
            "inputSchema": {"type": "object"},
        },
    )
    initialized = SimpleNamespace(
        serverInfo=SimpleNamespace(name="brep-mcp", version="0.103.0")
    )

    evidence = WindowsQualificationExecutor._mcp_evidence(
        recipe,
        initialized,
        SimpleNamespace(tools=[tool]),
        None,
        "safe_probe_execution_failed",
    )

    assert [item.result for item in evidence] == ["passed", "passed", "failed"]


def test_timeout_stops_owned_process_tree(tmp_path: Path) -> None:
    executor = WindowsQualificationExecutor()
    result = executor._run_process(
        [sys.executable, str(FIXTURE), "child-process"],
        cwd=_context(tmp_path).work_root,
        timeout_seconds=1,
        output_limit_bytes=4096,
    )

    assert result.timed_out is True
    assert result.terminated_processes >= 1
    time.sleep(0.1)
    assert not psutil.pid_exists(result.pid)


def test_root_validation_rejects_broad_or_unmarked_paths(tmp_path: Path) -> None:
    with pytest.raises(QualificationExecutionError, match="dedicated"):
        validate_isolated_root(tmp_path)
    with pytest.raises(QualificationExecutionError):
        validate_isolated_root(Path.home())

    safe = tmp_path / "windows-mcp-qualification" / "brep-mcp"
    assert validate_isolated_root(safe) == safe.resolve()


def test_destination_policy_accepts_only_recipe_origins(tmp_path: Path) -> None:
    executor = WindowsQualificationExecutor()
    recipe = get_windows_qualification_recipe("autodesk-product-help-mcp")
    executor.validate_destination(
        recipe, "https://developer.api.autodesk.com/knowledge/public/v1/mcp"
    )

    with pytest.raises(QualificationExecutionError, match="destination"):
        executor.validate_destination(recipe, "https://example.invalid/mcp")


def test_executor_denies_nonallowlisted_identity_before_dispatch(
    tmp_path: Path,
) -> None:
    executor = WindowsQualificationExecutor()
    context = _context(tmp_path)
    context = QualificationExecutionContext(
        work_root=context.work_root, server_id="unreviewed-mcp"
    )

    with pytest.raises(QualificationExecutionError, match="allowlist"):
        executor.execute_identity(context)


def test_cleanup_removes_read_only_git_files_inside_validated_root(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    context.server_root.mkdir()
    pack = context.server_root / "source" / ".git" / "objects" / "pack"
    pack.mkdir(parents=True)
    artifact = pack / "pack-fixture.idx"
    artifact.write_bytes(b"fixture")
    artifact.chmod(stat.S_IREAD)

    assert WindowsQualificationExecutor().remove_isolated_server_root(context)
    assert not context.server_root.exists()


def test_dotnet_build_restores_only_from_reviewed_nuget_origin(
    tmp_path: Path, monkeypatch
) -> None:
    recipe = get_windows_qualification_recipe("solid-edge-mcp-burhop")
    operation = next(
        item for item in recipe.operations if item.kind == "dotnet_local_build"
    )
    work_root = tmp_path / "windows-mcp-qualification"
    context = QualificationExecutionContext(work_root, recipe.server_id)
    project = (
        context.server_root
        / "source"
        / "src"
        / "SolidEdgeMcpServer"
        / "SolidEdgeMcpServer.csproj"
    )
    project.parent.mkdir(parents=True)
    project.write_text("<Project />", encoding="utf-8")
    monkeypatch.setattr("shutil.which", lambda name: "dotnet.exe")

    class RecordingExecutor(WindowsQualificationExecutor):
        def __init__(self) -> None:
            super().__init__()
            self.commands: list[list[str]] = []

        def _run_process(self, argv, **kwargs):
            self.commands.append(list(argv))
            if "build" in argv:
                application = context.server_root / "application"
                application.mkdir()
                (application / "SolidEdgeMcpServer.exe").write_bytes(b"fixture")
            return ProcessResult(
                pid=1,
                exit_code=0,
                timed_out=False,
                output_bytes=0,
                output_digest="0" * 64,
                output_truncated=False,
                duration_ms=0,
                terminated_processes=0,
            )

    executor = RecordingExecutor()
    outcome = executor._build_dotnet(recipe, operation, context)

    assert outcome.evidence[0].result == "passed"
    assert executor.commands[0][1] == "restore"
    assert "https://api.nuget.org/v3/index.json" in executor.commands[0]
    assert "--no-restore" in executor.commands[1]


def test_known_upstream_probe_failures_have_stable_safe_codes() -> None:
    solid_edge = ExceptionGroup(
        "outer",
        [
            RuntimeError(
                "Invalid structured content returned by tool cad.get_status: "
                "'activeDocument' is a required property"
            )
        ],
    )
    brep = RuntimeError("The URL must be of scheme file")

    assert (
        WindowsQualificationExecutor._probe_failure_code(
            solid_edge, "solid-edge-mcp-burhop"
        )
        == "safe_probe_output_schema_mismatch"
    )
    assert (
        WindowsQualificationExecutor._probe_failure_code(brep, "brep-mcp")
        == "safe_probe_upstream_entrypoint_defect"
    )


def test_product_help_wright_setup_preserves_external_terms_boundary(
    tmp_path: Path,
) -> None:
    recipe = get_windows_qualification_recipe("autodesk-product-help-mcp")
    operation = next(
        item for item in recipe.operations if item.kind == "wright_onboarding"
    )

    outcome = WindowsQualificationExecutor().execute_operation(
        recipe,
        operation,
        QualificationExecutionContext(
            tmp_path / "windows-mcp-qualification", recipe.server_id
        ),
    )

    assert outcome.evidence[0].result == "partial"
    assert outcome.evidence[0].reason_code == "wright_external_license_incomplete"
    assert outcome.evidence[0].missing_requirements == ["publisher_terms"]
