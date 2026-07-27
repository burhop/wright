from pathlib import Path


RUNTIME_ROOTS = (Path("apps"), Path("packages"))
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}
IGNORED_PARTS = {"tests", "node_modules", "dist", "dist-desktop", ".venv"}


def test_mcp_runtime_has_no_application_specific_provider_identifiers() -> None:
    forbidden = "solid" + "edge"
    violations: list[str] = []

    for root in RUNTIME_ROOTS:
        for path in root.rglob("*"):
            if path.suffix.lower() not in SOURCE_SUFFIXES or IGNORED_PARTS.intersection(
                path.parts
            ):
                continue
            normalized = "".join(
                character.lower()
                for character in path.read_text(encoding="utf-8", errors="ignore")
                if character.isalnum()
            )
            if forbidden in normalized:
                violations.append(path.as_posix())

    assert violations == []
