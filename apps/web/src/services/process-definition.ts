import { hostAdapter } from "./host-adapter";

export const PROCESS_DEFINITION_ID = "product-definition-v1" as const;
export const PROCESS_DEFINITION_SCHEMA_VERSION = "1.0.0" as const;
export const PROCESS_DEFINITION_SOURCE_ID =
  "process-definitions/product-definition-v1.json" as const;
export const MAX_PROCESS_DEFINITION_ENVELOPE_BYTES = 1024 * 1024 + 64 * 1024;
export const MAX_PROCESS_DEFINITION_ERROR_BYTES = 16 * 1024;

export interface ProcessDefinitionPhase {
  id: string;
  title: string;
  purpose: string;
  action_ids: string[];
}

export interface ProcessDefinitionAction {
  id: string;
  title: string;
  purpose: string;
  input_port_ids: string[];
  output_port_ids: string[];
  gate_ids: string[];
  feedback_path_ids: string[];
  expected_artifact_ids: string[];
}

export interface ProcessDefinitionPort {
  id: string;
  name: string;
  direction: "input" | "output";
  value_type:
    | "customer-need"
    | "requirement-set"
    | "product-model"
    | "review-decision"
    | "release-package";
  description: string;
  owner_action_id: string;
  source_port_id: string | null;
}

export interface ProcessDefinitionGate {
  id: string;
  title: string;
  condition: string;
  owner_action_id: string;
  pass_target_id: string;
  fail_target_id: string;
}

export interface ProcessDefinitionFeedbackPath {
  id: string;
  from_id: string;
  to_id: string;
  reason: string;
}

export interface ProcessDefinitionArtifact {
  id: string;
  name: string;
  artifact_type:
    | "requirements-baseline"
    | "product-definition"
    | "review-record"
    | "released-definition-package";
  purpose: string;
  produced_by_action_id: string;
}

export interface ProcessDefinition {
  $schema?: "./process-definition.schema.json";
  schema_version: typeof PROCESS_DEFINITION_SCHEMA_VERSION;
  process_id: typeof PROCESS_DEFINITION_ID;
  revision: number | bigint;
  title: string;
  purpose: string;
  content_sha256: string;
  phases: ProcessDefinitionPhase[];
  actions: ProcessDefinitionAction[];
  ports: ProcessDefinitionPort[];
  gates: ProcessDefinitionGate[];
  feedback_paths: ProcessDefinitionFeedbackPath[];
  artifacts: ProcessDefinitionArtifact[];
}

export interface ProcessDefinitionEnvelope {
  definition: ProcessDefinition;
  source_kind: "installed" | "packaged_fallback";
  source_id: typeof PROCESS_DEFINITION_SOURCE_ID;
  source_sha256: string;
  source_available: true;
  etag: string;
  supported_schema_versions: [typeof PROCESS_DEFINITION_SCHEMA_VERSION];
}

export type ProcessDefinitionErrorCode =
  | "PROCESS_DEFINITION_UNAVAILABLE"
  | "PROCESS_DEFINITION_IDENTITY_MISMATCH"
  | "PROCESS_DEFINITION_INVALID"
  | "PROCESS_DEFINITION_UNSUPPORTED_VERSION"
  | "PROCESS_DEFINITION_READ_FAILED";

export type ProcessDefinitionRecoveryClass =
  | "enable_or_reinstall"
  | "reinstall_exact_artifact"
  | "replace_validated_definition"
  | "install_compatible_wright"
  | "inspect_local_data_root";

export interface ProcessDefinitionError {
  error_code: ProcessDefinitionErrorCode;
  message: string;
  recovery_class: ProcessDefinitionRecoveryClass;
  trace_id: string;
  supported_schema_versions?: [typeof PROCESS_DEFINITION_SCHEMA_VERSION];
}

