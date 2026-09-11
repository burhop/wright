import type { RecoveryCommand } from "./command-system";
import {
  findBlock,
  findPort,
  type RecoveryBlock,
  type RecoveryWorkflow,
  type RecoveryPort,
} from "./model";
import { promptSourceCandidates, sourceKey } from "./prompt-settings";

export interface ToolSchema {
  type?: string | string[];
  title?: string;
  description?: string;
  enum?: unknown[];
  default?: unknown;
  properties?: Record<string, ToolSchema>;
  required?: string[];
  anyOf?: ToolSchema[];
  oneOf?: ToolSchema[];
}
export interface WorkflowMcpTool {
  name: string;
  server_id: string;
  server_name?: string;
  tool_name: string;
  title: string;
  description: string;
  input_schema: ToolSchema;
  output_schema?: ToolSchema;
  schema_digest: string;
}
export const isMcpBlock = (block: RecoveryBlock | null) =>
  block?.configuration.authoring_template === "mcp-tool";

export function hiddenMcpInputs(workflow: RecoveryWorkflow): Set<string> {
  const connected = new Set(
    workflow.relationships.map((edge) => edge.targetId),
  );
  return new Set(
    workflow.blocks
      .filter(isMcpBlock)
      .flatMap((block) =>
        block.inputPortIds.filter(
          (id) =>
            !connected.has(id) &&
            !(
              block.configuration.mcp_arguments_source === "connection" &&
              sourceKey(id) === block.configuration.mcp_arguments_input
            ),
        ),
      ),
  );
}
export function readJson<T>(value: unknown, fallback: T): T {
  try {
    const parsed = JSON.parse(String(value));
    return parsed !== null &&
      typeof parsed === "object" &&
      !Array.isArray(parsed)
      ? (parsed as T)
      : fallback;
  } catch {
    return fallback;
  }
}
export function fieldSchema(schema: ToolSchema): ToolSchema {
  return (
    schema.anyOf?.find((s) => s.type !== "null") ??
    schema.oneOf?.find((s) => s.type !== "null") ??
    schema
  );
}
export function workflowMcpServerName(
  tool: Pick<WorkflowMcpTool, "server_name">,
): string {
  const name = tool.server_name?.trim();
  return name && !/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(name)
    ? name
    : "MCP server";
}
export async function listWorkflowMcpTools(
  sessionId: string,
): Promise<WorkflowMcpTool[]> {
  // Registry names are presentation metadata; tool/server IDs remain the binding keys.
  const serverNames = fetch("/api/mcp/servers", { credentials: "same-origin" })
    .then(async (response) => {
      if (!response.ok) return new Map<string, string>();
      const data = await response.json();
      return new Map<string, string>(
        (data.servers ?? []).map(
          (server: { server_id: string; name: string }) => [
            server.server_id,
            server.name,
          ],
        ),
      );
    })
    .catch(() => new Map<string, string>());
  const [response, names] = await Promise.all([
    fetch(
      `/api/workspace/workflow-sources/tools?session_id=${encodeURIComponent(sessionId)}`,
      { credentials: "same-origin" },
    ),
    serverNames,
  ]);
  if (!response.ok)
    throw new Error(
      "Tools could not be loaded. Check Tool Registry and retry.",
    );
  const data: { tools: WorkflowMcpTool[] } = await response.json();
  return data.tools.map((tool) => ({
    ...tool,
    server_name: names.get(tool.server_id) ?? tool.server_name,
  }));
}
export function configureMcpTool(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  tool: WorkflowMcpTool,
): RecoveryCommand[] {
  const commands: RecoveryCommand[] = workflow.relationships
    .filter((edge) => block.inputPortIds.includes(edge.targetId))
    .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
  commands.push(
    ...block.inputPortIds.map((portId): RecoveryCommand => ({
      kind: "delete_port",
      portId,
    })),
  );
  const mapping: Record<string, string> = {};
  const values: Record<string, unknown> = {};
  const add = (
    suffix: string,
    name: string,
    typeId: string,
    description: string,
  ) => {
    const id = `port.${block.id.slice(6)}-${suffix}`;
    commands.push({
      kind: "add_port",
      port: {
        id,
        ownerBlockId: block.id,
        name,
        typeId,
        direction: "input",
        cardinality: "optional",
        required: false,
        artifactContractId: null,
        description,
      },
    });
    return sourceKey(id);
  };
  const jsonInput = add(
    "arguments",
    "Arguments (JSON)",
    "type.result.structured",
    "A complete JSON object with this tool's named arguments.",
  );
  Object.entries(tool.input_schema.properties ?? {}).forEach(
    ([name, schema], index) => {
      mapping[
        add(
          `argument-${index}`,
          name,
          fieldSchema(schema).type === "string"
            ? "type.document.engineering"
            : "type.result.structured",
          schema.description || `Value for ${name}.`,
        )
      ] = name;
      if (schema.default !== undefined && schema.default !== null)
        values[name] = schema.default;
    },
  );
  const config = {
    mcp_tool: tool.name,
    mcp_server: tool.server_id,
    mcp_schema_digest: tool.schema_digest,
    mcp_input_schema: JSON.stringify(tool.input_schema),
    mcp_description: tool.description,
    mcp_arguments: JSON.stringify(values),
    mcp_argument_ports: JSON.stringify(mapping),
    mcp_arguments_input: jsonInput,
    mcp_arguments_source: "fields",
    binding_state: "configured",
  };
  commands.push(
    ...Object.entries(config).map(([key, value]): RecoveryCommand => ({
      kind: "set_block_configuration",
      blockId: block.id,
      key,
      value,
    })),
  );
  if (
    block.title === "MCP tool" ||
    block.title === String(block.configuration.mcp_tool_title)
  )
    commands.push({
      kind: "set_block_title",
      blockId: block.id,
      title: tool.title,
    });
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "mcp_tool_title",
    value: tool.title,
  });
  return commands;
}
export function mcpCandidates(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  target: RecoveryPort,
) {
  const name = readJson<Record<string, string>>(
    block.configuration.mcp_argument_ports,
    {},
  )[sourceKey(target.id)];
  const schema = readJson<ToolSchema>(block.configuration.mcp_input_schema, {});
  const isText =
    name && fieldSchema(schema.properties?.[name] ?? {}).type === "string";
  return promptSourceCandidates(block, workflow).filter(
    (port) =>
      isText ||
      port.typeId === "type.result.structured" ||
      isPromptAiJson(findBlock(workflow, port.ownerBlockId)),
  );
}
function isPromptAiJson(block: RecoveryBlock | null) {
  return (
    block?.executionKind === "ai_capable" &&
    block.configuration.output_format === "json"
  );
}
export function connectMcpInput(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  targetId: string,
  sourceId: string,
): RecoveryCommand[] {
  const target = findPort(workflow, targetId);
  if (!target) return [];
  const commands: RecoveryCommand[] = workflow.relationships
    .filter((edge) => edge.targetId === targetId)
    .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
  if (!sourceId) return commands;
  const source = mcpCandidates(block, workflow, target).find(
    (p) => p.id === sourceId,
  );
  if (!source)
    throw new Error(
      "Choose an upstream response that matches this tool input.",
    );
  if (target.typeId !== source.typeId)
    commands.push({
      kind: "set_port_type",
      portId: targetId,
      typeId: source.typeId,
    });
  const whole = sourceKey(targetId) === block.configuration.mcp_arguments_input;
  if (
    (whole ? "connection" : "fields") !==
    (block.configuration.mcp_arguments_source ?? "fields")
  ) {
    commands.push(
      ...workflow.relationships
        .filter(
          (edge) =>
            edge.targetId !== targetId &&
            block.inputPortIds.includes(edge.targetId),
        )
        .map((edge): RecoveryCommand => ({
          kind: "disconnect",
          relationshipId: edge.id,
        })),
    );
  }
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "mcp_arguments_source",
    value: whole ? "connection" : "fields",
  });
  commands.push({
    kind: "connect",
    relationship: {
      id: `rel.${targetId.slice(5)}-source`,
      kind: "data",
      sourceId,
      targetId,
      label: target.name,
      condition: null,
    },
  });
  return commands;
}
