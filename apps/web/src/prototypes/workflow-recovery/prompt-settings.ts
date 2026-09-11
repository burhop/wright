import type { RecoveryCommand } from "./command-system";
import { findPort, type RecoveryBlock, type RecoveryWorkflow } from "./model";

export const RESPONSE_FORMATS = {
  text: ".txt",
  markdown: ".md",
  html: ".html",
  json: ".json",
} as const;
export type ResponseFormat = keyof typeof RESPONSE_FORMATS;
export const sourceKey = (id: string) =>
  id
    .slice(id.indexOf(".") + 1)
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .toLowerCase();
export const isPromptBlock = (block: RecoveryBlock | null) =>
  block?.executionKind === "ai_capable" &&
  block.kind === "work" &&
  block.bindingId === null;
export function isFinalPrompt(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
) {
  return !workflow.relationships.some(
    (edge) =>
      edge.kind === "data" && block.outputPortIds.includes(edge.sourceId),
  );
}
export function promptFormat(block: RecoveryBlock): ResponseFormat {
  const format = String(block.configuration.output_format ?? "text");
  return format in RESPONSE_FORMATS ? (format as ResponseFormat) : "text";
}
export function promptFilename(block: RecoveryBlock) {
  return String(
    block.configuration.output_filename ??
      `${sourceKey(block.id).replaceAll("_", "-")}${RESPONSE_FORMATS[promptFormat(block)]}`,
  );
}
export function promptSourceCandidates(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  references = false,
) {
  const descendants = new Set([block.id]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of workflow.relationships.filter(
      (e) => e.kind === "data",
    )) {
      const source = findPort(workflow, edge.sourceId)?.ownerBlockId;
      const target = findPort(workflow, edge.targetId)?.ownerBlockId;
      if (
        source &&
        target &&
        descendants.has(source) &&
        !descendants.has(target)
      ) {
        descendants.add(target);
        changed = true;
      }
    }
  }
  const types = new Set([
    "type.value.text",
    "type.file.workspace",
    "type.document.engineering",
    "type.design.specification",
    "type.report.check",
    "type.result.structured",
  ]);
  if (references && block.configuration.authoring_template !== "mcp-task")
    types.add("type.image.reference-set");
  return workflow.ports.filter(
    (port) =>
      port.direction === "output" &&
      !descendants.has(port.ownerBlockId) &&
      types.has(port.typeId) &&
      port.cardinality !== "many",
  );
}
export function connectPromptCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  sourceId: string,
): RecoveryCommand[] {
  const oldKey = block.configuration.prompt_input;
  const oldPort = workflow.ports.find(
    (port) => port.ownerBlockId === block.id && sourceKey(port.id) === oldKey,
  );
  const commands: RecoveryCommand[] = workflow.relationships
    .filter((edge) => edge.kind === "data" && edge.targetId === oldPort?.id)
    .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
  if (!sourceId)
    return [
      ...commands,
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "prompt_input",
        value: "",
      },
    ];
  const source = promptSourceCandidates(block, workflow).find(
    (port) => port.id === sourceId,
  );
  if (!source) throw new Error("Choose a compatible upstream response.");
  const targetId =
    workflow.ports.find(
      (port) =>
        port.ownerBlockId === block.id &&
        port.direction === "input" &&
        port.name === "Prompt" &&
        port.typeId === source.typeId,
    )?.id ??
    `port.${block.id.slice(6)}-prompt-${source.typeId.slice(5).replaceAll(".", "-")}`;
  if (!findPort(workflow, targetId))
    commands.push({
      kind: "add_port",
      port: {
        id: targetId,
        ownerBlockId: block.id,
        direction: "input",
        name: "Prompt",
        typeId: source.typeId,
        required: false,
        cardinality: "optional",
        artifactContractId: null,
        description: "The connected response becomes this step's prompt.",
      },
    });
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "prompt_input",
    value: sourceKey(targetId),
  });
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "prompt_source",
    value: "connection",
  });
  commands.push({
    kind: "connect",
    relationship: {
      id: `rel.${block.id.slice(6)}-prompt`,
      kind: "data",
      sourceId,
      targetId,
      label: "Prompt",
      condition: null,
    },
  });
  return commands;
}

export function connectReferenceCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  sourceId: string,
): RecoveryCommand[] {
  const source = promptSourceCandidates(block, workflow, true).find(
    (port) => port.id === sourceId,
  );
  if (!source) return [];
  const targetId = `port.${block.id.slice(6)}-reference-${source.id.slice(5)}`;
  if (workflow.relationships.some((edge) => edge.targetId === targetId))
    return [];
  return [
    ...(!findPort(workflow, targetId)
      ? [
          {
            kind: "add_port" as const,
            port: {
              id: targetId,
              ownerBlockId: block.id,
              direction: "input" as const,
              name: `Reference: ${source.name}`,
              typeId: source.typeId,
              required: false,
              cardinality: "optional" as const,
              artifactContractId: null,
              description: "Supporting material appended to the prompt.",
            },
          },
        ]
      : []),
    {
      kind: "connect",
      relationship: {
        id: `rel.${block.id.slice(6)}-reference-${source.id.slice(5)}`,
        kind: "data",
        sourceId,
        targetId,
        label: "Reference material",
        condition: null,
      },
    },
  ];
}
