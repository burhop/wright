from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_installed_wheel_has_offline_rivet_editor_runner_bridge_and_mcp(
    tmp_path: Path,
) -> None:
    wheel_dir = tmp_path / "wheel"
    wheel_dir.mkdir()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(wheel_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(wheel_dir.glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(installed)

    probe = tmp_path / "probe.py"
    probe.write_text(
        """
import importlib.metadata
import pathlib
import socket
import sys

installed = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(installed))

def no_network(*_args, **_kwargs):
    raise AssertionError("installed Rivet verification attempted network access")

socket.create_connection = no_network
socket.socket.connect = no_network

from agent_adapters.hermes_openai_bridge import HermesOpenAICompatibilityBridge
from core.workflow_editor import EditorAvailability
from core.workflow_runs import RunnerAvailability
from workspace_service.rivet_mcp import main as rivet_mcp_main
from workspace_service.workflow_editor import EditorAssetCatalog
from workspace_service.workflow_runner import RunnerAssetCatalog

for value in (
    HermesOpenAICompatibilityBridge,
    rivet_mcp_main,
    EditorAssetCatalog,
    RunnerAssetCatalog,
):
    assert installed in pathlib.Path(sys.modules[value.__module__].__file__).resolve().parents

editor_status, _editor_manifest, editor_detail = EditorAssetCatalog().status()
runner_status, runner_manifest, runner_detail = RunnerAssetCatalog().status()
assert editor_status is EditorAvailability.AVAILABLE, editor_detail
assert runner_status is RunnerAvailability.AVAILABLE, runner_detail
assert runner_manifest is not None and runner_manifest.entrypoint.is_file()

scripts = importlib.metadata.distribution("wright-engineering").entry_points
entry = next(item for item in scripts if item.name == "wright-rivet-mcp")
assert entry.value == "workspace_service.rivet_mcp:main"
""",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-I", str(probe), str(installed)],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
