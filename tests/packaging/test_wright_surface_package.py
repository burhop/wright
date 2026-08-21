from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.workspace_surfaces


@pytest.fixture(scope="module")
def installed_wheel(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("wright-surface-wheel")
    dist = root / "dist"
    target = root / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(dist),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    target.mkdir()
    with zipfile.ZipFile(wheels[0]) as archive:
        archive.extractall(target)
    return target


def _isolated_python(target: Path, program: str) -> subprocess.CompletedProcess[str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(target),
        "PYTHONIOENCODING": "utf-8",
    }
    if os.name == "nt":
        # Windows standard-library imports can initialize Winsock-backed
        # modules such as ``_overlapped``. Preserve only the OS bootstrap and
        # temporary-root variables they require; package discovery remains
        # confined to the extracted wheel through ``-I`` and the inserted path.
        for key in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
            value = os.environ.get(key)
            if value:
                environment[key] = value
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(target)!r})\n{program}",
        ],
        cwd=target,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_installed_wheel_imports_public_surface_helper_without_checkout(
    installed_wheel: Path,
) -> None:
    result = _isolated_python(
        installed_wheel,
        """
import json
import os
import pathlib
import socket
import subprocess
import sys
import threading
import urllib.request

before_env = dict(os.environ)
before_threads = {thread.ident for thread in threading.enumerate()}
socket.socket.connect = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network"))
subprocess.Popen = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("process"))
urllib.request.urlopen = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network"))
import wright

print(json.dumps({
    "contract_version": wright.CONTRACT_VERSION,
    "environment_unchanged": before_env == dict(os.environ),
    "threads_unchanged": before_threads == {thread.ident for thread in threading.enumerate()},
    "optional_modules": sorted(set(sys.modules) & {"matplotlib", "pandas", "plotly", "PIL"}),
    "module_path": str(pathlib.Path(wright.__file__).resolve()),
}))
""",
    )
    observed = json.loads(result.stdout)
    assert observed["contract_version"] == 1
    assert observed["environment_unchanged"] is True
    assert observed["threads_unchanged"] is True
    assert observed["optional_modules"] == []
    assert Path(observed["module_path"]).is_relative_to(installed_wheel)


def test_installed_wheel_exposes_versioned_schema_assets(
    installed_wheel: Path,
) -> None:
    result = _isolated_python(
        installed_wheel,
        """
import importlib.resources
import json

root = importlib.resources.files("core.surfaces").joinpath("schemas")
manifest = json.loads(root.joinpath("contract-set.json").read_text(encoding="utf-8"))
print(json.dumps({
    "version": manifest["contractVersion"],
    "files": sorted(manifest["files"]),
    "all_present": all(root.joinpath("v1", name).is_file() for name in manifest["files"]),
}))
""",
    )
    observed = json.loads(result.stdout)
    assert observed == {
        "version": 1,
        "files": [
            "display-envelope.schema.json",
            "live-app-manifest.schema.json",
            "surface-message.schema.json",
            "workspace-surfaces.openapi.yaml",
        ],
        "all_present": True,
    }
