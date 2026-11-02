import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, describe, expect, it, vi } from "vitest";

import {
  WorkflowRecoveryConcept as Editor,
  RelationshipInspector,
  type WorkflowRecoveryConceptProps,
  type WorkflowRecoveryPersistedSource,
} from "./WorkflowRecoveryConcept";
import savedWorkflowSource from "../../../../../specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow?raw";
import { cloneWorkflow, initialWorkflow, initialLayout } from "./model";
import { createAuthoringObject } from "./authoring-objects";
import { formatRecoveryAuthoringSource } from "./recovery-authoring";
import { blankWorkflowSource } from "../../services/blank-workflow";
import type { WorkflowRunOptions } from "./WorkflowRecoveryConcept";
import type { WorkspaceEngineeringResult } from "../../services/workspace-service";
import { WorkspaceWorkflowRunError } from "../../services/workflow-run-error";
import {
  workspaceService,
  type WorkflowApprovalCheckpoint,
  type WorkspaceWorkflowReview,
} from "../../services/workspace-service";

// Historical projection checks exercise the explicit internal preview. The
// workspace default is covered below and cannot enter the manual simulation.
const WorkflowRecoveryConcept = (props: WorkflowRecoveryConceptProps) => (
  <Editor {...props} simulationPreview />
);

const reportPrompt =
  "Compare aluminum and steel for a mounting bracket. Include a table and a conclusion.";
const reportWorkflowSource = `workflow prompt_to_html
  name: "Prompt to HTML"
  purpose: "Create an HTML report from a prompt."
  discipline: "mechanical.design"
  reviewed_ai_suggestions: true
end
task document_1
  name: "Create HTML report"
  purpose: "Create report.html in this workspace."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: []
  outputs: [{"description":"The report","item":null,"key":"document_1_document_out","kind":"engineering_document","name":"HTML report","quantity":"one","required":true}]
  prompt: ${JSON.stringify(reportPrompt)}
  settings: {"authoring_template":"document","binding_state":"unbound","output_filename":"report.html","output_format":"html"}
  tool: null
  reusable_step: null
end`;

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

beforeAll(() => {
  vi.stubGlobal("ResizeObserver", MockResizeObserver);
});

it("recovers invalid raw source, the last applied diagram and moved layout without accepting or running", async () => {
  const workflow = cloneWorkflow(initialWorkflow);
  workflow.metadata.title = "Recovered diagram title";
  const layout = structuredClone(initialLayout);
  const block = workflow.blocks[0]!;
  layout.positions[block.id] = { x: 432, y: 321 };
  const onDraftChange = vi.fn();
  const onSave = vi.fn();
  const onRun = vi.fn();
  render(
    <Editor
      workflowSource={formatRecoveryAuthoringSource(initialWorkflow).text}
      workflowLayout={initialLayout}
      initialDraft={{
        source: "",
        applied_source: formatRecoveryAuthoringSource(workflow).text,
        layout,
        view: "code",
      }}
      onDraftChange={onDraftChange}
      onSave={onSave}
      onRun={onRun}
    />,
  );
  expect(screen.getByLabelText("Workflow source")).toHaveValue("");
  expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
  await waitFor(() => expect(onDraftChange).toHaveBeenCalled());
  const [observed, dirty] = onDraftChange.mock.calls.at(-1)!;
  expect(dirty).toBe(true);
  expect(observed.source).toBe("");
  expect(observed.applied_source).toContain("Recovered diagram title");
  expect(observed.layout.positions[block.id]).toEqual({ x: 432, y: 321 });
  expect(onSave).not.toHaveBeenCalled();
  expect(onRun).not.toHaveBeenCalled();
});

it("keeps the accepted Undo baseline after explicitly recovering a diagram draft", async () => {
  const workflow = cloneWorkflow(initialWorkflow);
  workflow.metadata.title = "Recovered editable title";
  const source = formatRecoveryAuthoringSource(workflow).text;
  const onDraftChange = vi.fn();
  render(
    <Editor
      workflowSource={formatRecoveryAuthoringSource(initialWorkflow).text}
      workflowLayout={initialLayout}
      onDraftChange={onDraftChange}
      initialDraft={{
        source,
        applied_source: source,
        layout: initialLayout,
        view: "diagram",
      }}
    />,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-undo"));
  await waitFor(() =>
    expect(onDraftChange.mock.calls.at(-1)?.[0].applied_source).not.toContain(
      "Recovered editable title",
    ),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-redo"));
  await waitFor(() =>
    expect(onDraftChange.mock.calls.at(-1)?.[0].applied_source).toContain(
      "Recovered editable title",
    ),
  );
});

it("keeps the editor usable when LAN HTTP has no Web Crypto digest", async () => {
  const browserCrypto = globalThis.crypto;
  vi.stubGlobal("crypto", { subtle: undefined });
  try {
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath="workflows/lan-report.workflow.wflow"
        storageDigest={"a".repeat(64)}
        definitionRevision={1}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
        "data-semantic-digest",
        "sha256:unavailable-in-this-browser",
      ),
    );
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "data-layout-digest",
      "sha256:unavailable-in-this-browser",
    );
  } finally {
    vi.stubGlobal("crypto", browserCrypto);
  }
});

it("shows a queued desktop task on the exact active run and clears it on completion without dispatching", async () => {
  const record: import("../../services/workspace-service").WorkspaceWorkflowRunSummary =
    {
      path: "runs/report/run-1.json",
      run_id: "run-1",
      status: "running",
      started_at: "2026-10-12T01:09:23Z",
      source_digest: "b".repeat(64),
      source_matches_current: true,
      results: [],
      execution: {
        active_task_id: "document_1",
        completed_task_ids: [],
        event_count: 3,
        model_call_count: 1,
        tool_call_count: 0,
        tool_completed_count: 0,
        revision_count: 0,
        outputs: [],
        last_progress: {
          kind: "step_started",
          task_title: "Create HTML report",
        },
        truncated: false,
      },
    };
  const runs = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockResolvedValue([record]);
  const reviews = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowReviews")
    .mockResolvedValue([]);
  const read = vi.fn().mockResolvedValue({
    runId: "run-1",
    requestId: "request-1",
    queuedAt: record.started_at,
    label: "Waiting for desktop chat",
    detail:
      "Send Continue the workflow in dave in the desktop chat to continue this same run.",
  });
  const onRun = vi.fn();
  const props = {
    workflowSource: reportWorkflowSource,
    workspaceId: "workspace-1",
    workspaceSessionId: "session-1",
    workflowFilePath: "workflows/report.workflow.wflow",
    storageDigest: record.source_digest,
    definitionRevision: 1,
    onRun,
    onReadReasoningStatus: read,
  };
  const view = render(<Editor {...props} />);
  try {
    const banner = await screen.findByTestId("workflow-run-reasoning-wait");
    expect(banner).toHaveTextContent("Waiting for desktop chat");
    expect(banner).toHaveTextContent("Queued at");
    expect(banner).toHaveTextContent("request-1");
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveTextContent(
      "Waiting for chat",
    );
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Waiting for desktop chat");
    fireEvent.click(screen.getByRole("button", { name: "Show waiting task" }));
    expect(screen.getByTestId("workflow-recovery-inspector")).toHaveTextContent(
      "Create report.html",
    );
    expect(onRun).not.toHaveBeenCalled();
    runs.mockResolvedValue([
      { ...record, status: "completed", completed_at: "2026-10-12T01:10:23Z" },
    ]);
    view.rerender(<Editor {...props} reopenRequest={1} />);
    await waitFor(() =>
      expect(
        screen.queryByTestId("workflow-run-reasoning-wait"),
      ).not.toBeInTheDocument(),
    );
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Completed");
    expect(onRun).not.toHaveBeenCalled();
  } finally {
    view.unmount();
    runs.mockRestore();
    reviews.mockRestore();
  }
});

it.each([
  ["empty", () => blankWorkflowSource("Readiness check")],
  ["configured", () => reportWorkflowSource],
] as const)(
  "does not call a %s unstarted workflow ready to run",
  async (kind, source) => {
    const onRun = vi.fn();
    render(
      <Editor
        workflowSource={source()}
        workflowFilePath="workflows/readiness.workflow.wflow"
        storageDigest={"a".repeat(64)}
        definitionRevision={1}
        onRun={onRun}
        templateReadiness={
          {
            state: "not_template",
          } as import("../../services/workspace-service").WorkspaceWorkflowSourceReadiness
        }
      />,
    );
    const toggle = screen.getByTestId("workflow-recovery-run-details-toggle");
    await waitFor(() => expect(toggle).toHaveTextContent("Not started"));
    expect(toggle).not.toHaveTextContent("Ready to run");
    fireEvent.click(toggle);
    expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
      "Not started",
    );
    expect(
      screen.getByTestId("workflow-native-run-summary"),
    ).not.toHaveTextContent("Ready to run");
    fireEvent.click(screen.getByRole("button", { name: "View run readiness" }));
    expect(
      screen.getByTestId("workflow-recovery-run-readiness"),
    ).toHaveAttribute("open");
    expect(
      screen.getByTestId("workflow-recovery-run-readiness-toggle"),
    ).toHaveFocus();
    if (kind === "empty") {
      expect(
        screen.getByTestId("workflow-recovery-run-readiness-toggle"),
      ).not.toHaveTextContent("Authoring checks pass");
      expect(
        screen.getByTestId("workflow-recovery-run-readiness"),
      ).toHaveTextContent("Add a processing step");
    }
    expect(onRun).not.toHaveBeenCalled();
  },
);

