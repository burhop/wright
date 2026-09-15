import re
from pathlib import Path


RUNTIME_ROOTS = (Path("apps"), Path("packages"))
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}
IGNORED_PARTS = {"tests", "node_modules", "dist", "dist-desktop", ".venv"}
QUALIFICATION_MODULE_ROOT = Path("packages/tool_registry/src/tool_registry")


def _is_allowed_provider_boundary(path: Path) -> bool:
    return path.parent == QUALIFICATION_MODULE_ROOT and path.name.startswith(
        ("windows_qualification_", "native_application_")
    )


def _is_test_module(path: Path) -> bool:
    return ".spec." in path.name or ".test." in path.name


def _contains_application_specific_provider_identifier(source: str) -> bool:
    # Canonical MCP server identities describe the selected integration; they
    # are not provider IDs or generic runtime coupling.
    without_server_identities = re.sub(
        r"server[._-]solid[._-]edge",
        "",
        source,
        flags=re.IGNORECASE,
    )
    normalized = "".join(
        character.lower()
        for character in without_server_identities
        if character.isalnum()
    )
    return "solid" + "edge" in normalized


def test_mcp_runtime_has_no_application_specific_provider_identifiers() -> None:
    violations: list[str] = []

    for root in RUNTIME_ROOTS:
        for path in root.rglob("*"):
            if (
                path.suffix.lower() not in SOURCE_SUFFIXES
                or IGNORED_PARTS.intersection(path.parts)
                or _is_allowed_provider_boundary(path)
                or _is_test_module(path)
            ):
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            if _contains_application_specific_provider_identifier(source):
                violations.append(path.as_posix())

    assert violations == []