export type ProcessDefinitionFetchResult =
  | {
      state: "current";
      status: 200;
      etag: string;
      envelope: ProcessDefinitionEnvelope;
    }
  | {
      state: "not_modified";
      status: 304;
      etag: string;
      envelope: null;
    };

export class ProcessDefinitionDecodeError extends Error {
  readonly code: string;
  readonly path: string;

  constructor(code: string, path: string) {
    super(`${code} at ${path || "/"}`);
    this.name = "ProcessDefinitionDecodeError";
    this.code = code;
    this.path = path;
  }
}

export class ProcessDefinitionServiceError extends Error {
  readonly status: number;
  readonly detail: ProcessDefinitionError;

  constructor(status: number, detail: ProcessDefinitionError) {
    super(detail.message);
    this.name = "ProcessDefinitionServiceError";
    this.status = status;
    this.detail = detail;
  }
}

class StrictJsonParser {
  private position = 0;
  private readonly source: string;

  constructor(source: string) {
    this.source = source;
  }

  parse(): unknown {
    this.space();
    const value = this.value();
    this.space();
    if (this.position !== this.source.length) this.fail("TRAILING_DATA");
    return value;
  }

  private fail(code: string): never {
    throw new ProcessDefinitionDecodeError(code, `/bytes/${this.position}`);
  }

  private space(): void {
    while (["\t", "\n", "\r", " "].includes(this.source[this.position] ?? "")) {
      this.position += 1;
    }
  }

  private value(): unknown {
    const token = this.source[this.position];
    if (token === "{") return this.object();
    if (token === "[") return this.array();
    if (token === '"') return this.string();
    if (token === "t") return this.literal("true", true);
    if (token === "f") return this.literal("false", false);
    if (token === "n") return this.literal("null", null);
    if (token === "-" || /[0-9]/.test(token ?? "")) return this.integer();
    return this.fail("JSON_VALUE_INVALID");
  }

  private object(): Record<string, unknown> {
    const result = Object.create(null) as Record<string, unknown>;
    const keys = new Set<string>();
    this.position += 1;
    this.space();
    if (this.source[this.position] === "}") {
      this.position += 1;
      return result;
    }
    while (true) {
      if (this.source[this.position] !== '"') this.fail("OBJECT_KEY_INVALID");
      const key = this.string();
      if (keys.has(key)) this.fail("DUPLICATE_OBJECT_KEY");
      keys.add(key);
      this.space();
      if (this.source[this.position] !== ":") this.fail("OBJECT_COLON_MISSING");
      this.position += 1;
      this.space();
      result[key] = this.value();
      this.space();
      if (this.source[this.position] === "}") {
        this.position += 1;
        return result;
      }
      if (this.source[this.position] !== ",") this.fail("OBJECT_COMMA_MISSING");
      this.position += 1;
      this.space();
    }
  }

  private array(): unknown[] {
    const result: unknown[] = [];
    this.position += 1;
    this.space();
    if (this.source[this.position] === "]") {
      this.position += 1;
      return result;
    }
    while (true) {
      result.push(this.value());
      this.space();
      if (this.source[this.position] === "]") {
        this.position += 1;
        return result;
      }
      if (this.source[this.position] !== ",") this.fail("ARRAY_COMMA_MISSING");
      this.position += 1;
      this.space();
    }
  }

