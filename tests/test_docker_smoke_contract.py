from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_docker_smoke_script_matches_entrypoint_llm_contract() -> None:
    script = read_text("scripts/docker-smoke-test.sh")
    entrypoint = read_text("docker/entrypoint.sh")

    assert "WRIGHT_DOCKER_IMAGE" in script
    assert "WRIGHT_DOCKER_SKIP_BUILD" in script
    assert "Testing setup-pending warning with missing LLM provider" in script
    assert "Warning: no LLM provider is configured" in script
    assert (
        "Container warned and continued when LLM provider settings were missing"
        in script
    )
    assert "did not fail-fast" not in script
    assert "correctly failed-fast" not in script
    assert "Warning: no LLM provider is configured" in entrypoint


def test_hermes_api_key_is_safe_when_it_starts_with_option_prefix() -> None:
    smoke = read_text("scripts/docker-smoke-test.sh")
    entrypoint = read_text("docker/entrypoint.sh")
    profile_setup = read_text("scripts/setup-wright-profile.sh")

    assert 'HERMES_API_KEY="-ci-smoke-leading-hyphen"' in smoke
    assert 'config set API_SERVER_KEY -- "${HERMES_API_KEY}"' in entrypoint
    assert 'config set API_SERVER_KEY -- "${HERMES_API_KEY}"' in profile_setup
    assert "Container failed while testing setup-pending startup" in smoke


def test_docker_smoke_script_docs_include_existing_image_mode() -> None:
    readme = read_text("scripts/README.md")

    assert "warns and continues if no LLM provider is configured" in readme
    assert "WRIGHT_DOCKER_IMAGE=wright:latest" in readme
    assert "WRIGHT_DOCKER_SKIP_BUILD=1" in readme
    assert "reconcile_hermes_pip_check.py" in readme


def test_private_mcp_build_helpers_accept_active_gh_token_with_stale_accounts() -> None:
    smoke = read_text("scripts/docker-mcp-smoke-test.sh")
    linux_family = read_text("scripts/docker-image-family-build.sh")
    windows_family = read_text("scripts/docker-image-family-build.ps1")

    for script in (smoke, linux_family, windows_family):
        assert "gh auth token" in script
        assert "id=github_token,env=GITHUB_TOKEN" in script
        assert "gh auth status" not in script


def test_mcp_smoke_executes_brep_cli_and_stdio_handshake() -> None:
    smoke = read_text("scripts/docker-mcp-smoke-test.sh")

    assert "brep --help >/dev/null" in smoke
    assert 'command="/opt/wright/mcp/bin/brep-mcp-wrapped"' in smoke
    assert 'if "run_program" not in names:' in smoke


def test_docker_smoke_script_keeps_gateway_process_name() -> None:
    workflow = read_text(".github/workflows/docker-build.yml")
    smoke = read_text("scripts/docker-smoke-test.sh")

    assert "WRIGHT_DOCKER_SKIP_BUILD=1 scripts/docker-smoke-test.sh" in workflow
    assert "hermes-gateway" in smoke
    assert "hermes-webui.*RUNNING" not in workflow
    assert "Hermes gateway direct health is ready" in smoke
    assert "Agent health attempt" in smoke


def test_dockerfile_pins_hermes_runtime_for_reproducible_gateway() -> None:
    dockerfile = read_text("docker/Dockerfile")

    assert (
        "python:3.13-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a"
        in dockerfile
    )
    assert "hermes-agent==0.19.0" in dockerfile


