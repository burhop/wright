import { describe, expect, it, vi } from "vitest";

import { WrightSurfaceSdk } from "./wright-surface-sdk";

const binding = {
  workspaceId: "workspace-1",
  sessionId: "session-1",
  surfaceId: "surface-1",
  instanceId: "instance-1",
  generation: 2,
  documentOrigin: "https://s-one.preview.example.test",
  serverId: "web-app",
};

function message(
  operation: string,
  kind: "request" | "result" | "event" | "cancel",
  overrides: Record<string, unknown> = {},
) {
  return {
    protocolVersion: "1.0",
    kind,
    messageId: crypto.randomUUID(),
    correlationId: crypto.randomUUID(),
    binding,
    operation,
    sequence: 0,
    createdAt: new Date().toISOString(),
    deadlineAt: new Date(Date.now() + 30_000).toISOString(),
    ...overrides,
  };
}

class Socket {
  readyState: number = WebSocket.OPEN;
  readonly sent: string[] = [];
  private readonly listeners = new Map<
    string,
    ((event: MessageEvent) => void)[]
  >();

  addEventListener(name: string, listener: EventListenerOrEventListenerObject) {
    const callback = listener as (event: MessageEvent) => void;
    this.listeners.set(name, [...(this.listeners.get(name) || []), callback]);
  }

  send(value: string) {
    this.sent.push(value);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
  }

  emit(value: unknown) {
    for (const listener of this.listeners.get("message") || []) {
      listener({ data: JSON.stringify(value) } as MessageEvent);
    }
  }
}

async function registered() {
  const socket = new Socket();
  const sdk = new WrightSurfaceSdk({
    origin: binding.documentOrigin,
    socketFactory: () => socket as unknown as WebSocket,
  });
  const controller = new AbortController();
  const handler = vi.fn(async ({ partId }) => ({ selected: partId }));
  const promise = sdk.registerTool({
    name: "select_part",
    description: "Select a visible part",
    inputSchema: { type: "object" },
    handler,
    signal: controller.signal,
  });
  socket.emit(message("webmcp.connected", "event"));
  await vi.waitFor(() => expect(socket.sent).toHaveLength(1));
  const request = JSON.parse(socket.sent[0]);
  socket.emit(
    message("webmcp.register.result", "result", {
      replyTo: request.messageId,
      correlationId: request.correlationId,
      toolName: "select_part",
      payload: { registered: true },
    }),
  );
  return { sdk, socket, controller, handler, registration: await promise };
}

describe("WrightSurfaceSdk", () => {
  it("registers and invokes only the exact scoped tool without global events", async () => {
    const current = await registered();
    const request = message("webmcp.tool.call", "request", {
      toolName: "select_part",
      payload: { partId: "part-7" },
    });
    current.socket.emit(request);
    await vi.waitFor(() => expect(current.handler).toHaveBeenCalledOnce());
    await vi.waitFor(() => expect(current.socket.sent).toHaveLength(2));
    const result = JSON.parse(current.socket.sent[1]);
    expect(result).toMatchObject({
      kind: "result",
      replyTo: request.messageId,
      operation: "webmcp.tool.result",
      payload: { selected: "part-7" },
      binding,
    });
    current.sdk.dispose();
  });

  it("unregisters on abort and ignores stale-origin calls", async () => {
    const current = await registered();
    current.socket.emit(
      message("webmcp.tool.call", "request", {
        binding: { ...binding, generation: 3 },
        toolName: "select_part",
        payload: { partId: "stale" },
      }),
    );
    expect(current.handler).not.toHaveBeenCalled();
    current.controller.abort();
    await vi.waitFor(() => expect(current.socket.sent).toHaveLength(2));
    const unregister = JSON.parse(current.socket.sent[1]);
    expect(unregister.operation).toBe("webmcp.unregister");
    current.socket.emit(
      message("webmcp.unregister.result", "result", {
        replyTo: unregister.messageId,
        correlationId: unregister.correlationId,
        toolName: "select_part",
        payload: { unregistered: true },
      }),
    );
    current.sdk.dispose();
  });
});