  private string(): string {
    this.position += 1;
    let result = "";
    while (this.position < this.source.length) {
      const token = this.source[this.position] ?? "";
      this.position += 1;
      if (token === '"') {
        validateCanonicalText(result, `/bytes/${this.position}`);
        return result;
      }
      if (token.charCodeAt(0) < 0x20) this.fail("STRING_CONTROL_INVALID");
      if (token !== "\\") {
        result += token;
        continue;
      }
      const escaped = this.source[this.position] ?? "";
      this.position += 1;
      const short: Record<string, string> = {
        '"': '"',
        "\\": "\\",
        "/": "/",
        b: "\b",
        f: "\f",
        n: "\n",
        r: "\r",
        t: "\t",
      };
      if (escaped in short) {
        result += short[escaped];
        continue;
      }
      if (escaped !== "u") this.fail("STRING_ESCAPE_INVALID");
      const first = this.hexCodeUnit();
      if (first >= 0xd800 && first <= 0xdbff) {
        if (this.source.slice(this.position, this.position + 2) !== "\\u") {
          this.fail("UNICODE_SURROGATE_INVALID");
        }
        this.position += 2;
        const second = this.hexCodeUnit();
        if (second < 0xdc00 || second > 0xdfff) {
          this.fail("UNICODE_SURROGATE_INVALID");
        }
        result += String.fromCodePoint(
          0x10000 + (first - 0xd800) * 0x400 + second - 0xdc00,
        );
      } else if (first >= 0xdc00 && first <= 0xdfff) {
        this.fail("UNICODE_SURROGATE_INVALID");
      } else {
        result += String.fromCharCode(first);
      }
    }
    return this.fail("STRING_UNTERMINATED");
  }

  private hexCodeUnit(): number {
    const encoded = this.source.slice(this.position, this.position + 4);
    if (!/^[0-9a-fA-F]{4}$/.test(encoded)) this.fail("UNICODE_ESCAPE_INVALID");
    this.position += 4;
    return Number.parseInt(encoded, 16);
  }

  private integer(): number | bigint {
    const start = this.position;
    if (this.source[this.position] === "-") this.position += 1;
    if (this.source[this.position] === "0") {
      this.position += 1;
      if (/[0-9]/.test(this.source[this.position] ?? "")) {
        this.fail("NUMBER_LEADING_ZERO");
      }
    } else if (/[1-9]/.test(this.source[this.position] ?? "")) {
      while (/[0-9]/.test(this.source[this.position] ?? "")) this.position += 1;
    } else {
      return this.fail("NUMBER_INVALID");
    }
    if (/[.eE]/.test(this.source[this.position] ?? "")) {
      this.fail("NUMBER_PROFILE_INVALID");
    }
    const token = this.source.slice(start, this.position);
    if (token === "-0") this.fail("NEGATIVE_ZERO_INVALID");
    const value = Number(token);
    return Number.isSafeInteger(value) ? value : BigInt(token);
  }

  private literal<T>(token: string, value: T): T {
    if (
      this.source.slice(this.position, this.position + token.length) !== token
    ) {
      this.fail("LITERAL_INVALID");
    }
    this.position += token.length;
    return value;
  }
}

export function parseProcessJsonBytes(bytes: Uint8Array): unknown {
  if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    throw new ProcessDefinitionDecodeError("UTF8_BOM_INVALID", "/bytes/0");
  }
  let source: string;
  try {
    source = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new ProcessDefinitionDecodeError("UTF8_INVALID", "/bytes");
  }
  return new StrictJsonParser(source).parse();
}

function validateCanonicalText(value: string, path: string): void {
  if (value.normalize("NFC") !== value) {
    throw new ProcessDefinitionDecodeError("TEXT_NOT_NFC", path);
  }
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (next < 0xdc00 || next > 0xdfff) {
        throw new ProcessDefinitionDecodeError(
          "UNICODE_SURROGATE_INVALID",
          path,
        );
      }
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) {
      throw new ProcessDefinitionDecodeError("UNICODE_SURROGATE_INVALID", path);
    }
  }
}

function canonicalString(value: string, path: string): string {
  validateCanonicalText(value, path);
  let result = '"';
  for (const token of value) {
    const code = token.codePointAt(0) ?? 0;
    if (token === '"') result += '\\"';
    else if (token === "\\") result += "\\\\";
    else if (token === "\b") result += "\\b";
    else if (token === "\t") result += "\\t";
    else if (token === "\n") result += "\\n";
    else if (token === "\f") result += "\\f";
    else if (token === "\r") result += "\\r";
    else if (code < 0x20) result += `\\u${code.toString(16).padStart(4, "0")}`;
    else result += token;
  }
  return `${result}"`;
}

