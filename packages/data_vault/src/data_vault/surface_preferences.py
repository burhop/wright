"""Presentation preference persistence public boundary.

The implementation remains shared with the foundational surface repository so
existing imports keep working while consumers gain a focused module boundary.
"""

from .surface_repository import (
    PresentationPreferenceRecord,
    SurfacePreferenceRepository,
    SurfaceRevisionConflict,
)

__all__ = [
    "PresentationPreferenceRecord",
    "SurfacePreferenceRepository",
    "SurfaceRevisionConflict",
]
