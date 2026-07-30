from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
VERIFY_PATH = ROOT / "docker" / "mcp" / "verify-bundle.py"
GENERATE_PATH = ROOT / "docker" / "mcp" / "generate-config.py"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_path(name: str) -> Path:
    return ROOT / "tests" / "fixtures" / "mcp_bundle" / name


def test_bundle_manifest_schema_declares_required_fields() -> None:
    schema = json.loads(read_text("docker/mcp-bundle.schema.json"))

    assert schema["type"] == "object"
    for field in ("schema_version", "bundle_id", "applications", "mcp_servers"):
        assert field in schema["required"]
    app_required = schema["properties"]["applications"]["items"]["required"]
    server_required = schema["properties"]["mcp_servers"]["items"]["required"]
    for field in ("id", "display_name", "availability", "source", "compliance_profile"):
        assert field in app_required
    for field in ("id", "display_name", "availability", "mcp_source", "launch"):
        assert field in server_required


def test_default_bundle_has_corrected_initial_applications_and_mcp_servers() -> None:
    bundle = yaml.safe_load(read_text("docker/mcp-bundle.yaml"))
    application_ids = {entry["id"] for entry in bundle["applications"]}
    server_ids = {entry["id"] for entry in bundle["mcp_servers"]}
    serialized = yaml.safe_dump(bundle).lower()

    assert application_ids == {"openscad", "freecad", "brep", "playwright"}
    assert server_ids == {
        "openscad-mcp",
        "freecad-mcp",
        "brep-mcp",
        "solid-edge-mcp",
        "playwright-mcp",
    }
    assert "opencad" not in serialized
    assert "opencascade" not in serialized
    assert "caid" not in serialized


def test_validator_accepts_default_bundle() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_default")
    result = verifier.validate_bundle_file(ROOT / "docker" / "mcp-bundle.yaml")

    assert result["ok"] is True
    assert {item["status"] for item in result["applications"]} == {"accepted"}
    assert {item["status"] for item in result["mcp_servers"]} == {"accepted"}


def test_validator_accepts_allowed_pinned_permissive_fixture() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle")
    result = verifier.validate_bundle_file(fixture_path("allowed.yaml"))

    assert result["ok"] is True
    assert result["mcp_servers"][0]["status"] == "accepted"


def test_validator_rejects_unpinned_git_refs() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_unpinned")

    with pytest.raises(verifier.BundleValidationError, match="floating git ref"):
        verifier.validate_bundle_file(fixture_path("unpinned.yaml"))


def test_validator_requires_gpl_runtime_source_compliance() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_gpl_missing")

    with pytest.raises(verifier.BundleValidationError, match="source_access"):
        verifier.validate_bundle_file(fixture_path("gpl-missing-compliance.yaml"))


def test_validator_accepts_complete_gpl_runtime_profile() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_gpl")
    result = verifier.validate_bundle_file(fixture_path("gpl-runtime-compliant.yaml"))

    assert result["ok"] is True
    evidence = result["applications"][0]["compliance"]
    assert evidence["profile_id"] == "gpl-2.0-runtime-redistribution"
    assert evidence["modification_status"] == "unmodified"


def test_validator_accepts_remote_only_without_local_launch() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_remote")
    result = verifier.validate_bundle_file(fixture_path("remote-only.yaml"))

    assert result["ok"] is True
    assert result["mcp_servers"][0]["status"] == "remote_only"


def test_generate_config_outputs_hermes_config_and_compliance_artifacts(tmp_path) -> None:
    generator = load_module(GENERATE_PATH, "generate_config")
    generator.generate(
        bundle_path=fixture_path("gpl-runtime-compliant.yaml"),
        output_dir=tmp_path,
    )

    hermes_config = yaml.safe_load((tmp_path / "hermes-mcp.generated.yaml").read_text())
    status = json.loads((tmp_path / "mcp-bundle-status.json").read_text())
    notice = (tmp_path / "licenses" / "THIRD-PARTY-COMPLIANCE.json").read_text()
    no_warranty = (tmp_path / "licenses" / "NO-WARRANTY-GPL-2.0.txt").read_text()

    assert "mcp_servers" in hermes_config
    assert "gpl-runtime-mcp" in hermes_config["mcp_servers"]
    assert status["bundle_id"] == "fixture-gpl-runtime-compliant"
    assert "applications" in status
    assert "mcp_servers" in status
    assert "gpl-2.0-runtime-redistribution" in notice
    assert "NO WARRANTY" in no_warranty


