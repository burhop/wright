"""Customer setup controls exercise real preparation/storage, without provider calls."""

import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from workspace_service import handle_setup_resources as resources
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.engineering_workflow_templates import (
    EngineeringWorkflowTemplateCatalog,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.handle_setup import (
    PrintedHandleSetup,
    SetupScope,
    SetupProposalRequest,
    SetupAcceptRequest,
)
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow
from workspace_service.workflow_sources import (
    WorkspaceWorkflowSourceUseCases,
    WorkflowSourceStorageError,
)


requires_posix_recipe = pytest.mark.skipif(
    os.name == "nt",
    reason="Installed Printed02 recipe requires an exact shared POSIX workspace mount; native rejection is tested separately",
)


async def fixture(root):
    root.mkdir(exist_ok=True)
    executor = BoundedExecutor()
    defaults = load_default_workflow_instructions().model_dump(mode="json")
    sources = WorkspaceWorkflowSourceUseCases(
        executor, instruction_defaults=lambda _: {"instructions": defaults}
    )
    templates = EngineeringWorkflowTemplateService(sources)
    template = (
        EngineeringWorkflowTemplateCatalog().get("replacement-drawer-handle").template
    )
    instance = await templates.instantiate(
        workspace_id="workspace-setup",
        workspace_dir=str(root),
        template_id=template.template_id,
        template_version=template.version,
        expected_source_digest=template.source_digest,
        workflow_path="workflows/handle.workflow.wflow",
        request_id="setup-request-001",
        created_by="local-test",
    )
    scope = {
        "session_id": "fixture-session",
        "path": instance.document.path,
        "expected_storage_revision": instance.document.storage_revision,
        "expected_storage_digest": instance.document.storage_digest,
    }
    available = [
        {
            "server_id": "fixture-" + role,
            "name": "fixture-" + role + "__" + value["tool_name"],
            **value,
        }
        for role, value in resources.contract()["tools"].items()
    ]
    profile = json.loads(
        (
            resources.PACKAGE
            / "process_validation/profiles/printed-replacement-part-02.json"
        ).read_bytes()
    )
    profiles = {}
    for role in ("machine", "process", "filament"):
        values = {
            item["selector"].removeprefix("/"): item["constraint"]["expected"]
            for item in profile["checks"]
            if item["subject_role"] == role + "_profile"
            and item["reader"] == "structured"
        }
        if role == "process":
            values["tree_support_wall_count"] = "-1"
            (root / "process_original.json").write_text(json.dumps(values))
            profiles["process_original"] = {"path": "process_original.json"}
            values["tree_support_wall_count"] = "0"
            role = "process_orca"
        (root / (role + ".json")).write_text(json.dumps(values))
        profiles[role] = {"path": role + ".json"}
    request = SetupProposalRequest(
        **scope,
        tools={
            role: {key: tool[key] for key in ("server_id", "name", "schema_digest")}
            for role, tool in zip(resources.contract()["tools"], available)
        },
        workspace_mount=str(root),
        profiles=profiles,
        selected_orientation="pads_down",
    )
    return (
        PrintedHandleSetup(sources, executor),
        sources,
        executor,
        instance,
        available,
        request,
    )


@requires_posix_recipe
def test_installed_customer_setup_proposes_then_cas_accepts_without_execution(tmp_path):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            scope = SetupScope.model_validate(
                request.model_dump(include=set(SetupScope.model_fields))
            )
            options = await setup.options(
                "workspace-setup", str(tmp_path), scope, available
            )
            assert options["profiles"]["mode"] == "workspace_files"
            assert len(options["tools"]["geometry"]) == 1
            origin = await sources.read_template_origin(str(tmp_path), request.path)
            proposal = await setup.propose(
                "workspace-setup", str(tmp_path), request, available
            )
            assert (
                await sources.read(str(tmp_path), request.path)
            ) == instance.document
            assert proposal["workspace_id"] == "workspace-setup"
            assert len(proposal["dependencies"]) <= 128
            assert proposal["summary"]["step_count"] == 16
            before = next(
                b for b in _parse(instance.document.source) if b["kind"] == "workflow"
            )
            after = next(
                b for b in _parse(proposal["source"]) if b["kind"] == "workflow"
            )
            assert (
                after == before
            )  # Includes the exact persisted default instruction collection.
            plan = compile_prompt_workflow(proposal["source"])
            assert len(plan.steps) == 16
            validator = next(
                block["fields"]["settings"]["validation"]
                for block in _parse(proposal["source"])
                if "validation" in block["fields"].get("settings", {})
            )
            assert validator["budget"] == {
                "max_bytes": 33554432,
                "max_entities": 1000000,
                "timeout_seconds": 120,
                "memory_limit_mb": 512,
            }
            construction = next(
                block["fields"]["settings"]
                for block in _parse(proposal["source"])
                if block["fields"].get("settings", {}).get("mcp_server")
                == "fixture-construction"
            )
            assert construction["mcp_tool"] == "fixture-construction__execute_code"
            assert (
                construction["mcp_schema_digest"]
                == (resources.contract()["tools"]["construction"]["schema_digest"])
            )
            assert {
                Path(value).name
                for value in construction["expected_files"].splitlines()
            } == {
                "source_mesh.stl",
                "source-native.brep",
                "native-geometry-observations.json",
            }
            original_profile = json.loads(
                (
                    resources.PACKAGE
                    / "process_validation/profiles/printed-replacement-part-02.json"
                ).read_bytes()
            )
            full_profile = next(
                item
                for item in proposal["dependencies"]
                if item["path"].endswith("/orca-full-profile.json")
            )
            derived_profile = json.loads((tmp_path / full_profile["path"]).read_bytes())
            assert derived_profile["baseline"] == original_profile["baseline"]
            assert len(derived_profile["checks"]) == 43
            for check in original_profile["checks"]:
                if check["id"] != "slice-lineage":
                    assert check in derived_profile["checks"]
            assert '"tool":"test_handoff"' not in proposal["source"]
            assert '"tool":"local_simulate_handoff"' in proposal["source"]

            selected_tools = {
                section["fields"].get("settings", {}).get("mcp_tool")
                for section in _parse(proposal["source"])
            }
            assert "write_text_document" not in selected_tools
            assert "inspect_file" not in selected_tools
            original_prompt = (
                resources.PACKAGE
                / "engineering_workflow_templates/inputs/replacement-drawer-handle/prompt.txt"
            ).read_bytes()
            # Find the full provider arguments by their contract, without assuming a port filename.
            calls = []
            for item in proposal["dependencies"]:
                if item["path"].endswith(".json"):
                    value = json.loads((tmp_path / item["path"]).read_bytes())
                    if isinstance(value, dict) and set(value) == {
                        "code",
                        "user_prompt",
                    }:
                        calls.append(value)
            assert len(calls) == 2  # Blender repair call and its review copy.
            assert all(
                call["user_prompt"].encode() == original_prompt for call in calls
            )
            assert original_prompt.count(b"\r\n") == 3
            assert not list(tmp_path.rglob("*.stl"))
            assert not (tmp_path / ".wright/workflow-runs").exists()
            accept = SetupAcceptRequest(
                **scope.model_dump(),
                proposal_id=proposal["proposal_id"],
                proposal_digest=proposal["proposal_digest"],
            )
            accepted = await setup.accept(
                "workspace-setup", str(tmp_path), accept, available
            )
            assert accepted.source == proposal["source"]
            assert accepted.storage_revision == instance.document.storage_revision + 1
            assert (
                await sources.read_template_origin(str(tmp_path), request.path)
            ) == origin
            assert accepted.layout_status == "stale"
            with pytest.raises(WorkflowSourceStorageError):
                await setup.accept("workspace-setup", str(tmp_path), accept, available)
        finally:
            await executor.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "fault",
    [
        "tool",
        "mount",
        pytest.param("profile", marks=requires_posix_recipe),
        pytest.param("original_input", marks=requires_posix_recipe),
        "source_scope",
    ],
)
def test_setup_rejects_incompatible_inputs_before_acceptance(tmp_path, fault):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            if fault == "tool":
                available = []
            if fault == "mount":
                request.workspace_mount = "/work"
            if fault == "profile":
                (tmp_path / "filament.json").write_text('{"filament_type":["PLA"]}')
            if fault == "original_input":
                origin = await sources.read_template_origin(str(tmp_path), request.path)
                (tmp_path / origin["template_inputs"][0]["path"]).write_text("changed")
            if fault == "source_scope":
                request.expected_storage_digest = "f" * 64
            with pytest.raises(WorkflowSourceStorageError):
                await setup.propose(
                    "workspace-setup", str(tmp_path), request, available
                )
            assert (
                await sources.read(str(tmp_path), request.path)
            ) == instance.document
            assert not (tmp_path / ".wright/workflow-runs").exists()
        finally:
            await executor.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "fault",
    [
        "dependency",
        "manifest",
        "tool",
        "construction_only",
        "recipe",
        "workspace",
        "source",
    ],
)
@requires_posix_recipe
def test_setup_accept_rechecks_scope_snapshots_recipe_and_enabled_tools(
    tmp_path, fault, monkeypatch
):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            proposal = await setup.propose(
                "workspace-setup", str(tmp_path), request, available
            )
            scope = request.model_dump(include=set(SetupScope.model_fields))
            accept = SetupAcceptRequest(
                **scope,
                proposal_id=proposal["proposal_id"],
                proposal_digest=proposal["proposal_digest"],
            )
            if fault == "dependency":
                (tmp_path / proposal["dependencies"][0]["path"]).write_bytes(b"changed")
            if fault == "manifest":
                (
                    tmp_path
                    / ".wright/handle-setup"
                    / proposal["proposal_id"]
                    / "proposal.json"
                ).write_bytes(b"{}")
            if fault == "tool":
                available = []
            if fault == "construction_only":
                available = [
                    tool
                    for tool in available
                    if tool["server_id"] != "fixture-construction"
                ]
            if fault == "recipe":
                monkeypatch.setattr(
                    resources, "recipe_identity", lambda: {"id": "changed"}
                )
            if fault == "source":
                accept.expected_storage_revision += 1
            with pytest.raises(WorkflowSourceStorageError):
                await setup.accept(
                    "other-workspace" if fault == "workspace" else "workspace-setup",
                    str(tmp_path),
                    accept,
                    available,
                )
            assert (
                await sources.read(str(tmp_path), request.path)
            ) == instance.document
        finally:
            await executor.close()

    asyncio.run(run())


