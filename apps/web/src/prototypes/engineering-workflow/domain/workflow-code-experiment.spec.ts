import { describe, expect, it } from "vitest";

import { diagnosticWorkflow } from "../fixtures/diagnostic-workflow";
import {
  parseWorkflowCodeDocument,
  serializeWorkflowCodeDocument,
  workflowCodeDocumentFromPreview,
} from "./workflow-code-experiment";

const requiredBlockIds = diagnosticWorkflow.blocks.map(
  ({ blockId }) => blockId,
);

describe("workflow code experiment", () => {
  it("round trips every phase, block, port, and connection in the four-block fixture", () => {
    const source = serializeWorkflowCodeDocument(diagnosticWorkflow);
    const result = parseWorkflowCodeDocument(
      source,
      diagnosticWorkflow,
      requiredBlockIds,
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(workflowCodeDocumentFromPreview(result.workflow)).toEqual(
      workflowCodeDocumentFromPreview(diagnosticWorkflow),
    );
  });

  it("applies a valid semantic edit to the diagram projection", () => {
    const document = workflowCodeDocumentFromPreview(diagnosticWorkflow);
    document.title = "Generic Four-Block Experiment";
    document.blocks[1].title = "Review Research";
    document.connections[0].label = "review material";

    const result = parseWorkflowCodeDocument(
      JSON.stringify(document),
      diagnosticWorkflow,
      requiredBlockIds,
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.workflow.title).toBe("Generic Four-Block Experiment");
    expect(result.workflow.blocks[1]).toMatchObject({
      blockId: "diagnostic-ai-task",
      title: "Review Research",
    });
    expect(result.workflow.connections[0].label).toBe("review material");
  });

  it("returns structured syntax and referential errors without a partial workflow", () => {
    expect(
      parseWorkflowCodeDocument("{", diagnosticWorkflow, requiredBlockIds),
    ).toMatchObject({
      ok: false,
      errors: [{ path: "$", code: "JSON_SYNTAX" }],
    });

    const document = workflowCodeDocumentFromPreview(diagnosticWorkflow);
    document.connections[0].source.blockId = "missing-block";
    const result = parseWorkflowCodeDocument(
      JSON.stringify(document),
      diagnosticWorkflow,
      requiredBlockIds,
    );
    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.errors).toContainEqual(
      expect.objectContaining({
        path: "connections.0.source.blockId",
        code: "UNKNOWN_BLOCK",
      }),
    );
  });

  it("keeps fixture identities explicit while the diagnostic runner depends on them", () => {
    const document = workflowCodeDocumentFromPreview(diagnosticWorkflow);
    document.blocks = document.blocks.filter(
      ({ blockId }) => blockId !== "diagnostic-mcp-action",
    );
    document.connections = document.connections.filter(
      ({ source, target }) =>
        source.blockId !== "diagnostic-mcp-action" &&
        target.blockId !== "diagnostic-mcp-action",
    );

    const result = parseWorkflowCodeDocument(
      JSON.stringify(document),
      diagnosticWorkflow,
      requiredBlockIds,
    );
    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.errors).toContainEqual({
      path: "blocks",
      code: "REQUIRED_FIXTURE_BLOCK",
      message:
        "This four-block experiment requires stable block identity diagnostic-mcp-action.",
    });
  });
});
