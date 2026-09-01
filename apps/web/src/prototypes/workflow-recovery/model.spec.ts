import { describe, expect, it } from "vitest";

import { canonicalDefinitionBytes } from "./canonical-wire";
import { aiDrawingProposal, applyRecoveryBatch } from "./command-system";
import { cloneLayout, cloneWorkflow, initialLayout, initialWorkflow, toDraftProjection } from "./model";

describe("recovery renderer projection", () => {
  it("matches the strict Python kernel's canonical digest bytes", async () => {
    const bytes = new TextEncoder().encode(canonicalDefinitionBytes(initialWorkflow));
    const buffer = await crypto.subtle.digest("SHA-256", bytes);
    const digest = [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");

    expect(digest).toBe("e22d6a0c1f991e03107cfe53dc0c3fb3c4ccb0083ded6c1e114270c5a7a180d0");
  });

  it("derives approval gates and feedback paths from canonical relationships", () => {
    const projection = toDraftProjection(initialWorkflow, initialLayout);
    const review = projection.phases.flatMap((phase) => phase.blocks).find((block) => block.semanticId === "block.review-design");

    expect(review?.gates).toEqual([expect.objectContaining({
      id: "gate.review-decision",
      semanticId: "gate.review-decision",
      proceed_target_block_id: "block.export-step",
      revise_target_block_id: "block.generate-geometry",
      feedback_path_id: "rel.review-revise",
    })]);
    expect(projection.feedbackPaths).toEqual([expect.objectContaining({
      id: "rel.review-revise",
      from_gate_id: "gate.review-decision",
      to_block_id: "block.generate-geometry",
      label: "Revise geometry",
    })]);
  });

  it("does not invent a gate for an approval block without decision and feedback relationships", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, aiDrawingProposal(initialWorkflow));
    expect(result.ok).toBe(true);
    const projection = toDraftProjection(result.workflow!, result.layout!);
    const drawingReview = projection.phases.flatMap((phase) => phase.blocks).find((block) => block.semanticId === "block.review-inspection-drawing");

    expect(drawingReview?.gates).toEqual([]);
    expect(projection.feedbackPaths).toHaveLength(1);
  });

  it("projects every valid feedback outcome from one approval without collapsing identities", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    workflow.relationships.push({
      id: "rel.review-restart",
      kind: "feedback",
      sourceId: "block.review-design",
      targetId: "block.capture-brief",
      label: "Restart from brief",
      condition: "The design brief itself is incomplete",
    });

    const projection = toDraftProjection(workflow, initialLayout);
    expect(projection.feedbackPaths.map((feedback) => feedback.semanticId)).toEqual([
      "rel.review-revise",
      "rel.review-restart",
    ]);
    expect(projection.feedbackPaths[1]).toEqual(expect.objectContaining({
      from_gate_id: "gate.review-decision",
      to_block_id: "block.capture-brief",
      label: "Restart from brief",
    }));
  });

  it("projects decision-origin feedback directly when no approval gate adapter exists", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const layout = cloneLayout(initialLayout);
    workflow.blocks.push({
      id: "block.route-rework",
      kind: "decision",
      title: "Route rework",
      purpose: "Choose whether the brief needs revision.",
      phaseId: "phase.verify",
      executionKind: "human",
      instructions: "Return incomplete requirements to the brief.",
      configuration: {},
      inputPortIds: [],
      outputPortIds: [],
      bindingId: null,
      componentRef: null,
    });
    workflow.phases.find((phase) => phase.id === "phase.verify")!.blockIds.push("block.route-rework");
    workflow.relationships.push({
      id: "rel.route-rework-to-brief",
      kind: "feedback",
      sourceId: "block.route-rework",
      targetId: "block.capture-brief",
      label: "Revise brief",
      condition: "Requirements are incomplete",
    });
    layout.positions["block.route-rework"] = { x: 900, y: 640 };

    const projection = toDraftProjection(workflow, layout);
    expect(projection.feedbackPaths).toContainEqual(expect.objectContaining({
      id: "rel.route-rework-to-brief",
      from_gate_id: "block.route-rework",
      to_block_id: "block.capture-brief",
      semanticId: "rel.route-rework-to-brief",
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
      componentRef: { componentId: "component.fixture", versionRange: "^1.0.0" },
    });
    layout.positions["block.reusable-fixture"] = { x: 50, y: 50 };

    const projection = toDraftProjection(workflow, layout);
    const components = projection.phases.find((phase) => phase.id === "phase.unassigned-component");
    expect(components?.blocks.map((block) => block.semanticId)).toEqual(["block.reusable-fixture"]);
  });
});
