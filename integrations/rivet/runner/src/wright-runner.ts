import { createHash, randomUUID } from "node:crypto";
import { isAbsolute } from "node:path";
import { readFile } from "node:fs/promises";
import { format } from "node:util";

import {
  createProcessor,
  loadProjectFromFile,
  type MCP,
  type MCPProvider,
  type Project,
} from "@valerypopoff/rivet2-node";

export const WRIGHT_RIVET_RUNNER_PROTOCOL = 2;
export const RIVET_SOURCE_REVISION = "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053";
export const RIVET_PACKAGE_VERSION = "2.1.9";

const MAX_REQUEST_BYTES = 2 * 1024 * 1024;
const MAX_EVENT_BYTES = 64 * 1024;
const MAX_OUTPUT_BYTES = 1024 * 1024;
const RUN_ID_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/;
const DIGEST_PATTERN = /^[a-f0-9]{64}$/;
const NODE_HANDLE_PATTERN = /^wright:[A-Za-z0-9_-]{16,128}$/;
const QUALIFIED_TOOL_PATTERN =
  /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}__[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const DISCOVERY_HANDLE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const MAX_BRIDGE_RESPONSE_BYTES = 1024 * 1024;
const MAX_BRIDGE_EVENTS = 2_000;
const MAX_INSPECTION_ITEMS = 64;
const MAX_INSPECTION_VALUE_BYTES = 2 * 1024;
const MAX_INSPECTION_COLLECTION_BYTES = 20 * 1024;
const MAX_INSPECTION_DEPTH = 8;
const MAX_INSPECTION_CHILDREN = 64;
const STABLE_RIVET_ERROR = /^RIVET_[A-Z0-9_]{1,64}$/;
const SECRET_FIELD =
  /token|secret|password|passwd|api[_-]?key|authorization|credential/i;
const URL_SECRET = /([?&](?:token|access_token|api_key|key)=)[^&\s]+/gi;
const BINARY_DATA_TYPES = new Set(["audio", "binary", "document", "image"]);
const OUTPUT_SECRETS = new Set<string>();

function writeDiagnostic(...values: unknown[]): void {
  let encoded = format(...values);
  for (const secret of OUTPUT_SECRETS) {
    if (secret.length >= 8) encoded = encoded.split(secret).join("[REDACTED]");
  }
  process.stderr.write(`${encoded}\n`);
}

// Stdout is the Wright JSONL protocol channel. Rivet and its dependencies
// occasionally log node failures through console.log(), so route every console
// diagnostic to stderr before a graph can execute.
console.log = writeDiagnostic;
console.info = writeDiagnostic;
console.debug = writeDiagnostic;
console.warn = writeDiagnostic;
console.error = writeDiagnostic;

const CAPABILITY_NODE_TYPES: Readonly<Record<string, ReadonlySet<string>>> = {
  ai: new Set([
    "chat",
    "chatAnthropic",
    "chatGoogle",
    "chatHuggingFace",
    "chatLoop",
    "llmChatV2",
    "llmProfile",
    "openaiAttachAssistantFile",
    "openaiCreateThread",
    "openaiCreateThreadMessage",
    "openaiDeleteThread",
    "openaiGetFile",
    "openaiGetThread",
    "openaiListFiles",
    "openaiListThreadMessages",
    "openaiRunThread",
    "openaiUploadFile",
  ]),
  code: new Set(["code", "codeNew", "externalCall"]),
  dataset: new Set([
    "appendToDataset",
    "createDataset",
    "datasetNearestNeighbors",
    "datasetSelector",
    "getAllDatasets",
    "getDatasetRow",
    "loadDataset",
    "replaceDataset",
  ]),
  filesystem: new Set([
    "fileBrowser",
    "filePathBrowser",
    "readAllFiles",
    "readDirectory",
    "readFile",
  ]),
  interactive: new Set(["userInput"]),
  mcp: new Set(["mcpDiscovery", "mcpGetPrompt", "mcpToolCall"]),
  network: new Set(["httpCall"]),
};

export type WrightRunnerRequest = {
  protocolVersion: number;
  runId: string;
  projectPath: string;
  expectedDigest: string;
  graph?: string;
  inputs?: Record<string, unknown>;
  context?: Record<string, unknown>;
  ai?: { baseUrl: string; token: string; model: string };
  capabilities?: string[];
  mcp?: WrightMcpGrant;
};

type WrightMcpBinding = {
  nodeId: string;
  handle: string;
  qualifiedToolName: string;
  bindingDigest: string;
};

type WrightMcpGrant = {
  authorityId: string;
  bridgeBaseUrl: string;
  token: string;
  expiresAt: string;
  bindingSetDigest: string;
  discoveryHandle: string;
  bindings: WrightMcpBinding[];
};

type RunnerError = Error & { code?: string };

function failure(code: string, message: string): RunnerError {
  const error = new Error(message) as RunnerError;
  error.code = code;
  return error;
}

function stableRunnerError(caught: unknown): RunnerError | undefined {
  const pending: unknown[] = [caught];
  const visited = new Set<unknown>();
  while (pending.length > 0) {
    const current = pending.shift();
    if (
      current == null ||
      (typeof current !== "object" && typeof current !== "function") ||
      visited.has(current)
    ) {
      continue;
    }
    visited.add(current);
    const candidate = current as RunnerError;
    if (
      typeof candidate.code === "string" &&
      STABLE_RIVET_ERROR.test(candidate.code)
    ) {
      return candidate;
    }
    if (current instanceof AggregateError) {
      pending.push(...current.errors);
    }
    if ("cause" in candidate) {
      pending.push(candidate.cause);
    }
  }
  return undefined;
}

function writeEvent(event: Record<string, unknown>): void {
  let encoded = JSON.stringify(event);
  for (const secret of OUTPUT_SECRETS) {
    if (secret.length >= 8) encoded = encoded.split(secret).join("[REDACTED]");
  }
  if (Buffer.byteLength(encoded, "utf8") > MAX_EVENT_BYTES) {
    throw failure(
      "RIVET_RUNNER_EVENT_TOO_LARGE",
      "Runner event exceeded the bounded JSONL event size.",
    );
  }
  process.stdout.write(`${encoded}\n`);
}

type InspectionProjection = {
  values: Record<string, unknown>[];
  complete: boolean;
  state: "available" | "no-value" | "truncated" | "unavailable";
  omittedCount: number;
};

function inspectionJson(value: unknown): string {
  return JSON.stringify(value) ?? "null";
}

function inspectionDigest(value: unknown): string {
  return createHash("sha256").update(inspectionJson(value)).digest("hex");
}

function binaryMetadata(
  value: unknown,
  dataType: string,
): Record<string, unknown> {
  const semantic =
    value && typeof value === "object" && "value" in value
      ? (value as { value?: unknown }).value
      : value;
  const structured =
    semantic && typeof semantic === "object"
      ? (semantic as Record<string, unknown>)
      : undefined;
  const payload = structured?.data ?? semantic;
  const bytes =
    payload instanceof Uint8Array
      ? payload.byteLength
      : Array.isArray(payload)
        ? payload.length
        : undefined;
  return {
    data_type: dataType,
    media_type:
      typeof structured?.mediaType === "string"
        ? structured.mediaType.slice(0, 255)
        : null,
    bytes,
    body: "not retained",
  };
}

function safeInspectionValue(
  value: unknown,
  depth = 0,
): { value: unknown; redactions: number; bounded: boolean } {
  if (depth >= MAX_INSPECTION_DEPTH) {
    return { value: "[projection depth limit]", redactions: 0, bounded: true };
  }
  if (value instanceof Uint8Array || Buffer.isBuffer(value)) {
    return {
      value: { body: "not retained", bytes: value.byteLength },
      redactions: 0,
      bounded: true,
    };
  }
  if (typeof value === "function") {
    return { value: "[function not retained]", redactions: 0, bounded: true };
  }
  if (typeof value === "string") {
    let safe = value.replace(URL_SECRET, "$1[redacted]");
    let redactions = safe === value ? 0 : 1;
    for (const secret of OUTPUT_SECRETS) {
      if (secret.length >= 8 && safe.includes(secret)) {
        safe = safe.split(secret).join("[redacted]");
        redactions += 1;
      }
    }
    if (
      /^data:[^;,\s]+;base64,/i.test(safe) ||
      (safe.length >= 256 &&
        safe.length % 4 === 0 &&
        new Set(safe).size >= 12 &&
        /^[A-Za-z0-9+/]+={0,2}$/.test(safe))
    ) {
      return {
        value: { body: "base64 not retained" },
        redactions: redactions + 1,
        bounded: true,
      };
    }
    if (safe.length > 4096) {
      return {
        value: `${safe.slice(0, 4096)}…[truncated]`,
        redactions,
        bounded: true,
      };
    }
    return { value: safe, redactions, bounded: false };
  }
  if (Array.isArray(value)) {
    let redactions = 0;
    let bounded = value.length > MAX_INSPECTION_CHILDREN;
    const projected = value.slice(0, MAX_INSPECTION_CHILDREN).map((item) => {
      const child = safeInspectionValue(item, depth + 1);
      redactions += child.redactions;
      bounded ||= child.bounded;
      return child.value;
    });
    return { value: projected, redactions, bounded };
  }
  if (value && typeof value === "object") {
    let redactions = 0;
    const entries = Object.entries(value as Record<string, unknown>);
    let bounded = entries.length > MAX_INSPECTION_CHILDREN;
    const projected: Record<string, unknown> = {};
    for (const [key, childValue] of entries.slice(0, MAX_INSPECTION_CHILDREN)) {
      if (SECRET_FIELD.test(key)) {
        projected[key] = "[redacted]";
        redactions += 1;
        continue;
      }
      const child = safeInspectionValue(childValue, depth + 1);
      projected[key] = child.value;
      redactions += child.redactions;
      bounded ||= child.bounded;
    }
    return { value: projected, redactions, bounded };
  }
  return { value, redactions: 0, bounded: false };
}

function projectInspectionValue(
  name: string,
  value: unknown,
  origin: string,
): Record<string, unknown> {
  const envelope =
    value &&
    typeof value === "object" &&
    typeof (value as { type?: unknown }).type === "string"
      ? (value as { type: string; value?: unknown })
      : undefined;
  const dataType = envelope?.type ?? (value === null ? "null" : typeof value);
  const semantic = envelope ? envelope.value : value;
  const scalarType = dataType.endsWith("[]") ? dataType.slice(0, -2) : dataType;
  const binaryOmitted =
    BINARY_DATA_TYPES.has(scalarType) ||
    dataType.startsWith("fn<") ||
    typeof semantic === "function" ||
    (typeof semantic === "string" &&
      (/^data:[^;,\s]+;base64,/i.test(semantic) ||
        (semantic.length >= 256 &&
          semantic.length % 4 === 0 &&
          new Set(semantic).size >= 12 &&
          /^[A-Za-z0-9+/]+={0,2}$/.test(semantic))));
  const projected = binaryOmitted
    ? { value: binaryMetadata(value, dataType), redactions: 0, bounded: true }
    : safeInspectionValue(semantic);
  const encoded = inspectionJson(projected.value);
  const exceedsLimit =
    Buffer.byteLength(encoded, "utf8") > MAX_INSPECTION_VALUE_BYTES;
  const complete = !binaryOmitted && !projected.bounded && !exceedsLimit;
  const preview =
    typeof projected.value === "string"
      ? projected.value.slice(0, 1024)
      : encoded.slice(0, 1024);
  const evidenceState = binaryOmitted
    ? "not-retained"
    : exceedsLimit || projected.bounded
      ? "truncated"
      : projected.redactions > 0
        ? "redacted"
        : semantic == null
          ? "no-value"
          : "available";
  return {
    result_id: `${origin}:${name}`,
    name: name.slice(0, 255),
    origin,
    kind: binaryOmitted
      ? "structured"
      : Array.isArray(projected.value)
        ? "list"
        : projected.value && typeof projected.value === "object"
          ? "structured"
          : projected.value === null
            ? "null"
            : typeof projected.value === "string"
              ? "text"
              : typeof projected.value,
    data_type: dataType,
    evidence_state: evidenceState,
    value: complete ? projected.value : null,
    preview,
    complete,
    truncation_reason: binaryOmitted
      ? "binary_omitted"
      : projected.bounded
        ? "projection_limit"
        : exceedsLimit
          ? "size_limit"
          : null,
    original_bytes: Buffer.byteLength(encoded, "utf8"),
    retained_bytes: complete
      ? Buffer.byteLength(encoded, "utf8")
      : Buffer.byteLength(preview, "utf8"),
    digest: inspectionDigest(projected.value),
    redaction_count: projected.redactions,
    artifact: null,
  };
}

function projectInspectionValues(
  values: unknown,
  origin: string,
): InspectionProjection {
  try {
    const entries =
      values && typeof values === "object" && !Array.isArray(values)
        ? Object.entries(values as Record<string, unknown>)
        : [];
    const projected = entries
      .slice(0, MAX_INSPECTION_ITEMS)
      .map(([name, value]) => projectInspectionValue(name, value, origin));
    let complete = entries.length <= projected.length;
    while (
      projected.length > 0 &&
      Buffer.byteLength(inspectionJson(projected), "utf8") >
        MAX_INSPECTION_COLLECTION_BYTES
    ) {
      projected.pop();
      complete = false;
    }
    complete &&= projected.every((item) => item.complete !== false);
    return {
      values: projected,
      complete,
      state:
        entries.length === 0
          ? "no-value"
          : complete
            ? "available"
            : "truncated",
      omittedCount: Math.max(0, entries.length - projected.length),
    };
  } catch {
    return {
      values: [],
      complete: false,
      state: "unavailable",
      omittedCount: 0,
    };
  }
}

async function readRequest(): Promise<WrightRunnerRequest> {
  process.stdin.setEncoding("utf8");
  let raw = "";
  for await (const chunk of process.stdin) {
    raw += chunk;
    if (Buffer.byteLength(raw, "utf8") > MAX_REQUEST_BYTES) {
      throw failure(
        "RIVET_RUNNER_REQUEST_TOO_LARGE",
        "Runner request exceeded the input limit.",
      );
    }
  }
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    throw failure(
      "RIVET_RUNNER_REQUEST_INVALID",
      "Runner request must be one JSON object.",
    );
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw failure(
      "RIVET_RUNNER_REQUEST_INVALID",
      "Runner request must be one JSON object.",
    );
  }
  return value as WrightRunnerRequest;
}

