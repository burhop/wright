import { createHash, randomUUID } from "node:crypto";
import { isAbsolute } from "node:path";
import { readFile } from "node:fs/promises";

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
const STABLE_RIVET_ERROR = /^RIVET_[A-Z0-9_]{1,64}$/;
const OUTPUT_SECRETS = new Set<string>();

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

function projectNodeTypes(project: Project): Set<string> {
  const types = new Set<string>();
  for (const graph of Object.values(project.graphs ?? {})) {
    const nodes = Array.isArray(graph.nodes)
      ? graph.nodes
      : Object.values(graph.nodes ?? {});
    for (const node of nodes) {
      if (node && typeof node.type === "string") types.add(node.type);
    }
  }
  return types;
}

function enforceCapabilities(
  project: Project,
  request: WrightRunnerRequest,
): void {
  const granted = new Set(request.capabilities ?? []);
  if (request.ai) granted.add("ai");
  const nodeTypes = projectNodeTypes(project);
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
      return { content, isError: terminal.isError };
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
  const project = prepareMcpProject(loadedProject, request);
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
    onNodeStart: (event) =>
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-start",
        ...nodeLabel(event),
      }),
    onNodeFinish: (event) =>
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-finish",
        ...nodeLabel(event),
      }),
    onNodeError: (event) =>
      writeEvent({
        type: "progress",
        runId: request.runId,
        state: "running",
        phase: "node-error",
        ...nodeLabel(event),
      }),
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
    const error = caught as RunnerError;
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
