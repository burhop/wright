"""Real nested provider measurements keep their exact outer artifact identity."""

import hashlib
import json

import pytest

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationProfile,
    ValidationRequest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


def evaluate(tmp_path, _, *, profile, file_bytes):
    (tmp_path / "provider.json").write_bytes(file_bytes)
    subject = SubjectBinding(
        id="measurement",
        role="result",
        kind="file",
        format="json",
        locator="provider.json",
        encoding="raw-bytes",
        sha256=hashlib.sha256(file_bytes).hexdigest(),
        result_id="run:measure:result",
        producer=ProducerIdentity(
            run_id="run", step_id="measure", attempt=1, output_port="result"
        ),
    )
    request = ValidationRequest(
        trace_id="json-container",
        workspace_id="workspace",
        invocation_id="check",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="json-container",
    )
    service = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "validation.sqlite3"),
        SubjectResolver("workspace", str(tmp_path)),
    )
    return service.evaluate(request, profile), service, request


def profile(pointer="/content/0/text"):
    raw = load_profile("structured-demo").model_dump()
    raw["id"] = "json-container-observation"
    raw["baseline"]["requirements"] = raw["baseline"]["requirements"][:1]
    raw["checks"] = raw["checks"][:1]
    raw["checks"][0].update(
        reader="structured-json-container",
        parameters={"json_container_pointer": pointer},
    )
    return ValidationProfile.model_validate(raw)


def envelope(inner):
    return json.dumps({"content": [{"type": "text", "text": inner}]}).encode()


def test_actual_measurement_is_not_replaced_by_provider_pass_flag(tmp_path):
    raw = envelope('{"length_mm":98,"status":"pass"}')
    outcome, _, _ = evaluate(tmp_path, None, profile=profile(), file_bytes=raw)
    assert not outcome.release_eligible
    finding = outcome.assessment.findings[0]
    assert finding.observed == 98 and finding.state == "fail"
    measurement = outcome.assessment.measurements[0]
    assert measurement.subject_sha256 == hashlib.sha256(raw).hexdigest()
    assert "#/content/0/text::json#/length_mm" in measurement.evidence_refs[0]
    assert measurement.reader.id == "structured-json-container"


def test_corrected_exact_artifact_passes_with_its_own_identity(tmp_path):
    raw = envelope('{"length_mm":100}')
    outcome, _, _ = evaluate(tmp_path, None, profile=profile(), file_bytes=raw)
    assert outcome.release_eligible
    assert (
        outcome.assessment.measurements[0].subject_sha256
        == hashlib.sha256(raw).hexdigest()
    )


@pytest.mark.parametrize(
    "inner",
    [
        '{"length_mm":98,"length_mm":100}',
        '{"length_mm":NaN}',
        '{"length_mm":Infinity}',
        "not JSON",
        '{"length_mm":100} trailing',
    ],
)
def test_ambiguous_or_nonfinite_inner_json_is_rejected(tmp_path, inner):
    outcome, _, _ = evaluate(
        tmp_path, None, profile=profile(), file_bytes=envelope(inner)
    )
    assert not outcome.release_eligible
    assert outcome.assessment.findings[0].code == "output.invalid_json"


@pytest.mark.parametrize("pointer", [None, 3, "", "content/0/text", "/content/~2/text"])
def test_invalid_container_configuration_cannot_release(tmp_path, pointer):
    outcome, _, _ = evaluate(
        tmp_path,
        None,
        profile=profile(pointer),
        file_bytes=envelope('{"length_mm":100}'),
    )
    assert not outcome.release_eligible


def test_missing_container_does_not_scan_other_messages(tmp_path):
    raw = json.dumps({"other": '{"length_mm":100}'}).encode()
    outcome, _, _ = evaluate(tmp_path, None, profile=profile(), file_bytes=raw)
    assert not outcome.release_eligible
    assert outcome.assessment.findings[0].code == "output.required_value_missing"


def test_object_container_is_rejected_instead_of_implicitly_reinterpreted(tmp_path):
    raw = json.dumps({"content": [{"text": {"length_mm": 100}}]}).encode()
    outcome, _, _ = evaluate(tmp_path, None, profile=profile(), file_bytes=raw)
    assert not outcome.release_eligible
    assert outcome.assessment.findings[0].code == "output.json_container_type"