function validateRequest(request: WrightRunnerRequest): void {
  if (
    request.protocolVersion !== 1 &&
    request.protocolVersion !== WRIGHT_RIVET_RUNNER_PROTOCOL
  ) {
    throw failure(
      "RIVET_RUNNER_PROTOCOL_UNSUPPORTED",
      "Unsupported Wright Rivet runner protocol.",
    );
  }
  if (!RUN_ID_PATTERN.test(request.runId ?? "")) {
    throw failure("RIVET_RUNNER_REQUEST_INVALID", "Invalid run identifier.");
  }
  if (
    typeof request.projectPath !== "string" ||
    !isAbsolute(request.projectPath)
  ) {
    throw failure(
      "RIVET_RUNNER_REQUEST_INVALID",
      "Project path must be absolute.",
    );
  }
  if (!DIGEST_PATTERN.test(request.expectedDigest ?? "")) {
    throw failure(
      "RIVET_RUNNER_REQUEST_INVALID",
      "Expected digest must be a lowercase SHA-256 digest.",
    );
  }
  if (
    request.inputs != null &&
    (typeof request.inputs !== "object" || Array.isArray(request.inputs))
  ) {
    throw failure("RIVET_RUNNER_REQUEST_INVALID", "Inputs must be an object.");
  }
  if (
    request.context != null &&
    (typeof request.context !== "object" || Array.isArray(request.context))
  ) {
    throw failure("RIVET_RUNNER_REQUEST_INVALID", "Context must be an object.");
  }
  if (request.protocolVersion === 1 && request.mcp != null) {
    throw failure(
      "RIVET_MCP_GRANT_REQUIRED",
      "MCP grants require Wright Rivet runner protocol v2.",
    );
  }
  if (request.protocolVersion === 2) validateMcpGrant(request);
}

