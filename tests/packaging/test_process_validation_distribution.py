"""Installed-wheel and offline distribution checks for process validation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).parents[2]
PROFILE_MEMBERS = {
    "workspace_service/process_validation/profiles/coverage.json",
    "workspace_service/process_validation/profiles/structured-demo.json",
    "workspace_service/process_validation/profiles/parametric-drill-jig-01.json",
    "workspace_service/process_validation/profiles/heat-spreader-sizing-01.json",
}


@pytest.fixture(scope="module")
def installed_validator(tmp_path_factory):
    root = tmp_path_factory.mktemp("process-validation-wheel")
    dist = root / "dist"
    installed = root / "installed"
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
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        installed.mkdir()
        archive.extractall(installed)
    return root, installed, names


def _isolated_python(
    installed: Path, cwd: Path, program: str
) -> subprocess.CompletedProcess[str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
    }
    if os.name == "nt":
        for key in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
            value = os.environ.get(key)
            if value:
                environment[key] = value
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(installed)!r})\n{program}",
        ],
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_wheel_contains_validator_code_profiles_and_console_entrypoint(
    installed_validator,
):
    _, _, names = installed_validator
    assert PROFILE_MEMBERS <= names
    assert {
        "core/process_validation.py",
        "data_vault/process_validation_repository.py",
        "workspace_service/process_validation_cli.py",
        "workspace_service/process_validation_tools.py",
        "workspace_service/process_validation/readers/geometry.py",
        "workspace_service/process_validation/readers/thermal.py",
    } <= names
    assert not any(
        name.startswith(("tests/", "scripts/", "artifacts/")) for name in names
    )

    entry_points = next(
        name for name in names if name.endswith(".dist-info/entry_points.txt")
    )
    installed = installed_validator[1]
    text = (installed / entry_points).read_text(encoding="utf-8")
    assert (
        "wright-process-validate = workspace_service.process_validation_cli:main"
        in text
    )


def test_installed_cli_and_gateway_evaluate_offline_without_checkout(
    installed_validator,
):
    root, installed, _ = installed_validator
    runtime = root / "runtime"
    runtime.mkdir()
    result = _isolated_python(
        installed,
        runtime,
        f"""
import asyncio
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.resources
import io
import json
import os
import pathlib
import socket
import subprocess
from types import SimpleNamespace
import urllib.request

from core.process_validation import ProducerIdentity, SubjectBinding, ValidationRequest, canonical_digest
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.gateway import ProcessValidationGatewayProvider
from workspace_service.process_validation.readers.geometry import StepSeatGeometryReader
from workspace_service.process_validation.readers.thermal import ThermalFieldReader
from workspace_service.process_validation_cli import main
import core.process_validation as core_module
import data_vault.process_validation_repository as repository_module
import workspace_service.process_validation as validation_package
import httpx

socket.create_connection = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("network"))
urllib.request.urlopen = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("network"))
subprocess.Popen = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("process"))
httpx.Client.request = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("network"))
async def blocked_async_request(*_a, **_k):
    raise AssertionError("network")
httpx.AsyncClient.request = blocked_async_request

root = pathlib.Path.cwd()
workspace = root / "workspace"
workspace.mkdir()
database = root / "validation.sqlite3"
profile = load_profile("structured-demo")
jig_profile = load_profile("parametric-drill-jig-01")
heat_profile = load_profile("heat-spreader-sizing-01")
value = {{"length_mm": 100, "part_id": "demo-plate"}}
invocation = "offline-import"
subject = SubjectBinding(
    id="offline-subject",
    role="result",
    result_id="offline-result",
    producer=ProducerIdentity(run_id=invocation, step_id="import", attempt=1, output_port="result"),
    kind="value",
    value=value,
    sha256=canonical_digest(value),
)
request = ValidationRequest(
    trace_id="offline-trace",
    workspace_id="installed-workspace",
    invocation_id=invocation,
    subjects=(subject,),
    profile_ref=profile.reference(),
    baseline_ref=profile.baseline.reference(),
    idempotency_key="offline-evaluation",
)
(workspace / "request.json").write_text(request.model_dump_json(), encoding="utf-8")

stdout, stderr = io.StringIO(), io.StringIO()
with redirect_stdout(stdout), redirect_stderr(stderr):
    return_code = main([
        "evaluate",
        "--workspace", str(workspace),
        "--workspace-id", "installed-workspace",
        "--db", str(database),
        "--request", "request.json",
        "--profile", "structured-demo",
    ])
evaluation = json.loads(stdout.getvalue())

provider = ProcessValidationGatewayProvider(str(database))
session = SimpleNamespace(
    session_id="installed-session",
    principal_id="installed-principal",
    workspace_id="installed-workspace",
    workspace_path=str(workspace),
)
tools = provider.tools(session)
get_tool = next(item for item in tools if item.tool_name == "get")
gateway_stdout = io.StringIO()
with redirect_stdout(gateway_stdout):
    gateway_result = asyncio.run(provider.call(
        session,
        get_tool,
        {{"assessment_id": evaluation["assessment_id"]}},
        request_id="installed-get",
        approval_context=None,
        progress_callback=None,
    ))

resource_root = importlib.resources.files("workspace_service.process_validation").joinpath("profiles")
coverage = json.loads(resource_root.joinpath("coverage.json").read_text(encoding="utf-8"))
target = pathlib.Path({str(installed)!r}).resolve()
module_paths = [
    pathlib.Path(core_module.__file__).resolve(),
    pathlib.Path(repository_module.__file__).resolve(),
    pathlib.Path(validation_package.__file__).resolve(),
]
print(json.dumps({{
    "return_code": return_code,
    "release_eligible": evaluation["release_eligible"],
    "assessment_id": evaluation["assessment_id"],
    "gateway_assessment_id": gateway_result["structuredContent"]["assessment"]["id"],
    "gateway_tools": sorted(item.name for item in tools),
    "coverage_version": coverage["schema_version"],
    "qualified_scenarios": coverage["qualified_scenarios"],
    "profile_id": profile.id,
    "engineering_profiles": [jig_profile.id, heat_profile.id],
    "engineering_readers": [
        StepSeatGeometryReader.identity.id,
        ThermalFieldReader.identity.id,
    ],
    "modules_from_wheel": all(path.is_relative_to(target) for path in module_paths),
    "database_exists": database.is_file(),
}}))
""",
    )
    observed = json.loads(result.stdout)
    source_coverage = json.loads(
        (
            REPOSITORY
            / "packages/workspace_service/src/workspace_service/process_validation/"
            "profiles/coverage.json"
        ).read_text(encoding="utf-8")
    )
    assert observed.pop("qualified_scenarios") == source_coverage[
        "qualified_scenarios"
    ]
    assert observed == {
        "return_code": 0,
        "release_eligible": True,
        "assessment_id": observed["assessment_id"],
        "gateway_assessment_id": observed["assessment_id"],
        "gateway_tools": [
            "wright_validation__evaluate",
            "wright_validation__export",
            "wright_validation__get",
            "wright_validation__read",
        ],
        "coverage_version": "wright.process-validation-coverage/2",
        "profile_id": "structured-demo",
        "engineering_profiles": [
            "parametric-drill-jig-01-seat-geometry",
            "heat-spreader-sizing-01-fields",
        ],
        "engineering_readers": ["step-seat-geometry", "thermal-field"],
        "modules_from_wheel": True,
        "database_exists": True,
    }
