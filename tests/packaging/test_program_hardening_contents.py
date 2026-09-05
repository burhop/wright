from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_program_diagnostics_and_current_schema_ship_in_the_wheel(
    tmp_path: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert {
            "workspace_service/support_diagnostics.py",
            "workspace_service/support_diagnostic_service.py",
            "api/routers/support_diagnostics.py",
            "wright_engineering/compatibility.json",
            "wright_engineering/static/web/asset-manifest.json",
        } <= names
        compatibility = json.loads(
            archive.read("wright_engineering/compatibility.json")
        )
        assert compatibility["data_schema"]["max"] == 17
        diagnostic_source = b"\n".join(
            archive.read(name)
            for name in (
                "workspace_service/support_diagnostics.py",
                "workspace_service/support_diagnostic_service.py",
                "api/routers/support_diagnostics.py",
            )
        )
        for prohibited in (
            b"sk-live-private-token-123456",
            b"customer-bracket-feature-vector-42",
            b"M3 S12000",
            b"G28",
        ):
            assert prohibited not in diagnostic_source


def test_program_contracts_and_operator_docs_remain_schema_valid_and_public() -> None:
    contracts = ROOT / "specs" / "073-program-hardening" / "contracts"
    for name in (
        "support-diagnostic-snapshot.schema.json",
        "state-inventory.schema.json",
        "compatibility-evidence.schema.json",
    ):
        document = json.loads((contracts / name).read_text(encoding="utf-8"))
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    for relative in (
        "docs/operations/engineering-support-diagnostics.md",
        "docs/getting-started/program-state-lifecycle.md",
        "docs/testing/engineering-program-usability.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert len(text) > 1_000
        assert "physical" in text.lower()
