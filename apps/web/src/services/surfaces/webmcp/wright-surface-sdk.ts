import { surfaceRequestId } from "../ids";

const MAX_MESSAGE_BYTES = 1_048_576;

export interface WrightSurfaceToolCallContext {
  readonly signal: AbortSignal;
}

export interface WrightSurfaceTool {
  readonly name: string;
  readonly description: string;
  readonly inputSchema: Readonly<Record<string, unknown>>;
  readonly handler: (
    argumentsValue: Readonly<Record<string, unknown>>,
    context: WrightSurfaceToolCallContext,
  ) =>
    | Promise<Readonly<Record<string, unknown>>>
    | Readonly<Record<string, unknown>>;
  readonly signal: AbortSignal;
}

export interface WrightSurfaceRegistration {
  readonly dispose: () => Promise<void>;
}

interface SurfaceBinding {
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly surfaceId: string;
  readonly instanceId: string;
  readonly generation: number;
  readonly documentOrigin: string;
  readonly serverId: string;
}

interface SurfaceMessage extends Record<string, unknown> {
  protocolVersion: "1.0";
  kind: "request" | "result" | "error" | "event" | "cancel";
  messageId: string;
  correlationId: string;
  replyTo?: string;
  binding: SurfaceBinding;
  operation: string;
  toolName?: string;
  sequence: number;
  createdAt: string;
  deadlineAt: string;
  payload?: unknown;
  error?: { code: string; message: string; retryable: boolean };
}

