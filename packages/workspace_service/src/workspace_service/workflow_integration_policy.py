"""Fail-closed, run-scoped integration authority enrolled by local test management.

Enrollment is deliberately not exposed through an HTTP route. A policy is not
engineering qualification and never updates public template readiness flags.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from urllib.parse import urlsplit

from core.canonical_json import canonical_json_bytes
from data_vault.workflow_integration_repository import WorkflowIntegrationRepository

from .workflow_source_execution import WorkflowSourceExecutionError
from .workspace_path import WorkspacePath


LOCAL_REVIEW_BINDING = {
    "server": "wright",
    "tool": "review_artifacts",
    "schema": hashlib.sha256(b"wright.local_review.v1").hexdigest(),
}
LOCAL_REVIEW_DESTINATION = {"kind": "local_review", "id": "workspace"}
TEST_HANDOFF_BINDING = {
    "server": "wright",
    "tool": "test_handoff",
    "schema": hashlib.sha256(b"wright.integration_test_handoff.v1").hexdigest(),
}


class WorkflowIntegrationPolicyError(WorkflowSourceExecutionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(
            code,
            message,
            "Re-enroll the exact isolated test run through local campaign management.",
        )


def _fail(message: str, code: str = "WORKFLOW_INTEGRATION_POLICY_INVALID"):
    raise WorkflowIntegrationPolicyError(code, message)


def _sha(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        _fail("An exact lowercase SHA-256 identity is required.")
    return value


def _path(value: object) -> str:
    if not isinstance(value, str) or "\\" in value or "%" in value:
        _fail("Use an exact workspace-relative POSIX path.")
    try:
        parts = WorkspacePath._validate_relative(value)
    except ValueError:
        _fail("Integration paths must remain inside the workspace.")
    if "/".join(parts) != value:
        _fail("Integration paths must have a canonical spelling.")
    return value


def _test_uri(value: object) -> str:
    if not isinstance(value, str):
        _fail("A test destination URI is required.")
    try:
        parsed = urlsplit(value)
    except ValueError:
        _fail("The test destination URI is malformed.")
    if (
        parsed.scheme != "test"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or "%" in value
        or "\\" in value
        or any(p in {".", ".."} for p in parsed.path.split("/"))
    ):
        _fail(
            "Automatic integration authority only permits explicit test:// destinations."
        )
    return value


def _tool_identity(tool: dict) -> tuple[str, str, str]:
    if not isinstance(tool, dict) or not tool.get("server_id") or not tool.get("name"):
        _fail("Every allowed tool needs its exact server and name.")
    return str(tool["server_id"]), str(tool["name"]), _sha(tool.get("schema_digest"))


class WorkflowIntegrationPolicyService:
    def __init__(self, db_path: str, enabled: bool | None = None) -> None:
        self.repository = WorkflowIntegrationRepository(db_path)
        self.enabled = (
            os.environ.get("WRIGHT_WORKFLOW_INTEGRATION_TESTS") == "1"
            if enabled is None
            else enabled
        )

    def require_enabled(self) -> None:
        if not self.enabled:
            _fail(
                "Integration test execution is disabled on this host.",
                "WORKFLOW_INTEGRATION_DISABLED",
            )

    def enroll(
        self,
        *,
        campaign_id: str,
        dataset_id: str,
        dataset_digest: str,
        workspace_id: str,
        source_path: str,
        source_digest: str,
        input_files: dict[str, str],
        output_root: str,
        allowed_tools: list[dict],
        approval_mode: str = "manual",
        test_destinations=(),
        expires_at: int | None = None,
    ) -> str:
        """Trusted offline management only; never call with a public request body."""
        self.require_enabled()
        for value in (campaign_id, dataset_id, workspace_id):
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                _fail("Campaign, dataset and workspace identities are required.")
        if approval_mode not in {"manual", "auto"}:
            _fail("Approval mode must be manual or auto.")
        if not isinstance(input_files, dict) or not input_files:
            _fail("An integration grant must bind its staged input files.")
        inputs = {_path(p): _sha(h) for p, h in input_files.items()}
        output_root, source_path = _path(output_root), _path(source_path)
        if source_path in inputs:
            _fail("The definition and staged input files must have distinct paths.")
        if any(
            p == output_root or p.startswith(output_root + "/")
            for p in [source_path, *inputs]
        ):
            _fail("Inputs and source cannot occupy the run output root.")
        identities = sorted({_tool_identity(t) for t in allowed_tools})
        now = int(time.time())
        if expires_at is not None and (
            type(expires_at) is not int or expires_at <= now
        ):
            _fail("Grant expiration must be in the future.")
        document = {
            "schema_version": 1,
            "campaign_id": campaign_id,
            "dataset_id": dataset_id,
            "dataset_digest": _sha(dataset_digest),
            "workspace_id": workspace_id,
            "source_path": source_path,
            "source_digest": _sha(source_digest),
            "input_files": inputs,
            "output_root": output_root,
            "allowed_tools": [
                dict(zip(("server_id", "name", "schema_digest"), t)) for t in identities
            ],
            "approval_mode": approval_mode,
            "test_destinations": sorted({_test_uri(t) for t in test_destinations}),
            "created_at": now,
            "expires_at": expires_at,
        }
        policy_digest = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
        self.repository.enroll(policy_digest, document)
        return policy_digest

    def get(self, policy_digest: str) -> dict:
        self.require_enabled()
        row = self.repository.get(_sha(policy_digest))
        if row is None:
            _fail("No locally enrolled integration grant has this identity.")
        grant = row["document"]
        if hashlib.sha256(canonical_json_bytes(grant)).hexdigest() != policy_digest:
            _fail("Stored integration authority failed its immutable identity check.")
        if row["revoked_at"] is not None:
            _fail("Integration authority was revoked.")
        if grant["expires_at"] is not None and grant["expires_at"] <= time.time():
            _fail("Integration authority expired.")
        return {**grant, "integration_policy_digest": policy_digest}

    def revoke(self, policy_digest: str) -> None:
        self.get(policy_digest)
        self.repository.revoke(policy_digest, int(time.time()))

    @staticmethod
    def _action(grant: dict, action: dict) -> None:
        kind = action.get("action_kind", action.get("action", {}).get("kind"))
        if kind == "local_review":
            if (
                action.get("binding") != LOCAL_REVIEW_BINDING
                or action.get("destination") != LOCAL_REVIEW_DESTINATION
                or action.get("action", {}).get("kind") != "local_review"
                or action.get("action", {}).get("mode") != "review_only"
            ):
                _fail(
                    "Local review authority must bind Wright's fixed review-only operation."
                )
            return
        if kind not in {
            "printer_transfer",
            "supplier_upload_preview",
            "cart_quote_handoff",
        }:
            _fail("This external action is outside integration authority.")
        if action.get("action", {}).get("kind") != kind:
            _fail("The checkpoint and proposed action kinds do not match.")
        destination = action.get("destination", {}).get("id")
        if _test_uri(destination) not in grant["test_destinations"]:
            _fail("The exact test destination was not enrolled.")
        if action.get("binding") != TEST_HANDOFF_BINDING:
            _fail("Integration handoffs must bind Wright's fixed transport simulator.")
        receipt_path = _path(action.get("settings", {}).get("receipt_path"))
        if not receipt_path.startswith(grant["output_root"] + "/"):
            _fail(
                "The simulated handoff receipt must stay inside the enrolled output root."
            )

    async def authorize(
        self,
        policy_digest: str,
        *,
        workspace_id: str,
        workspace_dir: str,
        source_path: str,
        source_digest: str,
        plan,
        tool_runtime,
        files,
    ) -> dict:
        grant = self.get(policy_digest)
        if (
            grant["workspace_id"] != workspace_id
            or grant["source_path"] != source_path
            or grant["source_digest"] != source_digest
            or plan.definition_digest != source_digest
        ):
            _fail(
                "Integration authority does not match this workspace and exact definition."
            )
        paths = WorkspacePath(workspace_dir)
        try:
            for path, expected in {
                source_path: source_digest,
                **grant["input_files"],
            }.items():
                paths.resolve(path, must_exist=True)
                data = await files.read_reference(workspace_dir, path)
                if hashlib.sha256(data).hexdigest() != expected:
                    _fail("A source or staged input changed after enrollment.")
            root = paths.resolve(grant["output_root"])
            for fields in plan.inputs.values():
                settings = fields.get("settings", {})
                bound_file = settings.get("workspace_file")
                if bound_file and bound_file not in grant["input_files"]:
                    _fail("A canonical input file is not bound by the grant.")
                text = settings.get("input_text")
                if not bound_file and (not isinstance(text, str) or not text.strip()):
                    _fail(
                        "Every canonical input must have actual text or an enrolled file."
                    )
            allowed = {_tool_identity(t) for t in grant["allowed_tools"]}
            available = (
                {_tool_identity(t) for t in tool_runtime.available()}
                if tool_runtime
                else set()
            )
            if not allowed.issubset(available):
                _fail("An enrolled tool is unavailable or its schema changed.")
            for step in plan.steps:
                if (
                    step.tool_name
                    and (step.server_id, step.tool_name, step.schema_digest)
                    not in allowed
                ):
                    _fail(
                        "A canonical operation is not bound to an enrolled exact tool."
                    )
                if step.agent_task and not any(t[0] == step.server_id for t in allowed):
                    _fail("Agent tool execution requires an enrolled server tool set.")
                outputs = ([step.output_path] if step.save else []) + list(
                    step.expected_files
                )
                for config in (step.cad, step.application):
                    if config:
                        outputs += [
                            config[k]
                            for k in ("native_path", "copy_path", "output_path")
                            if config.get(k)
                        ]
                        outputs += [
                            e.get("path", e.get("name"))
                            for e in config.get("exports", [])
                            if e.get("path") or e.get("name")
                        ]
                for path in outputs:
                    target = paths.resolve(_path(path))
                    if target == root or not target.is_relative_to(root):
                        _fail(
                            "Every saved or expected output must be inside the enrolled output root."
                        )
                if step.external_action:
                    self._action(grant, step.external_action)
                    receipt = step.external_action.get("settings", {}).get(
                        "receipt_path"
                    )
                    if receipt:
                        target = paths.resolve(receipt)
                        if not target.is_relative_to(root) or target == root:
                            _fail(
                                "The simulated receipt path must stay inside the enrolled output root."
                            )
        except (OSError, ValueError, TypeError) as error:
            _fail(
                f"Integration input or output preparation failed: {type(error).__name__}."
            )
        return {
            **grant,
            "actor": f"integration_test:{grant['campaign_id']}",
            "execution_kind": "integration",
        }

    def authorize_decision(
        self,
        policy_digest: str,
        *,
        workspace_id: str,
        checkpoint,
        expected_subject_digest: str,
    ) -> dict:
        """Derive automatic actor; exact artifact/source re-read remains mandatory in resume."""
        from .workflow_external_actions import approval_subject_digest

        grant = self.get(policy_digest)
        if grant["approval_mode"] != "auto":
            _fail("Manual campaign approval requires the workspace user's decision.")
        subject = checkpoint.subject
        context = checkpoint.continuation.get("execution_context", {})
        if (
            workspace_id != grant["workspace_id"]
            or checkpoint.workspace_id != workspace_id
            or checkpoint.subject_digest != expected_subject_digest
            or approval_subject_digest(subject) != expected_subject_digest
            or subject.get("definition_digest") != grant["source_digest"]
            or context.get("integration_policy_digest") != policy_digest
            or context.get("dataset_digest") != grant["dataset_digest"]
            or context.get("dataset_id") != grant["dataset_id"]
            or context.get("campaign_id") != grant["campaign_id"]
        ):
            _fail("The checkpoint does not match the exact enrolled run subject.")
        if checkpoint.expires_at is not None and checkpoint.expires_at <= time.time():
            _fail("The checkpoint expired.")
        for item in checkpoint.continuation.get("input_files", []):
            if grant["input_files"].get(item.get("path")) != item.get("sha256"):
                _fail("Checkpoint inputs do not match the enrolled dataset.")
        self._action(grant, {**subject, "action_kind": checkpoint.action_kind})
        return {
            **grant,
            "actor": f"integration_test:{grant['campaign_id']}",
            "reason": f"Integration campaign {grant['campaign_id']} policy {policy_digest}",
        }