function compareUtf8(left: string, right: string): number {
  const encoder = new TextEncoder();
  const a = encoder.encode(left);
  const b = encoder.encode(right);
  const length = Math.min(a.length, b.length);
  for (let index = 0; index < length; index += 1) {
    if (a[index] !== b[index]) return (a[index] ?? 0) - (b[index] ?? 0);
  }
  return a.length - b.length;
}

export function canonicalProcessJson(value: unknown, path = ""): string {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "string") return canonicalString(value, path);
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || Object.is(value, -0)) {
      throw new ProcessDefinitionDecodeError("CANONICAL_NUMBER_INVALID", path);
    }
    return String(value);
  }
  if (typeof value === "bigint") return value.toString(10);
  if (Array.isArray(value)) {
    return `[${value
      .map((item, index) => canonicalProcessJson(item, `${path}/${index}`))
      .join(",")}]`;
  }
  if (typeof value === "object") {
    const row = value as Record<string, unknown>;
    const keys = Object.keys(row).sort(compareUtf8);
    return `{${keys
      .map(
        (key) =>
          `${canonicalString(key, `${path}/${key}`)}:${canonicalProcessJson(
            row[key],
            `${path}/${key}`,
          )}`,
      )
      .join(",")}}`;
  }
  throw new ProcessDefinitionDecodeError("CANONICAL_VALUE_INVALID", path);
}

export async function canonicalProcessDigest(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalProcessJson(value));
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function objectValue(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ProcessDefinitionDecodeError("EXPECTED_OBJECT", path);
  }
  return value as Record<string, unknown>;
}

function closedObject(
  value: unknown,
  allowed: readonly string[],
  required: readonly string[],
  path: string,
): Record<string, unknown> {
  const row = objectValue(value, path);
  for (const key of required) {
    if (!(key in row)) {
      throw new ProcessDefinitionDecodeError("MISSING_FIELD", `${path}/${key}`);
    }
  }
  for (const key of Object.keys(row)) {
    if (!allowed.includes(key)) {
      throw new ProcessDefinitionDecodeError("UNKNOWN_FIELD", `${path}/${key}`);
    }
  }
  return row;
}

function stringValue(value: unknown, path: string, maximum = 1000): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    [...value].length > maximum
  ) {
    throw new ProcessDefinitionDecodeError("EXPECTED_TEXT", path);
  }
  validateCanonicalText(value, path);
  return value;
}

function enumValue<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  const parsed = stringValue(value, path);
  if (!allowed.includes(parsed as T)) {
    throw new ProcessDefinitionDecodeError("ENUM_INVALID", path);
  }
  return parsed as T;
}

function idValue(value: unknown, path: string): string {
  const parsed = stringValue(value, path, 80);
  if (parsed.length < 3 || !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(parsed)) {
    throw new ProcessDefinitionDecodeError("ID_INVALID", path);
  }
  return parsed;
}

function digest(value: unknown, path: string): string {
  const parsed = stringValue(value, path, 64);
  if (!/^[0-9a-f]{64}$/.test(parsed)) {
    throw new ProcessDefinitionDecodeError("DIGEST_INVALID", path);
  }
  return parsed;
}

function positiveInteger(value: unknown, path: string): number | bigint {
  if (
    (typeof value === "number" && Number.isSafeInteger(value) && value >= 1) ||
    (typeof value === "bigint" && value >= 1n)
  ) {
    return value;
  }
  throw new ProcessDefinitionDecodeError("POSITIVE_INTEGER_REQUIRED", path);
}

function arrayValue(
  value: unknown,
  path: string,
  maximum: number,
  minimum = 0,
): unknown[] {
  if (
    !Array.isArray(value) ||
    value.length < minimum ||
    value.length > maximum
  ) {
    throw new ProcessDefinitionDecodeError("ARRAY_BOUNDS_INVALID", path);
  }
  return value;
}

