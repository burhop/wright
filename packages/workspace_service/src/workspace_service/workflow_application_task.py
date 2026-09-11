"""Application resource adapter for provider-declared engineering tasks.

Providers opt into wright/application metadata. Local CAD retains its existing
adapter; both use the same AI task loop and EngineeringResult contract.
"""

import json
from dataclasses import replace, asdict
from urllib.parse import urlsplit
from .workflow_results import (
    EngineeringResult,
    Representation,
    Provenance,
    InputRequirement,
    validate_result_input,
)
from .workflow_resource_lease import ApplicationLease
from .workflow_source_execution import _invalid


def parse_application(raw):
    if not raw:
        return None
    try:
        config = json.loads(raw)
        if not isinstance(config, dict) or config.get("source") not in {
            "new",
            "resource",
            "upstream",
        }:
            raise ValueError()
        if config.get("edit_mode", "modify") not in {"modify", "copy"}:
            raise ValueError()
        if config["source"] == "resource" and not (
            isinstance(config.get("resource_id"), str) and config["resource_id"].strip()
        ):
            raise ValueError()
        if config.get("revision") is not None and not isinstance(
            config["revision"], str
        ):
            raise ValueError()
        if not isinstance(config.get("output_port", "resource"), str) or not config.get(
            "output_port", "resource"
        ):
            raise ValueError()
        if config["source"] == "upstream" and not config.get("from_port"):
            raise ValueError()
        if (
            not isinstance(config.get("exports", []), list)
            or len(config.get("exports", [])) > 12
        ):
            raise ValueError()
        for ex in config.get("exports", []):
            if not isinstance(ex, dict) or any(
                not isinstance(ex.get(k), str) or not ex[k].strip()
                for k in ("format", "name", "port")
            ):
                raise ValueError()
            if ex.get("policy", "indexed") not in {"indexed", "overwrite"}:
                raise ValueError()
        ports = [ex["port"] for ex in config.get("exports", [])]
        if (
            len(set(ports)) != len(ports)
            or config.get("output_port", "resource") in ports
        ):
            raise ValueError()
        return config
    except (ValueError, TypeError):
        raise _invalid(
            "Choose an application resource and complete its export settings."
        ) from None


def application_profile(runtime, step):
    profiles = [
        t.upstream_meta["wright/application"]
        for t in runtime.task_tools(step)
        if t.upstream_meta.get("wright/application")
    ]
    if not profiles:
        return None
    profile = profiles[0]
    if (
        any(p != profile for p in profiles)
        or not isinstance(profile, dict)
        or profile.get("version") != 1
    ):
        raise _invalid(
            "The application resource adapter is inconsistent or unsupported."
        )
    if profile.get("kind") not in {
        "cad_model",
        "analysis",
        "structured",
        "file",
        "image",
        "text",
    } or not profile.get("provider_id"):
        raise _invalid(
            "The application must declare its engineering result kind and provider identity."
        )
    for field in (
        "create_tools",
        "formats",
        "export_policies",
        "import_formats",
        "import_kinds",
    ):
        if not isinstance(profile.get(field, []), list) or any(
            not isinstance(v, str) or not v for v in profile.get(field, [])
        ):
            raise _invalid(f"The application declared invalid {field}.")
    for role in ("list_tool", "inspect_tool"):
        tool = next(
            (t for t in runtime.task_tools(step) if t.tool_name == profile.get(role)),
            None,
        )
        if tool is None or not tool.annotations.get("readOnlyHint", False):
            raise _invalid(f"The application needs a read-only {role}.")
    if profile.get("import_formats"):
        importer = next(
            (
                t
                for t in runtime.task_tools(step)
                if t.tool_name == profile.get("import_tool")
            ),
            None,
        )
        if importer is None or "source" not in importer.input_schema.get(
            "properties", {}
        ):
            raise _invalid(
                "The application import adapter must accept a typed source representation."
            )
        if any(
            kind not in {"cad_model", "analysis", "structured", "file", "image", "text"}
            for kind in profile.get("import_kinds", [])
        ):
            raise _invalid("The application declared an unsupported import type.")
    path_arg = profile.get("export_path_argument")
    if path_arg is not None:
        exporter = next(
            (
                t
                for t in runtime.task_tools(step)
                if t.tool_name == profile.get("export_tool")
            ),
            None,
        )
        reserved = {
            "format",
            "name",
            "policy",
            profile.get("id_argument", "resource_id"),
            profile.get("revision_argument"),
        }
        if (
            not isinstance(path_arg, str)
            or not path_arg
            or path_arg in reserved
            or exporter is None
            or exporter.input_schema.get("properties", {}).get(path_arg, {}).get("type")
            != "string"
        ):
            raise _invalid(
                "The application workspace export adapter must declare a distinct string path argument."
            )
    return profile


