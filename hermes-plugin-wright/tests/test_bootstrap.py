from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _load_bootstrap(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "bootstrap.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bootstrap_uses_no_git_or_manager_runtime_import() -> None:
    source = (ROOT / "bootstrap.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imported.update(
        node.names[0].name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    )
    assert "wright_engineering" not in imported
    assert "hermes" not in imported
    assert '"git"' not in source.lower()


def test_bootstrap_is_rooted_in_wright_home() -> None:
    source = (ROOT / "bootstrap.py").read_text(encoding="utf-8")
    assert 'os.environ.get("WRIGHT_HOME"' in source
    assert 'os.environ.get("HERMES_HOME"' not in source


def test_local_bootstrap_uses_explicit_complete_wheelhouse(
    tmp_path: Path, monkeypatch
) -> None:
    wheel = tmp_path / "candidate" / "wright_engineering-0.1.5-py3-none-any.whl"
    wheel.parent.mkdir()
    wheel.write_bytes(b"wheel")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    monkeypatch.setenv("WRIGHT_RUNTIME_ARTIFACT", str(wheel))
    monkeypatch.setenv("WRIGHT_RUNTIME_WHEELHOUSE", str(wheelhouse))
    module = _load_bootstrap("wright_bootstrap_wheelhouse_test")
    try:
        target, options = module._install_target()
    finally:
        sys.modules.pop(module.__name__, None)
    assert wheel.as_uri() in target
    assert options == ["--no-index", "--find-links", str(wheelhouse.resolve())]


def test_windows_adapter_removal_clears_read_only_git_pack_files(
    tmp_path: Path, monkeypatch
) -> None:
    host_is_windows = os.name == "nt"
    module = _load_bootstrap("wright_bootstrap_remove_test")
    plugin = tmp_path / "plugin"
    pack = plugin / ".git" / "objects" / "pack"
    pack.mkdir(parents=True)
    index = pack / "candidate.idx"
    index.write_bytes(b"index")
    index.chmod(stat.S_IREAD)
    monkeypatch.setattr(module, "_is_windows", lambda: True)
    try:
        module._prepare_adapter_removal(plugin)
    finally:
        sys.modules.pop(module.__name__, None)

    if host_is_windows:
        assert not index.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY
    else:
        assert index.stat().st_mode & stat.S_IWUSR


def test_bootstrap_builds_venv_at_final_path_for_working_console_scripts(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_bootstrap("wright_bootstrap_final_path_test")
    root = tmp_path / "wright-home"
    environment = module.bootstrap_environment(root)
    python = module._environment_python(environment)
    calls = []

    def fake_run(command, *, env, require_success=True):
        calls.append(list(command))
        if command[1:4] == ["-m", "venv", "--copies"]:
            assert Path(command[4]) == environment
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_bytes(b"python")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module, "wright_home", lambda: root)
    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(
        module,
        "_install_target",
        lambda: ("wright-engineering==0.1.8", []),
    )
    try:
        assert module.ensure_bootstrap() == python
    finally:
        sys.modules.pop(module.__name__, None)

    assert calls[1][0] == str(python)
    assert (environment / ".wright-bootstrap-ready").is_file()
