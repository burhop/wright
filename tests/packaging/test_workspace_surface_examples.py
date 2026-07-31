from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.workspace_surfaces


@pytest.fixture(scope="module")
def clean_example_runtime(tmp_path_factory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("wright-example-wheel")
    dist = root / "dist"
    installed = root / "installed"
    examples = root / "examples"
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
    wheel = next(dist.glob("*.whl"))
    installed.mkdir()
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(installed)
    shutil.copytree(ROOT / "examples/workspace-surfaces", examples)
    return installed, examples


def _run(installed: Path, examples: Path, name: str, prelude: str) -> str:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
    }
    program = f"""
import runpy, sys
sys.path.insert(0, {str(installed)!r})
{prelude}
runpy.run_path({str(examples / name)!r}, run_name='__main__')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", program],
        cwd=examples,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_beginner_example_runs_offline_from_installed_wheel_without_checkout(
    clean_example_runtime,
) -> None:
    installed, examples = clean_example_runtime
    output = _run(
        installed,
        examples,
        "beginner_graph.py",
        """
from wright.client import DisplayClient, use_display_client
def transport(method, url, headers, payload):
    assert url == '/display'
    return 201, {'surfaceId': 'surface-1', 'displayId': payload['displayId'], 'revision': payload['revision'], 'title': payload['title']}
client = DisplayClient(endpoint='/display', token='ci-test-token', workspace_id='workspace-1', transport=transport)
scope = use_display_client(client)
scope.__enter__()
""",
    )
    assert "surface-1" in output


@pytest.mark.parametrize(
    "example,package",
    [("matplotlib_graph.py", "matplotlib"), ("plotly_graph.py", "plotly")],
)
def test_optional_examples_are_offline_and_actionable_when_dependency_is_absent(
    clean_example_runtime, example: str, package: str
) -> None:
    installed, examples = clean_example_runtime
    output = _run(
        installed,
        examples,
        example,
        f"""
import builtins
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] == {package!r}:
        raise ImportError('blocked for clean-wheel smoke')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
""",
    )
    assert package in output.lower()
    assert "pip install" in output.lower()
