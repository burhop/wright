from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_external_actions import approval_subject_digest
from workspace_service.workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
    TEST_HANDOFF_BINDING,
    WorkflowIntegrationPolicyError,
    WorkflowIntegrationPolicyService,
)
from workspace_service.workflow_source_execution import PromptStep, PromptWorkflow


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Files:
    async def read_reference(self, workspace_dir, path):
        return (Path(workspace_dir) / path).read_bytes()


@pytest.fixture
def case(tmp_path):
    (tmp_path / "inputs").mkdir()
    (tmp_path / "workflows").mkdir()
    (tmp_path / "inputs/brief.md").write_bytes(b"Make a bracket, units mm")
    (tmp_path / "workflows/case.wflow").write_bytes(b"immutable accepted source")
    tool = {"server_id": "cad", "name": "cad_create", "schema_digest": "d" * 64}
    service = WorkflowIntegrationPolicyService(str(tmp_path / "state.db"), enabled=True)
    grant = dict(
        campaign_id="campaign",
        dataset_id="bracket-01",
        dataset_digest="a" * 64,
        workspace_id="workspace",
        source_path="workflows/case.wflow",
        source_digest=sha(b"immutable accepted source"),
        input_files={"inputs/brief.md": sha(b"Make a bracket, units mm")},
        output_root="outputs/attempt-01",
        allowed_tools=[tool],
        approval_mode="auto",
        test_destinations=["test://campaign/printer"],
    )
    step = PromptStep(
        "cad",
        "CAD",
        "Create bracket",
        None,
        (),
        "json",
        "outputs/attempt-01/result.json",
        True,
        "indexed",
        tool_name=tool["name"],
        server_id=tool["server_id"],
        schema_digest=tool["schema_digest"],
    )
    plan = PromptWorkflow(
        "Bracket",
        (step,),
        {
            "brief": {
                "settings": {
                    "input_mode": "workspace-file",
                    "workspace_file": "inputs/brief.md",
                }
            }
        },
        definition_digest=grant["source_digest"],
    )
    args = dict(
        workspace_id="workspace",
        workspace_dir=str(tmp_path),
        source_path=grant["source_path"],
        source_digest=grant["source_digest"],
        plan=plan,
        tool_runtime=SimpleNamespace(available=lambda: [tool]),
        files=Files(),
    )
    return SimpleNamespace(
        root=tmp_path, service=service, grant=grant, args=args, step=step, tool=tool
    )


def test_default_disabled_even_with_persisted_grant(case, monkeypatch):
    identity = case.service.enroll(**case.grant)
    monkeypatch.delenv("WRIGHT_WORKFLOW_INTEGRATION_TESTS", raising=False)
    disabled = WorkflowIntegrationPolicyService(str(case.root / "state.db"))
    with pytest.raises(WorkflowIntegrationPolicyError, match="disabled"):
        disabled.get(identity)
    with pytest.raises(WorkflowIntegrationPolicyError, match="disabled"):
        disabled.enroll(**case.grant)


@pytest.mark.asyncio
async def test_exact_run_allowed_without_public_qualification(case):
    identity = case.service.enroll(**case.grant)
    context = await case.service.authorize(identity, **case.args)
    assert context["integration_policy_digest"] == identity
    assert context["actor"] == "integration_test:campaign"
    assert context["execution_kind"] == "integration"
    assert "verified" not in context and "ready" not in context


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["source", "input", "schema", "workspace", "path", "new_input"]
)
async def test_changed_identity_blocks_before_execution(case, change):
    identity = case.service.enroll(**case.grant)
    if change in {"source", "input"}:
        relative = "workflows/case.wflow" if change == "source" else "inputs/brief.md"
        (case.root / relative).write_bytes(b"changed")
    elif change == "schema":
        case.args["tool_runtime"] = SimpleNamespace(
            available=lambda: [{**case.tool, "schema_digest": "f" * 64}]
        )
    elif change == "workspace":
        case.args["workspace_id"] = "other"
    elif change == "path":
        case.args["source_path"] = "workflows/other.wflow"
    else:
        case.args["plan"] = replace(
            case.args["plan"],
            inputs={
                "brief": {"settings": {"workspace_file": "inputs/not-enrolled.md"}}
            },
        )
    with pytest.raises(WorkflowIntegrationPolicyError):
        await case.service.authorize(identity, **case.args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "outputs/other/file.step",
        "../outside.step",
        "C:/outside.step",
        "outputs/attempt-01",
    ],
)
async def test_output_confinement(case, path):
    identity = case.service.enroll(**case.grant)
    case.args["plan"] = replace(
        case.args["plan"], steps=(replace(case.step, expected_files=(path,)),)
    )
    with pytest.raises(WorkflowIntegrationPolicyError):
        await case.service.authorize(identity, **case.args)


