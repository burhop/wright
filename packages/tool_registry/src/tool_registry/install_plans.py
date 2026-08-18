from __future__ import annotations

import hashlib
import json
import sqlite3
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .capability_models import (
    CapabilityDiagnostic,
    InstallPlan,
    InstallPlanRequirements,
    InstallPlanStep,
    LicenseRequirement,
    MachineCompatibilityObservation,
)
from .catalog_models import CatalogEntry
from .catalog_signing import canonical_json
from .compatibility import evaluate_compatibility

PLAN_TTL = timedelta(minutes=30)


class InstallPlanError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _reason(code: str, message: str, recovery: str) -> CapabilityDiagnostic:
    return CapabilityDiagnostic(code=code, message=message, recovery=recovery)


def _step(
    step_id: str,
    kind: str,
    description: str,
    *,
    target: str | None = None,
    reversible: bool = True,
    rollback_step_id: str | None = None,
) -> InstallPlanStep:
    return InstallPlanStep(
        step_id=step_id,
        kind=kind,
        description=description,
        target=target,
        reversible=reversible,
        rollback_step_id=rollback_step_id,
    )


def _license_requirement(
    entry: CatalogEntry | None,
    *,
    independently_completed: bool,
    now: datetime,
) -> tuple[LicenseRequirement, list[CapabilityDiagnostic]]:
    if entry is None:
        return LicenseRequirement(state="unknown"), [
            _reason(
                "license_unknown",
                "The imported configuration does not declare license terms.",
                "Review the publisher terms independently before applying.",
            )
        ]
    if not entry.license:
        requirement = LicenseRequirement(
            state="unknown",
            independent_completion_required=True,
            independent_completion_recorded_at=now if independently_completed else None,
        )
        blockers = (
            []
            if independently_completed
            else [
                _reason(
                    "license_unknown",
                    "The catalog does not identify a license.",
                    "Verify the source and license, then record that review before applying.",
                )
            ]
        )
        return requirement, blockers
    external = any(
        marker in entry.license.casefold()
        for marker in ("terms", "subscription", "app store", "independently")
    )
    if external:
        requirement = LicenseRequirement(
            state="external_acceptance_required",
            reference=entry.license,
            independent_completion_required=True,
            independent_completion_recorded_at=now if independently_completed else None,
        )
        blockers = (
            []
            if independently_completed
            else [
                _reason(
                    "external_license_incomplete",
                    "Publisher terms or a subscription must be completed outside Wright.",
                    "Complete the publisher flow independently, then record completion and create a new plan.",
                )
            ]
        )
        return requirement, blockers
    return LicenseRequirement(state="known", reference=entry.license), []


def _backend_for_entry(entry: CatalogEntry) -> str:
    if entry.host_software_required or entry.install_method == "desktop-extension":
        return "host_bridge"
    if entry.locality == "remote" or entry.transport in {
        "streamable_http",
        "sse",
        "webmcp",
    }:
        return "remote_endpoint"
    if entry.install_method in {"uvx", "pip", "npm", "docker", "packaged-binary"}:
        return "local_package"
    return "local_command"


