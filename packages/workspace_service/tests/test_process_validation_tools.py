import asyncio
import hashlib
import json

import pytest
from jsonschema import validate

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
)
from core.tools import ToolContext
from tool_registry.gateway_models import GatewayError, GatewaySessionContext
from workspace_service.process_validation.application import ValidationApplication
from workspace_service.process_validation.configuration import ProfileLocation
from workspace_service.process_validation.gateway import (
    ProcessValidationGatewayProvider,
)
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation_cli import main
from workspace_service.process_validation_tools import ProcessValidationTool


def args(length=100):
    profile = load_profile("structured-demo")
    value = {"part_id": "demo-plate", "length_mm": length}
    subject = SubjectBinding(
        id="imported-output",
        role="result",
        result_id="imported-output",
        producer=ProducerIdentity(
            run_id="invocation", step_id="import", attempt=1, output_port="result"
        ),
        kind="value",
        value=value,
        sha256=canonical_digest(value),
    )
    request = ValidationRequest(
        trace_id="trace",
        workspace_id="workspace",
        invocation_id="invocation",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="first",
    )
    return {
        "request": request.model_dump(mode="json"),
        "profile": {
            "source": "packaged",
            "name": "structured-demo",
            "reference": profile.reference().model_dump(),
        },
    }


def context(workspace="workspace"):
    return ToolContext(
        principal_id="local",
        workspace_id=workspace,
        trace_id="trace",
        request_id="tool-call",
    )


@pytest.mark.parametrize("length,passing", [(100, True), (98, False)])
def test_direct_tool_and_gateway_share_the_same_persisted_assessment(
    tmp_path, length, passing
):
    application = ValidationApplication(
        tmp_path / "state.db", "workspace", str(tmp_path)
    )
    arguments = args(length)
    request = ValidationRequest.model_validate(arguments["request"])
    direct = application.evaluate(
        request, ProfileLocation.model_validate(arguments["profile"])
    )
    tool = ProcessValidationTool(application)
    contract = tool.contract()
    result = asyncio.run(tool.execute(arguments, context=context()))
    validate(result, contract["output_schema"])
    assert result["assessment_id"] == direct.assessment.id
    assert result["release_eligible"] is passing
    provider = ProcessValidationGatewayProvider(application.repository.db_path)
    session = GatewaySessionContext(
        "session", "local", "workspace", str(tmp_path), "stdio"
    )
    projected = next(t for t in provider.tools(session) if t.tool_name == "evaluate")
    response = asyncio.run(
        provider.call(
            session,
            projected,
            arguments,
            request_id="call",
            approval_context={},
            progress_callback=None,
        )
    )
    assert response["isError"] is False  # A completed noncompliant check is data.
    assert response["structuredContent"] == result


def test_read_returns_actionable_findings_and_enforces_workspace(tmp_path):
    application = ValidationApplication(
        tmp_path / "state.db", "workspace", str(tmp_path)
    )
    result = asyncio.run(
        ProcessValidationTool(application).execute(args(98), context=context())
    )
    tool = ProcessValidationTool(application, "read")
    read = asyncio.run(
        tool.execute(
            {"assessment_id": result["assessment_id"], "limit": 1}, context=context()
        )
    )
    assert read["findings"][0]["observed"] == 98
    assert read["findings"][0]["expected"]["target"] == 100
    with pytest.raises(PermissionError):
        asyncio.run(
            tool.execute(
                {"assessment_id": result["assessment_id"]}, context=context("other")
            )
        )
    foreign = ProcessValidationTool(
        ValidationApplication(tmp_path / "state.db", "other", str(tmp_path)), "read"
    )
    with pytest.raises(KeyError):
        asyncio.run(
            foreign.execute(
                {"assessment_id": result["assessment_id"]}, context=context("other")
            )
        )


@pytest.mark.parametrize(
    "fault", ["workspace", "canonical", "invented_producer", "profile"]
)
def test_caller_cannot_forge_authority_or_modify_profile(tmp_path, fault):
    arguments = args()
    if fault == "workspace":
        arguments["request"]["workspace_id"] = "other"
    if fault == "canonical":
        arguments["request"].update(run_id="invocation", check_step_id="real-check")
    if fault == "invented_producer":
        arguments["request"]["subjects"][0]["producer"]["step_id"] = "real-producer"
    if fault == "profile":
        arguments["profile"]["reference"]["sha256"] = "b" * 64
    application = ValidationApplication(
        tmp_path / "state.db", "workspace", str(tmp_path)
    )
    with pytest.raises((ValueError, PermissionError)):
        asyncio.run(
            ProcessValidationTool(application).execute(arguments, context=context())
        )


def test_gateway_invalid_binding_is_a_tool_error(tmp_path):
    provider = ProcessValidationGatewayProvider(tmp_path / "state.db")
    session = GatewaySessionContext(
        "session", "local", "workspace", str(tmp_path), "stdio"
    )
    arguments = args()
    arguments["request"]["workspace_id"] = "outside"
    with pytest.raises(GatewayError):
        asyncio.run(
            provider.call(
                session,
                provider.tools(session)[0],
                arguments,
                request_id="call",
                approval_context={},
                progress_callback=None,
            )
        )


