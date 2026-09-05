"""Package-resource discovery and compatibility of domain-only path validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from itertools import product
from pathlib import Path, PureWindowsPath

import pytest

from core.native_process import (
    NativeProcessError,
    _validate_relative_path,
    language_contract,
    validate_definition,
)

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "packages/core/src/core"
CONTRACTS = ROOT / "specs/079-wright-native-authoring/contracts"
PATHS = json.loads(
    (
        ROOT / "apps/web/src/components/native-process/native-paths.fixture.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("path", "accepted"),
    [(path, True) for path in PATHS["accepted"]]
    + [(path, False) for path in PATHS["rejected"]],
)
def test_artifact_path_matches_shared_client_vectors(path, accepted):
    definition = json.loads(
        (CONTRACTS / "examples/concept-brief.json").read_text(encoding="utf-8")
    )
    definition["steps"][0].update(operation="artifact.input@1", config={"path": path})
    definition["ports"][0]["type"] = "artifact"
    definition["connections"] = []
    if accepted:
        document = validate_definition(definition)
        assert document.as_dict()["steps"][0]["config"]["path"] == path
    else:
        with pytest.raises(NativeProcessError) as caught:
            validate_definition(definition)
        expected_code = "ARTIFACT_PATH" if path else "SCHEMA_INVALID"
        assert caught.value.findings[0].code == expected_code


def test_removing_windows_drive_parser_preserves_lexical_rejections():
    # Drive-relative, UNC, extended-length and device paths plus every short
    # combination of drive/separator/segment/control syntax exercise the old
    # platform-independent parser against the domain-only replacement.
    explicit = [
        "C:",
        "C:relative.txt",
        "c:/absolute.txt",
        "\\\\host\\share\\file.txt",
        "//host/share/file.txt",
        "\\\\?\\C:\\file.txt",
        "\\\\?\\UNC\\host\\share\\file.txt",
        "\\\\.\\PhysicalDrive0",
        *PATHS["accepted"],
        *PATHS["rejected"],
    ]
    generated = (
        "".join(chars)
        for size in range(5)
        for chars in product("C:/.\\\0", repeat=size)
    )
    for path in (*explicit, *generated):
        old_rejected = bool(
            PureWindowsPath(path).drive
            or path.startswith(("/", "\\"))
            or any(
                part in {"", ".", ".."} for part in path.replace("\\", "/").split("/")
            )
            or ":" in path
            or "\0" in path
        )
        try:
            _validate_relative_path(path, "source")
        except NativeProcessError as error:
            assert old_rejected, repr(path)
            assert error.findings[0].code == "ARTIFACT_PATH"
        else:
            assert not old_rejected, repr(path)


@pytest.mark.parametrize("packaging", ["directory", "zip"])
def test_schema_discovery_uses_installed_package_resources(tmp_path, packaging):
    if packaging == "directory":
        artifact = tmp_path / "installed"
        shutil.copytree(
            CORE,
            artifact / "core",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    else:
        artifact = tmp_path / "installed.zip"
        with zipfile.ZipFile(artifact, "w") as archive:
            for path in CORE.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(CORE.parent).as_posix())

    # -I ignores the checkout's PYTHONPATH. A fresh interpreter must discover
    # the schema through the supplied package, including a non-filesystem ZIP.
    definition = json.loads(
        (CONTRACTS / "examples/concept-brief.json").read_text(encoding="utf-8")
    )
    probe = """
import json
import sys
sys.path.insert(0, sys.argv[1])
import core.native_process as native
definition = json.load(sys.stdin)
document = native.validate_definition(definition)
print(json.dumps({
    "origin": native.__file__,
    "contract": native.language_contract(),
    "canonical": document.canonical_bytes.hex(),
    "ready": not native.readiness(document),
}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(artifact)],
        input=json.dumps(definition),
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=tmp_path,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["origin"].startswith(str(artifact))
    assert observed["contract"] == language_contract()
    assert (
        observed["canonical"] == validate_definition(definition).canonical_bytes.hex()
    )
    assert observed["ready"] is True
