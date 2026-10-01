import type { ContractName, ContractTypes } from "./contracts.generated";
import { contractSchemas } from "./schemas.generated";
import { clientError } from "./errors";

type Schema = Readonly<Record<string, unknown>>;
const encoder = new TextEncoder();
const inlineBytes = 65_536;

function invalid(path: string): never {
  throw clientError(
    "RESPONSE_INVALID",
    `The process data does not match its supported contract (${path}).`,
    "Refresh the process view. If the problem persists, check client and server versions.",
  );
}

function object(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

/** Reject coercion, cycles, custom toJSON/accessors and non-finite JSON. */
export function checkJson(value: unknown, maxDepth = 40): void {
  const seen = new WeakSet<object>();
  let nodes = 0;
  function walk(item: unknown, level: number): void {
    if (level > maxDepth || ++nodes > 2_000_000) invalid("JSON bounds");
    if (item === null || typeof item === "boolean") return;
    if (typeof item === "string") {
      for (const character of item) {
        const code = character.codePointAt(0)!;
        if (code >= 0xd800 && code <= 0xdfff) invalid("UTF-8 string");
      }
      return;
    }
    if (typeof item === "number") {
      if (!Number.isFinite(item)) invalid("finite number");
      return;
    }
    if (!Array.isArray(item) && !object(item)) invalid("JSON value");
    if (seen.has(item)) invalid("cyclic JSON");
    seen.add(item);
    for (const key of Reflect.ownKeys(item)) {
      if (Array.isArray(item) && key === "length") continue;
      if (typeof key !== "string") invalid("JSON key");
      const descriptor = Object.getOwnPropertyDescriptor(item, key)!;
      if (!("value" in descriptor) || !descriptor.enumerable)
        invalid("JSON property");
      walk(descriptor.value, level + 1);
    }
    // Sparse arrays serialize silently as null. Require actual JSON elements.
    if (Array.isArray(item) && Object.keys(item).length !== item.length)
      invalid("JSON array");
    seen.delete(item);
  }
  walk(value, 0);
}

function inline(value: unknown): void {
  checkJson(value, 24);
  if (encoder.encode(JSON.stringify(value)).byteLength > inlineBytes)
    invalid("inline JSON size");
}

function schemaObject(value: unknown): Schema {
  if (!object(value)) invalid("owning schema");
  return value;
}

function matches(
  schema: Schema,
  value: unknown,
  path: string,
  depth = 0,
): void {
  if (depth > 64) invalid("schema nesting");
  if (Object.keys(schema).length === 0) {
    inline(value);
    return;
  }
  if (typeof schema.$ref === "string") {
    if (!schema.$ref.startsWith("#/$defs/"))
      invalid("local contract reference");
    const target = contractSchemas[schema.$ref.slice(8)];
    if (!target) invalid("known contract reference");
    matches(schemaObject(target), value, path, depth + 1);
    return;
  }
  for (const keyword of ["anyOf", "oneOf"]) {
    const variants = schema[keyword];
    if (!Array.isArray(variants)) continue;
    let accepted = 0;
    for (const variant of variants) {
      try {
        matches(schemaObject(variant), value, path, depth + 1);
        accepted++;
      } catch {
        /* try the other owning union arm */
      }
    }
    if (accepted === 0 || (keyword === "oneOf" && accepted !== 1))
      invalid(path);
    return;
  }
  if ("const" in schema && value !== schema.const) invalid(path);
  if (Array.isArray(schema.enum) && !schema.enum.includes(value)) invalid(path);
  const kind = schema.type;
  if (kind === "null" && value !== null) invalid(path);
  if (kind === "boolean" && typeof value !== "boolean") invalid(path);
  if (kind === "string") {
    if (typeof value !== "string") invalid(path);
    const length = [...value].length;
    if (typeof schema.minLength === "number" && length < schema.minLength)
      invalid(path);
    if (typeof schema.maxLength === "number" && length > schema.maxLength)
      invalid(path);
    // Patterns are fixed owning schemas, never user-supplied executable validators.
    if (
      typeof schema.pattern === "string" &&
      !new RegExp(schema.pattern).test(value)
    )
      invalid(path);
  }
  if (kind === "number" || kind === "integer") {
    if (
      typeof value !== "number" ||
      !Number.isFinite(value) ||
      (kind === "integer" && !Number.isInteger(value))
    )
      invalid(path);
    if (typeof schema.minimum === "number" && value < schema.minimum)
      invalid(path);
    if (typeof schema.maximum === "number" && value > schema.maximum)
      invalid(path);
    if (
      typeof schema.exclusiveMinimum === "number" &&
      value <= schema.exclusiveMinimum
    )
      invalid(path);
    if (
      typeof schema.exclusiveMaximum === "number" &&
      value >= schema.exclusiveMaximum
    )
      invalid(path);
  }
  if (kind === "array") {
    if (!Array.isArray(value)) invalid(path);
    if (typeof schema.minItems === "number" && value.length < schema.minItems)
      invalid(path);
    if (typeof schema.maxItems === "number" && value.length > schema.maxItems)
      invalid(path);
    for (let i = 0; i < value.length; i++) {
      const child =
        Array.isArray(schema.prefixItems) && i < schema.prefixItems.length
          ? schema.prefixItems[i]
          : schema.items;
      if (child === false) invalid(path);
      if (child !== undefined && child !== true)
        matches(schemaObject(child), value[i], `${path}[${i}]`, depth + 1);
    }
  }
  if (kind === "object") {
    if (!object(value)) invalid(path);
    const properties = schema.properties ? schemaObject(schema.properties) : {};
    const keys = Object.keys(value);
    if (
      typeof schema.minProperties === "number" &&
      keys.length < schema.minProperties
    )
      invalid(path);
    if (
      typeof schema.maxProperties === "number" &&
      keys.length > schema.maxProperties
    )
      invalid(path);
    if (Array.isArray(schema.required))
      for (const key of schema.required)
        if (typeof key !== "string" || !Object.hasOwn(value, key))
          invalid(`${path}.${String(key)}`);
    for (const key of keys) {
      if (Object.hasOwn(properties, key))
        matches(
          schemaObject(properties[key]),
          value[key],
          `${path}.${key}`,
          depth + 1,
        );
      else if (schema.additionalProperties === false) invalid(`${path}.${key}`);
      else if (object(schema.additionalProperties))
        matches(
          schema.additionalProperties,
          value[key],
          `${path}.${key}`,
          depth + 1,
        );
    }
  }
}

/** Transport shape validation only. Engineering/currentness authority remains server-side. */
export function assertContract<K extends ContractName>(
  name: K,
  value: unknown,
): ContractTypes[K] {
  checkJson(value);
  matches(schemaObject(contractSchemas[name]), value, name);
  return value as ContractTypes[K];
}

export function identifier(value: string, label: string): string {
  if (
    typeof value !== "string" ||
    value.trim() !== value ||
    value.length < 1 ||
    [...value].length > 160 ||
    /[\x00-\x1f]/.test(value)
  )
    invalid(label);
  return value;
}

export function relativeLocator(value: string): string {
  identifier(value, "relative locator");
  if (
    /[\\:\x00]/.test(value) ||
    value.split("/").some((part) => ["", ".", ".."].includes(part))
  )
    invalid("relative locator");
  return value;
}
