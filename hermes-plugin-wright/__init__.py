"""Wright Engineering Catalog plugin registration.

Hermes can load plugins in two ways:
1. As an installed Python distribution via the hermes_agent.plugins entry point.
2. As a copied flat directory from plugins/wright/__init__.py.

The source tree is intentionally flat for Hermes' directory plugin loader, while
the wheel maps those files into the hermes_plugin_wright package. When Hermes
loads the flat directory directly, bootstrap this module as that package name so
imports resolve the same way in both modes.
"""
from __future__ import annotations

import os
import sys

if __name__ != "hermes_plugin_wright":
    module = sys.modules[__name__]
    module.__path__ = [os.path.dirname(__file__)]
    module.__package__ = "hermes_plugin_wright"
    sys.modules.setdefault("hermes_plugin_wright", module)

import structlog

try:
    from hermes_plugin_wright.catalog import CatalogLoader
    from hermes_plugin_wright.commands import register_commands
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - exercised by Hermes at import time
    CatalogLoader = None
    register_commands = None
    _IMPORT_ERROR = exc

logger = structlog.get_logger("hermes_plugin_wright")


def register(ctx):
    """Main plugin entry point called by Hermes PluginManager."""
    logger.info("Wright plugin loaded")
    if _IMPORT_ERROR is not None:
        logger.error(
            "Failed to import Wright plugin modules",
            error=str(_IMPORT_ERROR),
        )
        raise RuntimeError("Wright plugin import failed") from _IMPORT_ERROR

    try:
        catalog = CatalogLoader()
        register_commands(ctx, catalog)
        logger.info("Wright commands registered successfully")
    except Exception as exc:
        logger.exception("Failed to register Wright commands", error=str(exc))
        raise
