import { LATEST_PROTOCOL_VERSION } from "@modelcontextprotocol/ext-apps/app-bridge";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { SurfaceDescriptor } from "../surface-contract";
import {
  McpAppPresenter,
  type McpAppPresentationProjection,
  type McpAppPresenterGateway,
} from "./mcp-app-presenter";

const contentHash = "c".repeat(64);

function descriptor(): SurfaceDescriptor {
  return {
    schemaVersion: 1,
    surfaceId: "surface-mcp",
    workspaceId: "workspace-a",
    source: {
      kind: "mcp_app",
      sourceId: "server-a:ui://server-a/app",
      sourceVersion: contentHash,
      serverId: "server-a",
      resourceUri: "ui://server-a/app",
      contentHash,
    },
    title: "Reference MCP App",
    lifecycle: "ready",
    instance: {
      instanceId: "mcp-instance",
      generation: 2,
      sharing: "isolated",
    },
    presentations: [{ kind: "panel", eligible: true }],
    capabilities: [],
    revision: 3,
    createdAt: "2026-07-31T12:00:00Z",
    updatedAt: "2026-07-31T12:00:00Z",
  };
}

function supported(
  overrides: Partial<McpAppPresentationProjection> = {},
): McpAppPresentationProjection {
  return {
    capability: "supported",
    protocolVersion: LATEST_PROTOCOL_VERSION,
    contentHash,
    sandboxOrigin: "https://mcp-sandbox.test",
    resource: {
      html: "<!doctype html><html><body>reference app</body></html>",
      mediaType: "text/html;profile=mcp-app",
    },
    fallbackResult: {
      content: [{ type: "text", text: "Useful text fallback" }],
      structuredContent: { retained: true },
    },
    ...overrides,
  };
}

function gateway(
  projection: McpAppPresentationProjection,
): McpAppPresenterGateway {
  return {
    getPresentation: vi.fn(async () => projection),
    callTool: vi.fn(async () => ({ content: [] })),
    listResources: vi.fn(async () => ({ resources: [] })),
    listResourceTemplates: vi.fn(async () => ({ resourceTemplates: [] })),
    readResource: vi.fn(async ({ uri }) => ({
      contents: [{ uri, text: "resource" }],
    })),
    updateModelContext: vi.fn(async () => undefined),
    sendUserMessage: vi.fn(async () => undefined),
  };
}

function mount(projection: McpAppPresentationProjection) {
  const container = document.createElement("div");
  document.body.append(container);
  const presenterGateway = gateway(projection);
  const presenter = new McpAppPresenter(descriptor(), {
    sessionId: "session-a",
    gateway: presenterGateway,
    hostOrigin: "https://wright.test",
  });
  presenter.mount(container);
  return { container, presenter, presenterGateway };
}

async function expectFallback(
  projection: McpAppPresentationProjection,
  text: RegExp | string,
): Promise<string> {
  const { container, presenter } = mount(projection);
  await vi.waitFor(() => {
    expect(
      container.querySelector('[data-testid="mcp-app-fallback"]'),
    ).not.toBeNull();
  });
  expect(container.textContent).toMatch(text);
  expect(
    container.querySelector('[data-testid="mcp-app-sandbox-frame"]'),
  ).toBeNull();
  const rendered = container.textContent || "";
  presenter.dispose();
  return rendered;
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe("McpAppPresenter", () => {
  it("shows useful tool fallback when the UI capability is absent", async () => {
    const rendered = await expectFallback(
      supported({
        capability: "absent",
        reason: "Server did not negotiate io.modelcontextprotocol/ui.",
      }),
      /Useful text fallback/,
    );
    expect(rendered).toContain('"retained": true');
  });

  it("falls back for unsupported protocol, missing resource, and bad media type", async () => {
    await expectFallback(
      supported({ protocolVersion: "2099-01-01" }),
      /unsupported protocol 2099-01-01/i,
    );
    await expectFallback(
      supported({ resource: undefined, reason: "Resource disappeared." }),
      /Resource disappeared/,
    );
    await expectFallback(
      supported({
        resource: { html: "<p>ordinary HTML</p>", mediaType: "text/html" },
      }),
      /unsupported media type text\/html/i,
    );
  });

  it("fails closed when CSP metadata requests an invalid or local domain", async () => {
    await expectFallback(
      supported({
        resource: {
          html: "<p>unsafe app</p>",
          mediaType: "text/html;profile=mcp-app",
          csp: { connectDomains: ["http://169.254.169.254/latest/meta-data"] },
        },
      }),
      /blocked by its renderer or security policy/i,
    );
  });

  it("fails closed when the renderer cannot create an isolated frame", async () => {
    await expectFallback(
      supported({ sandboxOrigin: "https://wright.test" }),
      /sandbox origin must differ/i,
    );
  });

  it("mounts a distinct-origin outer sandbox with stable automation identifiers", async () => {
    const { container, presenter, presenterGateway } = mount(supported());
    await vi.waitFor(() => {
      expect(
        container.querySelector('[data-testid="mcp-app-sandbox-frame"]'),
      ).not.toBeNull();
    });
    const frame = container.querySelector<HTMLIFrameElement>(
      '[data-testid="mcp-app-sandbox-frame"]',
    );
    expect(
      container.querySelector('[data-testid="mcp-app-surface"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="mcp-app-status"]'),
    ).toHaveTextContent(/waiting for the isolated/i);
    expect(frame).toHaveAttribute("sandbox", "allow-scripts allow-same-origin");
    expect(frame).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(frame?.src).toMatch(
      /^https:\/\/mcp-sandbox\.test\/surface-sandbox\/index\.html\?/,
    );
    expect(frame?.src).toContain("hostOrigin=https%3A%2F%2Fwright.test");
    expect(presenterGateway.getPresentation).toHaveBeenCalledWith(
      expect.objectContaining({ surfaceId: "surface-mcp" }),
      expect.any(AbortSignal),
    );

    presenter.focus();
    expect(document.activeElement).toBe(frame);
    presenter.dispose();
    expect(container.children).toHaveLength(0);
  });

  it("survives projection failures and provides a retry action", async () => {
    const container = document.createElement("div");
    document.body.append(container);
    const presenterGateway = gateway(supported());
    vi.mocked(presenterGateway.getPresentation)
      .mockRejectedValueOnce(new Error("resource read timed out"))
      .mockResolvedValueOnce(supported());
    const presenter = new McpAppPresenter(descriptor(), {
      sessionId: "session-a",
      gateway: presenterGateway,
      hostOrigin: "https://wright.test",
    });
    presenter.mount(container);
    await vi.waitFor(() =>
      expect(container).toHaveTextContent(/resource read timed out/i),
    );
    container
      .querySelector<HTMLButtonElement>('[data-testid="mcp-app-retry"]')
      ?.click();
    await vi.waitFor(() => {
      expect(
        container.querySelector('[data-testid="mcp-app-sandbox-frame"]'),
      ).not.toBeNull();
    });
    expect(presenterGateway.getPresentation).toHaveBeenCalledTimes(2);
    presenter.dispose();
  });
});
