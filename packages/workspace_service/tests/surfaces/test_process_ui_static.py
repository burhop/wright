"""Actual loopback static host and fixed declarations; synthetic bundle, no process runs."""

from http.client import HTTPConnection
import json
from pathlib import Path
from threading import Thread
from typing import get_args
import sys

import pytest

from core.process_interactions import ProcessCapability, ProcessRef
from core.process_interfaces import InterfaceManifest
from core.surfaces.live_app_manifest import (
    ManifestError,
    PROCESS_SURFACE_CAPABILITIES,
    parse_live_app_manifest,
)
from data_vault.process_ui_artifacts import ImmutableFileSet
from workspace_service.surfaces.process_ui_manifest import process_ui_manifest
from workspace_service.surfaces.process_ui_static import (
    ProcessStaticAssets,
    STATIC_CSP,
    make_static_server,
)


def manifest():
    return InterfaceManifest(
        ui_id="ui-" + "a" * 32,
        revision_id="revision-" + "b" * 32,
        title="Synthetic comparison",
        process=ProcessRef(
            workspace_id="workspace",
            source_path="workflows/synthetic.wflow",
            source_digest="a" * 64,
        ),
        client_version="1.0.0",
        kit_version="1.0.0",
    )


def stored(tmp_path, **extra):
    interface = manifest()
    directory = (
        tmp_path
        / f".wright/process-uis/{interface.ui_id}/revisions/{interface.revision_id}"
    )
    identity = ImmutableFileSet(directory).publish(
        {
            "source.json": b'{"private":"not served"}',
            "binding.json": b"{}",
            "build-report.json": b"{}",
            "dist/app.js": b"export function mount() {}",
            "dist/style.css": b"body {color: blue}",
            **extra,
        }
    )
    return directory, identity


def test_fixed_manifest_is_deterministic_and_contains_only_installed_runtime_launch(
    tmp_path,
):
    _, digest = stored(tmp_path)
    value, parsed = process_ui_manifest(str(tmp_path), manifest(), digest)
    other, again = process_ui_manifest(str(tmp_path), manifest(), digest)
    assert value == other and parsed.canonical_hash == again.canonical_hash
    argv = parsed.launch.argv
    assert argv[0] == str(Path(sys.executable).absolute())
    assert argv[1:3] == ("-m", "workspace_service.surfaces.process_ui_static")
    assert "${WRIGHT_PORT}" in argv and "${WRIGHT_BIND_HOST}" in argv
    assert parsed.launch.environment == {} and parsed.launch.working_directory == "."
    assert parsed.presentation.panel and not parsed.presentation.browser
    assert parsed.presentation.sharing == "isolated"
    assert parsed.lifetime.policy == "presentation"
    assert parsed.capabilities == frozenset(manifest().capabilities)
    assert "wright.tool.call" not in parsed.capabilities


def test_manifest_process_capabilities_are_exactly_the_public_closed_operations(
    tmp_path,
):
    assert PROCESS_SURFACE_CAPABILITIES == frozenset(get_args(ProcessCapability))
    _, digest = stored(tmp_path)
    value, _ = process_ui_manifest(str(tmp_path), manifest(), digest)
    value["capabilities"] = ["process.invokeTool"]
    with pytest.raises(ManifestError):
        parse_live_app_manifest(value)


def test_manifest_rejects_wrong_inventory_unallocated_paths_and_missing_python(
    tmp_path,
):
    _, digest = stored(tmp_path)
    with pytest.raises(ValueError):
        process_ui_manifest(str(tmp_path), manifest(), "f" * 64)
    bad = manifest().model_copy(update={"ui_id": "../outside"})
    with pytest.raises(ValueError):
        process_ui_manifest(str(tmp_path), bad, digest)
    with pytest.raises(ValueError):
        process_ui_manifest(
            str(tmp_path),
            manifest(),
            digest,
            python_executable=tmp_path / "missing-python",
        )


def test_actual_static_server_serves_only_verified_dist_and_health_with_restrictive_headers(
    tmp_path,
):
    directory, digest = stored(tmp_path)
    assets = ProcessStaticAssets(directory, digest)
    server = make_static_server(assets, "127.0.0.1", 0)
    worker = Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    )
    worker.start()
    try:
        for path, status in [
            ("/", 200),
            ("/app.js", 200),
            ("/style.css", 200),
            ("/wright-runtime.js", 200),
            ("/__wright/health", 200),
            ("/source.json", 404),
            ("/binding.json", 404),
            ("/build-report.json", 404),
            ("/../source.json", 404),
            ("/%2e%2e/source.json", 404),
            ("/__wright/process/context", 404),
        ]:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            client.request("GET", path)
            response = client.getresponse()
            raw = response.read()
            assert response.status == status, path
            assert response.getheader("Content-Security-Policy") == STATIC_CSP
            assert response.getheader("X-Content-Type-Options") == "nosniff"
            assert response.getheader("Cache-Control") == "no-store"
            assert "private" not in raw.decode()
            assert "ws:" not in STATIC_CSP and "wss:" not in STATIC_CSP
            client.close()
        client = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        client.request("HEAD", "/app.js")
        response = client.getresponse()
        assert response.status == 200 and response.read() == b""
        client.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        assert not worker.is_alive()


@pytest.mark.parametrize(
    "path",
    [
        "/source.json",
        "//remote/app.js",
        "https://remote/app.js",
        "/%61pp.js",
        "/assets\\app.js",
    ],
)
def test_static_lookup_rejects_alternate_paths_and_urls(tmp_path, path):
    directory, digest = stored(tmp_path)
    assert ProcessStaticAssets(directory, digest).response(path) is None


def test_static_host_rejects_public_bind_and_corrupt_vault_without_compiler_or_model(
    tmp_path,
):
    directory, digest = stored(tmp_path)
    assets = ProcessStaticAssets(directory, digest)
    with pytest.raises(ValueError):
        make_static_server(assets, "0.0.0.0", 0)
    inventory = json.loads((directory / "inventory.json").read_bytes())
    (directory / inventory["dist/app.js"]["storage_key"]).write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        ProcessStaticAssets(directory, digest)


@pytest.mark.parametrize(
    "name", ["dist/untrusted.html", "dist/image.svg", "dist/server.py"]
)
def test_static_host_rejects_unsupported_bundle_media(tmp_path, name):
    directory, digest = stored(tmp_path, **{name: b"unsupported"})
    with pytest.raises(ValueError):
        ProcessStaticAssets(directory, digest)
