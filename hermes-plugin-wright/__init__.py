"""Wright Engineering Catalog — Hermes Plugin Registration."""
import structlog

logger = structlog.get_logger("hermes_plugin_wright")


def register(ctx):
    """Main plugin entry point called by Hermes PluginManager."""
    logger.info("Wright plugin loaded")