def test_dockerfile_mcp_derives_from_existing_appliance_contract_and_adds_node_runtime() -> None:
    dockerfile = read_text("docker/Dockerfile.mcp")

    assert "ARG WRIGHT_BASE_IMAGE=wright:test" in dockerfile
    assert "FROM ${WRIGHT_BASE_IMAGE}" in dockerfile
    assert "FROM node:24.17.0-slim" in dockerfile
    assert "COPY --from=node-runtime" in dockerfile
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_URL" in dockerfile
    assert "https://github.com/burhop/SolidEdgeMCP.git" in dockerfile
    assert "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330" in dockerfile
    assert "verify-bundle.py" in dockerfile
    assert "generate-config.py" in dockerfile
    assert "COPY docker/entrypoint.sh /entrypoint.sh" in dockerfile
    assert "chmod 755 /entrypoint.sh" in dockerfile
    assert "chmod a+r /etc/supervisor/conf.d/wright.conf" in dockerfile
    assert "su agent -c 'test -r /etc/supervisor/conf.d/wright.conf'" in dockerfile
    assert "test -f /container-manifest.md" in dockerfile
    assert "rm -rf /home/agent/.cache/uv" in dockerfile
    assert "chown -R agent:agent /home/agent" in dockerfile
    assert "ENTRYPOINT" not in dockerfile


def test_mcp_install_is_manifest_driven_and_uses_build_time_caches() -> None:
    script = read_text("docker/mcp/install-bundle.sh")

    for expected in (
        "applications",
        "mcp_servers",
        "UV_CACHE_DIR",
        "/tmp/wright-mcp-uv-cache",
        "npm install --global",
        "playwright install --with-deps",
        "default_url",
        "SolidEdgeMcpServer",
        "not runnable inside this Linux appliance",
        "freecad-mcp-wrapped",
        "solid-edge-mcp",
        "WRIGHT_SOLIDEDGE_MCP_GIT_URL",
    ):
        assert expected in script
    assert "brep-caid-opencascade" not in script
    assert "OpenCASCADE" not in script


def test_base_dockerfile_normalizes_supervisor_config_permissions() -> None:
    dockerfile = read_text("docker/Dockerfile")

    assert "COPY docker/supervisord.conf /etc/supervisor/conf.d/wright.conf" in dockerfile
    assert "chmod 444 /etc/supervisor/conf.d/wright.conf" in dockerfile


def test_compose_mcp_uses_separate_volume_names_and_same_port_contract() -> None:
    compose = read_text("docker-compose.mcp.yml")

    assert "127.0.0.1:8080:8000" in compose
    assert "platform: ${WRIGHT_MCP_DOCKER_PLATFORM:-linux/amd64}" in compose
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_URL: ${WRIGHT_SOLIDEDGE_MCP_GIT_URL:-https://github.com/burhop/SolidEdgeMCP.git}" in compose
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_REF: ${WRIGHT_SOLIDEDGE_MCP_GIT_REF:-2aad5bd24df6ce1ac9578ad35c4da7ac241b5330}" in compose
    for volume in (
        "wright_mcp_data",
        "wright_mcp_workspaces",
        "wright_mcp_config",
        "wright_mcp_hermes",
        "wright_mcp_logs",
    ):
        assert volume in compose
    assert "wright_hermes:/home/agent/.hermes" not in compose


def test_entrypoint_materializes_mcp_bundle_config_idempotently() -> None:
    entrypoint = read_text("docker/entrypoint.sh")

    assert "materialize_mcp_bundle_config" in entrypoint
    assert "WRIGHT_MCP_HERMES_CONFIG" in entrypoint
    assert "mcp_servers" in entrypoint
    assert "os.replace(temporary, path)" in entrypoint


def test_smoke_script_covers_services_entries_and_local_tooling() -> None:
    smoke = read_text("scripts/docker-mcp-smoke-test.sh")

    for expected in (
        "WRIGHT_MCP_DOCKER_IMAGE",
        "WRIGHT_MCP_SKIP_BUILD",
        "WRIGHT_MCP_DOCKER_PLATFORM",
        "show_container_diagnostics",
        "docker inspect -f '{{.State.Running}}'",
        "wright-api-stderr.log",
        "http://localhost:8000/api/health",
        "hermes-gateway",
        "openscad-mcp",
        "freecad-mcp",
        "brep-mcp",
        "solid-edge-mcp",
        "playwright-mcp",
        "command -v brep",
        "command -v playwright-mcp",
    ):
        assert expected in smoke


def test_docs_link_mcp_quickstart_from_existing_guides() -> None:
    readme = read_text("README.md")
    quickstart = read_text("docs/getting-started/quickstart-docker.md")
    docker_guide = read_text("docs/user-guide/docker.md")

    assert "quickstart-docker-mcp.md" in readme
    assert "quickstart-docker-mcp.md" in quickstart
    assert "quickstart-docker-mcp.md" in docker_guide


def test_engineer_quickstart_contains_required_sections_and_corrected_tools() -> None:
    guide = read_text("docs/getting-started/quickstart-docker-mcp.md")
    squashed = " ".join(guide.split()).lower()

    for expected in (
        "what this image includes",
        "before you start",
        "run with docker compose",
        "open wright",
        "remote access",
        "included tools",
        "verification prompts",
        "cleanup",
        "third-party license",
    ):
        assert expected in squashed

    for expected in ("openscad", "freecad", "brep", "solidedgemcp", "playwright mcp"):
        assert expected in squashed
    assert "opencad" not in squashed
    assert "opencascade" not in squashed
