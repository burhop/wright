"""Declarative example preparation. Execution remains owned by Wright."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from workspace_service.workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_run_paths import VERSION as RUN_PATH_VERSION, TOKEN as RUN_PATH_TOKEN

REPO = Path(__file__).resolve().parents[2]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def port(key, kind="engineering_document"):
    return dict(
        key=key,
        name=key.replace("_", " "),
        kind=kind,
        item=None,
        required=True,
        quantity="one",
        description="Original input or exact same-run evidence",
    )


class Definition:
    def __init__(self, template, workspace, attempt, tools, *, run_path_template=""):
        if run_path_template not in ("", RUN_PATH_VERSION):
            raise ValueError("Use the supported explicit run-path template version")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", attempt):
            raise ValueError("Use a bounded lowercase attempt identifier")
        self.workspace = Path(workspace).resolve(strict=True)
        self.case = template
        self.attempt = attempt
        self.relative = f"process-proofs/{template}/{attempt}"
        self.root = self.workspace / self.relative
        if self.root.exists():
            raise ValueError(
                "Choose a fresh attempt; existing proof bytes are retained"
            )
        self.run_path_template = run_path_template
        self.output_root = self.relative + "/outputs"
        self.output = self.output_root + ("/" + RUN_PATH_TOKEN if run_path_template else "")
        self.input_root = self.relative + "/inputs"
        self.suffix = attempt.replace("-", "_")
        self.tools = tools
        template_path = (
            REPO
            / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates"
            / (template + ".workflow.wflow")
        )
        self.template_bytes = template_path.read_bytes()
        self.sections = _parse(
            self.template_bytes.decode().replace("__instance__", self.suffix)
        )
        self.staged = []
        self.used_tools = {}
        self.root.mkdir(parents=True)
        (self.workspace / self.output_root).mkdir()

    def original(self, name):
        matches = [
            item for item in self.sections if item["id"] == name + "_" + self.suffix
        ]
        if len(matches) != 1:
            raise ValueError("Original stage absent or ambiguous: " + name)
        return matches[0]

    def stage(self, name, title):
        value = dict(
            kind="task",
            id=name + "_" + self.suffix,
            fields=dict(
                name=title,
                purpose=title,
                step_type="work",
                group=None,
                performed_by="configured_tool",
                inputs=[],
                outputs=[],
                settings={},
                tool=None,
                reusable_step=None,
            ),
        )
        self.sections.append(value)
        return value

    def input_bytes(
        self, name, data, *, original=None, kind="engineering_document", title=None,
        run_paths=False,
    ):
        if type(run_paths) is not bool or (run_paths and not self.run_path_template):
            raise ValueError("Declare the supported run-path version before templating configuration text")
        if run_paths and kind != "engineering_document":
            raise ValueError("Only explicit configuration text can be a run-path template")
        relative = self.input_root + "/" + name
        write_new(self.workspace / relative, data)
        self.staged.append(dict(path=relative, sha256=sha(data), original=original))
        identity = (
            "input_" + re.sub(r"[^a-z0-9_]", "_", name.lower()) + "_" + self.suffix
        )
        value = dict(
            kind="input",
            id=identity,
            fields=dict(
                name=title or name,
                purpose="Original supplied requirements or explicitly configured operation",
                step_type="work",
                group=None,
                provided_by="engineer",
                inputs=[],
                outputs=[port(identity + "_out", kind)],
                instructions="Preserve exact supplied bytes and their stated scope.",
                settings={"input_mode": "workspace-file", "workspace_file": relative,
                          **({"run_path_template": self.run_path_template} if run_paths else {})},
                tool=None,
                reusable_step=None,
            ),
        )
        self.sections.append(value)
        return identity + "." + identity + "_out"

    def reference(self, source, target, key, kind="engineering_document"):
        key = re.sub(r"[^a-z0-9_]", "_", key.lower())
        identity = target["id"] + "_" + key
        target["fields"]["inputs"].append(port(identity, kind))
        self.sections.append(
            dict(
                kind="connection",
                id="bind_" + identity,
                fields=dict(
                    type="item",
                    **{"from": source, "to": target["id"] + "." + identity},
                    label="exact input or upstream evidence",
                    when=None,
                ),
            )
        )
        return identity

    def file_outputs(self, step, mapping):
        step["fields"]["outputs"].extend(
            port(role, "workspace_file") for role in mapping
        )
        step["fields"]["settings"].setdefault("expected_file_ports", {}).update(mapping)
        return {role: (step, role, "workspace_file") for role in mapping}

    def select(self, server, local_name):
        matches = [
            item
            for item in self.tools
            if item.get("server_id") == server and item.get("tool_name") == local_name
        ]
        if len(matches) != 1 or not re.fullmatch(
            r"[0-9a-f]{64}", matches[0].get("schema_digest", "")
        ):
            raise ValueError(
                "Export fresh Wright tools with exact binding/schema: "
                + server
                + "/"
                + local_name
            )
        selected = matches[0]
        self.used_tools[(server, selected["name"])] = {
            key: selected[key] for key in ("server_id", "name", "schema_digest")
        }
        return selected

    def ai(
        self,
        step,
        instructions,
        filename,
        *,
        server=None,
        expected=(),
        calls=8,
        format="json",
        timeout=180,
    ):
        fields = step["fields"]
        fields.update(
            step_type="work",
            performed_by="ai_assisted",
            prompt=instructions,
            outputs=[port(step["id"] + "_result")],
        )
        fields.pop("instructions", None)
        fields["settings"] = dict(
            output_format=format,
            save_output=True,
            output_filename=self.output + "/" + filename,
            file_policy="overwrite",
            **({"run_path_template": self.run_path_template} if self.run_path_template else {}),
        )
        if server:
            fields["settings"].update(
                authoring_template="mcp-task",
                mcp_server=server,
                max_tool_calls=calls,
                timeout_seconds=timeout,
                expected_files="\n".join(self.output + "/" + item for item in expected),
                task_guidance="Use only actual selected tools; retain raw failures and observations. Never fabricate files, measurements, reviews or provider approval.",
            )
        return step["id"] + "." + step["id"] + "_result"

    def exact_mcp(self, step, selected, arguments_input, expected, filename):
        fields = step["fields"]
        fields.update(
            step_type="work",
            performed_by="configured_tool",
            prompt="",
            outputs=[port(step["id"] + "_result")],
        )
        fields["settings"] = dict(
            authoring_template="mcp-tool",
            mcp_server=selected["server_id"],
            mcp_tool=selected["name"],
            mcp_schema_digest=selected["schema_digest"],
            mcp_arguments_source="connection",
            mcp_arguments_input=arguments_input,
            mcp_arguments="{}",
            timeout_seconds=180,
            output_format="json",
            save_output=True,
            output_filename=self.output + "/" + filename,
            file_policy="overwrite",
            expected_files="\n".join(self.output + "/" + item for item in expected),
            **({"run_path_template": self.run_path_template} if self.run_path_template else {}),
        )

    def review(self, step, subject, *, profile=None):
        settings = dict(
            authoring_template="external-action-approval",
            action_kind="local_review",
            approval_binding=dict(
                server="wright",
                tool="review_artifacts",
                schema=sha(b"wright.local_review.v1"),
            ),
            approval_destination=dict(kind="local_review", id="workspace"),
            approval_settings={"review_task_id": step["id"]},
            approval_action={"kind": "local_review", "mode": "review_only"},
        )
        if profile:
            settings["approval_settings"]["validation_review"] = profile
        step["fields"].update(
            step_type="review",
            performed_by="engineer",
            instructions=subject,
            settings=settings,
        )

    def validator(self, profile_resource, sources, *, budget=None):
        path = (
            REPO
            / "packages/workspace_service/src/workspace_service/process_validation/profiles"
            / (profile_resource + ".json")
        )
        coverage = json.loads((path.parent / "coverage.json").read_bytes())
        selected = next(
            item["full_profile"]
            for item in coverage["scenarios"]
            if item["scenario_id"] == self.case + "-01"
        )
        step = self.stage("validate_outputs", "Check exact current engineering outputs")
        step["fields"].update(
            prompt="",
            inputs=[
                port("validate_" + role, kind) for role, (_, _, kind) in sources.items()
            ],
            outputs=[port("assessment")],
            settings={
                "authoring_template": "process-validator",
                "output_format": "json",
                "max_revisions": 0,
                "validation": {
                    "profile": {
                        "source": "packaged",
                        "name": profile_resource,
                        "reference": selected["profile_ref"],
                    },
                    "baseline": selected["baseline_ref"],
                    "subjects": {role: "validate_" + role for role in sources},
                },
            },
        )
        if budget is not None:
            step["fields"]["settings"]["validation"]["budget"] = budget
        for role, (producer, key, _) in sources.items():
            self.sections.append(
                dict(
                    kind="connection",
                    id="validate_bind_" + role + "_" + self.suffix,
                    fields=dict(
                        type="item",
                        **{
                            "from": producer["id"] + "." + key,
                            "to": step["id"] + ".validate_" + role,
                        },
                        label="exact current validation subject",
                        when=None,
                    ),
                )
            )
        return step

    def save(self, chain):
        existing_order = {
            (item["fields"]["from"], item["fields"]["to"])
            for item in self.sections
            if item["kind"] == "connection"
            and item["fields"]["type"] == "order"
            and item["fields"].get("when") is None
        }
        for before, after in zip(chain, chain[1:]):
            if (before["id"], after["id"]) in existing_order:
                continue
            self.sections.append(
                dict(
                    kind="connection",
                    id="sequence_" + after["id"],
                    fields=dict(
                        type="order",
                        **{"from": before["id"], "to": after["id"]},
                        label="accepted process order",
                        when=None,
                    ),
                )
            )
        source = (
            "\n\n".join(
                item["kind"]
                + " "
                + item["id"]
                + "\n"
                + "\n".join(
                    "  "
                    + key
                    + ": "
                    + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    for key, value in item["fields"].items()
                )
                + "\nend"
                for item in self.sections
            )
            + "\n"
        )
        validate_workspace_authoring_shape(source)
        plan = compile_prompt_workflow(source)
        # A prepared file is a proposal. Only the normal source service creates
        # accepted workflow revision history and supplies runtime authority.
        relative = (
            self.root.relative_to(self.workspace).as_posix()
            + "/prepared.workflow.wflow"
        )
        accepted_path = (
            "workflows/" + self.case + "-" + self.attempt + ".workflow.wflow"
        )
        write_new(self.workspace / relative, source.encode())
        report = dict(
            schema_version=1,
            feature="083-process-working-interfaces",
            status="prepared_not_executed",
            template_id=self.case,
            attempt=self.attempt,
            source_path=relative,
            accepted_source_path=accepted_path,
            source_acceptance_required=True,
            source_sha256=sha(source.encode()),
            template_source_sha256=sha(self.template_bytes),
            input_files=self.staged,
            output_root=self.output_root,
            **({"run_path_template": self.run_path_template, "output_template": self.output}
               if self.run_path_template else {}),
            tool_allowlist=list(self.used_tools.values()),
            step_count=len(plan.steps),
            physical_dispatch=False,
            approval_policy_not_enrolled=True,
            engineering_acceptance=False,
        )
        write_new(
            self.root / "preparation.json",
            (json.dumps(report, indent=2) + "\n").encode(),
        )
        return report
