"""Definition-only transfer through existing confined source and file storage."""

from __future__ import annotations

import base64
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from core.process_interactions import ProcessRef
from core.process_validation import ValidationProfile, canonical_digest, canonical_json
from core.redaction import SECRET_KEY_RE
from core.workflow_bundle import (
    ASSET_MAX_BYTES,
    BundleAsset,
    BundleDependency,
    BundleDiagnostic,
    BundleInspection,
    PortableInterface,
    WorkflowBundle,
    portable_path,
)
from core.workflow_instructions import WorkflowInstructionSet
from data_vault.process_interface_repository import ProcessInterfaceRepository

from .process_interfaces.service import ProcessScope
from .process_validation.configuration import ValidatorConfiguration
from .workflow_source_execution import WorkflowSourceExecutionError, _parse
from .workflow_sources import (
    WorkspaceWorkflowSourceStore,
    WorkflowSourceStorageError,
    validate_source_layout,
)
from .workspace_path import WorkspacePath


class WorkflowBundleError(ValueError):
    pass


def _dependency_inventory(source: str) -> tuple[BundleDependency, ...]:
    """Discover dependencies from the source, never trust a supplied manifest."""
    sections = _parse(source)
    if sum(section["kind"] == "workflow" for section in sections) != 1:
        raise WorkflowBundleError("A bundle requires exactly one workflow declaration")
    dependencies: dict[tuple[str, str], BundleDependency] = {}

    def add(category, identity, **details):
        dependencies[(category, identity)] = BundleDependency(
            category=category,
            identity=identity,
            disposition="external",
            details=details,
        )

    for section in sections:
        fields = section["fields"]
        settings = fields.get("settings", {})
        if not isinstance(settings, dict):
            raise WorkflowBundleError("Workflow settings must be an object")
        if section["kind"] == "workflow":
            if "instructions" in fields:
                instructions = WorkflowInstructionSet.model_validate(
                    fields["instructions"]
                )
                dependencies[("instructions", "embedded")] = BundleDependency(
                    category="instructions",
                    identity="embedded",
                    disposition="embedded",
                    sha256=canonical_digest(instructions),
                    details={
                        "version": instructions.schema_version,
                        **(
                            {
                                "action_intent_contract": instructions.action_intent_contract
                            }
                            if instructions.action_intent_contract is not None
                            else {}
                        ),
                    },
                )
            else:
                add("instructions", "legacy-local-defaults", migration_required=True)
        if section["kind"] == "input" and settings.get("workspace_file"):
            add("reference", portable_path(settings["workspace_file"]))
        metadata = settings.get("interaction_input")
        if isinstance(metadata, dict) and metadata.get("option_source"):
            from .process_interfaces.options import OptionSource

            option = OptionSource.model_validate(metadata["option_source"])
            add(
                "provider",
                str(section["id"]) + ":options",
                server_id=option.server_id,
                tool_name=option.tool_name,
                schema_digest=option.schema_digest,
                qualification="requires-local-registry-review",
            )
        if "validation" in settings:
            raw = settings["validation"]
            config = ValidatorConfiguration.model_validate(
                json.loads(raw) if isinstance(raw, str) else raw
            )
            add(
                "validation_profile",
                config.profile.source + ":" + config.profile.name,
                configuration=config.model_dump(mode="json"),
            )
        server = settings.get("mcp_server") or settings.get("mcp_server_id")
        if server:
            tool = settings.get("mcp_tool", "")
            add(
                "provider",
                str(section["id"]),
                server_id=str(server),
                tool_name=str(tool),
                schema_digest=settings.get("mcp_schema_digest", ""),
                qualification="requires-local-registry-review",
            )
        if section["kind"] == "task" and fields.get("performed_by") == "ai_assisted":
            add(
                "model",
                str(section["id"]),
                requested_model=settings.get("model", "workspace-default"),
                output_format=settings.get("output_format", "text"),
                qualification="requires-local-adapter-readiness",
            )
    return tuple(dependencies.values())


