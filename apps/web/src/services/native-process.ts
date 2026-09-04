import { hostAdapter } from "./host-adapter";
import telemetry from "./telemetry";

export type PortType = "text" | "quantity" | "artifact";
export type ConfigValue =
  string | number | boolean | null | string[] | { value: string; unit: string };
export interface NativeStep {
  id: string;
  title: string;
  operation: string;
  config: Record<string, ConfigValue>;
}
export interface NativePort {
  id: string;
  step_id: string;
  key: string;
  label: string;
  direction: "input" | "output";
  type: PortType;
  cardinality: "one" | "many";
  required: boolean;
}
export interface NativeConnection {
  id: string;
  source_port_id: string;
  target_port_id: string;
}
export interface NativeOutput {
  id: string;
  title: string;
  port_id: string;
}
export interface NativeDefinition {
  format: "wright-native-process";
  schema_version: "1.0.0";
  id: string;
  title: string;
  steps: NativeStep[];
  ports: NativePort[];
  connections: NativeConnection[];
  outputs: NativeOutput[];
}
export type Presentation = Record<string, { x: number; y: number }>;
export interface NativeDocument {
  definition: NativeDefinition;
  presentation: Presentation;
}
export interface SavedProcess extends NativeDocument {
  revision: number;
  token: string;
  semantic_digest: string;
  updated_at: string;
}
export interface ProcessSummary {
  id: string;
  title: string;
  revision: number;
  token: string;
  updated_at: string;
}
export interface NativeFinding {
  code: string;
  step_id?: string | null;
  port_id?: string | null;
  message: string;
  recovery: string;
}
export interface NativeCheck {
  structurally_valid: boolean;
  ready: boolean;
  findings: NativeFinding[];
}
export interface JsonSchema {
  $ref?: string;
  $defs?: Record<string, JsonSchema>;
  type?: string;
  const?: unknown;
  enum?: unknown[];
  properties?: Record<string, JsonSchema>;
  required?: string[];
  additionalProperties?: boolean | JsonSchema;
  items?: JsonSchema;
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  propertyNames?: JsonSchema;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  maxProperties?: number;
  oneOf?: JsonSchema[];
  allOf?: JsonSchema[];
  if?: JsonSchema;
  then?: JsonSchema;
}
export interface OperationPort {
  key: string;
  label?: string;
  type: PortType;
  cardinality: "one";
  required: true;
}
export interface NativeOperation {
  id: string;
  inputs: OperationPort[];
  outputs: OperationPort[];
  config_schema: JsonSchema;
  required_config_keys: string[];
}
export interface NativeContract {
  format: "wright-native-process";
  schema_version: "1.0.0";
  schema: JsonSchema;
  operations: NativeOperation[];
  canonicalization: unknown;
}
export interface NativeExample extends NativeDocument {
  id: string;
  title: string;
}
export interface NativeFailure {
  code: string;
  message: string;
  recovery: string;
  trace_id?: string;
  findings?: NativeFinding[];
}
export class NativeProcessError extends Error {
  readonly detail: NativeFailure;
  readonly status: number;
  constructor(detail: NativeFailure, status = 0) {
    super(detail.message);
    this.name = "NativeProcessError";
    this.detail = detail;
    this.status = status;
  }
}

async function request<T>(
  session: string,
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams({ session_id: session });
  const url = `${hostAdapter.getApiBaseUrl()}/api/native-processes${path}${path.includes("?") ? "&" : "?"}${query}`;
  const span = telemetry.startSpan(
    `native.process ${method} ${path.split("?")[0]}`,
  );
  try {
    const response = await hostAdapter.fetch(url, {
      method,
      signal,
      headers: {
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(span.traceId ? { "X-Trace-Id": span.traceId } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new NativeProcessError(
        {
          code: "NATIVE_UNAVAILABLE",
          message:
            "The native process service returned an unreadable response.",
          recovery: "Check service health and retry. Your draft is retained.",
        },
        response.status,
      );
    }
    if (!response.ok) {
      const outer = payload as {
        detail?: NativeFailure;
      } & Partial<NativeFailure>;
      const detail =
        outer.detail && typeof outer.detail === "object" ? outer.detail : outer;
      throw new NativeProcessError(
        {
          code:
            typeof detail.code === "string"
              ? detail.code
              : "NATIVE_UNAVAILABLE",
          message:
            typeof detail.message === "string"
              ? detail.message
              : "The native process request failed.",
          recovery:
            typeof detail.recovery === "string"
              ? detail.recovery
              : "Check service health and retry. Your draft is retained.",
          trace_id: detail.trace_id,
          findings: detail.findings,
        },
        response.status,
      );
    }
    span.end();
    return payload as T;
  } catch (error) {
    span.error(
      error instanceof Error
        ? error
        : new Error("Native process request failed"),
    );
    throw error;
  }
}
export const nativeProcessApi = {
  contract: (session: string, signal?: AbortSignal) =>
    request<NativeContract>(session, "/contract", "GET", undefined, signal),
  examples: (session: string, signal?: AbortSignal) =>
    request<{ examples: NativeExample[] }>(
      session,
      "/examples",
      "GET",
      undefined,
      signal,
    ),
  list: (session: string, cursor?: string, signal?: AbortSignal) =>
    request<{ documents: ProcessSummary[]; next_cursor: string | null }>(
      session,
      cursor ? `?cursor=${encodeURIComponent(cursor)}` : "",
      "GET",
      undefined,
      signal,
    ),
  get: (session: string, id: string, signal?: AbortSignal) =>
    request<SavedProcess>(
      session,
      `/${encodeURIComponent(id)}`,
      "GET",
      undefined,
      signal,
    ),
  create: (session: string, document: NativeDocument, requestId: string) =>
    request<SavedProcess>(session, "", "POST", {
      definition: document.definition,
      presentation: document.presentation,
      request_id: requestId,
    }),
  save: (
    session: string,
    document: NativeDocument,
    token: string,
    requestId: string,
  ) =>
    request<SavedProcess>(
      session,
      `/${encodeURIComponent(document.definition.id)}`,
      "PUT",
      {
        definition: document.definition,
        presentation: document.presentation,
        expected_token: token,
        request_id: requestId,
      },
    ),
  check: (
    session: string,
    definition: NativeDefinition,
    signal?: AbortSignal,
  ) =>
    request<NativeCheck>(
      session,
      "/check",
      "POST",
      { definition, bindings: {} },
      signal,
    ),
};
