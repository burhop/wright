"""Check the installed public runtime and run the sdist's conformance tests."""

import ast
from importlib import import_module, metadata
from ipaddress import ip_address
import json
from pathlib import Path
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import pytest


DIRECT_DEPENDENCIES = {"jsonschema", "mcp", "pydantic"}
# jsonschema supplies the referencing registry used for local schema validation.
PUBLIC_IMPORTS = sys.stdlib_module_names | DIRECT_DEPENDENCIES | {"referencing", "wright_workflow"}
COMMERCIAL_MODULES = {
    "wright", "wright_pro", "wright_pro_release", "wright_engineering", "hermes_plugin_wright",
    "api", "core", "agent_adapters", "data_vault", "model_registry", "tool_registry", "workspace_service",
}


def check_packages(report, distribution):
    resolved = {canonicalize_name(entry["metadata"]["name"]) for entry in report["install"]}
    direct = {canonicalize_name(Requirement(req).name) for req in distribution.requires or []}
    if "wright-workflow" not in resolved:
        raise ValueError("The install report did not record a new standalone engine installation")
    if direct != DIRECT_DEPENDENCIES:
        raise ValueError(f"Unexpected public engine dependency declaration: {sorted(direct)}")
    private = {
        name for name in resolved if (name.startswith("wright-") and name != "wright-workflow")
        or name in {"hermes-plugin-wright", "hermes-agent", "openai-codex"}
    }
    if private:
        raise ValueError(f"Commercial distribution in the public installation: {sorted(private)}")


def check_source(path):
    tree = ast.parse(path.read_bytes(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            names = [node.module]
        else:
            continue
        for name in names:
            if name.split(".", 1)[0] not in PUBLIC_IMPORTS:
                raise ValueError(f"{path.name}:{node.lineno} imports an unreviewed module: {name}")


class CheckCommercialImports:
    def __init__(self):
        self.attempted = set()

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in COMMERCIAL_MODULES:
            self.attempted.add(fullname)
            raise ModuleNotFoundError(f"Commercial import from the standalone installation: {fullname}", name=fullname)
        return None


class CheckLocalConnections:
    def __init__(self):
        self.attempted = set()

    def __call__(self, event, args):
        if event == "socket.getaddrinfo":
            host = args[0]
        elif event == "socket.connect" and isinstance(args[1], tuple):
            host = args[1][0]
        else:
            return
        if isinstance(host, bytes):
            host = host.decode("ascii")
        if host is None or host.lower().rstrip(".") == "localhost":
            return
        try:
            if ip_address(host).is_loopback:
                return
        except ValueError:
            pass
        self.attempted.add(host)
        raise RuntimeError(f"External network access during standalone conformance: {host}")


def main(report, tests):
    distribution = metadata.distribution("wright-workflow")
    check_packages(json.loads(report.read_bytes()), distribution)
    guard = CheckCommercialImports()
    already_loaded = COMMERCIAL_MODULES.intersection(sys.modules)
    if already_loaded:
        raise ValueError(f"Commercial modules already loaded: {sorted(already_loaded)}")
    connections = CheckLocalConnections()
    sys.addaudithook(connections)
    sys.meta_path.insert(0, guard)
    try:
        for member in distribution.files or []:
            if member.parts[0] != "wright_workflow" or member.suffix != ".py":
                continue
            path = Path(distribution.locate_file(member)).resolve(strict=True)
            check_source(path)
            name = ".".join(member.with_suffix("").parts).removesuffix(".__init__")
            loaded = import_module(name)
            if Path(loaded.__file__).resolve() != path:
                raise ValueError(f"{name} was imported from outside the installed wheel")
        result = pytest.main(["-q", str(tests)])
    finally:
        sys.meta_path.remove(guard)
    if guard.attempted:
        raise ValueError(f"Commercial imports attempted during conformance: {sorted(guard.attempted)}")
    if connections.attempted:
        raise ValueError(f"External connections attempted during conformance: {sorted(connections.attempted)}")
    return result


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
