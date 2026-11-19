"""Resolve typed inputs and freeze explicitly supplied file bytes for a single run."""

import hashlib
from pathlib import Path

from .artifacts import WorkflowReference
from .bundle import portable_path
from .contracts import canonical_digest
from .interaction_schema import checked_value_schema, validate_response
from .paths import ConfinedDirectory
from .source import _invalid


def prepare_inputs(definition, supplied):
    pending = dict(supplied)
    values, files = {}, {}
    assets = {a.path: a for a in definition.bundle.assets} if definition.bundle else {}
    for section in definition.graph.inputs:
        block = section["id"]
        fields = section["fields"]
        settings = fields["settings"]
        ports = fields["outputs"]
        if len(ports) != 1 or ports[0].get("quantity") != "one" or fields.get("inputs"):
            raise _invalid(f"{block}: this input shape requires a qualified host.")
        source = block + "." + ports[0]["key"]
        meta = settings.get("interaction_input", {})
        if set(settings) - {"interaction_input", "workspace_file"} or not isinstance(
            meta, dict
        ):
            raise _invalid(f"{block}: input settings require a qualified host.")
        if (
            set(meta)
            - {"version", "value_schema", "required", "default", "title", "description"}
            or meta.get("version", 1) != 1
        ):
            raise _invalid(f"{block}: input metadata requires a qualified handler.")
        if block in pending and source in pending:
            raise _invalid(f"{block}: the same input was supplied twice.")
        key = source if source in pending else block
        present = key in pending or "default" in meta
        value = pending.pop(key) if key in pending else meta.get("default")
        if ports[0]["kind"] == "workspace_file":
            location = portable_path(
                settings.get("workspace_file") or f"inputs/{block}"
            )
            if present:
                if not isinstance(value, (Path, dict)) or (
                    isinstance(value, dict) and set(value) != {"path"}
                ):
                    raise _invalid(f"{block}: supply an explicit file reference.")
                if key not in supplied:
                    raise _invalid(
                        f"{block}: a workflow default cannot select a caller file."
                    )
                path = value if isinstance(value, Path) else Path(value["path"])
                with path.open("rb") as stream:
                    data = stream.read(100 * 1024 * 1024 + 1)
            elif location in assets:
                data = assets[location].decoded()
            else:
                raise _invalid(f"{block}: supply the declared file.")
            if not 0 < len(data) <= 100 * 1024 * 1024:
                raise _invalid(f"{block}: file is empty or exceeds 100 MiB.")
            if location in files and files[location] != data:
                raise _invalid(f"{block}: two input revisions occupy the same path.")
            files[location] = data
            values[source] = {
                "kind": "file",
                "path": location,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        else:
            if not present:
                raise _invalid(
                    f"{block}: supply a value or declare an explicit default."
                )
            if "value_schema" in meta:
                validate_response(checked_value_schema(meta["value_schema"]), value)
            values[source] = {
                "kind": "value",
                "value": value,
                "sha256": canonical_digest(value),
            }
    if pending:
        raise _invalid("The input snapshot includes an undeclared block or port.")
    return values, files


def materialize_inputs(root, files):
    root.mkdir(exist_ok=True)
    confined = ConfinedDirectory(root)
    for name, data in files.items():
        target = confined.resolve(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != data:
                raise _invalid(f"Input target {name} already contains different bytes.")
        else:
            with target.open("xb") as stream:
                stream.write(data)


def verify_record(root, address, record):
    if record["kind"] == "value":
        if canonical_digest(record["value"]) != record["sha256"]:
            raise _invalid(f"The recorded value for {address} changed.")
        return record["value"]
    target = ConfinedDirectory(root).resolve(record["path"], must_exist=True)
    with target.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if target.stat().st_size != record["size"] or digest != record["sha256"]:
        raise _invalid(f"The connected file for {address} changed.")
    return WorkflowReference(
        record["path"], digest, file_only=True, size_bytes=record["size"]
    )
