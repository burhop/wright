"""Exact, revocable integration authority for one declared text output call."""

from __future__ import annotations

import copy
import hashlib
import json

from .workflow_integration_policy import _fail, _path
from .workspace_document_artifacts import (
    MAX_DOCUMENT_BYTES,
    WORKSPACE_DOCUMENT_PROVIDER_ID,
    WORKSPACE_DOCUMENT_TOOL_NAME,
    WORKSPACE_WRITE_APPROVAL,
)
from .workspace_path import WorkspacePath


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


class IntegrationDocumentWriteAuthority:
    """Server-created capability; no request/model supplied approval booleans."""

    def __init__(
        self,
        *,
        policies,
        files,
        artifacts,
        runtime,
        context,
        plan,
        workspace_dir,
        workspace_id,
        run_id,
    ):
        self.policies, self.files, self.runtime = policies, files, runtime
        self.artifacts = artifacts
        self.context, self.plan = copy.deepcopy(context), copy.deepcopy(plan)
        self.workspace_dir, self.workspace_id, self.run_id = (
            workspace_dir,
            workspace_id,
            run_id,
        )
        self.declared = {
            step.id: frozenset(step.expected_files) for step in self.plan.steps
        }

    def _guard(self, step, tool, arguments, arguments_digest):
        from .workflow_mcp_execution import schema_digest

        context = self.context
        current = self.policies.get(context["integration_policy_digest"])
        expected = {
            **current,
            "actor": "integration_test:" + current["campaign_id"],
            "execution_kind": "integration",
        }
        if (
            expected != context
            or current["workspace_id"] != self.workspace_id
            or current["approval_mode"] != "auto"
        ):
            _fail(
                "Document writing requires current immutable automatic integration authority."
            )
        identity = {
            "server_id": tool.server_id,
            "name": tool.name,
            "schema_digest": schema_digest(tool),
        }
        if (
            tool.server_id != WORKSPACE_DOCUMENT_PROVIDER_ID
            or tool.name != WORKSPACE_DOCUMENT_TOOL_NAME
            or tool.required_approvals != frozenset({WORKSPACE_WRITE_APPROVAL})
            or identity not in current["allowed_tools"]
            or step.server_id != tool.server_id
        ):
            _fail(
                "This document tool/schema is outside the exact enrolled write authority."
            )
        if _digest(arguments) != arguments_digest:
            _fail("Document arguments changed after exact-call authorization.")
        relative = _path(arguments.get("relativePath"))
        if relative not in self.declared.get(step.id, ()):
            _fail("Document path is not an expected output of this canonical step.")
        paths = WorkspacePath(self.workspace_dir)
        target, output_root = (
            paths.resolve(relative),
            paths.resolve(current["output_root"]),
        )
        if target == output_root or not target.is_relative_to(output_root):
            _fail("Document write escapes the enrolled attempt output root.")
        if arguments.get("overwrite", False) is not False or target.exists():
            _fail(
                "Integration document authority creates a new file only; existing output cannot be overwritten."
            )
        content = arguments.get("content")
        if (
            not isinstance(content, str)
            or not content
            or not 0 < len(content.encode("utf-8")) <= MAX_DOCUMENT_BYTES
        ):
            _fail("Document content must be bounded nonempty UTF-8 text.")
        # The final gateway callback rechecks authority and immutable source/input
        # bytes after the audit event is durable and immediately before dispatch.
        for path, expected_hash in {
            current["source_path"]: current["source_digest"],
            **current["input_files"],
        }.items():
            actual = paths.resolve(path, must_exist=True).read_bytes()
            if hashlib.sha256(actual).hexdigest() != expected_hash:
                _fail("An enrolled input or source changed before document dispatch.")
        return relative

    async def prepare(self, step, tool, arguments, *, request_id):
        context = await self.policies.authorize(
            self.context["integration_policy_digest"],
            workspace_id=self.workspace_id,
            workspace_dir=self.workspace_dir,
            source_path=self.context["source_path"],
            source_digest=self.context["source_digest"],
            plan=self.plan,
            tool_runtime=self.runtime,
            files=self.files,
        )
        if context != self.context:
            _fail("Integration document context changed after run preparation.")
        identity = _digest(arguments)
        relative = self._guard(step, tool, arguments, identity)

        def before_dispatch(current_tool):
            self._guard(step, current_tool, arguments, identity)
            if relative.endswith(".py"):
                if self.artifacts is None:
                    _fail("The private integration source publisher is unavailable.")
                self.artifacts._grant_integration_source_write(
                    request_id=request_id,
                    session_id=self.runtime.session_id,
                    workspace_id=self.workspace_id,
                    relative_path=relative,
                    content_sha256=hashlib.sha256(
                        arguments["content"].encode()
                    ).hexdigest(),
                    policy_digest=context["integration_policy_digest"],
                    actor=context["actor"],
                )

        return {
            "run_id": self.run_id,
            "task_id": step.id,
            "actor": context["actor"],
            "integration_policy_digest": context["integration_policy_digest"],
            "source_digest": context["source_digest"],
            "dataset_digest": context["dataset_digest"],
            "tool": tool.name,
            "schema_digest": step.schema_digest,
            "request_id": request_id,
            "approval": WORKSPACE_WRITE_APPROVAL,
            "relative_path": relative,
            "arguments_digest": identity,
            "content_sha256": hashlib.sha256(arguments["content"].encode()).hexdigest(),
            "content_bytes": len(arguments["content"].encode()),
            "media_type": arguments["mediaType"],
        }, before_dispatch


def bind_integration_document_writes(
    *, service, runtime, context, plan, workspace_dir, workspace_id, run_id
):
    """Called only after normal initial/resume policy authentication succeeds."""
    if runtime is not None and context is not None:
        if runtime._integration_document_write_authority is not None:
            _fail("An active runtime cannot change its document-write authority.")
        runtime._integration_document_write_authority = (
            IntegrationDocumentWriteAuthority(
                policies=service.workflow_integration_policies,
                files=service.files,
                artifacts=getattr(service, "workspace_document_artifacts", None),
                runtime=runtime,
                context=context,
                plan=plan,
                workspace_dir=workspace_dir,
                workspace_id=workspace_id,
                run_id=run_id,
            )
        )
        from .workflow_integration_file_read import IntegrationFileReadAuthority

        runtime._integration_file_read_authority = IntegrationFileReadAuthority(
            policies=service.workflow_integration_policies,
            files=service.files,
            artifacts=getattr(service, "workspace_document_artifacts", None),
            runtime=runtime,
            context=context,
            plan=plan,
            workspace_dir=workspace_dir,
            workspace_id=workspace_id,
            run_id=run_id,
        )

        from .workflow_integration_file_copy import IntegrationFileCopyAuthority

        runtime._integration_file_copy_authority = IntegrationFileCopyAuthority(
            policies=service.workflow_integration_policies,
            files=service.files,
            artifacts=getattr(service, "workspace_document_artifacts", None),
            runtime=runtime,
            context=context,
            plan=plan,
            workspace_dir=workspace_dir,
            workspace_id=workspace_id,
            run_id=run_id,
        )
