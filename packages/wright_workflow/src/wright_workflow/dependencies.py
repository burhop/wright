"""Derive the dependency inventory from the source and verify transferred assets."""

import json
import re

from .bundle import BundleDependency, portable_path
from .contracts import canonical_digest
from .instructions import WorkflowInstructionSet
from .layout_wire import validate_source_layout
from .source import WorkflowSourceExecutionError
from .validation_wire import ValidationProfile, ValidatorConfiguration

SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?server[_-]?key|api[_-]?key|secret|token|password|authorization|cookie|credential|private[_-]?key|x[_-](?:upload|download)[_-]ticket)"
)


def dependency_inventory(sections) -> tuple[BundleDependency, ...]:
    """Discover dependencies from the source, never trust a supplied manifest."""
    if sum(section["kind"] == "workflow" for section in sections) != 1:
        raise ValueError("A bundle requires exactly one workflow declaration")
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
            raise ValueError("Workflow settings must be an object")
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
            from .option_wire import OptionSource

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
            portable = {}
            if "mcp_binding" in settings:
                from .bindings import PortableBinding

                portable["portable_binding"] = PortableBinding.model_validate(
                    settings["mcp_binding"]
                ).model_dump(mode="json")
            tool = settings.get("mcp_tool", "")
            add(
                "provider",
                str(section["id"]),
                server_id=str(server),
                tool_name=str(tool),
                schema_digest=settings.get("mcp_schema_digest", ""),
                qualification="requires-local-registry-review",
                **portable,
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
                raise ValueError(
                    "Credential configuration cannot be transferred in a workflow bundle"
                )
            _credential_configuration(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _credential_configuration(child)


def check_dependencies(sections, required, bundle):
    def invalid(message):
        raise WorkflowSourceExecutionError(
            "WORKFLOW_BUNDLE_INVALID",
            message,
            "Re-export the accepted workflow and its dependencies.",
        )

    for section in sections:
        _credential_configuration(section["fields"])
    if bundle.layout is not None:
        validate_source_layout(bundle.layout)
    manifest = {
        (entry.category, entry.identity): entry for entry in bundle.dependencies
    }
    assets = {asset.path: asset for asset in bundle.assets}
    used_assets = set()
    for expected in required:
        entry = manifest.pop((expected.category, expected.identity), None)
        if entry is None:
            invalid(f"Missing {expected.category} dependency for {expected.identity}.")
        _credential_configuration(entry.details)
        if entry == expected:
            continue
        if expected.category == "provider":
            details = dict(entry.details)
            operations = details.pop("qualified_operations", [])
            if (
                entry.disposition != "external"
                or entry.sha256 is not None
                or details != expected.details
                or not isinstance(operations, list)
                or any(
                    not isinstance(op, dict)
                    or set(op) != {"tool_name", "schema_digest"}
                    or any(
                        value is not None and not isinstance(value, str)
                        for value in op.values()
                    )
                    for op in operations
                )
            ):
                invalid(f"Provider declaration differs from {expected.identity}.")
            continue
        if entry.disposition != "embedded" or bundle.mode != "bundle":
            invalid(f"Dependency differs from {expected.identity}.")
        if expected.category == "reference":
            asset = assets.get(entry.identity)
            if entry.details or asset is None or asset.sha256 != entry.sha256:
                invalid(f"Embedded reference differs from {expected.identity}.")
            if asset.path.lower().endswith(".json"):
                _credential_configuration(json.loads(asset.decoded()))
            used_assets.add(asset.path)
        elif expected.category == "validation_profile":
            config = ValidatorConfiguration.model_validate(
                expected.details["configuration"]
            )
            if (
                set(entry.details) != {"configuration", "profile"}
                or expected.details["configuration"] != entry.details["configuration"]
            ):
                invalid("Validation profile declaration differs from the source.")
            profile = ValidationProfile.model_validate(entry.details["profile"])
            if (
                profile.reference() != config.profile.reference
                or profile.baseline.reference() != config.baseline
                or canonical_digest(profile) != entry.sha256
            ):
                invalid(
                    "Validation profile or baseline differs from the declared revision."
                )
            if config.profile.source == "workspace":
                asset = assets.get(config.profile.name)
                if (
                    asset is None
                    or ValidationProfile.model_validate_json(asset.decoded()) != profile
                ):
                    invalid("Validation profile bytes differ from the snapshot.")
                used_assets.add(asset.path)
        else:
            invalid(f"Dependency differs from {expected.identity}.")
    if assets.keys() != used_assets:
        invalid("Bundle contains an undeclared file asset.")
    for ui in bundle.interfaces:
        entry = manifest.pop(("ui", ui.manifest.ui_id), None)
        if (
            entry is None
            or entry.sha256 != ui.source_digest
            or entry.disposition != "embedded"
            or entry.details != {"activation": "local-rebuild-and-review-required"}
            or ui.manifest.process.source_digest != bundle.source_digest
        ):
            invalid(
                "Saved interface binds different source bytes or activation metadata."
            )
    if manifest:
        invalid("Bundle contains an undeclared dependency.")
