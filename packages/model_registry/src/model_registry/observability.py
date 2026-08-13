"""Public model-library observability contract shared across package boundaries."""

from core.model_observability import (
    MODEL_BOUNDARY_EVENTS as MODEL_BOUNDARY_EVENTS,
)
from core.model_observability import ModelBoundaryObserver as ModelBoundaryObserver

__all__ = ["MODEL_BOUNDARY_EVENTS", "ModelBoundaryObserver"]