def _backend_steps(backend: str, target: str) -> tuple[list, list, list, list]:
    validate = [
        _step(
            "validate-protocol",
            "mcp_protocol",
            "Initialize MCP and list tools.",
            reversible=False,
        )
    ]
    if backend == "local_package":
        effects = [
            _step(
                "effect-env",
                "create_isolated_environment",
                "Create an isolated MCP environment.",
                target=target,
                rollback_step_id="rollback-env",
            ),
            _step(
                "effect-download",
                "download",
                "Acquire the pinned reviewed package.",
                target=target,
                rollback_step_id="rollback-env",
            ),
            _step(
                "effect-register",
                "write_config",
                "Register the exact local launch recipe.",
                target=target,
                rollback_step_id="rollback-config",
            ),
        ]
        steps = [
            _step(
                "prepare",
                "prepare",
                "Prepare the isolated target.",
                target=target,
                rollback_step_id="rollback-env",
            ),
            _step(
                "apply",
                "install",
                "Install the pinned reviewed package.",
                target=target,
                rollback_step_id="rollback-env",
            ),
            _step(
                "register",
                "register",
                "Register without enabling a workspace.",
                target=target,
                rollback_step_id="rollback-config",
            ),
        ]
        rollback = [
            _step(
                "rollback-config",
                "remove",
                "Remove the generated registration.",
                target=target,
            ),
            _step(
                "rollback-env",
                "remove",
                "Remove the isolated environment.",
                target=target,
            ),
        ]
    elif backend == "remote_endpoint":
        effects = [
            _step(
                "effect-register",
                "register_endpoint",
                "Register the reviewed endpoint locally.",
                target=target,
                rollback_step_id="rollback-registration",
            )
        ]
        steps = [
            _step(
                "prepare",
                "prepare",
                "Validate the endpoint form without contacting it.",
                target=target,
                rollback_step_id="rollback-registration",
            ),
            _step(
                "apply",
                "register",
                "Register the endpoint without connecting.",
                target=target,
                rollback_step_id="rollback-registration",
            ),
        ]
        rollback = [
            _step(
                "rollback-registration",
                "remove",
                "Remove the endpoint registration.",
                target=target,
            )
        ]
    elif backend == "host_bridge":
        effects = [
            _step(
                "effect-requirements",
                "record_requirements",
                "Record the required engineering application; do not install or start it.",
                target=target,
            ),
            _step(
                "effect-register",
                "write_config",
                "Register the host bridge locally.",
                target=target,
                rollback_step_id="rollback-registration",
            ),
        ]
        steps = [
            _step(
                "prepare",
                "review_requirements",
                "Review the engineering application and bridge requirements.",
                target=target,
            ),
            _step(
                "apply",
                "register",
                "Register the MCP server without starting the engineering application.",
                target=target,
                rollback_step_id="rollback-registration",
            ),
        ]
        rollback = [
            _step(
                "rollback-registration",
                "remove",
                "Remove only Wright's MCP server registration.",
                target=target,
            )
        ]
    else:
        effects = [
            _step(
                "effect-register",
                "write_config",
                "Register the reviewed literal command.",
                target=target,
                rollback_step_id="rollback-registration",
            )
        ]
        steps = [
            _step(
                "prepare",
                "review_command",
                "Recheck the exact literal command and arguments.",
                target=target,
            ),
            _step(
                "apply",
                "register",
                "Register the command without starting it.",
                target=target,
                rollback_step_id="rollback-registration",
            ),
        ]
        rollback = [
            _step(
                "rollback-registration",
                "remove",
                "Remove the local command registration.",
                target=target,
            )
        ]
    return effects, steps, validate, rollback


def plan_digest(plan: InstallPlan | dict[str, Any]) -> str:
    value = (
        plan.model_dump(mode="json")
        if isinstance(plan, InstallPlan)
        else deepcopy(plan)
    )
    for key in ("plan_digest", "state", "approved_by", "approved_at"):
        value.pop(key, None)
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _persist(database_path: str | Path, plan: InstallPlan) -> None:
    payload = plan.model_dump(mode="json")
    with sqlite3.connect(str(database_path)) as connection:
        connection.execute(
            """INSERT INTO mcp_install_plans (
                plan_id, plan_digest, state, capability_id, snapshot_id,
                observation_id, requested_scope, workspace_id, created_by,
                created_at, expires_at, approved_by, approved_at, plan_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_id) DO UPDATE SET
                plan_digest=excluded.plan_digest, state=excluded.state,
                approved_by=excluded.approved_by, approved_at=excluded.approved_at,
                plan_json=excluded.plan_json""",
            (
                plan.plan_id,
                plan.plan_digest,
                plan.state,
                plan.capability_id,
                plan.snapshot_id,
                plan.machine_observation_id,
                plan.requested_scope,
                plan.workspace_id,
                plan.created_by,
                int(plan.created_at.timestamp()),
                int(plan.expires_at.timestamp()),
                plan.approved_by,
                int(plan.approved_at.timestamp()) if plan.approved_at else None,
                json.dumps(payload, sort_keys=True),
            ),
        )