def test_setup_request_rejects_arbitrary_geometry_code_and_unknown_fields():
    with pytest.raises(ValidationError):
        SetupScope(
            session_id="s",
            path="workflows/a.workflow.wflow",
            expected_storage_revision=1,
            expected_storage_digest="a" * 64,
            code="arbitrary()",
        )


@requires_posix_recipe
def test_installed_resource_tree_has_no_repository_or_dataset_dependency(
    tmp_path, monkeypatch
):
    """Reproduce distribution mappings in an isolated tree, then run full preparation."""
    package = tmp_path / "installed/workspace_service"
    package.mkdir(parents=True)
    mapping = json.loads(
        (resources.PACKAGE / "handle_setup_resources.json").read_bytes()
    )
    shutil.copyfile(
        resources.PACKAGE / "handle_setup_resources.json",
        package / "handle_setup_resources.json",
    )
    for item in mapping["files"]:
        target = (
            package / "engineering_workflow_templates/setup_resources" / item["target"]
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resources.recipe_root() / item["target"], target)
    for row in resources.inventory():
        if row["resource"] in [item["target"] for item in mapping["files"]]:
            continue
        relative = row["resource"]
        if relative.startswith("inputs/"):
            relative = (
                "engineering_workflow_templates/inputs/replacement-drawer-handle/"
                + relative.removeprefix("inputs/")
            )
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resources.PACKAGE / relative, target)
    shutil.copyfile(
        resources.PACKAGE
        / "engineering_workflow_templates/inputs/replacement-drawer-handle/rights.json",
        package
        / "engineering_workflow_templates/inputs/replacement-drawer-handle/rights.json",
    )
    original = resources.recipe_identity()
    monkeypatch.setattr(resources, "PACKAGE", package)
    assert resources.recipe_identity() == original
    assert "installed" in str(resources.recipe_root())

    async def run():
        workspace = tmp_path / "workspace"
        setup, sources, executor, instance, available, request = await fixture(
            workspace
        )
        try:
            proposal = await setup.propose(
                "workspace-setup", str(workspace), request, available
            )
            assert proposal["summary"]["step_count"] == 16
            assert proposal["recipe"] == original
            assert not (tmp_path / "tests").exists()
        finally:
            await executor.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "outside", ["../outside.json", "/tmp/outside.json", "linked.json"]
)
@requires_posix_recipe
def test_setup_profiles_cannot_escape_workspace(tmp_path, outside):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            if outside == "linked.json":
                (tmp_path / outside).symlink_to(tmp_path / "machine.json")
            request.profiles.machine.path = outside
            with pytest.raises(ValueError):
                await setup.propose(
                    "workspace-setup", str(tmp_path), request, available
                )
            assert (
                await sources.read(str(tmp_path), request.path)
            ) == instance.document
            assert not (tmp_path / ".wright/handle-setup").exists()
        finally:
            await executor.close()

    asyncio.run(run())


