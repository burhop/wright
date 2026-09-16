import profiles from "./validation-profiles.json";
import { stableValue } from "./canonical-wire";
import type { RecoveryCommand } from "./command-system";
import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import { sourceKey } from "./prompt-settings";

export const validationProfiles = profiles;
export const isValidatorBlock = (block: RecoveryBlock | null) =>
  block?.configuration.authoring_template === "process-validator";

export interface ValidatorSettings {
  profile: {
    source: "packaged" | "workspace";
    name: string;
    reference: { id: string; version: string; sha256: string };
  };
  baseline: { id: string; version: string; sha256: string };
  subjects: Record<string, string>;
  budget?: {
    max_bytes?: number;
    max_entities?: number;
    timeout_seconds?: number;
    memory_limit_mb?: number;
  };
}

export function validatorSettings(
  block: RecoveryBlock,
): ValidatorSettings | null {
  try {
    const result: unknown = JSON.parse(String(block.configuration.validation));
    if (!result || typeof result !== "object" || Array.isArray(result))
      return null;
    const value = result as ValidatorSettings;
    const pin = (p: unknown): boolean =>
      !!p &&
      typeof p === "object" &&
      !Array.isArray(p) &&
      ["id", "version", "sha256"].every(
        (k) => typeof (p as Record<string, unknown>)[k] === "string",
      ) &&
      /^[a-f0-9]{64}$/.test(String((p as Record<string, unknown>).sha256));
    if (
      !value.profile ||
      !["packaged", "workspace"].includes(value.profile.source) ||
      typeof value.profile.name !== "string" ||
      !pin(value.profile.reference) ||
      !pin(value.baseline) ||
      !value.subjects ||
      typeof value.subjects !== "object" ||
      Array.isArray(value.subjects) ||
      !Object.keys(value.subjects).length ||
      Object.values(value.subjects).some((s) => typeof s !== "string" || !s) ||
      new Set(Object.values(value.subjects)).size !==
        Object.keys(value.subjects).length ||
      Object.keys(value).some(
        (key) => !["profile", "baseline", "subjects", "budget"].includes(key),
      )
    )
      return null;
    return value;
  } catch {
    return null;
  }
}

export function validationProfileCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  name: string,
): RecoveryCommand[] {
  const profile = validationProfiles.find((item) => item.name === name);
  if (!profile) throw new Error("Choose an available validation profile.");
  const existing = validatorSettings(block);
  const roles = profile.roles;
  const reuse =
    existing &&
    JSON.stringify(Object.keys(existing.subjects).sort()) ===
      JSON.stringify([...roles].sort());
  if (
    !reuse &&
    workflow.relationships.some(
      (edge) =>
        edge.kind === "data" && block.inputPortIds.includes(edge.targetId),
    )
  )
    throw new Error(
      "Disconnect the current subjects before changing to a profile with different inputs.",
    );
  const commands: RecoveryCommand[] = [];
  const subjects: Record<string, string> = {};
  if (!reuse)
    for (const id of block.inputPortIds)
      commands.push({ kind: "delete_port", portId: id });
  for (const role of roles) {
    const id = `port.${block.id.slice(6)}-subject-${role.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
    subjects[role] = reuse ? existing.subjects[role]! : sourceKey(id);
    if (!reuse)
      commands.push({
        kind: "add_port",
        port: {
          id,
          ownerBlockId: block.id,
          direction: "input",
          name: role,
          typeId: "type.document.engineering",
          required: true,
          cardinality: "one",
          artifactContractId: null,
          description: `Exact producer output inspected for ${role}.`,
        },
      });
  }
  commands.push({
    kind: "set_block_configuration",
    blockId: block.id,
    key: "validation",
    value: JSON.stringify(
      stableValue({
        profile: {
          source: "packaged",
          name: profile.name,
          reference: profile.profile_ref,
        },
        baseline: profile.baseline_ref,
        subjects,
      } satisfies ValidatorSettings),
    ),
  });
  return commands;
}

export function validationSubjectCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  targetId: string,
  sourceId: string,
): RecoveryCommand[] {
  const target = workflow.ports.find(
    (port) =>
      port.id === targetId &&
      port.ownerBlockId === block.id &&
      port.direction === "input",
  );
  if (!target) throw new Error("Choose a validator input.");
  const commands: RecoveryCommand[] = workflow.relationships
    .filter((edge) => edge.kind === "data" && edge.targetId === target.id)
    .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
  if (sourceId) {
    const source = workflow.ports.find(
      (port) =>
        port.id === sourceId &&
        port.direction === "output" &&
        port.ownerBlockId !== block.id,
    );
    if (!source) throw new Error("Choose a producing step output.");
    commands.push({
      kind: "set_port_type",
      portId: target.id,
      typeId: source.typeId,
    });
    commands.push({
      kind: "connect",
      relationship: {
        id: `rel.validation-${target.id.slice(5)}`,
        kind: "data",
        sourceId: source.id,
        targetId: target.id,
        label: `Validate ${target.name}`,
        condition: null,
      },
    });
  }
  return commands;
}