function exactKeys(
  value: Record<string, unknown>,
  allowed: ReadonlySet<string>,
  code: string,
): void {
  if (Object.keys(value).some((key) => !allowed.has(key))) {
    throw failure(code, "The Wright MCP grant contains unsupported fields.");
  }
}

function validateMcpGrant(request: WrightRunnerRequest): void {
  exactKeys(
    request as unknown as Record<string, unknown>,
    new Set([
      "protocolVersion",
      "runId",
      "projectPath",
      "expectedDigest",
      "graph",
      "inputs",
      "context",
      "ai",
      "capabilities",
      "mcp",
    ]),
    "RIVET_MCP_BRIDGE_DENIED",
  );
  if (request.mcp == null) return;
  if (!(request.capabilities ?? []).includes("mcp")) {
    throw failure(
      "RIVET_MCP_GRANT_REQUIRED",
      "The MCP capability was not granted.",
    );
  }
  const grant = request.mcp;
  exactKeys(
    grant as unknown as Record<string, unknown>,
    new Set([
      "authorityId",
      "bridgeBaseUrl",
      "token",
      "expiresAt",
      "bindingSetDigest",
      "discoveryHandle",
      "bindings",
    ]),
    "RIVET_MCP_BRIDGE_DENIED",
  );
  let bridge: URL;
  try {
    bridge = new URL(grant.bridgeBaseUrl);
  } catch {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The Wright MCP bridge address is invalid.",
    );
  }
  if (
    bridge.protocol !== "http:" ||
    bridge.hostname !== "127.0.0.1" ||
    !bridge.port ||
    bridge.pathname !== "/internal/rivet-mcp/v1" ||
    bridge.search ||
    bridge.hash ||
    bridge.username ||
    bridge.password
  ) {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The Wright MCP bridge must use its exact loopback address.",
    );
  }
  const expiry = Date.parse(grant.expiresAt);
  if (!Number.isFinite(expiry) || expiry <= Date.now()) {
    throw failure(
      "RIVET_MCP_AUTHORITY_EXPIRED",
      "The Wright MCP run authority expired.",
    );
  }
  if (
    typeof grant.authorityId !== "string" ||
    grant.authorityId.length < 1 ||
    grant.authorityId.length > 128 ||
    typeof grant.token !== "string" ||
    grant.token.length < 43 ||
    grant.token.length > 512 ||
    /\s/.test(grant.token) ||
    !DIGEST_PATTERN.test(grant.bindingSetDigest ?? "") ||
    !DISCOVERY_HANDLE_PATTERN.test(grant.discoveryHandle ?? "") ||
    !Array.isArray(grant.bindings)
  ) {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The Wright MCP run grant is invalid.",
    );
  }
  const nodeIds = new Set<string>();
  const handles = new Set<string>();
  for (const binding of grant.bindings) {
    exactKeys(
      binding as unknown as Record<string, unknown>,
      new Set(["nodeId", "handle", "qualifiedToolName", "bindingDigest"]),
      "RIVET_MCP_BINDING_MISMATCH",
    );
    if (
      typeof binding.nodeId !== "string" ||
      binding.nodeId.length < 1 ||
      binding.nodeId.length > 256 ||
      !NODE_HANDLE_PATTERN.test(binding.handle ?? "") ||
      !QUALIFIED_TOOL_PATTERN.test(binding.qualifiedToolName ?? "") ||
      !DIGEST_PATTERN.test(binding.bindingDigest ?? "") ||
      nodeIds.has(binding.nodeId) ||
      handles.has(binding.handle)
    ) {
      throw failure(
        "RIVET_MCP_BINDING_MISMATCH",
        "The Wright MCP binding map is invalid.",
      );
    }
    nodeIds.add(binding.nodeId);
    handles.add(binding.handle);
  }
}

