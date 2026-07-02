from core.redaction import REDACTED, redact_command, redact_mapping, redact_text


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
