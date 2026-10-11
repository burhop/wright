import { cadModelTypes, mcpServerChoices } from "./mcp-server-blocks";
import { useEffect, useState } from "react";
import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import { CadTaskOptions } from "./CadTaskOptions";
import { ApplicationTaskOptions } from "./ApplicationTaskOptions";
import type { RecoveryCommand } from "./command-system";
import { listWorkflowMcpTools, type WorkflowMcpTool } from "./mcp-settings";

export function McpTaskOptions({
  block,
  workflow,
  sessionId,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  sessionId?: string;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const [tools, setTools] = useState<WorkflowMcpTool[]>([]);
  const [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setTools([]);
    setError("");
    setLoading(Boolean(sessionId));
    if (sessionId)
      void listWorkflowMcpTools(sessionId)
        .then((value) => {
          if (active) setTools(value);
        })
        .catch(() => {
          if (active)
            setError(
              "Could not load workspace MCP servers. Retry or check MCP Tools.",
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    return () => {
      active = false;
    };
  }, [sessionId, retry]);
  const config = (key: string, value: string | number) =>
    onApply([
      { kind: "set_block_configuration", blockId: block.id, key, value },
    ]);
  const servers = mcpServerChoices(tools);
  const names = Object.fromEntries(
    servers.map((server) => [server.id, server.name]),
  );
  const current = String(block.configuration.mcp_server ?? "");
  const revision = workflow.relationships.find(
    (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
  );
  const reviseTo = (targetId: string) => {
    const commands: RecoveryCommand[] = workflow.relationships
      .filter((edge) => edge.kind === "feedback" && edge.sourceId === block.id)
      .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
    if (targetId)
      commands.push({
        kind: "connect",
        relationship: {
          id: `rel.design-check-revision-${block.id.replaceAll(".", "-")}`,
          kind: "feedback",
          sourceId: block.id,
          targetId,
          label: "Revise design",
          condition: "revise",
        },
      });
    onApply(commands);
  };
  return (
    <section data-testid="workflow-recovery-mcp-task-options">
      <label>
        MCP server
        <select
          value={current}
          disabled={readOnly || loading}
          data-testid="workflow-recovery-task-server"
          onChange={(e) => {
            const server = servers.find((item) => item.id === e.target.value);
            onApply([
              {
                kind: "set_block_configuration",
                blockId: block.id,
                key: "mcp_server",
                value: server?.id ?? "",
              },
              {
                kind: "set_block_configuration",
                blockId: block.id,
                key: "mcp_server_name",
                value: server?.name ?? "",
              },
            ]);
          }}
        >
          <option value="">Choose server later</option>
          {current && !servers.some((server) => server.id === current) && (
            <option value={current}>
              {names[current] ??
                String(
                  block.configuration.mcp_server_name || "Selected server",
                )}{" "}
              · {loading ? "loading…" : "unavailable"}
            </option>
          )}
          {servers.map((server) => (
            <option key={server.id} value={server.id}>
              {server.name}
            </option>
          ))}
        </select>
        <small>
          Servers enabled for this workspace are listed here. The AI chooses
          their operations to carry out your instructions. Select a server
          before running.
        </small>
      </label>
      {error && <p role="alert">{error}</p>}
      <button
        type="button"
        className="recovery-button recovery-button--secondary"
        disabled={readOnly || loading || !sessionId}
        onClick={() => setRetry((value) => value + 1)}
      >
        Refresh servers
      </button>
      {!loading && !error && sessionId && !servers.length && (
        <p>
          No MCP servers are available to this workspace. Enable a server in MCP
          Tools; your task can remain unbound while you edit.
        </p>
      )}
      {!block.configuration.image_output && (
        <>
          <CadTaskOptions
            modelTypes={cadModelTypes(
              tools.filter((tool) => tool.server_id === current),
            )}
            block={block}
            workflow={workflow}
            sessionId={sessionId}
            readOnly={readOnly}
            onApply={onApply}
          />
          <ApplicationTaskOptions
            block={block}
            workflow={workflow}
            sessionId={sessionId}
            readOnly={readOnly}
            onApply={onApply}
          />
        </>
      )}
      {block.configuration.cad && (
        <section aria-label="Design check behavior">
          <label>
            <input
              type="checkbox"
              checked={block.configuration.design_check === true}
              disabled={readOnly}
              onChange={(e) => {
                const commands: RecoveryCommand[] = [
                  {
                    kind: "set_block_configuration",
                    blockId: block.id,
                    key: "design_check",
                    value: e.target.checked,
                  },
                ];
                if (e.target.checked)
                  commands.push(
                    {
                      kind: "set_block_configuration",
                      blockId: block.id,
                      key: "output_format",
                      value: "json",
                    },
                    {
                      kind: "set_block_configuration",
                      blockId: block.id,
                      key: "max_revisions",
                      value: 2,
                    },
                  );
                else
                  commands.push(
                    ...workflow.relationships
                      .filter(
                        (edge) =>
                          edge.sourceId === block.id &&
                          (edge.kind === "feedback" ||
                            edge.kind === "decision"),
                      )
                      .map((edge) => ({
                        kind: "disconnect" as const,
                        relationshipId: edge.id,
                      })),
                  );
                onApply(commands);
              }}
            />
            Design check
          </label>
          {block.configuration.design_check === true && (
            <>
              <p>
                Inspect the connected model using read-only tools. Continue only
                when every check passes. Missing evidence stops the run.
              </p>
              <label>
                If corrections are needed
                <select
                  aria-label="Design check revision target"
                  value={revision?.targetId ?? ""}
                  disabled={readOnly}
                  onChange={(e) => reviseTo(e.target.value)}
                >
                  <option value="">Stop and show the corrections</option>
                  {workflow.blocks
                    .slice(
                      0,
                      workflow.blocks.findIndex((item) => item.id === block.id),
                    )
                    .filter((item) => {
                      try {
                        const cad = JSON.parse(String(item.configuration.cad));
                        return (
                          cad.source === "new" &&
                          (cad.policy ?? "indexed") === "indexed"
                        );
                      } catch {
                        return false;
                      }
                    })
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        Return to {item.title}
                      </option>
                    ))}
                </select>
              </label>
              {revision && (
                <label>
                  Maximum corrected revisions
                  <input
                    aria-label="Maximum corrected revisions"
                    type="number"
                    min={1}
                    max={3}
                    disabled={readOnly}
                    value={Number(block.configuration.max_revisions ?? 2)}
                    onChange={(e) =>
                      config("max_revisions", Number(e.target.value))
                    }
                  />
                </label>
              )}
            </>
          )}
        </section>
      )}
      <label>
        Expected result
        <textarea
          rows={2}
          value={String(block.configuration.expected_result ?? "")}
          readOnly={readOnly}
          data-testid="workflow-recovery-task-result"
          placeholder="What should this task produce or establish?"
          onChange={(e) => config("expected_result", e.target.value)}
        />
      </label>
      <details>
        <summary>Additional guidance and limits</summary>
        {!block.configuration.cad && !block.configuration.image_output && (
          <label>
            Files the tools must produce
            <textarea
              rows={2}
              value={String(block.configuration.expected_files ?? "")}
              readOnly={readOnly}
              onChange={(e) => config("expected_files", e.target.value)}
              placeholder="Optional workspace paths, one per line"
            />
            <small>
              Wright checks these files exist and are non-empty before reporting
              completion.
            </small>
          </label>
        )}
        <label>
          Tool guidance
          <textarea
            rows={3}
            value={String(block.configuration.task_guidance ?? "")}
            readOnly={readOnly}
            onChange={(e) => config("task_guidance", e.target.value)}
            placeholder="Conventions or instructions for using these tools"
          />
        </label>
        <label>
          Maximum tool calls
          <input
            type="number"
            min={1}
            max={32}
            step={1}
            value={Number(block.configuration.max_tool_calls ?? 8)}
            disabled={readOnly}
            onChange={(e) => config("max_tool_calls", Number(e.target.value))}
          />
          <small>
            1–32 calls per task; default 8. The time limit still applies.
          </small>
        </label>
        <label>
          Time limit (seconds)
          <input
            type="number"
            min={30}
            max={600}
            value={Number(block.configuration.timeout_seconds ?? 300)}
            disabled={readOnly}
            onChange={(e) => config("timeout_seconds", Number(e.target.value))}
          />
        </label>
      </details>
    </section>
  );
}
