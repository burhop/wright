import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { McpAppPresenterGateway } from "../../services/surfaces/mcp/mcp-app-presenter";
import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import { McpAppSurface } from "./McpAppSurface";

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
  title: "Reference MCP App",
  lifecycle: "ready",
  presentations: [],
  capabilities: [],
  revision: 2,
  createdAt: "2026-07-31T00:00:00Z",
  updatedAt: "2026-07-31T00:00:00Z",
};

function gateway(): McpAppPresenterGateway {
  return {
    getPresentation: vi.fn(async () => ({
      capability: "absent" as const,
      reason: "Server did not negotiate MCP Apps.",
      fallbackResult: {
        content: [
          {
            type: "text" as const,
            text: "The design contains one bracket.",
          },
        ],
      },
    })),
    callTool: vi.fn(),
    listResources: vi.fn(),
    listResourceTemplates: vi.fn(),
    readResource: vi.fn(),
    updateModelContext: vi.fn(),
    sendUserMessage: vi.fn(),
  };
}

describe("McpAppSurface", () => {
  it("mounts the presenter, exposes focus mode, and renders useful fallback", async () => {
    const onFocusMode = vi.fn();
    render(
      <McpAppSurface
        descriptor={descriptor}
        sessionId="session-a"
        gateway={gateway()}
        onFocusMode={onFocusMode}
      />,
    );

    expect(await screen.findByTestId("mcp-app-fallback")).toHaveTextContent(
      "The design contains one bracket.",
    );
    screen.getByTestId("surface-enter-focus").click();
    expect(onFocusMode).toHaveBeenCalledOnce();
    expect(screen.getByTestId("mcp-app-workspace-surface")).toHaveAttribute(
      "aria-label",
      "Reference MCP App",
    );
  });
});