function containsSecretMaterial(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(containsSecretMaterial);
  if (!value || typeof value !== "object") {
    return (
      typeof value === "string" &&
      /^[a-z][a-z0-9+.-]*:\/\/[^/\s]*@/i.test(value)
    );
  }
  return Object.entries(value as Record<string, unknown>).some(
    ([key, item]) =>
      /(?:^|[_-])(token|secret|password|passwd|api[_-]?key|authorization|credential)(?:$|[_-])/i.test(
        key,
      ) || containsSecretMaterial(item),
  );
}

export async function verifyProjectDigest(
  request: WrightRunnerRequest,
): Promise<string> {
  const project = await readFile(request.projectPath);
  const actual = createHash("sha256").update(project).digest("hex");
  if (actual !== request.expectedDigest) {
    throw failure(
      "RIVET_WORKFLOW_DIGEST_MISMATCH",
      "Workflow contents changed after the run was authorized.",
    );
  }
  return project.toString("utf8");
}

function projectNodeTypes(
  project: Project,
  graphSelector?: string,
): Set<string> {
  const types = new Set<string>();
  for (const node of graphNodes(project, graphSelector)) {
    if (node && typeof node.type === "string") types.add(node.type);
  }
  return types;
}

function enforceCapabilities(
  project: Project,
  request: WrightRunnerRequest,
): void {
  const granted = new Set(request.capabilities ?? []);
  if (request.ai) granted.add("ai");
  const nodeTypes = projectNodeTypes(project, request.graph);
  for (const [capability, protectedTypes] of Object.entries(
    CAPABILITY_NODE_TYPES,
  )) {
    const deniedType = [...nodeTypes].find((type) => protectedTypes.has(type));
    if (deniedType && !granted.has(capability)) {
      throw failure(
        "RIVET_RUNNER_CAPABILITY_DENIED",
        `Node type ${deniedType} requires the ${capability} capability.`,
      );
    }
  }
}

