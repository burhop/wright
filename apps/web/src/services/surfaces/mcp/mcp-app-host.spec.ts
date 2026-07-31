import { LATEST_PROTOCOL_VERSION } from "@modelcontextprotocol/ext-apps/app-bridge";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ExactOriginPostMessageTransport,
  McpAppHost,
  type McpAppGateway,
  type McpAppHostOptions,
} from "./mcp-app-host";
import { validateSandboxPolicy } from "./sandbox-proxy";

const SANDBOX_ORIGIN = "https://mcp-sandbox.test";
const ENVELOPE = {
  version: 1,
  surfaceId: "surface-mcp",
  generation: 4,
  nonce: "abcdefghijklmnopqrstuvwxyz123456",
} as const;

function createFrame(): { frame: HTMLIFrameElement; frameWindow: Window } {
  const frame = document.createElement("iframe");
  document.body.append(frame);
  const frameWindow = frame.contentWindow;
  if (!frameWindow) throw new Error("test iframe has no contentWindow");
  return { frame, frameWindow };
}

function incoming(
  source: Window,
  message: Record<string, unknown>,
  origin = SANDBOX_ORIGIN,
  envelope: Record<string, unknown> = ENVELOPE,
): void {
  window.dispatchEvent(
    new MessageEvent("message", {
      source,
      origin,
      data: { ...message, _wright: envelope },
    }),
  );
}

function gateway(): McpAppGateway {
  return {
    callTool: vi.fn(
      async (): Promise<CallToolResult> => ({
        content: [{ type: "text", text: "tool complete" }],
        structuredContent: { answer: 42 },
      }),
    ),
    listResources: vi.fn(async () => ({ resources: [] })),
    listResourceTemplates: vi.fn(async () => ({ resourceTemplates: [] })),
    readResource: vi.fn(async ({ uri }) => ({
      contents: [{ uri, mimeType: "text/plain", text: "resource" }],
    })),
    updateModelContext: vi.fn(async () => undefined),
    sendUserMessage: vi.fn(async () => undefined),
    openExternalLink: vi.fn(async () => undefined),
  };
}

function options(
  frameWindow: Window,
  appGateway: McpAppGateway,
  overrides: Partial<McpAppHostOptions> = {},
): McpAppHostOptions {
  return {
    frameWindow,
    sandboxOrigin: SANDBOX_ORIGIN,
    workspaceId: "workspace-a",
    sessionId: "session-a",
    surfaceId: ENVELOPE.surfaceId,
    generation: ENVELOPE.generation,
    serverId: "server-a",
    nonce: ENVELOPE.nonce,
    resource: {
      html: "<!doctype html><html><body><script>/* bundled app */</script></body></html>",
      mediaType: "text/html;profile=mcp-app",
    },
    policy: validateSandboxPolicy(undefined, undefined),
    gateway: appGateway,
    enabledHostCapabilities: new Set([
      "context.update",
      "user.message",
      "open.link",
    ]),
    hostContext: {
      theme: "light",
      displayMode: "inline",
      availableDisplayModes: ["inline", "fullscreen"],
      locale: "en-US",
      platform: "web",
    },
    eventWindow: window,
    ...overrides,
  };
}

