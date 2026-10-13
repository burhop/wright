import json

import pytest

from core.redaction import (
    REDACTED,
    redact_command,
    redact_evidence,
    redact_mapping,
    redact_text,
)


def test_redact_text_scrubs_secret_assignments_and_bearer_tokens():
    text = "API_TOKEN=hunter2 Authorization: Bearer abc.def"

    redacted = redact_text(text)

    assert "hunter2" not in redacted
    assert "abc.def" not in redacted
    assert REDACTED in redacted


def test_redact_mapping_scrubs_secret_keys_recursively():
    payload = {
        "env": {"API_KEY": "secret", "SAFE": "value"},
        "args": [{"password": "pw"}],
    }

    redacted = redact_mapping(payload)

    assert redacted["env"]["API_KEY"] == REDACTED
    assert redacted["env"]["SAFE"] == "value"
    assert redacted["args"][0]["password"] == REDACTED


def test_redact_command_scrubs_secret_flags_and_assignments():
    command = ["tool", "--token", "abc123", "password=hunter2", "--safe", "ok"]

    redacted = redact_command(command)

    assert "abc123" not in redacted
    assert "hunter2" not in redacted
    assert "--safe ok" in redacted


@pytest.mark.parametrize("header", ["X-Download-Ticket", "X-Upload-Ticket"])
def test_one_time_transfer_headers_are_removed_from_mappings_and_commands(header):
    secret = "test-transfer-value.a/b+padding=="
    command = f"curl -H '{header}: {secret}' https://files.example/model.step"
    payload = {"headers": {header: secret}, "download": {"command": command}}

    redacted = redact_mapping(payload)

    assert redacted["headers"][header] == REDACTED
    assert secret not in json.dumps(redacted)
    assert "https://files.example/model.step" in redacted["download"]["command"]
    assert secret not in redact_command(command)
    assert secret not in redact_command(["curl", "-H", f"{header}: {secret}"])


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_transfer_header_redaction_preserves_embedded_json_at_each_encoding_depth(
    depth,
):
    secret = "fake-transfer-credential"
    value = {"headers": {"x-download-ticket": secret}, "artifact": "part.step"}
    text = json.dumps(value)
    for _ in range(depth):
        text = json.dumps({"text": text})

    redacted = redact_text(text)

    assert secret not in redacted
    decoded = json.loads(redacted)
    for _ in range(depth):
        decoded = json.loads(decoded["text"])
    assert decoded == {
        "headers": {"x-download-ticket": REDACTED},
        "artifact": "part.step",
    }


def test_public_report_ticket_id_and_noncredential_ticket_word_remain_observable():
    payload = {"ticket_id": "BUG-42", "message": "Track the report ticket BUG-42."}
    assert redact_mapping(payload) == payload


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_evidence_redacts_json_credentials_without_changing_public_identity(depth):
    payload = {
        "headers": {"Authorization": "Bearer private-test-value"},
        "credential_binding_digest": "a" * 64,
        "max_tokens": 4096,
        "ticket_id": "BUG-42",
        "source_digest": "b" * 64,
        "command": 'curl -H "X-Download-Ticket: private-transfer-value==" URL',
        "env": {"API_TOKEN": "private-environment-value"},
    }
    value = payload
    for _ in range(depth):
        value = {"text": json.dumps(value)}

    clean = redact_evidence(value)

    assert not any(
        secret in json.dumps(clean)
        for secret in (
            "private-test-value",
            "private-transfer-value",
            "private-environment-value",
        )
    )
    for _ in range(depth):
        clean = json.loads(clean["text"])
    assert clean["credential_binding_digest"] == "a" * 64
    assert clean["source_digest"] == "b" * 64
    assert clean["max_tokens"] == 4096
    assert clean["ticket_id"] == "BUG-42"
    assert payload["env"]["API_TOKEN"] == "private-environment-value"


def test_public_evidence_preserves_original_embedded_json_bytes():
    value = {
        "response": '{"measurements": [1,2], "units":"mm"}',
        "credential_binding_digest": "c" * 64,
        "token_count": 30,
    }
    assert redact_evidence(value) == value


@pytest.mark.parametrize("container", [list, tuple])
def test_evidence_preserves_provenance_containers_while_redacting_nested_secrets(
    container,
):
    secret = "fake-sequence-transfer-value"
    revisions = container([("source", "a" * 64)])
    payload = {
        "input_revisions": revisions,
        "nested": container(
            [{"headers": {"X-Download-Ticket": secret}, "reference": ("part", 2)}]
        ),
    }

    clean = redact_evidence(payload)

    assert clean["input_revisions"] == revisions
    assert type(clean["input_revisions"]) is container
    assert type(clean["nested"]) is container
    assert clean["nested"][0]["reference"] == ("part", 2)
    assert clean["nested"][0]["headers"]["X-Download-Ticket"] == REDACTED
    assert secret not in json.dumps(clean)
    assert payload["nested"][0]["headers"]["X-Download-Ticket"] == secret
    assert redact_evidence(clean) == clean
