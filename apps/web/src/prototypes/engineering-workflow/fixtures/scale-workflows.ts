import type {
  WorkflowBlockRole,
  WorkflowPhaseTone,
  WorkflowPreview,
  WorkflowPreviewBlock,
  WorkflowPreviewConnection,
  WorkflowPreviewPhase,
} from "../workflow-preview-model";
import { drillBitHolderWorkflow } from "./drill-bit-holder-workflow";

export type WorkflowScale = 25 | 100;

const phaseTemplates: readonly {
  phaseId: string;
  label: string;
  description: string;
  tone: WorkflowPhaseTone;
}[] = [
  {
    phaseId: "define",
    label: "Define",
    description: "Scaled definition and design work.",
    tone: "define",
  },
  {
    phaseId: "verify",
    label: "Verify",
    description: "Scaled checks, evidence, and review work.",
    tone: "verify",
  },
  {
    phaseId: "manufacture",
    label: "Manufacture",
    description: "Scaled release and handoff work.",
    tone: "manufacture",
  },
] as const;

function roleFor(indexInPhase: number, phaseCount: number): WorkflowBlockRole {
  if (indexInPhase === 0) return "input";
  if (indexInPhase === phaseCount - 1) return "notification";
  if (indexInPhase > 0 && indexInPhase % 9 === 0) return "decision";
  return (["ai-task", "mcp-action", "artifact"] as const)[
    (indexInPhase - 1) % 3
  ];
}

function phaseCounts(blockCount: WorkflowScale): number[] {
  const base = Math.floor(blockCount / phaseTemplates.length);
  const remainder = blockCount % phaseTemplates.length;
  return phaseTemplates.map((_, index) => base + (index < remainder ? 1 : 0));
}

export function createScaleWorkflow(
  blockCount: WorkflowScale,
): WorkflowPreview {
  const counts = phaseCounts(blockCount);
  const phases: WorkflowPreviewPhase[] = phaseTemplates.map(
    (template, index) => ({
      ...template,
      index: index + 1,
      height: 56 + Math.ceil(counts[index] / 10) * 82,
    }),
  );
  const blocks: WorkflowPreviewBlock[] = [];
  let globalIndex = 0;

  for (const [phaseIndex, phase] of phases.entries()) {
    const count = counts[phaseIndex];
    for (let indexInPhase = 0; indexInPhase < count; indexInPhase += 1) {
      globalIndex += 1;
      const role = roleFor(indexInPhase, count);
      blocks.push({
        blockId: `scale-${blockCount}-block-${globalIndex}`,
        phaseId: phase.phaseId,
        sequence: `S${String(globalIndex).padStart(3, "0")}`,
        role,
        title:
          role === "decision"
            ? `Review ${globalIndex}`
            : `Scale Step ${globalIndex}`,
        purpose: `Deterministic ${role} fixture for block ${globalIndex}.`,
        ...(role === "mcp-action" ? { badge: "EXACT TOOL" } : {}),
        ...(role === "artifact" ? { badge: "ARTIFACT" } : {}),
        position: {
          x: 14 + (indexInPhase % 10) * 132,
          y: 50 + Math.floor(indexInPhase / 10) * 82,
          width: role === "decision" ? 76 : 112,
          height: role === "decision" ? 76 : 68,
        },
        inspector: {
          summary: `Scale fixture block ${globalIndex} of ${blockCount}.`,
          fields: [
            { label: "Role", value: role },
            { label: "Phase", value: phase.label },
          ],
        },
      });
    }
  }

  const connections: WorkflowPreviewConnection[] = blocks
    .slice(1)
    .map((target, index) => ({
      connectionId: `scale-${blockCount}-forward-${index + 1}`,
      sourceBlockId: blocks[index].blockId,
      targetBlockId: target.blockId,
      semantics: index % 3 === 0 ? "control" : "data",
    }));

  for (const phase of phases) {
    const phaseBlocks = blocks.filter(
      ({ phaseId }) => phaseId === phase.phaseId,
    );
    if (phaseBlocks.length < 8) continue;
    connections.push({
      connectionId: `scale-${blockCount}-${phase.phaseId}-feedback`,
      sourceBlockId: phaseBlocks.at(-1)!.blockId,
      targetBlockId: phaseBlocks[3].blockId,
      semantics: "feedback",
      label: "revise",
    });
  }

  return {
    schemaVersion: "0.1-visual-slice",
    workflowId: `engineering-workflow-scale-${blockCount}`,
    revision: 1,
    title: `${blockCount}-Block Engineering Workflow Scale Fixture`,
    purpose: "Measure candidate render, fit, selection, and focus behavior.",
    phases,
    blocks,
    connections,
  };
}

export function workflowForBakeoffSearch(search: string): WorkflowPreview {
  const scale = new URLSearchParams(search).get("scale");
  if (scale === "25" || scale === "100") {
    return createScaleWorkflow(Number(scale) as WorkflowScale);
  }
  return drillBitHolderWorkflow;
}