function findOutgoing(
  postMessage: { mock: { calls: unknown[][] } },
  predicate: (message: Record<string, unknown>) => boolean,
): Record<string, unknown> | undefined {
  return postMessage.mock.calls
    .map((call) => call[0])
    .filter((message): message is Record<string, unknown> =>
      typeof message === "object" && message !== null,
    )
    .find(predicate);
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe("ExactOriginPostMessageTransport", () => {
  it("accepts only its exact source, origin, envelope, and first request id", async () => {
    const { frameWindow } = createFrame();
    const violations: string[] = [];
    const transport = new ExactOriginPostMessageTransport(
      frameWindow,
      frameWindow,
      {
        sandboxOrigin: SANDBOX_ORIGIN,
        surfaceId: ENVELOPE.surfaceId,
        generation: ENVELOPE.generation,
        nonce: ENVELOPE.nonce,
      },
      window,
      (reason) => violations.push(reason),
    );
    const received = vi.fn();
    transport.onmessage = received;
    await transport.start();
    const request = { jsonrpc: "2.0", id: 7, method: "ping", params: {} };

    incoming(window, request);
    incoming(frameWindow, request, "https://attacker.test");
    incoming(frameWindow, request, SANDBOX_ORIGIN, { ...ENVELOPE, generation: 3 });
    incoming(frameWindow, request);
    incoming(frameWindow, request);

    expect(received).toHaveBeenCalledTimes(1);
    expect(received).toHaveBeenCalledWith(request);
    expect(violations).toEqual([
      "wrong_source",
      "wrong_origin",
      "stale_or_invalid_envelope",
      "replayed_request",
    ]);
    await transport.close();
  });

  it("posts only to the configured exact sandbox origin with a surface envelope", async () => {
    const { frameWindow } = createFrame();
    const postMessage = vi.spyOn(frameWindow, "postMessage").mockImplementation(() => undefined);
    const transport = new ExactOriginPostMessageTransport(
      frameWindow,
      frameWindow,
      {
        sandboxOrigin: SANDBOX_ORIGIN,
        surfaceId: ENVELOPE.surfaceId,
        generation: ENVELOPE.generation,
        nonce: ENVELOPE.nonce,
      },
      window,
    );
    await transport.start();
    await transport.send({ jsonrpc: "2.0", method: "notifications/resources/list_changed" });

    expect(postMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        jsonrpc: "2.0",
        _wright: ENVELOPE,
      }),
      SANDBOX_ORIGIN,
    );
    await transport.close();
  });
});

