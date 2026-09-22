"""Selected-provider native KiCad report export; no arbitrary CLI surface."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Literal
from xml.etree import ElementTree


def check(kind: Literal["erc", "drc"], source_path: str, report_path: str, *, root: Path = Path("/work")) -> dict:
    if kind not in {"erc", "drc"}:
        raise ValueError("Only native ERC and DRC are supported")
    root = root.resolve(strict=True)
    source = Path(source_path).resolve(strict=True)
    report = Path(report_path).resolve()
    if not source.is_relative_to(root) or not report.is_relative_to(root):
        raise ValueError("Native rule check paths must remain inside the selected workspace")
    suffix = ".kicad_sch" if kind == "erc" else ".kicad_pcb"
    if source.suffix != suffix or report.suffix != ".json" or report.exists():
        raise ValueError("Require matching native source and a new JSON report")
    if not source.is_file() or not 0 < source.stat().st_size <= 20 * 1024 * 1024:
        raise ValueError("Native source is empty or oversized")
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-rule-", dir=report.parent) as temporary:
        native_report = Path(temporary) / "report.json"
        completed = subprocess.run([
            "kicad-cli", "sch" if kind == "erc" else "pcb", kind,
            "--format", "json", "--output", str(native_report), str(source),
        ], capture_output=True, text=True, timeout=90)
        if completed.returncode != 0 or not native_report.is_file():
            raise ValueError(f"Native KiCad {kind.upper()} did not produce a report (exit {completed.returncode})")
        data = native_report.read_bytes()
        if not 0 < len(data) <= 20 * 1024 * 1024:
            raise ValueError("Native rule report is empty or oversized")
        value = json.loads(data)
        if kind == "erc":
            issues = [issue for sheet in value["sheets"] for issue in sheet["violations"]]
        else:
            issues = value["violations"] + value["unconnected_items"] + value.get("schematic_parity", [])
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_digest:
            raise ValueError("Native source changed during rule checking")
        # Publish actual native bytes without changing severity or hiding issues.
        with report.open("xb") as stream:
            stream.write(data)
    return {
        "operation": f"native_{kind}", "engine": "kicad-cli", "exit_code": completed.returncode,
        "source_sha256": source_digest, "issue_count": len(issues),
        "error_count": sum(item.get("severity") == "error" for item in issues),
        "warning_count": sum(item.get("severity") == "warning" for item in issues),
        "issues": issues,
        "produced_files": [{"output_path": str(report), "output_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "output_format": "json", "output_port": "report"}],
    }


def export_interconnect(source_path: str, output_directory: str, *, root: Path = Path("/work")) -> dict:
    """Export native facts for a downstream independent pin/net comparison."""
    root = root.resolve(strict=True)
    source = Path(source_path).resolve(strict=True)
    output = Path(output_directory).resolve()
    if not source.is_relative_to(root) or not output.is_relative_to(root):
        raise ValueError("Native interconnect paths must stay inside the selected workspace")
    if source.suffix != ".kicad_sch" or not source.is_file() or output.exists():
        raise ValueError("Require an actual schematic and a fresh native-check directory")
    original = source.read_bytes()
    if not 0 < len(original) <= 20 * 1024 * 1024:
        raise ValueError("Native schematic is empty or oversized")
    source_sha = hashlib.sha256(original).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-interconnect-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        netlist = temporary / "netlist.xml"
        result = subprocess.run([
            "kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
            "--output", str(netlist), str(source),
        ], capture_output=True, text=True, timeout=90)
        if result.returncode != 0 or not netlist.is_file():
            raise ValueError("Native KiCad netlist export did not produce an XML artifact")
        raw = netlist.read_bytes()
        if not 0 < len(raw) <= 20 * 1024 * 1024:
            raise ValueError("Native netlist is empty or oversized")
        text = raw.decode("utf-8-sig")
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ValueError("Native netlist must not contain document types or entities")
        try:
            parsed = ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise ValueError("Invalid native KiCad netlist XML") from exc
        if parsed.tag != "export" or parsed.find("components") is None or parsed.find("nets") is None:
            raise ValueError("Native XML is not a KiCad exported netlist")
        if source.read_bytes() != original:
            raise ValueError("Schematic changed during native netlist export")
        erc = check("erc", str(source), str(temporary / "erc.json"), root=root)
        if source.read_bytes() != original:
            raise ValueError("Schematic changed between netlist and ERC observations")
        erc_bytes = (temporary / "erc.json").read_bytes()
        proof = {
            "schema": "wright-native-kicad-interconnect-v1",
            "status": "exported_not_design_approval",
            "engine": "kicad-cli",
            "source_path": str(source), "source_sha256": source_sha,
            "netlist_sha256": hashlib.sha256(raw).hexdigest(),
            "erc_sha256": hashlib.sha256(erc_bytes).hexdigest(),
            "erc_error_count": erc["error_count"],
            "erc_warning_count": erc["warning_count"],
        }
        outputs = {"netlist.xml": raw, "erc.json": erc_bytes,
                   "inspection.json": (json.dumps(proof, indent=2) + "\n").encode()}
        output.mkdir(exist_ok=False)
        files = []
        for name, content in outputs.items():
            path = output / name
            with path.open("xb") as stream:
                stream.write(content)
            files.append({"output_path": str(path), "output_bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest(),
                          "output_format": path.suffix.removeprefix("."), "output_port": path.stem})
    return {**proof, "produced_files": files}


def register(server):
    @server.tool()
    def native_rule_check(kind: Literal["erc", "drc"], source_path: str, report_path: str) -> dict:
        """Run real KiCad ERC/DRC and retain its complete JSON report under /work. Issues remain failures for the engineering review; report creation alone is not a clean-design verdict."""
        return check(kind, source_path, report_path)

    @server.tool()
    def native_interconnect_export(source_path: str, output_directory: str) -> dict:
        """Export actual KiCad XML nets, complete native ERC and their exact schematic hashes into a new directory. Preserves all errors and warnings; does not assert pin/net correspondence or design approval."""
        return export_interconnect(source_path, output_directory)
