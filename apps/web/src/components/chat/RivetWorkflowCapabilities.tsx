import { useCallback, useEffect, useMemo, useState } from "react";

import {
  workspaceService,
  type RivetMcpBindingPreview,
  type RivetMcpCapabilities,
  type RivetWorkflowOperation,
} from "../../services/workspace-service";

export function RivetWorkflowCapabilities({
  sessionId,
  workflow,
}: {
  sessionId: string;
  workflow: RivetWorkflowOperation;
}) {
  const [capabilities, setCapabilities] = useState<RivetMcpCapabilities | null>(
    null,
  );
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<RivetMcpBindingPreview | null>(null);
  const [message, setMessage] = useState("Loading workspace capabilities…");

  const load = useCallback(async () => {
    setPreview(null);
    setMessage("Loading workspace capabilities…");
    try {
      const next = await workspaceService.getRivetMcpCapabilities(
        sessionId,
        workflow.slug,
      );
      setCapabilities(next);
      const initial: Record<string, string> = {};
      for (const requirement of next.requirements) {
        if (requirement.node_type !== "mcpToolCall") continue;
        const candidates = next.capabilities.filter(
          (item) =>
            item.binding_eligible &&
            (item.qualified_tool_name === requirement.static_tool_name ||
              item.tool_name === requirement.static_tool_name),
        );
        if (candidates.length === 1)
          initial[requirement.node_id] = candidates[0].qualified_tool_name;
      }
      setSelections(initial);
      setMessage("Choose one exact workspace capability for every MCP node.");
    } catch (error) {
      setCapabilities(null);
      setMessage(
        error instanceof Error
          ? error.message
          : "Workspace MCP capabilities are unavailable.",
      );
    }
  }, [sessionId, workflow.slug]);

  useEffect(() => {
    void load();
  }, [load]);

  const toolRequirements = useMemo(
    () =>
      capabilities?.requirements.filter(
        (item) => item.node_type === "mcpToolCall",
      ) || [],
    [capabilities],
  );

  const prepareBindings = async () => {
    if (!capabilities) return;
    try {
      const next = await workspaceService.previewRivetMcpBindings(
        sessionId,
        workflow.slug,
        workflow.revision,
        workflow.etag,
        toolRequirements
          .filter((item) => selections[item.node_id])
          .map((item) => ({
            node_id: item.node_id,
            qualified_tool_name: selections[item.node_id],
          })),
        capabilities.graph_id,
      );
      setPreview(next);
      setMessage(
        next.ready
          ? "Tool connections are ready and will be applied when the workflow runs."
          : "Resolve every blocker before running the workflow.",
      );
    } catch (error) {
      setPreview(null);
      setMessage(
        error instanceof Error ? error.message : "Binding preview failed.",
      );
    }
  };

  if (!capabilities) {
    return (
      <div data-testid="workflow-capabilities-tab">
        <p role="status" aria-live="polite">
          {message}
        </p>
        <button
          data-testid="workflow-binding-refresh"
          type="button"
          onClick={() => void load()}
        >
          Retry capability check
        </button>
      </div>
    );
  }

  if (toolRequirements.length === 0) {
    return (
      <div data-testid="workflow-capabilities-tab">
        <p>
          This workflow has no MCP tool-call nodes and is ready to run.
        </p>
        <p role="status" aria-live="polite">
          {message}
        </p>
      </div>
    );
  }

  return (
    <div data-testid="workflow-capabilities-tab">
      <p>
        Bind each MCP node to one namespaced tool. Wright applies a unique match
        automatically at run time; use this panel only when a node is ambiguous.
      </p>
      {capabilities.issues.map((issue) => (
        <p key={`${issue.code}-${issue.node_id || "project"}`} role="alert">
          {issue.code}: {issue.message}
        </p>
      ))}
      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 18rem), 1fr))",
          gap: "var(--space-sm)",
        }}
      >
        {toolRequirements.map((requirement) => {
          const compatible = capabilities.capabilities.filter(
            (item) => item.binding_eligible,
          );
          const binding = preview?.bindings.find(
            (item) => item.node_id === requirement.node_id,
          );
          return (
            <section
              key={requirement.node_id}
              data-testid={`workflow-binding-row-${requirement.node_id}`}
              style={{
                border: "1px solid var(--color-border)",
                padding: "var(--space-sm)",
              }}
            >
              <h4 style={{ marginTop: 0 }}>Node {requirement.node_id}</h4>
              <label>
                Exact workspace tool
                <select
                  data-testid={`workflow-binding-select-${requirement.node_id}`}
                  value={selections[requirement.node_id] || ""}
                  onChange={(event) => {
                    setSelections((current) => ({
                      ...current,
                      [requirement.node_id]: event.target.value,
                    }));
                    setPreview(null);
                  }}
                >
                  <option value="">Choose a namespaced tool</option>
                  {compatible.map((item) => (
                    <option
                      key={item.qualified_tool_name}
                      value={item.qualified_tool_name}
                    >
                      {item.qualified_tool_name} — {item.compatibility}
                    </option>
                  ))}
                </select>
              </label>
              {binding?.blockers.map((blocker) => (
                <p
                  key={blocker}
                  data-testid={`workflow-binding-blocker-${requirement.node_id}`}
                  role="alert"
                >
                  Blocked: {blocker.replaceAll("_", " ")}
                </p>
              ))}
              {binding && binding.blockers.length === 0 && (
                <details
                  data-testid={`workflow-binding-details-${requirement.node_id}`}
                >
                  <summary>Tool identity and risk</summary>
                  <dl>
                    <dt>Tool</dt>
                    <dd>{binding.selected_tool}</dd>
                    <dt>Server revision</dt>
                    <dd>{binding.server_revision}</dd>
                    <dt>Schema</dt>
                    <dd>{binding.schema_digest}</dd>
                    <dt>Validation</dt>
                    <dd>{binding.validation_evidence_id}</dd>
                    <dt>Approval gates</dt>
                    <dd>
                      {Array.isArray(binding.risk?.required_approvals) &&
                      binding.risk.required_approvals.length
                        ? binding.risk.required_approvals.join(", ")
                        : "None"}
                    </dd>
                  </dl>
                </details>
              )}
            </section>
          );
        })}
      </div>
      <button
        data-testid="workflow-binding-refresh"
        type="button"
        onClick={() => void load()}
      >
        Refresh current capabilities
      </button>{" "}
      <button
        data-testid="workflow-prepare-binding-summary"
        type="button"
        disabled={toolRequirements.some((item) => !selections[item.node_id])}
        onClick={() => void prepareBindings()}
      >
        Prepare tool connections
      </button>
      <p data-testid="workflow-binding-policy-summary">
        Tool snapshot: {preview?.policy_snapshot_digest || "Prepared at run time"}
      </p>
      <p role="status" aria-live="polite">
        {message}
      </p>
    </div>
  );
}
