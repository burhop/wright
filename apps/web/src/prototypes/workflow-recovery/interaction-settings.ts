import type { RecoveryCommand } from "./command-system";
import {
  RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY,
  recoveryAuthoringSectionKind,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import { sourceKey } from "./prompt-settings";

export const isHumanInputBlock = (block: RecoveryBlock | null) =>
  block?.configuration.authoring_template === "human-input";

/** Read the existing nested-object envelope; never reinterpret a scalar as authority. */
export function interactionObject(
  block: RecoveryBlock,
  key: "interaction_input" | "human_interaction",
): Record<string, unknown> | null {
  const retained = block.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY];
  if (retained === undefined) return null;
  const objects: unknown = JSON.parse(String(retained));
  if (!objects || typeof objects !== "object" || Array.isArray(objects))
    throw new Error(
      "The stored declaration object is invalid. Inspect its source.",
    );
  const value = (objects as Record<string, unknown>)[key];
  if (value === undefined) return null;
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error(
      "The stored declaration must be an object. Inspect its source.",
    );
  return structuredClone(value) as Record<string, unknown>;
}

export function declarationJson(text: string): Record<string, unknown> {
  if (new TextEncoder().encode(text).length > 65536)
    throw new Error("Keep the declaration within 64 KiB.");
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("Use a complete JSON object for the declaration.");
  }
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Use a JSON object for the declaration.");
  const depth = (item: unknown, level = 0): void => {
    if (level > 24)
      throw new Error("Keep declaration nesting within 24 levels.");
    if (typeof item === "number" && !Number.isFinite(item))
      throw new Error("Use finite numbers in the declaration.");
    if (item && typeof item === "object")
      Object.values(item).forEach((child) => depth(child, level + 1));
  };
  depth(value);
  return value as Record<string, unknown>;
}

export function inputDeclarationCommands(
  block: RecoveryBlock,
  text: string,
): RecoveryCommand[] {
  if (recoveryAuthoringSectionKind(block) !== "input")
    throw new Error("Choose an input source for preparation metadata.");
  const value = declarationJson(text);
  if (
    value.version !== 1 ||
    !value.value_schema ||
    typeof value.value_schema !== "object" ||
    Array.isArray(value.value_schema)
  )
    throw new Error("Declare version 1 and an object value_schema.");
  if (value.required !== undefined && typeof value.required !== "boolean")
    throw new Error("Required must be true or false.");
  return [
    {
      kind: "set_block_object_configuration",
      blockId: block.id,
      key: "interaction_input",
      value,
    },
  ];
}

/** Only declared incoming structured task outputs may resolve planned questions. */
export function connectedRequirementsSources(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
) {
  return workflow.relationships
    .filter(
      (edge) =>
        edge.kind === "data" && block.inputPortIds.includes(edge.targetId),
    )
    .flatMap((edge) => {
      const port = workflow.ports.find((item) => item.id === edge.sourceId);
      const owner = workflow.blocks.find(
        (item) => item.id === port?.ownerBlockId,
      );
      if (
        !port ||
        !owner ||
        port.direction !== "output" ||
        port.typeId !== "type.result.structured" ||
        owner.executionKind === "human" ||
        recoveryAuthoringSectionKind(owner) !== "task"
      )
        return [];
      return [
        {
          key: `${sourceKey(owner.id)}.${sourceKey(port.id)}`,
          label: `${owner.title} · ${port.name}`,
        },
      ];
    })
    .filter(
      (item, index, all) =>
        all.findIndex((value) => value.key === item.key) === index,
    );
}

export function humanInputDeclarationCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  text: string,
): RecoveryCommand[] {
  if (
    !isHumanInputBlock(block) ||
    block.executionKind !== "human" ||
    block.kind !== "work"
  )
    throw new Error("Choose a declared Engineer input step.");
  const value = declarationJson(text);
  if (
    ![1, 2, 3].includes(value.version as number) ||
    value.kind !== "input" ||
    typeof value.instructions !== "string" ||
    !value.instructions.trim() ||
    value.instructions.length > 8000
  )
    throw new Error(
      "Declare version 1, 2 or 3 input with meaningful instructions of at most 8,000 characters.",
    );
  if (
    !value.response_schema ||
    typeof value.response_schema !== "object" ||
    Array.isArray(value.response_schema) ||
    (value.response_schema as Record<string, unknown>).type !== "object"
  )
    throw new Error("The response schema must declare type object.");
  if (value.version === 3) {
    const when = value.when as Record<string, unknown> | null;
    const schema = value.response_schema as Record<string, unknown>;
    const properties = schema.properties;
    const fieldNames =
      properties && typeof properties === "object" && !Array.isArray(properties)
        ? Object.keys(properties)
        : [];
    if (
      !when ||
      typeof when !== "object" ||
      Array.isArray(when) ||
      Object.keys(when).some(
        (key) => !["kind", "source", "fields"].includes(key),
      ) ||
      when.kind !== "unresolved_fields" ||
      typeof when.source !== "string" ||
      !connectedRequirementsSources(block, workflow).some(
        (item) => item.key === when.source,
      ) ||
      !Array.isArray(when.fields) ||
      !fieldNames.length ||
      schema.additionalProperties !== false ||
      when.fields.length !== fieldNames.length ||
      !when.fields.every(
        (field) => typeof field === "string" && fieldNames.includes(field),
      ) ||
      new Set(when.fields).size !== fieldNames.length
    )
      throw new Error(
        "Conditional input needs a connected structured task result and exactly the declared answer fields, with additionalProperties false.",
      );
  } else if (value.when !== undefined && value.when !== null) {
    throw new Error(
      "A conditional input declaration requires version 3. Choose the declared unresolved-fields condition.",
    );
  }
  const outputs = workflow.ports.filter((port) =>
    block.outputPortIds.includes(port.id),
  );
  if (
    outputs.length !== 1 ||
    outputs[0].typeId !== "type.result.structured" ||
    outputs[0].cardinality !== "one" ||
    value.output_port !== sourceKey(outputs[0].id)
  )
    throw new Error(
      "Use this step's single structured response output. Inspect its connections before changing a port.",
    );
  return [
    {
      kind: "set_block_object_configuration",
      blockId: block.id,
      key: "human_interaction",
      value,
    },
    {
      kind: "set_block_definition",
      blockId: block.id,
      patch: { instructions: value.instructions },
    },
  ];
}

export function declarationEditorKey(block: RecoveryBlock): string {
  return `${block.id}:${block.instructions}:${String(block.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY] ?? "")}`;
}
