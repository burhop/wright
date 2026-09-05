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
export type NativeRunState =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "timed_out"
  | "interrupted";
export type NativeStepState =
  "pending" | "running" | "succeeded" | "failed" | "blocked" | "cancelled";
export interface NativeBinding {
  server_id: string;
  tool_name: string;
  input_schema_digest: string;
  output_schema_digest: string;
}
export interface NativeBindingOption extends NativeBinding {
  title: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown> | null;
}
export interface NativeRunSummary {
  run_id: string;
  process_id: string;
  state: NativeRunState;
  semantic_digest: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  derived_from_run_id: string | null;
  reason: NativeFinding | null;
  trace_id: string;
}
export type NativeValue =
  | string
  | { value: string; unit: string }
  | {
      artifact_id: string;
      content_digest: string;
      size: number;
      filename: string;
    };
export interface NativeRunStep {
  step_id: string;
  operation: string;
  state: NativeStepState;
  started_at: string | null;
  completed_at: string | null;
  inputs: Record<string, NativeValue> | null;
  outputs: Record<string, NativeValue> | null;
  reason: NativeFinding | null;
}
export interface NativeArtifact {
  artifact_id: string;
  step_id: string;
  port_id: string;
  filename: string;
  content_digest: string;
  size: number;
  media_type: string;
  provenance: Record<string, unknown>;
}
export interface NativeRun extends NativeRunSummary {
  snapshot: {
    definition: NativeDefinition;
    revision: number;
    token: string;
    semantic_digest: string;
  };
  bindings: Record<string, NativeBinding>;
  actor: string;
  timeout_seconds: number;
  steps: NativeRunStep[];
  artifacts: NativeArtifact[];
  last_sequence: number;
}
export interface NativeEvent {
  sequence: number;
  occurred_at: string;
  kind: string;
  payload: Record<string, unknown>;
  trace_id: string;
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
      `/documents${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`,
      "GET",
      undefined,
      signal,
    ),
  get: (session: string, id: string, signal?: AbortSignal) =>
    request<SavedProcess>(
      session,
      `/documents/${encodeURIComponent(id)}`,
      "GET",
      undefined,
      signal,
    ),
  create: (session: string, document: NativeDocument, requestId: string) =>
    request<SavedProcess>(session, "/documents", "POST", {
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
      `/documents/${encodeURIComponent(document.definition.id)}`,
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
    bindings: Record<string, NativeBinding> = {},
  ) =>
    request<NativeCheck>(
      session,
      "/check",
      "POST",
      { definition, bindings },
      signal,
    ),
};

export const nativeRunApi = {
  history: (
    session: string,
    processId: string,
    cursor?: string,
    signal?: AbortSignal,
  ) =>
    request<{ runs: NativeRunSummary[]; next_cursor: string | null }>(
      session,
      `/documents/${encodeURIComponent(processId)}/runs${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`,
      "GET",
      undefined,
      signal,
    ),
  get: (session: string, runId: string, signal?: AbortSignal) =>
    request<NativeRun>(
      session,
      `/runs/${encodeURIComponent(runId)}`,
      "GET",
      undefined,
      signal,
    ),
  events: (
    session: string,
    runId: string,
    after: number,
    signal?: AbortSignal,
  ) =>
    request<{ events: NativeEvent[]; next_sequence: number }>(
      session,
      `/runs/${encodeURIComponent(runId)}/events?after_sequence=${after}&limit=200`,
      "GET",
      undefined,
      signal,
    ),
  start: (
    session: string,
    processId: string,
    expectedToken: string,
    requestId: string,
    bindings: Record<string, NativeBinding>,
    timeoutSeconds: number,
    derivedFrom: string | null,
  ) =>
    request<{ run_id: string; state: NativeRunState; semantic_digest: string }>(
      session,
      `/documents/${encodeURIComponent(processId)}/runs`,
      "POST",
      {
        expected_token: expectedToken,
        request_id: requestId,
        bindings,
        timeout_seconds: timeoutSeconds,
        derived_from_run_id: derivedFrom,
      },
    ),
  cancel: (session: string, runId: string) =>
    request<NativeRunSummary>(
      session,
      `/runs/${encodeURIComponent(runId)}/cancel`,
      "POST",
    ),
  bindings: (session: string, signal?: AbortSignal) =>
    request<{ bindings: NativeBindingOption[] }>(
      session,
      "/bindings",
      "GET",
      undefined,
      signal,
    ),
};

/** Artifact bytes are never exposed to the viewer/download link until size and SHA-256 match the run index. */
export async function fetchNativeArtifact(
  session: string,
  runId: string,
  artifact: NativeArtifact,
  signal?: AbortSignal,
): Promise<Blob> {
  if (!crypto.subtle)
    throw new NativeProcessError({
      code: "NATIVE_ARTIFACT_INVALID",
      message:
        "This browser cannot verify artifact digests on the current connection.",
      recovery: "Open Wright over HTTPS or from localhost, then retry.",
    });
  const limit = 10 * 1024 * 1024;
  if (
    !Number.isSafeInteger(artifact.size) ||
    artifact.size < 0 ||
    artifact.size > limit
  )
    throw new NativeProcessError({
      code: "NATIVE_ARTIFACT_INVALID",
      message: "The recorded artifact size is invalid.",
      recovery: "Inspect the run and service diagnostics.",
    });
  const span = telemetry.startSpan("native.process artifact");
  try {
    const url = `${hostAdapter.getApiBaseUrl()}/api/native-processes/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifact.artifact_id)}?session_id=${encodeURIComponent(session)}`;
    const response = await hostAdapter.fetch(url, {
      signal,
      headers: span.traceId ? { "X-Trace-Id": span.traceId } : {},
    });
    if (!response.ok)
      throw new NativeProcessError(
        {
          code: "NATIVE_ARTIFACT_INVALID",
          message: `Artifact access failed (HTTP ${response.status}).`,
          recovery:
            "Reconnect and inspect run permissions or artifact integrity.",
        },
        response.status,
      );
    const reader = response.body?.getReader(),
      chunks: Uint8Array[] = [];
    let size = 0;
    if (reader) {
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > limit || size > artifact.size) {
          await reader.cancel();
          throw new Error("Artifact exceeds its recorded size.");
        }
        chunks.push(part.value);
      }
    } else {
      const bytes = new Uint8Array(await response.arrayBuffer());
      chunks.push(bytes);
      size = bytes.length;
    }
    if (size !== artifact.size || size > limit)
      throw new Error("Artifact size does not match its run record.");
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.length;
    }
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    const digest = Array.from(new Uint8Array(hash), (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("");
    if (
      digest !== artifact.content_digest ||
      response.headers.get("X-Content-SHA256") !== digest
    )
      throw new Error(
        "Artifact digest does not match its run record and response.",
      );
    span.end();
    // Downloads remain inert even if an indexed artifact contains HTML or SVG.
    return new Blob([bytes], { type: "application/octet-stream" });
  } catch (failure) {
    span.error(
      failure instanceof Error
        ? failure
        : new Error("Artifact verification failed"),
    );
    if (failure instanceof NativeProcessError) throw failure;
    throw new NativeProcessError({
      code: "NATIVE_ARTIFACT_INVALID",
      message:
        failure instanceof Error
          ? failure.message
          : "Artifact verification failed.",
      recovery:
        "No unverified bytes were displayed. Reconnect or inspect service integrity diagnostics.",
    });
  }
}
