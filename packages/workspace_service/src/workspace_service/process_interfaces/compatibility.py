"""Saved presentation compatibility against accepted declarations, not engineering verdicts."""

from core.process_interfaces import Compatibility
from core.process_interactions import Reason

from .authoring import accepted_binding_catalog
from .build import validate_manifest_bindings
from .errors import ProcessInterfaceError


async def check_interface_compatibility(application, scope, process, revision):
    manifest = revision.manifest
    try:
        resolved = await application.resolve_process(scope, process)
        optional = validate_manifest_bindings(
            manifest,
            process,
            accepted_binding_catalog(resolved.document),
            allow_process_revision=True,
        )
        missing = set(manifest.capabilities) - scope.capabilities
        if missing:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view lacks a capability requested by the saved interface.",
                "Open an authorized view or update the interface to use the available process operations.",
            )
        return Compatibility(
            ui_id=manifest.ui_id,
            revision_id=manifest.revision_id,
            current_process=process,
            state="compatible",
            optional_absences=optional,
        )
    except ProcessInterfaceError as error:
        return Compatibility(
            ui_id=manifest.ui_id,
            revision_id=manifest.revision_id,
            current_process=process,
            state="incompatible",
            reasons=(error.reason,),
        )
    except (ValueError, KeyError):
        return Compatibility(
            ui_id=manifest.ui_id,
            revision_id=manifest.revision_id,
            current_process=process,
            state="unsupported",
            reasons=(
                Reason(
                    code="UI_INCOMPATIBLE",
                    message="The current process declaration cannot be checked against this saved interface.",
                    correction="Use the common working view and update the interface after resolving its supported declarations.",
                ),
            ),
        )
