"""Wright Engineering Catalog — Hermes Plugin Registration."""
import structlog
from hermes_plugin_wright.catalog import CatalogLoader
from hermes_plugin_wright.commands import register_commands

logger = structlog.get_logger("hermes_plugin_wright")


def register(ctx):
    """Main plugin entry point called by Hermes PluginManager."""
    logger.info("Wright plugin loaded")
    try:
        catalog = CatalogLoader()
        register_commands(ctx, catalog)
        logger.info("Wright commands registered successfully")
    except Exception as e:
        logger.error("Failed to register Wright commands", error=str(e))