async def application_call(runtime, step, name, arguments, emit=None):
    from .workflow_mcp_execution import schema_digest

    tool = next((t for t in runtime.task_tools(step) if t.tool_name == name), None)
    if tool is None:
        raise _invalid(f"The application operation {name} is unavailable.")
    invocation = replace(
        step, tool_name=tool.name, schema_digest=schema_digest(tool), agent_task=False
    )
    runtime.validate(invocation, arguments, tool.input_schema)
    if emit:
        await emit(
            "tool_started",
            task_id=step.id,
            task_title=step.title,
            tool=name,
            arguments=arguments,
        )
    value, text = await runtime.call(invocation, arguments, on_event=emit)
    record = {
        "tool": tool.name,
        "arguments": arguments,
        "status": "succeeded",
        "result": value,
        "text": text,
    }
    if emit:
        await emit("tool_completed", task_id=step.id, task_title=step.title, **record)
    return value, record


def resource_representation(resource, profile, server):
    if not isinstance(resource, dict) or any(
        not isinstance(resource.get(k), str) or not resource[k].strip()
        for k in ("resource_id", "name")
    ):
        raise _invalid(
            "The application did not return an identified engineering resource."
        )
    if resource.get("revision") is not None and not isinstance(
        resource["revision"], str
    ):
        raise _invalid("The application returned an invalid resource revision.")
    location = resource.get("url")
    kind = "cloud_resource" if location else "application_document"
    if location:
        url = urlsplit(location)
        if (
            url.scheme not in {"https", "http"}
            or not url.hostname
            or url.username
            or url.password
        ):
            raise _invalid("The application returned an invalid resource link.")
    durability = resource.get("durability")
    if durability not in {"persistent", "session", "run"}:
        raise _invalid(
            "The application must declare whether its result is persistent or temporary."
        )
    return Representation(
        kind,
        location or resource["resource_id"],
        resource.get("format", ""),
        provider_id=f"{server}:{profile['provider_id']}",
        resource_id=resource["resource_id"],
        revision=resource.get("revision"),
        durability=durability,
    )


async def application_options(runtime, step, *, resources=False):
    profile = application_profile(runtime, step)
    if not profile:
        return {"supported": False}
    value = {
        "supported": True,
        "name": profile.get("name", profile["provider_id"]),
        "kind": profile["kind"],
        "can_create": bool(profile.get("create_tools")),
        "can_copy": bool(profile.get("copy_tool")),
        "exports_to_workspace": bool(profile.get("export_path_argument")),
        "formats": profile.get("formats", []),
        "export_policies": profile.get("export_policies", []),
        "resources": [],
    }
    value.update(
        import_formats=profile.get("import_formats", []),
        import_kinds=profile.get("import_kinds", [profile["kind"], "file"]),
    )
    if resources:
        items, _ = await application_call(runtime, step, profile["list_tool"], {})
        if not isinstance(items, dict) or not isinstance(items.get("resources"), list):
            raise _invalid("The application returned an invalid resource list.")
        for item in items["resources"]:
            resource_representation(item, profile, step.server_id)
        value["resources"] = items["resources"]
    return value


