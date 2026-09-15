"""Selected-provider native KiCad report export; no arbitrary CLI surface."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Literal


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


def register(server):
    @server.tool()
    def native_rule_check(kind: Literal["erc", "drc"], source_path: str, report_path: str) -> dict:
        """Run real KiCad ERC/DRC and retain its complete JSON report under /work. Issues remain failures for the engineering review; report creation alone is not a clean-design verdict."""
        return check(kind, source_path, report_path)
