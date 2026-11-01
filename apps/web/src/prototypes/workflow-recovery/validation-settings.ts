import profiles from "./validation-profiles.json";
import { stableValue } from "./canonical-wire";
import type { RecoveryCommand } from "./command-system";
import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import { savedResponsePublication, sourceKey } from "./prompt-settings";

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
  rework_scope?: "producer" | "verified_segment";
  repair_subjects?: string[];
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
        (key) =>
          ![
            "profile",
            "baseline",
            "subjects",
            "budget",
            "rework_scope",
            "repair_subjects",
          ].includes(key),
      )
    )
      return null;
    if (
      value.rework_scope !== undefined &&
      !["producer", "verified_segment"].includes(value.rework_scope)
    )
      return null;
    const repairs = value.repair_subjects ?? [];
    if (
      !Array.isArray(repairs) ||
      repairs.some(
        (role) =>
          typeof role !== "string" || !Object.hasOwn(value.subjects, role),
      ) ||
      new Set(repairs).size !== repairs.length
    )
      return null;
    if (
      value.rework_scope === "verified_segment"
        ? !repairs.length
        : repairs.length
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
  if (existing?.rework_scope === "verified_segment")
    throw new Error(
      "This check repeats a group of steps. Edit its requirements and correction settings together in Source.",
    );
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
  if (!reuse) {
    commands.push(
      ...workflow.relationships
        .filter(
          (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
        )
        .map((edge) => ({
          kind: "disconnect" as const,
          relationshipId: edge.id,
        })),
      {
        kind: "set_block_configuration" as const,
        blockId: block.id,
        key: "max_revisions",
        value: 0,
      },
    );
    for (const id of block.inputPortIds)
      commands.push({ kind: "delete_port", portId: id });
  }
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
  const revision = workflow.relationships.find(
    (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
  );
  const nextOwner = workflow.ports.find(
    (port) => port.id === sourceId,
  )?.ownerBlockId;
  if (revision && revision.targetId !== nextOwner)
    commands.push(
      { kind: "disconnect", relationshipId: revision.id },
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "max_revisions",
        value: 0,
      },
    );
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

function safeValidatorProducer(block: RecoveryBlock): boolean {
  const template = block.configuration.authoring_template;
  return (
    block.executionKind === "ai_capable" &&
    !["mcp-task", "mcp-tool"].includes(String(template)) &&
    !block.configuration.cad &&
    !block.configuration.application_resource &&
    template !== "external-action-approval" &&
    template !== "manual-review" &&
    !savedResponsePublication(block) &&
    block.configuration.file_policy !== "overwrite"
  );
}

export function validationRevisionTargets(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
): RecoveryBlock[] {
  const settings = validatorSettings(block);
  if (!settings) return [];
  const inputIds = new Set(
    block.inputPortIds.filter((id) =>
      Object.values(settings.subjects).includes(sourceKey(id)),
    ),
  );
  const owners = new Set(
    workflow.relationships
      .filter((edge) => edge.kind === "data" && inputIds.has(edge.targetId))
      .map(
        (edge) =>
          workflow.ports.find((port) => port.id === edge.sourceId)
            ?.ownerBlockId,
      )
      .filter((id): id is string => Boolean(id)),
  );
  if (owners.size !== 1) return [];
  const ownerId = [...owners][0]!;
  const validatorIndex = workflow.blocks.findIndex(
    (item) => item.id === block.id,
  );
  const ownerIndex = workflow.blocks.findIndex((item) => item.id === ownerId);
  const owner = workflow.blocks[ownerIndex];
  if (
    !owner ||
    ownerIndex < 0 ||
    validatorIndex < 0 ||
    ownerIndex >= validatorIndex ||
    !safeValidatorProducer(owner)
  )
    return [];
  return [owner];
}

export function validationRevisionCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  targetId: string,
): RecoveryCommand[] {
  const commands: RecoveryCommand[] = workflow.relationships
    .filter((edge) => edge.kind === "feedback" && edge.sourceId === block.id)
    .map((edge) => ({ kind: "disconnect", relationshipId: edge.id }));
  if (!targetId) {
    commands.push({
      kind: "set_block_configuration",
      blockId: block.id,
      key: "max_revisions",
      value: 0,
    });
    return commands;
  }
  if (
    !validationRevisionTargets(block, workflow).some(
      (item) => item.id === targetId,
    )
  )
    throw new Error(
      "Automatic correction requires one earlier ordinary AI producer that owns every validated subject.",
    );
  commands.push(
    {
      kind: "connect",
      relationship: {
        id: `rel.validation-revision-${block.id.replaceAll(".", "-")}`,
        kind: "feedback",
        sourceId: block.id,
        targetId,
        label: "Correct output",
        condition: "revise",
      },
    },
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "max_revisions",
      value: Math.max(1, Number(block.configuration.max_revisions ?? 0)),
    },
  );
  return commands;
}

export function validationRevisionLimitCommands(
  block: RecoveryBlock,
  workflow: RecoveryWorkflow,
  limit: number,
): RecoveryCommand[] {
  if (!Number.isInteger(limit) || limit < 0 || limit > 3)
    throw new Error(
      "Choose a whole-number correction limit from zero to three.",
    );
  const commands: RecoveryCommand[] = [
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "max_revisions",
      value: limit,
    },
  ];
  if (limit === 0)
    commands.unshift(
      ...workflow.relationships
        .filter(
          (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
        )
        .map((edge) => ({
          kind: "disconnect" as const,
          relationshipId: edge.id,
        })),
    );
  return commands;
}