def local_action():
    return dict(
        action_kind="local_review",
        binding=LOCAL_REVIEW_BINDING,
        destination=LOCAL_REVIEW_DESTINATION,
        settings={"review_task_id": "review"},
        action={"kind": "local_review", "mode": "review_only"},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind",
    [
        "local_review",
        "printer_transfer",
        "supplier_upload_preview",
        "cart_quote_handoff",
    ],
)
async def test_exact_local_and_test_actions_allowed(case, kind):
    action = local_action()
    if kind != "local_review":
        action = dict(
            action_kind=kind,
            binding=TEST_HANDOFF_BINDING,
            destination={"kind": "test", "id": "test://campaign/printer"},
            settings={"receipt_path": "outputs/attempt-01/handoff.json"},
            action={"kind": kind},
        )
    identity = case.service.enroll(**case.grant)
    review = replace(
        case.step,
        id="review",
        tool_name="",
        save=False,
        output_path="",
        external_action=action,
    )
    case.args["plan"] = replace(case.args["plan"], steps=(case.step, review))
    await case.service.authorize(identity, **case.args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "destination",
    [
        "192.168.1.2",
        "mqtts://printer",
        "https://sendcutsend.com",
        "test://other/printer",
    ],
)
async def test_real_and_unenrolled_destinations_rejected(case, destination):
    identity = case.service.enroll(**case.grant)
    action = dict(
        action_kind="printer_transfer",
        binding={"server": "cad", "tool": "cad_create", "schema": "d" * 64},
        destination={"kind": "printer", "id": destination},
        action={"kind": "printer_transfer"},
    )
    case.args["plan"] = replace(
        case.args["plan"], steps=(replace(case.step, external_action=action),)
    )
    with pytest.raises(WorkflowIntegrationPolicyError):
        await case.service.authorize(identity, **case.args)


@pytest.mark.parametrize(
    "destination",
    [
        "https://supplier.example",
        "test://user:password@campaign/path",
        "test://campaign/../real",
    ],
)
def test_enrollment_never_grants_real_destination(case, destination):
    with pytest.raises(WorkflowIntegrationPolicyError):
        case.service.enroll(**{**case.grant, "test_destinations": [destination]})


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["real_tool", "outside_receipt"])
async def test_test_uri_cannot_authorize_real_tool_or_unconfined_receipt(case, change):
    identity = case.service.enroll(**case.grant)
    action = dict(
        action_kind="printer_transfer",
        binding=TEST_HANDOFF_BINDING,
        destination={"kind": "test", "id": "test://campaign/printer"},
        settings={"receipt_path": "outputs/attempt-01/handoff.json"},
        action={"kind": "printer_transfer"},
    )
    if change == "real_tool":
        action["binding"] = {"server": "cad", "tool": "cad_create", "schema": "d" * 64}
    else:
        action["settings"] = {"receipt_path": "outside/handoff.json"}
    case.args["plan"] = replace(
        case.args["plan"], steps=(replace(case.step, external_action=action),)
    )
    with pytest.raises(WorkflowIntegrationPolicyError):
        await case.service.authorize(identity, **case.args)


def checkpoint(case, identity):
    subject = {
        "definition_digest": case.grant["source_digest"],
        "input_digests": list(case.grant["input_files"].values()),
        "artifact_digests": ["b" * 64],
        **{k: v for k, v in local_action().items() if k != "action_kind"},
    }
    return SimpleNamespace(
        subject=subject,
        subject_digest=approval_subject_digest(subject),
        workspace_id="workspace",
        action_kind="local_review",
        expires_at=None,
        continuation={
            "execution_context": {**case.grant, "integration_policy_digest": identity},
            "input_files": [
                {"path": p, "sha256": h} for p, h in case.grant["input_files"].items()
            ],
        },
    )


def test_auto_actor_is_derived_and_manual_never_auto_decides(case):
    identity = case.service.enroll(**case.grant)
    pending = checkpoint(case, identity)
    result = case.service.authorize_decision(
        identity,
        workspace_id="workspace",
        checkpoint=pending,
        expected_subject_digest=pending.subject_digest,
    )
    assert result["actor"] == "integration_test:campaign"
    manual = case.service.enroll(**{**case.grant, "approval_mode": "manual"})
    pending = checkpoint(case, manual)
    with pytest.raises(WorkflowIntegrationPolicyError, match="Manual"):
        case.service.authorize_decision(
            manual,
            workspace_id="workspace",
            checkpoint=pending,
            expected_subject_digest=pending.subject_digest,
        )


@pytest.mark.parametrize("change", ["dataset", "binding", "digest", "input", "expiry"])
def test_automatic_checkpoint_rejects_changed_authority(case, change):
    identity = case.service.enroll(**case.grant)
    pending = checkpoint(case, identity)
    if change == "dataset":
        pending.continuation["execution_context"]["dataset_digest"] = "f" * 64
    elif change == "binding":
        pending.subject["binding"] = {"server": "real-printer", "tool": "start"}
        pending.subject_digest = approval_subject_digest(pending.subject)
    elif change == "input":
        pending.continuation["input_files"][0]["sha256"] = "f" * 64
    elif change == "expiry":
        pending.expires_at = 1
    else:
        pending.subject_digest = "f" * 64
    with pytest.raises(WorkflowIntegrationPolicyError):
        case.service.authorize_decision(
            identity,
            workspace_id="workspace",
            checkpoint=pending,
            expected_subject_digest=pending.subject_digest,
        )


def test_unknown_revoked_and_expired_grants(case, monkeypatch):
    with pytest.raises(WorkflowIntegrationPolicyError):
        case.service.get("0" * 64)
    identity = case.service.enroll(**case.grant)
    case.service.revoke(identity)
    with pytest.raises(WorkflowIntegrationPolicyError, match="revoked"):
        case.service.get(identity)
    import time

    expiry = int(time.time()) + 10
    expiring = case.service.enroll(**{**case.grant, "expires_at": expiry})
    monkeypatch.setattr(
        "workspace_service.workflow_integration_policy.time.time", lambda: expiry
    )
    with pytest.raises(WorkflowIntegrationPolicyError, match="expired"):
        case.service.get(expiring)
