"""Authenticate fixed canonical working copies against actual file lineage."""

from __future__ import annotations

from .workflow_integration_document_write import IntegrationDocumentWriteAuthority
from .workflow_integration_policy import _fail, _path
from .workspace_file_copy import COPY_TOOL_NAME
from .workspace_file_inspection import argument_digest
from .workspace_file_identity import workspace_file_sha256
from .workspace_path import WorkspacePath


class IntegrationFileCopyAuthority(IntegrationDocumentWriteAuthority):
    def _guard(self, step, tool, arguments, digest):
        from .workflow_mcp_execution import schema_digest

        current = self.policies.get(self.context["integration_policy_digest"])
        expected = {
            **current,
            "actor": "integration_test:" + current["campaign_id"],
            "execution_kind": "integration",
        }
        if (
            expected != self.context
            or current["workspace_id"] != self.workspace_id
            or current["approval_mode"] != "auto"
        ):
            _fail(
                "Working copies require current immutable automatic integration authority."
            )
        identity = {
            "server_id": tool.server_id,
            "name": tool.name,
            "schema_digest": schema_digest(tool),
        }
        declared = next((item for item in self.plan.steps if item.id == step.id), None)
        if (
            declared != step
            or step.agent_task
            or step.arguments_from
            or step.argument_sources
            or step.tool_name != COPY_TOOL_NAME
            or step.server_id != "wright-workspace-files"
            or tool.name != COPY_TOOL_NAME
            or tool.server_id != step.server_id
            or identity not in current["allowed_tools"]
            or step.schema_digest != identity["schema_digest"]
            or step.arguments != arguments
            or argument_digest(arguments) != digest
        ):
            _fail(
                "Working copy must use its exact fixed canonical operation and enrolled tool/schema."
            )
        source, destination = (
            _path(arguments.get("sourcePath")),
            _path(arguments.get("destinationPath")),
        )
        paths = WorkspacePath(self.workspace_dir)
        target, output = (
            paths.resolve(destination),
            paths.resolve(current["output_root"]),
        )
        if (
            target == output
            or not target.is_relative_to(output)
            or target.exists()
            or step.save
            and step.output_path
            and target == paths.resolve(step.output_path)
        ):
            _fail(
                "Working copy must be a new declared attempt path, separate from its receipt."
            )
        for path, expected_hash in {
            current["source_path"]: current["source_digest"],
            **current["input_files"],
        }.items():
            if workspace_file_sha256(self.workspace_dir, path) != expected_hash:
                _fail("Enrolled source or input changed before working-copy dispatch.")
        if source in current["input_files"]:
            evidence = {
                "sha256": current["input_files"][source],
                "bytes": None,
                "provenance": {
                    "kind": "enrolled_input",
                    "dataset_digest": current["dataset_digest"],
                },
            }
        else:
            original = paths.resolve(source, must_exist=True)
            if original == output or not original.is_relative_to(output):
                _fail("Working-copy source escapes this attempt.")
            evidence = None
            # Only the canonical engine sets this private list from verified
            # results (or its authenticated, restored continuation).
            for result in self.runtime._verified_copy_sources:
                if result.provenance.run_id != self.run_id:
                    continue
                producer = next(
                    (
                        item
                        for item in self.plan.steps
                        if item.id == result.provenance.task_id
                    ),
                    None,
                )
                if producer is None or source not in producer.expected_files:
                    continue
                if self.plan.steps.index(producer) >= self.plan.steps.index(declared):
                    continue
                for representation in result.representations:
                    if (
                        representation.kind == "workspace_file"
                        and representation.location == source
                        and representation.sha256
                        and representation.size_bytes is not None
                    ):
                        evidence = {
                            "sha256": representation.sha256,
                            "bytes": representation.size_bytes,
                            "provenance": {
                                "kind": "verified_run_output",
                                "run_id": self.run_id,
                                "task_id": producer.id,
                                "result_id": result.id,
                            },
                        }
            if evidence is None:
                _fail(
                    "Working-copy source has no verified prior current-run production evidence."
                )
        return source, destination, evidence

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
            _fail("Integration working-copy context changed after run preparation.")
        digest = argument_digest(arguments)
        source, destination, evidence = self._guard(step, tool, arguments, digest)

        def before_dispatch(current_tool):
            if self._guard(step, current_tool, arguments, digest) != (
                source,
                destination,
                evidence,
            ):
                _fail("Working-copy source evidence changed before dispatch.")
            if self.artifacts is None:
                _fail("The private working-copy service is unavailable.")
            self.artifacts.file_copier.grant(
                request_id=request_id,
                session_id=self.runtime.session_id,
                workspace_id=self.workspace_id,
                workspace_path=self.workspace_dir,
                arguments=arguments,
                expected_sha256=evidence["sha256"],
                expected_bytes=evidence["bytes"],
                source_provenance={
                    **evidence["provenance"],
                    "source_digest": context["source_digest"],
                    "run_id": self.run_id,
                    "copy_step_id": step.id,
                },
                policy_digest=context["integration_policy_digest"],
            )

        return {
            "run_id": self.run_id,
            "task_id": step.id,
            "actor": context["actor"],
            "integration_policy_digest": context["integration_policy_digest"],
            "source_digest": context["source_digest"],
            "dataset_digest": context["dataset_digest"],
            "source_path": source,
            "destination_path": destination,
            "source_sha256": evidence["sha256"],
            "source_provenance": evidence["provenance"],
            "arguments_digest": digest,
            "request_id": request_id,
            "tool": tool.name,
            "schema_digest": step.schema_digest,
        }, before_dispatch
