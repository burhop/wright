"""Installed Printed02 setup: inspectable source proposals, then existing source CAS.

This application use case invokes no model, provider, review, or workflow runner.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from . import handle_setup_resources as resources
from .adapters.filesystem import LocalWorkspaceFiles
from .workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)
from .workflow_sources import WorkflowSourceStorageError
from .workspace_path import WorkspacePath

DIGEST = r"^[0-9a-f]{64}$"
PROFILE_ROLES = ("machine", "process_original", "process_orca", "filament")
MAX_FILE = 1024 * 1024
MAX_MANIFEST = 2 * 1024 * 1024


class SetupScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=256)
    path: str = Field(pattern=r"^workflows/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$")
    expected_storage_revision: int = Field(ge=1, strict=True)
    expected_storage_digest: str = Field(pattern=DIGEST)


class SetupTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    server_id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    schema_digest: str = Field(pattern=DIGEST)


class SetupTools(BaseModel):
    model_config = ConfigDict(extra="forbid")
    construction: SetupTool
    geometry: SetupTool
    slicer: SetupTool
    inspection: SetupTool


class SetupFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1, max_length=512)


class SetupProfiles(BaseModel):
    model_config = ConfigDict(extra="forbid")
    machine: SetupFile
    process_original: SetupFile
    process_orca: SetupFile
    filament: SetupFile


class SetupProposalRequest(SetupScope):
    tools: SetupTools
    workspace_mount: str = Field(min_length=1, max_length=1024)
    profiles: SetupProfiles
    selected_orientation: Literal["pads_down", "side"]


class SetupAcceptRequest(SetupScope):
    proposal_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    proposal_digest: str = Field(pattern=DIGEST)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()


def fail(message: str, *, conflict=False):
    raise WorkflowSourceStorageError(
        "handle_setup_conflict" if conflict else "handle_setup_invalid", message
    )


def read_bounded(paths, path, limit=MAX_FILE):
    target = paths.resolve(path, must_exist=True)
    if not target.is_file() or not 0 < target.stat().st_size <= limit:
        fail("Setup file is missing, empty or exceeds its size bound: " + path)
    with target.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        fail("Setup file changed beyond its size bound: " + path)
    return raw


def _source(sections):
    return (
        "\n\n".join(
            item["kind"]
            + " "
            + item["id"]
            + "\n"
            + "\n".join(
                "  "
                + key
                + ": "
                + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                for key, value in item["fields"].items()
            )
            + "\nend"
            for item in sections
        )
        + "\n"
    )


def _select_tools(available, requested=None):
    chosen, options = {}, {}
    for role, expected in resources.contract()["tools"].items():
        matches = [
            tool
            for tool in available
            if tool.get("tool_name") == expected["tool_name"]
            and tool.get("schema_digest") == expected["schema_digest"]
        ]
        options[role] = [
            {
                key: tool[key]
                for key in ("server_id", "name", "tool_name", "schema_digest")
            }
            for tool in matches
        ]
        if requested is not None:
            selected = getattr(requested, role).model_dump()
            exact = [
                tool
                for tool in matches
                if all(tool.get(key) == value for key, value in selected.items())
            ]
            if len(exact) != 1:
                fail(
                    "The selected "
                    + role
                    + " tool or schema is unavailable; enable the qualified provider for this workspace and prepare again",
                    conflict=True,
                )
            chosen[role] = exact[0]
    return chosen, options


class PrintedHandleSetup:
    def __init__(self, sources, executor):
        self.sources = sources
        self.executor = executor

    async def _scope(self, workspace_id, workspace_dir, body):
        document = await self.sources.read(workspace_dir, body.path)
        if (
            document.storage_revision != body.expected_storage_revision
            or document.storage_digest != body.expected_storage_digest
        ):
            fail("The accepted source changed; reload it before setup", conflict=True)
        origin = await self.sources.read_template_origin(workspace_dir, body.path)
        if (
            not origin
            or origin.get("template_id") != "replacement-drawer-handle"
            or origin.get("workspace_id") != workspace_id
        ):
            fail(
                "Setup requires an instantiated replacement-drawer-handle starter in this workspace"
            )
        if origin.get("instantiated_source_digest") != document.storage_digest:
            fail(
                "This bounded setup applies to the unchanged starter; preserve edited work and instantiate a fresh starter"
            )
        blocks = _parse(document.source)
        workflow = next(item for item in blocks if item["kind"] == "workflow")
        if "workflow." + workflow["id"] != origin.get("workflow_id"):
            fail("The starter workflow identity changed", conflict=True)
        return document, origin, workflow

    async def options(self, workspace_id, workspace_dir, body, available):
        _, _, workflow = await self._scope(workspace_id, workspace_dir, body)
        _, options = _select_tools(available)
        return {
            "workspace_id": workspace_id,
            "path": body.path,
            "workflow_id": workflow["id"],
            "recipe": resources.recipe_identity(),
            "workspace_mount": str(WorkspacePath(workspace_dir).root),
            "tools": options,
            "profiles": {"mode": "workspace_files", "roles": list(PROFILE_ROLES)},
            "requirements": resources.contract()["requirements"],
        }

    async def propose(self, workspace_id, workspace_dir, body, available):
        document, origin, workflow = await self._scope(
            workspace_id, workspace_dir, body
        )
        chosen, _ = _select_tools(available, body.tools)
        return await self.executor.run_to_completion(
            "workspace.handle_setup.propose",
            lambda: self._prepare(
                workspace_id,
                workspace_dir,
                body,
                available,
                chosen,
                document,
                origin,
                workflow,
            ),
        )

    def _prepare(
        self,
        workspace_id,
        workspace_dir,
        body,
        available,
        chosen,
        document,
        origin,
        workflow,
    ):
        paths = WorkspacePath(workspace_dir)
        if body.workspace_mount != str(paths.root) or not re.fullmatch(
            r"/[A-Za-z0-9_/-]+", body.workspace_mount
        ):
            fail(
                "This qualified recipe requires every provider to mount the exact managed POSIX workspace path (without spaces): "
                + str(paths.root)
            )
        # Diagnose changed supplied inputs before staging any proposal.
        for item in origin.get("template_inputs", []):
            if digest(read_bounded(paths, item["path"])) != item["sha256"]:
                fail(
                    "A supplied starter input changed; preserve it as a separate authored process rather than replacing its requirements",
                    conflict=True,
                )
        profile_raw = {}
        for role in PROFILE_ROLES:
            path = getattr(body.profiles, role).path
            if not path.endswith(".json"):
                fail("Select a workspace JSON profile for " + role)
            raw = read_bounded(paths, path)
            try:
                value = json.loads(raw)
            except (ValueError, UnicodeError):
                fail("The selected profile is not valid JSON: " + role)
            if not isinstance(value, dict):
                fail("The selected profile must be a JSON object: " + role)
            profile_raw[role] = raw
        proposal_id = uuid.uuid4().hex
        attempt = "setup-" + proposal_id
        staging = ".wright/handle-setup/" + proposal_id
        files = LocalWorkspaceFiles(workspace_dir)

        def write(name, raw):
            path = staging + "/" + name
            actual = files.write_generated(path, raw, "indexed")
            if actual != path:
                fail(
                    "Fresh setup storage collided; retained files were not overwritten",
                    conflict=True,
                )
            return {"path": str(paths.resolve(path)), "sha256": digest(raw)}

        profile_refs = {
            role: write(role + ".json", raw) for role, raw in profile_raw.items()
        }
        geometry = resources.recipe_root() / "printed-replacement-part/handle-geometry"
        basis_raw = (geometry / "basis.json").read_bytes()
        basis = json.loads(basis_raw)
        relative_output = (
            "process-proofs/printed-replacement-part/" + attempt + "/outputs"
        )
        basis["binding"].update(
            proposed_selected_mount=body.workspace_mount,
            proposed_attempt=attempt,
            expected_relative_output=relative_output + "/{{wright.run_id}}",
        )
        basis["setup_provenance"] = {
            "recipe": resources.recipe_identity(),
            "generic_basis_sha256": digest(basis_raw),
            "workspace_id": workspace_id,
            "source_digest": document.storage_digest,
            "attempt": attempt,
        }
        operations = {"basis": write("basis.json", encode(basis))}
        original_line = "OUTPUT_ROOT = '/WRIGHT_HANDLE_OUTPUTS/' + RUN_ID"
        for role in ("construction", "repair"):
            raw = (geometry / (role + ".json")).read_bytes()
            operation = json.loads(raw)
            if (
                set(operation) != {"code"}
                or operation["code"].count(original_line) != 1
            ):
                fail("The trusted geometry asset has an unsupported output binding")
            operation["code"] = operation["code"].replace(
                original_line,
                "OUTPUT_ROOT = "
                + repr(body.workspace_mount + "/" + relative_output + "/")
                + " + RUN_ID",
            )
            operations[role] = write(role + ".json", encode(operation))
        bindings = {
            "construction_binding": {
                "server": chosen["construction"]["server_id"],
                "tool": chosen["construction"]["tool_name"],
                "outputs": resources.contract()["construction_outputs"],
            },
            "geometry_server": chosen["geometry"]["server_id"],
            "inspection_server": chosen["inspection"]["server_id"],
            "inspection_backend": "skfem",
            "slicer_server": chosen["slicer"]["server_id"],
            "scenario_id": "printed-replacement-part-02",
            "workflow_id": workflow["id"],
            "run_path_template": "wright.run-path/1",
            "orientation_comparison": True,
            "geometry_operation_mode": "configured_tool",
            "geometry_operation_files": operations,
            "inspection_workspace": body.workspace_mount,
            "profiles": {
                "machine": profile_refs["machine"],
                "process": profile_refs["process_orca"],
                "filament": profile_refs["filament"],
            },
            "slice_binding": {
                "kind": "orca-shell-3mf-v1",
                "engine_version": "2.4.2",
                "executable": "/opt/orca/AppRun",
                "workspace_mount": body.workspace_mount,
                "selected_orientation": body.selected_orientation,
                "original_process_profile": profile_refs["process_original"],
            },
            "geometry_guidance": resources.contract()["geometry_guidance"],
            "validation_resource_budget": resources.contract()[
                "validation_resource_budget"
            ],
            "simulator_destination": "test://setup-placeholder/not-executable",
        }
        write("bindings.json", encode(bindings))
        paths.resolve("process-proofs/printed-replacement-part/" + attempt)
        try:
            prepared = resources.load_preparer().prepare(
                paths.root, attempt, available, bindings
            )
        except (ValueError, KeyError, TypeError) as error:
            fail(
                "Profile or recipe compatibility failed; retained setup files are not accepted: "
                + str(error)
            )
        prepared_raw = read_bounded(paths, prepared["source_path"])
        sections = _parse(prepared_raw.decode())
        target_workflow = next(item for item in sections if item["kind"] == "workflow")
        target_workflow["fields"].update(deepcopy(workflow["fields"]))
        from .workflow_external_actions import (
            LOCAL_SIMULATION_BINDING,
            LOCAL_SIMULATION_DESTINATION,
        )

        transfer = [
            item
            for item in sections
            if item["fields"]
            .get("settings", {})
            .get("approval_binding", {})
            .get("tool")
            == "test_handoff"
        ]
        if len(transfer) != 1:
            fail("The recipe transfer declaration is ambiguous")
        settings = transfer[0]["fields"]["settings"]
        settings.update(
            approval_binding=deepcopy(LOCAL_SIMULATION_BINDING),
            approval_destination=deepcopy(LOCAL_SIMULATION_DESTINATION),
            approval_settings={"simulation": True},
            approval_action={
                "kind": "printer_transfer",
                "mode": "local_simulation",
                "simulation": True,
            },
        )
        source = _source(sections)
        validate_workspace_authoring_shape(source)
        plan = compile_prompt_workflow(source)
        source_ref = write("proposal.workflow.wflow", source.encode())
        dependencies = []
        for directory in (
            staging,
            "process-proofs/printed-replacement-part/" + attempt,
        ):
            for candidate in sorted(paths.resolve(directory).rglob("*")):
                if candidate.is_file():
                    relative = candidate.relative_to(paths.root).as_posix()
                    raw = read_bounded(paths, relative)
                    dependencies.append(
                        {
                            "path": relative,
                            "sha256": digest(raw),
                            "size_bytes": len(raw),
                        }
                    )
        value = {
            "schema_version": 1,
            "workspace_id": workspace_id,
            "path": body.path,
            "proposal_id": proposal_id,
            "recipe": resources.recipe_identity(),
            "workflow_id": workflow["id"],
            "expected_storage_revision": document.storage_revision,
            "expected_storage_digest": document.storage_digest,
            "source": source,
            "source_digest": source_ref["sha256"],
            "tools": body.tools.model_dump(),
            "dependencies": dependencies,
            "profiles": {
                role: {
                    "original_path": getattr(body.profiles, role).path,
                    "snapshot_path": str(Path(ref["path"]).relative_to(paths.root)),
                    "sha256": ref["sha256"],
                }
                for role, ref in profile_refs.items()
            },
            "summary": {
                "changes": [
                    "Bind the supplied Printed02 scenario to the selected exact tools and four profile snapshots.",
                    "Preserve the original workflow identity and saved workflow instruction collection.",
                    "Keep design and geometry review before slicing; compare pads-down and side; use a manual local simulated transfer.",
                ],
                "limitations": resources.contract()["requirements"],
                "selected_orientation": body.selected_orientation,
                "step_count": len(plan.steps),
                "engineering_acceptance": False,
                "physical_dispatch": False,
            },
            "transformation": {
                "prepared_source_sha256": digest(prepared_raw),
                "accepted_proposal_sha256": source_ref["sha256"],
                "preserved_workflow_fields": list(workflow["fields"]),
                "transfer_binding": LOCAL_SIMULATION_BINDING,
            },
        }
        raw = encode(value)
        if len(raw) > MAX_MANIFEST or len(dependencies) > 128:
            fail("Setup proposal exceeds its bounded inventory")
        write("proposal.json", raw)
        return {**value, "proposal_digest": digest(raw)}

    async def accept(self, workspace_id, workspace_dir, body, available):
        await self._scope(workspace_id, workspace_dir, body)

        def verify():
            paths = WorkspacePath(workspace_dir)
            raw = read_bounded(
                paths,
                ".wright/handle-setup/" + body.proposal_id + "/proposal.json",
                MAX_MANIFEST,
            )
            if digest(raw) != body.proposal_digest:
                fail(
                    "The setup proposal changed; inspect a fresh proposal",
                    conflict=True,
                )
            value = json.loads(raw)
            for key, expected in {
                "workspace_id": workspace_id,
                "path": body.path,
                "proposal_id": body.proposal_id,
                "expected_storage_revision": body.expected_storage_revision,
                "expected_storage_digest": body.expected_storage_digest,
                "recipe": resources.recipe_identity(),
            }.items():
                if value.get(key) != expected:
                    fail(
                        "The setup proposal scope, source or recipe changed; prepare again",
                        conflict=True,
                    )
            _select_tools(available, SetupTools.model_validate(value["tools"]))
            if (
                not isinstance(value["dependencies"], list)
                or len(value["dependencies"]) > 128
            ):
                fail("Invalid setup dependency inventory")
            for item in value["dependencies"]:
                content = read_bounded(paths, item["path"])
                if (
                    digest(content) != item["sha256"]
                    or len(content) != item["size_bytes"]
                ):
                    fail("A setup dependency changed: " + item["path"], conflict=True)
            if digest(value["source"].encode()) != value["source_digest"]:
                fail("The proposed source changed", conflict=True)
            validate_workspace_authoring_shape(value["source"])
            compile_prompt_workflow(value["source"])
            return value["source"]

        source = await self.executor.run_to_completion(
            "workspace.handle_setup.verify", verify
        )
        return await self.sources.update(
            workspace_dir,
            body.path,
            expected_storage_revision=body.expected_storage_revision,
            expected_storage_digest=body.expected_storage_digest,
            semantic_change_validated=True,
            source=source,
        )
