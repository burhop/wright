import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    "demo_agentcad_config", Path(__file__).parents[1] / "scripts/configure-agentcad-demo-bootstrap.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def prepare(root):
    source = root / "sources/qualified/bootstrap.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# synthetic test source; never executed\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    command = ["uv", "run", "--no-project", "--isolated", "--python", "3.12.11",
               "--with", "agentcad[mcp]==0.6.0", "--with", "numpy==2.5.2",
               "--with", "build123d==0.10.0", "python", "-B", str(source)]
    proof = dict(snapshot=str(source), bootstrap_sha256=digest, command=command,
                 status="passed", continuous_open_stdin=True, native_status="success")
    evidence = root / "agentcad-bootstrap-qualification/attempt-002"
    evidence.mkdir(parents=True)
    for name in ("qualification.json", "demo-installation.json"):
        (evidence / name).write_text(json.dumps(proof))
    return source, evidence, command


def test_ordinary_demo_never_enables_an_uninstalled_bootstrap(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "get_server", lambda *_: pytest.fail("Unexpected registry read"))
    assert module.configure(tmp_path, tmp_path / "state.db")["configured"] is False


def test_catalog_reconciliation_restores_only_exact_qualified_command(tmp_path, monkeypatch):
    _, _, command = prepare(tmp_path)
    calls = []
    server = SimpleNamespace(is_installed=True, command=["old", "catalog", "default"])
    monkeypatch.setattr(module, "get_server", lambda *_: server)
    monkeypatch.setattr(module, "update_server", lambda *args: calls.append(args))
    assert module.configure(tmp_path, tmp_path / "state.db")["changed"] is True
    assert calls == [(str(tmp_path / "state.db"), "agentcad", {"command": command})]
    server.command = command
    assert module.configure(tmp_path, tmp_path / "state.db")["changed"] is False
    assert len(calls) == 1


@pytest.mark.parametrize("mutation", ["source", "command", "failed", "outside"])
def test_changed_bootstrap_cannot_alter_registry(tmp_path, monkeypatch, mutation):
    source, evidence, _ = prepare(tmp_path)
    proof = json.loads((evidence / "qualification.json").read_text())
    if mutation == "source":
        source.write_bytes(b"different source")
    elif mutation == "command":
        proof["command"] = ["unqualified", "command"]
    elif mutation == "failed":
        proof["native_status"] = "failed"
    else:
        proof["snapshot"] = str(tmp_path / "outside.py")
    (evidence / "qualification.json").write_text(json.dumps(proof))
    monkeypatch.setattr(module, "get_server", lambda *_: pytest.fail("Unexpected registry read"))
    with pytest.raises(ValueError):
        module.configure(tmp_path, tmp_path / "state.db")
