from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_docker_smoke_script_matches_entrypoint_llm_contract() -> None:
    script = read_text("scripts/docker-smoke-test.sh")
    entrypoint = read_text("docker/entrypoint.sh")

    assert "WRIGHT_DOCKER_IMAGE" in script
    assert "WRIGHT_DOCKER_SKIP_BUILD" in script
    assert "Testing setup-pending warning with missing LLM_API_URL" in script
    assert "Warning: LLM_API_URL environment variable is not set" in script
    assert "Container warned and continued when LLM_API_URL was missing" in script
    assert "did not fail-fast" not in script
    assert "correctly failed-fast" not in script
    assert "Warning: LLM_API_URL environment variable is not set" in entrypoint


def test_docker_smoke_script_docs_include_existing_image_mode() -> None:
    readme = read_text("scripts/README.md")

    assert "warns and continues if `LLM_API_URL` is missing" in readme
    assert "WRIGHT_DOCKER_IMAGE=wright-agent:latest" in readme
    assert "WRIGHT_DOCKER_SKIP_BUILD=1" in readme


def test_docker_smoke_script_keeps_gateway_process_name() -> None:
    workflow = read_text(".github/workflows/docker-build.yml")

    assert "hermes-gateway.*RUNNING" in workflow
    assert "hermes-webui.*RUNNING" not in workflow
    assert "Hermes gateway direct health is ready" in workflow
    assert "Agent health attempt" in workflow


def test_dockerfile_pins_hermes_runtime_for_reproducible_gateway() -> None:
    dockerfile = read_text("docker/Dockerfile")

    assert "hermes-agent==0.18.0" in dockerfile


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
    assert "WRIGHT_PLUGIN_REF" in common
    assert "--ref dev|main" in common
    assert "https://github.com/burhop/wright" in common
    assert "tree/${PLUGIN_REF}/${PLUGIN_SUBDIR}" in common
    assert "--ref main" in readme
    assert "hermes plugins install" in read_text("scripts/test-hermes-plugin-install.sh")
    assert "hermes plugins remove" in read_text("scripts/test-hermes-plugin-uninstall.sh")
    assert "hermes plugins update" in read_text("scripts/test-hermes-plugin-update.sh")
