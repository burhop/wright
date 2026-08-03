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
    servers = {entry["id"]: entry for entry in bundle["mcp_servers"]}
    server_ids = set(servers)
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
    assert servers["playwright-mcp"]["install"]["playwright_mcp_browsers"] == ["chrome-for-testing"]


def test_arm64_bundle_uses_platform_native_freecad_source() -> None:
    bundle = yaml.safe_load(read_text("docker/mcp-bundle.linux-arm64.yaml"))
    apps = {entry["id"]: entry for entry in bundle["applications"]}

    assert bundle["bundle_id"] == "wright-mcp-appliance-linux-arm64"
    assert bundle["base_image"] == "wright:standard-linux-arm64"
    assert apps["freecad"]["source"]["type"] == "github_release"
    assert "Linux-aarch64" in apps["freecad"]["source"]["url"]
    assert "freecad" not in apps["freecad"]["install"]["system_packages"]
    assert apps["freecad"]["install"]["release_assets"]
    assert "Linux-x86_64" not in yaml.safe_dump(apps["freecad"])
    assert "Linux-aarch64" in yaml.safe_dump(apps["freecad"])
    servers = {entry["id"]: entry for entry in bundle["mcp_servers"]}
    assert servers["playwright-mcp"]["install"]["playwright_mcp_browsers"] == ["chrome-for-testing"]


def test_windows_bundle_declares_windows_runnable_mcp_subset_and_solid_edge_boundary() -> None:
    bundle = yaml.safe_load(read_text("docker/mcp-bundle.windows-amd64.yaml"))
    applications = {entry["id"]: entry for entry in bundle["applications"]}
    servers = {entry["id"]: entry for entry in bundle["mcp_servers"]}

    assert bundle["bundle_id"] == "wright-mcp-appliance-windows-amd64"
    assert applications["solid-edge"]["availability"] == "windows_only"
    assert applications["solid-edge"]["compliance_profile"]["id"] == "blocked"
    assert servers["solid-edge-mcp"]["mcp_source"]["default_url"] == "https://github.com/burhop/SolidEdgeMCP.git"
    assert servers["solid-edge-mcp"]["mcp_source"]["default_ref"] == "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330"
    assert servers["brep-mcp"]["launch"]["command"] == ["node", "C:/wright/mcp/bin/brep-mcp-wrapped.cjs"]
    assert servers["playwright-mcp"]["install"]["playwright_mcp_browsers"] == ["chrome-for-testing"]
    assert "C:/wright/workspace" in yaml.safe_dump(servers["solid-edge-mcp"])


def test_validator_accepts_default_bundle() -> None:
    verifier = load_module(VERIFY_PATH, "verify_bundle_default")
    result = verifier.validate_bundle_file(ROOT / "docker" / "mcp-bundle.yaml")

    assert result["ok"] is True
    assert {item["status"] for item in result["applications"]} == {"accepted"}
    server_status = {item["id"]: item["status"] for item in result["mcp_servers"]}
    assert server_status == {
        "openscad-mcp": "accepted",
        "freecad-mcp": "accepted",
        "brep-mcp": "accepted",
        "solid-edge-mcp": "blocked",
        "playwright-mcp": "accepted",
    }


@pytest.mark.parametrize(
    "bundle_name",
    ["mcp-bundle.yaml", "mcp-bundle.linux-arm64.yaml", "mcp-bundle.windows-amd64.yaml"],
)
def test_validator_accepts_managed_platform_bundles(bundle_name: str) -> None:
    verifier = load_module(VERIFY_PATH, f"verify_bundle_{bundle_name.replace('.', '_')}")
    result = verifier.validate_bundle_file(ROOT / "docker" / bundle_name)

    assert result["ok"] is True


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

    assert "# syntax=docker/dockerfile:1.7" in dockerfile
    assert "ARG WRIGHT_BASE_IMAGE=wright:test" in dockerfile
    assert "FROM ${WRIGHT_BASE_IMAGE}" in dockerfile
    assert "FROM node:26.5.1-slim" in dockerfile
    assert "COPY --from=node-runtime" in dockerfile
    assert "WRIGHT_MCP_BUNDLE_FILE" in dockerfile
    assert "mcp-bundle*.yaml" in dockerfile
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_URL" in dockerfile
    assert "https://github.com/burhop/SolidEdgeMCP.git" in dockerfile
    assert "2aad5bd24df6ce1ac9578ad35c4da7ac241b5330" in dockerfile
    assert "verify-bundle.py" in dockerfile
    assert "generate-config.py" in dockerfile
    assert "--mount=type=secret,id=github_token" in dockerfile
    assert "WRIGHT_MCP_GITHUB_TOKEN_FILE=/run/secrets/github_token" in dockerfile
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
        "playwright_mcp_browsers",
        "playwright-mcp install-browser --with-deps",
        "link_system_app_binaries",
        "default_url",
        "SolidEdgeMcpServer",
        "not runnable inside this Linux appliance",
        "freecad-mcp-wrapped",
        "brep-mcp-wrapped",
        "brep-mcp-launcher.cjs",
        "solid-edge-mcp",
        "WRIGHT_SOLIDEDGE_MCP_GIT_URL",
        "WRIGHT_MCP_GITHUB_TOKEN_FILE",
        "GIT_ASKPASS",
    ):
        assert expected in script
    assert "brep-caid-opencascade" not in script
    assert "OpenCASCADE" not in script


def test_base_dockerfile_normalizes_supervisor_config_permissions() -> None:
    dockerfile = read_text("docker/Dockerfile")

    assert "COPY docker/supervisord.conf /etc/supervisor/conf.d/wright.conf" in dockerfile
    assert "chmod 444 /etc/supervisor/conf.d/wright.conf" in dockerfile
    assert "linux-aarch64" in dockerfile
    assert "MICROMAMBA_ARM64_SHA256=6ec1517c8c89c875a8fa93f9c66abd4fe3dd147341376bdc37b57c526bc13e44" in dockerfile


