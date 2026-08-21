"""Application service joining curated scenarios to revision-checked Rivet runs."""

from __future__ import annotations

import platform
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from core.engineering_scenarios import (
    AssertionCategory,
    AssertionResult,
    AssertionState,
    EngineeringScenarioError,
    ScenarioCatalogEntry,
    ScenarioState,
)
from core.rivet_mcp import canonical_digest
from core.workflow_runs import WorkflowRun
from data_vault import EngineeringScenarioRepository, WorkflowRunRepository
from tool_registry.canonical_catalog import load_canonical_entries
from tool_registry.catalog_platforms import platform_selection_reason

from .engineering_scenario_artifacts import artifact_document, normalize_artifact
from .engineering_scenario_assertions import EngineeringAssertionRegistry
from .engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    EngineeringScenarioManifest,
    contract_document,
    fixture_documents,
    workflow_text,
)
from .workflow_operations import (
    WorkflowMcpBindingPreview,
    WorkflowOperationsError,
    WorkspaceWorkflowOperations,
)
from .workflows import WorkspaceWorkflowStore


@dataclass(frozen=True, slots=True)
class ScenarioBlocker:
    code: str
    message: str
    recovery: str


@dataclass(frozen=True, slots=True)
class ScenarioPreflight:
    preflight_id: str
    scenario_id: str
    scenario_revision: int
    manifest_digest: str
    workflow_slug: str
    workflow_revision: int | None
    workflow_digest: str | None
    graph_id: str
    binding_set_digest: str | None
    state: str
    capabilities: tuple[Mapping[str, Any], ...]
    environment: Mapping[str, Any]
    blockers: tuple[ScenarioBlocker, ...]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ScenarioEnvironmentAuthorization:
    """Explicit, non-persistent permission for one environment preflight."""

    allow_tier2: bool = False
    allow_tier3: bool = False
    network: bool = False
    credentials: bool = False
    proprietary_application: bool = False
    gpu: bool = False
    hardware: bool = False
    large_download: bool = False
    license_reviewed: bool = False
    disposable: bool = False


@dataclass(frozen=True, slots=True)
class Tier2AdapterPlan:
    """Bounded evidence plan for a selected clean-container MCP probe."""

    catalog_id: str
    catalog_digest: str
    platform_target: str
    package_identity: str | None
    install_command_digest: str
    safe_tool: str
    state: str
    blockers: tuple[ScenarioBlocker, ...]
    pending_evidence: tuple[str, ...]
    evidence_resources: tuple[str, ...]
    discovery_digest: str | None = None
    gateway_digest: str | None = None
    cleanup_state: str = "not_started"


def _platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    architecture = "arm64" if machine in {"arm64", "aarch64"} else "amd64"
    if system == "darwin":
        return "macos"
    return f"{system}-{architecture}"


