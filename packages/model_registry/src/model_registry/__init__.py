"""Safe local engineering model contracts for Wright."""

from importlib.resources import files


def schema_root():
    """Return the packaged engineering-model JSON Schema resource root."""

    return files("model_registry.schemas")


__all__ = ["schema_root"]