describe("McpAppHost", () => {
  it("uses the official initialization, resource, context, tool, and teardown lifecycle", async () => {
    const { frameWindow } = createFrame();
    const postMessage = vi.spyOn(frameWindow, "postMessage").mockImplementation(() => undefined);
    const appGateway = gateway();
    const statuses: string[] = [];
    const initialToolResult: CallToolResult = {
      content: [{ type: "text", text: "useful fallback" }],
    };
    const host = new McpAppHost(
      options(frameWindow, appGateway, {
        initialToolInput: { location: "Boston" },
        initialToolResult,
        onStatus: (status) => statuses.push(status),
      }),
    );

    await host.connect();
    host.updateHostContext({ theme: "dark", displayMode: "fullscreen" });
    expect(
      findOutgoing(
        postMessage,
        (message) => message.method === "ui/notifications/host-context-changed",
      ),
    ).toBeUndefined();

    incoming(frameWindow, {
      jsonrpc: "2.0",
      method: "ui/notifications/sandbox-proxy-ready",
      params: {},
    });
    await vi.waitFor(() => {
      const resource = findOutgoing(
        postMessage,
        (message) => message.method === "ui/notifications/sandbox-resource-ready",
      );
      expect(resource).toMatchObject({
        params: {
          sandbox: "allow-scripts",
          html: expect.stringContaining("bundled app"),
          csp: {
            connectDomains: [],
            resourceDomains: [],
            frameDomains: [],
            baseUriDomains: [],
          },
          permissions: {},
        },
      });
    });
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 1,
      method: "ui/initialize",
      params: {
        appInfo: { name: "Reference App", version: "1.0.0" },
        appCapabilities: {},
        protocolVersion: LATEST_PROTOCOL_VERSION,
      },
    });
    await vi.waitFor(() => expect(findOutgoing(postMessage, (message) => message.id === 1)).toBeDefined());
    incoming(frameWindow, {
      jsonrpc: "2.0",
      method: "ui/notifications/initialized",
      params: {},
    });
    await vi.waitFor(() => {
      expect(host.currentStatus).toBe("ready");
      expect(
        findOutgoing(
          postMessage,
          (message) => message.method === "ui/notifications/tool-input",
        ),
      ).toBeDefined();
      expect(
        findOutgoing(
          postMessage,
          (message) => message.method === "ui/notifications/tool-result",
        ),
      ).toBeDefined();
      expect(
        findOutgoing(
          postMessage,
          (message) => message.method === "ui/notifications/host-context-changed",
        ),
      ).toBeDefined();
    });

    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 2,
      method: "resources/read",
      params: { uri: "ui://server-a/details" },
    });
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: { name: "refresh", arguments: { force: true } },
    });
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 4,
      method: "ui/update-model-context",
      params: { content: [{ type: "text", text: "selected part" }] },
    });
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 5,
      method: "ui/message",
      params: { role: "user", content: [{ type: "text", text: "Use this selection" }] },
    });
    await vi.waitFor(() => {
      expect(appGateway.readResource).toHaveBeenCalledWith(
        { uri: "ui://server-a/details" },
        expect.objectContaining({
          workspaceId: "workspace-a",
          sessionId: "session-a",
          surfaceId: "surface-mcp",
          generation: 4,
          serverId: "server-a",
          signal: expect.any(AbortSignal),
        }),
      );
      expect(appGateway.callTool).toHaveBeenCalledTimes(1);
      expect(appGateway.updateModelContext).toHaveBeenCalledTimes(1);
      expect(appGateway.sendUserMessage).toHaveBeenCalledTimes(1);
      for (const id of [2, 3, 4, 5]) {
        expect(findOutgoing(postMessage, (message) => message.id === id)).toBeDefined();
      }
    });

    const teardown = host.teardown();
    let teardownRequest: Record<string, unknown> | undefined;
    await vi.waitFor(() => {
      teardownRequest = findOutgoing(
        postMessage,
        (message) => message.method === "ui/resource-teardown",
      );
      expect(teardownRequest).toBeDefined();
    });
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: teardownRequest?.id,
      result: {},
    });
    await teardown;

    expect(host.currentStatus).toBe("closed");
    expect(statuses).toEqual([
      "connecting",
      "waiting_for_proxy",
      "loading_resource",
      "initializing",
      "ready",
      "tearing_down",
      "closed",
    ]);
  });

  it("rejects privileged operations before the view completes initialization", async () => {
    const { frameWindow } = createFrame();
    const postMessage = vi.spyOn(frameWindow, "postMessage").mockImplementation(() => undefined);
    const appGateway = gateway();
    const host = new McpAppHost(options(frameWindow, appGateway));
    await host.connect();

    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 8,
      method: "tools/call",
      params: { name: "too-early", arguments: {} },
    });

    await vi.waitFor(() => {
      const response = findOutgoing(postMessage, (message) => message.id === 8);
      expect(response?.error).toEqual(
        expect.objectContaining({ message: expect.stringMatching(/before initialization/i) }),
      );
    });
    expect(appGateway.callTool).not.toHaveBeenCalled();
    await host.teardown();
  });

  it("fails closed for an unsupported resource media type", () => {
    const { frameWindow } = createFrame();
    expect(
      () =>
        new McpAppHost(
          options(frameWindow, gateway(), {
            resource: { html: "<p>not an app</p>", mediaType: "text/html" },
          }),
        ),
    ).toThrow(/unsupported MCP App media type/i);
  });

  it("does not advertise ungranted host operations", async () => {
    const { frameWindow } = createFrame();
    const postMessage = vi
      .spyOn(frameWindow, "postMessage")
      .mockImplementation(() => undefined);
    const host = new McpAppHost(
      options(frameWindow, gateway(), {
        enabledHostCapabilities: new Set(),
      }),
    );

    await host.connect();
    incoming(frameWindow, {
      jsonrpc: "2.0",
      id: 41,
      method: "ui/initialize",
      params: {
        appInfo: { name: "No grants", version: "1.0.0" },
        appCapabilities: {},
        protocolVersion: LATEST_PROTOCOL_VERSION,
      },
    });
    let initialize: Record<string, unknown> | undefined;
    await vi.waitFor(() => {
      initialize = findOutgoing(postMessage, (message) => message.id === 41);
      expect(initialize).toBeDefined();
    });
    const capabilities = (initialize?.result as Record<string, unknown>)
      .hostCapabilities as Record<string, unknown>;
    expect(capabilities).not.toHaveProperty("updateModelContext");
    expect(capabilities).not.toHaveProperty("message");
    expect(capabilities).not.toHaveProperty("openLinks");
    await host.teardown();
  });
});