function idList(value: unknown, path: string, minimum = 0): string[] {
  const parsed = arrayValue(value, path, 100, minimum).map((item, index) =>
    idValue(item, `${path}/${index}`),
  );
  if (new Set(parsed).size !== parsed.length) {
    throw new ProcessDefinitionDecodeError("DUPLICATE_REFERENCE", path);
  }
  return parsed;
}

function phase(value: unknown, path: string): ProcessDefinitionPhase {
  const keys = ["id", "title", "purpose", "action_ids"] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    title: stringValue(row.title, `${path}/title`),
    purpose: stringValue(row.purpose, `${path}/purpose`),
    action_ids: idList(row.action_ids, `${path}/action_ids`, 1),
  };
}

function action(value: unknown, path: string): ProcessDefinitionAction {
  const keys = [
    "id",
    "title",
    "purpose",
    "input_port_ids",
    "output_port_ids",
    "gate_ids",
    "feedback_path_ids",
    "expected_artifact_ids",
  ] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    title: stringValue(row.title, `${path}/title`),
    purpose: stringValue(row.purpose, `${path}/purpose`),
    input_port_ids: idList(row.input_port_ids, `${path}/input_port_ids`),
    output_port_ids: idList(row.output_port_ids, `${path}/output_port_ids`),
    gate_ids: idList(row.gate_ids, `${path}/gate_ids`),
    feedback_path_ids: idList(
      row.feedback_path_ids,
      `${path}/feedback_path_ids`,
    ),
    expected_artifact_ids: idList(
      row.expected_artifact_ids,
      `${path}/expected_artifact_ids`,
    ),
  };
}

function port(value: unknown, path: string): ProcessDefinitionPort {
  const keys = [
    "id",
    "name",
    "direction",
    "value_type",
    "description",
    "owner_action_id",
    "source_port_id",
  ] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    name: stringValue(row.name, `${path}/name`),
    direction: enumValue(
      row.direction,
      ["input", "output"] as const,
      `${path}/direction`,
    ),
    value_type: enumValue(
      row.value_type,
      [
        "customer-need",
        "requirement-set",
        "product-model",
        "review-decision",
        "release-package",
      ] as const,
      `${path}/value_type`,
    ),
    description: stringValue(row.description, `${path}/description`),
    owner_action_id: idValue(row.owner_action_id, `${path}/owner_action_id`),
    source_port_id:
      row.source_port_id === null
        ? null
        : idValue(row.source_port_id, `${path}/source_port_id`),
  };
}

function gate(value: unknown, path: string): ProcessDefinitionGate {
  const keys = [
    "id",
    "title",
    "condition",
    "owner_action_id",
    "pass_target_id",
    "fail_target_id",
  ] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    title: stringValue(row.title, `${path}/title`),
    condition: stringValue(row.condition, `${path}/condition`),
    owner_action_id: idValue(row.owner_action_id, `${path}/owner_action_id`),
    pass_target_id: idValue(row.pass_target_id, `${path}/pass_target_id`),
    fail_target_id: idValue(row.fail_target_id, `${path}/fail_target_id`),
  };
}

function feedbackPath(
  value: unknown,
  path: string,
): ProcessDefinitionFeedbackPath {
  const keys = ["id", "from_id", "to_id", "reason"] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    from_id: idValue(row.from_id, `${path}/from_id`),
    to_id: idValue(row.to_id, `${path}/to_id`),
    reason: stringValue(row.reason, `${path}/reason`),
  };
}