def test_docker_runtime_serves_image_built_frontend_dist() -> None:
    dockerfile = read_text("docker/Dockerfile")
    dockerignore = read_text(".dockerignore")
    supervisor = read_text("docker/supervisord.conf")
    mcp_run = read_text("scripts/docker-mcp-run.sh")
    mcp_dockerfile = read_text("docker/Dockerfile.mcp")

    assert "ENV FRONTEND_DIST_DIR=/workspace/apps/web/dist" in dockerfile
    assert "ENV WRIGHT_WORKSPACES_DIR=/home/agent/workspace" in dockerfile
    assert "ENV WRIGHT_WORKSPACE_PATH=/home/agent/workspace" in dockerfile
    assert "ENV WRIGHT_MCP_BUNDLE=" in dockerfile
    assert "ENV WRIGHT_MCP_HERMES_CONFIG=" in dockerfile
    assert "ENV WRIGHT_MCP_STATUS=" in dockerfile
    assert "ARG VITE_WRIGHT_PROCESS_DEFINITION_VIEW=0" in dockerfile
    assert (
        'VITE_WRIGHT_PROCESS_DEFINITION_VIEW="${VITE_WRIGHT_PROCESS_DEFINITION_VIEW}"'
        in dockerfile
    )
    assert "npm run build --workspace=apps/web" in dockerfile
    assert (
        "COPY --from=web-builder /usr/local/bin/node /usr/local/bin/node" in dockerfile
    )
    assert "COPY --from=web-builder /usr/local/lib/node_modules" in dockerfile
    assert "integrations/rivet/editor/ integrations/rivet/editor/" in dockerfile
    assert "integrations/rivet/runner/ integrations/rivet/runner/" in dockerfile
    assert "integrations/rivet/spike/" in dockerignore
    assert "!integrations/rivet/editor/dist/**" in dockerignore
    assert "!integrations/rivet/runner/dist/**" in dockerignore
    for feature_flag in (
        "WRIGHT_RIVET_WORKFLOWS_ENABLED=1",
        "WRIGHT_RIVET_RUNNER_ENABLED=1",
        "WRIGHT_RIVET_EDITOR_ENABLED=1",
        "WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED=1",
        "WRIGHT_SURFACES_ENABLED=1",
        "WRIGHT_SURFACES_LIVE_APPS_ENABLED=1",
    ):
        assert f"ENV {feature_flag}" in dockerfile
    assert (
        "mkdir -p /home/agent/.config /home/agent/.cache /home/agent/.local/share"
        in dockerfile
    )
    assert (
        "mkdir -p /home/agent/.config /home/agent/.cache /home/agent/.local/share"
        in mcp_dockerfile
    )
    assert 'FRONTEND_DIST_DIR="%(ENV_FRONTEND_DIST_DIR)s"' in supervisor
    assert 'WRIGHT_WORKSPACES_DIR="%(ENV_WRIGHT_WORKSPACES_DIR)s"' in supervisor
    assert 'WRIGHT_WORKSPACE_PATH="%(ENV_WRIGHT_WORKSPACE_PATH)s"' in supervisor
    assert 'WRIGHT_MCP_BUNDLE="%(ENV_WRIGHT_MCP_BUNDLE)s"' in supervisor
    assert 'WRIGHT_MCP_HERMES_CONFIG="%(ENV_WRIGHT_MCP_HERMES_CONFIG)s"' in supervisor
    assert 'WRIGHT_MCP_STATUS="%(ENV_WRIGHT_MCP_STATUS)s"' in supervisor
    assert "-e WRIGHT_WORKSPACES_DIR=/home/agent/workspace" in mcp_run
    assert "-e WRIGHT_WORKSPACE_PATH=/home/agent/workspace" in mcp_run
    assert (
        '-e FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-/workspace/apps/web/dist}"'
        in mcp_run
    )


