from __future__ import annotations

import subprocess
import tarfile
import zipfile
from pathlib import Path


def test_wheel_and_sdist_contain_canonical_catalog_resources(tmp_path) -> None:
    package = Path(__file__).parents[1]
    subprocess.run(
        ["uv", "build", "--out-dir", str(tmp_path), str(package)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    sdist = next(tmp_path.glob("*.tar.gz"))
    required = {
        "tool_registry/catalog/engineering-catalog.yaml",
        "tool_registry/catalog/schema.json",
    }
    with zipfile.ZipFile(wheel) as archive:
        assert required <= set(archive.namelist())
    with tarfile.open(sdist, "r:gz") as archive:
        names = {"/".join(name.split("/")[1:]) for name in archive.getnames()}
        assert {
            "src/tool_registry/catalog/engineering-catalog.yaml",
            "src/tool_registry/catalog/schema.json",
        } <= names