function artifact(value: unknown, path: string): ProcessDefinitionArtifact {
  const keys = [
    "id",
    "name",
    "artifact_type",
    "purpose",
    "produced_by_action_id",
  ] as const;
  const row = closedObject(value, keys, keys, path);
  return {
    id: idValue(row.id, `${path}/id`),
    name: stringValue(row.name, `${path}/name`),
    artifact_type: enumValue(
      row.artifact_type,
      [
        "requirements-baseline",
        "product-definition",
        "review-record",
        "released-definition-package",
      ] as const,
      `${path}/artifact_type`,
    ),
    purpose: stringValue(row.purpose, `${path}/purpose`),
    produced_by_action_id: idValue(
      row.produced_by_action_id,
      `${path}/produced_by_action_id`,
    ),
  };
}

export function decodeProcessDefinition(value: unknown): ProcessDefinition {
  const allowed = [
    "$schema",
    "schema_version",
    "process_id",
    "revision",
    "title",
    "purpose",
    "content_sha256",
    "phases",
    "actions",
    "ports",
    "gates",
    "feedback_paths",
    "artifacts",
  ] as const;
  const required = allowed.filter((key) => key !== "$schema");
  const row = closedObject(value, allowed, required, "/definition");
  const schemaRef = row.$schema;
  if (
    schemaRef !== undefined &&
    schemaRef !== "./process-definition.schema.json"
  ) {
    throw new ProcessDefinitionDecodeError(
      "SCHEMA_REFERENCE_INVALID",
      "/definition/$schema",
    );
  }
  return {
    ...(schemaRef === undefined
      ? {}
      : { $schema: "./process-definition.schema.json" as const }),
    schema_version: enumValue(
      row.schema_version,
      [PROCESS_DEFINITION_SCHEMA_VERSION] as const,
      "/definition/schema_version",
    ),
    process_id: enumValue(
      row.process_id,
      [PROCESS_DEFINITION_ID] as const,
      "/definition/process_id",
    ),
    revision: positiveInteger(row.revision, "/definition/revision"),
    title: stringValue(row.title, "/definition/title"),
    purpose: stringValue(row.purpose, "/definition/purpose"),
    content_sha256: digest(row.content_sha256, "/definition/content_sha256"),
    phases: arrayValue(row.phases, "/definition/phases", 20, 1).map(
      (item, index) => phase(item, `/definition/phases/${index}`),
    ),
    actions: arrayValue(row.actions, "/definition/actions", 100, 1).map(
      (item, index) => action(item, `/definition/actions/${index}`),
    ),
    ports: arrayValue(row.ports, "/definition/ports", 300).map((item, index) =>
      port(item, `/definition/ports/${index}`),
    ),
    gates: arrayValue(row.gates, "/definition/gates", 100).map((item, index) =>
      gate(item, `/definition/gates/${index}`),
    ),
    feedback_paths: arrayValue(
      row.feedback_paths,
      "/definition/feedback_paths",
      100,
    ).map((item, index) =>
      feedbackPath(item, `/definition/feedback_paths/${index}`),
    ),
    artifacts: arrayValue(row.artifacts, "/definition/artifacts", 200).map(
      (item, index) => artifact(item, `/definition/artifacts/${index}`),
    ),
  };
}

export function decodeProcessDefinitionEnvelope(
  value: unknown,
): ProcessDefinitionEnvelope {
  const keys = [
    "definition",
    "source_kind",
    "source_id",
    "source_sha256",
    "source_available",
    "etag",
    "supported_schema_versions",
  ] as const;
  const row = closedObject(value, keys, keys, "");
  const supported = arrayValue(
    row.supported_schema_versions,
    "/supported_schema_versions",
    1,
    1,
  );
  if (supported[0] !== PROCESS_DEFINITION_SCHEMA_VERSION) {
    throw new ProcessDefinitionDecodeError(
      "SUPPORTED_VERSIONS_INVALID",
      "/supported_schema_versions",
    );
  }
  if (row.source_available !== true) {
    throw new ProcessDefinitionDecodeError(
      "SOURCE_AVAILABILITY_INVALID",
      "/source_available",
    );
  }
  return {
    definition: decodeProcessDefinition(row.definition),
    source_kind: enumValue(
      row.source_kind,
      ["installed", "packaged_fallback"] as const,
      "/source_kind",
    ),
    source_id: enumValue(
      row.source_id,
      [PROCESS_DEFINITION_SOURCE_ID] as const,
      "/source_id",
    ),
    source_sha256: digest(row.source_sha256, "/source_sha256"),
    source_available: true,
    etag: digest(row.etag, "/etag"),
    supported_schema_versions: [PROCESS_DEFINITION_SCHEMA_VERSION],
  };
}