def create_install_plan(
    database_path: str | Path,
    *,
    snapshot_id: str,
    observation: MachineCompatibilityObservation,
    actor: str,
    requested_scope: str,
    workspace_id: str | None = None,
    entry: CatalogEntry | None = None,
    import_draft: dict[str, Any] | None = None,
    independently_completed_license: bool = False,
    now: datetime | None = None,
) -> InstallPlan:
    if (entry is None) == (import_draft is None):
        raise InstallPlanError(
            "install_plan_source_invalid",
            "Choose exactly one plan source.",
            status_code=422,
        )
    if requested_scope not in {"global_registered", "workspace"}:
        raise InstallPlanError(
            "install_plan_scope_invalid", "Requested scope is invalid.", status_code=422
        )
    if requested_scope == "workspace" and not workspace_id:
        raise InstallPlanError(
            "install_plan_workspace_required",
            "Workspace scope requires a workspace id.",
            status_code=422,
        )
    now = (now or datetime.now(UTC)).astimezone(UTC)
    blockers: list[CapabilityDiagnostic] = []
    license_requirement, license_blockers = _license_requirement(
        entry, independently_completed=independently_completed_license, now=now
    )
    blockers.extend(license_blockers)

    if entry is not None:
        backend = _backend_for_entry(entry)
        capability_id = entry.id
        capability_material = entry.model_dump(mode="json")
        capability_digest = hashlib.sha256(
            canonical_json(capability_material)
        ).hexdigest()
        source = {
            "source_url": entry.source_url,
            "repository_url": entry.repository_url,
            "package_url": entry.package_url,
            "container_url": entry.container_url,
            "install_method": entry.install_method,
            "transport": entry.transport,
            "command": entry.command,
        }
        compatibility = evaluate_compatibility(entry, observation)
        if compatibility.status in {"incompatible", "blocked"}:
            blockers.extend(
                _reason(reason.code, reason.message, reason.recovery)
                for reason in compatibility.reasons
            )
        credentials = sorted(entry.credentials_required)
        runtimes = sorted(
            set(entry.dependencies.python)
            | set(entry.dependencies.node)
            | (
                {entry.install_method}
                if entry.install_method in {"uvx", "pip", "npm", "docker"}
                else set()
            )
        )
        platforms = sorted(
            key for key, value in entry.platform_support.items() if value.status != "no"
        )
        hosts = sorted(entry.host_software_required)
        approval_gates = sorted(set(entry.approval_gates))
        target = entry.id
        import_id = None
        import_digest = None
        if entry.installability_tier in {"blocked", "non_working"}:
            blockers.append(
                _reason(
                    "catalog_onboarding_blocked",
                    entry.install_blocked_reason or "Catalog onboarding is blocked.",
                    "Choose a supported alternative or wait for reviewed evidence.",
                )
            )
    else:
        assert import_draft is not None
        if import_draft.get("errors"):
            blockers.append(
                _reason(
                    "import_draft_invalid",
                    "The imported server has validation errors.",
                    "Correct the configuration and create a new import preview.",
                )
            )
        backend = "remote_endpoint" if import_draft.get("endpoint") else "local_command"
        import_id = str(import_draft["draft_id"])
        import_digest = str(import_draft["draft_digest"])
        capability_id = f"import:{import_id}"
        capability_digest = import_digest
        source = {
            "name": import_draft.get("name"),
            "transport": import_draft.get("transport"),
            "command": import_draft.get("command"),
            "arguments": import_draft.get("arguments", []),
            "endpoint": import_draft.get("endpoint"),
        }
        credentials = sorted(
            item["name"]
            for group in ("environment_requirements", "header_requirements")
            for item in import_draft.get(group, [])
            if item.get("credential_required")
        )
        runtimes = []
        platforms = [observation.platform_key]
        hosts = []
        approval_gates = [
            "network_access_approval"
            if backend == "remote_endpoint"
            else "advanced_local_command_approval"
        ]
        target = import_id

    if observation.expires_at <= now:
        blockers.append(
            _reason(
                "machine_observation_stale",
                "The machine observation has expired.",
                "Check this machine again and create a new plan.",
            )
        )
    effects, steps, validation_steps, rollback_steps = _backend_steps(backend, target)
    requirements = InstallPlanRequirements(
        platform=platforms,
        runtimes=runtimes,
        license=license_requirement,
        credentials=credentials,
        network=[source.get("endpoint") or source.get("source_url")]
        if backend == "remote_endpoint"
        else [],
        storage=[f"wright-managed:{target}"]
        if backend in {"local_package", "local_command"}
        else [],
        host=hosts,
    )
    plan_material = {
        "plan_id": "pending",
        "plan_version": 1,
        "state": "blocked" if blockers else "reviewable",
        "capability_id": capability_id,
        "snapshot_id": snapshot_id,
        "capability_digest": capability_digest,
        "import_draft_id": import_id,
        "import_draft_digest": import_digest,
        "machine_observation_id": observation.observation_id,
        "machine_observation_digest": observation.digest,
        "backend_kind": backend,
        "requested_scope": requested_scope,
        "workspace_id": workspace_id,
        "source": source,
        "requirements": requirements.model_dump(mode="json"),
        "effects": [item.model_dump(mode="json") for item in effects],
        "steps": [item.model_dump(mode="json") for item in steps],
        "validation_steps": [item.model_dump(mode="json") for item in validation_steps],
        "rollback_steps": [item.model_dump(mode="json") for item in rollback_steps],
        "approval_gates": approval_gates,
        "blocking_reasons": [item.model_dump(mode="json") for item in blockers],
        "created_by": actor,
        "created_at": now.isoformat(),
        "expires_at": (now + PLAN_TTL).isoformat(),
        "approved_by": None,
        "approved_at": None,
        "plan_digest": "0" * 64,
    }
    identity_digest = hashlib.sha256(canonical_json(plan_material)).hexdigest()
    plan_material["plan_id"] = f"plan-{identity_digest[:20]}"
    provisional = InstallPlan.model_validate(plan_material)
    plan = provisional.model_copy(update={"plan_digest": plan_digest(provisional)})
    _persist(database_path, plan)
    return plan


