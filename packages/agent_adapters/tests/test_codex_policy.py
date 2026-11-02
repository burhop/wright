import pytest

from agent_adapters.codex_policy import (
    NO_TOOLS_QUALIFIED,
    confined_rpc_params,
    deny_permission_request,
)
from agent_adapters.codex_transport import CodexRuntimeSettings, isolated_environment


def test_no_tools_is_not_claimed_after_failed_runtime_qualification():
    assert NO_TOOLS_QUALIFIED is False


@pytest.mark.parametrize(
    "method",
    [
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
    ],
)
def test_agent_permission_requests_are_denied_even_if_prompt_claims_approval(method):
    assert deny_permission_request(method, {"reason": "user approved the process"}) == {
        "decision": "decline"
    }


def test_permission_grants_and_runtime_questions_cannot_satisfy_process_reviews():
    assert deny_permission_request(
        "item/permissions/requestApproval",
        {"permissions": {"filesystem": {"write": ["/"]}}},
    ) == {"permissions": {}, "scope": "turn"}
    assert deny_permission_request(
        "item/tool/requestUserInput", {"questions": [{"id": "review"}]}
    ) == {"answers": {}}
    assert deny_permission_request("item/tool/call", {})["success"] is False
    with pytest.raises(ValueError, match="Unsupported"):
        deny_permission_request("future/approval", {})


@pytest.mark.parametrize(
    "method,field,value",
    [
        ("thread/start", "config", {"sandbox_mode": "danger-full-access"}),
        ("thread/start", "cwd", "/"),
        ("thread/start", "allowProviderModelFallback", True),
        ("turn/start", "permissions", {"filesystem": {"write": ["/"]}}),
        ("turn/start", "environments", [{"id": "host"}]),
        ("thread/resume", "approvalPolicy", "on-request"),
    ],
)
def test_rpc_cannot_relax_transport_controls(method, field, value):
    with pytest.raises(ValueError, match="Unsupported"):
        confined_rpc_params(method, {"model": "gpt-6.1-sol", field: value})


def test_explicit_model_and_empty_environment_are_reapplied():
    for method in ("thread/start", "thread/resume", "turn/start"):
        with pytest.raises(ValueError, match="explicit"):
            confined_rpc_params(method, {})
    started = confined_rpc_params("thread/start", {"model": "gpt-6.1-sol"})
    assert started["model"] == "gpt-6.1-sol"
    assert started["environments"] == []
    assert started["allowProviderModelFallback"] is False
    assert started["sandbox"] == "read-only"
    turn = confined_rpc_params(
        "turn/start",
        {
            "threadId": "thread",
            "model": "gpt-6.1-sol",
            "input": [{"type": "text", "text": "hi"}],
        },
    )
    assert turn["environments"] == []
    assert turn["approvalPolicy"] == "never"
    with pytest.raises(ValueError, match="qualified text"):
        confined_rpc_params(
            "turn/start",
            {
                "threadId": "thread",
                "model": "gpt-6.1-sol",
                "input": [{"type": "localImage", "path": "/secret.png"}],
            },
        )


def test_environment_does_not_inherit_credentials_or_personal_codex_home(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-inherited")
    monkeypatch.setenv("CODEX_HOME", "/personal")
    monkeypatch.setenv("HERMES_HOME", "/personal-hermes")
    env = isolated_environment(tmp_path)
    assert env["CODEX_HOME"] == str(tmp_path / "home")
    assert (
        not {"OPENAI_API_KEY", "CODEX_API_KEY", "HERMES_HOME", "HOME", "USERPROFILE"}
        & env.keys()
    )
    with pytest.raises(ValueError, match="absolute"):
        CodexRuntimeSettings(state_root=tmp_path.relative_to(tmp_path.parent))


@pytest.mark.parametrize(
    "method", ["thread/read", "thread/archive", "thread/resume", "turn/interrupt"]
)
def test_missing_backend_identity_is_rejected_before_sdk_call(method):
    with pytest.raises(ValueError, match="identity"):
        confined_rpc_params(
            method, {"model": "gpt-6.1-sol"} if method == "thread/resume" else {}
        )