def test_docker_smoke_strictly_reconciles_hermes_security_overrides() -> None:
    dockerfile = read_text("docker/Dockerfile")
    smoke = read_text("scripts/docker-smoke-test.sh")

    assert '"cryptography==50.0.0"' in dockerfile
    assert '"pillow==12.3.0"' in dockerfile
    assert '"msgpack==1.2.1"' in dockerfile
    assert (
        "debian:trixie-slim@sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258"
        in dockerfile
    )
    assert '"setuptools==84.0.0"' in dockerfile
    assert "pip/_vendor" in dockerfile
    assert "setuptools@78.1.1" in dockerfile
    assert "brace-expansion@5.0.9" in dockerfile
    assert "ip-address@10.3.1" in dockerfile
    assert "tar@7.5.22" in dockerfile
    assert "unexpected npm tar override" in dockerfile
    assert "libssl3t64" in dockerfile
    assert "npm install --global npm@12.0.2" in dockerfile
    assert "util-linux" in dockerfile
    assert "openssl-provider-legacy" in dockerfile
    assert "pip check --python /opt/hermes/.venv/bin/python" in smoke
    assert "reconcile_hermes_pip_check.py" in smoke


def test_docker_smoke_checks_offline_rivet_first_run_runtime() -> None:
    smoke = read_text("scripts/docker-smoke-test.sh")

    assert "NODE_VERSION=$(docker run" in smoke
    assert "EditorAssetCatalog().status()" in smoke
    assert "RunnerAssetCatalog().status()" in smoke
    assert "EditorSettings.from_env().enabled" in smoke
    assert "RunnerSettings.from_env().enabled" in smoke


def test_docker_smoke_does_not_require_host_jq() -> None:
    smoke = read_text("scripts/docker-smoke-test.sh")

    assert "jq -r" not in smoke
    assert "json.load(sys.stdin)" in smoke


def test_docker_smoke_respects_explicit_host_python() -> None:
    smoke = read_text("scripts/docker-smoke-test.sh")

    assert "export MSYS_NO_PATHCONV=1" in smoke
    assert 'PYTHON_CMD=("$PYTHON")' in smoke
    assert smoke.count('"${PYTHON_CMD[@]}"') == 2
    assert "scripts/reconcile_hermes_pip_check.py" in smoke
    assert '"${PYTHON_CMD[@]}" -c' in smoke


def test_dockerfile_copies_root_package_files_before_workspace_install() -> None:
    dockerfile = read_text("docker/Dockerfile")

    readme_copy = "COPY --chown=agent:agent README.md README.md"
    src_copy = "COPY --chown=agent:agent src/ src/"
    workspace_install = "# Install the workspace packages."

    assert readme_copy in dockerfile
    assert src_copy in dockerfile
    assert dockerfile.index(readme_copy) < dockerfile.index(workspace_install)
    assert dockerfile.index(src_copy) < dockerfile.index(workspace_install)


def test_hermes_plugin_lifecycle_scripts_are_documented_and_docker_backed() -> None:
    makefile = read_text("Makefile")
    readme = read_text("scripts/README.md")
    common = read_text("scripts/hermes-plugin-lifecycle-common.sh")

    for script in (
        "test-hermes-plugin-install.sh",
        "test-hermes-plugin-uninstall.sh",
        "test-hermes-plugin-update.sh",
    ):
        script_text = read_text(f"scripts/{script}")
        assert "hermes-plugin-lifecycle-common.sh" in script_text
        assert script in readme

    assert "hermes-plugin-lifecycle-test:" in makefile
    assert "WRIGHT_DOCKER_IMAGE" in common
    assert "WRIGHT_HERMES_EXPECTED_VERSION:-0.19.0" in common
    assert "WRIGHT_PLUGIN_REF" in common
    assert "--ref dev|main" in common
    assert "https://github.com/burhop/wright" in common
    assert "tree/${PLUGIN_REF}/${PLUGIN_SUBDIR}" in common
    assert "--ref main" in readme
    assert "hermes plugins install" in read_text(
        "scripts/test-hermes-plugin-install.sh"
    )
    assert "hermes plugins remove" in read_text(
        "scripts/test-hermes-plugin-uninstall.sh"
    )
    assert "hermes plugins update" in read_text("scripts/test-hermes-plugin-update.sh")
