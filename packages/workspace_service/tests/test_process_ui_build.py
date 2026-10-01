"""Fixed compiler and source/binding limits; real local compilation, no model."""

from dataclasses import replace
from pathlib import Path
import shutil
import asyncio
import json

import pytest

from core.process_interfaces import InterfaceBinding, InterfaceManifest, SourceEnvelope
from core.process_interactions import ProcessRef
from workspace_service.process_interfaces.build import (
    BuildToolchain,
    build_interface,
    validate_manifest_bindings,
)
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.resources import (
    AuthoringOutput,
    load_authoring_resources,
)

ROOT = Path(__file__).resolve().parents[3]


def reference():
    return ProcessRef(
        workspace_id="isolated-build",
        source_path="workflows/comparison.wflow",
        source_digest="a" * 64,
    )


def manifest(**changes):
    values = dict(
        ui_id="comparison-ui",
        revision_id="revision-one",
        title="Compare results",
        process=reference(),
        client_version="1.0.0",
        kit_version="1.0.0",
    )
    return InterfaceManifest(**(values | changes))


def toolchain():
    node = shutil.which("node")
    assert node, "This explicit local-compiler qualification requires installed Node"
    return BuildToolchain(
        Path(node), ROOT, ROOT / "packages/process_client", ROOT / "packages/ui_kit"
    )


def test_installed_role_resources_are_versioned_and_closed():
    first, second = load_authoring_resources(), load_authoring_resources()
    assert first == second
    assert first.version == "process-ui-author-1"
    assert "no executable tools" in first.instructions
    assert "another process executor" in first.instructions
    assert "default function App" in first.template
    assert set(first.output_schema["properties"]) == {"source", "manifest"}
    assert first.output_schema["additionalProperties"] is False
    result = AuthoringOutput.model_validate(
        {
            "source": {"files": {"App.tsx": first.template}},
            "manifest": manifest().model_dump(mode="json"),
        }
    )
    assert result.manifest.process == reference()


@pytest.mark.parametrize(
    "changes",
    [
        {"timeout_seconds": 0},
        {"timeout_seconds": 121},
        {"maximum_bundle_bytes": 0},
        {"maximum_bundle_bytes": 31_457_281},
    ],
)
def test_administrative_build_limits_are_bounded(changes):
    with pytest.raises(ValueError):
        replace(toolchain(), **changes)


def test_missing_compiler_is_actionable(tmp_path):
    with pytest.raises(ProcessInterfaceError) as exc:
        replace(toolchain(), node=tmp_path / "missing-node").describe()
    assert exc.value.reason.code == "CAPABILITY_UNAVAILABLE"


def test_model_repair_diagnostic_omits_private_host_locations(tmp_path):
    from workspace_service.process_interfaces.build import public_build_diagnostic

    configured = toolchain()
    message = (
        f"{tmp_path}/App.tsx: unknown import from {configured.client_root}/src/types.ts"
    )
    public = public_build_diagnostic(message, draft=tmp_path, toolchain=configured)
    assert str(tmp_path) not in public and str(configured.client_root) not in public
    assert "<interface>/App.tsx" in public and "<process-client>" in public


def test_toolchain_versions_match_current_lockfile():
    declared = toolchain().describe()["packages"]
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))[
        "packages"
    ]
    for name in ("typescript", "vite", "react", "react-dom"):
        assert declared[name]["version"] == lock[f"node_modules/{name}"]["version"]


def test_exact_catalog_binding_and_optional_absence():
    binding = InterfaceBinding(
        binding_id="brief-field",
        kind="input",
        selector="brief",
        block_id="brief",
        port_id="brief_out",
        expected_schema={"type": "string"},
    )
    catalog = [
        {
            "kind": "input",
            "selector": "brief",
            "block_id": "brief",
            "port_id": "brief_out",
            "expected_schema": {"type": "string"},
        }
    ]
    assert (
        validate_manifest_bindings(manifest(bindings=(binding,)), reference(), catalog)
        == ()
    )
    for field, value in [
        ("port_id", "wrong"),
        ("block_id", "wrong"),
        ("expected_schema", {"type": "number"}),
    ]:
        wrong = binding.model_copy(update={field: value})
        with pytest.raises(ProcessInterfaceError):
            validate_manifest_bindings(
                manifest(bindings=(wrong,)), reference(), catalog
            )
    optional = binding.model_copy(
        update={"required": False, "fallback": "Show common results instead."}
    )
    reasons = validate_manifest_bindings(
        manifest(bindings=(optional,)), reference(), []
    )
    assert reasons[0].binding_id == "brief-field"
    assert reasons[0].correction == optional.fallback
    with pytest.raises(ProcessInterfaceError):
        validate_manifest_bindings(
            manifest(bindings=(binding,)), reference(), catalog + catalog
        )


