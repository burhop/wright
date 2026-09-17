"""Preflight recognizes the exact receipt bound to an external action."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "engineering_preflight",
    ROOT / "scripts/audit-engineering-batch-preflight.py",
)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def task(settings):
    return {"fields": {"settings": settings}}


def test_external_action_receipt_is_a_static_declared_output():
    settings = {
        "authoring_template": "external-action-approval",
        "approval_settings": {
            "receipt_path": "campaign/case/attempt/artifacts/transfer-receipt.json"
        },
    }

    declared, expected_files = preflight.declared_paths_for_task(task(settings))

    assert expected_files == []
    assert declared == [
        "campaign/case/attempt/artifacts/transfer-receipt.json"
    ]


def test_json_encoded_approval_settings_preserve_the_same_receipt_contract():
    settings = {
        "authoring_template": "external-action-approval",
        "approval_settings": json.dumps(
            {"receipt_path": "campaign/case/attempt/artifacts/receipt.json"}
        ),
        "expected_files": "campaign/case/attempt/artifacts/package.3mf",
    }

    declared, expected_files = preflight.declared_paths_for_task(task(settings))

    assert expected_files == ["campaign/case/attempt/artifacts/package.3mf"]
    assert declared == [
        "campaign/case/attempt/artifacts/package.3mf",
        "campaign/case/attempt/artifacts/receipt.json",
    ]


def test_json_encoded_cad_contract_declares_native_and_export_outputs():
    settings = {
        "cad": json.dumps(
            {
                "source": "new",
                "native_path": "campaign/case/attempt/artifacts/part.psm",
                "save_native": True,
                "exports": [
                    {
                        "format": "step",
                        "path": "campaign/case/attempt/artifacts/part.step",
                    },
                    {
                        "format": "flat_dxf",
                        "path": "campaign/case/attempt/artifacts/part.dxf",
                    },
                ],
            }
        )
    }

    declared, expected_files = preflight.declared_paths_for_task(task(settings))

    assert expected_files == [
        "campaign/case/attempt/artifacts/part.psm",
        "campaign/case/attempt/artifacts/part.step",
        "campaign/case/attempt/artifacts/part.dxf",
    ]
    assert declared == expected_files


def test_validator_binding_must_match_the_declared_full_campaign_scope():
    profile_ref = {"id": "profile", "version": "1", "sha256": "a" * 64}
    baseline_ref = {"id": "baseline", "version": "1", "sha256": "b" * 64}
    support = {
        "profile": {
            "profile_resource": "profile-resource",
            "profile_ref": profile_ref,
            "baseline_ref": baseline_ref,
        },
        "campaign_credit": {
            "full_scope": True,
            "requirement_ids": ["REQ-1"],
            "subject_roles": ["basis", "result"],
        },
    }
    settings = {
        "validation": {
            "profile": {
                "source": "packaged",
                "name": "profile-resource",
                "reference": profile_ref,
            },
            "baseline": baseline_ref,
            "subjects": {"basis": "validate_basis", "result": "validate_result"},
        }
    }

    assert preflight.validation_contract_errors(settings, support) == []

    settings["validation"]["subjects"]["unreviewed"] = "validate_unreviewed"
    assert preflight.validation_contract_errors(settings, support) == [
        {
            "code": "validator_subject_scope_mismatch",
            "missing_roles": [],
            "extra_roles": ["unreviewed"],
        }
    ]


def test_validator_binding_rejects_bounded_or_unpinned_credit():
    settings = {"validation": {"profile": {}, "baseline": {}, "subjects": {}}}
    support = {
        "profile": {},
        "campaign_credit": {"full_scope": False},
    }

    assert {
        error["code"]
        for error in preflight.validation_contract_errors(settings, support)
    } == {
        "campaign_full_scope_not_declared",
        "campaign_profile_not_declared",
        "validator_baseline_not_current_full_scope",
        "validator_subject_scope_mismatch",
    }