it("explains that input blocks alone do not make a runnable process", async () => {
  const onRun = vi.fn();
  render(
    <Editor
      workflowSource={blankWorkflowSource("Input only")}
      workflowFilePath="workflows/input-only.workflow.wflow"
      storageDigest={"a".repeat(64)}
      definitionRevision={1}
      onRun={onRun}
    />,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
  fireEvent.click(screen.getByTestId("workflow-recovery-create-group-input"));
  fireEvent.click(
    screen.getByTestId("workflow-recovery-create-template-text-input"),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-run-readiness-toggle"));
  expect(
    screen.getByTestId("workflow-recovery-readiness-no-tasks"),
  ).toHaveTextContent("Input blocks supply data");
  expect(
    screen.getByTestId("workflow-recovery-run-details-toggle"),
  ).toHaveTextContent("Not started");
  expect(onRun).not.toHaveBeenCalled();
});

it("follows an exact source step without reloading or replacing an open source draft", async () => {
  const process = {
    workspace_id: "workspace",
    source_path: "workflows/report.workflow.wflow",
    source_digest: "a".repeat(64),
  };
  const props = {
    workflowSource: reportWorkflowSource,
    workspaceId: "workspace",
    workflowFilePath: process.source_path,
    storageDigest: process.source_digest,
    definitionRevision: 2,
  };
  const view = render(<Editor {...props} />);
  fireEvent.change(screen.getByTestId("workflow-recovery-view-select"), {
    target: { value: "code" },
  });
  const editor = screen.getByTestId(
    "workflow-recovery-source-editor",
  ) as HTMLTextAreaElement;
  const draft = `${reportWorkflowSource}\nunsaved draft`;
  fireEvent.change(editor, { target: { value: draft } });
  view.rerender(
    <Editor
      {...props}
      navigation={{
        requestId: "step-one",
        resolution: {
          process,
          target: { kind: "block", block_id: "document_1" },
        },
      }}
    />,
  );
  expect(screen.getByTestId("workflow-recovery-source-editor")).toHaveValue(
    draft,
  );
  expect(screen.getByTestId("workflow-recovery-inspector")).toBeVisible();
  expect(
    screen.queryByTestId("workflow-navigation-error"),
  ).not.toBeInTheDocument();
  const selected = screen.getByTestId("workflow-recovery-inspector");
  expect(selected).toHaveTextContent("Create report.html in this workspace.");
});

it("explains a mismatched saved revision while preserving the open editor", async () => {
  const props = {
    workflowSource: reportWorkflowSource,
    workspaceId: "workspace",
    workflowFilePath: "workflows/report.workflow.wflow",
    storageDigest: "a".repeat(64),
    definitionRevision: 2,
  };
  render(
    <Editor
      {...props}
      navigation={{
        requestId: "other-revision",
        resolution: {
          process: {
            workspace_id: "workspace",
            source_path: props.workflowFilePath,
            source_digest: "b".repeat(64),
          },
          target: { kind: "block", block_id: "document_1" },
        },
      }}
    />,
  );
  await screen.findByTestId("workflow-navigation-error");
  expect(screen.getByTestId("workflow-navigation-error")).toHaveTextContent(
    "different saved workflow revision",
  );
  expect(screen.getByTestId("workflow-recovery-concept")).toBeInTheDocument();
});

it("explains a template gate without claiming a run failed or a prompt was sent", async () => {
  const onRun = vi
    .fn()
    .mockRejectedValue(
      new WorkspaceWorkflowRunError(
        "This engineering template needs setup or qualification before a live run.",
        "workflow_template_setup_required",
        "Bracket geometry and CalculiX D034 integration require clean-environment qualification.",
        "request",
        "trace-blocked",
      ),
    );
  render(
    <Editor
      workflowSource={reportWorkflowSource}
      definitionRevision={2}
      storageDigest={"b".repeat(64)}
      onRun={onRun}
    />,
  );
  await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
  const issue = await screen.findByTestId("workflow-run-issue");
  expect(issue).toHaveTextContent("No workflow steps ran");
  expect(issue).toHaveTextContent("Wright template/integration maintainers");
  expect(issue).toHaveTextContent("Not assessed");
  expect(
    screen.getByTestId("workflow-recovery-run-details-toggle"),
  ).toHaveTextContent("Run not started");
  expect(
    screen.getByTestId("workflow-recovery-native-run-mode"),
  ).not.toHaveTextContent("Workflow failed");
  expect(
    screen.queryByTestId("workflow-recovery-native-run-input"),
  ).not.toBeInTheDocument();
  await userEvent.click(screen.getByText("Technical log and telemetry"));
  expect(screen.getByTestId("workflow-run-error-diagnostic")).toHaveTextContent(
    "trace-blocked",
  );
  expect(screen.getByTestId("workflow-run-error-diagnostic")).toHaveTextContent(
    "CalculiX",
  );
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Copy diagnostic" }),
  );
  await waitFor(() =>
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("trace-blocked"),
    ),
  );
  expect(writeText.mock.calls[0]?.[0]).not.toContain(reportPrompt);
});

it("rehydrates a pending review into the normal run drawer without running or pulsing", async () => {
  const review: WorkspaceWorkflowReview = {
    review_id: "review-1",
    package_digest: "package",
    state: "pending",
    run_id: "run-1",
    workflow_path: "workflows/review.wflow",
    source_digest: "source",
    task_id: "review",
    task_title: "Engineer review",
    instructions: "Check dimensions.",
    artifacts: [
      {
        output_path: "report-001.html",
        sha256: "sha",
        output_bytes: 128,
        output_format: "html",
        task_id: "document_1",
        task_title: "Report",
      },
    ],
    created_at: "2026-09-08T10:00:00Z",
    decided_at: null,
    actor: null,
    reason: null,
  };
  const fetch = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowReviews")
    .mockResolvedValue([review]);
  const onRun = vi.fn();
  const onOpenFile = vi.fn();
  render(
    <Editor
      workflowSource={reportWorkflowSource}
      workflowFilePath={review.workflow_path}
      definitionRevision={2}
      storageDigest={"b".repeat(64)}
      workspaceSessionId="session"
      onRun={onRun}
      onOpenFile={onOpenFile}
    />,
  );
  await waitFor(() =>
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Awaiting your review"),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(
    await screen.findByTestId("workflow-document-review"),
  ).toHaveTextContent("Check dimensions.");
  fireEvent.click(screen.getByRole("button", { name: "Open report-001.html" }));
  expect(onOpenFile).toHaveBeenCalledWith("report-001.html");
  expect(onRun).not.toHaveBeenCalled();
  expect(
    document.querySelector('[data-active="true"][data-run-state="running"]'),
  ).toBeNull();
  expect(
    screen.getByTestId("workflow-recovery-block-block.document-1"),
  ).toHaveAttribute("data-run-state", "idle");
  fetch.mockRestore();
});

it.each([
  ["pending", "Awaiting your review"],
  ["approved", "Review approved"],
  ["changes_requested", "Changes requested"],
] as const)(
  "rehydrates %s into the drawer and summary, preserving older reviews",
  async (state, label) => {
    const current: WorkspaceWorkflowReview = {
      review_id: "new-review",
      package_digest: "new-package",
      state,
      run_id: "run-new",
      workflow_path: "workflows/review.wflow",
      source_digest: "source",
      task_id: "review",
      task_title: "Latest engineer review",
      instructions: "Check the current synthetic package.",
      artifacts: [],
      created_at: "2026-09-08T10:00:00Z",
      decided_at: state === "pending" ? null : "2026-09-08T10:10:00Z",
      actor: null,
      reason: state === "changes_requested" ? "Add tolerances" : null,
    };
    const older = {
      ...current,
      review_id: "old-review",
      package_digest: "old-package",
      state: "pending" as const,
      task_title: "Older engineer review",
      created_at: "2026-09-07T10:00:00Z",
    };
    const fetch = vi
      .spyOn(workspaceService, "getWorkspaceWorkflowReviews")
      .mockResolvedValue([current, older]);
    const onRun = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath={current.workflow_path}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        workspaceSessionId="session"
        onRun={onRun}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      ).toHaveTextContent(label),
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
    expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
      label,
    );
    expect(
      screen.getByTestId("workflow-native-run-summary"),
    ).not.toHaveTextContent("Run the saved workflow");
    expect(
      screen.getByText("Awaiting your review · Older engineer review"),
    ).toBeVisible();
    expect(onRun).not.toHaveBeenCalled();
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "idle");
    fetch.mockRestore();
  },
);

it.each(["approved", "changes_requested"] as const)(
  "updates summary immediately after %s on a reopened review",
  async (state) => {
    const pending: WorkspaceWorkflowReview = {
      review_id: "review-decision",
      package_digest: "package",
      state: "pending",
      run_id: "run",
      workflow_path: "workflows/review.wflow",
      source_digest: "source",
      task_id: "review",
      task_title: "Engineer review",
      instructions: "Review the synthetic document.",
      artifacts: [],
      created_at: "2026-09-08T10:00:00Z",
      decided_at: null,
      actor: null,
      reason: null,
    };
    const fetch = vi
      .spyOn(workspaceService, "getWorkspaceWorkflowReviews")
      .mockResolvedValue([pending]);
    const decide = vi
      .spyOn(workspaceService, "decideWorkspaceWorkflowReview")
      .mockResolvedValue({
        ...pending,
        state,
        reason: "Synthetic review note",
      });
    const onRun = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath={pending.workflow_path}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        workspaceSessionId="session"
        onRun={onRun}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      ).toHaveTextContent("Awaiting your review"),
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
    if (state === "changes_requested")
      fireEvent.change(
        screen.getByLabelText("Review notes (required for changes)"),
        { target: { value: "Synthetic review note" } },
      );
    fireEvent.click(
      screen.getByRole("button", {
        name: state === "approved" ? "Approve" : "Request changes",
      }),
    );
    const label =
      state === "approved" ? "Review approved" : "Changes requested";
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      ).toHaveTextContent(label),
    );
    expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
      label,
    );
    expect(
      screen.getByTestId("workflow-native-run-summary"),
    ).not.toHaveTextContent("Ready to run");
    expect(onRun).not.toHaveBeenCalled();
    expect(decide).toHaveBeenCalledOnce();
    fetch.mockRestore();
    decide.mockRestore();
  },
);

function missingInteractiveTestIds(root: HTMLElement): string[] {
  return [
    ...root.querySelectorAll<HTMLElement>(
      'button, input, textarea, select, summary, a[href], [role="button"], [tabindex]:not([tabindex="-1"])',
    ),
  ]
    .filter((element) => !element.dataset.testid)
    .map(
      (element) =>
        `${element.tagName.toLowerCase()}:${element.getAttribute("aria-label") ?? element.textContent?.trim().slice(0, 40) ?? ""}`,
    );
}

async function openDesignIntentSettings() {
  fireEvent.click(
    screen.getByTestId("workflow-recovery-block-block.design-intent"),
  );
}

function renameBlock(id: string, title: string) {
  fireEvent.doubleClick(
    screen.getByTestId(`workflow-recovery-block-${id}`).querySelector("h3")!,
  );
  const field = screen.getByTestId(`workflow-recovery-rename-${id}`);
  fireEvent.change(field, { target: { value: title } });
  fireEvent.keyDown(field, { key: "Enter" });
}

