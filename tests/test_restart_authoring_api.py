"""Pure ownership checks for the optional operator restart helper: no signals."""

from pathlib import Path
import hashlib
import io
import urllib.error

import pytest

from scripts.recovery import restart_authoring_api as helper
from scripts.recovery.restart_authoring_api import validate_api_process_command


def test_local_snapshot_preserves_invalid_workflow_bytes_and_detects_changes(tmp_path):
    folder = tmp_path / "workflows"
    folder.mkdir()
    path = folder / "old.workflow.wflow"
    path.write_bytes(b"not valid workflow syntax")
    before = helper.snapshot_local_workflows(tmp_path)
    assert before == {
        "workflows/old.workflow.wflow": hashlib.sha256(path.read_bytes()).hexdigest()
    }
    path.write_bytes(b"changed invalid source")
    assert helper.snapshot_local_workflows(tmp_path) != before


@pytest.mark.parametrize(
    "status,code,known,allowed",
    [
        (503, "workflow_source_integrity", True, True),
        (503, "workflow_source_integrity", False, False),
        (503, "workspace_timeout", True, False),
        (500, "workflow_source_integrity", True, False),
    ],
)
def test_only_fingerprinted_preexisting_integrity_errors_allow_preservation(
    status, code, known, allowed
):
    error = urllib.error.HTTPError(
        "http://127.0.0.1/local",
        status,
        "error",
        {},
        io.BytesIO(('{"error_code":"' + code + '"}').encode()),
    )
    assert (
        helper.preserved_integrity_error(
            error,
            "workflows/old.workflow.wflow",
            {"workflows/old.workflow.wflow": "a" * 64} if known else {},
        )
        is allowed
    )


def command(repo: Path, *, python_wrapper: bool = True) -> list[str]:
    prefix = [str(repo / ".venv/Scripts/uvicorn.exe")]
    if python_wrapper:
        prefix.insert(0, str(repo / ".venv/Scripts/python.exe"))
    return [*prefix, "api.main:app", "--host", "127.0.0.1", "--port", "8018"]


@pytest.mark.parametrize("python_wrapper", [False, True])
def test_exact_owned_api_command_is_accepted(tmp_path, python_wrapper):
    validate_api_process_command(
        tmp_path,
        8018,
        command(tmp_path, python_wrapper=python_wrapper),
        tmp_path / "apps/api",
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda values: [values[0] + ".unrelated", *values[1:]],
        lambda values: [values[0], values[1] + ".unrelated", *values[2:]],
        lambda values: [values[0], "--note=" + values[1], *values[2:]],
        lambda values: [*values, "--reload"],
        lambda values: [*values, "--port", "8018"],
        lambda values: [*values[:-1], "9999", "--note", "8018"],
        lambda values: [*values[:4], "0.0.0.0", *values[5:]],
        lambda values: [*values[:2], "unrelated.main:app", *values[3:]],
        lambda values: [],
    ],
)
def test_similar_or_changed_process_commands_are_rejected(tmp_path, mutation):
    with pytest.raises(RuntimeError, match="exact owned API"):
        validate_api_process_command(
            tmp_path, 8018, mutation(command(tmp_path)), tmp_path / "apps/api"
        )


def test_wrong_working_directory_is_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="exact owned API"):
        validate_api_process_command(tmp_path, 8018, command(tmp_path), tmp_path)