def classify_scenario_environment(
    document: Mapping[str, Any],
    *,
    platform_tag: str,
    authorization: ScenarioEnvironmentAuthorization | None = None,
) -> tuple[ScenarioBlocker, ...]:
    authorization = authorization or ScenarioEnvironmentAuthorization()
    environment = document["environment"]
    blockers: list[ScenarioBlocker] = []
    tier = str(document["tier"])
    if tier == "tier2" and not authorization.allow_tier2:
        blockers.append(
            ScenarioBlocker(
                "scenario_tier_opt_in_required",
                "tier2 scenarios require explicit opt-in",
                "Select the documented clean-container or manual validation path.",
            )
        )
    if tier == "tier3" and not authorization.allow_tier3:
        blockers.append(
            ScenarioBlocker(
                "scenario_tier_opt_in_required",
                "tier3 scenarios require explicit manual opt-in",
                "Use the documented credentialed or proprietary validation path.",
            )
        )
    platforms = set(environment.get("platforms", ()))
    if platforms and platform_tag not in platforms:
        blockers.append(
            ScenarioBlocker(
                "scenario_platform_unsupported",
                f"Scenario does not declare support for {platform_tag}",
                "Choose a declared platform or update validated platform evidence.",
            )
        )
    for key, label in (
        ("network", "network access"),
        ("credentials", "credentials"),
        ("proprietary_application", "a proprietary application"),
        ("gpu", "a GPU"),
        ("hardware", "physical hardware"),
        ("large_download", "a large download"),
    ):
        required = bool(environment.get(key))
        if tier == "tier1" and required:
            blockers.append(
                ScenarioBlocker(
                    "scenario_tier_invalid",
                    f"Tier 1 unexpectedly requires {label}",
                    "Reclassify the scenario before running it.",
                )
            )
        elif required and not bool(getattr(authorization, key)):
            blockers.append(
                ScenarioBlocker(
                    f"scenario_{key}_authorization_required",
                    f"Scenario requires {label}",
                    "Provide explicit one-run authorization or choose a deterministic Tier 1 scenario.",
                )
            )
    if environment.get("license_prompt") and not authorization.license_reviewed:
        blockers.append(
            ScenarioBlocker(
                "scenario_license_review_required",
                "Scenario package license has not been reviewed",
                "Review the exact package license separately; Wright never accepts terms automatically.",
            )
        )
    if environment.get("host_mutation"):
        blockers.append(
            ScenarioBlocker(
                "scenario_host_mutation_forbidden",
                "Scenario would mutate the developer host",
                "Use a disposable clean container and keep host software outside Wright's base image.",
            )
        )
    if environment.get("interactive_prompt"):
        blockers.append(
            ScenarioBlocker(
                "scenario_interactive_prompt_forbidden",
                "Scenario would open an interactive install or credential prompt",
                "Resolve requirements before the run; unattended validation must fail closed.",
            )
        )
    if tier == "tier2" and not authorization.disposable:
        blockers.append(
            ScenarioBlocker(
                "scenario_disposable_environment_required",
                "Tier 2 validation requires a disposable clean container",
                "Follow the clean-container MCP validation process.",
            )
        )
    if environment.get("catalog_state") in {
        "api_wrapper_candidate",
        "watchlist",
        "no_public_mcp",
        "unconfirmed",
    }:
        blockers.append(
            ScenarioBlocker(
                "scenario_catalog_entry_unconfirmed",
                "Catalog entry is not a confirmed runnable MCP",
                "Keep it visible as a candidate or watchlist entry until primary evidence confirms an MCP.",
            )
        )
    if document["safety"].get("physical_actuation") is not False:
        blockers.append(
            ScenarioBlocker(
                "scenario_physical_actuation_forbidden",
                "Physical actuation is forbidden",
                "Use static artifact validation only.",
            )
        )
    return tuple(blockers)


_TIER2_ADAPTERS = {
    "nvidia-elements-mcp": "skills_list",
    "ansys-fluent-mcp": "session_status",
}


