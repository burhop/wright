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