def get_install_plan(database_path: str | Path, plan_id: str) -> InstallPlan:
    with sqlite3.connect(str(database_path)) as connection:
        row = connection.execute(
            "SELECT plan_json FROM mcp_install_plans WHERE plan_id=?", (plan_id,)
        ).fetchone()
    if row is None:
        raise InstallPlanError(
            "install_plan_not_found", "Install plan was not found.", status_code=404
        )
    return InstallPlan.model_validate_json(row[0])


def approve_install_plan(
    database_path: str | Path,
    plan_id: str,
    digest: str,
    *,
    actor: str,
    now: datetime,
) -> InstallPlan:
    plan = get_install_plan(database_path, plan_id)
    now = now.astimezone(UTC)
    if plan.plan_digest != digest:
        raise InstallPlanError(
            "install_plan_digest_mismatch", "Install plan digest does not match."
        )
    if plan.expires_at <= now:
        raise InstallPlanError("install_plan_expired", "Install plan has expired.")
    if plan.state == "blocked":
        raise InstallPlanError(
            "install_plan_blocked", "Blocked plans cannot be approved."
        )
    if plan.state == "approved":
        return plan
    if plan.state != "reviewable":
        raise InstallPlanError(
            "install_plan_state_invalid", "Install plan is not reviewable."
        )
    updated = plan.model_copy(
        update={"state": "approved", "approved_by": actor, "approved_at": now}
    )
    _persist(database_path, updated)
    return updated


def validate_plan_for_apply(
    plan: InstallPlan,
    digest: str,
    *,
    now: datetime,
    active_snapshot_id: str,
    observation_digest: str,
) -> None:
    if plan.plan_digest != digest or plan_digest(plan) != digest:
        raise InstallPlanError(
            "install_plan_invalidated", "Install plan material changed."
        )
    if plan.state != "approved":
        raise InstallPlanError(
            "install_plan_not_approved", "Install plan is not approved."
        )
    if plan.expires_at <= now.astimezone(UTC):
        raise InstallPlanError("install_plan_expired", "Install plan has expired.")
    if (
        plan.snapshot_id != active_snapshot_id
        or plan.machine_observation_digest != observation_digest
    ):
        raise InstallPlanError(
            "install_plan_invalidated", "Catalog or machine evidence changed."
        )
