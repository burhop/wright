"""Qualify existing Wright validation on exact numerical research output bytes.

No production profile registration, review, gateway operation or new evaluator.
"""

import argparse
import hashlib
import json
from pathlib import Path
from core.process_validation import (
    ValidationProfile,
    ProducerIdentity,
    SubjectBinding,
    ValidationRequest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--basis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    basis = json.loads(args.basis.read_text(encoding="utf-8"))
    digest = hashlib.sha256(args.basis.read_bytes()).hexdigest()
    profile = ValidationProfile.model_validate(
        {
            "id": basis["id"],
            "version": basis["version"],
            "baseline": {
                "id": basis["id"] + "-basis",
                "version": "1",
                "requirements": [
                    {
                        "id": c["id"],
                        "text": "Synthetic numerical control: " + c["id"],
                        "scope": "content",
                        "sources": [
                            {
                                "artifact_ref": "examples/reverse-engineering-workflow/projection-qualification-basis.json",
                                "sha256": digest,
                                "locator": "checks/" + str(i),
                            }
                        ],
                    }
                    for i, c in enumerate(basis["checks"])
                ],
            },
            "checks": [
                {
                    "id": c["id"],
                    "requirement_ids": [c["id"]],
                    "subject_role": "result",
                    "reader": "structured",
                    "selector": c["selector"],
                    "constraint": c["constraint"],
                    "unit": c["unit"],
                    "evidence_method": "structured_value",
                }
                for c in basis["checks"]
            ],
            "limitations": [
                basis["scope"],
                "Validates recorded numeric controls, not their independent physical truth.",
            ],
            "supported_kinds": ["file"],
        }
    )

    def write(name, value):
        (args.output / name).write_text(
            json.dumps(value, indent=2, allow_nan=False), encoding="utf-8"
        )

    write("profile.json", profile.model_dump(mode="json"))
    raw = args.report.read_bytes()
    (args.output / "result.json").write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    subject = SubjectBinding(
        id="projection-result",
        role="result",
        kind="file",
        format="json",
        locator="result.json",
        encoding="raw-bytes",
        sha256=sha,
        result_id="local-projection-01:measurement:report",
        producer=ProducerIdentity(
            run_id="local-projection-01",
            step_id="measurement",
            attempt=1,
            output_port="report",
        ),
    )
    service = ProcessValidationService(
        ProcessValidationRepository(args.output / "validation.sqlite3"),
        SubjectResolver("re-method-qualification", str(args.output.resolve())),
    )

    def evaluate(key):
        request = ValidationRequest(
            trace_id=key,
            workspace_id="re-method-qualification",
            invocation_id=key,
            subjects=(subject,),
            profile_ref=profile.reference(),
            baseline_ref=profile.baseline.reference(),
            idempotency_key=key,
        )
        result = service.evaluate(request, profile)
        write(
            key + ".json",
            {
                "attempt": result.attempt.state,
                "is_current": result.is_current,
                "assessment": result.assessment.model_dump(mode="json")
                if result.assessment
                else None,
            },
        )
        return result

    nominal = evaluate("exact-report")
    # Disposable local copy only. The actual geometry/report remains untouched.
    (args.output / "result.json").write_bytes(raw + b"\n")
    changed = evaluate("changed-bytes")
    current = service.get_result(nominal.assessment.id).currentness.is_current
    write(
        "summary.json",
        {
            "exact_report_checks_pass": nominal.release_eligible,
            "changed_bytes_rejected": not changed.release_eligible,
            "old_assessment_stale_after_change": not current,
            "original_report_sha256": sha,
            "original_unchanged": hashlib.sha256(args.report.read_bytes()).hexdigest()
            == sha,
            "scope": basis["scope"],
            "profile_reference": profile.reference().model_dump(mode="json"),
        },
    )
    assert nominal.release_eligible and not changed.release_eligible and not current
    print(
        json.dumps(
            {
                "status": "pass",
                "numeric_checks": len(profile.checks),
                "changed_bytes_rejected": True,
                "stale_assessment_rejected": True,
            }
        )
    )


if __name__ == "__main__":
    main()
