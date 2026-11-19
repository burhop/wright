"""Wire schema validation shared by declared responses and optional UI manifests."""

from __future__ import annotations

from typing import Annotated, Literal

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import (
    AfterValidator,
    JsonValue,
    StringConstraints,
    model_validator,
)

from .contracts import Contract, Digest, Identifier, canonical_json

ResultIdentifier = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=482)
]


Text = Annotated[str, StringConstraints(min_length=1, max_length=8192)]


def relative_locator(value: str) -> str:
    if any(c in value for c in ("\\", ":", "\x00")) or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ValueError("File locator must be a confined workspace-relative path")
    return value


INTERACTION_VERSION = "wright.process-interaction/1"


INLINE_BYTES = 65_536

PAGE_ITEMS = 256


MAX_JSON_DEPTH = 24


def checked_json(value: JsonValue) -> JsonValue:
    if len(canonical_json(value).encode("utf-8")) > INLINE_BYTES:
        raise ValueError("Inline JSON exceeds 64 KiB; use an artifact reference")

    def depth(item, level=0):
        if level > MAX_JSON_DEPTH:
            raise ValueError("JSON nesting exceeds the supported bound")
        if isinstance(item, dict):
            for child in item.values():
                depth(child, level + 1)
        elif isinstance(item, list):
            for child in item:
                depth(child, level + 1)

    depth(value)
    return value


Locator = Annotated[Identifier, AfterValidator(relative_locator)]


InlineJSON = Annotated[JsonValue, AfterValidator(checked_json)]


def checked_file_locator(value: str) -> str:
    # A file path is not a single identifier. Preserve its exact spelling while
    # rejecting ambiguous whitespace/control characters before confinement checks.
    if value.strip() != value or any(
        ord(char) < 32 or ord(char) == 127 for char in value
    ):
        raise ValueError(
            "File locator cannot contain surrounding whitespace or controls"
        )
    return relative_locator(value)


FileLocator = Annotated[Text, AfterValidator(checked_file_locator)]


ProcessCapability = Literal[
    "process.read",
    "process.inputs",
    "process.start",
    "process.respond",
    "process.review",
    "process.action",
    "process.cancel",
    "process.results",
    "process.navigate",
]


def checked_value_schema(schema: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Bounded JSON Schema subset with local, acyclic definitions only.

    Unsupported keywords fail explicitly. Arbitrary regular expressions and
    remote references are outside v1; validation cannot execute producer code.
    """
    checked_json(schema)
    allowed = {
        "$schema",
        "$defs",
        "$ref",
        "type",
        "title",
        "description",
        "default",
        "enum",
        "const",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minProperties",
        "maxProperties",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "format",
    }
    if (
        "$schema" in schema
        and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema"
    ):
        raise ValueError("Unsupported value-schema dialect")

    visits = 0

    def walk(node, stack=(), level=0):
        nonlocal visits
        visits += 1
        if visits > 4096:
            raise ValueError("Value-schema expansion exceeds the supported bound")
        if level > MAX_JSON_DEPTH:
            raise ValueError("Value-schema nesting exceeds the supported bound")
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            raise ValueError("A value-schema node must be an object or boolean")
        if unknown := set(node) - allowed:
            raise ValueError(
                f"Unsupported value-schema keywords: {', '.join(sorted(unknown))}"
            )
        if node.get("format") not in {None, "date-time", "date", "time", "uuid"}:
            raise ValueError("Unsupported value-schema format")
        if "$ref" in node:
            ref = node["$ref"]
            if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
                raise ValueError("Value-schema references must name a local definition")
            name = ref[len("#/$defs/") :].replace("~1", "/").replace("~0", "~")
            definitions = schema.get("$defs", {})
            if not isinstance(definitions, dict) or name not in definitions:
                raise ValueError("Value-schema reference does not resolve")
            if ref in stack:
                raise ValueError("Recursive value-schema references are unsupported")
            walk(definitions[name], (*stack, ref), level + 1)
        for key in ("properties", "$defs"):
            entries = node.get(key, {})
            if not isinstance(entries, dict) or len(entries) > PAGE_ITEMS:
                raise ValueError("Value-schema entries must be a bounded object")
            for child in entries.values():
                walk(child, stack, level + 1)
        for key in ("items", "additionalProperties"):
            if key in node:
                walk(node[key], stack, level + 1)

    walk(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_response(schema: dict[str, JsonValue], value: JsonValue) -> None:
    checked_value_schema(schema)
    checked_json(value)
    error = next(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        None,
    )
    if error is not None:
        location = "/".join(str(part) for part in error.absolute_path) or "root"
        raise ValueError(
            f"Response does not match declared {error.validator} at {location}"
        )


def unique_ids(items, field: str) -> None:
    values = [getattr(item, field) for item in items]
    if len(set(values)) != len(values):
        raise ValueError(f"{field} identities must be unique")


class ProcessRef(Contract):
    workspace_id: Identifier
    source_path: Locator
    source_digest: Digest
    semantic_digest: Digest | None = None
    source_contract: Identifier = "canonical-source"


class NavigationTarget(Contract):
    kind: Literal["process", "block", "run", "result", "assessment", "evidence"]
    block_id: Identifier | None = None
    run_id: Identifier | None = None
    result_id: ResultIdentifier | None = None
    assessment_id: Identifier | None = None
    artifact_ref: FileLocator | None = None

    @model_validator(mode="after")
    def exact_destination(self):
        required = {
            "block": "block_id",
            "run": "run_id",
            "result": "result_id",
            "assessment": "assessment_id",
            "evidence": "artifact_ref",
        }.get(self.kind)
        if required and not getattr(self, required):
            raise ValueError(f"{self.kind} navigation requires {required}")
        return self