def test_wrong_process_or_versions_rejected():
    with pytest.raises(ProcessInterfaceError):
        validate_manifest_bindings(
            manifest(), reference().model_copy(update={"workspace_id": "other"}), []
        )
    with pytest.raises(ProcessInterfaceError):
        validate_manifest_bindings(manifest(client_version="2.0.0"), reference(), [])


@pytest.mark.asyncio
async def test_reference_compiles_with_public_packages_and_no_generated_scripts(
    tmp_path,
):
    resources = load_authoring_resources()
    output = await build_interface(
        source=SourceEnvelope(files={"App.tsx": resources.template}),
        manifest=manifest(),
        process=reference(),
        catalog=[],
        toolchain=toolchain(),
        builds_root=tmp_path,
    )
    assert output.report.state == "built", output.report.diagnostics
    assert output.dist and (output.dist / "app.js").is_file()
    assert output.report.bundled_bytes > 0
    assert output.report.bundle_digest
    assert not (output.root / "package.json").exists()
    assert not (output.root / "vite.config.js").exists()
    assert (output.root / "build-report.json").is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source",
    [
        "import x from 'node:fs'; export default function App(){return null}",
        "import x from '../../apps/web/private'; export default function App(){return null}",
        "export default function App(){import('react');return null}",
        "export default function App(){fetch('/admin');return null}",
        "export default function App(){return <a href='https://example.invalid'>Link</a>}",
        "export default function App(){return new Function('return 1')()}",
        "const value: number = 'wrong type'; export default function App(){return null}",
    ],
)
async def test_fixed_compiler_rejects_private_dynamic_network_or_invalid_source(
    tmp_path, source
):
    output = await build_interface(
        source=SourceEnvelope(files={"App.tsx": source}),
        manifest=manifest(),
        process=reference(),
        catalog=[],
        toolchain=toolchain(),
        builds_root=tmp_path,
    )
    assert output.report.state == "failed"
    assert output.report.diagnostics
    assert output.dist is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "css",
    [
        "@import 'remote.css';",
        "p {background:url(https://example.invalid/a.png)}",
        "p {width:expression(alert(1))}",
    ],
)
async def test_css_cannot_fetch_or_execute(tmp_path, css):
    output = await build_interface(
        source=SourceEnvelope(
            files={
                "App.tsx": "export default function App(){return null}",
                "style.css": css,
            }
        ),
        manifest=manifest(),
        process=reference(),
        catalog=[],
        toolchain=toolchain(),
        builds_root=tmp_path,
    )
    assert output.report.state == "failed"
    assert output.dist is None


@pytest.mark.asyncio
@pytest.mark.parametrize("condition", ["timeout", "overflow", "cancel"])
async def test_builder_bounds_and_disposes_its_owned_child(
    tmp_path, monkeypatch, condition
):
    entered = asyncio.Event()

    class Child:
        returncode = None
        killed = False

        @property
        def stdout(self):
            return self

        async def read(self, size):
            assert size == 262145
            entered.set()
            if condition == "overflow":
                return b"x" * size
            await asyncio.Event().wait()

        def kill(self):
            self.killed = True
            self.returncode = -9

        async def wait(self):
            return self.returncode

    child = Child()

    async def create(*argv, **kwargs):
        assert argv[0] == str(toolchain().node)
        assert argv[1].endswith("wright-fixed-builder.mjs")
        assert kwargs["stdin"] == asyncio.subprocess.DEVNULL
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    task = asyncio.create_task(
        build_interface(
            source=SourceEnvelope(
                files={"App.tsx": "export default function App(){return null}"}
            ),
            manifest=manifest(),
            process=reference(),
            catalog=[],
            toolchain=replace(toolchain(), timeout_seconds=1),
            builds_root=tmp_path,
        )
    )
    await entered.wait()
    if condition == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        result = await task
        assert result.report.state == "failed"
        assert result.dist is None
    assert child.killed
