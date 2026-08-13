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
from .runtime import (
    AdapterDescriptor as AdapterDescriptor,
    AdapterRegistration as AdapterRegistration,
    RuntimeAdapterRegistry as RuntimeAdapterRegistry,
    RuntimeFailure as RuntimeFailure,
    RuntimeSupervisor as RuntimeSupervisor,
    built_in_runtime_registry as built_in_runtime_registry,
)
from .testing import (
    EvidenceFailure as EvidenceFailure,
    ModelValidationEvidence as ModelValidationEvidence,
    evaluate_test_vector as evaluate_test_vector,
    validate_mandatory_vectors as validate_mandatory_vectors,
)
from .extensions import (
    EngineeringExtensionRegistries as EngineeringExtensionRegistries,
    ExtensionError as ExtensionError,
    built_in_extension_registries as built_in_extension_registries,
)
from .conformance import (
    ConformanceFinding as ConformanceFinding,
    ConformanceReport as ConformanceReport,
    run_package_conformance as run_package_conformance,
)


def schema_root():
    """Return the packaged engineering-model JSON Schema resource root."""

    return files("model_registry.schemas")


__all__ = [
    "FailureCategory",
    "ConformanceFinding",
    "ConformanceReport",
    "EngineeringExtensionRegistries",
    "ExtensionError",
    "AdapterDescriptor",
    "AdapterRegistration",
    "EvidenceFailure",
    "HostObservation",
    "ModelPackage",
    "ModelEffectPlan",
    "ModelPlanError",
    "ModelPolicy",
    "ModelRegistryError",
    "ModelTestVector",
    "ModelVariant",
    "ModelValidationEvidence",
    "PolicyResult",
    "PolicyState",
    "RuntimeAdapterRegistry",
    "RuntimeFailure",
    "RuntimeSupervisor",
    "built_in_runtime_registry",
    "built_in_extension_registries",
    "canonical_digest",
    "canonical_json",
    "confirm_effect_plan",
    "create_effect_plan",
    "evaluate_test_vector",
    "run_package_conformance",
    "schema_root",
    "validate_mandatory_vectors",
]
