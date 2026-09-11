import { describe, expect, it } from "vitest";

import type { DraftProjection } from "./draft-projection";
import {
  findBlockByIdentity,
  graphDetailLevel,
  projectComponentStates,
  resolveComponentScope,
  validateComponentProjection,
} from "./component-graph";

const projection = {
  draftId: "workflow.component-contract",
  revision: 7,
  title: "Component contract",
  purpose: "Prove collapsed reusable component identity.",
  phases: [
    {
      id: "phase.review",
      semanticId: "phase.review",
      name: "Review",
      purpose: "Review the design.",
      order: 0,
      block_ids: ["block.review-design"],
      blocks: [
        {
          id: "block.review-design",
          semanticId: "block.review-design",
          title: "Review design",
          purpose: "Apply the approved review cell.",
          role: "review",
          phase_id: "phase.review",
          input_port_ids: [],
          output_port_ids: [],
          gate_ids: [],
          intended_artifact_ids: [],
          position: { semantic_id: "block.review-design", x: 100, y: 80 },
          inputs: [],
          outputs: [],
          gates: [],
          artifacts: [],
          componentRef: {
            componentId: "component.review-cell",
            versionRange: "^1.0.0",
          },
        },
      ],
    },
  ],
  connections: [],
  feedbackPaths: [],
  components: [
    {
      semanticId: "component.review-cell",
      version: "1.0.0",
      title: "Review cell",
      inputPortIds: [],
      outputPortIds: [],
      internalDefinitionDigest: `sha256:${"a".repeat(64)}`,
      internalAddresses: [
        {
          semanticId: "component.review-cell.block.evaluate",
          conceptKind: "block",
          relativePath: "blocks/block.evaluate",
        },
        {
          semanticId: "component.review-cell.relationship.accept",
          conceptKind: "relationship",
          relativePath: "relationships/rel.accept",
        },
      ],
    },
  ],
} satisfies DraftProjection;

describe("component and large-graph projection behavior", () => {
  it("keeps a stable scoped internal identity addressable while its instance is collapsed", () => {
    expect(validateComponentProjection(projection)).toEqual([]);
    const scope = resolveComponentScope(
      projection,
      "block.review-design",
      "component.review-cell.relationship.accept",
    );
    expect(scope).toEqual({
      componentInstanceId: "block.review-design",
      componentId: "component.review-cell",
      componentVersion: "1.0.0",
      internalSemanticId: "component.review-cell.relationship.accept",
    });

    const state = projectComponentStates(
      projection,
      new Set(["block.review-design"]),
      [scope],
    )[0];
    expect(state).toMatchObject({
      instanceSemanticId: "block.review-design",
      collapsed: true,
      internalAddressCount: 2,
      targetedInternalSemanticIds: [
        "component.review-cell.relationship.accept",
      ],
    });
  });

  it("fails closed for duplicate, escaping, or out-of-scope internal addresses", () => {
    const invalid = structuredClone(projection);
    invalid.components[0]!.internalAddresses.push({
      semanticId: "component.other.block.escape",
      conceptKind: "block",
      relativePath: "blocks/../escape",
    });
    expect(validateComponentProjection(invalid)).toEqual([
      "WORKFLOW_COMPONENT_INTERNAL_ADDRESS_SCOPE_INVALID:component.other.block.escape",
      "WORKFLOW_COMPONENT_INTERNAL_ADDRESS_PATH_INVALID:blocks/../escape",
    ]);
    expect(() =>
      resolveComponentScope(
        invalid,
        "block.review-design",
        "component.other.block.escape",
      ),
    ).toThrow("WORKFLOW_COMPONENT_PROJECTION_INVALID");
  });

  it("uses deterministic detail levels and stable identity-first graph navigation", () => {
    expect(graphDetailLevel(25)).toBe("detailed");
    expect(graphDetailLevel(26)).toBe("compact");
    expect(
      findBlockByIdentity(projection, "block.review-design")?.semanticId,
    ).toBe("block.review-design");
    expect(findBlockByIdentity(projection, "review design")?.semanticId).toBe(
      "block.review-design",
    );
    expect(findBlockByIdentity(projection, "missing")).toBeNull();
  });
});
