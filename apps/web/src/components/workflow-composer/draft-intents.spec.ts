import { describe, expect, it } from "vitest";

import fixture from "../../../../../packages/core/tests/fixtures/workflow_drafts/representative-workflow.json";
import {
  decodeWorkflowDraft,
  verifyWorkflowDraftIdentity,
  type WorkflowDraft,
} from "../../services/workflow-drafts";
import {
  createDraftIntentState,
  reduceDraftCanvasIntent,
  type DraftIntentState,
} from "./draft-intents";

function state(
  draft: WorkflowDraft = decodeWorkflowDraft(fixture),
): DraftIntentState {
  return createDraftIntentState(draft);
}

function snapshot(value: unknown): string {
  return JSON.stringify(value);
}

describe("reduceDraftCanvasIntent", () => {
  it("selects known identities without changing canonical draft bytes", async () => {
    const source = state();
    const before = snapshot(source.lastValidDraft);

    const selected = await reduceDraftCanvasIntent(source, {
      type: "select",
      semanticId: "block.define-product",
    });
    const cleared = await reduceDraftCanvasIntent(selected, {
      type: "select",
      semanticId: null,
    });

    expect(selected.selectedSemanticId).toBe("block.define-product");
    expect(selected.lastValidDraft).toBe(source.lastValidDraft);
    expect(cleared.selectedSemanticId).toBeNull();
    expect(snapshot(source.lastValidDraft)).toBe(before);
  });

  it("creates a host-identified block atomically and preserves revision authority", async () => {
    const source = state();
    const before = snapshot(source.lastValidDraft);

    const result = await reduceDraftCanvasIntent(source, {
      type: "create-block",
      phaseId: "phase.release",
      role: "work",
      x: 1240,
      y: 80,
    });

    expect(snapshot(source.lastValidDraft)).toBe(before);
    expect(result.lastValidDraft).not.toBe(source.lastValidDraft);
    expect(result.lastValidDraft.revision).toBe(source.lastValidDraft.revision);
    const added = result.lastValidDraft.semantic.blocks.at(-1);
    expect(added?.id).toMatch(/^block\.draft-[0-9]+$/);
    expect(
      result.lastValidDraft.semantic.phases.find(
        (phase) => phase.id === "phase.release",
      )?.block_ids,
    ).toContain(added?.id);
    expect(result.lastValidDraft.layout.positions).toContainEqual({
      semantic_id: added?.id,
      x: 1240,
      y: 80,
    });
    expect(result.diagnostics).toEqual([]);
    await verifyWorkflowDraftIdentity(result.lastValidDraft);
  });

  it("moves and edits only the selected block while retaining unrelated identities", async () => {
    const source = state();
    const moved = await reduceDraftCanvasIntent(source, {
      type: "move-block",
      semanticId: "block.review-product-definition",
      x: 720,
      y: 96,
    });
    const edited = await reduceDraftCanvasIntent(moved, {
      type: "edit-block",
      semanticId: "block.review-product-definition",
      title: "Review the product definition",
      purpose: "Check completeness and record bounded corrections.",
    });

    expect(moved.lastValidDraft.semantic_sha256).toBe(
      source.lastValidDraft.semantic_sha256,
    );
    expect(moved.lastValidDraft.layout_sha256).not.toBe(
      source.lastValidDraft.layout_sha256,
    );
    expect(edited.lastValidDraft.layout_sha256).toBe(
      moved.lastValidDraft.layout_sha256,
    );
    expect(
      edited.lastValidDraft.semantic.blocks.map((block) => block.id),
    ).toEqual(source.lastValidDraft.semantic.blocks.map((block) => block.id));
    expect(
      edited.lastValidDraft.semantic.blocks.find(
        (block) => block.id === "block.review-product-definition",
      )?.title,
    ).toBe("Review the product definition");
    await verifyWorkflowDraftIdentity(edited.lastValidDraft);
  });

  it("creates and deletes one compatible connection without mutating ports", async () => {
    const source = state();
    const without = await reduceDraftCanvasIntent(source, {
      type: "delete-connection",
      semanticId: "connection.definition-to-review",
    });
    const restored = await reduceDraftCanvasIntent(without, {
      type: "create-connection",
      sourcePortId: "port.product-definition-out",
      targetPortId: "port.product-definition-in",
    });

    expect(without.lastValidDraft.semantic.connections).toHaveLength(2);
    expect(restored.lastValidDraft.semantic.connections).toHaveLength(3);
    expect(restored.lastValidDraft.semantic.connections.at(-1)?.id).toMatch(
      /^connection\.draft-[0-9]+$/,
    );
    expect(restored.lastValidDraft.semantic.ports).toEqual(
      source.lastValidDraft.semantic.ports,
    );
    expect(restored.diagnostics).toEqual([]);
  });

  it("contains an invalid connection and preserves the exact last-valid reference", async () => {
    const source = state();
    const before = snapshot(source.lastValidDraft);

    const rejected = await reduceDraftCanvasIntent(source, {
      type: "create-connection",
      sourcePortId: "port.product-definition-out",
      targetPortId: "port.accepted-definition-out",
    });

    expect(rejected.lastValidDraft).toBe(source.lastValidDraft);
    expect(snapshot(rejected.lastValidDraft)).toBe(before);
    expect(rejected.diagnostics).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: "CONNECTION_TARGET_INVALID",
          affected_semantic_ids: expect.arrayContaining([
            "port.product-definition-out",
            "port.accepted-definition-out",
          ]),
        }),
      ]),
    );
  });

  it("creates and edits gate, feedback, and intended artifact relationships atomically", async () => {
    const source = state();
    const gateDeleted = await reduceDraftCanvasIntent(source, {
      type: "delete-concept",
      semanticId: "gate.definition-accepted",
    });
    const gateCreated = await reduceDraftCanvasIntent(gateDeleted, {
      type: "create-gate",
      ownerBlockId: "block.review-product-definition",
      condition: "The definition meets the review criteria.",
      proceedTargetBlockId: "block.release-product-definition",
      reviseTargetBlockId: "block.define-product",
    });
    const gate = gateCreated.lastValidDraft.semantic.gates.at(-1);
    const feedback = gateCreated.lastValidDraft.semantic.feedback_paths.find(
      (item) => item.id === gate?.feedback_path_id,
    );
    expect(gate?.id).toMatch(/^gate\.draft-[0-9]+$/);
    expect(feedback?.from_gate_id).toBe(gate?.id);
    expect(feedback?.to_block_id).toBe(gate?.revise_target_block_id);

    const feedbackEdited = await reduceDraftCanvasIntent(gateCreated, {
      type: "edit-feedback",
      semanticId: feedback?.id ?? "missing",
      toBlockId: "block.capture-requirements",
      reason: "Capture the missing requirements before another review.",
    });
    expect(
      feedbackEdited.lastValidDraft.semantic.gates.at(-1)
        ?.revise_target_block_id,
    ).toBe("block.capture-requirements");

    const artifactCreated = await reduceDraftCanvasIntent(feedbackEdited, {
      type: "create-intended-artifact",
      ownerBlockId: "block.review-product-definition",
      title: "Correction record",
      artifactTypeId: "type.correction-record",
      description: "The intended correction record; no artifact is executed.",
    });
    const artifact =
      artifactCreated.lastValidDraft.semantic.intended_artifacts.at(-1);
    expect(artifact?.id).toMatch(/^artifact\.draft-[0-9]+$/);
    expect(
      artifactCreated.lastValidDraft.semantic.blocks.find(
        (block) => block.id === "block.review-product-definition",
      )?.intended_artifact_ids,
    ).toContain(artifact?.id);
    expect(artifactCreated.diagnostics).toEqual([]);
  });

  it("rejects dangling block deletion and recovers with a corrected intent", async () => {
    const source = state();
    const moved = await reduceDraftCanvasIntent(source, {
      type: "move-block",
      semanticId: "block.review-product-definition",
      x: 700,
      y: 100,
    });
    const rejected = await reduceDraftCanvasIntent(moved, {
      type: "delete-concept",
      semanticId: "block.define-product",
    });
    expect(rejected.lastValidDraft).toBe(moved.lastValidDraft);
    expect(rejected.diagnostics[0]).toEqual(
      expect.objectContaining({
        code: "DELETE_CONCEPT_DEPENDENCY",
        affected_semantic_ids: expect.arrayContaining(["block.define-product"]),
      }),
    );

    const corrected = await reduceDraftCanvasIntent(rejected, {
      type: "move-block",
      semanticId: "block.define-product",
      x: 360,
      y: 40,
    });
    expect(corrected.diagnostics).toEqual([]);
    expect(
      corrected.lastValidDraft.layout.positions.find(
        (position) =>
          position.semantic_id === "block.review-product-definition",
      ),
    ).toEqual(expect.objectContaining({ x: 700, y: 100 }));
    await verifyWorkflowDraftIdentity(corrected.lastValidDraft);
  });
});
