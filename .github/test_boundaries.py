from importlib import import_module
from types import SimpleNamespace
import sys

import pytest

from check_installed import CheckCommercialImports, CheckLocalConnections, check_packages, check_source
from test_distribution import verify


def test_unreviewed_filenames_fail_before_installation(tmp_path):
    (tmp_path / "wright_workflow-1.2.3-py3-none-any.whl").touch()
    (tmp_path / "wright_workflow-1.2.3.tar.gz").touch()
    with pytest.raises(ValueError, match="exactly the reviewed wheel and sdist"):
        verify(tmp_path)


def test_static_import_in_an_unused_branch_is_checked(tmp_path):
    source = tmp_path / "example.py"
    source.write_text("if False:\n    from wright_pro import workspace\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unreviewed module: wright_pro"):
        check_source(source)


def test_optional_dynamic_import_is_recorded(monkeypatch):
    guard = CheckCommercialImports()
    monkeypatch.setattr(sys, "meta_path", [guard, *sys.meta_path])
    with pytest.raises(ModuleNotFoundError):
        import_module("wright_pro")
    assert guard.attempted == {"wright_pro"}


def test_transitive_private_distribution_is_rejected():
    engine = SimpleNamespace(requires=["jsonschema", "mcp", "pydantic"])
    report = {"install": [{"metadata": {"name": name}} for name in ("wright_workflow", "wright_pro")]}
    with pytest.raises(ValueError, match="Commercial distribution.*wright-pro"):
        check_packages(report, engine)


def test_network_observer_allows_loopback_and_rejects_external_lookup():
    observer = CheckLocalConnections()
    observer("socket.getaddrinfo", ("localhost", 80))
    observer("socket.connect", (None, ("::1", 80, 0, 0)))
    observer("socket.connect", (None, ("127.0.0.1", 80)))
    with pytest.raises(RuntimeError, match="External network access"):
        observer("socket.getaddrinfo", ("catalog.example.invalid", 80))
    assert observer.attempted == {"catalog.example.invalid"}