@requires_posix_recipe
def test_profile_snapshot_is_explicit_and_remains_stable_when_original_is_edited(
    tmp_path,
):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            proposal = await setup.propose(
                "workspace-setup", str(tmp_path), request, available
            )
            original = (tmp_path / "machine.json").read_bytes()
            (tmp_path / "machine.json").write_bytes(b'{"changed":true}')
            snapshot = proposal["profiles"]["machine"]
            assert (tmp_path / snapshot["snapshot_path"]).read_bytes() == original
            assert snapshot["sha256"] == hashlib.sha256(original).hexdigest()
            accept = SetupAcceptRequest(
                **request.model_dump(include=set(SetupScope.model_fields)),
                proposal_id=proposal["proposal_id"],
                proposal_digest=proposal["proposal_digest"],
            )
            accepted = await setup.accept(
                "workspace-setup", str(tmp_path), accept, available
            )
            assert accepted.source == proposal["source"]
        finally:
            await executor.close()

    asyncio.run(run())


@pytest.mark.parametrize("fault", ["missing", "disabled", "schema"])
def test_setup_requires_exact_construction_capability_before_staging(tmp_path, fault):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            if fault == "missing":
                body = request.model_dump()
                del body["tools"]["construction"]
                with pytest.raises(ValidationError):
                    SetupProposalRequest.model_validate(body)
            else:
                if fault == "disabled":
                    available = [
                        tool
                        for tool in available
                        if tool["server_id"] != "fixture-construction"
                    ]
                else:
                    available[0] = {**available[0], "schema_digest": "f" * 64}
                with pytest.raises(WorkflowSourceStorageError, match="construction"):
                    await setup.propose(
                        "workspace-setup", str(tmp_path), request, available
                    )
            assert await sources.read(str(tmp_path), request.path) == instance.document
            assert not (tmp_path / ".wright/handle-setup").exists()
        finally:
            await executor.close()

    asyncio.run(run())


@pytest.mark.parametrize("mount", ["native", "windows", "different"])
def test_setup_rejects_unqualified_mount_without_staging(tmp_path, mount):
    async def run():
        setup, sources, executor, instance, available, request = await fixture(tmp_path)
        try:
            request.workspace_mount = {
                "native": str(tmp_path),
                "windows": r"C:\wright\workspace",
                "different": "/different-workspace",
            }[mount]
            if mount == "native" and os.name != "nt":
                proposal = await setup.propose(
                    "workspace-setup", str(tmp_path), request, available
                )
                assert proposal["summary"]["step_count"] == 16
                assert (
                    await sources.read(str(tmp_path), request.path) == instance.document
                )
                assert not (tmp_path / ".wright/workflow-runs").exists()
                return
            with pytest.raises(
                WorkflowSourceStorageError, match="exact managed POSIX workspace path"
            ):
                await setup.propose(
                    "workspace-setup", str(tmp_path), request, available
                )
            assert await sources.read(str(tmp_path), request.path) == instance.document
            assert not (tmp_path / ".wright/handle-setup").exists()
            assert not (tmp_path / ".wright/workflow-runs").exists()
            assert not list(tmp_path.rglob("*.stl"))
        finally:
            await executor.close()

    asyncio.run(run())
