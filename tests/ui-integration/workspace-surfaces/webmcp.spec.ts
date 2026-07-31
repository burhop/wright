import { expect, test, type Page } from "@playwright/test";

async function installFakeSocket(page: Page): Promise<void> {
  await page.addInitScript(() => {
    class FakeSocket extends EventTarget {
      static readonly OPEN = 1;
      static readonly CLOSED = 3;
      readyState = FakeSocket.OPEN;
      readonly sent: string[] = [];

      constructor(readonly url: string) {
        super();
        (window as any).__webmcpSockets = [
          ...((window as any).__webmcpSockets || []),
          this,
        ];
      }

      send(value: string) {
        this.sent.push(value);
      }

      close() {
        this.readyState = FakeSocket.CLOSED;
        this.dispatchEvent(new Event("close"));
      }

      emit(value: unknown) {
        this.dispatchEvent(
          new MessageEvent("message", { data: JSON.stringify(value) }),
        );
      }
    }
    (window as any).WebSocket = FakeSocket;
  });
}

async function register(page: Page, surfaceId: string): Promise<void> {
  await page.goto("/");
  await page.evaluate(async (selectedSurface) => {
    const module = await import(
      "/src/services/surfaces/webmcp/wright-surface-sdk.ts"
    );
    const sdk = new module.WrightSurfaceSdk({ origin: location.origin });
    const controller = new AbortController();
    (window as any).__webmcp = { sdk, controller, calls: [] as unknown[] };
    const promise = sdk.registerTool({
      name: "select_part",
      description: "Select a visible part",
      inputSchema: { type: "object" },
      signal: controller.signal,
      handler: async (argumentsValue: unknown) => {
        (window as any).__webmcp.calls.push(argumentsValue);
        return { selected: true };
      },
    });
    const socket = (window as any).__webmcpSockets.find((candidate: any) =>
      candidate.url.endsWith("/__wright/webmcp"),
    );
    const now = new Date();
    const binding = {
      workspaceId: "workspace-1",
      sessionId: "session-1",
      surfaceId: selectedSurface,
      instanceId: `instance-${selectedSurface}`,
      generation: 1,
      documentOrigin: location.origin,
      serverId: "web-app",
    };
    (window as any).__webmcp.binding = binding;
    (window as any).__webmcp.socket = socket;
    socket.emit({
      protocolVersion: "1.0",
      kind: "event",
      messageId: crypto.randomUUID(),
      correlationId: crypto.randomUUID(),
      binding,
      operation: "webmcp.connected",
      sequence: 0,
      createdAt: now.toISOString(),
      deadlineAt: new Date(now.getTime() + 30_000).toISOString(),
    });
    await new Promise((resolve) => setTimeout(resolve));
    const registration = JSON.parse(socket.sent[0]);
    socket.emit({
      ...registration,
      kind: "result",
      messageId: crypto.randomUUID(),
      replyTo: registration.messageId,
      operation: "webmcp.register.result",
      payload: { registered: true },
    });
    (window as any).__webmcp.registration = await promise;
  }, surfaceId);
}

test("scopes identical tools, falls back without native WebMCP, denies stale scope, and tears down", async ({
  browser,
}) => {
  const first = await browser.newPage();
  const second = await browser.newPage();
  await installFakeSocket(first);
  await installFakeSocket(second);
  await Promise.all([register(first, "surface-a"), register(second, "surface-b")]);

  expect(await first.evaluate(() => "modelContext" in document)).toBe(false);
  expect(await second.evaluate(() => "modelContext" in document)).toBe(false);
  const bindings = await Promise.all([
    first.evaluate(() => JSON.parse((window as any).__webmcp.socket.sent[0]).binding),
    second.evaluate(() => JSON.parse((window as any).__webmcp.socket.sent[0]).binding),
  ]);
  expect(bindings.map((value) => value.surfaceId)).toEqual([
    "surface-a",
    "surface-b",
  ]);

  await first.evaluate(() => {
    const state = (window as any).__webmcp;
    const socket = state.socket;
    socket.emit({
      protocolVersion: "1.0",
      kind: "request",
      messageId: crypto.randomUUID(),
      correlationId: crypto.randomUUID(),
      binding: { ...state.binding, generation: 99 },
      operation: "webmcp.tool.call",
      toolName: "select_part",
      sequence: 0,
      createdAt: new Date().toISOString(),
      deadlineAt: new Date(Date.now() + 30_000).toISOString(),
      payload: { partId: "stale" },
    });
  });
  expect(await first.evaluate(() => (window as any).__webmcp.calls)).toEqual([]);

  await first.evaluate(() => (window as any).__webmcp.controller.abort());
  await expect
    .poll(() =>
      first.evaluate(() => {
        const sent = (window as any).__webmcp.socket.sent.map(JSON.parse);
        return sent.some((message: any) => message.operation === "webmcp.unregister");
      }),
    )
    .toBe(true);

  await first.close();
  await second.close();
});
