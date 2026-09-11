"""CAD document identity and verified deliverables for workspace MCP tasks."""

from dataclasses import dataclass, replace
from pathlib import Path
import asyncio
import json

from .workflow_source_execution import _error, _invalid, _safe_path
from .workflow_references import snapshot_task_files, verify_task_files
from .workspace_path import WorkspacePath
from .workflow_results import (
    EngineeringResult,
    Representation,
    Provenance,
    InputRequirement,
    validate_result_input,
    file_representation,
    file_result,
)


@dataclass(frozen=True)
class CadDocument:
    server_id: str
    document: dict
    result: EngineeringResult | None = None


def _require(condition):
    if not condition:
        raise ValueError("Invalid CAD configuration")


def parse_cad(raw, *, terminal):
    if not raw:
        return None
    try:
        value = json.loads(raw)
        _require(isinstance(value, dict))
        _require(value.get("source") in {"new", "workspace", "session", "upstream"})
        _require(value.get("edit_mode", "in_place") in {"in_place", "copy"})
        _require(type(value.get("save_native", True)) is bool)
        _require(value.get("policy", "indexed") in {"indexed", "overwrite"})
        _require(
            isinstance(value.get("exports", []), list)
            and len(value.get("exports", [])) <= 12
        )
        for export in value.get("exports", []):
            _require(
                isinstance(export, dict)
                and isinstance(export.get("format"), str)
                and export["format"]
            )
            _safe_path(export.get("path"))
            _require(export.get("policy", "indexed") in {"indexed", "overwrite"})
        if value["source"] == "workspace":
            _safe_path(value.get("file"))
        if value["source"] == "session":
            _require(isinstance(value.get("document_id"), str) and value["document_id"])
        if value["source"] == "upstream":
            _require(isinstance(value.get("from_port"), str) and value["from_port"])
        if value.get("save_native", True) or value["source"] == "new":
            _safe_path(value.get("native_path"))
        if value.get("edit_mode") == "copy" and value["source"] != "new":
            _safe_path(value.get("copy_path"))
        if terminal and not value.get("save_native", True) and not value.get("exports"):
            raise _invalid(
                "The final CAD step needs a saved model or an export.",
                "Select Save native model or add an export.",
            )
        return value
    except (ValueError, TypeError, AssertionError, KeyError):
        raise _invalid(
            "The CAD model or output settings are incomplete.",
            "Choose a model, workspace filenames and export formats.",
        ) from None


def unpack(value):
    # MCP SDKs wrap array results under result; tolerate either standard shape.
    if isinstance(value, dict) and "result" in value:
        return value["result"]
    return value


async def cad_call(runtime, step, name, arguments):
    from .workflow_mcp_execution import schema_digest

    tool = next((t for t in runtime.task_tools(step) if t.tool_name == name), None)
    if tool is None:
        raise _invalid(
            f"{step.title}: the server does not expose {name}.",
            "Enable a server configuration supporting this CAD operation.",
        )
    invocation = replace(
        step, tool_name=tool.name, schema_digest=schema_digest(tool), agent_task=False
    )
    runtime.validate(invocation, arguments, tool.input_schema)
    value, text = await runtime.call(invocation, arguments)
    value = unpack(value)
    if isinstance(value, dict) and (
        value.get("isSuccess") is False or value.get("isValid") is False
    ):
        raise _invalid(
            f"{step.title}: {name} did not succeed.",
            "Inspect the CAD tool result before retrying.",
        )
    return value, {
        "tool": tool.name,
        "arguments": arguments,
        "status": "succeeded",
        "result": value,
        "text": text,
    }


async def capabilities(runtime, step):
    names = {t.tool_name for t in runtime.task_tools(step)}
    if "cad.list_providers" not in names:
        return {"supported": False, "formats": [], "documents": []}
    providers, _ = await cad_call(runtime, step, "cad.list_providers", {})
    if isinstance(providers, dict):
        providers = providers.get("providers", [])
    provider = next(
        (p for p in providers if p.get("isDefault") and p.get("providerId") != "fake"),
        None,
    )
    if not provider:
        raise _invalid(
            "Select a real CAD provider; the fake provider cannot supply engineering models."
        )
    caps = provider.get("capabilities", {})
    formats = caps.get("exports", [])
    return {
        "supported": True,
        "provider_id": provider["providerId"],
        "provider_name": provider.get("displayName"),
        "formats": formats,
        "can_list": "cad.list_documents" in names,
        "can_open": "cad.open_document" in names,
        "can_save": "cad.save_document" in names,
        "can_create": any(n.startswith("cad.create_") for n in names),
    }


