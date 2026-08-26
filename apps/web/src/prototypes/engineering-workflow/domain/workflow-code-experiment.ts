import { z } from "zod";

import type {
  WorkflowBlockRole,
  WorkflowConnectionSemantics,
  WorkflowPhaseTone,
  WorkflowPreview,
  WorkflowPreviewDataType,
} from "../workflow-preview-model";

export const WORKFLOW_CODE_EXPERIMENT_VERSION = "0.1-discovery" as const;

const identifier = z
  .string()
  .trim()
  .min(1)
  .regex(/^[a-z][a-z0-9-]*$/, "Use lowercase letters, numbers, and hyphens.");

const outputPortSchema = z
  .object({
    portId: identifier,
    label: z.string().trim().min(1),
    dataType: z.enum([
      "request",
      "text",
      "images",
      "documents",
      "instruction",
      "result",
    ]),
  })
  .strict();

const workflowCodeDocumentSchema = z
  .object({
    schemaVersion: z.literal(WORKFLOW_CODE_EXPERIMENT_VERSION),
    workflowId: identifier,
    revision: z.number().int().positive(),
    title: z.string().trim().min(1),
    purpose: z.string().trim().min(1),
    phases: z
      .array(
        z
          .object({
            phaseId: identifier,
            label: z.string().trim().min(1),
            description: z.string().trim().min(1),
          })
          .strict(),
      )
      .min(1)
      .max(6),
    blocks: z
      .array(
        z
          .object({
            blockId: identifier,
            phaseId: identifier,
            role: z.enum([
              "input",
              "ai-task",
              "mcp-action",
              "artifact",
              "decision",
              "notification",
            ]),
            title: z.string().trim().min(1),
            purpose: z.string().trim().min(1),
            outputs: z.array(outputPortSchema).max(8).optional(),
          })
          .strict(),
      )
      .min(1)
      .max(12),
    connections: z
      .array(
        z
          .object({
            connectionId: identifier,
            source: z
              .object({
                blockId: identifier,
                portId: identifier.optional(),
              })
              .strict(),
            target: z
              .object({
                blockId: identifier,
                portId: identifier.optional(),
              })
              .strict(),
            semantics: z.enum(["data", "control", "feedback"]),
            label: z.string().trim().min(1).optional(),
          })
          .strict(),
      )
      .max(20),
  })
  .strict();

export type WorkflowCodeDocument = z.infer<typeof workflowCodeDocumentSchema>;

export interface WorkflowCodeIssue {
  path: string;
  code:
    | "JSON_SYNTAX"
    | "SCHEMA"
    | "DUPLICATE_ID"
    | "UNKNOWN_PHASE"
    | "UNKNOWN_BLOCK"
    | "UNKNOWN_PORT"
    | "REQUIRED_FIXTURE_BLOCK";
  message: string;
}

export type WorkflowCodeParseResult =
  | {
      ok: true;
      document: WorkflowCodeDocument;
      workflow: WorkflowPreview;
    }
  | { ok: false; errors: readonly WorkflowCodeIssue[] };

function duplicateIssues(
  values: readonly string[],
  collectionPath: string,
): WorkflowCodeIssue[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates].map((value) => ({
    path: collectionPath,
    code: "DUPLICATE_ID" as const,
    message: `Identity ${value} is used more than once.`,
  }));
}

function semanticIssues(
  document: WorkflowCodeDocument,
  requiredBlockIds: readonly string[],
): WorkflowCodeIssue[] {
  const errors: WorkflowCodeIssue[] = [
    ...duplicateIssues(
      document.phases.map(({ phaseId }) => phaseId),
      "phases",
    ),
    ...duplicateIssues(
      document.blocks.map(({ blockId }) => blockId),
      "blocks",
    ),
    ...duplicateIssues(
      document.connections.map(({ connectionId }) => connectionId),
      "connections",
    ),
  ];
  const phaseIds = new Set(document.phases.map(({ phaseId }) => phaseId));
  const blocksById = new Map(
    document.blocks.map((block) => [block.blockId, block]),
  );

  document.blocks.forEach((block, index) => {
    if (!phaseIds.has(block.phaseId)) {
      errors.push({
        path: `blocks.${index}.phaseId`,
        code: "UNKNOWN_PHASE",
        message: `Block ${block.blockId} references unknown phase ${block.phaseId}.`,
      });
    }
    errors.push(
      ...duplicateIssues(
        block.outputs?.map(({ portId }) => portId) ?? [],
        `blocks.${index}.outputs`,
      ),
    );
  });

  document.connections.forEach((connection, index) => {
    const source = blocksById.get(connection.source.blockId);
    if (!source) {
      errors.push({
        path: `connections.${index}.source.blockId`,
        code: "UNKNOWN_BLOCK",
        message: `Connection ${connection.connectionId} references unknown source block ${connection.source.blockId}.`,
      });
    } else if (
      connection.source.portId &&
      !source.outputs?.some(({ portId }) => portId === connection.source.portId)
    ) {
      errors.push({
        path: `connections.${index}.source.portId`,
        code: "UNKNOWN_PORT",
        message: `Connection ${connection.connectionId} references unknown output ${connection.source.portId} on ${source.blockId}.`,
      });
    }
    if (!blocksById.has(connection.target.blockId)) {
      errors.push({
        path: `connections.${index}.target.blockId`,
        code: "UNKNOWN_BLOCK",
        message: `Connection ${connection.connectionId} references unknown target block ${connection.target.blockId}.`,
      });
    }
  });

  for (const blockId of requiredBlockIds) {
    if (!blocksById.has(blockId)) {
      errors.push({
        path: "blocks",
        code: "REQUIRED_FIXTURE_BLOCK",
        message: `This four-block experiment requires stable block identity ${blockId}.`,
      });
    }
  }
  return errors;
}

