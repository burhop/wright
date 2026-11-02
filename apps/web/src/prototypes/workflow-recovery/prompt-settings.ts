import type { RecoveryCommand } from "./command-system";
import { findPort, type RecoveryBlock, type RecoveryWorkflow } from "./model";
import { configuredOutputs } from "./output-contracts";

const IMAGE_FORMATS = new Set([
  "png",
  "jpg",
  "jpeg",
  "webp",
  "gif",
  "screenshot_jpeg",
  "screenshot_png",
]);
export function isImageSource(
  portId: string,
  workflow: RecoveryWorkflow,
): boolean {
  const port = findPort(workflow, portId);
  const owner = workflow.blocks.find(
    (block) => block.id === port?.ownerBlockId,
  );
  if (!port || !owner) return false;
  if (port.typeId === "type.image.reference-set") return true;
  const format = configuredOutputs(owner, workflow).get(
    sourceKey(port.id),
  )?.format;
  if (format && IMAGE_FORMATS.has(format)) return true;
  const path =
    port.typeId === "type.file.workspace" && owner.configuration.workspace_file;
  return typeof path === "string" && /\.(png|jpe?g|webp|gif)$/i.test(path);
}

export const RESPONSE_FORMATS = {
  text: ".txt",
  markdown: ".md",
  html: ".html",
  json: ".json",
} as const;
export type ResponseFormat = keyof typeof RESPONSE_FORMATS;
/** Display source-authored publication without inventing or changing its binding. */
export function savedResponsePublication(block: RecoveryBlock) {
  const policy = String(block.configuration.file_policy ?? "indexed");
  const namedPort = block.configuration.saved_response_file_port;
  const publishing =
    policy === "publish_indexed" || policy === "publish_overwrite";
  if (!publishing && namedPort === undefined) return null;
  return {
    policy,
    label:
      policy === "publish_overwrite"
        ? "Publish at this run's configured path"
        : "Publish an indexed response file",
    publishing,
    port: typeof namedPort === "string" && namedPort ? namedPort : null,
  };
}
export const sourceKey = (id: string) =>
  id
    .slice(id.indexOf(".") + 1)
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .toLowerCase();
export const isPromptBlock = (block: RecoveryBlock | null) =>
  block?.executionKind === "ai_capable" &&
  block.kind === "work" &&
  block.bindingId === null;
export function promptIsConfigured(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
): boolean {
  return block.configuration.prompt_source === "connection"
    ? workflow.ports.some(
        (port) =>
          port.ownerBlockId === block.id &&
          port.direction === "input" &&
          sourceKey(port.id) === block.configuration.prompt_input &&
          workflow.relationships.some(
            (edge) =>
              edge.kind === "data" &&
              edge.targetId === port.id &&
              findPort(workflow, edge.sourceId)?.direction === "output",
          ),
      )
    : Boolean(block.instructions.trim());
}
export function promptConfigurationLabel(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
): string {
  return promptIsConfigured(block, workflow)
    ? "Configured AI prompt"
    : "Prompt not configured";
}
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
  if (references) types.add("type.image.reference-set");
  return workflow.ports.filter(
    (port) =>
      port.direction === "output" &&
      !descendants.has(port.ownerBlockId) &&
      types.has(port.typeId) &&
      (references || !isImageSource(port.id, workflow)) &&
      port.cardinality !== "many",
  );
}
export function connectPromptCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  sourceId: string,
): RecoveryCommand[] {
  const oldKey = block.configuration.prompt_input;
  const oldPort =
    workflow.ports.find(
      (port) =>
        port.ownerBlockId === block.id &&
        port.direction === "input" &&
        sourceKey(port.id) === oldKey,
    ) ??
    workflow.ports.find(
      (port) =>
        port.ownerBlockId === block.id &&
        port.direction === "input" &&
        port.name === "Prompt",
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
  const reusable =
    oldPort &&
    !oldPort.artifactContractId &&
    !workflow.relationships.some(
      (edge) =>
        (edge.sourceId === oldPort.id || edge.targetId === oldPort.id) &&
        edge.kind !== "data",
    )
      ? oldPort
      : undefined;
  const targetId =
    reusable?.id ??
    workflow.ports.find(
      (port) =>
        port.ownerBlockId === block.id &&
        port.direction === "input" &&
        port.name === "Prompt" &&
        port.typeId === source.typeId,
    )?.id ??
    `port.${block.id.slice(6)}-prompt-${source.typeId.slice(5).replaceAll(".", "-")}`;
  if (reusable && reusable.typeId !== source.typeId)
    commands.push({
      kind: "set_port_type",
      portId: targetId,
      typeId: source.typeId,
    });
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
  targetPortId?: string,
): RecoveryCommand[] {
  const source = promptSourceCandidates(block, workflow, true).find(
    (port) => port.id === sourceId,
  );
  if (!source) return [];
  const imagePort = workflow.ports.find(
    (port) =>
      port.ownerBlockId === block.id &&
      port.direction === "input" &&
      port.name === "Reference image" &&
      !workflow.relationships.some((edge) => edge.targetId === port.id),
  );
  const targetId =
    targetPortId ??
    (isImageSource(sourceId, workflow) ? imagePort?.id : undefined) ??
    `port.${block.id.slice(6)}-reference-${source.id.slice(5)}`;
  const target = findPort(workflow, targetId);
  if (
    targetPortId &&
    (!target ||
      target.ownerBlockId !== block.id ||
      target.name !== "Reference image" ||
      !isImageSource(sourceId, workflow))
  )
    return [];
  const incoming = workflow.relationships.filter(
    (edge) => edge.targetId === targetId,
  );
  if (incoming.some((edge) => edge.sourceId === sourceId)) return [];
  return [
    ...incoming.map((edge) => ({
      kind: "disconnect" as const,
      relationshipId: edge.id,
    })),
    ...(target && target.typeId !== source.typeId
      ? [
          {
            kind: "set_port_type" as const,
            portId: targetId,
            typeId: source.typeId,
          },
        ]
      : []),
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
