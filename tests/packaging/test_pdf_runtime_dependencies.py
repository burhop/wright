"""The bundled runtime must install the same passive PDF reader dependencies."""
from pathlib import Path
import tomllib

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["pypdfium2", "pillow"])
def test_public_runtime_declares_pdf_reader_dependencies(name):
    public = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    service = tomllib.loads(
        (ROOT / "packages/workspace_service/pyproject.toml").read_text(encoding="utf-8")
    )
    runtime = {
        canonicalize_name(req.name): req
        for value in public["project"]["optional-dependencies"]["runtime"]
        for req in [Requirement(value)]
    }
    private = {
        canonicalize_name(req.name): req
        for value in service["project"]["dependencies"]
        for req in [Requirement(value)]
    }
    assert name in runtime, f"Installed Wright runtime omits PDF dependency {name}"
    assert runtime[name].specifier == private[name].specifier
    assert runtime[name].marker is None, "PDF preview must also install on Linux"