const phaseTones: readonly WorkflowPhaseTone[] = [
  "define",
  "verify",
  "manufacture",
];

function projectDocument(
  document: WorkflowCodeDocument,
  reference: WorkflowPreview,
): WorkflowPreview {
  const referencePhases = new Map(
    reference.phases.map((phase) => [phase.phaseId, phase]),
  );
  const referenceBlocks = new Map(
    reference.blocks.map((block) => [block.blockId, block]),
  );
  const blockIndexWithinPhase = new Map<string, number>();

  return {
    schemaVersion: "0.1-visual-slice",
    workflowId: document.workflowId,
    revision: document.revision,
    title: document.title,
    purpose: document.purpose,
    phases: document.phases.map((phase, index) => ({
      ...phase,
      index: index + 1,
      tone:
        referencePhases.get(phase.phaseId)?.tone ??
        phaseTones[index % phaseTones.length],
      height: referencePhases.get(phase.phaseId)?.height ?? 270,
    })),
    blocks: document.blocks.map((block, index) => {
      const phaseIndex = blockIndexWithinPhase.get(block.phaseId) ?? 0;
      blockIndexWithinPhase.set(block.phaseId, phaseIndex + 1);
      const referenceBlock = referenceBlocks.get(block.blockId);
      const isDecision = block.role === "decision";
      return {
        blockId: block.blockId,
        phaseId: block.phaseId,
        sequence: String(index + 1),
        role: block.role as WorkflowBlockRole,
        title: block.title,
        purpose: block.purpose,
        badge: referenceBlock?.badge,
        outputPorts: block.outputs?.map((output) => ({
          ...output,
          dataType: output.dataType as WorkflowPreviewDataType,
        })),
        position: {
          x: 42 + phaseIndex * 296,
          y: isDecision ? 80 : 92,
          width: isDecision ? 122 : 190,
          height: isDecision ? 122 : 98,
        },
        inspector: {
          summary: block.purpose,
          fields: referenceBlock?.inspector?.fields ?? [],
        },
      };
    }),
    connections: document.connections.map((connection) => ({
      connectionId: connection.connectionId,
      sourceBlockId: connection.source.blockId,
      targetBlockId: connection.target.blockId,
      semantics: connection.semantics as WorkflowConnectionSemantics,
      label: connection.label,
      sourcePortId: connection.source.portId,
      targetPortId: connection.target.portId,
    })),
  };
}

export function workflowCodeDocumentFromPreview(
  workflow: WorkflowPreview,
): WorkflowCodeDocument {
  return {
    schemaVersion: WORKFLOW_CODE_EXPERIMENT_VERSION,
    workflowId: workflow.workflowId,
    revision: workflow.revision,
    title: workflow.title,
    purpose: workflow.purpose,
    phases: workflow.phases.map(({ phaseId, label, description }) => ({
      phaseId,
      label,
      description,
    })),
    blocks: workflow.blocks.map((block) => ({
      blockId: block.blockId,
      phaseId: block.phaseId,
      role: block.role,
      title: block.title,
      purpose: block.purpose,
      ...(block.outputPorts
        ? {
            outputs: block.outputPorts.map(({ portId, label, dataType }) => ({
              portId,
              label,
              dataType,
            })),
          }
        : {}),
    })),
    connections: workflow.connections.map((connection) => ({
      connectionId: connection.connectionId,
      source: {
        blockId: connection.sourceBlockId,
        ...(connection.sourcePortId ? { portId: connection.sourcePortId } : {}),
      },
      target: {
        blockId: connection.targetBlockId,
        ...(connection.targetPortId ? { portId: connection.targetPortId } : {}),
      },
      semantics: connection.semantics,
      ...(connection.label ? { label: connection.label } : {}),
    })),
  };
}

export function serializeWorkflowCodeDocument(
  workflow: WorkflowPreview,
): string {
  return JSON.stringify(workflowCodeDocumentFromPreview(workflow), null, 2);
}

export function parseWorkflowCodeDocument(
  source: string,
  reference: WorkflowPreview,
  requiredBlockIds: readonly string[] = [],
): WorkflowCodeParseResult {
  let value: unknown;
  try {
    value = JSON.parse(source);
  } catch (error) {
    return {
      ok: false,
      errors: [
        {
          path: "$",
          code: "JSON_SYNTAX",
          message:
            error instanceof Error ? error.message : "Invalid JSON document.",
        },
      ],
    };
  }

  const parsed = workflowCodeDocumentSchema.safeParse(value);
  if (!parsed.success) {
    return {
      ok: false,
      errors: parsed.error.issues.map((issue) => ({
        path: issue.path.length ? issue.path.map(String).join(".") : "$",
        code: "SCHEMA" as const,
        message: issue.message,
      })),
    };
  }

  const errors = semanticIssues(parsed.data, requiredBlockIds);
  if (errors.length > 0) return { ok: false, errors };
  return {
    ok: true,
    document: parsed.data,
    workflow: projectDocument(parsed.data, reference),
  };
}
