import json
from datetime import UTC, datetime, timedelta
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from tool_registry.capability_models import (
    CapabilityDiagnostic,
    CatalogSnapshot,
    CredentialRequirement,
    ImportedMcpDraft,
    InstallPlan,
    InstallPlanRequirements,
    InstallPlanStep,
    LicenseRequirement,
    MachineCompatibilityObservation,
    ValidationEvidence,
)


def now() -> datetime:
    return datetime(2026, 8, 12, tzinfo=UTC)


def test_packaged_contract_schemas_and_public_only_trust_root_are_valid():
    catalog = files("tool_registry.catalog")
    for name in (
        "catalog-snapshot-envelope.schema.json",
        "import-preview.schema.json",
        "install-plan.schema.json",
    ):
        document = json.loads(catalog.joinpath(name).read_text("utf-8"))
        Draft202012Validator.check_schema(document)
    root = json.loads(catalog.joinpath("trust-root.json").read_text("utf-8"))
    assert root == {"root_version": 1, "channels": {}}
    assert "private" not in json.dumps(root).lower()


def test_snapshot_requires_timezone_ordered_expiry_and_canonical_digest():
    snapshot = CatalogSnapshot(
        snapshot_id="snapshot",
        channel="bundled",
        sequence=1,
        schema_version=1,
        issued_at=now(),
        expires_at=now() + timedelta(days=30),
        payload_sha256="a" * 64,
        payload_json={"format_version": 1, "servers": []},
        envelope_json=None,
        signer_key_id=None,
        signature=None,
        verification_state="bundled",
    )
    assert snapshot.verification_state == "bundled"
    with pytest.raises(ValidationError, match="expires_at"):
        snapshot.model_copy(
            update={"expires_at": now() - timedelta(seconds=1)}
        ).model_validate(
            snapshot.model_copy(
                update={"expires_at": now() - timedelta(seconds=1)}
            ).model_dump()
        )


def test_imported_draft_rejects_secret_values_and_keeps_requirements_only():
    draft = ImportedMcpDraft(
        draft_id="draft",
        name="Safe",
        source_format="claude_mcp_servers",
        transport="stdio",
        command="uvx",
        arguments=["safe-mcp"],
        environment_requirements=[
            CredentialRequirement(
                name="API_TOKEN", credential_required=True, value_supplied=True
            )
        ],
        redacted_preview={"env": {"API_TOKEN": "<credential required>"}},
        draft_digest="b" * 64,
    )
    assert "secret-value" not in draft.model_dump_json()
    with pytest.raises(ValidationError, match="secret-like"):
        ImportedMcpDraft(**{**draft.model_dump(), "raw_secret": "secret-value"})


def test_install_plan_blocks_external_license_and_rejects_secret_fields():
    plan = InstallPlan(
        plan_id="plan",
        state="blocked",
        capability_id="capability",
        snapshot_id="snapshot",
        capability_digest="c" * 64,
        machine_observation_id="observation",
        machine_observation_digest="d" * 64,
        backend_kind="remote_endpoint",
        requested_scope="global_registered",
        requirements=InstallPlanRequirements(
            license=LicenseRequirement(
                state="external_acceptance_required",
                reference="https://example.com/terms",
                independent_completion_required=True,
            )
        ),
        steps=[
            InstallPlanStep(
                step_id="register",
                kind="register_endpoint",
                description="Register",
                reversible=True,
            )
        ],
        blocking_reasons=[
            CapabilityDiagnostic(
                code="external_license_acceptance_required",
                message="Complete the external terms independently.",
                recovery="Return after completing the vendor step.",
            )
        ],
        created_by="engineer",
        created_at=now(),
        expires_at=now() + timedelta(minutes=10),
        plan_digest="e" * 64,
    )
    assert plan.state == "blocked"
    with pytest.raises(ValidationError, match="raw secret"):
        InstallPlan(**{**plan.model_dump(), "api_token": "secret-value"})


def test_observation_and_validation_evidence_require_digest_and_honest_pass():
    observation = MachineCompatibilityObservation(
        observation_id="observation",
        observed_at=now(),
        expires_at=now() + timedelta(minutes=5),
        platform_key="windows_11_x64",
        os_name="Windows",
        os_version="11",
        architecture="amd64",
        distribution_mode="test",
        digest="f" * 64,
    )
    assert observation.digest == "f" * 64
    with pytest.raises(ValidationError, match="required protocol steps"):
        ValidationEvidence(
            evidence_id="evidence",
            capability_id="capability",
            server_id="server",
            snapshot_id="snapshot",
            capability_digest="1" * 64,
            observation_id="observation",
            platform_key="windows_11_x64",
            architecture="amd64",
            state="passed",
            protocol_steps={"initialize": "passed"},
            observed_at=now(),
        )
