import { describe, expect, it } from "vitest";

import {
  diagnosticRequiredToolInputs,
  diagnosticToolsForServer,
  resolveExplicitDiagnosticMcpBinding,
  suggestDiagnosticMcpBinding,
  type DiagnosticMcpCatalog,
} from "./diagnostic-mcp-binding";

const catalog: DiagnosticMcpCatalog = {
  servers: [
    {
      serverId: "solid-edge",
      name: "Solid Edge MCP",
      description: "Modeling tools",
      transport: "stdio",
      active: true,
      installed: true,
    },
    {
      serverId: "openscad",
      name: "OpenSCAD MCP Server",
      description: "OpenSCAD tools",
      transport: "stdio",
      active: true,
      installed: true,
    },
  ],
  tools: [
    {
      toolId: "solid-edge:create-part",
      serverId: "solid-edge",
      name: "create_part",
      description: "Create a part",
      inputSchema: { type: "object", required: ["plan"] },
      enabled: true,
    },
    {
      toolId: "openscad:validate-scad",
      serverId: "openscad",
      name: "validate_scad",
      description: "Validate OpenSCAD",
      inputSchema: { type: "object", required: ["scad_content"] },
      enabled: true,
    },
  ],
};

describe("diagnostic MCP binding", () => {
  it("does not guess a server from generic engineering language", () => {
    expect(
      suggestDiagnosticMcpBinding(
        catalog,
        "Create a mounting part from the supplied design brief.",
      ),
    ).toBeNull();
  });

  it("suggests an exact tool when the context names its server and action", () => {
    expect(
      suggestDiagnosticMcpBinding(
        catalog,
        "Use the OpenSCAD MCP Server to validate_scad before release.",
      ),
    ).toEqual({
      serverId: "openscad",
      toolId: "openscad:validate-scad",
      source: "context",
      reason:
        "The block context explicitly names OpenSCAD MCP Server and validate_scad.",
    });
  });

  it("resolves an explicit fixture server without hard-coding its catalog ID", () => {
    expect(
      resolveExplicitDiagnosticMcpBinding(catalog, {
        serverName: "Solid Edge MCP",
        reason: "This test explicitly starts with Solid Edge MCP.",
      }),
    ).toEqual({
      serverId: "solid-edge",
      toolId: null,
      source: "fixture",
      reason: "This test explicitly starts with Solid Edge MCP.",
    });
  });

  it("filters tools and reads required schema inputs without vendor logic", () => {
    expect(
      diagnosticToolsForServer(catalog, "solid-edge").map(
        ({ toolId }) => toolId,
      ),
    ).toEqual(["solid-edge:create-part"]);
    expect(diagnosticRequiredToolInputs(catalog.tools[0])).toEqual(["plan"]);
  });
});
