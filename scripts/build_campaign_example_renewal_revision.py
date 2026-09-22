"""Build the prospective R1 campaign revision ledger without dispatching work."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/082-output-content-validation"
JSON_DESTINATION = SPEC / "campaign-example-renewal-revision.json"
MARKDOWN_DESTINATION = SPEC / "campaign-example-renewal-revision.md"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _renewal_module():
    path = ROOT / "scripts/campaign_example_renewal.py"
    spec = importlib.util.spec_from_file_location("campaign_example_renewal", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[bytes, bytes]:
    renewal = _renewal_module()
    lineup, _, decision = renewal.approved_documents()
    coverage_document = json.loads(
        (
            ROOT
            / "packages/workspace_service/src/workspace_service/process_validation/"
            "profiles/coverage.json"
        ).read_text(encoding="utf-8")
    )
    coverage = {item["scenario_id"]: item for item in coverage_document["scenarios"]}
    cases = []
    for path in sorted(
        (ROOT / "tests/datasets/engineering-workflows/scenarios").glob("*/*/scenario.json")
    ):
        raw = path.read_bytes()
        manifest = json.loads(raw)
        scenario_id = manifest["scenario_id"]
        contract = renewal.case_contract(manifest)
        support = coverage[scenario_id]
        profile = support.get("full_profile") or support["profile"]
        cases.append(
            {
                "scenario_id": scenario_id,
                "family": manifest["template_id"],
                "historical_identity": {
                    "scenario_manifest": path.relative_to(ROOT).as_posix(),
                    "scenario_manifest_sha256": _digest(raw),
                    "semantic_manifest_sha256": contract["scenario"][
                        "original_manifest_sha256"
                    ],
                    "preservation": "unchanged_history; prospective attempts only",
                },
                "prospective_identity": {
                    "campaign_revision_id": lineup["proposal_id"],
                    "contract_sha256": _digest(renewal.contract_bytes(manifest)),
                    "profile_resource": profile["profile_resource"],
                    "profile_ref": profile["profile_ref"],
                    "baseline_ref": profile["baseline_ref"],
                    "expected_output_roles": [
                        item["role"] for item in renewal.expected_outputs(manifest)
                    ],
                },
                "mapping": "same engineering subject; revised prospective process",
            }
        )
    if len(cases) != 30 or len({item["scenario_id"] for item in cases}) != 30:
        raise ValueError("Renewal revision must map exactly 30 unique scenarios")
    document = {
        "schema": "wright.campaign-example-renewal-revision/1",
        "revision_id": lineup["proposal_id"],
        "decision_id": decision["decision_id"],
        "decision_sha256": _digest(renewal.DECISION.read_bytes()),
        "lineup_sha256": _digest(renewal.LINEUP.read_bytes()),
        "engineering_inputs_sha256": _digest(renewal.ENGINEERING_INPUTS.read_bytes()),
        "status": "prospective_prepared_not_dispatched",
        "history_policy": {
            "prior_attempts_mutated": False,
            "prior_approvals_reused": False,
            "retry_budgets_reset": False,
            "campaign_credit_carried_forward": False,
        },
        "cases": cases,
    }
    json_bytes = (json.dumps(document, indent=2) + "\n").encode()
    lines = [
        "# Campaign example renewal revision",
        "",
        f"Revision: `{document['revision_id']}`. State: prepared, not dispatched.",
        "",
        "This ledger maps the 30 historical scenario identities to the approved R1",
        "prospective contracts and exact validator references. It does not edit an old",
        "attempt, reuse an approval, reset a retry budget, or award campaign credit.",
        "",
        "| Scenario | Historical manifest | Prospective profile | Output roles |",
        "| --- | --- | --- | --- |",
    ]
    for item in cases:
        old = item["historical_identity"]
        new = item["prospective_identity"]
        lines.append(
            f"| {item['scenario_id']} | `{old['scenario_manifest_sha256'][:12]}` | "
            f"`{new['profile_ref']['sha256'][:12]}` | "
            f"{', '.join(new['expected_output_roles'])} |"
        )
    return json_bytes, ("\n".join(lines) + "\n").encode()


def main() -> None:
    json_bytes, markdown_bytes = render()
    JSON_DESTINATION.write_bytes(json_bytes)
    MARKDOWN_DESTINATION.write_bytes(markdown_bytes)
    print("Wrote prospective renewal revision for 30 scenarios; dispatched 0")


if __name__ == "__main__":
    main()
