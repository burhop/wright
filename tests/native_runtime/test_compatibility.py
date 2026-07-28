from __future__ import annotations

import json
from pathlib import Path

import pytest

from wright_engineering.hermes_plugin.compatibility import (
    CompatibilityError,
    CompatibilityPolicy,
)


def _policy(tmp_path: Path, **overrides: object) -> CompatibilityPolicy:
    payload: dict[str, object] = {
        "contract_version": 1,
        "plugin_version": "0.1.5",
        "runtime_specifier": "==0.1.5",
        "hermes_specifier": ">=0.19,<1",
        "python_specifier": ">=3.11,<3.15",
        "platforms": ["windows-x86_64", "linux-x86_64", "macos-arm64"],
        "data_schema": {"min": 1, "max": 3},
        "plugin_install_capability": "python-distribution-v1",
    }
    payload.update(overrides)
    path = tmp_path / "compatibility.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return CompatibilityPolicy.load(path)


def test_compatible_versions_platform_and_schema_are_accepted(tmp_path: Path) -> None:
    policy = _policy(tmp_path)
    policy.require_compatible(
        plugin_version="0.1.5",
        runtime_version="0.1.5",
        hermes_version="0.19.0",
        python_version="3.13.5",
        platform_tag="windows-x86_64",
        data_schema=2,
        capability="python-distribution-v1",
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("plugin_version", "0.1.4", "plugin_incompatible"),
        ("runtime_version", "0.2.0", "runtime_incompatible"),
        ("hermes_version", "0.18.2", "hermes_incompatible"),
        ("python_version", "3.10.14", "python_incompatible"),
        ("platform_tag", "linux-arm64", "platform_incompatible"),
        ("data_schema", 4, "data_schema_incompatible"),
        ("capability", "git-plugin-v1", "plugin_capability_incompatible"),
    ],
)
def test_incompatibility_fails_closed(
    tmp_path: Path, field: str, value: object, code: str
) -> None:
    values: dict[str, object] = {
        "plugin_version": "0.1.5",
        "runtime_version": "0.1.5",
        "hermes_version": "0.19.0",
        "python_version": "3.13.5",
        "platform_tag": "windows-x86_64",
        "data_schema": 2,
        "capability": "python-distribution-v1",
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


def test_production_support_requires_released_hermes_and_previous_native(
    tmp_path: Path,
) -> None:
    candidate = _policy(tmp_path)
    assert not candidate.production_native_available
    assert candidate.released_hermes_version is None

    with pytest.raises(CompatibilityError, match="compatibility_contract_invalid"):
        _policy(tmp_path, production_native_available=True)

    released = _policy(
        tmp_path,
        production_native_available=True,
        released_hermes_version="0.19.1",
        previous_native_version="0.1.4",
    )
    assert released.production_native_available
