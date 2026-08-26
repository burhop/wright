import {
  diagnosticRequiredToolInputs,
  diagnosticToolsForServer,
  type DiagnosticMcpCatalog,
  type DiagnosticMcpSuggestion,
} from "./domain/diagnostic-mcp-binding";

export function DiagnosticMcpQuickBinding({
  catalog,
  loading,
  selectedServerId,
  selectedToolId,
  suggestion,
  runtimeReady = false,
  onSelectServer,
  onSelectTool,
}: {
  catalog: DiagnosticMcpCatalog | null;
  loading: boolean;
  selectedServerId: string | null;
  selectedToolId: string | null;
  suggestion: DiagnosticMcpSuggestion | null;
  runtimeReady?: boolean;
  onSelectServer: (serverId: string | null) => void;
  onSelectTool: (toolId: string | null) => void;
}) {
  const servers = catalog?.servers ?? [];
  const selectedServer =
    servers.find(({ serverId }) => serverId === selectedServerId) ?? null;
  const tools = catalog
    ? diagnosticToolsForServer(catalog, selectedServerId)
    : [];
  const selectedTool =
    tools.find(({ toolId }) => toolId === selectedToolId) ?? null;
  const requiredInputs = diagnosticRequiredToolInputs(selectedTool);

  return (
    <section className="ewp-mcp-quick-binding" aria-label="Quick MCP binding">
      <header>
        <strong>MCP block</strong>
        <small>
          {suggestion?.source === "fixture"
            ? "Fixture starting value"
            : suggestion?.source === "context"
              ? "Context suggestion"
              : "Choose from workspace"}
        </small>
      </header>

      <label>
        <span>Server</span>
        <select
          aria-label="Quick MCP server"
          disabled={loading || servers.length === 0}
          value={selectedServerId ?? ""}
          onChange={(event) =>
            onSelectServer(event.currentTarget.value || null)
          }
        >
          <option value="">
            {loading ? "Loading installed MCPs…" : "Choose an installed MCP"}
          </option>
          {servers.map((server) => (
            <option key={server.serverId} value={server.serverId}>
              {server.name} · {server.active ? "active" : "inactive"}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Exact tool</span>
        <select
          aria-label="Quick exact MCP tool"
          disabled={!selectedServer || tools.length === 0}
          value={selectedToolId ?? ""}
          onChange={(event) => onSelectTool(event.currentTarget.value || null)}
        >
          <option value="">
            {selectedServer
              ? tools.length > 0
                ? "Choose an exact tool"
                : "No catalog tools available"
              : "Choose an MCP first"}
          </option>
          {tools.map((tool) => (
            <option key={tool.toolId} value={tool.toolId}>
              {tool.name} {tool.enabled ? "" : "· disabled"}
            </option>
          ))}
        </select>
      </label>

      <p>
        {selectedServer
          ? selectedTool
            ? requiredInputs.length > 0
              ? runtimeReady
                ? `Selected · Step 2 will prepare ${requiredInputs.join(", ")}`
                : `Selected · map required input${requiredInputs.length === 1 ? "" : "s"}: ${requiredInputs.join(", ")}`
              : "Selected · no required inputs declared"
            : `${selectedServer.name} selected · choose one operation`
          : "Select a server now or let an agent propose one for review"}
      </p>
    </section>
  );
}

export default DiagnosticMcpQuickBinding;