function installNetworkGuard(request: WrightRunnerRequest): void {
  const permittedAiOrigin = request.ai
    ? new URL(request.ai.baseUrl).origin
    : undefined;
  const permittedMcpBase = request.mcp
    ? new URL(request.mcp.bridgeBaseUrl)
    : undefined;
  const nativeFetch = globalThis.fetch;
  globalThis.fetch = async (
    input: string | URL | Request,
    init?: RequestInit,
  ) => {
    const target = new URL(
      input instanceof Request ? input.url : input.toString(),
    );
    const isAi =
      permittedAiOrigin != null && target.origin === permittedAiOrigin;
    const isMcp =
      permittedMcpBase != null &&
      target.origin === permittedMcpBase.origin &&
      (target.pathname === `${permittedMcpBase.pathname}/discover` ||
        target.pathname === `${permittedMcpBase.pathname}/calls`) &&
      !target.search &&
      !target.hash;
    if (!isAi && !isMcp) {
      throw failure(
        "RIVET_RUNNER_NETWORK_DENIED",
        "Runner network access is restricted to exact Wright bridge addresses.",
      );
    }
    let guardedInit = init;
    if (isAi && request.ai && typeof init?.body === "string") {
      try {
        const payload = JSON.parse(init.body);
        if (payload && typeof payload === "object" && !Array.isArray(payload)) {
          guardedInit = {
            ...init,
            body: JSON.stringify({ ...payload, model: request.ai.model }),
          };
        }
      } catch {
        throw failure(
          "RIVET_RUNNER_AI_REQUEST_INVALID",
          "AI request body must be JSON.",
        );
      }
    }
    return nativeFetch(input, guardedInit);
  };
}

function graphNodes(project: Project, graphSelector?: string): any[] {
  const entries = Object.entries(project.graphs ?? {});
  const selected = graphSelector
    ? entries.filter(
        ([graphId, graph]) =>
          graphId === graphSelector || graph.metadata?.name === graphSelector,
      )
    : entries.filter(([graphId]) => graphId === project.metadata.mainGraphId);
  const graphs = selected.length > 0 ? selected : entries;
  return graphs.flatMap(([, graph]) =>
    Array.isArray(graph.nodes) ? graph.nodes : Object.values(graph.nodes ?? {}),
  );
}

function nodeIdentity(node: any): string {
  const title =
    typeof node?.title === "string" && node.title.trim()
      ? node.title.trim()
      : "LLM Chat";
  const id =
    typeof node?.id === "string" && node.id.trim()
      ? ` (${node.id.trim()})`
      : "";
  return `${title}${id}`;
}

function prepareAiProject(
  project: Project,
  request: WrightRunnerRequest,
): Project {
  if (!request.ai) return project;

  const chatNodes = graphNodes(project, request.graph).filter(
    (node) => node?.type === "llmChatV2",
  );
  if (chatNodes.length === 0) return project;

  const bridgeEndpoint = `${request.ai.baseUrl.replace(/\/$/, "")}/chat/completions`;
  for (const node of chatNodes) {
    const data = node.data ?? {};
    if (data.configurationMode === "profile") {
      throw failure(
        "RIVET_AI_PROFILE_BRIDGE_REQUIRED",
        `${nodeIdentity(node)} uses an LLM Profile whose provider cannot be bound to the Wright AI bridge before execution. Change this node to Inline configuration and run it again.`,
      );
    }

    node.data = {
      ...data,
      configurationMode: "inline",
      provider: "custom",
      model: request.ai.model,
      useModelInput: false,
      apiKeySource: "environment",
      customProviderApiKeyProgrammaticName: "",
      customProviderApiKeyEnvVarName: "CUSTOM_PROVIDER_API_KEY",
      customProviderBaseURL: bridgeEndpoint,
      useCustomProviderBaseURLInput: false,
      baseURL: "",
      useBaseURLInput: false,
      headers: [],
      useHeadersInput: false,
      extraProviderOptions: "",
      useExtraProviderOptionsInput: false,
      enableOpenAIWebSearch: false,
      enableOpenAICodeInterpreter: false,
      enableGoogleSearchGrounding: false,
      enableGoogleUrlContext: false,
    };
  }
  return project;
}

