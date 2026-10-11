"""Generate public TS shapes from the actual owning core schemas, never UI copies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from core.process_interfaces import contract_schemas

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "packages/process_client/src"
SUPPORTED = {
    "$ref",
    "type",
    "const",
    "enum",
    "anyOf",
    "oneOf",
    "discriminator",
    "title",
    "description",
    "default",
    "properties",
    "required",
    "additionalProperties",
    "minProperties",
    "maxProperties",
    "items",
    "prefixItems",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
    "pattern",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
}


def check_keywords(schema):
    if not isinstance(schema, dict):
        raise ValueError("Only owning object contract schemas are supported")
    unsupported = set(schema) - SUPPORTED
    if unsupported:
        raise ValueError(
            f"Extend the client validator before generating: {sorted(unsupported)}"
        )
    if (
        "$ref" in schema
        and len(set(schema) - {"$ref", "title", "description", "default"}) > 0
    ):
        raise ValueError(
            "Reference siblings need an explicit client validator extension"
        )
    for value in schema.get("properties", {}).values():
        check_keywords(value)
    for key in ("additionalProperties", "items"):
        if isinstance(schema.get(key), dict):
            check_keywords(schema[key])
    for key in ("anyOf", "oneOf", "prefixItems"):
        for value in schema.get(key, ()):
            check_keywords(value)


def literal(value):
    return json.dumps(value, ensure_ascii=False)


def shape(schema):
    if not schema:
        return "JsonValue"
    if "$ref" in schema:
        value = schema["$ref"]
        if not value.startswith("#/$defs/"):
            raise ValueError("Only shared local contract references are supported")
        return value.removeprefix("#/$defs/")
    if "const" in schema:
        return literal(schema["const"])
    if "enum" in schema:
        return " | ".join(literal(item) for item in schema["enum"])
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            return "(" + " | ".join(shape(item) for item in schema[keyword]) + ")"
    kind = schema.get("type")
    if kind == "array":
        if "prefixItems" in schema:
            return (
                "readonly ["
                + ", ".join(shape(item) for item in schema["prefixItems"])
                + "]"
            )
        return f"ReadonlyArray<{shape(schema.get('items', {}))}>"
    if kind == "object":
        properties = schema.get("properties", {})
        required = set(schema.get("required", ()))
        if properties:
            fields = [
                f"readonly {literal(key)}{'' if key in required else '?'}: {shape(value)};"
                for key, value in sorted(properties.items())
            ]
            if schema.get("additionalProperties") not in (False, None):
                raise ValueError(
                    "Mixed named/open object needs an explicit generator extension"
                )
            return "{\n  " + "\n  ".join(fields) + "\n}"
        additional = schema.get("additionalProperties", {})
        return (
            "Readonly<Record<string, never>>"
            if additional is False
            else f"Readonly<Record<string, {shape(additional if isinstance(additional, dict) else {})}>>"
        )
    if kind in {"string", "boolean", "null"}:
        return kind
    if kind in {"integer", "number"}:
        return "number"
    raise ValueError(f"Unsupported shared schema shape: {schema}")


def generate():
    roots = contract_schemas()
    fixture = json.loads(
        (ROOT / "packages/core/src/core/process_schemas/contracts-v1.json").read_text(
            encoding="utf-8"
        )
    )
    if fixture != roots:
        raise ValueError(
            "Refresh the owning core schema fixture before generating clients"
        )
    schemas = {}
    for name, schema in roots.items():
        for key, value in {
            **schema.get("$defs", {}),
            name: {k: v for k, v in schema.items() if k != "$defs"},
        }.items():
            if not re.fullmatch(r"[A-Za-z_]\w*", key):
                raise ValueError("Contract type names must be TypeScript identifiers")
            if key in schemas and schemas[key] != value:
                raise ValueError(f"Shared schema conflict: {key}")
            check_keywords(value)
            schemas[key] = value
    digest = hashlib.sha256(
        json.dumps(
            roots, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    header = f"// Generated from core.process_interfaces.contract_schemas(). Do not hand edit.\n// Schema SHA-256: {digest}\n"
    declarations = [
        "export type JsonValue = null | boolean | number | string | ReadonlyArray<JsonValue> | { readonly [key: string]: JsonValue };\n"
    ]
    for name, schema in sorted(schemas.items()):
        if name != "JsonValue":
            declarations.append(f"export type {name} = {shape(schema)};\n")
    declarations.append(
        "export type InputBinding = (ValueBinding & { readonly kind: 'value' }) | (FileBinding & { readonly kind: 'file' }) | (OptionBinding & { readonly kind: 'option' });\n"
    )
    declarations.append(
        "export interface ContractTypes {\n"
        + "".join(f"  readonly {name}: {name};\n" for name in sorted(schemas))
        + "}\n"
    )
    declarations.append("export type ContractName = keyof ContractTypes;\n")
    return {
        "contracts.generated.ts": header + "\n".join(declarations),
        "schemas.generated.ts": header
        + "export const contractSchemas: Readonly<Record<string, unknown>> = "
        + json.dumps(schemas, sort_keys=True, indent=2, ensure_ascii=False)
        + ";\n",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for filename, content in generate().items():
        path = TARGET / filename
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Client contract is stale: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Public client contract schemas match core.")


if __name__ == "__main__":
    main()
