"""Side-effect-free public Python helpers for Wright Workspace Surfaces."""

from .display import display
from .graphs import bar, histogram, line, scatter
from .models import (
    DisplayConfigurationError,
    DisplayContractError,
    DisplayHandle,
    DisplayTransportError,
    WrightDisplayError,
)

CONTRACT_VERSION = 1

__all__ = (
    "CONTRACT_VERSION",
    "DisplayConfigurationError",
    "DisplayContractError",
    "DisplayHandle",
    "DisplayTransportError",
    "WrightDisplayError",
    "bar",
    "display",
    "histogram",
    "line",
    "scatter",
)
