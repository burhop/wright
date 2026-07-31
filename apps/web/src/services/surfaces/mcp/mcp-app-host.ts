import {
  AppBridge,
  type McpUiHostCapabilities,
  type McpUiHostContext,
  type McpUiMessageRequest,
  type McpUiOpenLinkRequest,
  type McpUiResourceCsp,
  type McpUiResourcePermissions,
  type McpUiUpdateModelContextRequest,
} from "@modelcontextprotocol/ext-apps/app-bridge";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import type {
  CallToolRequest,
  CallToolResult,
  JSONRPCMessage,
  ListResourcesRequest,
  ListResourcesResult,
  ListResourceTemplatesRequest,
  ListResourceTemplatesResult,
  ReadResourceRequest,
  ReadResourceResult,
} from "@modelcontextprotocol/sdk/types.js";

import {
  MCP_SANDBOX_DEFAULT_ATTRIBUTE,
  MCP_SANDBOX_PROTOCOL_VERSION,
  type ValidatedSandboxPolicy,
} from "./sandbox-proxy";

const MAX_BRIDGE_MESSAGE_BYTES = 1_048_576;
const MAX_SEEN_REQUESTS = 2_048;
const TEARDOWN_TIMEOUT_MS = 1_500;

export type McpAppHostStatus =
  | "connecting"
  | "waiting_for_proxy"
  | "loading_resource"
  | "initializing"
  | "ready"
  | "tearing_down"
  | "closed"
  | "error";

export interface McpAppOperationContext {
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly surfaceId: string;
  readonly generation: number;
  readonly serverId: string;
  readonly signal: AbortSignal;
}