def test_compose_mcp_uses_separate_volume_names_and_same_port_contract() -> None:
    compose = read_text("docker-compose.mcp.yml")

    assert "image: ${WRIGHT_MCP_IMAGE:-wright:engineering-tools-linux-amd64}" in compose
    assert "127.0.0.1:8080:8000" in compose
    assert "platform: ${WRIGHT_MCP_DOCKER_PLATFORM:-linux/amd64}" in compose
    assert "WRIGHT_MCP_BUNDLE_FILE: ${WRIGHT_MCP_BUNDLE_FILE:-mcp-bundle.yaml}" in compose
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_URL: ${WRIGHT_SOLIDEDGE_MCP_GIT_URL:-https://github.com/burhop/SolidEdgeMCP.git}" in compose
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_REF: ${WRIGHT_SOLIDEDGE_MCP_GIT_REF:-2aad5bd24df6ce1ac9578ad35c4da7ac241b5330}" in compose
    assert "github_token" in compose
    assert "environment: GITHUB_TOKEN" in compose
    for volume in (
        "${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp}_data",
        "${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp}_workspaces",
        "${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp}_config",
        "${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp}_hermes",
        "${WRIGHT_MCP_VOLUME_PREFIX:-wright_mcp}_logs",
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
        "WRIGHT_MCP_BUNDLE_FILE",
        "github_token",
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
        "brep-mcp-wrapped",
        "command -v playwright-mcp",
        "@playwright/mcp/node_modules/playwright-core",
    ):
        assert expected in smoke


def test_brep_mcp_launcher_wraps_pinned_package_without_editing_it() -> None:
    launcher = read_text("docker/mcp/brep-mcp-launcher.cjs")

    assert "BREPJS_CAD_ROOT" in launcher
    assert "APPDATA" in launcher
    assert "npm_config_prefix" in launcher
    assert "dist\", \"mcp\", \"server.cjs" in launcher
    assert "dist\", \"cli\", \"main.js" in launcher
    assert "global.URL" in launcher
    assert "url.fileURLToPath" in launcher
    assert "require(mcpEntry)" in launcher


def test_image_family_declares_four_managed_images_with_persisted_paths() -> None:
    family = yaml.safe_load(read_text("docker/image-family.yaml"))
    images = {entry["id"]: entry for entry in family["images"]}

    assert set(images) == {
        "wright-standard",
        "wright-mcp-linux-amd64",
        "wright-mcp-linux-arm64",
        "wright-mcp-windows-amd64",
    }
    assert images["wright-mcp-linux-amd64"]["platform"] == "linux/amd64"
    assert images["wright-mcp-linux-arm64"]["platform"] == "linux/arm64"
    assert images["wright-mcp-windows-amd64"]["platform"] == "windows/amd64"
    assert (
        images["wright-mcp-linux-amd64"]["image"]
        == "wright:engineering-tools-linux-amd64"
    )
    assert (
        images["wright-mcp-linux-arm64"]["image"]
        == "wright:engineering-tools-linux-arm64"
    )
    assert (
        images["wright-mcp-windows-amd64"]["image"]
        == "wright:engineering-tools-windows-amd64"
    )
    for image in images.values():
        assert image["persisted_paths"]


def test_platform_build_scripts_cover_linux_arm64_and_windows_host_paths() -> None:
    shell = read_text("scripts/docker-image-family-build.sh")
    powershell = read_text("scripts/docker-image-family-build.ps1")
    windows_run = read_text("scripts/docker-mcp-run-windows.ps1")
    windows_dockerfile = read_text("docker/Dockerfile.windows.mcp")

    assert "mcp-bundle.linux-arm64.yaml" in shell
    assert "wright:engineering-tools-linux-arm64" in shell
    assert "wright:engineering-tools-linux-arm64" in read_text("scripts/docker-mcp-run.sh")
    assert "linux/arm64" in shell
    assert "docker/Dockerfile.windows.mcp" in powershell
    assert "windows-amd64" in powershell
    assert "wright:engineering-tools-windows-amd64" in powershell
    assert "github_token" in shell
    assert "github_token" in powershell
    assert "WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL" in powershell
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_REF=$solidEdgeRef" in powershell
    assert "C:\\wright\\workspace" in windows_run
    assert "WRIGHT_SOLIDEDGE_MCP_GIT_URL" in windows_dockerfile
    assert "WRIGHT_SOLIDEDGE_MCP_ARCHIVE_URL" in windows_dockerfile
    assert "brep-mcp-wrapped.cjs" in windows_dockerfile
    assert "playwright-mcp install-browser chrome-for-testing" in windows_dockerfile


def test_engineering_tools_image_family_cd_publishes_clear_tags() -> None:
    workflow = read_text(".github/workflows/docker-image-family.yml")
    docker_hub_readme = read_text("docker/DOCKER_HUB_README.md")
    ci_docs = read_text("docs/contributing/ci-cd-workflows.md")

    for text in (docker_hub_readme, ci_docs):
        assert "engineering-tools-linux-amd64" in text
        assert "engineering-tools-linux-arm64" in text
    assert 'tag="${prefix}-engineering-tools-${PROFILE}"' in workflow
    assert "profile: linux-amd64" in workflow
    assert "profile: linux-arm64" in workflow
    assert "ubuntu-24.04-arm" in workflow
    assert "DOCKERHUB_TOKEN is required to publish engineering-tools images" in workflow
    assert "scripts/docker-mcp-smoke-test.sh" in workflow


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
