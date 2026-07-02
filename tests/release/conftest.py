from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Iterable

import pytest

ROOT = Path(__file__).resolve().parents[2]


def repo_path(relative_path: str) -> Path:
    return ROOT / relative_path


def read_text(relative_path: str) -> str:
    return repo_path(relative_path).read_text(encoding="utf-8")


def run_cmd(
    args: Iterable[str | Path], *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    string_args = [str(arg) for arg in args]
    return subprocess.run(
        string_args,
        cwd=cwd or ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def copy_fixture(name: str, destination: Path) -> Path:
    source = ROOT / "tests" / "fixtures" / name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def read_toml(path: Path) -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover - Python 3.10 fallback only
        import tomli as tomllib
    with path.open("rb") as fh:
        return tomllib.load(fh)


def archive_members(path: Path) -> set[str]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    if path.suffixes[-2:] == [".tar", ".gz"] or path.suffix == ".tgz":
        with tarfile.open(path) as archive:
            return {member.name for member in archive.getmembers()}
    raise ValueError(f"Unsupported archive type: {path}")


@pytest.fixture
def mirror_fixture(tmp_path: Path) -> Path:
    return copy_fixture("hermes_plugin_mirror", tmp_path / "mirror")


@pytest.fixture
def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env
