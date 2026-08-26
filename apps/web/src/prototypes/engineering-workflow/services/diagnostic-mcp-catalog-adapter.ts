import {
  mcpService,
  type McpServer,
  type McpTool,
} from "../../../services/mcp-service";

import type {
  DiagnosticMcpCatalog,
  DiagnosticMcpServerOption,
  DiagnosticMcpToolOption,
} from "../domain/diagnostic-mcp-binding";

export interface DiagnosticMcpCatalogAdapter {
  listCatalog(): Promise<DiagnosticMcpCatalog>;
}

function serverOption(server: McpServer): DiagnosticMcpServerOption {
  return {
    serverId: server.server_id,
    name: server.name,
    description: server.description ?? "No server description provided.",
    transport: server.transport_variant ?? server.type,
    active: server.is_active,
    installed: server.is_installed,
  };
}

function toolOption(tool: McpTool): DiagnosticMcpToolOption {
  return {
    toolId: tool.tool_id,
    serverId: tool.server_id,
    name: tool.name,
    description: tool.description ?? "No tool description provided.",
    inputSchema: tool.input_schema,
    enabled: tool.is_enabled,
  };
}

export const wrightDiagnosticMcpCatalogAdapter: DiagnosticMcpCatalogAdapter = {
  async listCatalog() {
    const [servers, tools] = await Promise.all([
      mcpService.getServers(),
      mcpService.getTools(),
    ]);
    const installedServers = servers
      .filter(({ is_installed }) => is_installed)
      .map(serverOption)
      .toSorted((left, right) => left.name.localeCompare(right.name));
    const installedServerIds = new Set(
      installedServers.map(({ serverId }) => serverId),
    );
    return {
      servers: installedServers,
      tools: tools
        .filter(({ server_id }) => installedServerIds.has(server_id))
        .map(toolOption),
    };
  },
};

export const deterministicDiagnosticMcpCatalogAdapter: DiagnosticMcpCatalogAdapter =
  {
    async listCatalog() {
      return {
        servers: [
          {
            serverId: "fixture-modeling",
            name: "Fixture Modeling MCP",
            description: "Deterministic modeling fixture for component tests.",
            transport: "stdio",
            active: true,
            installed: true,
          },
          {
            serverId: "fixture-search",
            name: "Fixture Search MCP",
            description: "Deterministic inactive search fixture.",
            transport: "sse",
            active: false,
            installed: true,
          },
        ],
        tools: [
          {
            toolId: "fixture-modeling:create-candidate",
            serverId: "fixture-modeling",
            name: "create_candidate",
            description: "Create a candidate artifact from a reviewed brief.",
            inputSchema: {
              type: "object",
              properties: { brief: { type: "string" } },
              required: ["brief"],
              additionalProperties: false,
            },
            enabled: true,
          },
          {
            toolId: "fixture-modeling:inspect-candidate",
            serverId: "fixture-modeling",
            name: "inspect_candidate",
            description: "Inspect a candidate artifact.",
            inputSchema: {
              type: "object",
              properties: { artifactId: { type: "string" } },
              required: ["artifactId"],
              additionalProperties: false,
            },
            enabled: true,
          },
          {
            toolId: "fixture-search:search",
            serverId: "fixture-search",
            name: "search",
            description: "Search the deterministic fixture.",
            inputSchema: {
              type: "object",
              properties: { query: { type: "string" } },
              required: ["query"],
              additionalProperties: false,
            },
            enabled: true,
          },
        ],
      };
    },
  };