function prepareMcpProject(
  project: Project,
  request: WrightRunnerRequest,
): Project {
  const nodes = graphNodes(project, request.graph);
  const mcpNodes = nodes.filter(
    (node) =>
      node?.type === "mcpDiscovery" ||
      node?.type === "mcpGetPrompt" ||
      node?.type === "mcpToolCall",
  );
  if (mcpNodes.length === 0) {
    if (request.mcp && request.mcp.bindings.length > 0) {
      throw failure(
        "RIVET_MCP_BINDING_EXTRA",
        "The Wright MCP grant contains a binding not used by this graph.",
      );
    }
    return project;
  }
  if (
    request.protocolVersion !== 2 ||
    !request.mcp ||
    !(request.capabilities ?? []).includes("mcp")
  ) {
    throw failure(
      "RIVET_MCP_GRANT_REQUIRED",
      "This graph requires a current Wright MCP grant.",
    );
  }
  if (
    project.metadata.mcpServer &&
    Object.keys(project.metadata.mcpServer.mcpServers ?? {}).length > 0
  ) {
    throw failure(
      "RIVET_MCP_PROJECT_CONFIG_DENIED",
      "Project-provided MCP server configuration is denied.",
    );
  }
  if (mcpNodes.some((node) => node.type === "mcpGetPrompt")) {
    throw failure(
      "RIVET_MCP_PROJECT_CONFIG_DENIED",
      "MCP prompt operations are not authorized by this protocol.",
    );
  }
  const bindings = new Map(
    request.mcp.bindings.map((binding) => [binding.nodeId, binding]),
  );
  const toolNodes = mcpNodes.filter((node) => node.type === "mcpToolCall");
  for (const node of mcpNodes) {
    const data = node.data ?? {};
    if (containsSecretMaterial(data)) {
      throw failure(
        "RIVET_MCP_PROJECT_CONFIG_DENIED",
        "Secret-like MCP project configuration is denied.",
      );
    }
    if (
      data.useServerUrlInput === true ||
      data.useServerIdInput === true ||
      (typeof data.serverUrl === "string" && data.serverUrl.trim()) ||
      (typeof data.serverId === "string" && data.serverId.trim())
    ) {
      throw failure(
        "RIVET_MCP_PROJECT_CONFIG_DENIED",
        "Project-provided MCP connection details are denied.",
      );
    }
    if (node.type === "mcpDiscovery" && data.usePromptsOutput === true) {
      throw failure(
        "RIVET_MCP_PROJECT_CONFIG_DENIED",
        "MCP prompt discovery is not authorized by this protocol.",
      );
    }
    if (node.type === "mcpToolCall") {
      if (data.useToolNameInput === true) {
        throw failure(
          "RIVET_MCP_DYNAMIC_TOOL_DENIED",
          "Dynamic MCP tool names are not authorized.",
        );
      }
      const binding = bindings.get(node.id);
      if (!binding)
        throw failure(
          "RIVET_MCP_BINDING_MISSING",
          "A graph MCP node has no reviewed binding.",
        );
      if (data.toolName !== binding.qualifiedToolName) {
        throw failure(
          "RIVET_MCP_BINDING_MISMATCH",
          "The graph MCP tool no longer matches its reviewed binding.",
        );
      }
    }
  }
  const toolNodeIds = new Set(toolNodes.map((node) => node.id));
  if (
    request.mcp.bindings.some((binding) => !toolNodeIds.has(binding.nodeId))
  ) {
    throw failure(
      "RIVET_MCP_BINDING_EXTRA",
      "The Wright MCP grant contains an extra binding.",
    );
  }
  const transformed = structuredClone(project) as Project;
  for (const node of graphNodes(transformed, request.graph)) {
    if (node?.type === "mcpDiscovery") {
      node.data = {
        ...node.data,
        transportType: "http",
        serverUrl: `${request.mcp.bridgeBaseUrl}/mcp/${encodeURIComponent(request.mcp.discoveryHandle)}`,
        serverId: undefined,
      };
    } else if (node?.type === "mcpToolCall") {
      const binding = bindings.get(node.id)!;
      node.data = {
        ...node.data,
        transportType: "http",
        serverUrl: `${request.mcp.bridgeBaseUrl}/mcp/${encodeURIComponent(binding.handle)}`,
        serverId: undefined,
        toolName: binding.qualifiedToolName,
        useToolNameInput: false,
      };
    }
  }
  return transformed;
}

function providerHandle(serverUrl: string, grant: WrightMcpGrant): string {
  let url: URL;
  try {
    url = new URL(serverUrl);
  } catch {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The MCP node bridge address is invalid.",
    );
  }
  const base = new URL(grant.bridgeBaseUrl);
  const prefix = `${base.pathname}/mcp/`;
  if (
    url.origin !== base.origin ||
    !url.pathname.startsWith(prefix) ||
    url.search ||
    url.hash
  ) {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The MCP node bridge address is not authorized.",
    );
  }
  return decodeURIComponent(url.pathname.slice(prefix.length));
}

type BridgeTerminal = {
  type: "result";
  content?: MCP.ToolCallResponse["content"];
  structuredContent?: Record<string, unknown>;
  isError?: boolean;
  error?: { code?: string; message?: string };
};

