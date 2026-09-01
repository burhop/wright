import { describe, expect, it } from "vitest";

import { acceptRecoveryResult, aiDrawingProposal, applyRecoveryBatch, recoveryCommandBatch, textEditCommands, type RecoveryCommandBatch } from "./command-system";
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
    expect(Object.keys(parsed.sourceMap)).toHaveLength(66);
    expect(parsed.sourceMap["block.check-manufacturability"]).toBeDefined();
  });

  it("applies a semantic batch atomically and advances one revision", () => {
    const result = applyRecoveryBatch(cloneWorkflow(initialWorkflow), cloneLayout(initialLayout), recoveryCommandBatch(initialWorkflow.revision, "form", [
      { kind: "set_block_configuration", blockId: "block.generate-geometry", key: "thickness_mm", value: 8 },
    ]));
    expect(result.ok).toBe(true);
    expect(result.semanticChanged).toBe(true);
    const accepted = acceptRecoveryResult(initialWorkflow, initialLayout, result);
    expect(accepted?.workflow.revision).toBe(3);
    expect(accepted?.workflow.parentRevision).toBe(2);
    expect(accepted?.workflow.blocks.find((block) => block.id === "block.generate-geometry")?.configuration.thickness_mm).toBe(8);
  });

  it("keeps layout moves outside the semantic revision", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "graph", [
      { kind: "move_block", blockId: "block.export-step", x: 900, y: 120 },
    ]));
    expect(result.ok).toBe(true);
    expect(result.semanticChanged).toBe(false);
    const accepted = acceptRecoveryResult(initialWorkflow, initialLayout, result);
    expect(accepted?.workflow.revision).toBe(2);
    expect(accepted?.layout.positions["block.export-step"]).toEqual({ x: 900, y: 120 });
  });

  it("rejects mixed semantic and layout batches atomically", () => {
    const beforeWorkflow = structuredClone(initialWorkflow);
    const beforeLayout = structuredClone(initialLayout);
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "graph", [
      { kind: "move_block", blockId: "block.export-step", x: 900, y: 120 },
      { kind: "set_block_title", blockId: "block.export-step", title: "Export reviewed STEP" },
    ]));
    expect(result.ok).toBe(false);
    expect(result.diagnostics[0]?.code).toBe("WFR-COMMAND-MIXED-CONTAINMENT");
    expect(initialWorkflow).toEqual(beforeWorkflow);
    expect(initialLayout).toEqual(beforeLayout);
  });

  it("fails a stale or invalid batch without a partial mutation", () => {
    const stale = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision - 1, "ai_proposal", [
      { kind: "set_block_title", blockId: "block.generate-geometry", title: "Changed" },
    ]));
    expect(stale.ok).toBe(false);
    expect(stale.diagnostics[0]?.code).toBe("WFR-COMMAND-STALE-BASE");
    expect(initialWorkflow.blocks.find((block) => block.id === "block.generate-geometry")?.title).toBe("Create bracket CAD model");

    const invalid = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "graph", [
      { kind: "connect", relationship: { id: "rel.invalid", kind: "data", sourceId: "port.design-specification-check-in", targetId: "port.step-out", label: "invalid", condition: null } },
    ]));
    expect(invalid.ok).toBe(false);
    expect(initialWorkflow.relationships.some((item) => item.id === "rel.invalid")).toBe(false);
  });

  it.each([
    ["rel.duplicate-endpoints", "data", "port.design-intent-out", "port.design-intent-in", "WFR-RELATIONSHIP-DUPLICATE"],
    ["rel.invalid-feedback-source", "feedback", "block.generate-geometry", "block.design-intent", "WFR-RELATIONSHIP-SOURCE-KIND"],
    ["rel.non-feedback-cycle", "control", "block.release-package", "block.design-intent", "WFR-CYCLE-NON-FEEDBACK"],
  ] as const)("rejects invalid relationship topology %s", (id, kind, sourceId, targetId, code) => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "graph", [
      { kind: "connect", relationship: { id, kind, sourceId, targetId, label: id, condition: null } },
    ]));
    expect(result.ok).toBe(false);
    expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toContain(code);
    expect(initialWorkflow.relationships).toHaveLength(16);
  });

  it("translates valid text edits into the same command protocol", () => {
    const editedSource = formatRecoveryDsl(initialWorkflow).text.replace("Create bracket CAD model", "Create production bracket CAD model");
    const edited = parseRecoveryDsl(editedSource);
    expect(edited.ok).toBe(true);
    const commands = textEditCommands(initialWorkflow, edited.workflow!);
    expect(commands).toEqual([{ kind: "set_block_title", blockId: "block.generate-geometry", title: "Create production bracket CAD model" }]);
  });

  it("previews an AI proposal against a base revision without mutating accepted state", () => {
    const proposal = aiDrawingProposal(initialWorkflow);
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, proposal);
    expect(result.ok).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Add block · Create manufacturing drawing (block.create-inspection-drawing) ·"))).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Add port · Manufacturing drawing (port.drawing-out) ·"))).toBe(true);
    expect(result.diff.some((line) => line.startsWith("Connect · manufacturing drawing (rel.drawing-to-review) ·"))).toBe(true);
    expect(initialWorkflow.blocks).toHaveLength(9);
    expect(result.workflow?.blocks).toHaveLength(11);
  });

  it("reports every fact changed by one reviewed batch", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "ai_proposal", [
        { kind: "set_block_title", blockId: "block.generate-geometry", title: "Generate production geometry" },
        { kind: "set_block_configuration", blockId: "block.generate-geometry", key: "thickness_mm", value: 8 },
    ]));
    expect(result.ok).toBe(true);
    expect(result.diff).toEqual([
      'Configure block.generate-geometry · {"inside_radius_mm":4,"thickness_mm":6} → {"inside_radius_mm":4,"thickness_mm":8}',
      'Rename block.generate-geometry · "Create bracket CAD model" → "Generate production geometry"',
    ]);
  });

  it("rejects unknown command and layout versions without rewriting either input", () => {
    const command = recoveryCommandBatch(initialWorkflow.revision, "form", [{ kind: "set_block_title", blockId: "block.generate-geometry", title: "Changed" }]);
    const unknownCommand = { ...command, schemaVersion: "99.0.0" } as unknown as RecoveryCommandBatch;
    const commandBefore = structuredClone(unknownCommand);
    const commandResult = applyRecoveryBatch(initialWorkflow, initialLayout, unknownCommand);
    expect(commandResult.ok).toBe(false);
    expect(commandResult.diagnostics[0]?.code).toBe("WFR-COMMAND-VERSION-UNSUPPORTED");
    expect(unknownCommand).toEqual(commandBefore);

    const unknownLayout = { ...cloneLayout(initialLayout), schemaVersion: "99.0.0" } as unknown as typeof initialLayout;
    const layoutBefore = structuredClone(unknownLayout);
    const layoutResult = applyRecoveryBatch(initialWorkflow, unknownLayout, command);
    expect(layoutResult.ok).toBe(false);
    expect(layoutResult.diagnostics[0]?.code).toBe("WFR-LAYOUT-VERSION-UNSUPPORTED");
    expect(unknownLayout).toEqual(layoutBefore);
  });

  it("routes undo and redo snapshots through one atomic validated history batch", () => {
    const changedResult = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "form", [
      { kind: "set_block_title", blockId: "block.generate-geometry", title: "Changed geometry" },
    ]));
    const changed = acceptRecoveryResult(initialWorkflow, initialLayout, changedResult)!;
    const historyResult = applyRecoveryBatch(changed.workflow, changed.layout, recoveryCommandBatch(changed.workflow.revision, "history", [{
      kind: "restore_snapshot",
      direction: "undo",
      workflow: cloneWorkflow(initialWorkflow),
      layout: cloneLayout(initialLayout),
    }]));
    const restored = acceptRecoveryResult(changed.workflow, changed.layout, historyResult)!;
    expect(restored.workflow.revision).toBe(4);
    expect(restored.workflow.parentRevision).toBe(3);
    expect(restored.workflow.blocks.find((block) => block.id === "block.generate-geometry")?.title).toBe("Create bracket CAD model");

    const invalidWorkflow = cloneWorkflow(initialWorkflow);
    invalidWorkflow.blocks[0]!.outputPortIds.push("port.missing");
    const invalid = applyRecoveryBatch(changed.workflow, changed.layout, recoveryCommandBatch(changed.workflow.revision, "history", [{
      kind: "restore_snapshot",
      direction: "undo",
      workflow: invalidWorkflow,
      layout: cloneLayout(initialLayout),
    }]));
    expect(invalid.ok).toBe(false);
    expect(changed.workflow.blocks.find((block) => block.id === "block.generate-geometry")?.title).toBe("Changed geometry");
  });

  it("does not regress semantic identity when history restores layout only", () => {
    const currentWorkflow = cloneWorkflow(initialWorkflow);
    currentWorkflow.revision = 11;
    currentWorkflow.parentRevision = 10;
    currentWorkflow.semanticSha256 = "a".repeat(64);
    const currentLayout = cloneLayout(initialLayout);
    currentLayout.semanticRevision = 11;
    currentLayout.layoutRevision = 7;
    currentLayout.positions["block.generate-geometry"] = { x: 999, y: 444 };

    const snapshotWorkflow = cloneWorkflow(initialWorkflow);
    snapshotWorkflow.revision = 7;
    snapshotWorkflow.parentRevision = 6;
    snapshotWorkflow.semanticSha256 = null;
    const snapshotLayout = cloneLayout(initialLayout);
    snapshotLayout.semanticRevision = 7;
    snapshotLayout.layoutRevision = 3;

    const result = applyRecoveryBatch(currentWorkflow, currentLayout, recoveryCommandBatch(11, "history", [{
      kind: "restore_snapshot",
      direction: "undo",
      workflow: snapshotWorkflow,
      layout: snapshotLayout,
    }]));
    expect(result.ok).toBe(true);
    expect(result.semanticChanged).toBe(false);

    const restored = acceptRecoveryResult(currentWorkflow, currentLayout, result)!;
    expect(restored.workflow.revision).toBe(11);
    expect(restored.workflow.parentRevision).toBe(10);
    expect(restored.workflow.semanticSha256).toBe("a".repeat(64));
    expect(restored.layout.semanticRevision).toBe(11);
    expect(restored.layout.layoutRevision).toBe(8);
    expect(restored.layout.positions["block.generate-geometry"]).toEqual(initialLayout.positions["block.generate-geometry"]);
  });

  it("keeps a local semantic edit and paired projection comfortably inside the one-second bound", () => {
    const durations: number[] = [];
    for (let index = 0; index < 25; index += 1) {
      const started = performance.now();
      const result = applyRecoveryBatch(initialWorkflow, initialLayout, recoveryCommandBatch(initialWorkflow.revision, "form", [
        { kind: "set_block_title", blockId: "block.generate-geometry", title: `Geometry treatment ${index}` },
      ]));
      expect(result.ok).toBe(true);
      durations.push(performance.now() - started);
    }
    expect(Math.max(...durations)).toBeLessThan(1000);
  });
});