describe("WorkflowRecoveryConcept component states", () => {
  it("renames the workflow through metadata commands, Undo/Redo, save and cold reopen without running", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    }));
    const onRun = vi.fn();
    const view = render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    const name = screen.getByRole("textbox", { name: "Workflow name" });
    await userEvent.click(name);
    await userEvent.keyboard("Material comparison{Enter}");
    expect(
      screen.getByRole("heading", { name: "Material comparison", level: 1 }),
    ).toBeVisible();
    expect(
      screen.getByTestId("workflow-recovery-save-status"),
    ).toHaveTextContent("Unsaved");
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    expect(name).toHaveValue("Prompt to HTML");
    await userEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(name).toHaveValue("Material comparison");
    await userEvent.click(name);
    await userEvent.keyboard("Engineering material comparison");
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    const saved = onSave.mock.calls[0]![0];
    expect(saved).toContain('name: "Engineering material comparison"');
    expect(saved).toContain("workflow prompt_to_html");
    expect(saved).toContain(reportPrompt);
    expect(saved).toContain('"output_filename":"report.html"');
    expect(onRun).not.toHaveBeenCalled();
    view.unmount();
    render(
      <Editor
        workflowSource={saved}
        definitionRevision={3}
        storageDigest={"c".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    expect(screen.getByRole("textbox", { name: "Workflow name" })).toHaveValue(
      "Engineering material comparison",
    );
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
    expect(onRun).not.toHaveBeenCalled();
  });

  it("locks the workflow name while an unapplied source draft is present", () => {
    render(<Editor workflowSource={reportWorkflowSource} />);
    fireEvent.change(screen.getByTestId("workflow-recovery-view-select"), {
      target: { value: "code" },
    });
    fireEvent.change(screen.getByTestId("workflow-recovery-source-editor"), {
      target: { value: `${reportWorkflowSource}\nunfinished source` },
    });
    expect(
      screen.getByRole("textbox", { name: "Workflow name" }),
    ).toHaveAttribute("readonly");
    expect(screen.getByTestId("workflow-recovery-source-editor")).toHaveValue(
      `${reportWorkflowSource}\nunfinished source`,
    );
  });

  it("renames a block from its inspector heading through the normal undo and save commands", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    }));
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
      />,
    );
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    const name = screen.getByRole("textbox", { name: "Block name" });
    await userEvent.click(name);
    await userEvent.keyboard("Product design report{Enter}");
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveTextContent("Product design report");
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    expect(name).toHaveValue("Create HTML report");
    await userEvent.click(name);
    await userEvent.keyboard("Discard this{Escape}");
    expect(name).toHaveValue("Create HTML report");
    await userEvent.clear(name);
    await userEvent.tab();
    expect(name).toHaveValue("Create HTML report");
    await userEvent.click(name);
    await userEvent.keyboard("Product design report");
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(onSave.mock.calls[0]![0]).toContain('name: "Product design report"');
  });

  it("edits legacy review, tool and output blocks directly, preserving parameters and Undo", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    }));
    render(
      <Editor
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
      />,
    );
    for (const id of [
      "block.create-design-specification",
      "block.generate-geometry",
      "block.export-step",
    ]) {
      fireEvent.click(screen.getByTestId(`workflow-recovery-block-${id}`));
      expect(
        screen.queryByRole("tablist", { name: "Step detail sections" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("workflow-recovery-config-apply"),
      ).not.toBeInTheDocument();
      const instructions = screen.getByTestId(
        `workflow-recovery-block-instructions-${id}`,
      );
      expect(instructions).toBeVisible();
      const original = (instructions as HTMLTextAreaElement).value;
      fireEvent.change(instructions, {
        target: { value: "Use the connected design requirements." },
      });
      await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
      expect(instructions).toHaveValue(original);
      fireEvent.change(instructions, {
        target: { value: "Use the connected design requirements." },
      });
      await userEvent.click(
        screen.getByTestId("workflow-recovery-block-connections"),
      );
      expect(screen.getByRole("heading", { name: "Inputs" })).toBeVisible();
      expect(screen.getByRole("heading", { name: "Outputs" })).toBeVisible();
    }
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.generate-geometry"),
    );
    await userEvent.click(
      screen.getByTestId(
        "workflow-recovery-settings-advanced-block.generate-geometry",
      ),
    );
    const thickness = screen.getByTestId(
      "workflow-recovery-block-thickness-block.generate-geometry",
    );
    fireEvent.change(thickness, { target: { value: "3" } });
    expect(thickness).toHaveValue(3);
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(onSave.mock.calls[0]![0]).toContain(
      "Use the connected design requirements.",
    );
    expect(onSave.mock.calls[0]![0]).toContain('"thickness_mm":3');
  });

  it("blocks disconnected processes before saving or running, but permits draft saves and repair", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    }));
    const onRun = vi.fn(async () => ({
      outputPath: "report.html",
      outputBytes: 100,
      taskId: "document_1",
      taskTitle: "Create HTML report",
    }));
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    fireEvent.click(
      screen.getByTestId("workflow-recovery-create-group-document"),
    );
    fireEvent.click(
      screen.getByTestId("workflow-recovery-create-template-document"),
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-validate"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "2 disconnected groups",
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "move each independent process to its own workflow",
    );
    const dismiss = screen.getByRole("button", {
      name: "Dismiss workflow messages",
    });
    dismiss.focus();
    await userEvent.keyboard("{Enter}");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-validate")).toHaveFocus();
    expect(onRun).not.toHaveBeenCalled();
    expect(onSave).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("workflow-recovery-validate"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "2 disconnected groups",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Dismiss workflow messages" }),
    );

    fireEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "2 disconnected groups",
    );
    expect(onRun).not.toHaveBeenCalled();
    expect(onSave).not.toHaveBeenCalled();
    expect(
      screen.getByTestId("workflow-recovery-run-start"),
    ).not.toHaveTextContent("Running");
    fireEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(onRun).not.toHaveBeenCalled();
    const added = screen.getByTestId(
      "workflow-recovery-block-block.document-2",
    );
    added.focus();
    await userEvent.keyboard("{Delete}");
    fireEvent.click(screen.getByTestId("workflow-recovery-delete-confirm"));
    expect(
      screen.queryByTestId(
        "workflow-recovery-diagnostic-WFR-DISCONNECTED-PROCESS",
      ),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("workflow-recovery-undo"));
    fireEvent.click(screen.getByTestId("workflow-recovery-validate"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "2 disconnected groups",
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(
      screen.queryByTestId(
        "workflow-recovery-diagnostic-WFR-DISCONNECTED-PROCESS",
      ),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    expect(onSave).toHaveBeenCalledTimes(2);
  });

  it("shows authoritative template qualification and blocks a setup-required run before dispatch", async () => {
    const onRun = vi.fn();
    const onRefreshTemplateReadiness = vi.fn();
    render(
      <Editor
        onRun={onRun}
        onRefreshTemplateReadiness={onRefreshTemplateReadiness}
        templateReadiness={{
          state: "setup_required",
          template_id: "printed-replacement-part",
          template_version: "1.0.0",
          source_digest: null,
          layout_digest: null,
          definition_valid: true,
          configured: false,
          qualified: false,
          available: false,
          verified_run: false,
          facts: [],
          blocking_reasons: [
            "Connect and qualify the required engineering tools.",
          ],
          message: null,
        }}
      />,
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-run-readiness-toggle"),
    );
    expect(screen.getByText("Setup required")).toBeVisible();
    await userEvent.click(
      screen.getByTestId("workflow-recovery-template-readiness-refresh"),
    );
    expect(onRefreshTemplateReadiness).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(onRun).not.toHaveBeenCalled();
    expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
      "Run blocked before prompt dispatch",
    );
  });

  it("sends a revised starter through ordinary preflight without labeling it qualified", async () => {
    const onRun = vi
      .fn()
      .mockRejectedValue(
        new Error(
          "Current tool qualification is missing. Check readiness in the working view.",
        ),
      );
    const onRefreshTemplateReadiness = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath="workflows/revised.workflow.wflow"
        storageDigest={"b".repeat(64)}
        definitionRevision={2}
        onRun={onRun}
        onRefreshTemplateReadiness={onRefreshTemplateReadiness}
        templateReadiness={{
          state: "revised",
          template_id: "replacement-drawer-handle",
          template_version: "1.0.0",
          source_digest: "a".repeat(64),
          layout_digest: "c".repeat(64),
          accepted_source_digest: "b".repeat(64),
          definition_revision: 2,
          definition_valid: null,
          configured: null,
          qualified: null,
          available: null,
          verified_run: null,
          facts: [],
          blocking_reasons: [],
          message:
            "Check this accepted revision's current inputs, tools, model and authority in the working view before starting.",
        }}
      />,
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-run-readiness-toggle"),
    );
    expect(
      screen.getByText("Revised · preflight required", { exact: true }),
    ).toBeVisible();
    expect(screen.queryByText("Ready", { exact: true })).toBeNull();
    expect(screen.queryByText("Verified", { exact: true })).toBeNull();
    const issue = screen.getByTestId(
      "workflow-recovery-template-readiness-issue",
    );
    expect(issue).toHaveTextContent("replacement-drawer-handle");
    expect(issue).toHaveTextContent(
      "current inputs, tools, model and authority",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Refresh revision status" }),
    );
    expect(onRefreshTemplateReadiness).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    expect(onRun.mock.calls[0]?.[0].expectedStorageDigest).toBe("b".repeat(64));
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-native-run-summary"),
      ).toHaveTextContent("Current tool qualification is missing"),
    );
  });

  it("corrects the old single-file image template on save while preserving its file and identity", async () => {
    const workflow = cloneWorkflow(initialWorkflow);
    const image = createAuthoringObject("image-input", workflow, initialLayout);
    image.ports[0]!.cardinality = "many";
    image.block.configuration.workspace_file = "inputs/reference.png";
    workflow.blocks.push(image.block);
    workflow.ports.push(...image.ports);
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "a".repeat(64),
    }));
    render(
      <Editor
        workflowSource={formatRecoveryAuthoringSource(workflow).text}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
      />,
    );
    const block = screen.getByTestId(
      `workflow-recovery-block-${image.block.id}`,
    );
    fireEvent.doubleClick(block.querySelector("h3")!);
    const name = screen.getByTestId(
      `workflow-recovery-rename-${image.block.id}`,
    );
    fireEvent.change(name, { target: { value: "Selected reference" } });
    fireEvent.keyDown(name, { key: "Enter" });
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-save-status"),
      ).toHaveTextContent("Saved"),
    );
    expect(onSave.mock.calls[0]![0]).toContain("inputs/reference.png");
    expect(
      screen.getByTestId(`workflow-recovery-block-${image.block.id}`),
    ).toHaveTextContent("Selected reference");
    expect(
      screen.getByTestId(`workflow-recovery-handle-${image.ports[0]!.id}`),
    ).toHaveAttribute("data-cardinality", "one");
  });
  it("blocks a workspace run with actionable missing inputs and no manual simulation", async () => {
    render(
      <Editor
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "▶ Run" }));
    const dialog = screen.getByRole("dialog", { name: "Process cannot start" });
    expect(dialog).toHaveTextContent("3 inputs need configuration");
    expect(dialog).toHaveTextContent("Nothing was started or queued");
    expect(dialog).toHaveTextContent(
      "configuring inputs alone will not enable execution",
    );
    expect(
      screen.queryByTestId("workflow-recovery-run-mode"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Advance simulation" }),
    ).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Configure Design intent" }),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-input-text-block.design-intent"),
    ).toBeVisible();
    expect(
      screen.queryByTestId("workflow-recovery-config-apply"),
    ).not.toBeInTheDocument();
  });

  it("does not report configured inputs as missing or allow a run after configuring them", async () => {
    render(
      <Editor
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await userEvent.click(
      screen.getByRole("button", { name: "Configure Design intent" }),
    );
    fireEvent.change(
      screen.getByTestId("workflow-recovery-input-text-block.design-intent"),
      { target: { value: "Support the pump load." } },
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(screen.getByRole("dialog")).toHaveTextContent(
      "2 inputs need configuration",
    );
    expect(
      screen.queryByRole("button", { name: "Configure Design intent" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-execution-unavailable"),
    ).toBeVisible();
    expect(
      screen.queryByTestId("workflow-recovery-run-mode"),
    ).not.toBeInTheDocument();
  });

  it("runs the saved workspace source and reports the declared file without adding a viewer", async () => {
    let resolveRun!: (result: {
      outputPath: string;
      outputBytes: number;
      taskTitle: string;
      taskId: string;
    }) => void;
    const onRun = vi.fn().mockImplementation((options?: WorkflowRunOptions) => {
      options?.onEvent?.({
        kind: "run_started",
        at: new Date().toISOString(),
        task_id: "",
        task_title: "Create HTML report",
        run_log_path: "runs/report.json",
      });
      return new Promise<{
        outputPath: string;
        outputBytes: number;
        taskTitle: string;
        taskId: string;
      }>((resolve) => {
        resolveRun = resolve;
      });
    });
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        workspaceSessionId="session-1"
        onRun={onRun}
      />,
    );

    expect(
      screen.queryByTestId("workflow-recovery-native-run-input"),
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));

    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    expect(
      screen.getByTestId("workflow-recovery-native-run-mode"),
    ).toHaveTextContent("Workflow running");
    expect(
      screen.getByTestId("workflow-recovery-native-run-input"),
    ).toHaveTextContent("Saved prompt for");
    expect(
      screen.getByTestId("workflow-recovery-native-run-log"),
    ).toHaveTextContent("Run requested");
    expect(
      document.querySelector(
        '[data-testid^="workflow-recovery-block-"][data-run-state="running"][data-active="true"]',
      ),
    ).not.toBeNull();
    await act(async () => {
      resolveRun({
        outputPath: "report.html",
        outputBytes: 321,
        taskTitle: "Create HTML report",
        taskId: "document_1",
      });
    });
    expect(
      screen.getByTestId("workflow-recovery-native-run-mode"),
    ).toHaveTextContent("Workflow completed");
    expect(
      screen.getByTestId("workflow-recovery-native-run-mode"),
    ).toHaveTextContent("report.html");
    expect(
      screen.getByTestId("workflow-recovery-native-run-output-link"),
    ).toHaveAttribute("href", expect.stringContaining("path=report.html"));
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "idle");
    expect(
      screen.getByTestId("workflow-recovery-native-run-input"),
    ).toHaveTextContent(reportPrompt);
    expect(
      screen.queryByText("Automatic execution is not available in this build."),
    ).not.toBeInTheDocument();

    // Editing the next run must not rewrite the prompt shown for the completed run.
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    fireEvent.change(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
      { target: { value: "Write a different report about titanium." } },
    );
    expect(
      screen.queryByTestId("workflow-recovery-config-apply"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-native-run-input"),
    ).toHaveTextContent(reportPrompt);
    expect(
      screen.getByTestId("workflow-recovery-native-run-input"),
    ).not.toHaveTextContent("titanium");
  });

  it("shows the exact external-action subject and issues one-shot resume authority", async () => {
    const subject = {
      definition_digest: "a".repeat(64),
      input_digests: ["b".repeat(64)],
      artifact_digests: ["c".repeat(64)],
      binding: { server: "bambu", tool: "transfer", schema: "d".repeat(64) },
      destination: { kind: "printer", id: "p1s-shop" },
      settings: { material: "PLA", profile: "0.20-standard" },
      action: { kind: "printer_transfer", package: "c".repeat(64) },
    };
    const pending: WorkflowApprovalCheckpoint = {
      checkpoint_id: "checkpoint-12345678",
      workspace_id: "workspace-1",
      workflow_id: "workflows/printer.workflow.wflow",
      run_id: "run-1",
      step_id: "authorize_transfer",
      action_kind: "printer_transfer",
      subject,
      subject_digest: "e".repeat(64),
      state: "pending",
      continuation: { next_step_index: 1 },
      actor: null,
      reason: null,
      created_at: 1,
      updated_at: 1,
      expires_at: null,
      external_action: null,
    };
    const decide = vi
      .spyOn(workspaceService, "decideWorkflowApproval")
      .mockResolvedValue({ ...pending, state: "approved" });
    const resume = vi
      .spyOn(workspaceService, "resumeWorkflowApproval")
      .mockResolvedValue({
        ...pending,
        state: "consumed",
        external_action: {
          action_id: "resume-1",
          outcome: "not_dispatched",
          subject_digest: pending.subject_digest,
        },
      });
    const onRun = vi.fn().mockResolvedValue({
      status: "awaiting_approval" as const,
      approval: pending,
      outputPath: "package.3mf",
      outputBytes: 4096,
      taskTitle: "Generate supports and slice",
      taskId: "supports_and_slice",
      outputs: [
        {
          output_path: "package.3mf",
          output_bytes: 4096,
          output_format: "3mf",
          task_id: "supports_and_slice",
          task_title: "Generate supports and slice",
        },
      ],
    });
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath="workflows/printer.workflow.wflow"
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        workspaceSessionId="session-1"
        onRun={onRun}
      />,
    );

    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(
      await screen.findByTestId("workflow-external-approval"),
    ).toHaveTextContent(pending.subject_digest);
    expect(screen.getByTestId("workflow-external-approval")).toHaveTextContent(
      "p1s-shop",
    );
    await userEvent.click(
      screen.getByTestId("workflow-external-approval-approve"),
    );
    await userEvent.click(
      await screen.findByTestId("workflow-external-approval-resume"),
    );
    await waitFor(() => expect(resume).toHaveBeenCalledOnce());
    expect(decide).toHaveBeenCalledWith(
      "session-1",
      pending,
      "approved",
      null,
      expect.any(String),
    );
    expect(resume).toHaveBeenCalledWith(
      "session-1",
      expect.objectContaining({ state: "approved" }),
      expect.any(String),
    );
    expect(screen.getByTestId("workflow-external-approval")).toHaveTextContent(
      "waiting for the qualified adapter",
    );
    decide.mockRestore();
    resume.mockRestore();
  });

  it("explains a data connection in engineering terms without changing its definition", () => {
    const connection = initialWorkflow.relationships.find(
      (r) => r.kind === "data",
    )!;
    const apply = vi.fn();
    render(
      <RelationshipInspector
        relationshipId={connection.id}
        workflow={initialWorkflow}
        readOnly={false}
        onApply={apply}
        onDisconnect={vi.fn()}
      />,
    );
    const explanation = screen.getByTestId(
      "workflow-engineering-connection-context",
    );
    const sourcePort = initialWorkflow.ports.find(
      (p) => p.id === connection.sourceId,
    )!;
    const targetPort = initialWorkflow.ports.find(
      (p) => p.id === connection.targetId,
    )!;
    expect(explanation).toHaveTextContent(
      initialWorkflow.blocks.find((b) => b.id === sourcePort.ownerBlockId)!
        .title,
    );
    expect(explanation).toHaveTextContent(
      initialWorkflow.blocks.find((b) => b.id === targetPort.ownerBlockId)!
        .title,
    );
    expect(explanation).toHaveTextContent("Information carried:");
    expect(explanation).not.toHaveTextContent(connection.sourceId);
    expect(
      screen.getByTestId(
        `workflow-recovery-relationship-label-${connection.id}`,
      ),
    ).toHaveValue(connection.label);
    expect(apply).not.toHaveBeenCalled();
  });

  it("presents a local validation checkpoint as an exact requirements review", async () => {
    const pending: WorkflowApprovalCheckpoint = {
      checkpoint_id: "checkpoint-validation-review",
      workspace_id: "workspace-1",
      workflow_id: "workflows/validated.workflow.wflow",
      run_id: "run-validation-1",
      step_id: "review_requirements",
      action_kind: "local_review",
      subject: {
        definition_digest: "a".repeat(64),
        input_digests: ["b".repeat(64)],
        artifact_digests: ["c".repeat(64)],
        binding: { server: "wright", tool: "review_artifacts" },
        destination: { kind: "local_review", id: "workspace" },
        settings: {
          validation_review: {
            profile_ref: {
              id: "robot-arm-design-01",
              version: "1.0.0",
              sha256: "d".repeat(64),
            },
            requirement_ids: ["ARM-REQ-001", "ARM-REQ-004"],
          },
          validation_review_requirements: [
            {
              id: "ARM-REQ-001",
              text: "The arm reaches every declared target pose.",
              scope: "design",
              sources: [
                {
                  artifact_ref: "requirements/robot-arm.md",
                  locator: "R1",
                  sha256: "f".repeat(64),
                },
              ],
            },
            {
              id: "ARM-REQ-004",
              text: "The report identifies all unreachable poses.",
              scope: "content",
              sources: [
                {
                  artifact_ref: "requirements/robot-arm.md",
                  locator: "R4",
                  sha256: "1".repeat(64),
                },
              ],
            },
          ],
        },
        action: { kind: "local_review", mode: "review_only" },
      },
      subject_digest: "e".repeat(64),
      state: "pending",
      continuation: {
        next_step_index: 3,
        artifact_files: [
          { path: "results/arm-report.md", sha256: "c".repeat(64) },
        ],
        execution_context: { campaign_id: "controlled-test" },
      },
      actor: null,
      reason: null,
      created_at: 1,
      updated_at: 1,
      expires_at: null,
      external_action: null,
    };
    const onRun = vi.fn().mockResolvedValue({
      status: "awaiting_approval" as const,
      approval: pending,
      outputPath: "robot-arm.step",
      outputBytes: 4096,
      taskTitle: "Review requirements",
      taskId: "review_requirements",
      outputs: [],
    });
    const onOpenFile = vi.fn();
    const decide = vi
      .spyOn(workspaceService, "decideWorkflowApproval")
      .mockResolvedValue({ ...pending, state: "approved", updated_at: 2 });
    const resume = vi.spyOn(workspaceService, "resumeWorkflowApproval");
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        workflowFilePath="workflows/validated.workflow.wflow"
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        workspaceSessionId="session-1"
        onRun={onRun}
        onOpenFile={onOpenFile}
      />,
    );

    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    const panel = await screen.findByTestId("workflow-external-approval");
    expect(panel).toHaveTextContent("Review results against the requirements");
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Awaiting your review");
    const technical = screen.getByTestId("workflow-approval-technical-record");
    expect(technical).not.toHaveAttribute("open");
    expect(panel).toHaveTextContent("robot-arm-design-01");
    expect(panel).toHaveTextContent("1.0.0");
    expect(
      screen.getByTestId("workflow-validation-review-requirements"),
    ).not.toHaveTextContent("ARM-REQ-001");
    expect(
      screen.getByTestId("workflow-validation-review-requirements"),
    ).not.toHaveTextContent("ARM-REQ-004");
    expect(panel).toHaveTextContent(
      "The arm reaches every declared target pose.",
    );
    expect(panel).toHaveTextContent("requirements/robot-arm.md");
    expect(panel).toHaveTextContent("R4");
    expect(panel).not.toHaveTextContent("campaign runner");
    await userEvent.click(
      screen.getByRole("button", { name: "Open arm-report.md" }),
    );
    expect(onOpenFile).toHaveBeenCalledWith("results/arm-report.md");
    expect(
      screen.getByTestId("workflow-external-approval-approve"),
    ).toHaveTextContent("Approve reviewed requirements");
    await userEvent.click(
      screen.getByTestId("workflow-external-approval-approve"),
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      ).toHaveTextContent("Review approved · waiting to continue"),
    );
    expect(
      screen.queryByTestId("workflow-external-approval-resume"),
    ).toBeNull();
    expect(decide).toHaveBeenCalledWith(
      "session-1",
      pending,
      "approved",
      null,
      expect.any(String),
    );
    expect(resume).not.toHaveBeenCalled();
    decide.mockRestore();
    resume.mockRestore();
  });

  it("creates a local capture only from a verified run and selected persistent evidence", async () => {
    const createCapture = vi
      .spyOn(workspaceService, "createWorkflowDemoCapture")
      .mockResolvedValue({
        path: "captures/run-verified.demo-capture.zip",
        size_bytes: 2048,
        sha256: "d".repeat(64),
        manifest_digest: "e".repeat(64),
        artifact_count: 1,
        published: false,
      });
    const onOpenFile = vi.fn();
    const onRun = vi.fn().mockResolvedValue({
      status: "completed" as const,
      runId: "run-verified",
      runLogPath: "runs/report/run-verified.json",
      verification: {
        status: "verified",
        assertions: [{ id: "dimension-check", status: "passed" }],
      },
      captureRights: {
        capture_allowed: true,
        attribution: "Wright project fixture",
      },
      outputPath: "outputs/preview.svg",
      outputBytes: 512,
      taskTitle: "Verified preview",
      taskId: "preview",
      results: [
        {
          schema_version: 1,
          id: "run-verified:preview:image",
          kind: "image" as const,
          name: "Verified preview",
          artifact_role: "verification" as const,
          representations: [
            {
              kind: "workspace_file" as const,
              location: "outputs/preview.svg",
              format: "svg",
              provider_id: "",
              resource_id: "",
              revision: null,
              durability: "persistent" as const,
              sha256: "c".repeat(64),
              size_bytes: 512,
            },
          ],
          provenance: {
            run_id: "run-verified",
            task_id: "preview",
            output_port: "image",
            input_revisions: [],
          },
          exports: [],
        },
      ],
    });
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        workspaceSessionId="session-1"
        onRun={onRun}
        onOpenFile={onOpenFile}
      />,
    );

    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await userEvent.click(
      await screen.findByTestId("workflow-demo-capture-toggle"),
    );
    fireEvent.change(screen.getByTestId("workflow-demo-capture-caption"), {
      target: { value: "Verified dimension and mesh evidence." },
    });
    await userEvent.click(screen.getByTestId("workflow-demo-capture-create"));
    await waitFor(() => expect(createCapture).toHaveBeenCalledOnce());
    expect(createCapture).toHaveBeenCalledWith(
      "session-1",
      "run-verified",
      "runs/report/run-verified.json",
      ["run-verified:preview:image"],
      "Verified dimension and mesh evidence.",
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "No post was published",
    );
    await userEvent.click(screen.getByTestId("workflow-demo-capture-open"));
    expect(onOpenFile).toHaveBeenCalledWith(
      "captures/run-verified.demo-capture.zip",
    );
    createCapture.mockRestore();
  });

  it("explains why an unverified run cannot create a capture", async () => {
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        workspaceSessionId="session-1"
        onRun={vi.fn().mockResolvedValue({
          outputPath: "report.html",
          outputBytes: 128,
          taskTitle: "Report",
          taskId: "document_1",
        })}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(
      await screen.findByTestId("workflow-demo-capture-ineligible"),
    ).toHaveTextContent("verified engineering assertions");
    expect(
      screen.queryByTestId("workflow-demo-capture-create"),
    ).not.toBeInTheDocument();
  });

  it("projects completed steps, correction invalidation and transition gaps only during the active run", async () => {
    const secondTask = reportWorkflowSource
      .slice(reportWorkflowSource.indexOf("task document_1"))
      .replaceAll("document_1", "document_2")
      .replaceAll("Create HTML report", "Create second report")
      .replace(
        "inputs: []",
        'inputs: [{"description":"First report","item":null,"key":"document_2_input","kind":"engineering_document","name":"First report","quantity":"one","required":true}]',
      );
    const source = `${reportWorkflowSource}
${secondTask}
connection reports
  type: item
  from: "document_1.document_1_document_out"
  to: "document_2.document_2_input"
  label: "Report"
  when: null
end`;
    let options!: WorkflowRunOptions;
    let finish!: (result: {
      outputPath: string;
      outputBytes: number;
      taskTitle: string;
    }) => void;
    const onRun = vi.fn((value?: WorkflowRunOptions) => {
      options = value!;
      return new Promise<{
        outputPath: string;
        outputBytes: number;
        taskTitle: string;
      }>((resolve) => {
        finish = resolve;
      });
    });
    render(
      <Editor
        workflowSource={source}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    const first = screen.getByTestId(
      "workflow-recovery-block-block.document-1",
    );
    const second = screen.getByTestId(
      "workflow-recovery-block-block.document-2",
    );
    const send = async (
      kind: "step_started" | "step_completed" | "design_revision",
      taskId: string,
      invalidated?: string[],
    ) => {
      await act(async () => {
        options.onEvent?.({
          kind,
          at: new Date().toISOString(),
          task_id: taskId,
          task_title: taskId,
          invalidated_task_ids: invalidated,
        });
      });
    };
    await send("step_started", "document_1");
    expect(first).toHaveAttribute("data-run-state", "running");
    expect(second).toHaveAttribute("data-run-state", "queued");
    await send("step_completed", "document_1");
    expect(first).toHaveAttribute("data-run-state", "succeeded");
    expect(
      document.querySelector('[data-active="true"][data-run-state="running"]'),
    ).toBeNull();
    await send("step_started", "document_2");
    expect(first).toHaveAttribute("data-run-state", "succeeded");
    expect(second).toHaveAttribute("data-run-state", "running");
    // A late completed event for the first step must not clear the active second step.
    await send("step_completed", "document_1");
    expect(second).toHaveAttribute("data-run-state", "running");
    await send("step_completed", "document_2");
    await send("design_revision", "document_2", ["document_2"]);
    expect(first).toHaveAttribute("data-run-state", "succeeded");
    expect(second).toHaveAttribute("data-run-state", "queued");
    expect(
      document.querySelector('[data-active="true"][data-run-state="running"]'),
    ).toBeNull();
    await send("step_started", "document_2");
    expect(second).toHaveAttribute("data-run-state", "running");
    // Replacing an unknown active task with the first known task would mislead the user.
    await send("step_started", "unknown_task");
    expect(
      document.querySelector('[data-active="true"][data-run-state="running"]'),
    ).toBeNull();
    await send("step_started", "document_2");
    await send("step_completed", "document_2");
    await act(async () => {
      finish({
        outputPath: "report.html",
        outputBytes: 100,
        taskTitle: "Create second report",
      });
    });
    expect(first).toHaveAttribute("data-run-state", "idle");
    expect(second).toHaveAttribute("data-run-state", "idle");
    expect(
      screen.getByTestId("workflow-recovery-native-run-mode"),
    ).toHaveTextContent("Workflow completed");
    // Starting another run cannot carry the prior run's completed badges forward.
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledTimes(2));
    expect(first).toHaveAttribute("data-run-state", "running");
    expect(second).toHaveAttribute("data-run-state", "queued");
    await act(async () => {
      finish({
        outputPath: "report.html",
        outputBytes: 100,
        taskTitle: "Create second report",
      });
    });
  });

  it("does not queue saved input sources while the consuming AI task runs", async () => {
    const source = `${reportWorkflowSource.replace("inputs: []", 'inputs: [{"description":"Brief","item":null,"key":"document_1_input","kind":"text","name":"Brief","quantity":"one","required":true}]')}
input design_brief
  name: "Design brief"
  purpose: "Supply the design brief."
  step_type: work
  group: null
  provided_by: engineer
  inputs: []
  outputs: [{"description":"Brief","item":null,"key":"brief_out","kind":"text","name":"Brief","quantity":"one","required":true}]
  instructions: "Supply the brief."
  settings: {"authoring_template":"text-input","input_mode":"text","input_text":"Design a sensor bracket."}
  tool: null
  reusable_step: null
end
connection brief
  type: item
  from: "design_brief.brief_out"
  to: "document_1.document_1_input"
  label: "Brief"
  when: null
end`;
    let finish!: (result: {
      outputPath: string;
      outputBytes: number;
      taskTitle: string;
    }) => void;
    const onRun = vi.fn(
      () =>
        new Promise<{
          outputPath: string;
          outputBytes: number;
          taskTitle: string;
        }>((resolve) => {
          finish = resolve;
        }),
    );
    render(
      <Editor
        workflowSource={source}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    const input = screen.getByTestId(
      "workflow-recovery-block-block.design-brief",
    );
    expect(input).toHaveAttribute("data-run-state", "idle");
    expect(input).not.toHaveTextContent(/queued|running/i);
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "running");
    await act(async () => {
      finish({
        outputPath: "report.html",
        outputBytes: 100,
        taskTitle: "Create HTML report",
      });
    });
    expect(input).toHaveAttribute("data-run-state", "idle");
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "idle");
  });

  it("keeps verified partial results and the durable log accessible after a later step fails", async () => {
    const produced: WorkspaceEngineeringResult = {
      schema_version: 1,
      id: "run:first:model",
      kind: "cad_model",
      name: "Bracket",
      exports: [],
      provenance: {
        run_id: "run",
        task_id: "first",
        output_port: "model",
        input_revisions: [],
      },
      representations: [
        {
          kind: "workspace_file",
          location: "bracket.psm",
          format: "psm",
          provider_id: "",
          resource_id: "",
          revision: null,
          durability: "persistent",
          sha256: null,
          size_bytes: 42,
        },
      ],
    };
    const onOpenFile = vi.fn();
    const onRun = vi.fn(async (options?: WorkflowRunOptions) => {
      options?.onEvent?.({
        kind: "run_started",
        at: new Date().toISOString(),
        task_id: "",
        task_title: "Workflow",
        run_log_path: "runs/failed.json",
      });
      options?.onEvent?.({
        kind: "result_ready",
        at: new Date().toISOString(),
        task_id: "first",
        task_title: "Create bracket",
        engineering_result: produced,
      });
      throw new Error("Analysis service disconnected");
    });
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
        onOpenFile={onOpenFile}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-native-run-mode"),
      ).toHaveTextContent("Workflow failed"),
    );
    expect(
      screen.getByTestId("workflow-recovery-partial-results"),
    ).toHaveTextContent("Results produced so far");
    await userEvent.click(
      screen.getByRole("button", { name: "Open bracket.psm" }),
    );
    expect(onOpenFile).toHaveBeenCalledWith("bracket.psm");
    await userEvent.click(screen.getByText("Technical log and telemetry"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-open-run-record"),
    );
    expect(onOpenFile).toHaveBeenCalledWith("runs/failed.json");
    expect(screen.queryByText("Workflow completed")).not.toBeInTheDocument();
  });

  it("aborts a submitted run without resubmission and preserves its verified result", async () => {
    const produced: WorkspaceEngineeringResult = {
      schema_version: 1,
      id: "run:first:model",
      kind: "cad_model",
      name: "Bracket",
      exports: [],
      provenance: {
        run_id: "run",
        task_id: "first",
        output_port: "model",
        input_revisions: [],
      },
      representations: [
        {
          kind: "workspace_file",
          location: "bracket.psm",
          format: "psm",
          provider_id: "",
          resource_id: "",
          revision: null,
          durability: "persistent",
          sha256: null,
          size_bytes: 42,
        },
      ],
    };
    const onRun = vi.fn(
      (options?: WorkflowRunOptions) =>
        new Promise<never>((_resolve, reject) => {
          options?.onEvent?.({
            kind: "result_ready",
            at: new Date().toISOString(),
            task_id: "first",
            task_title: "Create bracket",
            engineering_result: produced,
          });
          options?.signal?.addEventListener(
            "abort",
            () => reject(new DOMException("Aborted", "AbortError")),
            { once: true },
          );
        }),
    );
    const onOpenFile = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
        onOpenFile={onOpenFile}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    await userEvent.click(screen.getByRole("button", { name: "Cancel run" }));
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-native-run-mode"),
      ).toHaveTextContent("may still be running"),
    );
    expect(onRun.mock.calls[0][0]?.signal?.aborted).toBe(true);
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "idle");
    await userEvent.click(
      screen.getByRole("button", { name: "Open bracket.psm" }),
    );
    expect(onOpenFile).toHaveBeenCalledWith("bracket.psm");
    expect(onRun).toHaveBeenCalledOnce();
    expect(screen.queryByText("Workflow completed")).not.toBeInTheDocument();
  });

  it("clears a rejected run's canvas badge without claiming that a prompt was dispatched", async () => {
    const onRun = vi
      .fn()
      .mockRejectedValue(
        new Error("Model connection lost. Reconnect the model and run again."),
      );
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-native-run-mode"),
      ).toHaveTextContent("Model connection lost"),
    );
    expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
      "Run blocked",
    );
    expect(screen.queryByText("Workflow failed")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("workflow-recovery-native-run-input"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveAttribute("data-run-state", "idle");
  });

  it("saves the latest prompt and output options before running that exact saved digest", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    }));
    const onRun = vi.fn(async () => ({
      outputPath: "report-001.json",
      outputBytes: 10,
      taskTitle: "Create HTML report",
    }));
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    expect(
      screen.queryByRole("tab", { name: "Settings" }),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-save-response")).toBeChecked();
    expect(
      screen.getByTestId("workflow-recovery-save-response"),
    ).toBeDisabled();
    await userEvent.clear(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
    );
    await userEvent.type(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
      "Return a JSON answer.",
    );
    fireEvent.change(screen.getByTestId("workflow-recovery-response-format"), {
      target: { value: "json" },
    });
    fireEvent.change(screen.getByTestId("workflow-recovery-file-policy"), {
      target: { value: "overwrite" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Save & run" }));
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
    expect(onSave.mock.calls[0]![0]).toContain(
      'prompt: "Return a JSON answer."',
    );
    expect(onSave.mock.calls[0]![0]).toContain('"output_format":"json"');
    expect(onSave.mock.calls[0]![0]).toContain('"file_policy":"overwrite"');
    expect(onRun).toHaveBeenCalledWith(
      expect.objectContaining({ expectedStorageDigest: "c".repeat(64) }),
    );
  });

  it("does not start two runs when Save & run is clicked while the save is pending", async () => {
    let savedSource = "";
    let resolveSave!: (result: {
      source: string;
      definition_revision: number;
      storage_digest: string;
    }) => void;
    const onSave = vi.fn(
      (source: string) =>
        new Promise<{
          source: string;
          definition_revision: number;
          storage_digest: string;
        }>((resolve) => {
          savedSource = source;
          resolveSave = resolve;
        }),
    );
    const onRun = vi.fn(async () => ({
      outputPath: "report-rapid.json",
      outputBytes: 10,
      taskTitle: "Create HTML report",
    }));
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    fireEvent.change(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
      { target: { value: "Save exactly once." } },
    );

    const saveAndRun = screen.getByRole("button", { name: "Save & run" });
    fireEvent.click(saveAndRun);
    fireEvent.click(saveAndRun);
    expect(onSave).toHaveBeenCalledOnce();

    resolveSave({
      source: savedSource,
      definition_revision: 3,
      storage_digest: "c".repeat(64),
    });
    await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
  });

  it("does not run after a failed save and keeps the prompt draft", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("Disk unavailable"));
    const onRun = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
        onRun={onRun}
      />,
    );
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    fireEvent.change(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
      { target: { value: "Keep this edit." } },
    );
    await userEvent.click(screen.getByRole("button", { name: "Save & run" }));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(onRun).not.toHaveBeenCalled();
    expect(
      screen.getByTestId(
        "workflow-recovery-block-instructions-block.document-1",
      ),
    ).toHaveValue("Keep this edit.");
  });

  it.each(["success", "failure"])(
    "holds source and history editing until a pending save ends with %s",
    async (outcome) => {
      let resolveSave!: (value: WorkflowRecoveryPersistedSource) => void;
      let rejectSave!: (error: Error) => void;
      const onSave = vi.fn(
        () =>
          new Promise<WorkflowRecoveryPersistedSource>((resolve, reject) => {
            resolveSave = resolve;
            rejectSave = reject;
          }),
      );
      render(
        <Editor
          workflowSource={reportWorkflowSource}
          definitionRevision={2}
          storageDigest={"b".repeat(64)}
          onSave={onSave}
        />,
      );
      fireEvent.click(
        screen.getByTestId("workflow-recovery-block-block.document-1"),
      );
      fireEvent.change(
        screen.getByTestId(
          "workflow-recovery-block-instructions-block.document-1",
        ),
        { target: { value: "Snapshot being saved." } },
      );
      fireEvent.click(screen.getByTestId("workflow-recovery-view-code"));
      const source = screen.getByTestId("workflow-recovery-source-editor");
      const snapshot = (source as HTMLTextAreaElement).value;
      fireEvent.click(screen.getByTestId("workflow-recovery-save"));
      expect(source).toHaveAttribute("readonly");
      expect(screen.getByTestId("workflow-recovery-undo")).toBeDisabled();
      expect(screen.getByTestId("workflow-recovery-redo")).toBeDisabled();
      expect(
        screen.getByTestId("workflow-recovery-source-apply"),
      ).toBeDisabled();
      fireEvent.change(source, {
        target: {
          value: snapshot.replace(
            "Snapshot being saved.",
            "Unaccepted late change",
          ),
        },
      });
      fireEvent.click(screen.getByTestId("workflow-recovery-save"));
      expect(source).toHaveValue(snapshot);
      expect(onSave).toHaveBeenCalledOnce();
      await act(async () => {
        if (outcome === "success")
          resolveSave({
            source: snapshot,
            definition_revision: 3,
            storage_digest: "c".repeat(64),
          });
        else rejectSave(new Error("Save failed for this fixture"));
      });
      expect(source).not.toHaveAttribute("readonly");
      expect(source).toHaveValue(snapshot);
      expect(screen.getByTestId("workflow-recovery-undo")).toBeEnabled();
      const next = snapshot.replace(
        "Snapshot being saved.",
        "Next edit after save.",
      );
      fireEvent.change(source, { target: { value: next } });
      expect(source).toHaveValue(next);
      expect(
        screen.getByTestId("workflow-recovery-source-apply"),
      ).toBeEnabled();
    },
  );

  it("blocks native execution of an unapplied or invalid source draft", async () => {
    const onRun = vi.fn();
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onRun={onRun}
      />,
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    fireEvent.change(screen.getByTestId("workflow-recovery-source-editor"), {
      target: { value: "workflow malformed\nend\n" },
    });
    const start = screen.getByTestId("workflow-recovery-run-start");
    expect(start).toBeDisabled();
    fireEvent.click(start);
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(start).toBeDisabled();
    expect(onRun).not.toHaveBeenCalled();
  });

  it("connects another response as the prompt and derives terminal saving from that connection", async () => {
    render(
      <Editor
        workflowSource={reportWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
      />,
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-group-document"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-template-ai-prompt"),
    );
    fireEvent.change(screen.getByTestId("workflow-recovery-prompt-source"), {
      target: { value: "connection" },
    });
    fireEvent.change(screen.getByTestId("workflow-recovery-prompt-from"), {
      target: { value: "port.document-1-document-out" },
    });
    expect(screen.getByTestId("workflow-recovery-prompt-from")).toHaveValue(
      "port.document-1-document-out",
    );
    expect(
      screen.getByTestId("workflow-recovery-save-response"),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    );
    expect(
      screen.getByTestId("workflow-recovery-save-response"),
    ).not.toBeDisabled();
    expect(
      screen.getByTestId("workflow-recovery-save-response"),
    ).not.toBeChecked();
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const code = screen.getByTestId<HTMLTextAreaElement>(
      "workflow-recovery-source-editor",
    ).value;
    expect(code).toContain('"prompt_source":"connection"');
    expect(code).toContain('from: "document_1.document_1_document_out"');
    expect(code).toContain('to: "ai_prompt_1.ai_prompt_1_prompt_in"');
  });

  it("portals dialogs above retained workspace tabs while trapping and restoring keyboard focus", async () => {
    const { container, unmount } = render(
      <div style={{ position: "relative", zIndex: 1 }}>
        <WorkflowRecoveryConcept />
      </div>,
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-file-technical-details"),
    );
    const opener = screen.getByTestId("workflow-recovery-port-lab-open");
    await userEvent.click(opener);
    const backdrop = screen.getByTestId("workflow-recovery-modal-backdrop");
    const dialog = screen.getByRole("dialog", {
      name: "Connection style preview",
    });
    expect(backdrop.parentElement).toBe(document.body);
    expect(container).not.toContainElement(backdrop);
    expect(backdrop).toHaveClass("workflow-recovery-modal-theme");
    expect(backdrop).not.toHaveClass("workflow-recovery");
    const close = screen.getByTestId("workflow-recovery-modal-close");
    expect(close).toHaveFocus();
    const buttons = [
      ...dialog.querySelectorAll<HTMLButtonElement>("button:not([disabled])"),
    ];
    fireEvent.keyDown(close, { key: "Tab", shiftKey: true });
    expect(buttons.at(-1)).toHaveFocus();
    fireEvent.keyDown(buttons.at(-1)!, { key: "Tab" });
    expect(close).toHaveFocus();
    fireEvent.keyDown(close, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
    await userEvent.click(opener);
    const backdropPress = new MouseEvent("mousedown", {
      bubbles: true,
      cancelable: true,
    });
    fireEvent(
      screen.getByTestId("workflow-recovery-modal-backdrop"),
      backdropPress,
    );
    expect(backdropPress.defaultPrevented).toBe(true);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
    await userEvent.click(opener);
    await userEvent.click(
      screen.getByTestId("workflow-recovery-modal-backdrop"),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
    await userEvent.click(opener);
    unmount();
    expect(
      screen.queryByTestId("workflow-recovery-modal-backdrop"),
    ).not.toBeInTheDocument();
  });

  it("opens an independently identified workflow file but rejects identity changes during contextual editing", async () => {
    const independent = savedWorkflowSource.replace(
      /^workflow mounting_bracket$/m,
      "workflow authored_inspection_plan",
    );
    render(
      <WorkflowRecoveryConcept
        workflowSource={independent}
        definitionRevision={1}
      />,
    );
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const source = screen.getByTestId<HTMLTextAreaElement>(
      "workflow-recovery-source-editor",
    );
    expect(source.value).toContain("workflow authored_inspection_plan");
    fireEvent.change(source, {
      target: {
        value: independent.replace(
          "workflow authored_inspection_plan",
          "workflow another_document",
        ),
      },
    });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(
      screen.getByTestId(
        "workflow-recovery-diagnostic-WFR-SOURCE-IDENTITY-UNKNOWN",
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "data-revision",
      "1",
    );
  });

  it("adds and saves objects in a newly identified workflow without reverting to the example identity", async () => {
    const independent = savedWorkflowSource.replace(
      /^workflow mounting_bracket$/m,
      "workflow authored_new_document",
    );
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 2,
      storage_digest: "a".repeat(64),
    }));
    render(
      <WorkflowRecoveryConcept
        workflowSource={independent}
        definitionRevision={1}
        storageDigest={"b".repeat(64)}
        onSave={onSave}
      />,
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-group-input"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-template-text-input"),
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.text-input-1"),
    ).toBeInTheDocument();
    fireEvent.change(
      screen.getByTestId("workflow-recovery-input-text-block.text-input-1"),
      {
        target: { value: "Test the new document's independent design intent." },
      },
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(onSave.mock.calls[0]![0]).toContain(
      "workflow authored_new_document",
    );
    expect(onSave.mock.calls[0]![0]).toContain("independent design intent");
    expect(
      screen.queryByTestId(
        "workflow-recovery-diagnostic-WFR-SOURCE-IDENTITY-UNKNOWN",
      ),
    ).not.toBeInTheDocument();
  });

  it("offers editable text and file input for company context despite its deterministic implementation binding", async () => {
    render(<WorkflowRecoveryConcept />);
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.company-context"),
    );
    expect(screen.getByTestId("workflow-recovery-input-editor")).toBeVisible();
    fireEvent.change(
      screen.getByTestId("workflow-recovery-input-text-block.company-context"),
      {
        target: {
          value:
            "Use company drawing standard ME-104. Prefer stock aluminum plate.",
        },
      },
    );
    expect(
      screen.getByTestId("workflow-recovery-inputs-toggle"),
    ).toHaveTextContent("1/3 configured");
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    expect(
      screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor")
        .value,
    ).toContain("company drawing standard ME-104");
  });

  it("creates independent text inputs by keyboard, persists real text, and cold-reopens authored input", async () => {
    let savedSource = "";
    const onSave = vi.fn(async (source: string) => {
      savedSource = source;
      return { source, definition_revision: 8, storage_digest: "a".repeat(64) };
    });
    const first = render(<WorkflowRecoveryConcept onSave={onSave} />);
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    screen.getByTestId("workflow-recovery-create-group-input").focus();
    await userEvent.keyboard("{Enter}");
    screen.getByTestId("workflow-recovery-create-template-text-input").focus();
    await userEvent.keyboard("{Enter}");
    expect(
      screen.getByTestId("workflow-recovery-block-block.text-input-1"),
    ).toBeInTheDocument();
    fireEvent.change(
      screen.getByTestId("workflow-recovery-input-text-block.text-input-1"),
      {
        target: {
          value:
            "Support a 400 N load. Use stainless steel. Review the mounting interface.",
        },
      },
    );
    renameBlock("block.text-input-1", "Pump support requirements");
    expect(
      screen.getByTestId("workflow-recovery-inputs-toggle"),
    ).toHaveTextContent("1/4 configured");
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-group-input"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-template-text-input"),
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.text-input-2"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-block-block.text-input-1"),
    ).toHaveTextContent("Pump support requirements");
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(savedSource).toContain("Support a 400 N load");
    first.unmount();
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedSource}
        definitionRevision={8}
        storageDigest={"a".repeat(64)}
        onSave={onSave}
      />,
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.text-input-1"),
    ).toHaveTextContent("Pump support requirements");
    fireEvent.click(
      screen.getByTestId("workflow-recovery-block-block.text-input-1"),
    );
    expect(
      screen.getByTestId("workflow-recovery-input-text-block.text-input-1"),
    ).toHaveValue(
      "Support a 400 N load. Use stainless steel. Review the mounting interface.",
    );
  });

  it("stores a workspace-relative file path and treats a bare filename as the workspace root", async () => {
    const onOpenFile = vi.fn();
    render(<WorkflowRecoveryConcept onOpenFile={onOpenFile} />);
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-group-input"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-template-file-input"),
    );
    expect(
      screen.queryByTestId("workflow-recovery-block-title-block.file-input-1"),
    ).not.toBeInTheDocument();
    fireEvent.change(
      screen.getByTestId("workflow-recovery-input-file-block.file-input-1"),
      { target: { value: "requirements.docx" } },
    );
    expect(
      screen.getByTestId("workflow-recovery-inputs-toggle"),
    ).toHaveTextContent("1/4 configured");
    expect(
      screen.getByTestId("workflow-recovery-input-file-block.file-input-1"),
    ).toHaveValue("requirements.docx");
    expect(
      screen.getByTestId("workflow-recovery-input-selected-path"),
    ).toHaveTextContent("requirements.docx");
    expect(
      screen.getByTestId("workflow-recovery-input-selected-path"),
    ).toHaveAttribute("title", "requirements.docx");
    await userEvent.click(screen.getByTestId("workflow-recovery-input-open"));
    expect(onOpenFile).toHaveBeenCalledWith("requirements.docx");
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    expect(
      screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor")
        .value,
    ).toContain("requirements.docx");
  });

  it("edits unbound prompts and parameters, confirms deletion, and restores the full object with undo", async () => {
    render(<WorkflowRecoveryConcept />);
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-group-document"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-create-template-document"),
    );
    const id = "block.document-1";
    fireEvent.change(
      screen.getByTestId(`workflow-recovery-block-instructions-${id}`),
      {
        target: {
          value:
            "Draft a design note. Keep assumptions separate and list questions for review.",
        },
      },
    );
    fireEvent.change(screen.getByTestId("workflow-recovery-response-format"), {
      target: { value: "markdown" },
    });
    expect(screen.queryByText("More options")).not.toBeInTheDocument();
    const block = screen.getByTestId(`workflow-recovery-block-${id}`);
    fireEvent.doubleClick(block.querySelector("h3")!);
    const name = screen.getByTestId(`workflow-recovery-rename-${id}`);
    fireEvent.change(name, { target: { value: "Design note" } });
    fireEvent.keyDown(name, { key: "Enter" });
    expect(block.querySelector("h3")).toHaveTextContent("Design note");
    block.focus();
    await userEvent.keyboard("{Delete}");
    expect(
      screen.getByRole("dialog", { name: "Delete workflow step" }),
    ).toHaveTextContent("0 connection(s)");
    await userEvent.click(
      screen.getByTestId("workflow-recovery-delete-cancel"),
    );
    expect(
      screen.getByTestId(`workflow-recovery-block-${id}`),
    ).toBeInTheDocument();
    screen.getByTestId(`workflow-recovery-block-${id}`).focus();
    await userEvent.keyboard("{Delete}");
    await userEvent.click(
      screen.getByTestId("workflow-recovery-delete-confirm"),
    );
    expect(
      screen.queryByTestId(`workflow-recovery-block-${id}`),
    ).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    fireEvent.click(screen.getByTestId(`workflow-recovery-block-${id}`));
    expect(
      screen.queryByTestId("workflow-recovery-inspector-tab-definition"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId(`workflow-recovery-block-instructions-${id}`),
    ).toHaveValue(
      "Draft a design note. Keep assumptions separate and list questions for review.",
    );
    expect(screen.getByTestId("workflow-recovery-response-format")).toHaveValue(
      "markdown",
    );
  });

  it("renders the compact Add step menu, transient Inputs and contextual Inspector with stable controls", async () => {
    const { container } = render(<WorkflowRecoveryConcept />);
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute(
      "data-revision",
      "2",
    );
    expect(
      screen.getByTestId("workflow-recovery-filebar").querySelector("h1"),
    ).toHaveAttribute(
      "title",
      "mounting-bracket.workflow.wflow · Local preview · not saved",
    );
    expect(
      screen.queryByRole("heading", { name: "Three source inputs" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryAllByTestId(/workflow-recovery-create-group-/),
    ).toHaveLength(0);
    fireEvent.click(screen.getByTestId("workflow-recovery-add-step"));
    expect(
      screen.getAllByTestId(/workflow-recovery-create-group-/),
    ).toHaveLength(4);
    expect(
      screen.getByTestId("workflow-recovery-inputs-toggle"),
    ).toHaveTextContent("0/3 configured");
    expect(
      screen.queryByTestId("workflow-recovery-inputs-navigator"),
    ).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByTestId("workflow-recovery-inputs-toggle"),
    );
    expect(
      screen.getByTestId("workflow-recovery-inputs-navigator"),
    ).toHaveTextContent("Needs input");
    await userEvent.click(
      screen.getByTestId(
        "workflow-recovery-input-navigate-block.design-intent",
      ),
    );
    expect(
      screen.queryByTestId("workflow-recovery-inputs-navigator"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-input-editor")).toBeVisible();
    expect(screen.queryByText(/PDF brief/i)).not.toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest,
      ).toMatch(/^sha256:/),
    );
    expect(
      screen.getByTestId("workflow-recovery-run-readiness-toggle"),
    ).toHaveTextContent("4 items need attention");
    await userEvent.click(
      screen.getByTestId("workflow-recovery-run-readiness-toggle"),
    );
    expect(
      screen.getByTestId("workflow-recovery-run-readiness"),
    ).toHaveTextContent("0/3 configured");
    expect(
      screen.getByTestId("workflow-recovery-block-block.review-design"),
    ).toHaveTextContent("Review CAD model for approval");
    expect(
      screen.queryByTestId(
        "workflow-recovery-readiness-task-block.review-design",
      ),
    ).not.toBeInTheDocument();
    expect(missingInteractiveTestIds(container)).toEqual([]);
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute(
      "title",
      expect.stringContaining("confirmed by the workspace host"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-inspector-close"),
    );
    expect(
      screen.queryByTestId("workflow-recovery-inspector"),
    ).not.toBeInTheDocument();
    expect(container.querySelector(".recovery-workbench")).not.toHaveClass(
      "recovery-workbench--inspecting",
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-inspector-open"),
    );
    fireEvent.click(
      screen.getByTestId(
        "workflow-recovery-block-block.create-design-specification",
      ),
    );
    expect(
      screen.queryByRole("tablist", { name: "Step detail sections" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByLabelText(/^AI prompt/, { selector: "textarea" }),
    ).toBeVisible();
    expect(
      screen.getByTestId(
        "workflow-recovery-block-review-toggle-block.create-design-specification",
      ).parentElement,
    ).toHaveAttribute("open");
    expect(
      screen.getByTestId<HTMLTextAreaElement>(
        "workflow-recovery-block-review-block.create-design-specification",
      ).value,
    ).toContain("Accept when: An engineer accepted the design specification");
    expect(
      screen.getByText(
        /These criteria come from this step's accept and revise paths/,
      ),
    ).toBeVisible();
    await userEvent.click(
      screen.getByTestId("workflow-recovery-file-technical-details"),
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-port-lab-open"),
    );
    expect(screen.getByTestId("workflow-port-lab")).toBeVisible();
    expect(missingInteractiveTestIds(container)).toEqual([]);
  });

  it("renders an explicit loading state without exposing stale editor authority", () => {
    render(<WorkflowRecoveryConcept surfaceState="loading" />);
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "aria-busy",
      "true",
    );
    expect(
      screen.queryByTestId("workflow-recovery-canvas"),
    ).not.toBeInTheDocument();
  });

  it("renders an error state, preserves accepted-state language, and exposes a testable retry", async () => {
    const retry = vi.fn();
    render(<WorkflowRecoveryConcept surfaceState="error" onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "accepted workflow was not changed",
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-boundary-retry"),
    );
    expect(retry).toHaveBeenCalledOnce();
  });

  it("fails closed on invalid persisted source instead of substituting the built-in workflow", () => {
    render(
      <WorkflowRecoveryConcept
        workflowSource={"workflow malformed\nend\n"}
        definitionRevision={19}
      />,
    );
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "data-surface-state",
      "invalid-source",
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "accepted diagram was not replaced with fallback content",
    );
    expect(
      screen.queryByTestId("workflow-recovery-canvas"),
    ).not.toBeInTheDocument();
  });

  it("contains an invalid source draft with a stable diagnostic and unchanged revision", async () => {
    render(<WorkflowRecoveryConcept />);
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const editor = screen.getByTestId<HTMLTextAreaElement>(
      "workflow-recovery-source-editor",
    );
    expect(editor.value).toContain("input design_intent");
    expect(editor.value).toContain("task generate_geometry");
    expect(editor.value).not.toMatch(/^\s*(revision|parent|semantic_sha256):/m);
    fireEvent.change(editor, {
      target: { value: "workflow malformed\nend\n" },
    });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(
      (await screen.findAllByTestId(/workflow-recovery-diagnostic-WFR-/))[0],
    ).toBeVisible();
    fireEvent.click(
      screen.getByRole("button", { name: "Dismiss workflow messages" }),
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(editor).toHaveValue("workflow malformed\nend\n");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    fireEvent.click(screen.getByTestId("workflow-recovery-validate"));
    expect(
      (await screen.findAllByTestId(/workflow-recovery-diagnostic-WFR-/))[0],
    ).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "data-revision",
      "2",
    );
  });

  it("loads a workspace source, marks semantic edits unsaved, and marks them saved only after success", async () => {
    let finishSave: () => void = () => undefined;
    const onSave = vi.fn(
      (source: string) =>
        new Promise<WorkflowRecoveryPersistedSource>((resolve) => {
          finishSave = () =>
            resolve({
              source,
              definition_revision: 37,
              storage_digest: "b".repeat(64),
            });
        }),
    );
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        workflowFilePath="workflows/bracket.workflow.wflow"
        onSave={onSave}
      />,
    );

    expect(
      screen.getByTestId("workflow-recovery-filebar").querySelector("h1"),
    ).toHaveAttribute("title", "bracket.workflow.wflow · Saved in workspace");
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
    await openDesignIntentSettings();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );
    renameBlock("block.design-intent", "Design intent and loads");
    expect(
      screen.getByTestId("workflow-recovery-filebar").querySelector("h1"),
    ).toHaveAttribute("title", expect.stringContaining("Unsaved changes"));
    expect(
      screen.getByTestId("workflow-recovery-save-status"),
    ).toHaveTextContent("Unsaved");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();

    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(onSave.mock.calls[0]?.[0]).toContain(
      'name: "Design intent and loads"',
    );
    expect(
      screen.getByRole("textbox", { name: "Workflow name" }),
    ).toHaveAttribute("readonly");
    await act(async () => finishSave());
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
        "data-revision",
        "37",
      ),
    );
    expect(
      screen.getByTestId("workflow-recovery-save-status"),
    ).toHaveTextContent("Saved");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent(
      "Saved",
    );
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute(
      "data-revision",
      "37",
    );
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    // Saving publishes the accepted revision before its async semantic digest.
    // Wait for the existing bounded-simulation reason, retaining the run guard.
    await waitFor(() => {
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
      expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute(
        "title",
        expect.stringContaining("exact mounting-bracket fixture facts"),
      );
    });
  });

  it("runs the host-confirmed revision with its semantic digest and separate storage proof after undo", async () => {
    const onSave = vi.fn(async (source: string) => ({
      source,
      definition_revision: 38,
      storage_digest: "c".repeat(64),
    }));
    const storageDigest = "b".repeat(64);
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        definitionRevision={37}
        storageDigest={storageDigest}
        onSave={onSave}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest,
      ).toMatch(/^sha256:[a-f0-9]{64}$/),
    );
    const semanticSha256 = screen
      .getByTestId("workflow-recovery-concept")
      .dataset.semanticDigest!.replace("sha256:", "");
    expect(semanticSha256).not.toBe(storageDigest);
    await openDesignIntentSettings();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );

    renameBlock("block.design-intent", "Temporary local title");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    expect(screen.getByTestId("workflow-recovery-concept")).not.toHaveAttribute(
      "data-revision",
      "37",
    );
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute(
      "data-subject-revision",
      "37",
    );
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute(
      "data-subject-semantic-digest",
      semanticSha256,
    );
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute(
      "data-subject-storage-digest",
      storageDigest,
    );
    await userEvent.click(
      screen.getByTestId("workflow-recovery-run-subject-details"),
    );
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveTextContent(
      `Definition semantic SHA-256 ${semanticSha256}`,
    );
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveTextContent(
      `Stored file SHA-256 ${storageDigest}`,
    );
    expect(onSave).not.toHaveBeenCalled();
  });

  it("locks semantic edits and candidate previews to an active run subject while leaving layout interaction available", async () => {
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"b".repeat(64)}
        onSave={vi.fn()}
      />,
    );
    await openDesignIntentSettings();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );

    renameBlock("block.design-intent", "Temporary design intent");
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );
    expect(screen.getByTestId("workflow-recovery-redo")).toBeEnabled();

    const revision = screen
      .getByTestId("workflow-recovery-authority")
      .getAttribute("data-revision");
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(
      screen.getByTestId("workflow-recovery-run-definition-lock"),
    ).toHaveTextContent("Canvas layout moves remain available");
    expect(
      screen.getByRole("textbox", { name: "Workflow name" }),
    ).toHaveAttribute("readonly");

    await userEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(
      screen.getByTestId(
        "workflow-recovery-diagnostic-WFR-RUN-DEFINITION-LOCKED",
      ),
    ).toHaveTextContent("End the current test");
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute(
      "data-revision",
      revision,
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.design-intent"),
    ).toHaveTextContent("Design intent");
    expect(
      screen.getByTestId("workflow-recovery-block-block.design-intent"),
    ).not.toHaveTextContent("Temporary design intent");
    expect(screen.getByTestId("workflow-recovery-redo")).toBeEnabled();

    fireEvent.doubleClick(
      screen
        .getByTestId("workflow-recovery-block-block.design-intent")
        .querySelector("h3")!,
    );
    expect(
      screen.queryByTestId("workflow-recovery-rename-block.design-intent"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId("workflow-recovery-block-block.design-intent"),
    ).not.toHaveTextContent("Form edit during run");

    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const source = screen.getByTestId<HTMLTextAreaElement>(
      "workflow-recovery-source-editor",
    );
    fireEvent.change(source, {
      target: {
        value: source.value.replace(
          'input design_intent\n  name: "Design intent"',
          'input design_intent\n  name: "Source edit during run"',
        ),
      },
    });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute(
      "data-revision",
      revision,
    );

    await userEvent.click(screen.getByTestId("workflow-recovery-view-diagram"));
    await userEvent.click(screen.getByTestId("workflow-recovery-ai-request"));
    expect(
      screen.queryByTestId("workflow-recovery-proposal"),
    ).not.toBeInTheDocument();
    const flowNode = screen
      .getByTestId("workflow-recovery-block-block.design-intent")
      .closest(".react-flow__node");
    expect(flowNode).toHaveClass("draggable");

    await userEvent.click(screen.getByTestId("workflow-recovery-run-end"));
    expect(
      screen.queryByTestId("workflow-recovery-run-mode"),
    ).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(
      screen.getByTestId("workflow-recovery-block-block.design-intent"),
    ).toHaveTextContent("Temporary design intent");
  });

  it("saves and cold-reopens accepted AI steps from only the public workflow file", async () => {
    let persistedSource = "";
    const onSave = vi.fn(async (source: string) => {
      persistedSource = source;
      return {
        source,
        definition_revision: 12,
        storage_digest: "c".repeat(64),
      };
    });
    const first = render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        definitionRevision={2}
        storageDigest={"a".repeat(64)}
        onSave={onSave}
      />,
    );

    await userEvent.click(screen.getByTestId("workflow-recovery-ai-request"));
    const friendlyChanges = screen.getByTestId(
      "workflow-recovery-proposal-change-list",
    );
    expect(friendlyChanges).toHaveTextContent(
      "Add step: Create manufacturing drawing",
    );
    expect(
      [...friendlyChanges.querySelectorAll("p")]
        .map((item) => item.textContent)
        .join(" "),
    ).not.toMatch(/\b(?:block|port|rel)\./);
    await userEvent.click(
      screen.getByTestId("workflow-recovery-proposal-accept"),
    );
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(persistedSource).toContain("task create_inspection_drawing");
    expect(persistedSource).toContain("connection approved_to_drawing");

    first.unmount();
    render(
      <WorkflowRecoveryConcept
        workflowSource={persistedSource}
        definitionRevision={12}
        storageDigest={"c".repeat(64)}
        onSave={vi.fn()}
      />,
    );
    expect(
      screen.getByTestId(
        "workflow-recovery-block-block.create-inspection-drawing",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId(
        "workflow-recovery-block-block.review-inspection-drawing",
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
      "data-revision",
      "12",
    );
  });

  it("retains local semantic edits when an ordinary save fails", async () => {
    const onSave = vi
      .fn()
      .mockRejectedValue(
        new Error(
          "Unable to save this workflow file. Your local edits were kept.",
        ),
      );
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        storageDigest={"a".repeat(64)}
        onSave={onSave}
      />,
    );
    await openDesignIntentSettings();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );
    renameBlock("block.design-intent", "Unsaved load definition");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "local edits were kept",
    );
    expect(
      screen.getByTestId("workflow-recovery-filebar").querySelector("h1"),
    ).toHaveAttribute("title", expect.stringContaining("Unsaved changes"));
    expect(screen.getByTestId("workflow-recovery-save")).toBeEnabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute(
      "title",
      expect.stringContaining("Save workflow changes successfully"),
    );
  });

  it("protects local source on stale saves until the engineer explicitly compares, copies, or reloads", async () => {
    const conflict = Object.assign(
      new Error("server detail must not be shown"),
      { code: "workflow_source_conflict" },
    );
    const onSave = vi.fn().mockRejectedValue(conflict);
    const storedSource = savedWorkflowSource.replace(
      'name: "Design intent"',
      'name: "Stored design intent"',
    );
    const onReadStoredSource = vi.fn().mockResolvedValue({
      source: storedSource,
      definition_revision: 8,
      storage_revision: 11,
      storage_digest: "b".repeat(64),
    });
    const onReloadStoredSource = vi.fn().mockResolvedValue(undefined);
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    render(
      <WorkflowRecoveryConcept
        workflowSource={savedWorkflowSource}
        storageDigest={"a".repeat(64)}
        onSave={onSave}
        onReadStoredSource={onReadStoredSource}
        onReloadStoredSource={onReloadStoredSource}
      />,
    );
    await openDesignIntentSettings();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled(),
    );
    renameBlock("block.design-intent", "Local design requirements");
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("workspace file changed elsewhere");
    expect(alert).toHaveTextContent("local edits are still here");
    expect(alert).not.toHaveTextContent("server detail");
    expect(
      screen.getByTestId("workflow-recovery-filebar").querySelector("h1"),
    ).toHaveAttribute("title", expect.stringContaining("Unsaved changes"));
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(
      screen.getByTestId("workflow-recovery-conflict-actions"),
    ).toBeVisible();

    renameBlock(
      "block.design-intent",
      "Local requirements retained after conflict",
    );
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();

    await userEvent.click(
      screen.getByTestId("workflow-recovery-conflict-copy-local"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        'name: "Local requirements retained after conflict"',
      ),
    );
    expect(
      screen.getByTestId("workflow-recovery-conflict-action-message"),
    ).toHaveTextContent("editor and stored file were not changed");

    await userEvent.click(
      screen.getByTestId("workflow-recovery-conflict-compare"),
    );
    const comparison = await screen.findByRole("dialog", {
      name: "Compare workflow sources",
    });
    expect(onReadStoredSource).toHaveBeenCalledOnce();
    expect(
      screen.getByTestId<HTMLTextAreaElement>(
        "workflow-recovery-source-comparison-local",
      ).value,
    ).toContain('name: "Local requirements retained after conflict"');
    expect(
      screen.getByTestId<HTMLTextAreaElement>(
        "workflow-recovery-source-comparison-stored",
      ).value,
    ).toContain('name: "Stored design intent"');
    expect(comparison).toHaveTextContent(
      "neither version has been applied or saved",
    );
    expect(screen.getByTestId("workflow-recovery-modal-close")).toHaveFocus();
    await userEvent.click(screen.getByTestId("workflow-recovery-modal-close"));
    expect(
      screen.getByTestId("workflow-recovery-conflict-compare"),
    ).toHaveFocus();

    await userEvent.click(
      screen.getByTestId("workflow-recovery-conflict-reload"),
    );
    expect(
      await screen.findByRole("dialog", { name: "Reload stored workflow?" }),
    ).toHaveTextContent("discard the unsaved local workflow edits");
    expect(onReloadStoredSource).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByTestId("workflow-recovery-conflict-reload-confirm"),
    );
    await waitFor(() => expect(onReloadStoredSource).toHaveBeenCalledOnce());
    expect(onSave).toHaveBeenCalledOnce();
  });
});