def test_exact_source_tree_module_launcher_is_accepted_without_extra_flags(tmp_path):
    module = [
        str(tmp_path / ".venv/Scripts/python.exe"),
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    validate_api_process_command(tmp_path, 8000, module, tmp_path)
    for changed in [
        module + ["--reload"],
        [*module[:-1], "8001"],
        ["python", *module[1:]],
    ]:
        with pytest.raises(RuntimeError, match="exact owned API"):
            validate_api_process_command(tmp_path, 8000, changed, tmp_path)
    with pytest.raises(RuntimeError, match="exact owned API"):
        validate_api_process_command(tmp_path, 8000, module, tmp_path / "apps/api")


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_invalid_listening_port_is_rejected(tmp_path, port):
    with pytest.raises(RuntimeError, match="exact owned API"):
        validate_api_process_command(
            tmp_path, port, command(tmp_path), tmp_path / "apps/api"
        )


def test_code_identity_requires_clean_committed_source(tmp_path, monkeypatch):
    monkeypatch.setattr(
        helper,
        "git_output",
        lambda _repo, *args: " M changed.py" if args[0] == "status" else "",
    )
    with pytest.raises(RuntimeError, match="clean committed"):
        helper.snapshot_code_identity(tmp_path)


def test_code_identity_records_commit_tree_and_exact_source_hashes(
    tmp_path, monkeypatch
):
    for relative in (*helper.BACKEND_SOURCE_FILES, helper.OPERATOR_SOURCE_FILE):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())

    def git(_repo, *args):
        if args == ("rev-parse", "HEAD"):
            return "a" * 40
        if args == ("rev-parse", "HEAD^{tree}"):
            return "b" * 40
        return ""

    monkeypatch.setattr(helper, "git_output", git)
    result = helper.snapshot_code_identity(tmp_path)
    assert result["git_commit"] == "a" * 40
    assert result["git_tree"] == "b" * 40
    assert result["tracked_worktree_clean"] is True
    assert result["backend_files"] == [
        {"path": relative, "sha256": hashlib.sha256(relative.encode()).hexdigest()}
        for relative in helper.BACKEND_SOURCE_FILES
    ]


def test_module_origin_validation_rejects_another_checkout(tmp_path):
    origins = {
        name: str(tmp_path / relative)
        for name, relative in helper.MODULE_SOURCE_FILES.items()
    }
    origins["api.main"] = str(tmp_path / "elsewhere/api/main.py")
    with pytest.raises(RuntimeError, match="expected checkout"):
        helper.validate_module_origins(tmp_path, origins)


def test_module_origin_validation_hashes_only_expected_source_paths(tmp_path):
    origins = {}
    for name, relative in helper.MODULE_SOURCE_FILES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        origins[name] = str(path)
    result = helper.validate_module_origins(tmp_path, origins)
    assert result == {
        name: {
            "path": origins[name],
            "sha256": hashlib.sha256(name.encode()).hexdigest(),
        }
        for name in origins
    }


def test_origin_probe_uses_same_runtime_environment_and_cwd_without_app_imports(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace
    import json

    origins = {}
    for name, relative in helper.MODULE_SOURCE_FILES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# source only")
        origins[name] = str(path)
    environment = {"PRIVATE_VALUE": "must remain in memory"}
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(origins), stderr="")

    monkeypatch.setattr(helper.subprocess, "run", run)
    result = helper.probe_module_origins(tmp_path, environment)
    args, kwargs = calls[0]
    assert args[:3] == [str(tmp_path / ".venv/Scripts/python.exe"), "-B", "-c"]
    assert kwargs["env"] is environment
    assert kwargs["cwd"] == tmp_path / "apps/api"
    assert "import api" not in args[3]
    assert "import workspace_service" not in args[3]
    assert "PathFinder.find_spec" in args[3]
    assert "PRIVATE_VALUE" not in str(result)


