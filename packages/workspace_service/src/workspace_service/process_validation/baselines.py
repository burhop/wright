"""Closed-schema, source-pinned packaged requirement baselines."""

from importlib.resources import files
import re

from core.process_validation import Baseline, VersionReference


_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,127}\Z")
_MAX_BASELINE_BYTES = 1024 * 1024


def load_baseline(name: str, *, expected: VersionReference | None = None) -> Baseline:
    if not _NAME.fullmatch(name):
        raise ValueError("Packaged baseline name must be a stable resource name")
    resource = files("workspace_service.process_validation").joinpath(
        "baselines", name + ".json"
    )
    with resource.open("rb") as handle:
        raw = handle.read(_MAX_BASELINE_BYTES + 1)
    if len(raw) > _MAX_BASELINE_BYTES:
        raise ValueError("Baseline exceeds 1 MiB")
    baseline = Baseline.model_validate_json(raw)
    if expected is not None and baseline.reference() != expected:
        raise ValueError("Baseline digest/version differs from its pinned reference")
    return baseline