export async function verifyProcessDefinitionIdentity(
  envelope: ProcessDefinitionEnvelope,
): Promise<void> {
  const definitionMaterial = { ...envelope.definition };
  delete (definitionMaterial as Partial<ProcessDefinition>).content_sha256;
  if (
    (await canonicalProcessDigest(definitionMaterial)) !==
    envelope.definition.content_sha256
  ) {
    throw new ProcessDefinitionDecodeError(
      "CONTENT_IDENTITY_MISMATCH",
      "/definition/content_sha256",
    );
  }
  const envelopeMaterial = { ...envelope };
  delete (envelopeMaterial as Partial<ProcessDefinitionEnvelope>).etag;
  if ((await canonicalProcessDigest(envelopeMaterial)) !== envelope.etag) {
    throw new ProcessDefinitionDecodeError(
      "ENVELOPE_IDENTITY_MISMATCH",
      "/etag",
    );
  }
}

function quotedEtag(value: string | null, path: string): string {
  if (value === null || !/^"[0-9a-f]{64}"$/.test(value)) {
    throw new ProcessDefinitionDecodeError("ETAG_INVALID", path);
  }
  return value;
}

async function readBoundedResponseBytes(
  response: Response,
  maximum: number,
): Promise<Uint8Array> {
  const declaredLength = response.headers.get("content-length");
  if (declaredLength !== null) {
    const parsedLength = Number(declaredLength);
    if (Number.isFinite(parsedLength) && parsedLength > maximum) {
      throw new ProcessDefinitionDecodeError("RESPONSE_TOO_LARGE", "/body");
    }
  }
  if (response.body === null) return new Uint8Array();

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maximum) {
      await reader.cancel();
      throw new ProcessDefinitionDecodeError("RESPONSE_TOO_LARGE", "/body");
    }
    chunks.push(value);
  }

  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return bytes;
}

