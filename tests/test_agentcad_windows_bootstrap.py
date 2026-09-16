import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/engineering/agentcad_windows_bootstrap.py"
spec = importlib.util.spec_from_file_location("agentcad_bootstrap", SOURCE)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def test_numpy_load_completes_before_mcp_can_start_stdin_reader(monkeypatch):
    events = []
    monkeypatch.setattr(bootstrap.sys, "platform", "win32")
    monkeypatch.setattr(bootstrap.importlib.metadata, "version", bootstrap.EXPECTED_VERSIONS.__getitem__)
    monkeypatch.setattr(bootstrap.importlib, "import_module", lambda name: events.append(("import_complete", name)))
    monkeypatch.setattr(bootstrap.runpy, "run_module", lambda name, **kwargs: events.append(("start", name, kwargs)))
    bootstrap.main()
    assert events == [("import_complete", "numpy"), ("import_complete", "build123d"),
                      ("start", "agentcad.mcp", {"run_name": "__main__"})]


@pytest.mark.parametrize("failure", ["version", "numpy_import", "platform"])
def test_unqualified_or_failed_initialization_never_starts_mcp(monkeypatch, failure):
    events = []
    monkeypatch.setattr(bootstrap.sys, "platform", "linux" if failure == "platform" else "win32")
    monkeypatch.setattr(bootstrap.importlib.metadata, "version",
                        lambda name: "different" if failure == "version" else bootstrap.EXPECTED_VERSIONS[name])
    def importing(name):
        raise ImportError("Native NumPy initialization failed")
    monkeypatch.setattr(bootstrap.importlib, "import_module", importing)
    monkeypatch.setattr(bootstrap.runpy, "run_module", lambda *args, **kwargs: events.append("started"))
    with pytest.raises((RuntimeError, ImportError)):
        bootstrap.main()
    assert not events