async def list_documents(runtime, step):
    caps = await capabilities(runtime, step)
    documents, _ = await cad_call(
        runtime, step, "cad.list_documents", {"providerId": caps["provider_id"]}
    )
    if isinstance(documents, dict):
        documents = documents.get("documents", [])
    return documents


class CadTask:
    def __init__(self, runtime, step, workspace_dir, responses, emit):
        self.runtime, self.step, self.root, self.responses, self.emit = (
            runtime,
            step,
            workspace_dir,
            responses,
            emit,
        )
        self.config = step.cad
        self.document = None
        self.records, self.outputs = [], []
        self.working_copy = None
        self.input_document = None
        from .workflow_resource_lease import ApplicationLease

        async def waiting():
            await emit(
                "task_progress",
                task_id=step.id,
                task_title=step.title,
                message="Waiting for another workflow to finish using this CAD application.",
            )

        self.lock = ApplicationLease(
            step.server_id, timeout=min(30, step.timeout_seconds), on_wait=waiting
        )

    def allows_tool(self, tool):
        name = tool.tool_name
        if name in {
            "cad.close_document",
            "cad.open_document",
            "cad.save_document",
            "cad.export_document",
            "cad.get_active_document",
        }:
            return False
        # The native model type selects its recipe family. Do not send every
        # unrelated CAD creation schema on every model decision.
        recipe_tools = {
            "cad.create_part_from_recipe",
            "cad.validate_recipe",
            "cad.create_sheet_metal_from_recipe",
            "cad.validate_sheet_metal_recipe",
            "cad.create_assembly_from_recipe",
            "cad.validate_assembly_recipe",
        }
        if name in recipe_tools:
            if name.startswith("cad.validate_"):
                return False  # Run deterministically before creation.
            if self.config["source"] != "new" or self.document is not None:
                return False
            family = {
                ".psm": {
                    "cad.create_sheet_metal_from_recipe",
                    "cad.validate_sheet_metal_recipe",
                },
                ".par": {"cad.create_part_from_recipe", "cad.validate_recipe"},
                ".asm": {
                    "cad.create_assembly_from_recipe",
                    "cad.validate_assembly_recipe",
                },
            }.get(Path(self.config["native_path"]).suffix.lower(), set())
            return name in family
        if name == "cad.connect":
            return self.document is None
        return tool.annotations.get(
            "readOnlyHint", False
        ) or "documentId" in tool.input_schema.get("properties", {})

    async def call(self, name, args):
        value, record = await cad_call(self.runtime, self.step, name, args)
        self.records.append(record)
        await self.emit(
            "tool_completed", task_id=self.step.id, task_title=self.step.title, **record
        )
        return value

    def path(self, relative, policy):
        relative = _safe_path(relative)
        target = WorkspacePath(self.root).resolve(relative)
        if policy == "indexed":
            base = Path(relative)
            for index in range(10000):
                candidate = (
                    relative
                    if index == 0
                    else str(
                        base.with_name(f"{base.stem}-{index:03d}{base.suffix}")
                    ).replace("\\", "/")
                )
                if not WorkspacePath(self.root).resolve(candidate).exists():
                    relative, target = (
                        candidate,
                        WorkspacePath(self.root).resolve(candidate),
                    )
                    break
            else:
                raise _invalid("No free indexed filename remains.")
        target.parent.mkdir(parents=True, exist_ok=True)
        return relative, str(target)

    async def start(self):
        self.caps = await capabilities(self.runtime, self.step)
        if not self.caps["supported"]:
            raise _invalid(
                "The selected server does not provide CAD document operations."
            )
        for export in self.config.get("exports", []):
            if export["format"] not in self.caps["formats"]:
                raise _invalid(
                    f"Export format {export['format']} is unavailable on this CAD server."
                )
        if not self.caps["can_list"]:
            raise _invalid(
                "The CAD server must support listing identified open documents."
            )
        if (
            self.config.get("save_native", True)
            or self.config["source"] == "new"
            or self.config.get("edit_mode") == "copy"
        ) and not self.caps["can_save"]:
            raise _invalid(
                "This server configuration cannot save native models.",
                "Update or enable the server’s native save operation.",
            )
        source = self.config["source"]
        if source == "workspace":
            target = WorkspacePath(self.root).resolve(
                self.config["file"], must_exist=True
            )
            self.document = await self.call(
                "cad.open_document",
                {
                    "path": str(target),
                    "providerId": self.caps["provider_id"],
                    "readOnly": self.config.get("edit_mode") == "copy",
                },
            )
        elif source in {"session", "upstream"}:
            if source == "upstream":
                ref = self.responses.get(self.step.cad_from)
                if (
                    not isinstance(ref, CadDocument)
                    or ref.server_id != self.step.server_id
                ):
                    raise _invalid(
                        "The upstream CAD document belongs to a different server or is unavailable."
                    )
                if ref.result:
                    try:
                        validate_result_input(
                            ref.result,
                            InputRequirement(
                                ("cad_model",),
                                provider_id=f"{self.step.server_id}:{self.caps['provider_id']}",
                            ),
                        )
                    except ValueError as error:
                        raise _invalid(str(error)) from error
                document_id = ref.document["documentId"]
            else:
                document_id = self.config["document_id"]
            documents = await list_documents(self.runtime, self.step)
            self.document = next(
                (d for d in documents if d.get("documentId") == document_id), None
            )
            if not self.document:
                raise _invalid(
                    "The selected CAD document is no longer open.",
                    "Select an open document again or use its saved workspace file.",
                )
            if source == "upstream":
                expected = ref.document.get("revision")
                if expected is not None and expected != self.document.get("revision"):
                    raise _invalid(
                        "The upstream model changed after it was produced.",
                        "Run its producing step again or explicitly select the newer model.",
                    )
        if self.document:
            self.input_document = dict(self.document)
        if self.document and self.config.get("edit_mode") == "copy":
            relative, target = self.path(
                self.config["copy_path"], self.config.get("policy", "indexed")
            )
            self.copy_before = snapshot_task_files(self.root, (relative,))
            result = await self.call(
                "cad.save_document",
                {
                    "providerId": self.caps["provider_id"],
                    "documentId": self.document["documentId"],
                    "outputPath": target,
                    "copy": True,
                    "overwrite": self.config.get("policy") == "overwrite",
                },
            )
            self.document = result["document"]
            verify_task_files(self.root, (relative,))
            self.working_copy = (relative, target)
        self.creation_path = None
        if source == "new":
            self.creation_path = self.path(
                self.config["native_path"], self.config.get("policy", "indexed")
            )
        self.creation_before = (
            snapshot_task_files(self.root, (self.creation_path[0],))
            if self.creation_path
            else {}
        )
        context = {
            "model_source": source,
            "document": self.document,
            "native_creation_path": self.creation_path[1]
            if self.creation_path
            else None,
            "instructions": "Modify only this document. Do not select the active document, close documents, save or export; Wright handles deliverables. For creation keep the new document open (closeAfterSave=false).",
        }
        return "\n\nCAD task target (authoritative):\n" + json.dumps(context)

    def guard(self, tool, arguments):
        name = tool.tool_name
        if not isinstance(arguments, dict):
            raise _invalid("CAD tool arguments must be an object.")
        if arguments.get("providerId") not in {None, self.caps["provider_id"]}:
            raise _invalid("The task attempted to use a different CAD provider.")
        if "providerId" in tool.input_schema.get("properties", {}) or name.startswith(
            "cad.create_"
        ):
            arguments["providerId"] = self.caps["provider_id"]
        if name.startswith("cad.create_"):
            if self.document is not None or self.config["source"] != "new":
                raise _invalid(
                    "This task must modify its selected model, not create a replacement."
                )
            arguments.update(
                outputPath=self.creation_path[1],
                closeAfterSave=False,
                overwrite=self.config.get("policy") == "overwrite",
            )
        elif name in {
            "cad.close_document",
            "cad.open_document",
            "cad.save_document",
            "cad.export_document",
        }:
            raise _invalid(
                "Wright manages CAD document selection and deliverables for this task."
            )
        elif name == "cad.verify_inspection_requirements":
            if not self.document:
                raise _invalid("Create or select the CAD model before inspecting it.")
            request = arguments.get("request")
            if not isinstance(request, dict):
                raise _invalid("CAD inspection requires an inspection request object.")
            selector = request.get("document")
            if selector is None:
                selector = {}
            if not isinstance(selector, dict):
                raise _invalid(
                    "The CAD inspection document selector must be an object."
                )
            if selector.get("documentId") not in {None, self.document["documentId"]}:
                raise _invalid(
                    "The task attempted to inspect a different CAD document."
                )
            request["document"] = {
                **selector,
                "documentId": self.document["documentId"],
                "active": False,
            }
        elif "documentId" in tool.input_schema.get("properties", {}):
            if not self.document:
                raise _invalid("Create the CAD model before attempting to change it.")
            if arguments.get("documentId") not in {None, self.document["documentId"]}:
                raise _invalid("The task attempted to target a different CAD document.")
            arguments["documentId"] = self.document["documentId"]
            if "active" in tool.input_schema.get("properties", {}):
                arguments["active"] = False
        elif name == "cad.connect" and self.document is not None:
            raise _invalid("The task is already bound to an open CAD document.")
        elif not tool.annotations.get("readOnlyHint", False) and name != "cad.connect":
            raise _invalid(
                "This operation cannot be bound to the selected CAD document."
            )
        return arguments

    def observe(self, tool, value):
        value = unpack(value)
        if tool.tool_name.startswith("cad.create_"):
            document = value.get("document") if isinstance(value, dict) else None
            if not document or not document.get("documentId"):
                raise _invalid(
                    "The CAD server did not return the created document identity."
                )
            self.document = document

    async def validate_creation(self, tool, arguments):
        names = {
            "cad.create_sheet_metal_from_recipe": "cad.validate_sheet_metal_recipe",
            "cad.create_part_from_recipe": "cad.validate_recipe",
            "cad.create_assembly_from_recipe": "cad.validate_assembly_recipe",
        }
        if tool.tool_name in names:
            recipe = {**arguments["recipe"], "mode": "preview"}
            await self.call(
                names[tool.tool_name],
                {"providerId": self.caps["provider_id"], "recipe": recipe},
            )

    async def finish(self):
        if not self.document:
            raise _invalid("The CAD task did not produce or modify a document.")
        documents = await list_documents(self.runtime, self.step)
        self.document = next(
            (
                d
                for d in documents
                if d.get("documentId") == self.document["documentId"]
            ),
            None,
        )
        if not self.document:
            raise _invalid(
                "The task document was closed before its results could be collected."
            )
        # Creation tools may save before subsequent feature edits. Save the final
        # in-memory document, not merely the original creation file.
        if (
            self.creation_path
            or self.working_copy
            or self.config.get("save_native", True)
        ):
            relative, target = (
                self.creation_path
                or self.working_copy
                or self.path(
                    self.config["native_path"], self.config.get("policy", "indexed")
                )
            )
            before = (
                self.creation_before
                if self.creation_path
                else self.copy_before
                if self.working_copy
                else snapshot_task_files(self.root, (relative,))
            )
            saved = await self.call(
                "cad.save_document",
                {
                    "providerId": self.caps["provider_id"],
                    "documentId": self.document["documentId"],
                    "outputPath": target,
                    "copy": False,
                    "overwrite": bool(self.creation_path or self.working_copy)
                    or self.config.get("policy") == "overwrite",
                },
            )
            self.document = saved["document"]
            self.outputs.extend(
                {
                    **f,
                    "output_port": self.config.get("native_port"),
                    "cad_role": "native",
                }
                for f in verify_task_files(self.root, (relative,), before)
            )
        before_export = dict(self.document)
        for export in self.config.get("exports", []):
            relative, target = self.path(
                export["path"], export.get("policy", "indexed")
            )
            before = snapshot_task_files(self.root, (relative,))
            export_result = await self.call(
                "cad.export_document",
                {
                    "providerId": self.caps["provider_id"],
                    "documentId": self.document["documentId"],
                    "active": False,
                    "format": export["format"],
                    "outputPath": target,
                    "overwrite": export.get("policy") == "overwrite",
                },
            )
            exported_files = verify_task_files(self.root, (relative,), before)
            if export["format"] == "flat_dxf":
                from .workflow_dxf_verification import verify_flat_dxf

                verification = await asyncio.to_thread(
                    verify_flat_dxf,
                    target,
                    relative_path=relative,
                    native_evidence=export_result.get("flatPatternEvidence")
                    if isinstance(export_result, dict)
                    else None,
                    provider_id=self.caps["provider_id"],
                    document_id=self.document["documentId"],
                )
                if verification["file"].get("sha256") != exported_files[0]["sha256"]:
                    verification["status"] = "fail"
                    verification["errors"].append(
                        {
                            "code": "file_changed",
                            "message": "The DXF changed during export verification.",
                        }
                    )
                report_relative, report_target = self.path(
                    relative + ".verification.json", "indexed"
                )
                Path(report_target).write_text(
                    json.dumps(verification, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                report_file = verify_task_files(self.root, (report_relative,))[0]
                self.records.append(
                    {
                        "kind": "export_verification",
                        "status": verification["status"],
                        "result": verification,
                        "report": report_file,
                    }
                )
                await self.emit(
                    "task_progress",
                    task_id=self.step.id,
                    task_title=self.step.title,
                    message=f"DXF export integrity: {verification['status']}. Report: {report_relative}",
                    export_verification=verification,
                    verification_report=report_file,
                )
                if verification["status"] != "pass":
                    # A failed export is not a downstream result. Its preserved
                    # diagnostic report is still a real file the user can open.
                    await self.emit(
                        "output_saved",
                        task_id=self.step.id,
                        task_title=self.step.title,
                        artifact_role="diagnostic",
                        artifact_title=f"DXF verification report · {verification['status']}",
                        status=verification["status"],
                        **report_file,
                    )
                    issues = verification["errors"] + verification["unverified"]
                    detail = " ".join(issue["message"] for issue in issues[:3])
                    raise _error(
                        "CAD_EXPORT_VERIFICATION_FAILED",
                        f"{self.step.title}: the DXF export is {verification['status']}. {detail}",
                        f"Review {report_relative}. Re-export with explicit length units or matching native flat measurement evidence, and supported closed cut contours, before requesting a quote. The exported DXF has been preserved.",
                    )
                for produced in exported_files:
                    produced["verification"] = verification
                    produced["verification_report"] = report_file
            self.outputs.extend(
                {**f, "output_port": export.get("port"), "cad_role": "export"}
                for f in exported_files
            )
        if self.config.get("exports"):
            # Exports can activate a model/view and mark an open document dirty.
            # Publish its observed state after export, never a pre-export snapshot.
            documents = await list_documents(self.runtime, self.step)
            self.document = next(
                (
                    d
                    for d in documents
                    if d.get("documentId") == before_export["documentId"]
                ),
                None,
            )
            if not self.document:
                raise _invalid(
                    "The task document was closed during export.",
                    "Review the exported files and select the intended model before continuing.",
                )
            if self.document.get("isDirty") and not before_export.get("isDirty"):
                await self.emit(
                    "task_progress",
                    task_id=self.step.id,
                    task_title=self.step.title,
                    message="The CAD application marked the open model modified during export. Its native file was not automatically saved after export.",
                )
        return CadDocument(self.step.server_id, self.document), self.outputs

    def engineering_result(self, run_id):
        """One model, with a live representation and any verified native file."""
        provider = f"{self.step.server_id}:{self.caps['provider_id']}"
        doc = self.document
        model_port = next(
            (p for p, kind in self.step.output_ports if kind == "cad_model"), "model"
        )
        revisions = (
            ((self.input_document["documentId"], self.input_document.get("revision")),)
            if self.input_document
            else ()
        )
        provenance = Provenance(run_id, self.step.id, model_port, revisions)
        representations = [
            Representation(
                "application_document",
                doc["documentId"],
                provider_id=provider,
                resource_id=doc["documentId"],
                revision=doc.get("revision"),
                durability="session",
            )
        ]
        representations.extend(
            file_representation(f) for f in self.outputs if f["cad_role"] == "native"
        )
        # A read/inspect task may retain an unchanged saved representation of
        # the exact upstream document. Never attach a stale file to dirty CAD.
        upstream = self.responses.get(self.step.cad_from)
        if (
            len(representations) == 1
            and doc.get("isDirty") is False
            and isinstance(upstream, CadDocument)
            and upstream.result
            and upstream.document.get("documentId") == doc["documentId"]
        ):
            import hashlib

            for rep in upstream.result.representations:
                if rep.kind != "workspace_file" or not rep.sha256:
                    continue
                try:
                    path = WorkspacePath(self.root).resolve(
                        rep.location, must_exist=True
                    )
                    if (
                        doc.get("fullPath")
                        and Path(doc["fullPath"]).resolve() != path.resolve()
                    ):
                        continue
                    if (
                        path.stat().st_size == rep.size_bytes
                        and hashlib.sha256(path.read_bytes()).hexdigest() == rep.sha256
                    ):
                        representations.append(rep)
                except (OSError, ValueError):
                    pass  # No durable representation is claimed when unavailable.
        exports = tuple(
            file_result(
                f,
                Provenance(
                    run_id,
                    self.step.id,
                    f.get("output_port") or f["output_path"],
                    revisions,
                ),
            )
            for f in self.outputs
            if f["cad_role"] == "export"
        )
        return EngineeringResult(
            f"{run_id}:{self.step.id}:{model_port}",
            "cad_model",
            doc.get("displayName") or self.step.title,
            tuple(representations),
            provenance,
            exports,
        )
