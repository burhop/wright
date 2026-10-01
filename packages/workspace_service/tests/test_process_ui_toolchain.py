"""Compiler discovery is native configuration, never generated launch data."""

from pathlib import Path

import pytest

from workspace_service.process_interfaces import toolchain as module
from workspace_service.process_interfaces.build import BuildToolchain
from workspace_service.process_interfaces.errors import ProcessInterfaceError


def test_checkout_discovers_only_the_qualified_local_envelope(monkeypatch):
    monkeypatch.delenv("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT", raising=False)
    configured = module.discover_build_toolchain()
    if not isinstance(configured, BuildToolchain):
        pytest.skip(
            "This installed host has no development compiler; separate installed resource proof applies"
        )
    declared = configured.describe()
    assert declared["packages"]["@wright/process-client"]["version"] == "1.0.0"
    assert declared["packages"]["@wright/ui-kit"]["version"] == "1.0.0"


@pytest.mark.parametrize("missing", ["node", "client", "kit", "dependencies"])
def test_missing_native_resources_report_unavailable_without_installing(
    tmp_path, monkeypatch, missing
):
    monkeypatch.setenv("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT", str(tmp_path))
    for name, path in {
        "dependencies": "node_modules",
        "client": "packages/process_client",
        "kit": "packages/ui_kit",
    }.items():
        if name != missing:
            (tmp_path / path).mkdir(parents=True)
    monkeypatch.setattr(
        module.shutil,
        "which",
        lambda _: None if missing == "node" else str(tmp_path / "node.exe"),
    )
    configured = module.discover_build_toolchain()
    assert isinstance(configured, module.UnavailableBuildToolchain)
    with pytest.raises(ProcessInterfaceError, match="compiler is unavailable"):
        configured.describe()
    assert not (tmp_path / "package-lock.json").exists()


def test_native_override_is_not_assumed_qualified_by_directory_presence(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT", str(tmp_path))
    node = tmp_path / "node.exe"
    node.write_bytes(b"not executed")
    monkeypatch.setattr(module.shutil, "which", lambda _: str(node))
    for path in ("node_modules", "packages/process_client", "packages/ui_kit"):
        (tmp_path / path).mkdir(parents=True)
    configured = module.discover_build_toolchain()
    assert isinstance(configured, BuildToolchain) and configured.node == Path(node)
    with pytest.raises(ProcessInterfaceError):
        configured.describe()


def test_installed_without_native_configuration_never_guesses_an_ancestor_checkout(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT", raising=False)
    monkeypatch.setattr(
        module,
        "__file__",
        str(tmp_path / "installed/workspace_service/process_interfaces/toolchain.py"),
    )
    configured = module.discover_build_toolchain()
    assert isinstance(configured, module.UnavailableBuildToolchain)


def test_installed_missing_public_resources_cannot_borrow_source_from_native_dependency_root(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT", str(tmp_path))
    monkeypatch.setattr(
        module,
        "__file__",
        str(tmp_path / "installed/workspace_service/process_interfaces/toolchain.py"),
    )
    monkeypatch.setattr(
        module, "files", lambda _: tmp_path / "missing-packaged-resources"
    )
    monkeypatch.setattr(module.shutil, "which", lambda _: str(tmp_path / "node.exe"))
    for path in ("node_modules", "packages/process_client", "packages/ui_kit"):
        (tmp_path / path).mkdir(parents=True)
    assert isinstance(
        module.discover_build_toolchain(), module.UnavailableBuildToolchain
    )