type SocketFactory = (url: string) => WebSocket;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function encodedSize(value: unknown): number {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

function socketUrl(origin: string): string {
  const value = new URL(origin);
  value.protocol = value.protocol === "https:" ? "wss:" : "ws:";
  value.pathname = "/__wright/webmcp";
  return value.href;
}

export class WrightSurfaceSdk {
  private socket: WebSocket | null = null;
  private binding: SurfaceBinding | null = null;
  private connectPromise: Promise<void> | null = null;
  private connectResolve: (() => void) | null = null;
  private connectReject: ((reason: unknown) => void) | null = null;
  private readonly registrations = new Map<string, WrightSurfaceTool>();
  private readonly control = new Map<
    string,
    { resolve: () => void; reject: (reason: unknown) => void }
  >();
  private readonly calls = new Map<string, AbortController>();
  private readonly socketFactory: SocketFactory;
  private readonly origin: string;
  private readonly pageHide: () => void;

  constructor(
    options: { origin?: string; socketFactory?: SocketFactory } = {},
  ) {
    this.origin = new URL(options.origin || window.location.origin).origin;
    this.socketFactory = options.socketFactory || ((url) => new WebSocket(url));
    this.pageHide = () => this.dispose();
    window.addEventListener("pagehide", this.pageHide);
  }

  async registerTool(
    tool: WrightSurfaceTool,
  ): Promise<WrightSurfaceRegistration> {
    this.validateTool(tool);
    if (tool.signal.aborted)
      throw new DOMException("Registration aborted", "AbortError");
    await this.connect();
    const message = this.message("request", "webmcp.register", tool.name, {
      tool: {
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      },
    });
    await this.controlRequest(message);
    this.registrations.set(tool.name, tool);
    const abort = () => void this.unregister(tool.name);
    tool.signal.addEventListener("abort", abort, { once: true });
    let disposed = false;
    return {
      dispose: async () => {
        if (disposed) return;
        disposed = true;
        tool.signal.removeEventListener("abort", abort);
        await this.unregister(tool.name);
      },
    };
  }

  dispose(): void {
    window.removeEventListener("pagehide", this.pageHide);
    for (const controller of this.calls.values()) controller.abort();
    this.calls.clear();
    this.registrations.clear();
    this.control.clear();
    this.socket?.close();
    this.socket = null;
    this.binding = null;
  }

  private async connect(): Promise<void> {
    if (this.binding && this.socket?.readyState === WebSocket.OPEN) return;
    if (this.connectPromise) return this.connectPromise;
    this.connectPromise = new Promise<void>((resolve, reject) => {
      this.connectResolve = resolve;
      this.connectReject = reject;
    });
    const socket = this.socketFactory(socketUrl(this.origin));
    this.socket = socket;
    socket.addEventListener("message", (event) =>
      this.receive(String(event.data)),
    );
    socket.addEventListener("error", () =>
      this.failConnection(new Error("WebMCP connection failed")),
    );
    socket.addEventListener("close", () =>
      this.failConnection(new Error("WebMCP connection closed")),
    );
    return this.connectPromise;
  }

  private failConnection(reason: Error): void {
    this.connectReject?.(reason);
    this.connectResolve = null;
    this.connectReject = null;
    this.connectPromise = null;
    for (const pending of this.control.values()) pending.reject(reason);
    this.control.clear();
    for (const controller of this.calls.values()) controller.abort();
    this.calls.clear();
    this.registrations.clear();
    this.binding = null;
  }

  private receive(raw: string): void {
    if (new TextEncoder().encode(raw).byteLength > MAX_MESSAGE_BYTES) return;
    let message: SurfaceMessage;
    try {
      const parsed: unknown = JSON.parse(raw);
      if (!isRecord(parsed) || parsed.protocolVersion !== "1.0") return;
      message = parsed as SurfaceMessage;
    } catch {
      return;
    }
    if (message.operation === "webmcp.connected" && message.kind === "event") {
      if (message.binding.documentOrigin !== this.origin) {
        this.failConnection(new Error("WebMCP binding origin mismatch"));
        return;
      }
      this.binding = Object.freeze({ ...message.binding });
      this.connectResolve?.();
      this.connectResolve = null;
      this.connectReject = null;
      return;
    }
    if (
      !this.binding ||
      JSON.stringify(message.binding) !== JSON.stringify(this.binding)
    )
      return;
    if (message.replyTo && this.control.has(message.replyTo)) {
      const pending = this.control.get(message.replyTo)!;
      this.control.delete(message.replyTo);
      if (message.kind === "error")
        pending.reject(
          new Error(message.error?.message || "WebMCP request failed"),
        );
      else pending.resolve();
      return;
    }
    if (message.kind === "cancel" && message.replyTo) {
      this.calls.get(message.replyTo)?.abort();
      return;
    }
    if (
      message.kind === "request" &&
      message.operation === "webmcp.tool.call"
    ) {
      void this.invoke(message);
    }
  }

  private async invoke(message: SurfaceMessage): Promise<void> {
    const tool = message.toolName
      ? this.registrations.get(message.toolName)
      : undefined;
    if (!tool || !isRecord(message.payload)) return;
    const controller = new AbortController();
    this.calls.set(message.messageId, controller);
    try {
      const result = await tool.handler(message.payload, {
        signal: controller.signal,
      });
      if (!isRecord(result) || encodedSize(result) > MAX_MESSAGE_BYTES) {
        throw new Error("WebMCP result must be a bounded object");
      }
      this.send(this.reply(message, "result", result));
    } catch (reason) {
      if (!controller.signal.aborted) {
        this.send(this.reply(message, "error", undefined, reason));
      }
    } finally {
      this.calls.delete(message.messageId);
    }
  }

  private async unregister(toolName: string): Promise<void> {
    const tool = this.registrations.get(toolName);
    if (!tool || !this.binding || this.socket?.readyState !== WebSocket.OPEN) {
      this.registrations.delete(toolName);
      return;
    }
    this.registrations.delete(toolName);
    const message = this.message("request", "webmcp.unregister", toolName, {
      tool: {
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      },
    });
    await this.controlRequest(message).catch(() => undefined);
  }

  private controlRequest(message: SurfaceMessage): Promise<void> {
    return new Promise((resolve, reject) => {
      this.control.set(message.messageId, { resolve, reject });
      try {
        this.send(message);
      } catch (reason) {
        this.control.delete(message.messageId);
        reject(reason);
      }
    });
  }

  private message(
    kind: SurfaceMessage["kind"],
    operation: string,
    toolName: string,
    payload?: unknown,
  ): SurfaceMessage {
    if (!this.binding) throw new Error("WebMCP connection is not bound");
    const now = new Date();
    return {
      protocolVersion: "1.0",
      kind,
      messageId: surfaceRequestId(),
      correlationId: surfaceRequestId(),
      binding: this.binding,
      operation,
      toolName,
      sequence: 0,
      createdAt: now.toISOString(),
      deadlineAt: new Date(now.getTime() + 30_000).toISOString(),
      ...(payload === undefined ? {} : { payload }),
    };
  }

  private reply(
    request: SurfaceMessage,
    kind: "result" | "error",
    payload?: unknown,
    reason?: unknown,
  ): SurfaceMessage {
    const message = this.message(
      kind,
      `webmcp.tool.${kind}`,
      request.toolName || "unknown",
      payload,
    );
    message.replyTo = request.messageId;
    message.correlationId = request.correlationId;
    if (kind === "error") {
      message.error = {
        code: "SURFACE_PROTOCOL_WEBMCP_HANDLER_FAILED",
        message:
          reason instanceof Error
            ? reason.message.slice(0, 2048)
            : "WebMCP handler failed",
        retryable: false,
      };
    }
    return message;
  }

  private send(message: SurfaceMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("WebMCP socket is not open");
    }
    if (encodedSize(message) > MAX_MESSAGE_BYTES)
      throw new Error("WebMCP message is too large");
    this.socket.send(JSON.stringify(message));
  }

  private validateTool(tool: WrightSurfaceTool): void {
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(tool.name)) {
      throw new TypeError("WebMCP tool name is invalid");
    }
    if (
      tool.description.length > 2048 ||
      encodedSize(tool.inputSchema) > 64 * 1024
    ) {
      throw new TypeError("WebMCP tool declaration exceeds its limit");
    }
  }
}