def test_packaged_cli_returns_a_measured_failure_and_can_read_it(tmp_path, capsys):
    (tmp_path / "request.json").write_text(
        json.dumps(args(98)["request"]), encoding="utf-8"
    )
    common = [
        "--workspace",
        str(tmp_path),
        "--workspace-id",
        "workspace",
        "--db",
        str(tmp_path / "state.db"),
    ]
    assert main(["evaluate", *common, "--request", "request.json"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert not result["release_eligible"]
    assert main(["read", *common, "--assessment", result["assessment_id"]]) == 0
    assert json.loads(capsys.readouterr().out)["findings"][0]["observed"] == 98
    assert main(["get", *common, "--assessment", result["assessment_id"]]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["assessment"]["id"] == result["assessment_id"]
    assert (
        main(
            [
                "export",
                *common,
                "--assessment",
                result["assessment_id"],
                "--format",
                "csv",
            ]
        )
        == 0
    )
    assert "requirement_id,requirement_text" in capsys.readouterr().out


def test_raw_inline_json_keeps_duplicate_fields_visible_to_the_reader(tmp_path):
    arguments = args()
    subject = arguments["request"]["subjects"][0]
    raw = '{"part_id":"demo-plate","length_mm":98,"length_mm":100}'
    subject.update(
        value=raw, encoding="raw-bytes", sha256=hashlib.sha256(raw.encode()).hexdigest()
    )
    application = ValidationApplication(
        tmp_path / "state.db", "workspace", str(tmp_path)
    )
    result = asyncio.run(
        ProcessValidationTool(application).execute(arguments, context=context())
    )
    assessment, _ = application.read(result["assessment_id"])
    assert not result["release_eligible"]
    assert any(f.code == "output.invalid_json" for f in assessment.findings)


def test_registered_output_cannot_be_replaced_or_relabelled_as_current(tmp_path):
    from data_vault.process_validation_repository import ValidationConflict

    application = ValidationApplication(
        tmp_path / "state.db", "workspace", str(tmp_path)
    )
    subject = SubjectBinding.model_validate(args()["request"]["subjects"][0])
    repository = application.repository
    repository.register_output("workspace", subject)
    assert repository.output_is_current("workspace", subject)
    assert not repository.output_is_current("other", subject)
    with pytest.raises(ValidationConflict):
        repository.register_output(
            "workspace", subject.model_copy(update={"id": "different"})
        )
    newer = subject.model_copy(
        update={
            "id": "new",
            "producer": subject.producer.model_copy(update={"attempt": 2}),
        }
    )
    repository.register_output("workspace", newer)
    assert not repository.output_is_current("workspace", subject)
    assert repository.output_is_current("workspace", newer)


def test_real_gateway_policy_dispatch_audit_and_output_schema(tmp_path):
    from types import SimpleNamespace
    from tool_registry.gateway_service import GatewayService
    from tool_registry.gateway_notifications import GatewayNotificationHub
    from tool_registry.gateway_resources import GatewayResourceProvider

    audit = []
    gateway = GatewayService(
        workspaces=SimpleNamespace(
            resolve_binding=lambda **kw: {**kw, "workspace_path": str(tmp_path)},
            enabled_server_ids=lambda session: set(),
        ),
        catalog=SimpleNamespace(
            servers=lambda: [], tools=lambda _: [], resources=lambda _: []
        ),
        lifecycle=SimpleNamespace(),
        audit=SimpleNamespace(record=audit.append),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        capability_providers=(ProcessValidationGatewayProvider(tmp_path / "state.db"),),
    )
    gateway.open_session(
        session_id="session",
        principal_id="local",
        workspace_id="workspace",
        transport="stdio",
    )
    gateway.initialize_session(
        "session",
        protocol_version="2025-11-25",
        client_name="test",
        client_version="1",
        client_capabilities={},
    )
    assert {t.name for t in gateway.list_tools("session")} == {
        "wright_validation__evaluate",
        "wright_validation__read",
        "wright_validation__get",
        "wright_validation__export",
    }
    result = asyncio.run(
        gateway.call_tool("session", "request", "wright_validation__evaluate", args(98))
    )
    assert not result.is_error and not result.structured_content["release_eligible"]
    read = asyncio.run(
        gateway.call_tool(
            "session",
            "read-request",
            "wright_validation__read",
            {"assessment_id": result.structured_content["assessment_id"]},
        )
    )
    assert (
        not read.is_error and read.structured_content["findings"][0]["observed"] == 98
    )
    report = asyncio.run(
        gateway.call_tool(
            "session",
            "get-request",
            "wright_validation__get",
            {"assessment_id": result.structured_content["assessment_id"]},
        )
    )
    assert report.structured_content["assessment"]["id"] == result.structured_content[
        "assessment_id"
    ]
    exported = asyncio.run(
        gateway.call_tool(
            "session",
            "export-request",
            "wright_validation__export",
            {
                "assessment_id": result.structured_content["assessment_id"],
                "format": "markdown",
            },
        )
    )
    assert exported.structured_content["content"].startswith(
        "# Process validation report"
    )
    assert any(item["server_id"] == "wright-process-validation" for item in audit)
