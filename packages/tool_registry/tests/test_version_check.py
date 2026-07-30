import asyncio
import json

import pytest

from tool_registry.version_check import (
    fetch_npm_latest,
    fetch_pypi_latest,
    get_npm_installed,
    get_package_info,
    get_pip_installed,
)


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (["uvx", "creo-mcp"], ("uvx", "creo-mcp")),
        (["uv", "run", "openscad-mcp"], ("uv", "openscad-mcp")),
        (
            ["uv", "run", "safe-github.com-name", "--verbose"],
            ("uv", "safe-github.com-name"),
        ),
        (
            ["uv", "run", "ordinary.git-name", "--verbose"],
            ("uv", "ordinary.git-name"),
        ),
        (
            [
                "uv",
                "run",
                "--with",
                "git+https://github.com/example/repo.git@v1.2.3",
                "repo-tool",
            ],
            ("uv", "repo-tool"),
        ),
        (["pip", "show", "solidworks-mcp-python"], ("pip", "solidworks-mcp-python")),
        (["npx", "-y", "@siemens/element-mcp"], ("npm", "@siemens/element-mcp")),
        (
            ["npx", "@mcp-b/webmcp-local-relay@latest"],
            ("npm", "@mcp-b/webmcp-local-relay"),
        ),
    ],
)
def test_get_package_info_accepts_structural_package_and_vcs_forms(
    command: list[str], expected: tuple[str, str]
):
    assert get_package_info(command) == expected


@pytest.mark.parametrize(
    "token",
    [
        "github.com.evil/package",
        "git+https://github.com.evil/repo.git",
        "git+https://github.com/example/repo",
        "git+https://github.com/example/repo.git?option=evil",
        "../../package",
        "--target",
        "package;command",
        "package%2fescape",
        "package#fragment",
    ],
)
def test_get_package_info_rejects_malformed_or_trusted_looking_tokens(token: str):
    assert get_package_info(["uv", "run", token]) == ("uv", None)


def test_invalid_vcs_requirement_does_not_fall_through_to_executable():
    assert get_package_info(
        [
            "uv",
            "run",
            "--with",
            "git+https://github.com.evil/repo.git",
            "repo-tool",
        ]
    ) == ("uv", None)


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_registry_urls_encode_validated_package_as_one_path_value(monkeypatch):
    urls: list[str] = []

    def urlopen(request, timeout):
        urls.append(request.full_url)
        payload = (
            {"version": "1.0.0"}
            if "npmjs" in request.full_url
            else {"info": {"version": "1.0.0"}}
        )
        return _Response(payload)

    monkeypatch.setattr("tool_registry.version_check.urllib.request.urlopen", urlopen)

    assert fetch_pypi_latest("solidworks-mcp-python") == "1.0.0"
    assert fetch_npm_latest("@siemens/element-mcp") == "1.0.0"
    assert urls == [
        "https://pypi.org/pypi/solidworks-mcp-python/json",
        "https://registry.npmjs.org/%40siemens%2Felement-mcp/latest",
    ]


@pytest.mark.asyncio
async def test_invalid_packages_never_reach_registry_or_subprocess(monkeypatch):
    def forbidden_urlopen(*args, **kwargs):
        raise AssertionError("registry request was not expected")

    async def forbidden_subprocess(*args, **kwargs):
        raise AssertionError("subprocess was not expected")

    monkeypatch.setattr(
        "tool_registry.version_check.urllib.request.urlopen", forbidden_urlopen
    )
    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden_subprocess)

    assert fetch_pypi_latest("--target") is None
    assert fetch_npm_latest("../../package") is None
    assert await get_pip_installed("--target") is None
    assert await get_npm_installed("../../package") is None
