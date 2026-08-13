import json
from datetime import UTC, datetime

import pytest
from fixtures.mcp_imports import ADVERSARIAL_LOCAL, OVERSIZED_DOCUMENT
from tool_registry.config_import import (
    ConfigurationImportError,
    ImportPreviewRepository,
    preview_configuration,
)

NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("configuration", "code"),
    [
        ('{"command":"uvx","command":"python"}', "import_duplicate_key"),
        ("not-json", "import_json_invalid"),
        (OVERSIZED_DOCUMENT, "import_too_large"),
    ],
    ids=["duplicate", "invalid-json", "oversized"],
)
def test_invalid_documents_fail_closed(configuration: str, code: str) -> None:
    with pytest.raises(ConfigurationImportError) as captured:
        preview_configuration(configuration, now=NOW)
    assert captured.value.code == code


def test_adversarial_shell_and_secret_input_is_redacted_and_never_expanded() -> None:
    preview = preview_configuration(ADVERSARIAL_LOCAL, now=NOW)
    draft = preview["drafts"][0]
    codes = {item["code"] for item in draft["errors"]}
    assert "command_unsafe" in codes
    assert "argument_shell_expression" in codes
    serialized = json.dumps(preview)
    assert "do-not-persist" not in serialized
    assert "whoami" in serialized  # literal diagnostic input, never executed


def test_mixed_validity_unknown_fields_invalid_url_and_missing_input() -> None:
    preview = preview_configuration(
        {
            "inputs": [],
            "servers": {
                "good": {"command": "uvx", "args": ["safe-mcp"]},
                "bad": {
                    "type": "http",
                    "url": "http://vendor.invalid/mcp#fragment",
                    "headers": {"Authorization": "${input:missing}"},
                    "surprise": True,
                },
            },
        },
        now=NOW,
    )
    assert len(preview["drafts"]) == 2
    bad = next(item for item in preview["drafts"] if item["name"] == "bad")
    assert {item["code"] for item in bad["errors"]} == {
        "endpoint_scheme_unsafe",
        "input_reference_unknown",
    }
    assert bad["warnings"][0]["code"] == "field_ignored"


def test_repository_retains_only_normalized_preview_and_honors_expiry() -> None:
    repository = ImportPreviewRepository()
    preview = repository.create(ADVERSARIAL_LOCAL, now=NOW)
    stored = repository.get(preview["preview_id"], now=NOW)
    assert "do-not-persist" not in json.dumps(repository.__dict__, default=str)
    assert stored == preview

    with pytest.raises(ConfigurationImportError, match="expired") as captured:
        repository.get(
            preview["preview_id"],
            now=datetime(2026, 8, 12, 13, tzinfo=UTC),
        )
    assert captured.value.code == "import_preview_expired"
