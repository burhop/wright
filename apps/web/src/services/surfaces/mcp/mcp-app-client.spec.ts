import { afterEach, describe, expect, it, vi } from "vitest";

import { hostAdapter } from "../../host-adapter";
import type { SurfaceDescriptor } from "../surface-contract";
import { McpAppClient } from "./mcp-app-client";

const descriptor: SurfaceDescriptor = {
  schemaVersion: 1,
  surfaceId: "surface-mcp",
  workspaceId: "workspace-a",
  source: {
    kind: "mcp_app",
    sourceId: "server-a:1:ui://server-a/app",
    sourceVersion: "a".repeat(64),
    serverId: "server-a",
    resourceUri: "ui://server-a/app",
    contentHash: "a".repeat(64),
  },
  title: "Reference app",
  lifecycle: "ready",
  presentations: [],
  capabilities: [],
  revision: 2,
  createdAt: "2026-07-31T00:00:00Z",
  updatedAt: "2026-07-31T00:00:00Z",
};

function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("McpAppClient", () => {
  it("parses a scoped presentation and preserves only known host capabilities", async () => {
    const fetch = vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      json({
        capability: "supported",
        protocolVersion: "2026-01-26",
        contentHash: "a".repeat(64),
        sandboxOrigin: "https://mcp-sandbox.example.test",
        resource: {
          html: "<main>App</main>",
          mediaType: "text/html;profile=mcp-app",
          csp: { connectDomains: [] },
          grantedPermissions: {},
        },
        fallbackResult: { content: [{ type: "text", text: "fallback" }] },
        hostCapabilities: [],
      }),
    );

    const result = await new McpAppClient("session-a").getPresentation(
      descriptor,
      new AbortController().signal,
    );

    expect(result.resource?.html).toBe("<main>App</main>");
    expect(result.hostCapabilities).toEqual([]);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/surface-mcp/mcp-app/presentation"),
      expect.objectContaining({
        headers: {
          "X-Wright-Workspace-ID": "workspace-a",
          "X-Wright-Session-ID": "session-a",
        },
      }),
    );
  });

  it("binds app tool calls to the operation context and server-owned route", async () => {
    const fetch = vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      json({
        content: [{ type: "text", text: "done" }],
        structuredContent: { ok: true },
      }),
    );
    const controller = new AbortController();

    const result = await new McpAppClient("surface-session").callTool(
      { name: "server-a__refresh", arguments: { force: true } },
      {
        workspaceId: "workspace-a",
        sessionId: "session-a",
        surfaceId: "surface-mcp",
        generation: 2,
        serverId: "server-a",
        signal: controller.signal,
      },
    );

    expect(result.structuredContent).toEqual({ ok: true });
    const [url, init] = fetch.mock.calls[0];
    expect(String(url)).toContain("/surface-mcp/mcp-app/tools/call");
    expect(init?.headers).toEqual({
      "X-Wright-Workspace-ID": "workspace-a",
      "X-Wright-Session-ID": "session-a",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(String(init?.body))).toEqual(
      expect.objectContaining({
        requestId: expect.any(String),
        name: "server-a__refresh",
        arguments: { force: true },
      }),
    );
  });

  it("rejects undeclared or malformed host capabilities", async () => {
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      json({ capability: "supported", hostCapabilities: ["host.shell"] }),
    );
    await expect(
      new McpAppClient("session-a").getPresentation(
        descriptor,
        new AbortController().signal,
      ),
    ).rejects.toThrow(/unsupported/i);
  });
});
