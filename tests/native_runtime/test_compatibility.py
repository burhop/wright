from __future__ import annotations

import json
from pathlib import Path

import pytest

from wright_engineering.runtime.compatibility import (
    CompatibilityError,
    CompatibilityPolicy,
)


def _policy(tmp_path: Path, **overrides: object) -> CompatibilityPolicy:
    payload: dict[str, object] = {
        "contract_version": 2,
        "runtime_version": "0.1.5",
        "runtime_specifier": "==0.1.5",
        "python_specifier": ">=3.11,<3.15",
        "platforms": ["windows-x86_64", "linux-x86_64", "macos-arm64"],
        "data_schema": {"min": 1, "max": 3},
        "manager_protocols": {
            "cli": {
                "adapter_protocol": "wright-lifecycle-v1",
                "install_interface": "console-script",
            },
            "hermes": {
                "adapter_protocol": "hermes-git-plugin-v1",
                "install_interface": "git",
                "host_specifier": ">=0.19,<1",
            },
            "codex": {
                "adapter_protocol": "mcp-v1",
                "install_interface": "mcp-config",
                "transports": ["stdio", "streamable-http"],
            },
        },
    }
    payload.update(overrides)
    path = tmp_path / "compatibility.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return CompatibilityPolicy.load(path)


def test_runtime_and_real_hermes_git_protocol_are_accepted(tmp_path: Path) -> None:
    _policy(tmp_path).require_compatible(
        runtime_version="0.1.5",
        manager_id="hermes",
        manager_version="0.19.0",
        adapter_protocol="hermes-git-plugin-v1",
        python_version="3.13.5",
        platform_tag="windows-x86_64",
        data_schema=2,
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("runtime_version", "0.2.0", "runtime_incompatible"),
        ("manager_version", "0.18.2", "manager_version_incompatible"),
        ("adapter_protocol", "python-distribution-v1", "manager_protocol_incompatible"),
        ("manager_id", "unknown", "manager_unsupported"),
        ("python_version", "3.10.14", "python_incompatible"),
        ("platform_tag", "linux-arm64", "platform_incompatible"),
        ("data_schema", 4, "data_schema_incompatible"),
    ],
)
def test_incompatibility_fails_closed(
    tmp_path: Path, field: str, value: object, code: str
) -> None:
    values: dict[str, object] = {
        "runtime_version": "0.1.5",
        "manager_id": "hermes",
        "manager_version": "0.19.0",
        "adapter_protocol": "hermes-git-plugin-v1",
        "python_version": "3.13.5",
        "platform_tag": "windows-x86_64",
        "data_schema": 2,
    }
    values[field] = value
    with pytest.raises(CompatibilityError) as exc:
        _policy(tmp_path).require_compatible(**values)  # type: ignore[arg-type]
    assert exc.value.code == code


def test_missing_or_malformed_contract_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(CompatibilityError, match="compatibility_contract_missing"):
        CompatibilityPolicy.load(tmp_path / "missing.json")
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(CompatibilityError, match="compatibility_contract_invalid"):
        CompatibilityPolicy.load(path)
