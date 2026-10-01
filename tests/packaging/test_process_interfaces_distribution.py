"""Installed UI resources and offline static hosting, with no checkout imports."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = "workspace_service/process_interfaces/resources/public"


def build(root, output, *targets):
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(output),
            *targets,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def unpack_wheel(output, installed):
    wheels = list(output.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        members = set(archive.namelist())
        for name in ("process_client", "ui_kit"):
            source_root = ROOT / f"packages/{name}/src"
            for source in source_root.rglob("*"):
                if source.is_file():
                    member = f"{PUBLIC}/{name}/src/{source.relative_to(source_root).as_posix()}"
                    assert archive.read(member) == source.read_bytes()
            for member in ("package.json", "README.md"):
                assert (
                    archive.read(f"{PUBLIC}/{name}/{member}")
                    == (ROOT / f"packages/{name}/{member}").read_bytes()
                )
        assert "workspace_service/surfaces/process_ui_static.py" in members
        assert not any(
            name.startswith(("tests/", "scripts/", "artifacts/")) for name in members
        )
        archive.extractall(installed)
    return members


@pytest.fixture(scope="module")
def installed_interfaces(tmp_path_factory):
    directory = tmp_path_factory.mktemp("process-interface-wheel")
    build(ROOT, directory / "dist", "--wheel")
    installed = directory / "installed"
    unpack_wheel(directory / "dist", installed)
    return directory, installed


def isolated(installed, cwd, program, **environment):
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    env.update(environment)
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(installed)!r})\n" + program,
        ],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_public_resources_and_static_host_work_without_compiler_or_model(
    installed_interfaces,
):
    directory, installed = installed_interfaces
    result = isolated(
        installed,
        directory,
        f"""
import json, pathlib, socket, subprocess
from http.client import HTTPConnection
from threading import Thread
from importlib.resources import files
from data_vault.process_ui_artifacts import ImmutableFileSet
from workspace_service.process_interfaces import toolchain
from workspace_service.process_interfaces.resources import load_authoring_resources
from workspace_service.surfaces import process_ui_static
assert pathlib.Path(toolchain.__file__).is_relative_to({str(installed)!r})
assert pathlib.Path(process_ui_static.__file__).is_relative_to({str(installed)!r})
def forbidden(*args, **kwargs):
    raise AssertionError('Offline saved hosting must not launch a compiler or model')
subprocess.Popen = forbidden
connect = socket.create_connection
def offline_connection(address, *args, **kwargs):
    assert address == ('127.0.0.1', server.server_port), 'External network is unavailable'
    return connect(address, *args, **kwargs)
socket.create_connection = offline_connection
toolchain.shutil.which = lambda _: None
assert isinstance(toolchain.discover_build_toolchain(), toolchain.UnavailableBuildToolchain)
resources = load_authoring_resources()
assert resources.version == 'process-ui-author-1'
public = files('workspace_service.process_interfaces.resources').joinpath('public')
assert public.joinpath('process_client/src/index.ts').is_file()
assert public.joinpath('ui_kit/src/styles.css').is_file()
vault = pathlib.Path('isolated-saved-bundle')
digest = ImmutableFileSet(vault).publish({{'dist/app.js': b'export function mount(){{}}'}})
assets = process_ui_static.ProcessStaticAssets(vault, digest)
server = process_ui_static.make_static_server(assets, '127.0.0.1', 0)
worker = Thread(target=server.serve_forever, kwargs={{'poll_interval': 0.01}}, daemon=True)
worker.start()
try:
    for path in ('/', '/app.js', '/wright-runtime.js', '/__wright/health'):
        client = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        client.request('GET', path)
        response = client.getresponse()
        assert response.status == 200
        assert response.getheader('content-security-policy') == process_ui_static.STATIC_CSP
        response.read(); client.close()
finally:
    server.shutdown(); server.server_close(); worker.join(2)
print(json.dumps({{'installed': True, 'offline_static_http': True, 'source_digest': resources.resource_digest}}))
""",
    )
    assert json.loads(result.stdout)["offline_static_http"] is True


def test_installed_compiler_uses_shipped_public_sources_and_explicit_native_dependencies(
    installed_interfaces,
):
    directory, installed = installed_interfaces
    result = isolated(
        installed,
        directory,
        f"""
import asyncio, json, pathlib
from workspace_service.process_interfaces import toolchain
from workspace_service.process_interfaces.build import BuildToolchain, build_interface
from workspace_service.process_interfaces.resources import load_authoring_resources
from core.process_interactions import ProcessRef
from core.process_interfaces import InterfaceManifest, SourceEnvelope
assert pathlib.Path(toolchain.__file__).is_relative_to({str(installed)!r})
configured = toolchain.discover_build_toolchain()
assert isinstance(configured, BuildToolchain)
assert configured.dependency_root == pathlib.Path({str(ROOT)!r})
assert configured.client_root.is_relative_to({str(installed)!r})
assert configured.kit_root.is_relative_to({str(installed)!r})
process = ProcessRef(workspace_id='installed-proof', source_path='workflows/example.wflow', source_digest='a'*64)
manifest = InterfaceManifest(ui_id='ui-installed', revision_id='revision-installed', title='Installed proof',
    process=process, client_version='1.0.0', kit_version='1.0.0')
source = SourceEnvelope(files={{'App.tsx': load_authoring_resources().template}})
built = asyncio.run(build_interface(source=source, manifest=manifest, process=process, catalog=[],
    toolchain=configured, builds_root=pathlib.Path('installed-builds')))
assert built.report.state == 'built', built.report.diagnostics
assert built.dist.joinpath('app.js').is_file()
print(json.dumps({{**configured.describe(), 'compiled_installed_sources': True}}))
""",
        WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT=str(ROOT),
    )
    data = json.loads(result.stdout)
    assert data["packages"]["@wright/process-client"]["version"] == "1.0.0"
    assert data["packages"]["@wright/ui-kit"]["version"] == "1.0.0"
    assert data["compiled_installed_sources"] is True


def test_private_service_direct_wheel_and_sdist_rebuild_include_the_same_resources(
    tmp_path,
):
    service = ROOT / "packages/workspace_service"
    build(service, tmp_path / "direct", "--wheel", "--sdist")
    unpack_wheel(tmp_path / "direct", tmp_path / "installed-direct")
    archive = next((tmp_path / "direct").glob("*.tar.gz"))
    with tarfile.open(archive) as source:
        source.extractall(tmp_path / "source", filter="data")
    root = next((tmp_path / "source").iterdir())
    assert not (root.parent / "process_client").exists()
    build(root, tmp_path / "rebuilt", "--wheel")
    unpack_wheel(tmp_path / "rebuilt", tmp_path / "installed-rebuilt")
