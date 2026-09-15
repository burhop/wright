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
