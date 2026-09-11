import { cadModelTypes } from "./mcp-server-blocks";
import { useEffect, useState } from "react";
import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import { CadTaskOptions } from "./CadTaskOptions";
import { ApplicationTaskOptions } from "./ApplicationTaskOptions";
import type { RecoveryCommand } from "./command-system";
import { listWorkflowMcpTools, workflowMcpServerName, type WorkflowMcpTool } from "./mcp-settings";

export function McpTaskOptions({ block, workflow, sessionId, readOnly, onApply }: {
  block: RecoveryBlock; workflow: RecoveryWorkflow; sessionId?: string; readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const [tools, setTools] = useState<WorkflowMcpTool[]>([]);
  const [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (sessionId) void listWorkflowMcpTools(sessionId).then(value => { if (active) setTools(value); })
      .catch(() => { if (active) setError("Could not load servers. Check Tool Registry."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [sessionId]);
  const config = (key: string, value: string | number) => onApply([{kind: "set_block_configuration", blockId: block.id, key, value}]);
  const servers = [...new Set(tools.map(tool => tool.server_id))];
  const names = Object.fromEntries(tools.map(tool => [tool.server_id, workflowMcpServerName(tool)]));
  const current = String(block.configuration.mcp_server ?? "");
  const revision = workflow.relationships.find(edge => edge.kind === "feedback" && edge.sourceId === block.id);
  const reviseTo = (targetId: string) => {
    const commands: RecoveryCommand[] = workflow.relationships.filter(edge => edge.kind === "feedback" && edge.sourceId === block.id)
      .map(edge => ({kind: "disconnect", relationshipId: edge.id}));
    if (targetId) commands.push({kind: "connect", relationship: {id: `rel.design-check-revision-${block.id.replaceAll('.', '-')}`,
      kind: "feedback", sourceId: block.id, targetId, label: "Revise design", condition: "revise"}});
    onApply(commands);
  };
  return <section data-testid="workflow-recovery-mcp-task-options">
    <label>MCP server<select value={current} disabled={readOnly || loading} data-testid="workflow-recovery-task-server" onChange={e => config("mcp_server", e.target.value)}>
      <option value="">Choose a workspace server</option>
      {current && !servers.includes(current) && <option value={current}>{names[current] ?? String(block.configuration.mcp_server_name || "Selected server")} · {loading ? "loading…" : "unavailable"}</option>}
      {servers.map(server => <option key={server} value={server}>{names[server] ?? "MCP server"}</option>)}
    </select><small>The AI chooses operations from this server to complete your task.</small></label>
    {error && <p role="alert">{error}</p>}
    <CadTaskOptions modelTypes={cadModelTypes(tools.filter(tool => tool.server_id === current))} block={block} workflow={workflow} sessionId={sessionId} readOnly={readOnly} onApply={onApply} />
    <ApplicationTaskOptions block={block} workflow={workflow} sessionId={sessionId} readOnly={readOnly} onApply={onApply} />
    {block.configuration.cad && <section aria-label="Design check behavior">
      <label><input type="checkbox" checked={block.configuration.design_check === true} disabled={readOnly}
        onChange={e => {
          const commands: RecoveryCommand[] = [{kind: "set_block_configuration", blockId: block.id, key: "design_check", value: e.target.checked}];
          if (e.target.checked) commands.push({kind: "set_block_configuration", blockId: block.id, key: "output_format", value: "json"},
            {kind: "set_block_configuration", blockId: block.id, key: "max_revisions", value: 2});
          else commands.push(...workflow.relationships.filter(edge => edge.sourceId === block.id && (edge.kind === "feedback" || edge.kind === "decision"))
            .map(edge => ({kind: "disconnect" as const, relationshipId: edge.id})));
          onApply(commands);
        }} />Design check</label>
      {block.configuration.design_check === true && <>
        <p>Inspect the connected model using read-only tools. Continue only when every check passes. Missing evidence stops the run.</p>
        <label>If corrections are needed<select aria-label="Design check revision target" value={revision?.targetId ?? ""} disabled={readOnly} onChange={e => reviseTo(e.target.value)}>
          <option value="">Stop and show the corrections</option>
          {workflow.blocks.slice(0, workflow.blocks.findIndex(item => item.id === block.id)).filter(item => {
            try { const cad = JSON.parse(String(item.configuration.cad)); return cad.source === "new" && (cad.policy ?? "indexed") === "indexed"; } catch { return false; }
          }).map(item => <option key={item.id} value={item.id}>Return to {item.title}</option>)}
        </select></label>
        {revision && <label>Maximum corrected revisions<input aria-label="Maximum corrected revisions" type="number" min={1} max={3} disabled={readOnly}
          value={Number(block.configuration.max_revisions ?? 2)} onChange={e => config("max_revisions", Number(e.target.value))} /></label>}
      </>}
    </section>}
    <label>Expected result<textarea rows={2} value={String(block.configuration.expected_result ?? "")} readOnly={readOnly} data-testid="workflow-recovery-task-result" placeholder="What should this task produce or establish?" onChange={e => config("expected_result", e.target.value)} /></label>
    <details><summary>Additional guidance and limits</summary>
      {!block.configuration.cad && <label>Files the tools must produce<textarea rows={2} value={String(block.configuration.expected_files ?? "")} readOnly={readOnly} onChange={e => config("expected_files", e.target.value)} placeholder="Optional workspace paths, one per line" /><small>Wright checks these files exist and are non-empty before reporting completion.</small></label>}
      <label>Tool guidance<textarea rows={3} value={String(block.configuration.task_guidance ?? "")} readOnly={readOnly} onChange={e => config("task_guidance", e.target.value)} placeholder="Conventions or instructions for using these tools" /></label>
      <label>Maximum tool calls<input type="number" min={1} max={32} step={1} value={Number(block.configuration.max_tool_calls ?? 8)} disabled={readOnly} onChange={e => config("max_tool_calls", Number(e.target.value))} /><small>1–32 calls per task; default 8. The time limit still applies.</small></label>
      <label>Time limit (seconds)<input type="number" min={30} max={600} value={Number(block.configuration.timeout_seconds ?? 300)} disabled={readOnly} onChange={e => config("timeout_seconds", Number(e.target.value))} /></label>
    </details>
  </section>;
}
