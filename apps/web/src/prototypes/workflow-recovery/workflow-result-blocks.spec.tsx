import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceEngineeringResult, WorkflowApprovalCheckpoint } from "../../services/workspace-service";
import { cloneWorkflow, initialWorkflow, RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY } from "./model";
import { resultAvailability, safeResultPath, workflowResultBlocks } from "./workflow-result-blocks";
import { WorkflowResultInspector, WorkflowResultsNavigator } from "./WorkflowResultInspector";

afterEach(cleanup);
const digest = "a".repeat(64);
function setup() {
  const workflow = cloneWorkflow(initialWorkflow);
  workflow.blocks.forEach((block) => { block.configuration = {}; });
  workflow.blocks.find((block) => block.id === "block.generate-geometry")!.configuration = {
    save_output: true, output_filename: "run/report.md",
    expected_files: "run/plot.svg\nrun/metrics.csv\n../unsafe.md",
    [RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY]: JSON.stringify({ expected_file_ports: { drawing: "run/model.step" } }),
  };
  const result: WorkspaceEngineeringResult = {
    schema_version: 1, id: "result", kind: "image", name: "A plot", exports: [],
    representations: [{kind: "workspace_file", location: "run/plot.svg", format: "svg",
      provider_id: "workspace", resource_id: "run/plot.svg", revision: null, durability: "persistent", sha256: digest, size_bytes: 100}],
    provenance: {run_id: "run", task_id: "generate_geometry", output_port: "plot", input_revisions: []},
  };
  return { workflow, result };
}

describe("read-only workflow result blocks", () => {
  it("groups declared and actual files by their exact producer, without changing the workflow", () => {
    const {workflow, result} = setup();
    const before = JSON.stringify(workflow);
    const blocks = workflowResultBlocks({ workflow, results: [result, result] });
    expect(blocks).toHaveLength(1);
    expect(blocks[0].producerId).toBe("block.generate-geometry");
    expect(blocks[0].title).toBe("Plots and supporting data");
    expect(blocks[0].files).toHaveLength(4);
    expect(blocks[0].files.filter((file) => file.available)).toHaveLength(1);
    expect(resultAvailability(blocks[0])).toBe("1 of 4 files available");
    expect(blocks[0].reviewLabel).toBe("");
    expect(JSON.stringify(workflow)).toBe(before);
  });
  it("shows expected files without claiming they exist", () => {
    const {workflow} = setup();
    const blocks = workflowResultBlocks({workflow});
    expect(resultAvailability(blocks[0])).toBe("Not produced yet");
    const open = vi.fn();
    render(<WorkflowResultInspector result={blocks[0]} onOpenFile={open} onSelectProducer={vi.fn()} />);
    expect(screen.queryByTestId("workflow-result-open")).toBeNull();
    expect(screen.getByRole("button", {name: /plot.svg/})).toBeDisabled();
    expect(open).not.toHaveBeenCalled();
  });
  it("keeps old-run files viewable but detaches their connectors after a source change", () => {
    const {workflow, result} = setup();
    const blocks = workflowResultBlocks({ workflow, results: [result], sourceMismatch: true });
    expect(blocks).toHaveLength(2);
    expect(blocks[0].files.every((file) => !file.available)).toBe(true);
    expect(blocks[1].producerId).toBeNull();
    expect(blocks[1].producerTitle).toBe("Saved workflow step");
    expect(resultAvailability(blocks[1])).toBe("From saved run · workflow changed");
  });
  it.each(["../outside.md", "/outside.md", "C:/outside.md", "https://outside/x", "run/../x", "run\\x", "run/x?other"])("rejects unsafe path %s", (path) => expect(safeResultPath(path)).toBe(false));
  it("only marks review membership when both path and recorded digest match", () => {
    const {workflow, result} = setup();
    const checkpoint: WorkflowApprovalCheckpoint = {checkpoint_id: "review", workspace_id: "workspace", workflow_id: "workflow",
      run_id: "run", step_id: "review", subject_digest: digest, actor: null, reason: null,
      created_at: 1, updated_at: 1, expires_at: null, external_action: null,
      action_kind: "local_review", state: "pending", subject: {artifact_digests: [digest]},
      continuation: {artifact_files: [{path: "run/plot.svg", sha256: digest}]}};
    expect(workflowResultBlocks({workflow, results: [result], checkpoint})[0].reviewLabel).toContain("awaiting review");
    result.representations[0].sha256 = "b".repeat(64);
    expect(workflowResultBlocks({workflow, results: [result], checkpoint})[0].reviewLabel).toBe("");
  });
  it("opens the exact selected file, and Results navigation only selects a result", () => {
    const {workflow, result} = setup();
    const blocks = workflowResultBlocks({workflow, results: [result]});
    const open = vi.fn(); const select = vi.fn();
    render(<><WorkflowResultsNavigator results={blocks} onSelect={select} />
      <WorkflowResultInspector result={blocks[0]} onOpenFile={open} onSelectProducer={vi.fn()} /></>);
    fireEvent.click(screen.getByTestId("workflow-results-toggle"));
    fireEvent.click(screen.getByRole("button", {name: /Plots and supporting data/}));
    expect(select).toHaveBeenCalledWith(blocks[0].id);
    expect(open).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("workflow-result-open"));
    expect(open).toHaveBeenCalledWith("run/plot.svg");
  });
});
