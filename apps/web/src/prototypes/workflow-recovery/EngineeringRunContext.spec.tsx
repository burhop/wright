import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type {
  WorkflowApprovalCheckpoint,
  WorkspaceWorkflowOutput,
  WorkspaceWorkflowRunSummary,
} from "../../services/workspace-service";
import {
  EngineeringActionScope,
  EngineeringFiles,
  EngineeringRunProgress,
  EngineeringStepContext,
} from "./EngineeringRunContext";
import {
  approvalPresentation,
  externallyManagedReview,
  fileKind,
  reviewFiles,
} from "./engineering-run-presentation";
import { cloneWorkflow, initialWorkflow } from "./model";
import { InputBlockEditor } from "./InputBlockEditor";

afterEach(cleanup);
const checkpoint = (
  state: WorkflowApprovalCheckpoint["state"] = "pending",
): WorkflowApprovalCheckpoint => ({
  checkpoint_id: "checkpoint",
  workspace_id: "workspace",
  workflow_id: "workflow",
  run_id: "run",
  step_id: "review",
  action_kind: "local_review",
  state,
  subject: { artifact_digests: ["a".repeat(64)] },
  subject_digest: "b".repeat(64),
  continuation: {},
  actor: null,
  reason: null,
  created_at: 1,
  updated_at: 1,
  expires_at: null,
  external_action: null,
});

describe("engineering presentation preserves evidence boundaries", () => {
  it.each([
    ["pending", "Awaiting your review"],
    ["approved", "Review approved · waiting to continue"],
    ["changes_requested", "Changes requested"],
    ["stale", "Review out of date"],
    ["expired", "Review expired"],
    ["consumed", "Review recorded"],
  ] as const)("does not mistake %s for workflow completion", (state, label) => {
    expect(approvalPresentation(checkpoint(state))?.label).toBe(label);
  });
  it("does not relabel a physical-action approval as an engineering review", () => {
    expect(
      approvalPresentation({
        ...checkpoint(),
        action_kind: "printer_transfer",
      }),
    ).toBeNull();
  });
  it("links only exact recorded package members, keeping names and paths intact", () => {
    const review = checkpoint();
    review.continuation.artifact_files = [
      { path: "run/metrics.json", sha256: "a".repeat(64) },
      { path: "run/overlay.svg", sha256: "a".repeat(64) },
      { path: "run/report.md", sha256: "a".repeat(64) },
      { path: "run/report.md", sha256: "a".repeat(64) },
      { path: "unreviewed.md", sha256: "c".repeat(64) },
      { path: "../outside.md", sha256: "a".repeat(64) },
      { path: "https://elsewhere/report.md", sha256: "a".repeat(64) },
      { path: "C:\\outside.md", sha256: "a".repeat(64) },
      { path: "missing-digest.md" },
      null,
    ];
    expect(reviewFiles(review)).toEqual([
      "run/report.md",
      "run/overlay.svg",
      "run/metrics.json",
    ]);
    expect(reviewFiles(checkpoint())).toEqual([]);
    expect(fileKind("metrics.json")).toBe("Supporting file"); // Do not invent a human-readable result from JSON.
  });
  it("does not infer an external continuation owner from file names", () => {
    const review = checkpoint();
    review.continuation.artifact_files = [
      { path: "campaign/report.md", sha256: "a".repeat(64) },
    ];
    expect(externallyManagedReview(review)).toBe(false);
    review.continuation.execution_context = { campaign_id: "managed" };
    expect(externallyManagedReview(review)).toBe(true);
  });
  it("opens exact paths even when two result basenames are identical", () => {
    const onOpenFile = vi.fn();
    render(
      <EngineeringFiles
        paths={["first/report.md", "second/report.md"]}
        onOpenFile={onOpenFile}
      />,
    );
    const buttons = screen.getAllByRole("button", { name: "Open report.md" });
    expect(buttons[0]).toHaveAttribute("title", "first/report.md");
    expect(buttons[1]).toHaveAttribute("title", "second/report.md");
    fireEvent.click(buttons[1]);
    expect(onOpenFile).toHaveBeenCalledWith("second/report.md");
  });
  it("shows external action settings without dropping nested authorization limits", () => {
    render(
      <EngineeringActionScope
        value={{
          destination: "Shop printer",
          limits: { quantity: 2, start_print: false },
          package: "a".repeat(64),
        }}
      />,
    );
    expect(screen.getByText("Shop printer")).toBeVisible();
    expect(screen.getByText("2")).toBeVisible();
    expect(screen.getByText("No")).toBeVisible();
    expect(screen.queryByText("a".repeat(64))).toBeNull();
  });
});