async function typedError(response: Response): Promise<ProcessDefinitionError> {
  const recoveries: Record<
    ProcessDefinitionErrorCode,
    ProcessDefinitionRecoveryClass
  > = {
    PROCESS_DEFINITION_UNAVAILABLE: "enable_or_reinstall",
    PROCESS_DEFINITION_IDENTITY_MISMATCH: "reinstall_exact_artifact",
    PROCESS_DEFINITION_INVALID: "replace_validated_definition",
    PROCESS_DEFINITION_UNSUPPORTED_VERSION: "install_compatible_wright",
    PROCESS_DEFINITION_READ_FAILED: "inspect_local_data_root",
  };
  const codesByStatus: Readonly<
    Record<number, readonly ProcessDefinitionErrorCode[]>
  > = {
    404: ["PROCESS_DEFINITION_UNAVAILABLE"],
    409: ["PROCESS_DEFINITION_IDENTITY_MISMATCH"],
    422: [
      "PROCESS_DEFINITION_INVALID",
      "PROCESS_DEFINITION_UNSUPPORTED_VERSION",
    ],
    503: ["PROCESS_DEFINITION_READ_FAILED"],
  };
  try {
    const allowed = [
      "error_code",
      "message",
      "recovery_class",
      "trace_id",
      "supported_schema_versions",
    ] as const;
    const required = [
      "error_code",
      "message",
      "recovery_class",
      "trace_id",
    ] as const;
    const bytes = await readBoundedResponseBytes(
      response,
      MAX_PROCESS_DEFINITION_ERROR_BYTES,
    );
    const row = closedObject(
      parseProcessJsonBytes(bytes),
      allowed,
      required,
      "",
    );
    const errorCode = enumValue(
      row.error_code,
      Object.keys(recoveries) as ProcessDefinitionErrorCode[],
      "/error_code",
    );
    if (!(codesByStatus[response.status] ?? []).includes(errorCode)) {
      throw new ProcessDefinitionDecodeError(
        "ERROR_STATUS_MISMATCH",
        "/status",
      );
    }
    const recovery = enumValue(
      row.recovery_class,
      [recoveries[errorCode]] as const,
      "/recovery_class",
    );
    const versions = row.supported_schema_versions;
    if (versions !== undefined) {
      const parsed = arrayValue(versions, "/supported_schema_versions", 1, 1);
      if (parsed[0] !== PROCESS_DEFINITION_SCHEMA_VERSION) {
        throw new ProcessDefinitionDecodeError(
          "SUPPORTED_VERSIONS_INVALID",
          "/supported_schema_versions",
        );
      }
    }
    return {
      error_code: errorCode,
      message: stringValue(row.message, "/message"),
      recovery_class: recovery,
      trace_id: stringValue(row.trace_id, "/trace_id"),
      ...(versions === undefined
        ? {}
        : { supported_schema_versions: [PROCESS_DEFINITION_SCHEMA_VERSION] }),
    };
  } catch {
    return {
      error_code: "PROCESS_DEFINITION_READ_FAILED",
      message: "Process definition could not be read.",
      recovery_class: "inspect_local_data_root",
      trace_id: "unavailable",
    };
  }
}

export async function fetchProcessDefinition(
  etag?: string,
  signal?: AbortSignal,
): Promise<ProcessDefinitionFetchResult> {
  const headers: Record<string, string> = {};
  if (etag !== undefined) headers["If-None-Match"] = quotedEtag(etag, "/etag");
  const response = await hostAdapter.fetch(
    `${hostAdapter.getApiBaseUrl()}/api/process-definitions/${PROCESS_DEFINITION_ID}`,
    { headers, signal, cache: "no-cache" },
  );
  if (response.status === 304) {
    if (etag === undefined) {
      throw new ProcessDefinitionDecodeError(
        "UNSOLICITED_NOT_MODIFIED",
        "/status",
      );
    }
    const responseEtag = quotedEtag(
      response.headers.get("etag"),
      "/headers/etag",
    );
    if (responseEtag !== etag) {
      throw new ProcessDefinitionDecodeError(
        "NOT_MODIFIED_IDENTITY_MISMATCH",
        "/headers/etag",
      );
    }
    return {
      state: "not_modified",
      status: 304,
      etag: responseEtag,
      envelope: null,
    };
  }
  if (!response.ok) {
    throw new ProcessDefinitionServiceError(
      response.status,
      await typedError(response),
    );
  }
  if (response.status !== 200) {
    throw new ProcessDefinitionDecodeError(
      "RESPONSE_STATUS_INVALID",
      "/status",
    );
  }
  const bytes = await readBoundedResponseBytes(
    response,
    MAX_PROCESS_DEFINITION_ENVELOPE_BYTES,
  );
  const envelope = decodeProcessDefinitionEnvelope(
    parseProcessJsonBytes(bytes),
  );
  await verifyProcessDefinitionIdentity(envelope);
  const responseEtag = quotedEtag(
    response.headers.get("etag"),
    "/headers/etag",
  );
  if (responseEtag !== `"${envelope.etag}"`) {
    throw new ProcessDefinitionDecodeError(
      "ETAG_IDENTITY_MISMATCH",
      "/headers/etag",
    );
  }
  return { state: "current", status: 200, etag: responseEtag, envelope };
}