def _credential_configuration(value):
    """Reject known credential configuration; never redact accepted instructions."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if (
                (
                    SECRET_KEY_RE.search(str(key))
                    or "access_code" in normalized
                    or "accesscode" in normalized
                )
                and isinstance(child, str)
                and child
            ):
                raise WorkflowBundleError(
                    "Credential configuration cannot be transferred in a workflow bundle"
                )
            _credential_configuration(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _credential_configuration(child)


def _check_source(source):
    try:
        sections = _parse(source)
    except WorkflowSourceExecutionError as exc:
        raise WorkflowBundleError(str(exc)) from exc
    for section in sections:
        _credential_configuration(section["fields"])
    return _dependency_inventory(source)


class WorkflowBundleService:
    def __init__(self, workspace):
        self.workspace = workspace

    async def export(
        self,
        workspace_id,
        workspace_dir,
        path,
        expected_storage_digest,
        *,
        mode="source",
        selected_reference_paths=(),
        selected_ui_ids=(),
        catalog=(),
    ):
        def build():
            store = WorkspaceWorkflowSourceStore(workspace_dir)
            document = store.read(path)
            if document.storage_digest != expected_storage_digest:
                raise WorkflowBundleError(
                    "The workflow changed; reopen it before exporting"
                )
            dependencies = list(_check_source(document.source))
            declared = {d.identity for d in dependencies if d.category == "reference"}
            selected = set(selected_reference_paths)
            if (
                len(selected) != len(selected_reference_paths)
                or not selected <= declared
            ):
                raise WorkflowBundleError(
                    "Select only unique reference files declared by this workflow"
                )
            if mode == "source" and (selected or selected_ui_ids):
                raise WorkflowBundleError(
                    "Select bundle mode to transfer assets or saved interfaces"
                )
            assets = []
            updated = []
            for dependency in dependencies:
                if (
                    dependency.category == "reference"
                    and dependency.identity in selected
                ):
                    content = store.read_artifact_bytes(
                        dependency.identity, max_bytes=ASSET_MAX_BYTES
                    )
                    if dependency.identity.endswith(".json"):
                        _credential_configuration(json.loads(content))
                    asset = BundleAsset(
                        path=dependency.identity,
                        sha256=hashlib.sha256(content).hexdigest(),
                        data_base64=base64.b64encode(content).decode("ascii"),
                    )
                    assets.append(asset)
                    dependency = dependency.model_copy(
                        update={"disposition": "embedded", "sha256": asset.sha256}
                    )
                if dependency.category == "validation_profile" and mode == "bundle":
                    config = ValidatorConfiguration.model_validate(
                        dependency.details["configuration"]
                    )
                    profile = config.load(workspace_dir)
                    dependency = dependency.model_copy(
                        update={
                            "disposition": "embedded",
                            "sha256": canonical_digest(profile),
                            "details": {
                                **dependency.details,
                                "profile": profile.model_dump(mode="json"),
                            },
                        }
                    )
                    if config.profile.source == "workspace":
                        content = store.read_artifact_bytes(
                            config.profile.name, max_bytes=ASSET_MAX_BYTES
                        )
                        assets.append(
                            BundleAsset(
                                path=config.profile.name,
                                sha256=hashlib.sha256(content).hexdigest(),
                                data_base64=base64.b64encode(content).decode("ascii"),
                            )
                        )
                if dependency.category == "provider":
                    matches = [
                        tool
                        for tool in catalog
                        if tool.get("server_id") == dependency.details["server_id"]
                        and (
                            not dependency.details["tool_name"]
                            or tool.get("name") == dependency.details["tool_name"]
                        )
                    ]
                    dependency = dependency.model_copy(
                        update={
                            "details": {
                                **dependency.details,
                                "qualified_operations": [
                                    {
                                        k: tool.get(k)
                                        for k in ("tool_name", "schema_digest")
                                    }
                                    for tool in matches
                                ],
                            }
                        }
                    )
                updated.append(dependency)
            interfaces = []
            if selected_ui_ids:
                if len(set(selected_ui_ids)) != len(selected_ui_ids):
                    raise WorkflowBundleError("Select unique saved interfaces")
                repository = ProcessInterfaceRepository(self.workspace.db_path)
                process = ProcessRef(
                    workspace_id=workspace_id,
                    source_path=path,
                    source_digest=document.storage_digest,
                )
                scope = ProcessScope(
                    "workflow-export", workspace_id, frozenset({"process.read"})
                )
                for ui_id in selected_ui_ids:
                    ui = repository.get_ui(workspace_id, ui_id)
                    if (
                        ui.process.source_path != path
                        or ui.archived
                        or ui.active_revision is None
                    ):
                        raise WorkflowBundleError(
                            "Select a saved interface bound to this exact workflow revision"
                        )
                    revision = repository.get_revision(
                        workspace_id, ui_id, ui.active_revision
                    )
                    if revision.manifest.process != process:
                        raise WorkflowBundleError(
                            "The saved interface is not bound to this exact workflow revision"
                        )
                    source = (
                        self.workspace.process_interfaces.ui_revisions.saved_source(
                            scope, process, revision
                        )
                    )
                    interfaces.append(
                        PortableInterface(
                            manifest=revision.manifest,
                            source=source,
                            source_digest=revision.source_digest,
                        )
                    )
                    updated.append(
                        BundleDependency(
                            category="ui",
                            identity=ui_id,
                            disposition="embedded",
                            sha256=revision.source_digest,
                            details={"activation": "local-rebuild-and-review-required"},
                        )
                    )
            # Shared profile/reference paths may refer to the same exact file.
            assets_by_path = {a.path: a for a in assets}
            bundle = WorkflowBundle(
                mode=mode,
                source=document.source,
                source_digest=document.storage_digest,
                layout=document.layout,
                assets=tuple(assets_by_path.values()),
                dependencies=tuple(updated),
                interfaces=tuple(interfaces),
            )
            return {
                "bundle": bundle.model_dump(mode="json"),
                "bundle_digest": canonical_digest(bundle),
            }

        return await self.workspace.executor.run(
            "workspace.workflow_bundle.export", build, timeout_seconds=30
        )

    def _inspect(self, workspace_dir, bundle, destination_path, *, catalog=()):
        bundle = WorkflowBundle.model_validate(bundle)
        paths = WorkspacePath(workspace_dir)
        diagnostics = []

        def diagnostic(code, message, dependency=None, severity="error"):
            diagnostics.append(
                BundleDiagnostic(
                    code=code, severity=severity, message=message, dependency=dependency
                )
            )

        try:
            required = _check_source(bundle.source)
            store = WorkspaceWorkflowSourceStore(workspace_dir)
            store._source_path(destination_path)
            if paths.resolve(destination_path).exists():
                raise ValueError(
                    "Destination source already exists; choose a new workflow filename"
                )
            if bundle.layout is not None:
                validate_source_layout(bundle.layout)
            declared = {(d.category, d.identity): d for d in required}
            manifest = {(d.category, d.identity): d for d in bundle.dependencies}
            if not set(declared) <= set(manifest):
                raise ValueError("The manifest omits a source dependency")
            if (
                set(manifest)
                - set(declared)
                - {key for key in manifest if key[0] == "ui"}
            ):
                raise ValueError("The manifest contains an undeclared dependency")
            for dependency in bundle.dependencies:
                _credential_configuration(dependency.details)
                allowed = {
                    "reference": set(),
                    "instructions": {
                        "version",
                        "migration_required",
                        "action_intent_contract",
                    },
                    "validation_profile": {"configuration", "profile"},
                    "provider": {
                        "server_id",
                        "tool_name",
                        "schema_digest",
                        "qualification",
                        "qualified_operations",
                    },
                    "model": {"requested_model", "output_format", "qualification"},
                    "ui": {"activation"},
                }[dependency.category]
                if set(dependency.details) - allowed:
                    raise ValueError(
                        "The manifest contains unsupported authority or dependency metadata"
                    )
            allowed_paths = {d.identity for d in required if d.category == "reference"}
            allowed_paths.update(
                ValidatorConfiguration.model_validate(
                    d.details["configuration"]
                ).profile.name
                for d in required
                if d.category == "validation_profile"
                and d.details["configuration"]["profile"]["source"] == "workspace"
            )
            for asset in bundle.assets:
                if asset.path not in allowed_paths:
                    raise ValueError(
                        "A transferred asset is not a declared input or validation profile"
                    )
                if paths.resolve(asset.path).exists():
                    raise ValueError(
                        "A transferred asset already exists; imports never overwrite workspace files"
                    )
            assets = {a.path: a for a in bundle.assets}
            for key, original in declared.items():
                dependency = manifest[key]
                if original.category == "reference":
                    if dependency.disposition == "embedded" and (
                        dependency.identity not in assets
                        or assets[dependency.identity].sha256 != dependency.sha256
                    ):
                        raise ValueError(
                            "An embedded reference file is missing or has a different digest"
                        )
                elif original.category == "instructions":
                    if dependency != original:
                        raise ValueError(
                            "Instruction manifest differs from the embedded source instructions"
                        )
                elif original.category == "validation_profile":
                    if (
                        dependency.details.get("configuration")
                        != original.details["configuration"]
                    ):
                        raise ValueError(
                            "Validation profile declaration differs from the source"
                        )
                    if dependency.disposition == "embedded":
                        config = ValidatorConfiguration.model_validate(
                            original.details["configuration"]
                        )
                        profile = ValidationProfile.model_validate(
                            dependency.details.get("profile")
                        )
                        if (
                            profile.reference() != config.profile.reference
                            or profile.baseline.reference() != config.baseline
                            or canonical_digest(profile) != dependency.sha256
                        ):
                            raise ValueError(
                                "Bundled validation profile differs from its pinned profile or baseline"
                            )
                        if config.profile.source == "workspace":
                            asset = assets.get(config.profile.name)
                            if (
                                asset is None
                                or ValidationProfile.model_validate_json(
                                    asset.decoded()
                                )
                                != profile
                            ):
                                raise ValueError(
                                    "Workspace validation profile bytes are missing or differ from the snapshot"
                                )
                        else:
                            try:
                                config.load(workspace_dir)
                            except (ValueError, FileNotFoundError):
                                diagnostic(
                                    "profile_installation_required",
                                    "The pinned packaged profile must be installed or explicitly migrated before running.",
                                    dependency.identity,
                                    "warning",
                                )
                elif original.category in {"model", "provider"}:
                    for name, value in original.details.items():
                        if dependency.details.get(name) != value:
                            raise ValueError(
                                "Capability requirements differ from the accepted source"
                            )
                    diagnostic(
                        "local_qualification_required",
                        "Qualify this binding using the local registry/adapter before running; names and UUIDs do not prove equivalence.",
                        dependency.identity,
                        "warning",
                    )
            ui_manifest = {
                d.identity: d for d in bundle.dependencies if d.category == "ui"
            }
            if {
                identity
                for identity, d in ui_manifest.items()
                if d.disposition == "embedded"
            } != {ui.manifest.ui_id for ui in bundle.interfaces}:
                raise ValueError(
                    "Saved interface dependency and source inventories disagree"
                )
            for ui in bundle.interfaces:
                if (
                    ui.manifest.process.source_digest != bundle.source_digest
                    or ui_manifest[ui.manifest.ui_id].sha256 != ui.source_digest
                ):
                    raise ValueError("Saved interface binds different source bytes")
                slug = Path(destination_path).name.removesuffix(".workflow.wflow")
                candidate = (
                    f"imported-assets/{slug}/interfaces/{ui.manifest.ui_id}.json"
                )
                portable_path(candidate)
                if paths.resolve(candidate).exists():
                    raise ValueError(
                        "An interface candidate already exists; select a fresh destination"
                    )
                diagnostic(
                    "ui_rebuild_required",
                    "Imported interface source is an inactive candidate. Rebind, rebuild and review locally; the common view remains available.",
                    ui.manifest.ui_id,
                    "warning",
                )
                if (ui.manifest.client_version, ui.manifest.kit_version) != (
                    "1.0.0",
                    "1.0.0",
                ):
                    diagnostic(
                        "ui_version_incompatible",
                        "This candidate requires unsupported client or kit versions. Migrate it before local rebuilding; use the common view meanwhile.",
                        ui.manifest.ui_id,
                        "warning",
                    )
            receipt = f"imported-assets/{Path(destination_path).name.removesuffix('.workflow.wflow')}/manifest.json"
            if paths.resolve(receipt).exists():
                raise ValueError(
                    "An import manifest already exists; select a fresh destination"
                )
            for dependency in bundle.dependencies:
                if dependency.disposition == "external":
                    diagnostic(
                        "external_dependency",
                        "This dependency remains external and must be prepared before starting.",
                        dependency.identity,
                        "warning",
                    )
        except (ValueError, OSError, WorkflowSourceStorageError) as exc:
            diagnostic("bundle_import_invalid", str(exc))
        return BundleInspection(
            bundle_digest=canonical_digest(bundle),
            can_import=not any(d.severity == "error" for d in diagnostics),
            diagnostics=tuple(diagnostics),
            external_dependencies=tuple(
                d for d in bundle.dependencies if d.disposition == "external"
            ),
            requirements=bundle.dependencies,
        )

    async def inspect(self, workspace_dir, bundle, destination_path, *, catalog=()):
        return await self.workspace.executor.run(
            "workspace.workflow_bundle.inspect",
            lambda: self._inspect(
                workspace_dir, bundle, destination_path, catalog=catalog
            ),
            timeout_seconds=30,
        )

    async def apply(
        self,
        workspace_dir,
        bundle,
        destination_path,
        expected_bundle_digest,
        *,
        catalog=(),
    ):
        def import_definition():
            accepted = WorkflowBundle.model_validate(bundle)
            report = self._inspect(
                workspace_dir, accepted, destination_path, catalog=catalog
            )
            if report.bundle_digest != expected_bundle_digest or not report.can_import:
                raise WorkflowBundleError(
                    "Bundle changed or dry-run diagnostics block this import"
                )
            store = WorkspaceWorkflowSourceStore(workspace_dir)
            paths = WorkspacePath(workspace_dir)
            imported = []
            # Existing pinned-directory write-once primitive owns reservation,
            # reparse-point checks and no-overwrite publication on every platform.
            slug = Path(destination_path).name.removesuffix(".workflow.wflow")
            receipt_path = f"imported-assets/{slug}/manifest.json"
            # Reserve this exact import before publishing any asset. The manifest
            # records intent, not completion; it survives partial writes and makes
            # the existing inspection reject replay after a client/owner restart.
            store._write_once(
                paths.resolve(receipt_path),
                canonical_json(
                    {
                        "bundle_digest": report.bundle_digest,
                        "requirements": accepted.dependencies,
                        "interface_candidates": [
                            ui.manifest.ui_id for ui in accepted.interfaces
                        ],
                        "destination_path": destination_path,
                        "authority": "definition-only-local-readiness-required",
                    }
                ).encode("utf-8"),
            )
            for asset in accepted.assets:
                store._write_once(paths.resolve(asset.path), asset.decoded())
                imported.append(asset.path)
            for ui in accepted.interfaces:
                candidate = (
                    f"imported-assets/{slug}/interfaces/{ui.manifest.ui_id}.json"
                )
                portable_path(candidate)
                store._write_once(
                    paths.resolve(candidate), canonical_json(ui).encode("utf-8")
                )
                imported.append(candidate)
            imported.append(receipt_path)
            # Deliberately bypass NEW-draft defaults: exact portable instruction
            # bodies remain accepted bytes even on a differently configured host.
            document = store.create(
                destination_path, accepted.source, layout=accepted.layout
            )
            return {
                "source": asdict(document),
                "imported_paths": imported,
                "inspection": report.model_dump(mode="json"),
            }

        return await self.workspace.executor.run_to_completion(
            "workspace.workflow_bundle.import", import_definition
        )