export interface McpAppGateway {
  callTool(
    params: CallToolRequest["params"],
    context: McpAppOperationContext,
  ): Promise<CallToolResult>;
  listResources(
    params: ListResourcesRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ListResourcesResult>;
  listResourceTemplates(
    params: ListResourceTemplatesRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ListResourceTemplatesResult>;
  readResource(
    params: ReadResourceRequest["params"],
    context: McpAppOperationContext,
  ): Promise<ReadResourceResult>;
  updateModelContext(
    params: McpUiUpdateModelContextRequest["params"],
    context: McpAppOperationContext,
  ): Promise<void>;
  sendUserMessage(
    params: McpUiMessageRequest["params"],
    context: McpAppOperationContext,
  ): Promise<void>;
  openExternalLink?(
    params: McpUiOpenLinkRequest["params"],
    context: McpAppOperationContext,
  ): Promise<void>;
}

export interface McpAppResourceDocument {
  readonly html: string;
  readonly mediaType: string;
  readonly csp?: McpUiResourceCsp;
  readonly grantedPermissions?: McpUiResourcePermissions;
}

export interface McpAppHostOptions {
  readonly frameWindow: Window;
  readonly sandboxOrigin: string;
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly surfaceId: string;
  readonly generation: number;
  readonly serverId: string;
  readonly nonce: string;
  readonly resource: McpAppResourceDocument;
  readonly policy: ValidatedSandboxPolicy;
  readonly gateway: McpAppGateway;
  readonly hostContext: McpUiHostContext;
  readonly initialToolInput?: Readonly<Record<string, unknown>>;
  readonly initialToolResult?: CallToolResult;
  readonly enabledHostCapabilities?: ReadonlySet<
    "context.update" | "user.message" | "open.link"
  >;
  readonly eventWindow?: Window;
  readonly onStatus?: (status: McpAppHostStatus, detail?: string) => void;
  readonly onSizeChange?: (size: { width?: number; height?: number }) => void;
  readonly onRequestTeardown?: () => void;
  readonly onSecurityViolation?: (reason: string) => void;
}

interface WrightEnvelope {
  readonly version: typeof MCP_SANDBOX_PROTOCOL_VERSION;
  readonly surfaceId: string;
  readonly generation: number;
  readonly nonce: string;
}

interface EnvelopedMessage extends Record<string, unknown> {
  readonly _wright: WrightEnvelope;
}

export class McpAppHostError extends Error {
  readonly code: string;

  constructor(
    code: string,
    message: string,
  ) {
    super(message);
    this.code = code;
    this.name = "McpAppHostError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isJsonRpcMessage(value: unknown): value is JSONRPCMessage {
  if (!isRecord(value) || value.jsonrpc !== "2.0") return false;
  if (typeof value.method === "string") {
    return value.id === undefined || typeof value.id === "string" || typeof value.id === "number";
  }
  if (value.id === undefined || (typeof value.id !== "string" && typeof value.id !== "number")) {
    return false;
  }
  return "result" in value || "error" in value;
}

function serializedSize(value: unknown): number {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

function exactOrigin(value: string): string {
  const parsed = new URL(value);
  if (parsed.origin === "null" || parsed.href !== `${parsed.origin}/`) {
    throw new TypeError("sandboxOrigin must be an exact HTTP(S) origin");
  }
  if (
    parsed.protocol !== "https:" &&
    parsed.hostname !== "localhost" &&
    !parsed.hostname.endsWith(".localhost")
  ) {
    throw new TypeError("sandboxOrigin must use HTTPS outside localhost development");
  }
  return parsed.origin;
}

export class ExactOriginPostMessageTransport implements Transport {
  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: <T extends JSONRPCMessage>(message: T) => void;
  readonly sessionId: string;

  private started = false;
  private closed = false;
  private readonly seenRequestIds = new Set<string>();
  private readonly targetOrigin: string;
  private readonly envelope: WrightEnvelope;
  private readonly listener: (event: MessageEvent) => void;
  private readonly eventTarget: Window;
  private readonly eventSource: Window;
  private readonly eventWindow: Window;
  private readonly onSecurityViolation: (reason: string) => void;

  constructor(
    eventTarget: Window,
    eventSource: Window,
    surface: Pick<
      McpAppHostOptions,
      "sandboxOrigin" | "surfaceId" | "generation" | "nonce"
    >,
    eventWindow: Window = window,
    onSecurityViolation: (reason: string) => void = () => undefined,
  ) {
    this.eventTarget = eventTarget;
    this.eventSource = eventSource;
    this.eventWindow = eventWindow;
    this.onSecurityViolation = onSecurityViolation;
    this.targetOrigin = exactOrigin(surface.sandboxOrigin);
    this.sessionId = `${surface.surfaceId}:${surface.generation}`;
    this.envelope = Object.freeze({
      version: MCP_SANDBOX_PROTOCOL_VERSION,
      surfaceId: surface.surfaceId,
      generation: surface.generation,
      nonce: surface.nonce,
    });
    this.listener = (event) => this.receive(event);
  }

  async start(): Promise<void> {
    if (this.closed) throw new Error("MCP App transport is closed");
    if (this.started) throw new Error("MCP App transport is already started");
    this.started = true;
    this.eventWindow.addEventListener("message", this.listener);
  }

  async send(message: JSONRPCMessage): Promise<void> {
    if (!this.started || this.closed) {
      throw new Error("MCP App transport is not active");
    }
    const outgoing = { ...message, _wright: this.envelope };
    if (serializedSize(outgoing) > MAX_BRIDGE_MESSAGE_BYTES) {
      throw new McpAppHostError(
        "MCP_APP_MESSAGE_TOO_LARGE",
        "MCP App message exceeds the 1 MiB host limit",
      );
    }
    this.eventTarget.postMessage(outgoing, this.targetOrigin);
  }

  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    if (this.started) this.eventWindow.removeEventListener("message", this.listener);
    this.onclose?.();
  }

  private reject(reason: string): void {
    this.onSecurityViolation(reason);
  }

  private receive(event: MessageEvent): void {
    if (this.closed) return;
    if (event.source !== this.eventSource) {
      this.reject("wrong_source");
      return;
    }
    if (event.origin !== this.targetOrigin) {
      this.reject("wrong_origin");
      return;
    }
    if (serializedSize(event.data) > MAX_BRIDGE_MESSAGE_BYTES) {
      this.reject("message_too_large");
      this.onerror?.(new Error("MCP App message exceeds the host limit"));
      return;
    }
    if (!isRecord(event.data)) {
      this.reject("malformed_message");
      return;
    }
    const envelope = event.data._wright;
    if (
      !isRecord(envelope) ||
      envelope.version !== this.envelope.version ||
      envelope.surfaceId !== this.envelope.surfaceId ||
      envelope.generation !== this.envelope.generation ||
      envelope.nonce !== this.envelope.nonce
    ) {
      this.reject("stale_or_invalid_envelope");
      return;
    }
    const message: Record<string, unknown> = { ...(event.data as EnvelopedMessage) };
    delete message._wright;
    if (!isJsonRpcMessage(message)) {
      this.reject("malformed_json_rpc");
      return;
    }
    if ("method" in message && "id" in message && message.id !== undefined) {
      const key = `${typeof message.id}:${String(message.id)}`;
      if (this.seenRequestIds.has(key)) {
        this.reject("replayed_request");
        return;
      }
      if (this.seenRequestIds.size >= MAX_SEEN_REQUESTS) {
        this.reject("request_window_exhausted");
        return;
      }
      this.seenRequestIds.add(key);
    }
    this.onmessage?.(message);
  }
}

function combinedSignal(
  hostSignal: AbortSignal,
  requestSignal: AbortSignal,
): { signal: AbortSignal; dispose: () => void } {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (hostSignal.aborted || requestSignal.aborted) controller.abort();
  hostSignal.addEventListener("abort", abort, { once: true });
  requestSignal.addEventListener("abort", abort, { once: true });
  return {
    signal: controller.signal,
    dispose: () => {
      hostSignal.removeEventListener("abort", abort);
      requestSignal.removeEventListener("abort", abort);
    },
  };
}

export class McpAppHost {
  private readonly bridge: AppBridge;
  private readonly transport: ExactOriginPostMessageTransport;
  private readonly lifetime = new AbortController();
  private status: McpAppHostStatus = "connecting";
  private initialized = false;
  private resourceSent = false;
  private closed = false;
  private pendingContext: McpUiHostContext | null = null;
  private readonly options: McpAppHostOptions;

  constructor(options: McpAppHostOptions) {
    this.options = options;
    if (options.resource.mediaType.toLowerCase() !== "text/html;profile=mcp-app") {
      throw new McpAppHostError(
        "MCP_APP_MEDIA_TYPE_UNSUPPORTED",
        `Unsupported MCP App media type: ${options.resource.mediaType}`,
      );
    }
    if (options.resource.html.length === 0) {
      throw new McpAppHostError("MCP_APP_RESOURCE_EMPTY", "MCP App resource is empty");
    }
    const enabled = options.enabledHostCapabilities || new Set();
    const capabilities: McpUiHostCapabilities = {
      serverTools: {},
      serverResources: {},
      sandbox: {
        csp: {
          connectDomains: [...options.policy.csp.connectDomains],
          resourceDomains: [...options.policy.csp.resourceDomains],
          frameDomains: [...options.policy.csp.frameDomains],
          baseUriDomains: [...options.policy.csp.baseUriDomains],
        },
        permissions: options.policy.permissions,
      },
      ...(enabled.has("context.update")
        ? {
            updateModelContext: {
              text: {},
              image: {},
              resource: {},
              resourceLink: {},
              structuredContent: {},
            },
          }
        : {}),
      ...(enabled.has("user.message")
        ? { message: { text: {}, image: {}, resource: {}, resourceLink: {} } }
        : {}),
      logging: {},
      ...(enabled.has("open.link") && options.gateway.openExternalLink
        ? { openLinks: {} }
        : {}),
    };
    this.bridge = new AppBridge(
      null,
      { name: "Wright", version: "1" },
      capabilities,
      { hostContext: options.hostContext },
    );
    this.transport = new ExactOriginPostMessageTransport(
      options.frameWindow,
      options.frameWindow,
      options,
      options.eventWindow,
      options.onSecurityViolation,
    );
    this.installHandlers();
  }

  get currentStatus(): McpAppHostStatus {
    return this.status;
  }

  async connect(): Promise<void> {
    this.assertOpen();
    this.transition("connecting");
    try {
      await this.bridge.connect(this.transport);
      this.transition("waiting_for_proxy");
    } catch (reason) {
      this.transition("error", reason instanceof Error ? reason.message : String(reason));
      throw reason;
    }
  }

  updateHostContext(context: McpUiHostContext): void {
    this.assertOpen();
    if (!this.initialized) {
      this.pendingContext = context;
      return;
    }
    this.bridge.setHostContext(context);
  }

  async teardown(): Promise<void> {
    if (this.closed) return;
    this.transition("tearing_down");
    this.lifetime.abort();
    if (this.initialized) {
      try {
        await this.bridge.teardownResource({}, { timeout: TEARDOWN_TIMEOUT_MS });
      } catch {
        // Teardown is bounded and best-effort; closing the transport revokes authority.
      }
    }
    this.closed = true;
    await this.bridge.close();
    this.transition("closed");
  }

  private installHandlers(): void {
    this.bridge.addEventListener("sandboxready", () => {
      if (this.closed || this.resourceSent) return;
      this.resourceSent = true;
      this.transition("loading_resource");
      void this.bridge
        .sendSandboxResourceReady({
          html: this.options.resource.html,
          sandbox: MCP_SANDBOX_DEFAULT_ATTRIBUTE,
          csp: {
            connectDomains: [...this.options.policy.csp.connectDomains],
            resourceDomains: [...this.options.policy.csp.resourceDomains],
            frameDomains: [...this.options.policy.csp.frameDomains],
            baseUriDomains: [...this.options.policy.csp.baseUriDomains],
          },
          permissions: this.options.policy.permissions,
        })
        .then(() => this.transition("initializing"))
        .catch((reason) =>
          this.transition("error", reason instanceof Error ? reason.message : String(reason)),
        );
    });
    this.bridge.addEventListener("initialized", () => {
      if (this.closed || this.initialized) return;
      this.initialized = true;
      this.transition("ready");
      if (this.pendingContext) {
        this.bridge.setHostContext(this.pendingContext);
        this.pendingContext = null;
      }
      void this.sendInitialToolState();
    });
    this.bridge.addEventListener("sizechange", (size) => this.options.onSizeChange?.(size));
    this.bridge.addEventListener("requestteardown", () => this.options.onRequestTeardown?.());

    this.bridge.oncalltool = (params, extra) =>
      this.operation(extra.signal, (context) => this.options.gateway.callTool(params, context));
    this.bridge.onlistresources = (params, extra) =>
      this.operation(extra.signal, (context) => this.options.gateway.listResources(params, context));
    this.bridge.onlistresourcetemplates = (params, extra) =>
      this.operation(extra.signal, (context) =>
        this.options.gateway.listResourceTemplates(params, context),
      );
    this.bridge.onreadresource = (params, extra) =>
      this.operation(extra.signal, (context) => this.options.gateway.readResource(params, context));
    if (this.options.enabledHostCapabilities?.has("context.update")) {
      this.bridge.onupdatemodelcontext = (params, extra) =>
        this.operation(extra.signal, async (context) => {
          await this.options.gateway.updateModelContext(params, context);
          return {};
        });
    }
    if (this.options.enabledHostCapabilities?.has("user.message")) {
      this.bridge.onmessage = (params, extra) =>
        this.operation(extra.signal, async (context) => {
          await this.options.gateway.sendUserMessage(params, context);
          return {};
        });
    }
    if (
      this.options.enabledHostCapabilities?.has("open.link") &&
      this.options.gateway.openExternalLink
    ) {
      this.bridge.onopenlink = (params, extra) =>
        this.operation(extra.signal, async (context) => {
          await this.options.gateway.openExternalLink?.(params, context);
          return {};
        });
    }
  }

  private async sendInitialToolState(): Promise<void> {
    if (this.options.initialToolInput) {
      await this.bridge.sendToolInput({ arguments: { ...this.options.initialToolInput } });
    }
    if (this.options.initialToolResult) {
      await this.bridge.sendToolResult(this.options.initialToolResult);
    }
  }

  private async operation<T>(
    requestSignal: AbortSignal,
    invoke: (context: McpAppOperationContext) => Promise<T>,
  ): Promise<T> {
    if (!this.initialized) {
      throw new McpAppHostError(
        "MCP_APP_NOT_READY",
        "MCP App operation was requested before initialization completed",
      );
    }
    this.assertOpen();
    const scope = combinedSignal(this.lifetime.signal, requestSignal);
    try {
      return await invoke({
        workspaceId: this.options.workspaceId,
        sessionId: this.options.sessionId,
        surfaceId: this.options.surfaceId,
        generation: this.options.generation,
        serverId: this.options.serverId,
        signal: scope.signal,
      });
    } finally {
      scope.dispose();
    }
  }

  private assertOpen(): void {
    if (this.closed || this.lifetime.signal.aborted) {
      throw new McpAppHostError("MCP_APP_CLOSED", "MCP App host is closed");
    }
  }

  private transition(status: McpAppHostStatus, detail?: string): void {
    this.status = status;
    this.options.onStatus?.(status, detail);
  }
}