def validate_application_connection(runtime, step, plan):
    """Reject an unavailable transfer before any producing task mutates data."""
    profile = application_profile(runtime, step)
    if not profile:
        raise _invalid(
            f"{step.title}: the application resource adapter is unavailable."
        )
    if not step.application_from:
        return
    producer_id, port = step.application_from.split(".", 1)
    producer = next(
        (candidate for candidate in plan.steps if candidate.id == producer_id), None
    )
    if producer is None:
        fields = plan.inputs.get(producer_id, {})
        output = next(
            (p for p in fields.get("outputs", []) if p.get("key") == port), {}
        )
        filename = fields.get("settings", {}).get("workspace_file", "")
        from pathlib import PurePosixPath

        format = PurePosixPath(filename).suffix.lstrip(".").lower()
        kind = "image" if output.get("kind") == "reference_images" else "file"
        if (
            output.get("kind") in {"workspace_file", "reference_images"}
            and filename
            and format in profile.get("import_formats", [])
            and kind in profile.get("import_kinds", [profile["kind"], "file"])
        ):
            return
        raise _invalid(
            f"{step.title}: this application cannot import the selected workspace input.",
            "Select a File or Image block with a format and input type supported by this application.",
        )
    if (
        producer.application
        and producer.server_id == step.server_id
        and port == producer.application.get("output_port", "resource")
    ):
        if application_profile(runtime, producer)["kind"] == profile["kind"]:
            return
    config = producer.cad or producer.application or {}
    exported = next(
        (ex for ex in config.get("exports", []) if ex.get("port") == port), None
    )
    if (
        exported
        and exported["format"] in profile.get("import_formats", [])
        and "file" in profile.get("import_kinds", [profile["kind"], "file"])
    ):
        return
    formats = ", ".join(profile.get("import_formats", []))
    raise _invalid(
        f"{step.title}: this connection has no compatible application representation.",
        f"Configure a named {formats} export in {producer.title}, then connect that export."
        if formats
        else "Choose a result from the same application; this server declares no supported file import.",
    )


