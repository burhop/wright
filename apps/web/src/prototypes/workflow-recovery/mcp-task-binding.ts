import type { RecoveryCommand } from "./command-system";
import { recoveryAuthoringSectionKind, type RecoveryBlock } from "./model";

export function isUnboundToolTask(block: RecoveryBlock): boolean {
  return (
    block.kind === "work" &&
    block.executionKind === "deterministic" &&
    recoveryAuthoringSectionKind(block) !== "input" &&
    !block.bindingId &&
    !block.componentRef &&
    !block.configuration.authoring_template
  );
}

export function configureMcpTaskServer(
  block: RecoveryBlock,
  serverId: string,
  serverName: string,
): RecoveryCommand[] {
  const commands: RecoveryCommand[] = [];
  if (isUnboundToolTask(block)) {
    if (!serverId) return [];
    commands.push({
      kind: "set_block_execution_kind",
      blockId: block.id,
      executionKind: "ai_capable",
    });
    for (const [key, value] of Object.entries({
      authoring_template: "mcp-task",
      output_format: "text",
      save_output: false,
      file_policy: "indexed",
      max_tool_calls: 8,
      timeout_seconds: 300,
    })) {
      commands.push({
        kind: "set_block_configuration",
        blockId: block.id,
        key,
        value,
      });
    }
  }
  for (const [key, value] of Object.entries({
    mcp_server: serverId,
    mcp_server_name: serverId ? serverName : "",
    binding_state: serverId ? "configured" : "unbound",
  })) {
    commands.push({
      kind: "set_block_configuration",
      blockId: block.id,
      key,
      value,
    });
  }
  return commands;
}

export function mcpTaskLabel(block: RecoveryBlock): string | undefined {
  if (isUnboundToolTask(block)) return "MCP: not selected";
  if (
    ["mcp-task", "mcp-tool"].includes(
      String(block.configuration.authoring_template),
    )
  ) {
    return block.configuration.mcp_server
      ? `MCP: ${block.configuration.mcp_server_name || block.configuration.mcp_server}`
      : "MCP: not selected";
  }
  return undefined;
}
