import { describe, expect, it } from "vitest";
import { cloneWorkflow, initialWorkflow } from "./model";
import { disconnectedProcessDiagnostic } from "./run-readiness";

function graph(count: number, edges: [number, number][] = []) {
  const workflow = cloneWorkflow(initialWorkflow);
  workflow.blocks = Array.from({ length: count }, (_, i) => ({ ...workflow.blocks[0]!, id: `b${i}`, title: `Task ${i}`, inputPortIds: [`in${i}`], outputPortIds: [`out${i}`] }));
  workflow.ports = workflow.blocks.flatMap((block, i) => [
    { ...initialWorkflow.ports[0]!, id: `in${i}`, ownerBlockId: block.id, direction: "input" as const },
    { ...initialWorkflow.ports[0]!, id: `out${i}`, ownerBlockId: block.id, direction: "output" as const },
  ]);
  workflow.relationships = edges.map(([a, b], i) => ({ id: `e${i}`, kind: "data", sourceId: `out${a}`, targetId: `in${b}`, label: "Response", condition: null }));
  return workflow;
}

describe("single-process run readiness", () => {
  it.each([0, 1])("leaves %i-block drafts to existing run checks", count => {
    expect(disconnectedProcessDiagnostic(graph(count))).toBeNull();
  });
  it("identifies two independent chains and an isolated block, even in one visual group", () => {
    const issue = disconnectedProcessDiagnostic(graph(5, [[0, 1], [2, 3]]));
    expect(issue?.explanation).toContain("3 disconnected groups");
    expect(issue?.correction).toContain("Task 0” (2 blocks)");
    expect(issue?.correction).toContain("Task 2” (2 blocks)");
    expect(issue?.correction).toContain("Task 4” (1 block)");
  });
  it("allows converging inputs, multiple deliverables, and an existing reviewed process", () => {
    expect(disconnectedProcessDiagnostic(graph(5, [[0, 2], [1, 2], [2, 3], [2, 4]]))).toBeNull();
    expect(disconnectedProcessDiagnostic(initialWorkflow)).toBeNull();
  });
  it.each(["control", "decision", "feedback"] as const)("recognizes %s paths between tasks", kind => {
    const workflow = graph(2);
    workflow.relationships = [{ id: "gate", kind, sourceId: "b0", targetId: "b1", label: "Review path", condition: "pass" }];
    expect(disconnectedProcessDiagnostic(workflow)).toBeNull();
  });
});
