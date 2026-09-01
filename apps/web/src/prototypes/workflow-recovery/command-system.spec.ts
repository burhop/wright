import { describe, expect, it } from "vitest";

import { acceptRecoveryResult, aiDrawingProposal, applyRecoveryBatch, textEditCommands } from "./command-system";
import { fromCanonicalWire, toCanonicalWire, type CanonicalWorkflowWire } from "./canonical-wire";
import { cloneLayout, cloneWorkflow, initialLayout, initialWorkflow } from "./model";
import { formatRecoveryDsl, parseRecoveryDsl } from "./recovery-dsl";
import goldenWire from "../../../../../specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.json";
import goldenDsl from "../../../../../specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow?raw";

describe("recovery command and source conformance", () => {
  it("is a lossless ergonomic view of the committed canonical wire document", () => {
    expect(toCanonicalWire(initialWorkflow)).toEqual(goldenWire);
    expect(fromCanonicalWire(goldenWire as unknown as CanonicalWorkflowWire)).toEqual(initialWorkflow);
    expect(toCanonicalWire(fromCanonicalWire(goldenWire as unknown as CanonicalWorkflowWire))).toEqual(goldenWire);
  });

  it("uses the exact committed DSL grammar and golden source", () => {
    const formatted = formatRecoveryDsl(initialWorkflow);
    expect(formatted.text).toBe(goldenDsl);
    expect(toCanonicalWire(parseRecoveryDsl(goldenDsl).workflow!)).toEqual(goldenWire);
  });

  it("round-trips every canonical identity through the disposable DSL", () => {
    const formatted = formatRecoveryDsl(initialWorkflow);
    const parsed = parseRecoveryDsl(formatted.text);
    expect(parsed.ok).toBe(true);
    expect(parsed.workflow).toEqual(initialWorkflow);
    expect(Object.keys(parsed.sourceMap)).toHaveLength(44);
    expect(parsed.sourceMap["block.check-manufacturability"]).toBeDefined();
  });

  it("applies a semantic batch atomically and advances one revision", () => {
    const result = applyRecoveryBatch(cloneWorkflow(initialWorkflow), cloneLayout(initialLayout), {
      baseRevision: 1,
      origin: "form",
      commands: [{ kind: "set_block_configuration", blockId: "block.generate-geometry", key: "thickness_mm", value: 8 }],
    });
    expect(result.ok).toBe(true);
    expect(result.semanticChanged).toBe(true);
    const accepted = acceptRecoveryResult(initialWorkflow, result);
    expect(accepted?.workflow.revision).toBe(2);
    expect(accepted?.workflow.parentRevision).toBe(1);
    expect(accepted?.workflow.blocks.find((block) => block.id === "block.generate-geometry")?.configuration.thickness_mm).toBe(8);
  });

  it("keeps layout moves outside the semantic revision", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, {
      baseRevision: 1,
      origin: "graph",
      commands: [{ kind: "move_block", blockId: "block.export-step", x: 900, y: 120 }],
    });
    expect(result.ok).toBe(true);
    expect(result.semanticChanged).toBe(false);
    const accepted = acceptRecoveryResult(initialWorkflow, result);
    expect(accepted?.workflow.revision).toBe(1);
    expect(accepted?.layout.positions["block.export-step"]).toEqual({ x: 900, y: 120 });
  });

  it("fails a stale or invalid batch without a partial mutation", () => {
    const stale = applyRecoveryBatch(initialWorkflow, initialLayout, {
      baseRevision: 0,
      origin: "ai_proposal",
      commands: [{ kind: "set_block_title", blockId: "block.generate-geometry", title: "Changed" }],
    });
    expect(stale.ok).toBe(false);
    expect(stale.diagnostics[0]?.code).toBe("WFR-COMMAND-STALE-BASE");
    expect(initialWorkflow.blocks[1]?.title).toBe("Generate bracket geometry");

    const invalid = applyRecoveryBatch(initialWorkflow, initialLayout, {
      baseRevision: 1,
      origin: "graph",
      commands: [{ kind: "connect", relationship: { id: "rel.invalid", kind: "data", sourceId: "port.material-in", targetId: "port.step-out", label: "invalid", condition: null } }],
    });
    expect(invalid.ok).toBe(false);
    expect(initialWorkflow.relationships.some((item) => item.id === "rel.invalid")).toBe(false);
  });

  it.each([
    ["rel.duplicate-endpoints", "data", "port.brief-out", "port.brief-in", "WFR-RELATIONSHIP-DUPLICATE"],
    ["rel.invalid-feedback-source", "feedback", "block.generate-geometry", "block.capture-brief", "WFR-RELATIONSHIP-SOURCE-KIND"],
    ["rel.non-feedback-cycle", "control", "block.release-package", "block.capture-brief", "WFR-CYCLE-NON-FEEDBACK"],
  ] as const)("rejects invalid relationship topology %s", (id, kind, sourceId, targetId, code) => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, {
      baseRevision: 1,
      origin: "graph",
      commands: [{ kind: "connect", relationship: { id, kind, sourceId, targetId, label: id, condition: null } }],
    });
    expect(result.ok).toBe(false);
    expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toContain(code);
    expect(initialWorkflow.relationships).toHaveLength(9);
  });

  it("translates valid text edits into the same command protocol", () => {
    const editedSource = formatRecoveryDsl(initialWorkflow).text.replace("Generate bracket geometry", "Generate production bracket geometry");
    const edited = parseRecoveryDsl(editedSource);
    expect(edited.ok).toBe(true);
    const commands = textEditCommands(initialWorkflow, edited.workflow!);
    expect(commands).toEqual([{ kind: "set_block_title", blockId: "block.generate-geometry", title: "Generate production bracket geometry" }]);
  });

  it("previews an AI proposal against a base revision without mutating accepted state", () => {
    const proposal = aiDrawingProposal(initialWorkflow);
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, proposal);
    expect(result.ok).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Add block · Create inspection drawing (block.create-inspection-drawing) ·"))).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Add port · Inspection drawing (port.drawing-out) ·"))).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Connect · drawing (rel.drawing-to-review) ·"))).toBe(true);
    expect(initialWorkflow.blocks).toHaveLength(6);
    expect(result.workflow?.blocks).toHaveLength(8);
  });

  it("reports every fact changed by one reviewed batch", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, {
      baseRevision: 1,
      origin: "ai_proposal",
      commands: [
        { kind: "set_block_title", blockId: "block.generate-geometry", title: "Generate production geometry" },
        { kind: "set_block_configuration", blockId: "block.generate-geometry", key: "thickness_mm", value: 8 },
      ],
    });
    expect(result.ok).toBe(true);
    expect(result.diff).toEqual([
      'Configure block.generate-geometry · {"inside_radius_mm":4,"thickness_mm":6} → {"inside_radius_mm":4,"thickness_mm":8}',
      'Rename block.generate-geometry · "Generate bracket geometry" → "Generate production geometry"',
    ]);
  });
});
