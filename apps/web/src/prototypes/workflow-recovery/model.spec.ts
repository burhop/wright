import { describe, expect, it } from "vitest";

import type { DraftCanvasIntent } from "../../components/workflow-composer/draft-intents";
import type { DraftCanvasRenderer } from "../../components/workflow-composer/renderer-types";
import { canonicalDefinitionBytes } from "./canonical-wire";
import { aiDrawingProposal, applyRecoveryBatch } from "./command-system";
import { cloneLayout, cloneWorkflow, initialLayout, initialRunProjection, initialWorkflow, resolveRecoveryComponentScope, toDraftProjection, validateRecoveryRunProjection } from "./model";

describe("recovery renderer projection", () => {
  it("matches the strict Python kernel's canonical digest bytes", async () => {
    const bytes = new TextEncoder().encode(canonicalDefinitionBytes(initialWorkflow));
    const buffer = await crypto.subtle.digest("SHA-256", bytes);
    const digest = [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");

    expect(digest).toBe("04cc79dad3b8177e52ab46d0c994d5d48b39f63d7483ccf504eb8d665b902b2d");
  });

  it("derives approval gates and feedback paths from canonical relationships", () => {
    const projection = toDraftProjection(initialWorkflow, initialLayout);
    const specification = projection.phases.flatMap((phase) => phase.blocks).find((block) => block.semanticId === "block.create-design-specification");
    const review = projection.phases.flatMap((phase) => phase.blocks).find((block) => block.semanticId === "block.review-design");

    expect(specification?.gates).toEqual([expect.objectContaining({
      id: "gate.create-design-specification-decision",
      semanticId: "gate.create-design-specification-decision",
      proceed_target_block_id: "block.generate-geometry",
      revise_target_block_id: "block.design-intent",
      feedback_path_id: "rel.specification-revise",
    })]);
    expect(review?.gates).toEqual([expect.objectContaining({
      id: "gate.review-decision",
      semanticId: "gate.review-decision",
      proceed_target_block_id: "block.export-step",
      revise_target_block_id: "block.generate-geometry",
      feedback_path_id: "rel.review-revise",
    })]);
    expect(projection.feedbackPaths).toEqual([
      expect.objectContaining({
        id: "rel.specification-revise",
        from_gate_id: "gate.create-design-specification-decision",
        to_block_id: "block.design-intent",
        label: "Revise design inputs",
      }),
      expect.objectContaining({
        id: "rel.review-revise",
        from_gate_id: "gate.review-decision",
        to_block_id: "block.generate-geometry",
        label: "Revise CAD model",
      }),
    ]);
  });

  it("resolves the golden review component to one stable diagnostic and run lineage scope", () => {
    const instance = initialWorkflow.blocks.find((block) => block.id === "block.review-design");
    expect(instance).toEqual(expect.objectContaining({
      kind: "component",
      componentRef: { componentId: "component.review-cell", versionRange: "^1.0.0" },
    }));
    const scope = resolveRecoveryComponentScope(
      initialWorkflow,
      "block.review-design",
      "component.review-cell.block.evaluate",
    );
    expect(scope).toEqual({
      componentInstanceId: "block.review-design",
      componentId: "component.review-cell",
      componentVersion: "1.0.0",
      internalSemanticId: "component.review-cell.block.evaluate",
    });
    expect({ code: "WFR-REVIEW-INPUT", componentScope: scope }.componentScope).toBe(scope);
    expect({ state: "queued", componentScope: scope }.componentScope).toBe(scope);
  });

  it("does not invent a gate for an approval block without decision and feedback relationships", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, aiDrawingProposal(initialWorkflow));
    expect(result.ok).toBe(true);
    const projection = toDraftProjection(result.workflow!, result.layout!);
    const drawingReview = projection.phases.flatMap((phase) => phase.blocks).find((block) => block.semanticId === "block.review-inspection-drawing");

    expect(drawingReview?.gates).toEqual([]);
    expect(projection.feedbackPaths).toHaveLength(2);
  });

  it("projects every valid feedback outcome from one approval without collapsing identities", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    workflow.relationships.push({
      id: "rel.review-restart",
      kind: "feedback",
      sourceId: "block.review-design",
      targetId: "block.design-intent",
      label: "Restart from design intent",
      condition: "The design intent itself is incomplete",
    });

    const projection = toDraftProjection(workflow, initialLayout);
    expect(projection.feedbackPaths.map((feedback) => feedback.semanticId)).toEqual([
      "rel.specification-revise",
      "rel.review-revise",
      "rel.review-restart",
    ]);
    expect(projection.feedbackPaths[2]).toEqual(expect.objectContaining({
      from_gate_id: "gate.review-decision",
      to_block_id: "block.design-intent",
      label: "Restart from design intent",
    }));
  });

  it("projects decision-origin feedback directly when no approval gate adapter exists", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const layout = cloneLayout(initialLayout);
    workflow.blocks.push({
      id: "block.route-rework",
      kind: "decision",
      title: "Route rework",
      purpose: "Choose whether the design intent needs revision.",
      phaseId: "phase.verify",
      executionKind: "human",
      instructions: "Return incomplete requirements to the design intent.",
      configuration: {},
      inputPortIds: [],
      outputPortIds: [],
      bindingId: null,
      componentRef: null,
    });
    workflow.phases.find((phase) => phase.id === "phase.verify")!.blockIds.push("block.route-rework");
    workflow.relationships.push({
      id: "rel.route-rework-to-design-intent",
      kind: "feedback",
      sourceId: "block.route-rework",
      targetId: "block.design-intent",
      label: "Revise design intent",
      condition: "Requirements are incomplete",
    });
    layout.positions["block.route-rework"] = { x: 900, y: 640 };

    const projection = toDraftProjection(workflow, layout);
    expect(projection.feedbackPaths).toContainEqual(expect.objectContaining({
      id: "rel.route-rework-to-design-intent",
      from_gate_id: "block.route-rework",
      to_block_id: "block.design-intent",
      semanticId: "rel.route-rework-to-design-intent",
    }));
  });

  it("keeps canonical unphased component blocks visible through an explicit projection-only group", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const layout = cloneLayout(initialLayout);
    workflow.blocks.push({
      ...structuredClone(workflow.blocks[0]!),
      id: "block.reusable-fixture",
      kind: "component",
      title: "Reusable fixture",
      phaseId: null,
      inputPortIds: [],
      outputPortIds: [],
      bindingId: null,
      componentRef: { componentId: "component.review-cell", versionRange: "^1.0.0" },
    });
    layout.positions["block.reusable-fixture"] = { x: 50, y: 50 };

    const projection = toDraftProjection(workflow, layout);
    const components = projection.phases.find((phase) => phase.id === "phase.unassigned-component");
    expect(components?.blocks.map((block) => block.semanticId)).toEqual(["block.reusable-fixture"]);
    const internalAddress = workflow.components[0]!.internalAddresses.find((address) => address.conceptKind === "relationship")!;
    const scopedAddress = resolveRecoveryComponentScope(workflow, "block.reusable-fixture", internalAddress.semanticId);
    expect(scopedAddress?.internalSemanticId).toBe(internalAddress.semanticId);
    expect(internalAddress.relativePath).toBe("relationships/rel.accept");
  });

  it("replaces renderer implementations without changing projection facts or emitted host intents", () => {
    const projection = toDraftProjection(initialWorkflow, initialLayout);
    const before = canonicalDefinitionBytes(initialWorkflow);
    const observed: string[][] = [];
    const emitted: DraftCanvasIntent[][] = [];
    const fake = (index: number): DraftCanvasRenderer => ({ projection: value, onIntent }) => {
      observed[index] = value.phases.flatMap((phase) => phase.blocks.map((block) => block.semanticId));
      const intent: DraftCanvasIntent = { type: "select", semanticId: "block.generate-geometry" };
      emitted[index] = [intent];
      onIntent(intent);
      return null;
    };
    const hostIntents: DraftCanvasIntent[][] = [[], []];
    fake(0)({ projection, selectedSemanticId: null, onIntent: (intent) => hostIntents[0]!.push(intent) });
    fake(1)({ projection, selectedSemanticId: null, onIntent: (intent) => hostIntents[1]!.push(intent) });
    expect(observed[0]).toEqual(observed[1]);
    expect(emitted[0]).toEqual(emitted[1]);
    expect(hostIntents[0]).toEqual(hostIntents[1]);
    expect(canonicalDefinitionBytes(initialWorkflow)).toBe(before);
  });

  it("rejects an unknown run version without changing the immutable record", () => {
    const run = initialRunProjection(initialWorkflow, "a".repeat(64), "2026-08-31T00:00:00Z");
    const unknown = { ...run, schemaVersion: "99.0.0" } as unknown as typeof run;
    const before = structuredClone(unknown);
    expect(validateRecoveryRunProjection(unknown)[0]?.code).toBe("WFR-RUN-VERSION-UNSUPPORTED");
    expect(unknown).toEqual(before);
  });
});
