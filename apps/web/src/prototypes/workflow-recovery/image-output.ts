import type { RecoveryCommand } from "./command-system";
import { findPort, type RecoveryBlock, type RecoveryWorkflow } from "./model";
import { sourceKey } from "./prompt-settings";

export interface ImageOutput {
  format: "png" | "jpeg";
  path: string;
  port: string;
}

export function imageOutput(block: RecoveryBlock): ImageOutput | null {
  try {
    const value = JSON.parse(String(block.configuration.image_output));
    return value &&
      ["png", "jpeg"].includes(value.format) &&
      typeof value.path === "string" &&
      typeof value.port === "string"
      ? value
      : null;
  } catch {
    return null;
  }
}

/** Image bytes become a verified file; activity text is supporting evidence. */
export function imageOutputCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  value: ImageOutput | null,
): RecoveryCommand[] {
  if (block.configuration.cad || block.configuration.application_resource)
    throw new Error("Set model image formats in this task's Exports.");
  if (block.outputPortIds.length !== 1)
    throw new Error(
      "This task has several outputs. Use a separate AI image task to preserve them.",
    );
  const port = findPort(workflow, block.outputPortIds[0]!);
  if (!port || port.artifactContractId)
    throw new Error(
      "This output has an engineering contract. Use a separate AI image task.",
    );
  const previous = imageOutput(block);
  if (!previous && String(block.configuration.expected_files ?? "").trim())
    throw new Error(
      "This task already declares tool-created files. Use a separate AI image task to preserve those outputs.",
    );
  const template = block.configuration.mcp_server ? "mcp-task" : "ai-prompt";
  const changing =
    !previous ||
    !value ||
    previous.format !== value.format ||
    previous.path !== value.path ||
    (value && block.configuration.authoring_template !== template);
  if (!changing) return [];
  if (workflow.relationships.some((edge) => edge.sourceId === port.id))
    throw new Error(
      "This output is connected to another step. Disconnect it before changing its format or filename.",
    );
  if (value) {
    value = { ...value, port: sourceKey(port.id) };
  }
  const references: RecoveryCommand[] = [];
  if (
    value &&
    !workflow.ports.some(
      (input) =>
        input.ownerBlockId === block.id &&
        input.direction === "input" &&
        input.name === "Reference image",
    )
  ) {
    // Explicit image configuration upgrades older blocks; loading does not edit source.
    const id = `port.${block.id.slice(6)}-reference-image-in`;
    if (findPort(workflow, id))
      throw new Error(
        "The reference image address is already used. Use a new AI image task.",
      );
    references.push({
      kind: "add_port",
      port: {
        id,
        ownerBlockId: block.id,
        direction: "input",
        name: "Reference image",
        typeId: "type.file.workspace",
        required: false,
        cardinality: "optional",
        artifactContractId: null,
        description: "Image supplied separately from the task instructions.",
      },
    });
  }
  const setting = (key: string, next: string | boolean): RecoveryCommand => ({
    kind: "set_block_configuration",
    blockId: block.id,
    key,
    value: next,
  });
  const path = value
    ? `outputs/{{wright.run_id}}/${sourceKey(block.id)}/${value.path}`
    : "";
  return [
    ...references,
    { kind: "delete_port", portId: port.id },
    {
      kind: "add_port",
      port: {
        ...port,
        name: value ? "Image" : "Response",
        typeId: value ? "type.file.workspace" : "type.document.engineering",
      },
    },
    setting("image_output", value ? JSON.stringify(value) : ""),
    setting("authoring_template", template),
    setting("output_format", "text"),
    setting("save_output", false),
    setting("expected_files", path),
    setting(
      "expected_file_ports",
      value ? JSON.stringify({ [value.port]: path }) : "{}",
    ),
    setting("run_path_template", value ? "wright.run-path/1" : ""),
    setting("revision_policy", value ? "create_new_files" : ""),
  ];
}