def test_nested_module_origin_probe_never_imports_application_packages(
    tmp_path, monkeypatch, capsys
):
    from importlib.machinery import ModuleSpec
    import importlib.machinery
    import importlib.util
    import json

    top_level_calls = []
    nested_calls = []

    def package_spec(name):
        spec = ModuleSpec(name, None, is_package=True)
        spec.submodule_search_locations = [str(tmp_path / name.replace(".", "/"))]
        return spec

    def top_level(name):
        assert "." not in name, "Dotted util.find_spec would import the parent"
        top_level_calls.append(name)
        return package_spec(name)

    def nested(name, parent_paths):
        parent = name.rsplit(".", 1)[0]
        assert parent_paths == [str(tmp_path / parent.replace(".", "/"))]
        nested_calls.append(name)
        if name in helper.MODULE_SOURCE_FILES:
            return ModuleSpec(
                name, None, origin=str(tmp_path / helper.MODULE_SOURCE_FILES[name])
            )
        return package_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", top_level)
    monkeypatch.setattr(importlib.machinery.PathFinder, "find_spec", nested)
    exec(helper.MODULE_ORIGIN_PROBE, {})
    origins = json.loads(capsys.readouterr().out)
    assert origins == {
        name: str((tmp_path / relative).resolve())
        for name, relative in helper.MODULE_SOURCE_FILES.items()
    }
    assert set(top_level_calls) == {"api", "agent_adapters", "workspace_service"}
    assert "api.routers" in nested_calls


def test_untracked_adapter_source_prevents_provenance(tmp_path, monkeypatch):
    def git(_repo, *args):
        if "--others" in args:
            assert "packages/agent_adapters/src" in args
            return "packages/agent_adapters/src/shadow.py"
        return ""

    monkeypatch.setattr(helper, "git_output", git)
    with pytest.raises(RuntimeError, match="clean committed"):
        helper.snapshot_code_identity(tmp_path)


def test_code_change_during_origin_probe_is_rejected(tmp_path, monkeypatch):
    snapshots = iter([{"git_commit": "before"}, {"git_commit": "after"}])
    monkeypatch.setattr(helper, "snapshot_code_identity", lambda _repo: next(snapshots))
    monkeypatch.setattr(helper, "probe_module_origins", lambda _repo, _env: {})
    with pytest.raises(RuntimeError, match="changed during"):
        helper.capture_code_provenance(tmp_path, {})


def test_untracked_backend_source_prevents_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(
        helper,
        "git_output",
        lambda _repo, *args: "apps/api/src/shadow.py" if "--others" in args else "",
    )
    with pytest.raises(RuntimeError, match="clean committed"):
        helper.snapshot_code_identity(tmp_path)


def test_origin_hash_must_match_the_committed_source_snapshot(tmp_path, monkeypatch):
    snapshot = {
        "backend_files": [
            {"path": value, "sha256": "before"} for value in helper.BACKEND_SOURCE_FILES
        ]
    }
    monkeypatch.setattr(helper, "snapshot_code_identity", lambda _repo: snapshot)
    monkeypatch.setattr(
        helper,
        "probe_module_origins",
        lambda _repo, _env: {
            name: {"sha256": "different"} for name in helper.MODULE_SOURCE_FILES
        },
    )
    with pytest.raises(RuntimeError, match="changed during"):
        helper.capture_code_provenance(tmp_path, {})


def test_actual_listener_must_belong_to_the_launched_process_tree(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    listener = SimpleNamespace(
        pid=102,
        net_connections=lambda **_kwargs: [
            SimpleNamespace(laddr=SimpleNamespace(port=8018), status="LISTEN")
        ],
        cmdline=lambda: command(tmp_path),
        cwd=lambda: str(tmp_path / "apps/api"),
    )
    launcher = SimpleNamespace(
        pid=101,
        children=lambda **_kwargs: [listener],
        net_connections=lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        helper.psutil,
        "Process",
        lambda pid: (
            launcher if pid == 101 else pytest.fail("Unrelated process was inspected")
        ),
    )
    assert helper.find_launched_api_listener(101, tmp_path, 8018) is listener


def test_no_listener_in_launched_tree_fails_without_scanning_unrelated_processes(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    launcher = SimpleNamespace(
        children=lambda **_kwargs: [],
        net_connections=lambda **_kwargs: [],
    )
    monkeypatch.setattr(helper.psutil, "Process", lambda _pid: launcher)
    with pytest.raises(RuntimeError, match="does not own"):
        helper.find_launched_api_listener(101, tmp_path, 8018)
