import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("kicad_native_check", Path(__file__).parents[1] / "scripts/kicad_campaign/native_rule_check.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


@pytest.mark.parametrize("kind", ["erc", "drc"])
def test_report_retains_native_errors_and_exact_bytes(tmp_path, monkeypatch, kind):
    source = tmp_path / ("board.kicad_sch" if kind == "erc" else "board.kicad_pcb")
    source.write_text("native source fixture")
    issue = {"severity": "error", "description": "Actual detected connection fault"}
    payload = {"sheets": [{"violations": [issue]}]} if kind == "erc" else {"violations": [], "unconnected_items": [issue], "schematic_parity": []}
    raw = json.dumps(payload, indent=3).encode()
    def run(command, **kwargs):
        assert command[:3] == ["kicad-cli", "sch" if kind == "erc" else "pcb", kind]
        assert kwargs["timeout"] == 90
        Path(command[6]).write_bytes(raw)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(native.subprocess, "run", run)
    result = native.check(kind, str(source), str(tmp_path / "report.json"), root=tmp_path)
    assert result["error_count"] == 1 and result["issue_count"] == 1
    assert (tmp_path / "report.json").read_bytes() == raw
    assert result["produced_files"][0]["output_bytes"] == len(raw)


@pytest.mark.parametrize("failure", ["escape", "existing", "wrong_type", "changed_source", "missing_report", "failed_cli"])
def test_native_check_rejects_unsafe_or_unproven_report(tmp_path, monkeypatch, failure):
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "board.kicad_pcb"
    source.write_text("native source fixture")
    target = root / "report.json"
    if failure == "escape":
        target = tmp_path / "escaped.json"
    elif failure == "existing":
        target.write_text("previous report")
    elif failure == "wrong_type":
        source = root / "unreviewed.py"
        source.write_text("not KiCad")
    def run(command, **kwargs):
        assert failure in {"changed_source", "missing_report", "failed_cli"}
        if failure != "missing_report":
            Path(command[6]).write_text('{"violations":[],"unconnected_items":[]}')
        if failure == "changed_source":
            source.write_text("changed source")
        return SimpleNamespace(returncode=1 if failure == "failed_cli" else 0)
    monkeypatch.setattr(native.subprocess, "run", run)
    with pytest.raises(ValueError):
        native.check("drc", str(source), str(target), root=root)
    assert target.read_text() == "previous report" if failure == "existing" else not target.exists()
