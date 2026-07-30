from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build-native-predecessor-fixture.py"


def _module():
    spec = importlib.util.spec_from_file_location("native_predecessor_fixture", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fixture_rewrites_wheel_identity_and_compatibility(tmp_path: Path) -> None:
    source = tmp_path / "wright_engineering-0.1.6-py3-none-any.whl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "wright_engineering-0.1.6.dist-info/METADATA",
            "Name: wright-engineering\nVersion: 0.1.6\n",
        )
        archive.writestr(
            "wright_engineering-0.1.6.dist-info/WHEEL",
            "Wheel-Version: 1.0\nTag: py3-none-any\n",
        )
        archive.writestr(
            "wright_engineering/compatibility.json",
            json.dumps({"runtime_version": "0.1.6", "runtime_specifier": "==0.1.6"}),
        )
        archive.writestr(
            "wright_engineering/runtime-extra-lock.json",
            json.dumps({"version": "0.1.6"}),
        )
        archive.writestr("wright_engineering-0.1.6.dist-info/RECORD", "")

    target = _module().build_fixture(source, tmp_path / "output", "0.1.6+fixture.1")

    assert target.name == "wright_engineering-0.1.6+fixture.1-py3-none-any.whl"
    with zipfile.ZipFile(target) as archive:
        metadata = archive.read(
            "wright_engineering-0.1.6+fixture.1.dist-info/METADATA"
        ).decode()
        compatibility = json.loads(
            archive.read("wright_engineering/compatibility.json")
        )
        assert "Version: 0.1.6+fixture.1" in metadata
        assert compatibility["runtime_version"] == "0.1.6+fixture.1"
        assert compatibility["runtime_specifier"] == "==0.1.6.*"
        assert archive.read("wright_engineering-0.1.6+fixture.1.dist-info/RECORD")


def test_default_fixture_version_tracks_root_release() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    wheel = Path(f"wright_engineering-{version}-py3-none-any.whl")

    assert _module().default_fixture_version(wheel) == f"{version}+fixture.1"