class ApplicationResourceTask:
    def __init__(self, runtime, step, responses, emit, workspace_dir=None, files=None):
        self.runtime, self.step, self.responses, self.emit = (
            runtime,
            step,
            responses,
            emit,
        )
        self.config = step.application
        self.profile = application_profile(runtime, step)
        if not self.profile:
            raise _invalid(
                "This server does not expose the application resource adapter."
            )
        self.resource = None
        self.input_resource = None
        self.records = []
        self.workspace_dir = workspace_dir
        self.files = files
        self.produced_files = []
        self.lock = ApplicationLease(
            step.server_id, timeout=min(step.timeout_seconds, 30)
        )

    @property
    def id_argument(self):
        return self.profile.get("id_argument", "resource_id")

    async def call(self, name, args):
        value, record = await application_call(
            self.runtime, self.step, name, args, self.emit
        )
        self.records.append(record)
        return value

    async def inspect(self, identity):
        value = await self.call(
            self.profile["inspect_tool"], {self.id_argument: identity}
        )
        resource_representation(value, self.profile, self.step.server_id)
        if value["resource_id"] != identity:
            raise _invalid(
                "The application returned a different resource than the selected one."
            )
        return value

    async def start(self):
        config = self.config
        if config.get("kind", self.profile["kind"]) != self.profile["kind"]:
            raise _invalid(
                "The selected application produces a different result type.",
                "Reselect the application resource controls and review downstream connections before running.",
            )
        for ex in config.get("exports", []):
            if ex["format"] not in self.profile.get(
                "formats", []
            ) or not self.profile.get("export_tool"):
                raise _invalid(
                    f"Export {ex['format']} is unavailable on this application."
                )
            if ex.get("policy", "indexed") not in self.profile.get(
                "export_policies", []
            ):
                raise _invalid(
                    "This application does not support the selected export naming policy.",
                    "Choose a supported indexed or overwrite policy; Wright will not guess whether an existing export can be replaced.",
                )
            if self.profile.get("export_path_argument"):
                from .workflow_source_execution import _safe_path

                _safe_path(ex["name"])
                if not self.workspace_dir or self.files is None:
                    raise _invalid(
                        "This application export needs a writable workspace."
                    )
        if config["source"] == "new":
            if not self.profile.get("create_tools"):
                raise _invalid("This application cannot create a new resource.")
        else:
            expected = config.get("revision")
            if config["source"] == "upstream":
                result = self.responses.get(self.step.application_from)
                if not isinstance(result, EngineeringResult):
                    raise _invalid(
                        "Connect an engineering resource from the producing application task."
                    )
                try:
                    (selected,) = validate_result_input(
                        result,
                        InputRequirement(
                            (self.profile["kind"],),
                            provider_id=f"{self.step.server_id}:{self.profile['provider_id']}",
                            representation_kinds=(
                                "application_document",
                                "cloud_resource",
                            ),
                        ),
                    )
                except ValueError:
                    selected = await self.import_result(result)
                    self.resource = await self.inspect(selected["resource_id"])
                    if selected.get("revision") is not None and selected[
                        "revision"
                    ] != self.resource.get("revision"):
                        raise _invalid(
                            "The imported resource changed before the task could use it."
                        )
                    return self.context()
                identity, expected = selected.resource_id, selected.revision
            else:
                identity = config["resource_id"]
            self.resource = await self.inspect(identity)
            if expected is not None and expected != self.resource.get("revision"):
                raise _invalid(
                    "The selected application resource changed.",
                    "Refresh the resource selection and review the new revision before running.",
                )
            self.input_resource = dict(self.resource)
            if config.get("edit_mode") == "copy":
                if not self.profile.get("copy_tool"):
                    raise _invalid(
                        "This application cannot make a working copy or new revision."
                    )
                copied = await self.call(
                    self.profile["copy_tool"],
                    self.revision_arguments({self.id_argument: identity}),
                )
                resource_representation(copied, self.profile, self.step.server_id)
                if copied["resource_id"] == identity and copied.get(
                    "revision"
                ) == self.resource.get("revision"):
                    raise _invalid(
                        "The application did not create a distinct copy or revision."
                    )
                self.resource = copied
        return self.context()

    def context(self):
        return "\n\nSelected application resource (authoritative):\n" + json.dumps(
            {
                "resource": self.resource,
                "mode": self.config["source"],
                "instructions": "Work only on this resource. Wright manages selection, copying, exports and result verification.",
            }
        )

    async def import_result(self, result):
        formats = self.profile.get("import_formats", [])
        if not formats:
            raise _invalid(
                "This application has no compatible direct resource representation.",
                "Choose a resource from the same application. No compatible file import is declared by this server.",
            )
        try:
            (selected,) = validate_result_input(
                result,
                InputRequirement(
                    tuple(
                        self.profile.get("import_kinds", [self.profile["kind"], "file"])
                    ),
                    formats=tuple(formats),
                    persistent=True,
                    representation_kinds=("workspace_file", "cloud_resource"),
                ),
            )
        except ValueError as error:
            raise _invalid(str(error)) from error
        if selected.kind == "workspace_file":
            if not self.workspace_dir or not selected.sha256:
                raise _invalid(
                    "The imported file needs a verified workspace location and content digest."
                )
            import hashlib
            from .workspace_path import WorkspacePath

            path = WorkspacePath(self.workspace_dir).resolve(
                selected.location, must_exist=True
            )
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != selected.sha256:
                raise _invalid(
                    "The exported file changed before import.",
                    "Run its producing step again before importing it.",
                )
        self.input_resource = {
            "resource_id": selected.resource_id or selected.location,
            "revision": selected.revision or selected.sha256,
            "representation": asdict(selected),
        }
        imported = await self.call(
            self.profile["import_tool"], {"source": asdict(selected)}
        )
        resource_representation(imported, self.profile, self.step.server_id)
        # Import creates a receiving-application resource. It never edits the
        # source resource or performs an implicit second copy operation.
        if (
            selected.provider_id
            == f"{self.step.server_id}:{self.profile['provider_id']}"
            and imported["resource_id"] == selected.resource_id
        ):
            raise _invalid(
                "Import did not create a distinct receiving-application resource."
            )
        return imported

    def allows_tool(self, tool):
        if tool.tool_name in {
            self.profile.get(k)
            for k in ("copy_tool", "export_tool", "list_tool", "import_tool")
        }:
            return False
        if tool.tool_name in self.profile.get("create_tools", []):
            return self.config["source"] == "new" and self.resource is None
        return self.id_argument in tool.input_schema.get("properties", {})

    def revision_arguments(self, arguments):
        revision_arg = self.profile.get("revision_argument")
        if revision_arg:
            if not self.resource or self.resource.get("revision") is None:
                raise _invalid(
                    "The selected resource has no revision for a protected operation."
                )
            arguments[revision_arg] = self.resource["revision"]
        return arguments

    def guard(self, tool, arguments):
        if not isinstance(arguments, dict):
            raise _invalid("The application operation needs named arguments.")
        if not self.allows_tool(tool):
            raise _invalid("This operation is managed by the application task.")
        if tool.tool_name in self.profile.get("create_tools", []):
            if self.resource or self.config["source"] != "new":
                raise _invalid(
                    "Modify the selected resource instead of creating a replacement."
                )
            return arguments
        if not self.resource:
            raise _invalid("Create the resource before editing it.")
        if arguments.get(self.id_argument) not in {None, self.resource["resource_id"]}:
            raise _invalid(
                "The task attempted to target a different application resource."
            )
        arguments[self.id_argument] = self.resource["resource_id"]
        if not tool.annotations.get("readOnlyHint", False):
            self.revision_arguments(arguments)
        return arguments

    async def validate_creation(self, tool, arguments):
        pass  # Existing task loop validates the provider's schema.

    def observe(self, tool, value):
        if tool.tool_name in self.profile.get(
            "create_tools", []
        ) or not tool.annotations.get("readOnlyHint", False):
            resource = (
                value.get("resource", value) if isinstance(value, dict) else value
            )
            resource_representation(resource, self.profile, self.step.server_id)
            if (
                self.resource
                and resource["resource_id"] != self.resource["resource_id"]
            ):
                raise _invalid("The application changed a different resource.")
            self.resource = resource

    async def finish(self, run_id):
        if not self.resource:
            raise _invalid("The task produced no application resource.")
        verified = await self.inspect(self.resource["resource_id"])
        if self.resource.get("revision") is not None and self.resource[
            "revision"
        ] != verified.get("revision"):
            raise _invalid(
                "The application resource changed before its result could be collected."
            )
        self.resource = verified
        # Preserve the final provider inspection separately from AI narration.
        # Campaign assertions can inspect quantities against this exact revision.
        self.resource_readback = self.records[-1]
        revisions = (
            ((self.input_resource["resource_id"], self.input_resource.get("revision")),)
            if self.input_resource
            else ()
        )
        port = self.config.get("output_port", "resource")
        provenance = Provenance(run_id, self.step.id, port, revisions)
        exports = []
        for ex in self.config.get("exports", []):
            arguments = self.revision_arguments(
                {
                    self.id_argument: verified["resource_id"],
                    "format": ex["format"],
                    "name": ex["name"],
                    "policy": ex.get("policy", "indexed"),
                }
            )
            if self.profile.get("export_path_argument"):
                representation = await self.export_workspace_file(ex, arguments)
                export_name = representation.location
            else:
                exported = await self.call(self.profile["export_tool"], arguments)
                representation = resource_representation(
                    exported, self.profile, self.step.server_id
                )
                export_name = exported["name"]
            if representation.format != ex["format"]:
                raise _invalid(
                    "The export result format does not match the requested format."
                )
            exports.append(
                EngineeringResult(
                    f"{run_id}:{self.step.id}:{ex['port']}",
                    "file",
                    export_name,
                    (representation,),
                    Provenance(run_id, self.step.id, ex["port"], revisions),
                )
            )
            partial = EngineeringResult(
                f"{run_id}:{self.step.id}:{port}",
                self.profile["kind"],
                verified["name"],
                (resource_representation(verified, self.profile, self.step.server_id),),
                provenance,
                tuple(exports),
            )
            await self.emit(
                "result_ready",
                task_id=self.step.id,
                task_title=self.step.title,
                engineering_result=partial.to_dict(),
            )
        return EngineeringResult(
            f"{run_id}:{self.step.id}:{port}",
            self.profile["kind"],
            verified["name"],
            (resource_representation(verified, self.profile, self.step.server_id),),
            provenance,
            tuple(exports),
        )

    async def export_workspace_file(self, ex, arguments):
        """Stage a provider export, then publish complete bytes with workspace policy."""
        import asyncio
        import hashlib
        import tempfile
        from pathlib import Path
        from .workflow_source_execution import _safe_path

        requested = _safe_path(ex["name"])
        root = Path(self.workspace_dir).resolve(strict=True)
        staging = Path(tempfile.mkdtemp(prefix=".wright-export-", dir=root)).resolve()
        if staging.parent != root:
            raise _invalid("The export staging directory is outside its workspace.")
        staged = staging / Path(requested).name
        try:
            arguments = {**arguments, self.profile["export_path_argument"]: str(staged)}
            exported = await self.call(self.profile["export_tool"], arguments)
            if (
                not isinstance(exported, dict)
                or exported.get("format") != ex["format"]
                or exported.get("isSuccess") is False
            ):
                raise _invalid(
                    "The application did not confirm the requested export format."
                )

            def read():
                if staged.resolve().parent != staging or not staged.is_file():
                    raise ValueError(
                        "The application did not write the requested staged export."
                    )
                with staged.open("rb") as stream:
                    data = stream.read(100 * 1024 * 1024 + 1)
                if not data or len(data) > 100 * 1024 * 1024:
                    raise ValueError("The exported file is empty or exceeds 100 MiB.")
                return data

            try:
                data = await asyncio.to_thread(read)
            except (OSError, ValueError) as error:
                raise _invalid(
                    "The application export could not be verified.", str(error)
                ) from error
            actual = await self.files.write_generated_bytes(
                self.workspace_dir, requested, data, ex.get("policy", "indexed")
            )
        except BaseException:
            # An interrupted provider may still be writing. Preserve its owned
            # staging directory and evidence; do not imply cancellation stopped it.
            await self.emit(
                "task_progress",
                task_id=self.step.id,
                task_title=self.step.title,
                message=f"Export incomplete. Staged files are retained at {staging.name} for inspection; they are not verified results. Check the application before retrying.",
            )
            raise
        else:
            # Remove only the verified staging file. Unexpected auxiliary files
            # remain for inspection rather than being recursively deleted.
            if staging.parent == root and staged.resolve().parent == staging:
                try:
                    staged.unlink()
                    staging.rmdir()
                except OSError:
                    await self.emit(
                        "task_progress",
                        task_id=self.step.id,
                        task_title=self.step.title,
                        message=f"Export published. Additional staging files remain at {staging.name}.",
                    )
        digest = hashlib.sha256(data).hexdigest()
        self.produced_files.append(
            dict(
                output_path=actual,
                output_format=ex["format"],
                output_bytes=len(data),
                sha256=digest,
                output_port=ex["port"],
            )
        )
        return Representation(
            "workspace_file",
            actual,
            ex["format"],
            durability="persistent",
            sha256=digest,
            size_bytes=len(data),
        )
