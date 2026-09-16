"""Minimal import surface for MCP wrapper discovery tests."""


class BlenderConnection:
    """Placeholder; discovery tests never instantiate the native connection."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Native Blender connections are unavailable in fixture tests")