async function readBridgeStream(
  response: Response,
  request: WrightRunnerRequest,
  binding?: WrightMcpBinding,
): Promise<BridgeTerminal> {
  if (!response.ok || !response.body) {
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The Wright MCP bridge denied the request.",
    );
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  let bytes = 0;
  let events = 0;
  let terminal: BridgeTerminal | undefined;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    bytes += value.byteLength;
    if (bytes > MAX_BRIDGE_RESPONSE_BYTES) {
      throw failure(
        "RIVET_MCP_RESULT_TOO_LARGE",
        "The Wright MCP bridge response exceeded its limit.",
      );
    }
    pending += decoder.decode(value, { stream: true });
    const lines = pending.split(/\r?\n/);
    pending = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      events += 1;
      if (
        events > MAX_BRIDGE_EVENTS ||
        Buffer.byteLength(line, "utf8") > MAX_EVENT_BYTES
      ) {
        throw failure(
          "RIVET_MCP_RESULT_TOO_LARGE",
          "The Wright MCP bridge event exceeded its limit.",
        );
      }
      let event: any;
      try {
        event = JSON.parse(line);
      } catch {
        throw failure(
          "RIVET_MCP_BRIDGE_DENIED",
          "The Wright MCP bridge returned an invalid event.",
        );
      }
      if (event?.type === "progress" || event?.type === "approval_required") {
        writeEvent({
          type: "progress",
          runId: request.runId,
          state: "running",
          phase:
            event.type === "approval_required"
              ? "mcp-approval-required"
              : `mcp-${event.phase ?? "child-progress"}`,
          nodeId: binding?.nodeId,
          callId: event.callId,
          bindingDigest: binding?.bindingDigest,
          status: event.status,
          title:
            typeof event.title === "string"
              ? event.title.slice(0, 256)
              : undefined,
          progress:
            typeof event.progress === "number" ? event.progress : undefined,
          approvalId: event.approvalId,
          approvalDigest: event.approvalDigest,
        });
      } else if (event?.type === "result") {
        terminal = event as BridgeTerminal;
      } else {
        throw failure(
          "RIVET_MCP_BRIDGE_DENIED",
          "The Wright MCP bridge returned an unsupported event.",
        );
      }
    }
  }
  if (!terminal)
    throw failure(
      "RIVET_MCP_BRIDGE_DENIED",
      "The Wright MCP bridge returned no terminal result.",
    );
  if (terminal.error) {
    const code = STABLE_RIVET_ERROR.test(terminal.error.code ?? "")
      ? terminal.error.code!
      : "RIVET_MCP_POLICY_DENIED";
    throw failure(code, "The Wright MCP call failed.");
  }
  return terminal;
}