def selected_tier2_adapter_plan(
    catalog_id: str,
    *,
    platform_target: str,
    authorization: ScenarioEnvironmentAuthorization | None = None,
) -> Tier2AdapterPlan:
    """Create an evidence-only plan; it never installs or starts a server."""

    if catalog_id not in _TIER2_ADAPTERS:
        raise EngineeringScenarioError(
            "scenario_tier2_adapter_unknown",
            "Only explicitly reviewed Tier 2 catalog adapters are available",
        )
    entries = {entry.id: entry for entry in load_canonical_entries()}
    entry = entries[catalog_id]
    confirmed = entry.verification_state in {
        "verified_mcp",
        "verified_docs_mcp",
        "community_mcp",
    }
    environment = {
        "network": True,
        "credentials": False,
        "proprietary_application": False,
        "gpu": False,
        "hardware": False,
        "large_download": False,
        "license_prompt": not entry.license or entry.license.lower() == "unknown",
        "host_mutation": False,
        "interactive_prompt": False,
        "platforms": [platform_target],
        "catalog_state": "confirmed" if confirmed else str(entry.evidence_class),
    }
    document = {
        "tier": "tier2",
        "environment": environment,
        "safety": {"physical_actuation": False},
    }
    blockers = list(
        classify_scenario_environment(
            document,
            platform_tag=platform_target,
            authorization=authorization,
        )
    )
    try:
        platform_reason = platform_selection_reason(
            entry,
            platform_target,
            mode="host",
            require_docker=True,
        )
    except ValueError as error:
        platform_reason = str(error)
    if platform_reason:
        blockers.append(
            ScenarioBlocker(
                "scenario_catalog_platform_incompatible",
                platform_reason,
                "Choose a catalog-declared clean-container platform.",
            )
        )
    pending = tuple(sorted(set(entry.validation_result.missing_dependencies)))
    evidence_resources = tuple(
        source.url for source in entry.source_records if source.kind == "evidence"
    )
    return Tier2AdapterPlan(
        catalog_id=catalog_id,
        catalog_digest=canonical_digest(entry.model_dump(mode="json")),
        platform_target=platform_target,
        package_identity=entry.package_url or entry.container_url,
        install_command_digest=canonical_digest(entry.command),
        safe_tool=_TIER2_ADAPTERS[catalog_id],
        state="blocked" if blockers else "partial",
        blockers=tuple(blockers),
        pending_evidence=pending,
        evidence_resources=evidence_resources,
    )


def _extract_artifact_claims(value: Any) -> tuple[Mapping[str, Any], ...]:
    found: list[Mapping[str, Any]] = []

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            if {
                "schema_version",
                "artifact_id",
                "domain",
                "kind",
                "source_schema",
                "producer",
            } <= set(item):
                found.append(item)
                return
            for child in item.values():
                visit(child)
        elif isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            for child in item:
                visit(child)

    visit(value)
    return tuple(found)


def _binding_provider(binding: Any):
    return getattr(binding, "provider", None) if binding is not None else None


