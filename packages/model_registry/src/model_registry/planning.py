"""Canonical, expiring effect plans for engineering-model lifecycle changes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Mapping

from pydantic import Field

from .models import FrozenModel, ModelPackage, canonical_digest
from .policy import HostObservation, ModelPolicy, PolicyState


class ModelPlanError(ValueError):
    """Stable non-secret plan confirmation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PlanEffect(FrozenModel):
    kind: Literal[
        "network",
        "read",
        "write",
        "cache_reuse",
        "activate",
        "deactivate",
        "export",
        "retain",
        "delete",
    ]
    description: str = Field(min_length=1, max_length=1000)
    source: str | None = Field(default=None, max_length=2048)
    safe_location: str | None = Field(default=None, max_length=256)
    exact_bytes: int | None = Field(default=None, ge=0)
    maximum_bytes: int = Field(ge=0)
    reversible: bool


class PlanBlocker(FrozenModel):
    category: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    message: str = Field(min_length=1, max_length=1000)
    recovery: str = Field(min_length=1, max_length=1000)


class PlanRequirements(FrozenModel):
    network: Literal["none", "required", "optional"]
    credential: Literal["none", "read_token_reference", "external_action"]
    license_action: Literal["none", "review", "external_acceptance"]
    runtime_change: Literal["separate_plan_only"] = "separate_plan_only"


class PlanCompatibility(FrozenModel):
    state: Literal["compatible", "incompatible", "uncertain", "blocked"]
    observed_at: datetime
    reasons: tuple[str, ...] = Field(default=(), max_length=128)


class PlanPrompt(FrozenModel):
    prompt_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    message: str = Field(min_length=1, max_length=1000)
    required: bool


class PlanRuntimeRequirement(FrozenModel):
    adapter_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    version_specifier: str = Field(min_length=1, max_length=128)
    state: Literal["available", "missing", "incompatible", "unhealthy", "blocked"]
    separate_plan_required: bool


class PlanReference(FrozenModel):
    kind: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    owner_id: str = Field(min_length=1, max_length=128)
    effect: Literal["create", "retain", "detach", "block"]


