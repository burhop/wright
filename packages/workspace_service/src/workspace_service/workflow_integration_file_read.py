"""Authenticate each integration file observation before private dispatch."""

from __future__ import annotations

from .workflow_integration_document_write import IntegrationDocumentWriteAuthority
from .workflow_integration_policy import _fail, _path
from .workspace_file_inspection import INSPECT_TOOL_NAME, argument_digest
from .workspace_path import WorkspacePath


class IntegrationFileReadAuthority(IntegrationDocumentWriteAuthority):
    def _guard(self, step, tool, arguments, arguments_digest):
        from .workflow_mcp_execution import schema_digest

        current = self.policies.get(self.context["integration_policy_digest"])
        expected = {
            **current,
            "actor": "integration_test:" + current["campaign_id"],
            "execution_kind": "integration",
        }
        if expected != self.context or current["workspace_id"] != self.workspace_id:
            _fail("File observation requires current immutable integration authority.")
        identity = {
            "server_id": tool.server_id,
            "name": tool.name,
            "schema_digest": schema_digest(tool),
        }
        if (
            tool.name != INSPECT_TOOL_NAME
            or tool.server_id != "wright-workspace-files"
            or identity not in current["allowed_tools"]
            or step.server_id != tool.server_id
        ):
            _fail("File observation tool/schema is outside the enrolled authority.")
        if argument_digest(arguments) != arguments_digest:
            _fail("File observation arguments changed after exact-call authorization.")
        relative = _path(arguments.get("relativePath"))
        paths = WorkspacePath(self.workspace_dir)
        # Scope is independent of existence: a model may inspect a declared
        # output before creating it. The inspector checks existence after the
        # audited private dispatch and reports ordinary gateway error semantics.
        target = paths.resolve(relative)
        output = paths.resolve(current["output_root"])
        if relative not in current["input_files"] and (
            target == output or not target.is_relative_to(output)
        ):
            _fail(
                "File observation must name an exact enrolled input or this attempt's output file."
            )
        # Authorize also validates the immutable source and every enrolled input;
        # repeat at dispatch to close audit/revocation/input-change windows.
        import hashlib

        for path, digest in {
            current["source_path"]: current["source_digest"],
            **current["input_files"],
        }.items():
            if (
                hashlib.sha256(
                    paths.resolve(path, must_exist=True).read_bytes()
                ).hexdigest()
                != digest
            ):
                _fail("Enrolled source or input changed before file observation.")
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
            _fail("Integration file observation context changed after run preparation.")
        digest = argument_digest(arguments)
        relative = self._guard(step, tool, arguments, digest)

        def before_dispatch(current_tool):
            self._guard(step, current_tool, arguments, digest)
            if self.artifacts is None:
                _fail("The private workspace file inspector is unavailable.")
            self.artifacts.file_inspector.grant(
                request_id=request_id,
                session_id=self.runtime.session_id,
                workspace_id=self.workspace_id,
                workspace_path=self.workspace_dir,
                arguments=arguments,
                expected_sha256=context["input_files"].get(relative),
                policy_digest=context["integration_policy_digest"],
            )

        return {
            "run_id": self.run_id,
            "task_id": step.id,
            "actor": context["actor"],
            "integration_policy_digest": context["integration_policy_digest"],
            "source_digest": context["source_digest"],
            "dataset_digest": context["dataset_digest"],
            "relative_path": relative,
            "arguments_digest": digest,
            "request_id": request_id,
            "tool": tool.name,
            "schema_digest": step.schema_digest,
        }, before_dispatch
