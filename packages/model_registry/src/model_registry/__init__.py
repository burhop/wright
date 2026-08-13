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
from .catalog import (
    ModelCatalog as ModelCatalog,
    ModelCatalogEntry as ModelCatalogEntry,
    ModelCatalogError as ModelCatalogError,
    ModelCatalogFilters as ModelCatalogFilters,
    ModelCatalogPage as ModelCatalogPage,
    ModelCatalogSnapshot as ModelCatalogSnapshot,
)
from .planning import (
    ModelEffectPlan as ModelEffectPlan,
    ModelPlanError as ModelPlanError,
    confirm_effect_plan as confirm_effect_plan,
    create_effect_plan as create_effect_plan,
)


def schema_root():
    """Return the packaged engineering-model JSON Schema resource root."""

    return files("model_registry.schemas")


__all__ = [
    "FailureCategory",
    "HostObservation",
    "ModelPackage",
    "ModelEffectPlan",
    "ModelPlanError",
    "ModelPolicy",
    "ModelRegistryError",
    "ModelTestVector",
    "ModelVariant",
    "PolicyResult",
    "PolicyState",
    "canonical_digest",
    "canonical_json",
    "confirm_effect_plan",
    "create_effect_plan",
    "schema_root",
]
