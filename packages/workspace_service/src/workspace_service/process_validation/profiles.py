"""Closed-schema, content-pinned packaged or workspace-owned profiles."""

from importlib.resources import files
import re

from core.process_validation import ValidationProfile, VersionReference

from ..workflow_sources import WorkspaceWorkflowSourceStore

_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,127}\Z")
_MAX_PROFILE_BYTES = 1024 * 1024


def load_profile(
    name: str,
    *,
    expected: VersionReference | None = None,
    workspace_root: str | None = None,
) -> ValidationProfile:
    if workspace_root is not None:
        raw = WorkspaceWorkflowSourceStore(workspace_root).read_artifact_bytes(
            name, max_bytes=_MAX_PROFILE_BYTES
        )
    else:
        if not _NAME.fullmatch(name):
            raise ValueError("Packaged profile name must be a stable resource name")
        resource = files("workspace_service.process_validation").joinpath(
            "profiles", name + ".json"
        )
        with resource.open("rb") as handle:
            raw = handle.read(_MAX_PROFILE_BYTES + 1)
    if len(raw) > _MAX_PROFILE_BYTES:
        raise ValueError("Profile exceeds 1 MiB")
    profile = ValidationProfile.model_validate_json(raw)
    if expected is not None and profile.reference() != expected:
        raise ValueError("Profile digest/version differs from its pinned reference")
    return profile
