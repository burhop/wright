"""Safe local engineering model contracts for Wright."""

from importlib.resources import files

from .models import (
    FailureCategory as FailureCategory,
    ModelPackage as ModelPackage,
    ModelRegistryError as ModelRegistryError,
    ModelTestVector as ModelTestVector,
    ModelVariant as ModelVariant,
    canonical_digest as canonical_digest,
    canonical_json as canonical_json,
)
from .policy import (
    HostObservation as HostObservation,
    ModelPolicy as ModelPolicy,
    PolicyResult as PolicyResult,
    PolicyState as PolicyState,
)
from .observability import (
    MODEL_BOUNDARY_EVENTS as MODEL_BOUNDARY_EVENTS,
    ModelBoundaryObserver as ModelBoundaryObserver,
)


def schema_root():
    """Return the packaged engineering-model JSON Schema resource root."""

    return files("model_registry.schemas")


__all__ = [
    "FailureCategory",
    "HostObservation",
    "ModelPackage",
    "ModelPolicy",
    "ModelRegistryError",
    "ModelTestVector",
    "ModelVariant",
    "PolicyResult",
    "PolicyState",
    "canonical_digest",
    "canonical_json",
    "schema_root",
]
