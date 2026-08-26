import {
  diagnosticRequiredToolInputs,
  diagnosticToolsForServer,
  type DiagnosticMcpBindingDefault,
  type DiagnosticMcpCatalog,
  type DiagnosticMcpSuggestion,
} from "./domain/diagnostic-mcp-binding";

export interface DiagnosticMcpBindingSummary {
  serverName: string;
  toolName: string;
  toolId: string;
  executable: boolean;
  requiredInputs: readonly string[];
  unmappedInputs: readonly string[];
}

export function DiagnosticMcpBindingPanel({
  catalog,
  loading,
  loadError,
  selectedServerId,
  selectedToolId,
  suggestion,
  configuredDefault,
  runtimeReady = false,
  onSelectServer,
  onSelectTool,
}: {
  catalog: DiagnosticMcpCatalog | null;
  loading: boolean;
  loadError: string | null;
  selectedServerId: string | null;
  selectedToolId: string | null;
  suggestion: DiagnosticMcpSuggestion | null;
  configuredDefault?: DiagnosticMcpBindingDefault;
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
  const bindingSelected = selectedServer !== null && selectedTool !== null;
  const executable =
    bindingSelected && selectedServer.active && selectedTool.enabled;

  return (
    <section
      className="ewp-mcp-binding"
      aria-labelledby="ewp-mcp-binding-title"
    >
      <header>
        <span>
          <h2 id="ewp-mcp-binding-title">MCP tool binding</h2>
          <small>
            Installed catalog ·{" "}
            {runtimeReady ? "runtime ready" : "selection only"}
          </small>
        </span>
        <strong data-state={bindingSelected ? "ready" : "missing"}>
          {bindingSelected ? "Selected" : "Not selected"}
        </strong>
      </header>
      <p>
        Choose an installed MCP server, then bind one exact tool and review its
        declared input schema.
        {runtimeReady
          ? " The workflow will generate and validate its arguments before making the call."
          : " No compatible runtime adapter is available for this selection."}
      </p>

      <label>
        <span>Installed MCP</span>
        <select
          aria-label="Installed MCP server"
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
        <small>
          {servers.length} installed MCP{servers.length === 1 ? "" : "s"}
          {selectedServer
            ? ` · ${selectedServer.transport} · ${selectedServer.active ? "available" : "not currently active"}`
            : ""}
        </small>
      </label>

      <label>
        <span>Exact tool</span>
        <select
          aria-label="Exact MCP tool"
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
        <small>
          {selectedServer
            ? `${tools.length} catalog tool${tools.length === 1 ? "" : "s"} exposed by this MCP`
            : "Tool choices are scoped to the selected MCP."}
        </small>
      </label>

      {loadError ? <p role="alert">{loadError}</p> : null}
      {suggestion ? (
        <p className="ewp-mcp-binding__suggestion" role="status">
          <strong>
            {suggestion.source === "fixture"
              ? "Fixture starting value"
              : "Context suggestion"}
          </strong>
          {suggestion.reason}
        </p>
      ) : configuredDefault ? (
        <p className="ewp-mcp-binding__suggestion" role="alert">
          <strong>Fixture default unavailable</strong>
          Wright could not uniquely resolve {configuredDefault.serverName} in
          the installed catalog. Choose an installed MCP manually.
        </p>
      ) : (
        <p className="ewp-mcp-binding__suggestion" data-state="neutral">
          <strong>No safe default</strong>
          The block context does not explicitly identify one installed MCP and
          tool. Wright will not guess from a broad category such as CAD or FEA.
        </p>
      )}

      {selectedServer ? (
        <section className="ewp-mcp-binding__selection">
          <h3>{selectedServer.name}</h3>
          <p>{selectedServer.description}</p>
          {selectedTool ? (
            <>
              <dl>
                <div>
                  <dt>Exact identity</dt>
                  <dd>{selectedTool.toolId}</dd>
                </div>
                <div>
                  <dt>Required inputs</dt>
                  <dd>
                    {requiredInputs.length > 0
                      ? requiredInputs.join(", ")
                      : "None declared"}
                  </dd>
                </div>
                <div>
                  <dt>Execution readiness</dt>
                  <dd>
                    {executable
                      ? runtimeReady
                        ? "Binding and schema-aware execution ready"
                        : "Binding ready · compatible runtime unavailable"
                      : !selectedServer.active
                        ? "Selected MCP is inactive"
                        : "Selected tool is disabled"}
                  </dd>
                </div>
              </dl>
              <p>{selectedTool.description}</p>
              {requiredInputs.length > 0 && !runtimeReady ? (
                <section
                  className="ewp-mcp-binding__mapping-warning"
                  role="alert"
                >
                  <strong>Input mapping required</strong>
                  <p>
                    This operation requires {requiredInputs.join(", ")}. Step 2
                    currently produces text, so Wright cannot validate a call to
                    this tool yet. Configure the AI task to produce a
                    schema-compatible object or add a mapping step. No MCP call
                    was attempted.
                  </p>
                </section>
              ) : (
                <p className="ewp-mcp-binding__mapping-ready" role="status">
                  {requiredInputs.length > 0
                    ? `Step 2 will generate and validate ${requiredInputs.join(", ")} against this exact tool contract before invocation.`
                    : "This tool declares no required inputs and is ready for the bounded runtime experiment."}
                </p>
              )}
              <details>
                <summary>View declared input schema</summary>
                <pre>{JSON.stringify(selectedTool.inputSchema, null, 2)}</pre>
              </details>
            </>
          ) : null}
        </section>
      ) : null}
    </section>
  );
}

export default DiagnosticMcpBindingPanel;
