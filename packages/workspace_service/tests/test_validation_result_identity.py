"""Long canonical addresses retain exact result linkage in validator storage."""
import hashlib
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from core.process_validation import ProducerIdentity, SubjectBinding
from workspace_service.process_validation.process import register_outputs
from workspace_service.workflow_results import EngineeringResult, Provenance, Representation


@pytest.mark.parametrize("with_result", [False, True])
@pytest.mark.parametrize("native_file", [False, True])
def test_long_valid_producer_components_register_without_changing_result_id(with_result, native_file):
    run, task, port = "r" * 160, "t" * 160, "p" * 160
    result_id = f"{run}:{task}:{port}"
    payload = "exact native result"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    stored = []
    app = SimpleNamespace(workspace_id="workspace", repository=SimpleNamespace(register_output=lambda workspace, subject: stored.append(subject)))
    step = SimpleNamespace(id=task, title="Long native task", output_ports=((port, "workspace_file" if native_file else "engineering_document"),), output_format="text")
    receipt = {"output_port":port,"output_path":"outputs/native.txt","sha256":digest,"output_format":"txt"}
    representation = Representation("workspace_file", "outputs/native.txt", "txt", sha256=digest) if native_file else Representation("value", "steps/response", "text", sha256=digest)
    result = EngineeringResult(result_id, "file" if native_file else "text", "Native output", (representation,), Provenance(run, task, port))
    register_outputs(app, step, {"producer_attempt":1}, run, {f"{task}.{port}":payload}, {f"{task}.{port}":[receipt]} if native_file else {}, [result] if with_result else [])
    assert len(stored) == 1
    assert stored[0].result_id == result_id
    assert stored[0].sha256 == digest
    assert stored[0].producer == ProducerIdentity(run_id=run, step_id=task, output_port=port, attempt=1)
    assert SubjectBinding.model_validate_json(stored[0].model_dump_json()) == stored[0]


def test_result_reference_still_bounded_and_producer_components_still_limited():
    values = dict(id="output",role="output",result_id="x" * 483,producer=ProducerIdentity(run_id="r",step_id="s",output_port="p",attempt=1),kind="value",value="value",sha256=hashlib.sha256(b"value").hexdigest(),encoding="raw-bytes")
    with pytest.raises(ValidationError, match="482"):
        SubjectBinding(**values)
    with pytest.raises(ValidationError, match="160"):
        ProducerIdentity(run_id="r",step_id="s"*161,output_port="p",attempt=1)
