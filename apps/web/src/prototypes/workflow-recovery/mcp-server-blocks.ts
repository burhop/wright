import { createAuthoringObject } from "./authoring-objects";
import { cadCommands, type CadOptions } from "./CadTaskOptions";
import type { RecoveryCommand } from "./command-system";
import type { RecoveryLayout, RecoveryWorkflow } from "./model";
import { workflowMcpServerName, type WorkflowMcpTool } from "./mcp-settings";

export interface McpServerChoice {
  id: string;
  name: string;
  tools: WorkflowMcpTool[];
}

export function mcpServerChoices(tools: WorkflowMcpTool[]): McpServerChoice[] {
  const servers = new Map<string, McpServerChoice>();
  for (const tool of tools) {
    if (!servers.has(tool.server_id))
      servers.set(tool.server_id, {
        id: tool.server_id,
        name: workflowMcpServerName(tool),
        tools: [],
      });
    servers.get(tool.server_id)!.tools.push(tool);
  }
  return [...servers.values()].sort((a, b) => a.name.localeCompare(b.name));
}

// Only offer managed model families whose exact operations are available.
// Other servers still use the shared AI task with their own discovered tools.
export function cadModelTypes(tools: WorkflowMcpTool[]) {
  const names = new Set(tools.map((tool) => tool.tool_name));
  return [
    { tool: "cad.create_part_from_recipe", label: "Part", extension: "par" },
    {
      tool: "cad.create_sheet_metal_from_recipe",
      label: "Sheet metal",
      extension: "psm",
    },
    {
      tool: "cad.create_assembly_from_recipe",
      label: "Assembly",
      extension: "asm",
    },
  ].filter((type) => names.has(type.tool));
}

export function createMcpServerBlock(
  server: McpServerChoice,
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  selectedBlockId?: string,
): RecoveryCommand[] {
  const add = createAuthoringObject("mcp-task", workflow, layout, {
    selectedBlockId,
  });
  add.block.title = server.name;
  add.block.purpose = `Complete an engineering task using ${server.name}.`;
  Object.assign(add.block.configuration, {
    mcp_server: server.id,
    mcp_server_name: server.name,
    binding_state: "configured",
  });
  const commands: RecoveryCommand[] = [add];
  const names = new Set(server.tools.map((tool) => tool.tool_name));
  const models = cadModelTypes(server.tools);
  if (
    names.has("cad.list_providers") &&
    names.has("cad.list_documents") &&
    names.has("cad.save_document") &&
    models.length
  ) {
    const extension = models[0]!.extension;
    const cad: CadOptions = {
      source: "new",
      edit_mode: "in_place",
      copy_path: `model-copy.${extension}`,
      save_native: true,
      native_path: `model.${extension}`,
      policy: "indexed",
      exports: [],
    };
    commands.push(
      ...cadCommands(
        add.block,
        {
          ...workflow,
          blocks: [...workflow.blocks, add.block],
          ports: [...workflow.ports, ...add.ports],
        },
        cad,
      ),
    );
    commands.push({
      kind: "set_block_configuration",
      blockId: add.block.id,
      key: "max_tool_calls",
      value: 32,
    });
    commands.push({
      kind: "set_block_configuration",
      blockId: add.block.id,
      key: "timeout_seconds",
      value: 600,
    });
  }
  return commands;
}
