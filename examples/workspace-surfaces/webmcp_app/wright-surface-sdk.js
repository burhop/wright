// Wright Surface SDK protocol 1.0 reference client. It does not modify document.modelContext.
const MAX_BYTES = 1_048_576;
const size = (value) => new TextEncoder().encode(JSON.stringify(value)).byteLength;
const record = (value) => typeof value === "object" && value !== null && !Array.isArray(value);

export class WrightSurfaceSdk {
  #socket;
  #binding;
  #ready;
  #resolveReady;
  #tools = new Map();
  #pending = new Map();
  #calls = new Map();

  constructor(origin = location.origin) {
    const url = new URL("/__wright/webmcp", origin);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    this.#ready = new Promise((resolve) => (this.#resolveReady = resolve));
    this.#socket = new WebSocket(url);
    this.#socket.addEventListener("message", (event) => this.#receive(String(event.data)));
    addEventListener("pagehide", () => this.dispose(), { once: true });
  }

  async registerTool(tool) {
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(tool.name)) throw new TypeError("Invalid tool name");
    if (tool.signal.aborted) throw new DOMException("Registration aborted", "AbortError");
    await this.#ready;
    await this.#control("webmcp.register", tool, { tool: this.#declaration(tool) });
    this.#tools.set(tool.name, tool);
    const abort = () => void this.#unregister(tool.name);
    tool.signal.addEventListener("abort", abort, { once: true });
    return { dispose: () => this.#unregister(tool.name) };
  }

  dispose() {
    for (const controller of this.#calls.values()) controller.abort();
    this.#calls.clear();
    this.#tools.clear();
    this.#pending.clear();
    this.#socket.close();
  }

  async #unregister(name) {
    const tool = this.#tools.get(name);
    this.#tools.delete(name);
    if (tool && this.#binding && this.#socket.readyState === WebSocket.OPEN) {
      await this.#control("webmcp.unregister", tool, { tool: this.#declaration(tool) }).catch(() => undefined);
    }
  }

  #declaration(tool) {
    return { name: tool.name, description: tool.description, inputSchema: tool.inputSchema };
  }

  #message(kind, operation, toolName, payload) {
    const now = new Date();
    return {
      protocolVersion: "1.0", kind, operation, toolName,
      messageId: crypto.randomUUID(), correlationId: crypto.randomUUID(),
      binding: this.#binding, sequence: 0, createdAt: now.toISOString(),
      deadlineAt: new Date(now.getTime() + 30_000).toISOString(), payload,
    };
  }

  #control(operation, tool, payload) {
    const message = this.#message("request", operation, tool.name, payload);
    return new Promise((resolve, reject) => {
      this.#pending.set(message.messageId, { resolve, reject });
      this.#send(message);
    });
  }

  async #invoke(message) {
    const tool = this.#tools.get(message.toolName);
    if (!tool || !record(message.payload)) return;
    const controller = new AbortController();
    this.#calls.set(message.messageId, controller);
    try {
      const result = await tool.handler(message.payload, { signal: controller.signal });
      if (!record(result) || size(result) > MAX_BYTES) throw new Error("Result must be a bounded object");
      const reply = this.#message("result", "webmcp.tool.result", message.toolName, result);
      reply.replyTo = message.messageId;
      reply.correlationId = message.correlationId;
      this.#send(reply);
    } catch (error) {
      if (!controller.signal.aborted) {
        const reply = this.#message("error", "webmcp.tool.error", message.toolName);
        reply.replyTo = message.messageId;
        reply.correlationId = message.correlationId;
        reply.error = { code: "SURFACE_PROTOCOL_WEBMCP_HANDLER_FAILED", message: String(error).slice(0, 2048), retryable: false };
        this.#send(reply);
      }
    } finally {
      this.#calls.delete(message.messageId);
    }
  }

  #receive(raw) {
    if (new TextEncoder().encode(raw).byteLength > MAX_BYTES) return;
    let message;
    try { message = JSON.parse(raw); } catch { return; }
    if (message.operation === "webmcp.connected" && message.kind === "event") {
      if (message.binding.documentOrigin !== location.origin) return this.dispose();
      this.#binding = Object.freeze({ ...message.binding });
      this.#resolveReady();
      return;
    }
    if (!this.#binding || JSON.stringify(message.binding) !== JSON.stringify(this.#binding)) return;
    if (message.replyTo && this.#pending.has(message.replyTo)) {
      const pending = this.#pending.get(message.replyTo);
      this.#pending.delete(message.replyTo);
      return message.kind === "error" ? pending.reject(new Error(message.error?.message || "Denied")) : pending.resolve();
    }
    if (message.kind === "cancel" && message.replyTo) return this.#calls.get(message.replyTo)?.abort();
    if (message.kind === "request" && message.operation === "webmcp.tool.call") void this.#invoke(message);
  }

  #send(message) {
    if (size(message) > MAX_BYTES) throw new Error("Message too large");
    this.#socket.send(JSON.stringify(message));
  }
}