function createWrightMcpProvider(
  request: WrightRunnerRequest,
  abortSignal: AbortSignal,
): MCPProvider | undefined {
  const grant = request.mcp;
  if (!grant) return undefined;
  const bindingsByHandle = new Map(
    grant.bindings.map((binding) => [binding.handle, binding]),
  );
  const post = async (
    operation: "discover" | "calls",
    body: Record<string, unknown>,
    binding?: WrightMcpBinding,
  ) => {
    const response = await fetch(`${grant.bridgeBaseUrl}/${operation}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${grant.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: abortSignal,
    });
    return readBridgeStream(response, request, binding);
  };
  const denyStdio = async (): Promise<never> => {
    throw failure(
      "RIVET_MCP_PROJECT_CONFIG_DENIED",
      "Direct MCP transports are not authorized.",
    );
  };
  const denyPrompts = async (): Promise<never> => {
    throw failure(
      "RIVET_MCP_PROJECT_CONFIG_DENIED",
      "MCP prompt operations are not authorized.",
    );
  };
  return {
    async getHTTPTools(_clientConfig, serverUrl) {
      const handle = providerHandle(serverUrl, grant);
      if (handle !== grant.discoveryHandle) {
        throw failure(
          "RIVET_MCP_BINDING_MISMATCH",
          "MCP discovery used an unauthorized handle.",
        );
      }
      const requestId = randomUUID();
      const terminal = await post("discover", {
        authorityId: grant.authorityId,
        runId: request.runId,
        discoveryHandle: grant.discoveryHandle,
        requestId,
      });
      const structured = terminal.structuredContent;
      if (!structured || !Array.isArray(structured.tools)) {
        throw failure(
          "RIVET_MCP_BRIDGE_DENIED",
          "The Wright MCP discovery response is invalid.",
        );
      }
      return structured.tools as MCP.Tool[];
    },
    getStdioTools: denyStdio,
    getHTTPPrompts: denyPrompts,
    getStdioPrompts: denyPrompts,
    async httpToolCall(_clientConfig, serverUrl, toolCall) {
      const handle = providerHandle(serverUrl, grant);
      const binding = bindingsByHandle.get(handle);
      if (!binding || toolCall.name !== binding.qualifiedToolName) {
        throw failure(
          "RIVET_MCP_BINDING_MISMATCH",
          "The MCP call no longer matches its reviewed binding.",
        );
      }
      const requestId = randomUUID();
      const terminal = await post(
        "calls",
        {
          authorityId: grant.authorityId,
          runId: request.runId,
          nodeHandle: binding.handle,
          bindingDigest: binding.bindingDigest,
          requestId,
          arguments: toolCall.arguments ?? {},
        },
        binding,
      );
      const content = Array.isArray(terminal.content)
        ? [...terminal.content]
        : [];
      if (terminal.structuredContent)
        content.push({
          type: "wright-structured",
          value: terminal.structuredContent,
        });
      return {
        content,
        structuredContent: terminal.structuredContent,
        isError: terminal.isError,
      };
    },
    stdioToolCall: denyStdio,
    getHTTPrompt: denyPrompts,
    getStdioPrompt: denyPrompts,
  };
}

function nodeLabel(event: any): Record<string, unknown> {
  return {
    nodeId: event?.node?.id,
    nodeType: event?.node?.type,
    nodeTitle: event?.node?.title,
  };
}

async function execute(request: WrightRunnerRequest): Promise<void> {
  validateRequest(request);
  if (request.ai?.token) OUTPUT_SECRETS.add(request.ai.token);
  if (request.mcp?.token) OUTPUT_SECRETS.add(request.mcp.token);
  await verifyProjectDigest(request);
  const loadedProject = await loadProjectFromFile(request.projectPath);
  const project = prepareMcpProject(
    prepareAiProject(loadedProject, request),
    request,
  );
  enforceCapabilities(project, request);
  installNetworkGuard(request);

  const abortController = new AbortController();
  const abort = () =>
    abortController.abort(
      failure("RIVET_RUNNER_CANCELLED", "Workflow run was cancelled."),
    );
  process.once("SIGINT", abort);
  process.once("SIGTERM", abort);

  writeEvent({
    type: "progress",
    runId: request.runId,
    state: "running",
    phase: "graph-starting",
  });
  const processor = createProcessor(project, {
    graph: request.graph,
    inputs: request.inputs ?? {},
    context: request.context ?? {},
    captureNodeTimings: true,
    projectPath: request.projectPath,
    abortSignal: abortController.signal,
    mcpProvider: createWrightMcpProvider(request, abortController.signal),
    openAiApiKey: request.ai?.token ?? "",
    customAiApiKey: request.ai?.token ?? "",
    openAiEndpoint: request.ai
      ? `${request.ai.baseUrl.replace(/\/$/, "")}/chat/completions`
      : "",
    getChatNodeEndpoint: request.ai
      ? async () => ({
          endpoint: `${request.ai!.baseUrl.replace(/\/$/, "")}/chat/completions`,
          headers: { Authorization: `Bearer ${request.ai!.token}` },
        })
      : undefined,
    onNodeStart: (event) => {
      const inputs = projectInspectionValues(event.inputs, "node_input");
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-start",
        ...nodeLabel(event),
        inputValues: inputs.values,
        inputComplete: inputs.complete,
        inputState: inputs.state,
        inputOmittedCount: inputs.omittedCount,
      });
    },
    onNodeFinish: (event) => {
      const outputs = projectInspectionValues(event.outputs, "node_output");
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-finish",
        ...nodeLabel(event),
        durationMs: event.durationMs,
        outputValues: outputs.values,
        outputComplete: outputs.complete,
        outputState: outputs.state,
        outputOmittedCount: outputs.omittedCount,
      });
    },
    onNodeError: (event) => {
      const eventError =
        stableRunnerError(event.error) ??
        (event.error instanceof Error
          ? event.error
          : new Error(String(event.error)));
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-error",
        errorCode: eventError.code,
        errorMessage: eventError.message,
        durationMs: event.durationMs,
        ...nodeLabel(event),
      });
    },
    onNodeExcluded: (event) => {
      const inputs = projectInspectionValues(event.inputs, "node_input");
      const outputs = projectInspectionValues(event.outputs, "node_output");
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-excluded",
        ...nodeLabel(event),
        exclusionReason:
          typeof event.reason === "string"
            ? event.reason.slice(0, 255)
            : undefined,
        inputValues: inputs.values,
        inputComplete: inputs.complete,
        inputState: inputs.state,
        inputOmittedCount: inputs.omittedCount,
        outputValues: outputs.values,
        outputComplete: outputs.complete,
        outputState: outputs.state,
        outputOmittedCount: outputs.omittedCount,
      });
    },
  });

  try {
    const outputs = await processor.run();
    const terminal = {
      type: "result",
      runId: request.runId,
      state: "succeeded",
      outputs,
    };
    if (
      Buffer.byteLength(JSON.stringify(terminal), "utf8") > MAX_OUTPUT_BYTES
    ) {
      throw failure(
        "RIVET_RUNNER_OUTPUT_TOO_LARGE",
        "Workflow output exceeded the configured limit.",
      );
    }
    writeEvent(terminal);
  } finally {
    processor.dispose();
    process.removeListener("SIGINT", abort);
    process.removeListener("SIGTERM", abort);
  }
}

async function main(): Promise<void> {
  let runId: string | undefined;
  try {
    const request = await readRequest();
    runId = request.runId;
    await execute(request);
  } catch (caught) {
    const outerError = caught as RunnerError;
    const error = stableRunnerError(caught) ?? outerError;
    const code =
      error.code ??
      (error.name === "AbortError"
        ? "RIVET_RUNNER_CANCELLED"
        : "RIVET_RUNNER_FAILED");
    const event = {
      type: "result",
      runId,
      state: code === "RIVET_RUNNER_CANCELLED" ? "cancelled" : "failed",
      error: {
        code,
        message: error.message || "Rivet workflow execution failed.",
      },
    };
    try {
      writeEvent(event);
    } catch {
      process.stdout.write(
        `${JSON.stringify({ type: "result", runId, state: "failed", error: { code: "RIVET_RUNNER_FAILED", message: "Runner failure." } })}\n`,
      );
    }
    process.exitCode = 1;
  }
}

void main();