class EngineeringScenarioService:
    def __init__(
        self,
        db_path: str,
        *,
        operations: WorkspaceWorkflowOperations,
        catalog: EngineeringScenarioCatalog | None = None,
        repository: EngineeringScenarioRepository | None = None,
        assertions: EngineeringAssertionRegistry | None = None,
    ) -> None:
        self._catalog = catalog or EngineeringScenarioCatalog()
        self._operations = operations
        self._repository = repository or EngineeringScenarioRepository(db_path)
        self._workflow_runs = WorkflowRunRepository(db_path)
        self._assertions = assertions or EngineeringAssertionRegistry()

    def list(
        self, *, domains: Sequence[str] = (), tier: str | None = None
    ) -> tuple[ScenarioCatalogEntry, ...]:
        return self._catalog.list(domains=domains, tier=tier)

    def detail(self, scenario_id: str) -> EngineeringScenarioManifest:
        return self._catalog.get(scenario_id)

    def prepare(self, *, workspace_dir: str, scenario_id: str):
        manifest = self._catalog.get(scenario_id)
        slug = f"scenario-{scenario_id}"
        store = WorkspaceWorkflowStore(workspace_dir)
        project = workflow_text(manifest)
        try:
            existing = store.read(slug)
        except FileNotFoundError:
            return store.create(slug, project)
        if existing.project != project:
            raise EngineeringScenarioError(
                "scenario_workflow_modified",
                "The prepared scenario workflow was modified; choose a new slug or restore it before continuing",
            )
        return existing

    async def preflight(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        scenario_id: str,
        allow_tier2: bool = False,
        platform_tag: str | None = None,
    ) -> ScenarioPreflight:
        manifest = self._catalog.get(scenario_id)
        document = self.prepare(workspace_dir=workspace_dir, scenario_id=scenario_id)
        graph_id = str(manifest.document["workflow"]["graph_id"])
        blockers = list(
            classify_scenario_environment(
                manifest.document,
                platform_tag=platform_tag or _platform_tag(),
                authorization=ScenarioEnvironmentAuthorization(
                    allow_tier2=allow_tier2,
                ),
            )
        )
        preview: WorkflowMcpBindingPreview | None = None
        capabilities: tuple[Mapping[str, Any], ...] = ()
        try:
            preview = await self._operations.preview_mcp_bindings(
                workspace_id=workspace_id,
                session_id=session_id,
                workspace_dir=workspace_dir,
                slug=document.slug,
                expected_revision=document.revision,
                expected_digest=document.digest,
                graph=graph_id,
                selections={
                    str(value["node_id"]): str(value["tool_name"])
                    for value in manifest.document["capabilities"]
                },
                units_policy={
                    str(value["node_id"]): {"scenario_manifest": manifest.digest}
                    for value in manifest.document["capabilities"]
                },
                material_defaults={},
            )
            capabilities = tuple(
                {
                    "node_id": value.requirement.node_id,
                    "requested_tool": value.requirement.static_tool_name,
                    "selected_tool": value.selected_tool,
                    "binding_digest": (
                        value.binding.binding_digest if value.binding else None
                    ),
                    "blockers": value.blockers,
                    "provider": (
                        _binding_provider(value.binding).canonical()
                        if _binding_provider(value.binding)
                        else None
                    ),
                    "provider_evidence_digest": (
                        _binding_provider(value.binding).provider_evidence_digest
                        if _binding_provider(value.binding)
                        else None
                    ),
                }
                for value in preview.nodes
            )
            declared_providers = {
                str(value["node_id"]): value.get("provider_kind")
                for value in manifest.document["capabilities"]
            }
            for value in preview.nodes:
                provider_label = (
                    "engineering model"
                    if declared_providers.get(value.requirement.node_id)
                    == "engineering_model"
                    else "MCP capability"
                )
                for code in value.blockers:
                    blockers.append(
                        ScenarioBlocker(
                            f"scenario_{code}",
                            f"Capability for node {value.requirement.node_id} is not ready: {code}",
                            f"Enable and validate the exact workspace {provider_label}, then refresh preflight.",
                        )
                    )
                expected_provider = declared_providers.get(value.requirement.node_id)
                actual_provider = (
                    _binding_provider(value.binding).provider_kind
                    if _binding_provider(value.binding)
                    else None
                )
                if expected_provider and actual_provider != expected_provider:
                    blockers.append(
                        ScenarioBlocker(
                            "scenario_provider_kind_mismatch",
                            f"Capability for node {value.requirement.node_id} has the wrong provider kind",
                            "Refresh discovery and review an exact capability from the declared provider kind.",
                        )
                    )
        except WorkflowOperationsError as error:
            blockers.append(
                ScenarioBlocker(
                    error.code.lower(),
                    str(error),
                    "Enable Rivet workflow operations and the workspace MCP gateway, then refresh preflight.",
                )
            )
        expires_at = preview.expires_at if preview else datetime.now(UTC)
        return ScenarioPreflight(
            preflight_id=f"scenario-preflight-{uuid.uuid4()}",
            scenario_id=scenario_id,
            scenario_revision=int(manifest.document["revision"]),
            manifest_digest=manifest.digest,
            workflow_slug=document.slug,
            workflow_revision=document.revision,
            workflow_digest=document.digest,
            graph_id=graph_id,
            binding_set_digest=(
                preview.binding_set.binding_set_digest
                if preview and preview.binding_set
                else None
            ),
            state="blocked" if blockers else "ready",
            capabilities=capabilities,
            environment={
                **dict(manifest.document["environment"]),
                "tier": manifest.document["tier"],
                "platform": platform_tag or _platform_tag(),
                "resource": dict(manifest.document["resource"]),
                "physical_actuation": False,
            },
            blockers=tuple(blockers),
            expires_at=expires_at,
        )

    async def start(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        scenario_id: str,
        manifest_digest: str,
        workflow_revision: int,
        workflow_digest: str,
        binding_set_digest: str,
        seed: int = 0,
    ) -> tuple[str, WorkflowRun]:
        manifest = self._catalog.get(scenario_id)
        if manifest.digest != manifest_digest:
            raise EngineeringScenarioError(
                "scenario_preflight_stale", "Scenario manifest changed"
            )
        environment_blockers = classify_scenario_environment(
            manifest.document,
            platform_tag=_platform_tag(),
        )
        if environment_blockers:
            raise EngineeringScenarioError(
                environment_blockers[0].code,
                environment_blockers[0].message,
            )
        document = self.prepare(workspace_dir=workspace_dir, scenario_id=scenario_id)
        if document.revision != workflow_revision or document.digest != workflow_digest:
            raise EngineeringScenarioError(
                "scenario_preflight_stale", "Scenario workflow changed"
            )
        run = await self._operations.start(
            workspace_id=workspace_id,
            session_id=session_id,
            workspace_dir=workspace_dir,
            slug=document.slug,
            expected_revision=workflow_revision,
            expected_digest=workflow_digest,
            binding_set_digest=binding_set_digest,
            graph=str(manifest.document["workflow"]["graph_id"]),
            context={
                "wright_engineering_scenario": {
                    "scenario_id": scenario_id,
                    "revision": manifest.document["revision"],
                    "manifest_digest": manifest.digest,
                    "seed": seed,
                }
            },
        )
        run_identity_digest = canonical_digest(
            {
                "kind": "engineering-scenario-run",
                "scenario_id": scenario_id,
                "scenario_revision": manifest.document["revision"],
                "manifest_digest": manifest.digest,
                "workflow_revision": workflow_revision,
                "workflow_digest": workflow_digest,
                "binding_set_digest": binding_set_digest,
            }
        )
        scenario_run_id = f"scenario-run-{uuid.uuid4()}"
        self._repository.create_draft(
            scenario_run_id=scenario_run_id,
            workflow_run_id=run.run_id,
            workspace_id=workspace_id,
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_revision=int(manifest.document["revision"]),
            manifest_digest=manifest.digest,
            workflow_digest=document.digest,
            binding_set_digest=binding_set_digest,
            identity={
                "scenario_id": scenario_id,
                "scenario_revision": manifest.document["revision"],
                "manifest_digest": manifest.digest,
                "workflow_id": run.workflow_id,
                "workflow_revision": run.revision,
                "workflow_digest": document.digest,
                "graph_id": manifest.document["workflow"]["graph_id"],
                "binding_set_digest": binding_set_digest,
                "assertion_set_digest": canonical_assertion_digest(manifest),
                "input_digest": canonical_digest(manifest.document.get("inputs", {})),
                "fixture_digest": canonical_digest(
                    fixture_documents(scenario_id, run_id="material-identity")
                ),
                "artifact_contract_digest": canonical_digest(
                    manifest.document["artifacts"]
                ),
                "capability_requirements_digest": canonical_digest(
                    manifest.document["capabilities"]
                ),
                "contract_set_digest": canonical_digest(
                    {
                        name: contract_document(name)
                        for name in (
                            (
                                "scenario-manifest-1.1.schema.json"
                                if manifest.document["schema_version"] == "1.1"
                                else "scenario-manifest.schema.json"
                            ),
                            "artifact-envelope.schema.json",
                            "assertion-result.schema.json",
                        )
                    }
                ),
                # Legacy evidence field; this is a machine-generated run
                # identity, not a user approval.
                "review_digest": run_identity_digest,
                "seed": seed,
            },
            environment={
                **dict(manifest.document["environment"]),
                "tier": manifest.document["tier"],
                "platform": _platform_tag(),
            },
            created_at=datetime.now(UTC),
        )
        return scenario_run_id, run

    def report(self, scenario_run_id: str) -> dict[str, Any] | None:
        current = self._repository.get(scenario_run_id)
        if current is None or current["state"] != "running":
            return _report_projection(current)
        workflow = self._workflow_runs.get(str(current["workflow_run_id"]))
        if workflow is None or workflow.state in {"queued", "running", "cancelling"}:
            return current
        if workflow.state == "cancelled":
            terminal = ScenarioState.CANCELLED
            claims: tuple[Mapping[str, Any], ...] = ()
        elif workflow.state == "failed":
            terminal = ScenarioState.FAILED
            claims = ()
        else:
            claims = _extract_artifact_claims(workflow.output_summary)
            terminal = ScenarioState.PASSED
        return self._finalize(
            current,
            terminal=terminal,
            claims=claims,
            workflow_state=workflow.state,
            failure_reason=workflow.reason_code,
        )

    def finalize_with_fixture_evidence(
        self, scenario_run_id: str, *, state: ScenarioState = ScenarioState.PASSED
    ) -> dict[str, Any]:
        """Deterministic test adapter; production uses artifacts from the run output."""
        current = self._repository.get(scenario_run_id)
        if current is None:
            raise EngineeringScenarioError(
                "scenario_report_unavailable", "Scenario report was not found"
            )
        claims = fixture_documents(
            str(current["scenario_id"]), run_id=str(current["workflow_run_id"])
        )
        return self._finalize(current, terminal=state, claims=claims)

    def _finalize(
        self,
        current: Mapping[str, Any],
        *,
        terminal: ScenarioState,
        claims: Sequence[Mapping[str, Any]],
        workflow_state: str | None = None,
        failure_reason: str | None = None,
    ) -> dict[str, Any]:
        manifest = self._catalog.get(str(current["scenario_id"]))
        expected_identity = {
            "scenario_revision": int(manifest.document["revision"]),
            "manifest_digest": manifest.digest,
            "assertion_set_digest": canonical_assertion_digest(manifest),
        }
        actual_identity = {
            "scenario_revision": int(current["scenario_revision"]),
            "manifest_digest": str(current["manifest_digest"]),
            "assertion_set_digest": str(
                current.get("identity", {}).get("assertion_set_digest", "")
            ),
        }
        differences = {
            key: {"recorded": actual_identity[key], "current": expected}
            for key, expected in expected_identity.items()
            if actual_identity[key] != expected
        }
        if differences:
            raise EngineeringScenarioError(
                "scenario_rebuild_identity_mismatch",
                "Scenario report cannot be rebuilt because material identities changed: "
                + ", ".join(sorted(differences)),
            )
        try:
            artifacts = {
                artifact.artifact_id: artifact
                for artifact in (normalize_artifact(value) for value in claims)
            }
            assertions = (
                self._assertions.evaluate_manifest(
                    manifest.document["assertions"], artifacts
                )
                if artifacts
                else ()
            )
        except ValueError as error:
            artifacts = {}
            reason_code = getattr(error, "code", "artifact_secret_material_forbidden")
            assertions = (
                _diagnostic_result(
                    reason_code=reason_code,
                    category=AssertionCategory.CONTRACT,
                    message=str(error),
                    recovery="Inspect the producing MCP node and artifact contract.",
                    observed={"error": str(error)},
                ),
            )
            terminal = ScenarioState.ERROR
        expected_artifacts = {
            str(item["artifact_id"]) for item in manifest.document["artifacts"]
        }
        if terminal == ScenarioState.PASSED and set(artifacts) != expected_artifacts:
            assertions = (
                *assertions,
                _diagnostic_result(
                    reason_code="scenario_artifact_set_mismatch",
                    category=AssertionCategory.CONTRACT,
                    message="Scenario produced an incomplete or unexpected artifact set",
                    recovery="Inspect the exact workflow nodes and artifact declarations.",
                    expected={"artifact_ids": sorted(expected_artifacts)},
                    observed={"artifact_ids": sorted(artifacts)},
                ),
            )
            terminal = ScenarioState.FAILED
        elif terminal == ScenarioState.PASSED and any(
            value.state != AssertionState.PASS for value in assertions
        ):
            terminal = ScenarioState.FAILED
        if (
            terminal in {ScenarioState.FAILED, ScenarioState.CANCELLED}
            and not assertions
        ):
            category = _workflow_failure_category(
                failure_reason or workflow_state or ""
            )
            reason_code = _stable_reason(
                failure_reason
                or (
                    "scenario_cancelled"
                    if terminal == ScenarioState.CANCELLED
                    else "scenario_workflow_failed"
                )
            )
            assertions = (
                _diagnostic_result(
                    reason_code=reason_code,
                    category=category,
                    message=f"Workflow ended as {workflow_state or terminal}",
                    recovery=_workflow_failure_recovery(category),
                    observed={
                        "workflow_state": workflow_state or str(terminal),
                        "reason_code": reason_code,
                    },
                ),
            )
        self._repository.finalize(
            scenario_run_id=str(current["scenario_run_id"]),
            state=terminal,
            artifacts=tuple(artifact_document(value) for value in artifacts.values()),
            assertions=assertions,
            cleanup_state="clean" if terminal != ScenarioState.CANCELLED else "unknown",
            residue={},
            finalized_at=datetime.now(UTC),
        )
        result = self._repository.get(str(current["scenario_run_id"]))
        assert result is not None
        return _report_projection(result)

    async def cancel(
        self,
        *,
        workspace_id: str,
        session_id: str,
        scenario_run_id: str,
    ) -> WorkflowRun:
        current = self._repository.get(scenario_run_id)
        if current is None:
            raise EngineeringScenarioError(
                "scenario_report_unavailable", "Scenario report was not found"
            )
        run = self._operations.run(
            workspace_id=workspace_id,
            session_id=session_id,
            run_id=str(current["workflow_run_id"]),
        )
        return await self._operations.cancel(
            workspace_id=workspace_id,
            session_id=session_id,
            run_id=run.run_id,
            generation=run.generation,
        )

    def compare(self, left: str, right: str) -> dict[str, Any]:
        first = self._repository.get(left)
        second = self._repository.get(right)
        if first is None or second is None:
            raise EngineeringScenarioError(
                "scenario_report_unavailable", "Scenario report was not found"
            )
        differences: list[dict[str, Any]] = []
        keys = (
            "scenario_id",
            "scenario_revision",
            "manifest_digest",
            "workflow_digest",
            "binding_set_digest",
        )
        for key in keys:
            if first.get(key) != second.get(key):
                differences.append(
                    {"field": key, "left": first.get(key), "right": second.get(key)}
                )
        for key in (
            "seed",
            "assertion_set_digest",
            "graph_id",
            "input_digest",
            "fixture_digest",
            "artifact_contract_digest",
            "capability_requirements_digest",
            "contract_set_digest",
            "review_digest",
        ):
            if first["identity"].get(key) != second["identity"].get(key):
                differences.append(
                    {
                        "field": key,
                        "left": first["identity"].get(key),
                        "right": second["identity"].get(key),
                    }
                )
        if first["environment"] != second["environment"]:
            differences.append(
                {
                    "field": "environment",
                    "left": first["environment"],
                    "right": second["environment"],
                }
            )
        first_artifacts = _material_artifacts(first["artifacts"])
        second_artifacts = _material_artifacts(second["artifacts"])
        for artifact_id in sorted(set(first_artifacts) | set(second_artifacts)):
            if first_artifacts.get(artifact_id) != second_artifacts.get(artifact_id):
                differences.append(
                    {
                        "field": f"artifact:{artifact_id}",
                        "left": first_artifacts.get(artifact_id),
                        "right": second_artifacts.get(artifact_id),
                    }
                )
        return {
            "strictly_reproducible": not differences,
            "differences": differences,
            "assertion_changes": compare_assertions(
                first["assertions"], second["assertions"]
            ),
        }


