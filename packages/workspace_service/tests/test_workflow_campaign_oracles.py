from copy import deepcopy
import pytest
from workspace_service.workflow_campaign_oracles import (
    attach_oracles,
    verify_engineering_assertions,
)


def evidence():
    return {
        "steps": [
            {
                "task_id": "modify",
                "cad_document": {"documentId": "model"},
                "tool_calls": [
                    {
                        "tool": "server__cad.list_variables",
                        "status": "succeeded",
                        "arguments": {"documentId": "model"},
                        "result": {
                            "result": [
                                {
                                    "name": "Thickness",
                                    "value": {"decimalValue": 2.5, "unit": "mm"},
                                }
                            ]
                        },
                    }
                ],
            }
        ]
    }


RULE = {
    "kind": "cad_variable",
    "task_id": "modify",
    "name": "Thickness",
    "expected": 2.5,
    "unit": "mm",
    "tolerance": 0.001,
}


def test_dimensional_oracle_uses_recorded_provider_values():
    assert verify_engineering_assertions(evidence(), [RULE])[0]["actual"] == 2.5


@pytest.mark.parametrize(
    "fault",
    ["wrong_value", "wrong_unit", "wrong_model", "late_mutation", "narration_only"],
)
def test_dimensional_oracle_rejects_unproved_or_incompatible_measurements(fault):
    data = evidence()
    step = data["steps"][0]
    read = step["tool_calls"][0]
    if fault == "wrong_value":
        read["result"]["result"][0]["value"]["decimalValue"] = 3
    if fault == "wrong_unit":
        read["result"]["result"][0]["value"]["unit"] = "m"
    if fault == "wrong_model":
        read["arguments"]["documentId"] = "other"
    if fault == "late_mutation":
        step["tool_calls"].append(
            {"tool": "server__cad.set_variable", "status": "succeeded"}
        )
    if fault == "narration_only":
        step.update(tool_calls=[], response="Thickness is 2.5 mm; verified.")
    with pytest.raises(ValueError):
        verify_engineering_assertions(data, [RULE])


def test_source_changes_require_oracle_review():
    manifest = {"cases": [{"id": "case", "source_sha256": "original"}]}
    assert attach_oracles(
        deepcopy(manifest),
        {"case": {"source_sha256": "original", "assertions": [RULE]}},
    )["cases"][0]["engineering_assertions"] == [RULE]
    with pytest.raises(ValueError, match="Review"):
        attach_oracles(
            manifest, {"case": {"source_sha256": "changed", "assertions": [RULE]}}
        )


def test_resource_revision_assertion_requires_actual_adapter_evidence():
    data = {
        "steps": [
            {
                "task_id": "analysis",
                "input_resource": {"revision": "r1"},
                "engineering_result": {
                    "representations": [
                        {
                            "kind": "cloud_resource",
                            "provider_id": "cloud",
                            "resource_id": "analysis",
                            "revision": "r2",
                        }
                    ]
                },
            }
        ]
    }
    assertion = {"kind": "resource_revision", "task_id": "analysis", "changed": True}
    assert verify_engineering_assertions(data, [assertion])[0]["revisions"] == ["r2"]
    data["steps"][0]["engineering_result"]["representations"][0]["revision"] = None
    with pytest.raises(ValueError):
        verify_engineering_assertions(data, [assertion])


def analysis_evidence():
    read = {
        "tool": "fea__inspect",
        "status": "succeeded",
        "result": {
            "resource_id": "solve-1",
            "revision": "r2",
            "quantities": {"max_displacement": {"value": 0.25, "unit": "mm"}},
        },
    }
    return {
        "steps": [
            {
                "task_id": "solve",
                "resource_readback": read,
                "tool_calls": [read],
                "engineering_result": {
                    "kind": "analysis",
                    "representations": [
                        {
                            "kind": "cloud_resource",
                            "provider_id": "fea:solver",
                            "resource_id": "solve-1",
                            "revision": "r2",
                        }
                    ],
                },
            }
        ]
    }


ANALYSIS_RULE = {
    "kind": "analysis_quantity",
    "task_id": "solve",
    "tool": "fea__inspect",
    "provider_id": "fea:solver",
    "path": ["quantities", "max_displacement"],
    "expected": 0.25,
    "unit": "mm",
    "tolerance": 0.001,
}


def test_analysis_quantity_uses_provider_snapshot_and_revision():
    check = verify_engineering_assertions(analysis_evidence(), [ANALYSIS_RULE])[0]
    assert check["actual"] == 0.25 and check["revision"] == "r2"


@pytest.mark.parametrize(
    "fault",
    [
        "narration",
        "tool",
        "resource",
        "revision",
        "provider",
        "unit",
        "value",
        "boolean",
        "nan",
        "missing",
        "tolerance",
    ],
)
def test_analysis_quantity_rejects_unverified_measurement(fault):
    data = analysis_evidence()
    rule = deepcopy(ANALYSIS_RULE)
    step = data["steps"][0]
    read = step["resource_readback"]
    quantity = read["result"]["quantities"]["max_displacement"]
    if fault == "narration":
        step.update(tool_calls=[], response="Verified displacement 0.25 mm.")
    if fault == "tool":
        read["tool"] = "other"
    if fault == "resource":
        read["result"]["resource_id"] = "other"
    if fault == "revision":
        read["result"]["revision"] = "r1"
    if fault == "provider":
        rule["provider_id"] = "other"
    if fault == "unit":
        quantity["unit"] = "m"
    if fault == "value":
        quantity["value"] = 2.5
    if fault == "boolean":
        quantity["value"] = True
    if fault == "nan":
        quantity["value"] = float("nan")
    if fault == "missing":
        del read["result"]["quantities"]
    if fault == "tolerance":
        rule["tolerance"] = -1
    with pytest.raises(ValueError):
        verify_engineering_assertions(data, [rule])
