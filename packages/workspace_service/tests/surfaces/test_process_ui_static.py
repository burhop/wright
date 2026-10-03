"""Actual loopback static host and fixed declarations; synthetic bundle, no process runs."""

from http.client import HTTPConnection
import json
import copy
from pathlib import Path
from threading import Thread
from typing import get_args
import sys
import shutil
import subprocess

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
from workspace_service.process_interfaces.presentation import (
    ProcessInterfacePresentations,
)
from workspace_service.surfaces.process_ui_static import (
    _RUNTIME,
    ProcessStaticAssets,
    STATIC_CSP,
    make_static_server,
)


def test_fixed_runtime_applies_only_supported_control_schemes():
    """Execute the shipped receiver before its separate network/mount startup."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("The fixed-runtime JavaScript check requires Node.js")
    receiver, startup = _RUNTIME.decode().split(
        "try {\n  const response = await fetch", 1
    )
    assert startup  # Keep this check attached to the actual shipped runtime.
    script = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const receiver = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const applied = new Map(), replies = [];
const parent = {postMessage: (value, origin) => replies.push({value, origin})};
const sandbox = {AbortController, URL, window: {parent, addEventListener() {}},
  document: {getElementById() {return {};}, documentElement: {style: {
    setProperty: (key, value) => applied.set(key, value)}}}};
vm.runInNewContext(receiver + `
mounted = true; context = {presentation_id:'presentation-one', generation:1};
globalThis.deliver = (type, tokens, nonce = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa') =>
  receiveHost({source:window.parent, origin:'https://wright.example.test', data:{
    schema_version:'wright.process-host/1', type, nonce,
    presentation_id:context.presentation_id, generation:context.generation, tokens}});
`, sandbox);
for (const scheme of ['light', 'dark']) {
  sandbox.deliver('hello', {'color-scheme':scheme, '--private-token':'private'});
  assert.equal(applied.get('color-scheme'), scheme);
  assert.equal(applied.has('--private-token'), false);
}
for (const scheme of ['normal', 'light dark', 'url(https://foreign.invalid)', 'light;display:none']) {
  sandbox.deliver('theme', {'color-scheme':scheme});
  assert.equal(applied.get('color-scheme'), 'dark');
}
sandbox.deliver('theme', {'color-scheme':'light'}, 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb');
assert.equal(applied.get('color-scheme'), 'dark');
sandbox.deliver('theme', {'color-scheme':'light'});
assert.equal(applied.get('color-scheme'), 'light');
assert.equal(replies.length, 2);
assert.equal(replies.every(reply => reply.value.type === 'ready'), true);
"""
    reply = subprocess.run(
        [node, "-e", script], input=json.dumps(receiver), text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert reply.returncode == 0, reply.stderr


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
    assert parsed.readiness.timeout_ms == 30_000
    assert parsed.readiness.interval_ms == 250
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


def test_host_local_declaration_rebinds_only_relocated_runtime_paths(tmp_path):
    _, digest = stored(tmp_path)
    value, parsed = process_ui_manifest(str(tmp_path), manifest(), digest)
    relocated = copy.deepcopy(value)
    relocated["launch"]["argv"][0] = "C:/old-runtime/python.exe"
    relocated["launch"]["argv"][4] = (
        "C:/old-workspace/.wright/process-uis/"
        + manifest().ui_id
        + "/revisions/"
        + manifest().revision_id
    )
    ProcessInterfacePresentations._install_manifest(
        str(tmp_path), relocated, parse_live_app_manifest(relocated)
    )
    ProcessInterfacePresentations._install_manifest(str(tmp_path), value, parsed)
    path = tmp_path / ".wright/apps" / (parsed.manifest_id + ".surface.json")
    assert json.loads(path.read_bytes()) == value
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize(
    "change",
    [
        "command",
        "inventory",
        "environment",
        "capabilities",
        "isolation",
        "vault",
        "relative",
    ],
)
def test_relocation_does_not_accept_changed_launch_or_authority(tmp_path, change):
    _, digest = stored(tmp_path)
    value, parsed = process_ui_manifest(str(tmp_path), manifest(), digest)
    altered = copy.deepcopy(value)
    if change == "command":
        altered["launch"]["argv"][2] = "other.runtime"
    elif change == "inventory":
        altered["launch"]["argv"][6] = "f" * 64
    elif change == "environment":
        altered["launch"]["environment"] = {"OTHER_RUNTIME": "true"}
    elif change == "capabilities":
        altered["capabilities"] = ["wright.tool.call"]
    elif change == "isolation":
        altered["presentation"]["browser"] = True
    elif change == "vault":
        altered["launch"]["argv"][4] += "-other"
    else:
        altered["launch"]["argv"][0] = "relative-python"
    ProcessInterfacePresentations._install_manifest(
        str(tmp_path), altered, parse_live_app_manifest(altered)
    )
    path = tmp_path / ".wright/apps" / (parsed.manifest_id + ".surface.json")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        ProcessInterfacePresentations._install_manifest(str(tmp_path), value, parsed)
    assert path.read_bytes() == before


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
