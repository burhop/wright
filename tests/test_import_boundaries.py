from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "architecture" / "python-packages.toml"
INTERNAL_DISTRIBUTIONS = {
    "wright-core": "core",
    "wright-data-vault": "data_vault",
    "wright-tool-registry": "tool_registry",
    "wright-agent-adapters": "agent_adapters",
    "wright-workspace-service": "workspace_service",
}


@dataclass(frozen=True)
class ImportUse:
    target: str
    line: int
    form: str


def _load_policy() -> dict[str, Any]:
    return tomllib.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _literal_dynamic_target(node: ast.Call) -> tuple[str | None, bool]:
    function = node.func
    is_import_module = (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
        and function.value.id == "importlib"
        and function.attr == "import_module"
    ) or (isinstance(function, ast.Name) and function.id == "import_module")
    is_dunder_import = isinstance(function, ast.Name) and function.id == "__import__"
    if not (is_import_module or is_dunder_import):
        return None, False
    if node.args and isinstance(node.args[0], ast.Constant):
        value = node.args[0].value
        return (value if isinstance(value, str) else None), True
    return None, True


def _imports(source: str, *, filename: str = "<memory>") -> list[ImportUse]:
    tree = ast.parse(source, filename=filename)
    uses: list[ImportUse] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            uses.extend(
                ImportUse(alias.name, node.lineno, "import") for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            uses.append(ImportUse(module, node.lineno, "from"))
        elif isinstance(node, ast.Call):
            target, recognized = _literal_dynamic_target(node)
            if recognized:
                uses.append(
                    ImportUse(target or "<non-literal-dynamic>", node.lineno, "dynamic")
                )
    return uses


def _top_level(target: str) -> str:
    return target.lstrip(".").split(".", 1)[0]


def _source_violations(
    owner: str,
    path: Path,
    source: str,
    policy: dict[str, Any],
) -> list[tuple[str, int, str]]:
    surfaces = policy["surfaces"]
    import_owners = {
        import_name: surface_name
        for surface_name, rule in surfaces.items()
        for import_name in rule["imports_as"]
    }
    rule = surfaces[owner]
    allowed = set(rule["allowed_dependencies"])
    forbidden = set(rule.get("forbidden_modules", []))
    violations: list[tuple[str, int, str]] = []
    for use in _imports(source, filename=str(path)):
        target = _top_level(use.target)
        if target == "<non-literal-dynamic>":
            violations.append((target, use.line, use.form))
            continue
        dependency = import_owners.get(target)
        if dependency is not None and dependency != owner and dependency not in allowed:
            violations.append((dependency, use.line, use.form))
        elif target in forbidden:
            violations.append((target, use.line, use.form))
    return violations


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _declared_internal_dependencies(metadata_path: Path) -> set[str]:
    data = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    result: set[str] = set()
    for raw in dependencies:
        name = re.split(r"[<>=!~;\s\[]", raw, maxsplit=1)[0].lower()
        if owner := INTERNAL_DISTRIBUTIONS.get(name):
            result.add(owner)
    return result


def test_package_policy_is_well_formed_and_acyclic():
    policy = _load_policy()
    surfaces = policy["surfaces"]
    known = set(surfaces)
    import_names: list[str] = []
    for owner, rule in surfaces.items():
        assert set(rule["allowed_dependencies"]) <= known - {owner}
        import_names.extend(rule["imports_as"])
        for root in rule["roots"]:
            assert (ROOT / root).is_dir(), f"missing source root for {owner}: {root}"
    assert len(import_names) == len(set(import_names))

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(owner: str) -> None:
        if owner in visiting:
            raise AssertionError(f"package dependency cycle contains {owner}")
        if owner in visited:
            return
        visiting.add(owner)
        for dependency in surfaces[owner]["allowed_dependencies"]:
            visit(dependency)
        visiting.remove(owner)
        visited.add(owner)

    for owner in surfaces:
        visit(owner)

    assert policy.get("temporary_exceptions", []) == []


def test_workspace_router_contains_transport_translation_only():
    path = ROOT / "apps/api/src/api/routers/workspace.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    forbidden_imports = {"sqlite3", "subprocess"}
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _top_level(alias.name) in forbidden_imports:
                    violations.append(f"{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _top_level(module) in forbidden_imports or module.startswith(
                "workspace_service.adapters.runtime"
            ):
                violations.append(f"{node.lineno}: from {module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                violations.append(f"{node.lineno}: open")
    assert violations == []


def test_removed_core_workspace_and_global_activation_do_not_return():
    assert not (ROOT / "packages/core/src/core/workspace.py").exists()
    assert not (ROOT / "packages/core/src/core/agent_sync.py").exists()
    legacy = (
        ROOT / "packages/workspace_service/src/workspace_service/adapters/runtime.py"
    )
    names = {
        node.name
        for node in ast.parse(legacy.read_text(encoding="utf-8")).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "activate_workspace" not in names


def test_production_source_obeys_package_policy():
    policy = _load_policy()
    exceptions = {
        (item["owner"], item["dependency"], item["path"])
        for item in policy.get("temporary_exceptions", [])
    }
    assert all("*" not in component for entry in exceptions for component in entry)
    seen_exceptions: set[tuple[str, str, str]] = set()
    violations: list[str] = []

    for owner, rule in policy["surfaces"].items():
        for root in rule["roots"]:
            for path in sorted((ROOT / root).rglob("*.py")):
                for dependency, line, form in _source_violations(
                    owner, path, path.read_text(encoding="utf-8"), policy
                ):
                    key = (owner, dependency, _relative(path))
                    if key in exceptions:
                        seen_exceptions.add(key)
                    else:
                        violations.append(
                            f"{_relative(path)}:{line}: {owner} -> {dependency} ({form})"
                        )

    stale = exceptions - seen_exceptions
    assert not stale, f"stale architecture exceptions: {sorted(stale)}"
    assert not violations, "forbidden package dependencies:\n" + "\n".join(violations)


def test_policy_matches_internal_package_metadata():
    policy = _load_policy()
    mismatches: list[str] = []
    for owner, rule in policy["surfaces"].items():
        metadata = ROOT / rule["metadata"]
        declared = _declared_internal_dependencies(metadata)
        allowed = set(rule["allowed_dependencies"])
        if declared != allowed:
            mismatches.append(
                f"{owner}: metadata={sorted(declared)} policy={sorted(allowed)}"
            )
    assert not mismatches, "internal dependency drift:\n" + "\n".join(mismatches)


@pytest.mark.parametrize(
    ("fixture_name", "form"),
    [
        ("forbidden_direct.py.txt", "import"),
        ("forbidden_from.py.txt", "from"),
        ("forbidden_local.py.txt", "import"),
        ("forbidden_dynamic.py.txt", "dynamic"),
        ("forbidden_nonliteral_dynamic.py.txt", "dynamic"),
    ],
)
def test_seeded_forbidden_import_forms_are_rejected(fixture_name: str, form: str):
    source = (ROOT / "tests" / "architecture_fixtures" / fixture_name).read_text()
    violations = _source_violations("core", Path("seed.py"), source, _load_policy())
    assert violations
    assert violations[0][2] == form


def test_seeded_approved_import_is_accepted():
    source = (ROOT / "tests" / "architecture_fixtures" / "approved.py.txt").read_text()
    assert (
        _source_violations(
            "workspace_service",
            Path("seed.py"),
            source,
            _load_policy(),
        )
        == []
    )
