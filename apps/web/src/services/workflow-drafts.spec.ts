import { describe, expect, it } from "vitest";

import fixture from "../../../../packages/core/tests/fixtures/workflow_drafts/representative-workflow.json";

import {
  decodeWorkflowDraft,
  verifyWorkflowDraftIdentity,
} from "./workflow-drafts";

describe("workflow draft browser boundary", () => {
  it("strictly decodes the bounded representative contract", () => {
    const draft = decodeWorkflowDraft(fixture);
    expect(draft.draft_id).toBe("draft.representative-product-definition");
    expect(() => decodeWorkflowDraft({ ...fixture, execute: true })).toThrow();
    expect(() => decodeWorkflowDraft({
      ...fixture,
      semantic: { ...fixture.semantic, blocks: Array(101).fill(fixture.semantic.blocks[0]) },
    })).toThrow();
  });

  it("verifies semantic and layout identities independently", async () => {
    const draft = decodeWorkflowDraft(fixture);
    await expect(verifyWorkflowDraftIdentity(draft)).resolves.toBeUndefined();

    const changed = decodeWorkflowDraft({
      ...fixture,
      semantic: { ...fixture.semantic, title: "Changed without a digest" },
    });
    await expect(verifyWorkflowDraftIdentity(changed)).rejects.toThrow(
      "WORKFLOW_DRAFT_SEMANTIC_IDENTITY_MISMATCH",
    );
  });
});