def canonical_assertion_digest(manifest: EngineeringScenarioManifest) -> str:
    return canonical_digest(manifest.document["assertions"])


def _report_projection(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    result = dict(value)
    advisory = None
    if result.get("state") == "passed":
        advisory = next(
            (
                artifact.get("content")
                for artifact in result.get("artifacts", ())
                if str(artifact.get("kind", "")).endswith("-advisory-report")
                and isinstance(artifact.get("content"), Mapping)
            ),
            None,
        )
    result["advisory"] = advisory
    return result


def _stable_reason(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized[:100] or "scenario_workflow_failed"


def _workflow_failure_category(reason: str) -> AssertionCategory:
    normalized = reason.lower()
    if any(value in normalized for value in ("approval", "policy", "denied")):
        return AssertionCategory.POLICY
    if any(
        value in normalized
        for value in ("transport", "bridge", "gateway", "panel", "host")
    ):
        return AssertionCategory.TRANSPORT
    if "timeout" in normalized or "expired" in normalized:
        return AssertionCategory.TIMEOUT
    if "cleanup" in normalized or "residue" in normalized or "cancel" in normalized:
        return AssertionCategory.CLEANUP
    if "mcp" in normalized or "tool" in normalized:
        return AssertionCategory.TOOL
    return AssertionCategory.INTERNAL


def _workflow_failure_recovery(category: AssertionCategory) -> str:
    return {
        AssertionCategory.POLICY: "Review the exact call policy or approval decision.",
        AssertionCategory.TRANSPORT: "Inspect the Wright gateway and application lifecycle.",
        AssertionCategory.TIMEOUT: "Inspect the timed-out node and bounded cleanup evidence.",
        AssertionCategory.CLEANUP: "Inspect cancellation and residue before retrying.",
        AssertionCategory.TOOL: "Inspect the named MCP tool result and server validation.",
    }.get(category, "Inspect the workflow run manifest and producing node.")


def _diagnostic_result(
    *,
    reason_code: str,
    category: AssertionCategory,
    message: str,
    recovery: str,
    expected: Any = None,
    observed: Any = None,
) -> AssertionResult:
    return AssertionResult(
        assertion_id="scenario-terminal-diagnostic",
        plugin="scenario",
        plugin_version="1.0",
        state=AssertionState.ERROR,
        category=category,
        reason_code=_stable_reason(reason_code),
        artifact_digests=(),
        producer={
            "node_id": "workflow",
            "capability": "wright__rivet_workflow",
        },
        expected=expected,
        observed=observed,
        message=message,
        recovery=recovery,
    )


def compare_assertions(
    left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], ...]:
    left_by_id = {str(value["assertion_id"]): value for value in left}
    right_by_id = {str(value["assertion_id"]): value for value in right}
    changes: list[dict[str, Any]] = []
    for assertion_id in sorted(set(left_by_id) | set(right_by_id)):
        first = left_by_id.get(assertion_id)
        second = right_by_id.get(assertion_id)
        if first != second:
            changes.append(
                {
                    "assertion_id": assertion_id,
                    "left_state": first.get("state") if first else None,
                    "right_state": second.get("state") if second else None,
                    "left_reason": first.get("reason_code") if first else None,
                    "right_reason": second.get("reason_code") if second else None,
                    "left_digest": canonical_digest(first) if first else None,
                    "right_digest": canonical_digest(second) if second else None,
                }
            )
    return tuple(changes)


def _material_artifacts(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for artifact in artifacts:
        artifact_id = str(artifact.get("artifact_id", ""))
        if not artifact_id:
            continue
        producer = artifact.get("producer")
        result[artifact_id] = {
            "domain": artifact.get("domain"),
            "kind": artifact.get("kind"),
            "source_schema": artifact.get("source_schema"),
            "upstream_digests": artifact.get("upstream_digests"),
            "units": artifact.get("units"),
            "coordinate_system": artifact.get("coordinate_system"),
            "content_digest": artifact.get("content_digest"),
            "validation_state": artifact.get("validation_state"),
            "producer_node": (
                producer.get("node_id") if isinstance(producer, Mapping) else None
            ),
            "producer_capability": (
                producer.get("capability") if isinstance(producer, Mapping) else None
            ),
        }
    return result