describe("block explanations and recorded results", () => {
  const workflow = cloneWorkflow(initialWorkflow);
  const block = workflow.blocks.find(
    (b) => b.id === "block.generate-geometry",
  )!;
  const outputs: WorkspaceWorkflowOutput[] = [
    {
      task_id: "generate_geometry",
      task_title: block.title,
      output_path: "results/bracket.step",
      output_bytes: 300,
      output_format: "step",
    },
  ];
  it("distinguishes declared outputs from produced files", () => {
    render(
      <EngineeringStepContext
        block={block}
        workflow={workflow}
        outputs={outputs}
        sourceMismatch={false}
        onOpenFile={vi.fn()}
      />,
    );
    expect(screen.getByText(block.purpose)).toBeVisible();
    expect(screen.getByText("Expected outputs")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Open bracket.step" }),
    ).toBeVisible();
  });
  it("does not attach old results to an edited workflow", () => {
    render(
      <EngineeringStepContext
        block={block}
        workflow={workflow}
        outputs={outputs}
        sourceMismatch
        onOpenFile={vi.fn()}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Open bracket.step" }),
    ).toBeNull();
    expect(screen.getByText(/different saved workflow/)).toBeVisible();
  });
  it("uses recorded completion only and opens the selected step", () => {
    const select = vi.fn();
    const run: WorkspaceWorkflowRunSummary = {
      path: "runs/run.json",
      status: "interrupted",
      source_digest: "a".repeat(64),
      started_at: "2026-09-21T12:00:00Z",
      results: [],
      execution: {
        completed_task_ids: ["generate_geometry"],
        active_task_id: "review_design",
        outputs,
        event_count: 2,
        model_call_count: 1,
        tool_call_count: 0,
        tool_completed_count: 0,
        revision_count: 0,
        truncated: false,
        last_progress: null,
      },
    };
    render(
      <EngineeringRunProgress
        run={run}
        workflow={workflow}
        onSelectBlock={select}
      />,
    );
    fireEvent.click(screen.getByText(/Step progress/));
    expect(screen.getByText("Finished")).toBeVisible();
    expect(screen.queryByText("Running")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: block.title }));
    expect(select).toHaveBeenCalledWith(block.id);
  });
});

describe("input file access", () => {
  it.each([false, true])(
    "supports full names and opening in read-only mode (image=%s)",
    (image) => {
      const path = `campaign/robot-tracking-diagnosis-01/attempt-008/inputs/${image ? "route-sketch.png" : "assembled-context.md"}`;
      const block = {
        ...initialWorkflow.blocks[0],
        configuration: { input_mode: "workspace-file", workspace_file: path },
      };
      const apply = vi.fn(),
        open = vi.fn();
      render(
        <InputBlockEditor
          block={block}
          readOnly
          onApply={apply}
          onOpenFile={open}
          isImage={image}
        />,
      );
      expect(
        screen.getByTestId("workflow-recovery-input-select"),
      ).toHaveAttribute("title", path);
      expect(
        screen.getByTestId("workflow-recovery-input-selected-path"),
      ).toHaveTextContent(path);
      fireEvent.click(screen.getByTestId("workflow-recovery-input-open"));
      expect(open).toHaveBeenCalledWith(path);
      expect(apply).not.toHaveBeenCalled();
    },
  );
  it("does not offer to open an unselected file", () => {
    const block = {
      ...initialWorkflow.blocks[0],
      configuration: { input_mode: "workspace-file", workspace_file: "" },
    };
    render(
      <InputBlockEditor
        block={block}
        readOnly={false}
        onApply={vi.fn()}
        onOpenFile={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("workflow-recovery-input-open")).toBeNull();
  });
});
