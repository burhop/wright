"""Fast boundary tests only; fake native runner is not provider qualification."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("native_interconnect_test", Path(__file__).parents[1] / "scripts/kicad_campaign/native_rule_check.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def test_retains_actual_native_xml_erc_and_source_identity(tmp_path, monkeypatch):
    source = tmp_path / "harness.kicad_sch"
    source.write_text("synthetic test source")
    xml = b'<?xml version="1.0"?><export version="E"><components/><nets/></export>'
    erc = json.dumps({"sheets":[{"violations":[{"severity":"error", "description":"retained finding"}]}]}).encode()

    def run(command, **kwargs):
        if command[:4] == ["kicad-cli", "sch", "export", "netlist"]:
            assert command[4:6] == ["--format", "kicadxml"]
            payload = xml
        else:
            assert command[:3] == ["kicad-cli", "sch", "erc"]
            payload = erc
        assert command[-1] == str(source.resolve())
        Path(command[command.index("--output") + 1]).write_bytes(payload)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(native.subprocess, "run", run)
    destination = tmp_path / "native-check"
    result = native.export_interconnect(str(source), str(destination), root=tmp_path)
    assert (destination / "netlist.xml").read_bytes() == xml
    assert (destination / "erc.json").read_bytes() == erc
    proof = json.loads((destination / "inspection.json").read_bytes())
    assert proof["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert proof["netlist_sha256"] == hashlib.sha256(xml).hexdigest()
    assert proof["erc_sha256"] == hashlib.sha256(erc).hexdigest()
    assert proof["erc_error_count"] == 1  # Never suppress real native findings.
    assert result["status"] == "exported_not_design_approval"
    assert len(result["produced_files"]) == 3


@pytest.mark.parametrize("defect", ["escape", "existing", "wrong_type", "failed_cli", "missing_xml", "changed_source", "invalid_xml", "external_entities"])
def test_refuses_unconfined_or_unproven_native_exports(tmp_path, monkeypatch, defect):
    root = tmp_path / "work"
    root.mkdir()
    source = root / ("harness.txt" if defect == "wrong_type" else "harness.kicad_sch")
    source.write_text("synthetic native input")
    destination = root / "native-check" if defect != "escape" else tmp_path / "escape"
    if defect == "existing":
        destination.mkdir()
        (destination / "prior.json").write_text("preserve")

    def run(command, **kwargs):
        assert defect in {"failed_cli", "missing_xml", "changed_source", "invalid_xml", "external_entities"}
        payload = b'<export version="E"><components/><nets/></export>'
        if defect == "invalid_xml":
            payload = b'<not-netlist/>'
        if defect == "external_entities":
            payload = b'<!DOCTYPE export [<!ENTITY x SYSTEM "file:///etc/passwd">]><export><components/><nets>&x;</nets></export>'
        if defect != "missing_xml":
            Path(command[command.index("--output") + 1]).write_bytes(payload)
        if defect == "changed_source":
            source.write_text("changed bytes")
        return SimpleNamespace(returncode=1 if defect == "failed_cli" else 0)

    monkeypatch.setattr(native.subprocess, "run", run)
    with pytest.raises(ValueError):
        native.export_interconnect(str(source), str(destination), root=root)
    if defect == "existing":
        assert (destination / "prior.json").read_text() == "preserve"
    else:
        assert not destination.exists()