class ModelEffectPlan(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(min_length=1, max_length=128)
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    principal_id: str = Field(min_length=1, max_length=128)
    operation_kind: Literal[
        "install", "import", "update", "rollback", "export", "uninstall", "purge"
    ]
    model_id: str = Field(min_length=1, max_length=128)
    package_revision: int = Field(ge=1)
    variant_id: str = Field(min_length=1, max_length=128)
    snapshot_id: str = Field(min_length=1, max_length=128)
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    effects: tuple[PlanEffect, ...] = Field(max_length=256)
    blockers: tuple[PlanBlocker, ...] = Field(max_length=128)
    requirements: PlanRequirements
    compatibility: PlanCompatibility
    prompts: tuple[PlanPrompt, ...] = Field(max_length=32)
    runtime_requirement: PlanRuntimeRequirement
    credential_reference_present: bool = False
    references: tuple[PlanReference, ...] = Field(default=(), max_length=1000)
    rollback: str = Field(min_length=1, max_length=2000)
    cleanup: str = Field(min_length=1, max_length=2000)
    created_at: datetime
    expires_at: datetime
    state: Literal[
        "preview", "confirmable", "blocked", "confirmed", "expired", "invalidated"
    ]

    def material(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", exclude={"plan_digest", "state"}, exclude_none=True
        )


def _runtime_state(blocker_categories: set[str]) -> str:
    if "runtime_missing" in blocker_categories:
        return "missing"
    if "runtime_incompatible" in blocker_categories:
        return "incompatible"
    if "runtime_unhealthy" in blocker_categories:
        return "unhealthy"
    return "available"


def _effect_material(
    package: ModelPackage,
    *,
    variant_id: str,
    cached_digests: set[str],
    operation_kind: str,
) -> tuple[PlanEffect, ...]:
    variant = package.variant(variant_id)
    effects: list[PlanEffect] = []
    for artifact in variant.artifacts:
        cached = artifact.sha256 in cached_digests
        read_kind = (
            "cache_reuse"
            if cached
            else (
                "network"
                if package.source.kind in {"https", "hugging_face"}
                else "read"
            )
        )
        effects.append(
            PlanEffect(
                kind=read_kind,
                description=(
                    f"Reuse verified content for {artifact.path}."
                    if cached
                    else f"Acquire the exact declared artifact {artifact.path}."
                ),
                source=artifact.source_uri,
                safe_location="Wright engineering-model operation staging",
                exact_bytes=artifact.size,
                maximum_bytes=artifact.size,
                reversible=True,
            )
        )
        effects.append(
            PlanEffect(
                kind="write",
                description=f"Promote verified content for {artifact.path} by SHA-256.",
                safe_location="Wright engineering-model content store",
                exact_bytes=artifact.size,
                maximum_bytes=artifact.size,
                reversible=True,
            )
        )
    effects.append(
        PlanEffect(
            kind="activate",
            description=(
                f"Atomically activate package revision {package.package_revision} "
                f"for {package.model_id}."
            ),
            safe_location="Wright engineering-model installation registry",
            exact_bytes=0,
            maximum_bytes=0,
            reversible=True,
        )
    )
    if operation_kind == "import":
        effects.insert(
            0,
            PlanEffect(
                kind="read",
                description="Inspect one caller-selected offline package archive.",
                safe_location="Wright engineering-model operation staging",
                maximum_bytes=variant.resources.download_bytes + 64 * 1024,
                reversible=True,
            ),
        )
    return tuple(effects)


def create_effect_plan(
    package: ModelPackage,
    *,
    variant_id: str,
    snapshot_id: str,
    principal_id: str,
    host: HostObservation,
    now: datetime,
    ttl: timedelta = timedelta(minutes=10),
    operation_kind: Literal["install", "import"] = "install",
    cached_digests: set[str] | frozenset[str] = frozenset(),
    credential_reference_present: bool = False,
    references: tuple[Mapping[str, str], ...] = (),
) -> ModelEffectPlan:
    """Build a complete deterministic preview; it performs no source or runtime call."""

    observed = now.astimezone(UTC)
    if ttl <= timedelta(0) or ttl > timedelta(hours=1):
        raise ModelPlanError("plan_ttl_invalid", "Plan expiry is invalid")
    policy = ModelPolicy().evaluate(package, variant_id=variant_id, host=host)
    variant = package.variant(variant_id)
    blockers = tuple(
        PlanBlocker(
            category=item.category, message=item.message, recovery=item.recovery
        )
        for item in policy.blockers
    )
    categories = {item.category for item in blockers}
    network_required = package.source.kind in {"https", "hugging_face"} and any(
        artifact.sha256 not in cached_digests for artifact in variant.artifacts
    )
    license_action = (
        "external_acceptance"
        if package.license.acceptance_required
        else "review"
        if package.license.redistribution == "review_required"
        else "none"
    )
    credential = (
        "external_action"
        if package.source.access in {"gated", "private"}
        and not credential_reference_present
        else "read_token_reference"
        if credential_reference_present
        else "none"
    )
    base: dict[str, Any] = {
        "schema_version": "1.0",
        "principal_id": principal_id,
        "operation_kind": operation_kind,
        "model_id": package.model_id,
        "package_revision": package.package_revision,
        "variant_id": variant_id,
        "snapshot_id": snapshot_id,
        "manifest_digest": package.digest,
        "effects": [
            item.model_dump(mode="json", exclude_none=True)
            for item in _effect_material(
                package,
                variant_id=variant_id,
                cached_digests=set(cached_digests),
                operation_kind=operation_kind,
            )
        ],
        "blockers": [item.model_dump(mode="json") for item in blockers],
        "requirements": {
            "network": "required" if network_required else "none",
            "credential": credential,
            "license_action": license_action,
            "runtime_change": "separate_plan_only",
        },
        "compatibility": {
            "state": str(policy.state),
            "observed_at": observed.isoformat().replace("+00:00", "Z"),
            "reasons": [item.message for item in blockers],
        },
        "prompts": [
            {
                "prompt_id": f"confirm-{operation_kind}",
                "message": (
                    f"Confirm the exact {operation_kind} effects for "
                    f"{package.display_name} revision {package.package_revision}."
                ),
                "required": True,
            }
        ],
        "runtime_requirement": {
            "adapter_id": variant.runtime.adapter_id,
            "version_specifier": variant.runtime.version_specifier,
            "state": _runtime_state(categories),
            "separate_plan_required": _runtime_state(categories) != "available",
        },
        "credential_reference_present": credential_reference_present,
        "references": [dict(item) for item in references],
        "rollback": (
            "If activation has not committed, remove operation staging. If activation "
            "commits, deactivate this exact revision while retaining referenced cache."
        ),
        "cleanup": (
            "Delete operation staging and release reservations; verified shared content "
            "is retained only when referenced or safely reusable."
        ),
        "created_at": observed.isoformat().replace("+00:00", "Z"),
        "expires_at": (observed + ttl).isoformat().replace("+00:00", "Z"),
        "state": "blocked" if policy.state != PolicyState.COMPATIBLE else "confirmable",
    }
    identity = canonical_digest(base)
    base["plan_id"] = f"plan-{identity[:24]}"
    base["plan_digest"] = canonical_digest(
        {key: value for key, value in base.items() if key != "state"}
    )
    return ModelEffectPlan.model_validate(base)


def confirm_effect_plan(
    plan: ModelEffectPlan,
    *,
    principal_id: str,
    plan_digest: str,
    now: datetime,
    current_plan: ModelEffectPlan,
) -> ModelEffectPlan:
    """Confirm one unchanged preview; callers persist the one-time transition."""

    if plan.state == "blocked":
        raise ModelPlanError(
            "plan_blocked", "The plan has blockers and cannot be confirmed"
        )
    invalid = (
        plan.state != "confirmable"
        or principal_id != plan.principal_id
        or plan_digest != plan.plan_digest
        or now.astimezone(UTC) >= plan.expires_at.astimezone(UTC)
        or current_plan.plan_digest != plan.plan_digest
        or current_plan.material() != plan.material()
    )
    if invalid:
        raise ModelPlanError(
            "plan_invalidated",
            "The preview changed or expired; create and review a fresh plan.",
        )
    return plan.model_copy(update={"state": "confirmed"})


__all__ = [
    "ModelEffectPlan",
    "ModelPlanError",
    "PlanBlocker",
    "PlanEffect",
    "confirm_effect_plan",
    "create_effect_plan",
]
