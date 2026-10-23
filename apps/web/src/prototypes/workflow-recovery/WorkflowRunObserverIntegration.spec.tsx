import robotTemplate from "../../../../../packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow?raw";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, expect, it, vi } from "vitest";
import {
  WorkflowRecoveryConcept,
  type WorkflowRunOptions,
  type WorkflowRecoveryRunResult,
} from "./WorkflowRecoveryConcept";
import {
  workspaceService,
  type WorkspaceWorkflowRunSummary,
} from "../../services/workspace-service";

const robotSource = robotTemplate.replaceAll("__instance__", "acceptance");
const task = (id: string, inputs = "[]") => `task ${id}
  name: "Report ${id}"
  purpose: "Create a report"
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: ${inputs}
  outputs: [{"key":"${id}_out","kind":"engineering_document","name":"Report","quantity":"one","required":true,"item":null,"description":"Report"}]
  prompt: "Create a useful report."
  settings: {"authoring_template":"document","binding_state":"unbound","output_filename":"${id}.html","output_format":"html"}
  tool: null
  reusable_step: null
end`;
const source = `workflow observed_test
  name: "Observed workflow"
  purpose: "Controlled observer test"
  discipline: "mechanical.design"
  reviewed_ai_suggestions: true
end
${task("document_1")}
${task("document_2", '[{"key":"document_2_in","kind":"engineering_document","name":"Prior report","quantity":"one","required":true,"item":null,"description":"The first report."}]')}
connection document_1_to_document_2
  type: item
  from: "document_1.document_1_out"
  to: "document_2.document_2_in"
  label: "report"
  when: null
end`;
const digest = "b".repeat(64);
const props = {
  workflowSource: source,
  workflowFilePath: "workflows/observed.workflow.wflow",
  definitionRevision: 2,
  storageDigest: digest,
  workspaceSessionId: "session",
  workspaceId: "workspace",
};
const snapshot = (
  status: WorkspaceWorkflowRunSummary["status"] = "running",
): WorkspaceWorkflowRunSummary => ({
  path: "runs/observed/20260908T100000Z-run.json",
  status,
  started_at: "2026-09-08T10:00:00Z",
  source_digest: digest,
  source_matches_current: true,
  run_id: "recorded-run",
  results: [],
  execution: {
    active_task_id: status === "running" ? "document_2" : null,
    completed_task_ids: ["document_1"],
    event_count: 8,
    model_call_count: 2,
    tool_call_count: 0,
    tool_completed_count: 0,
    revision_count: 0,
    outputs: [],
    last_progress: {
      kind: "step_started",
      at: "2026-09-08T10:00:01Z",
      task_id: "document_2",
      task_title: "Report document_2",
      execution_kind: "ai",
    },
    truncated: false,
  },
});
beforeAll(() =>
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    },
  ),
);
beforeEach(() => {
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
  vi.spyOn(workspaceService, "getWorkspaceWorkflowReviews").mockResolvedValue(
    [],
  );
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
const focus = () =>
  act(async () => {
    window.dispatchEvent(new Event("focus"));
  });

it.each([false, true])(
  "opens a saved run from history even when source cannot be drawn: %s",
  async (invalid) => {
    vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
      snapshot("waiting_human"),
    ]);
    const open = vi.fn(),
      run = vi.fn();
    render(
      <WorkflowRecoveryConcept
        {...props}
        workflowSource={invalid ? "invalid source" : source}
        onRun={run}
        onOpenRunWorkingView={open}
      />,
    );
    if (!invalid)
      fireEvent.click(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      );
    fireEvent.click(screen.getByText("Previous runs"));
    fireEvent.click(await screen.findByText(/Waiting for your input ·/));
    fireEvent.click(
      screen.getByRole("button", { name: "Open run in working view" }),
    );
    expect(open).toHaveBeenCalledExactlyOnceWith("recorded-run", digest);
    expect(run).not.toHaveBeenCalled();
    if (invalid)
      expect(screen.getByText("Workflow file needs correction.")).toBeVisible();
  },
);

it("shows a declared input wait and opens its exact run without starting another process", async () => {
  let current = snapshot("waiting_human");
  current.execution!.last_progress = {
    kind: "input_requested",
    task_id: "choice",
    task_title: "Choose interval",
    message: "Choose the analysis interval.",
  };
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockImplementation(
    async () => [current],
  );
  const onRun = vi.fn(),
    onOpenRunWorkingView = vi.fn();
  render(
    <WorkflowRecoveryConcept
      {...props}
      onRun={onRun}
      onOpenRunWorkingView={onOpenRunWorkingView}
    />,
  );
  const wait = await screen.findByTestId("workflow-run-input-wait");
  expect(wait).toHaveTextContent("Waiting for your input");
  expect(wait).toHaveTextContent("Choose the analysis interval.");
  expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  expect(screen.queryByTestId("workflow-run-failure-banner")).toBeNull();
  fireEvent.click(screen.getByTestId("workflow-run-answer-input"));
  expect(onOpenRunWorkingView).toHaveBeenCalledExactlyOnceWith(
    "recorded-run",
    digest,
  );
  expect(onRun).not.toHaveBeenCalled();
  current = snapshot("completed");
  await focus();
  await waitFor(() =>
    expect(screen.queryByTestId("workflow-run-input-wait")).toBeNull(),
  );
  expect(onRun).not.toHaveBeenCalled();
});

it("keeps saved results accessible when the diagram source is invalid, without restoring editing authority", async () => {
  const current = snapshot("completed");
  current.execution!.outputs = [
    {
      task_id: "document_2",
      task_title: "Slicing the final part",
      output_path: "campaign/part/artifacts/slice.gcode.3mf",
      output_bytes: 123,
      output_format: "3mf",
    },
  ];
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
    current,
  ]);
  const onRun = vi.fn(),
    onSave = vi.fn(),
    onOpenFile = vi.fn();
  render(
    <WorkflowRecoveryConcept
      {...props}
      workflowSource="workflow malformed\nend\n"
      onRun={onRun}
      onSave={onSave}
      onOpenFile={onOpenFile}
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Workflow file needs correction",
  );
  fireEvent.click(await screen.findByTestId("workflow-results-toggle"));
  fireEvent.click(
    screen.getByRole("button", { name: /Slicing the final part/ }),
  );
  fireEvent.click(screen.getByTestId("workflow-result-open"));
  expect(onOpenFile).toHaveBeenCalledWith(
    "campaign/part/artifacts/slice.gcode.3mf",
  );
  expect(screen.queryByTestId("workflow-recovery-canvas")).toBeNull();
  expect(screen.queryByTestId("workflow-recovery-run-start")).toBeNull();
  expect(onSave).not.toHaveBeenCalled();
  expect(onRun).not.toHaveBeenCalled();
});

it("does not carry invalid-source result links into another workflow while its status is loading", async () => {
  const current = snapshot("completed");
  current.execution!.outputs = [
    {
      task_id: "document_2",
      task_title: "Old result",
      output_path: "old/result.md",
      output_bytes: 1,
      output_format: "md",
    },
  ];
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockImplementation(
    async (_session, path) =>
      path === props.workflowFilePath ? [current] : new Promise(() => {}),
  );
  const invalid = {
    ...props,
    workflowSource: "workflow malformed\nend\n",
    onOpenFile: vi.fn(),
  };
  const view = render(<WorkflowRecoveryConcept {...invalid} />);
  await screen.findByTestId("workflow-result-open");
  view.rerender(
    <WorkflowRecoveryConcept
      {...invalid}
      workflowFilePath="workflows/another.wflow"
    />,
  );
  expect(screen.queryByTestId("workflow-result-open")).toBeNull();
  expect(screen.getByRole("status")).toHaveTextContent("Loading saved run");
});

it("recovers an external run into the existing graph and viewer links without POST or inert Cancel", async () => {
  let current = snapshot();
  const get = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockImplementation(async () => [current]);
  const onRun = vi.fn(),
    onOpenFile = vi.fn();
  const rendered = render(
    <WorkflowRecoveryConcept
      {...props}
      onRun={onRun}
      onOpenFile={onOpenFile}
    />,
  );
  const first = screen.getByTestId("workflow-recovery-block-block.document-1"),
    second = screen.getByTestId("workflow-recovery-block-block.document-2");
  await waitFor(() =>
    expect(second).toHaveAttribute("data-run-state", "running"),
  );
  expect(first).toHaveAttribute("data-run-state", "succeeded");
  expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  expect(screen.queryByTestId("workflow-recovery-run-cancel")).toBeNull();
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-run-observed-metrics")).toHaveTextContent(
    "2 model calls",
  );
  expect(
    screen.getByTestId("workflow-recovery-native-run-log"),
  ).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("Technical log and telemetry"));
  fireEvent.click(screen.getByTestId("workflow-recovery-open-run-record"));
  expect(onOpenFile).toHaveBeenCalledWith(current.path);
  current = {
    ...snapshot("completed"),
    execution_ended_at: "2026-09-08T10:01:00Z",
    execution: {
      ...current.execution!,
      active_task_id: null,
      completed_task_ids: ["document_1", "document_2"],
      outputs: [
        {
          task_id: "document_2",
          task_title: "Report document_2",
          output_path: "reports/result-003.html",
          output_bytes: 123,
          output_format: "html",
        },
      ],
    },
  };
  await focus();
  await waitFor(() => expect(second).toHaveAttribute("data-run-state", "idle"));
  expect(first).toHaveAttribute("data-run-state", "idle");
  expect(screen.getByTestId("workflow-recovery-run-start")).not.toBeDisabled();
  fireEvent.click(
    screen.getByTestId("workflow-recovery-native-run-output-link"),
  );
  expect(onOpenFile).toHaveBeenCalledWith("reports/result-003.html");
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
    "Workflow completed",
  );
  const readSignal = get.mock.calls.at(-1)![2]!.signal!;
  rendered.unmount();
  expect(readSignal.aborted).toBe(true);
  render(
    <WorkflowRecoveryConcept
      {...props}
      onRun={onRun}
      onOpenFile={onOpenFile}
    />,
  );
  await waitFor(() =>
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Completed"),
  );
  expect(onRun).not.toHaveBeenCalled();
});

it.each(["interrupted", "unknown"] as const)(
  "preserves truthful %s status and clears pulses",
  async (status) => {
    vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
      snapshot(status),
    ]);
    render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()} />);
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-run-details-toggle"),
      ).toHaveTextContent(
        status === "unknown"
          ? "Execution status unknown"
          : "Execution interrupted",
      ),
    );
    fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
    expect(
      screen.getByTestId("workflow-native-run-summary"),
    ).not.toHaveTextContent("Ready to run");
    expect(
      document.querySelector('[data-active="true"][data-run-state="running"]'),
    ).toBeNull();
    expect(screen.queryByTestId("workflow-recovery-run-cancel")).toBeNull();
  },
);

it("hides badges for dirty drafts while retaining exact run status and refresh failures", async () => {
  const get = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockResolvedValue([snapshot()]);
  render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()} />);
  const second = screen.getByTestId("workflow-recovery-block-block.document-2");
  await waitFor(() =>
    expect(second).toHaveAttribute("data-run-state", "running"),
  );
  fireEvent.click(second);
  fireEvent.change(
    screen.getByTestId("workflow-recovery-block-instructions-block.document-2"),
    { target: { value: "An edited local draft" } },
  );
  expect(second).toHaveAttribute("data-run-state", "idle");
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-run-source-mismatch")).toBeVisible();
  get.mockRejectedValue(new Error("Offline"));
  await focus();
  await waitFor(() =>
    expect(screen.getByTestId("workflow-run-refresh-error")).toHaveTextContent(
      "last known status",
    ),
  );
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
    "Workflow running",
  );
  expect(
    screen.getByTestId("workflow-recovery-block-instructions-block.document-2"),
  ).toHaveValue("An edited local draft");
});

it("does not assign an active badge to a different saved source", async () => {
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
    {
      ...snapshot(),
      source_digest: "c".repeat(64),
      source_matches_current: false,
    },
  ]);
  render(<WorkflowRecoveryConcept {...props} onRun={vi.fn()} />);
  await waitFor(() =>
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Running"),
  );
  expect(
    document.querySelector('[data-active="true"][data-run-state="running"]'),
  ).toBeNull();
  expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
});

it("restores validator hold diagnostics and opens the exact saved assessment", async () => {
  const onOpenFile = vi.fn();
  const held = snapshot();
  held.execution = {
    ...held.execution!,
    last_progress: {
      kind: "design_check",
      at: "2026-09-08T10:00:03Z",
      task_id: "document_2",
      task_title: "Validate structured output",
      status: "revise",
      assessment_id: "assessment-held",
      assessment_path: "validation/assessment-held.json",
      complete_result_ref:
        "wright://workspace/workspace/validation/assessment-held",
    },
  };
  vi.spyOn(workspaceService, "getWorkspaceWorkflowRuns").mockResolvedValue([
    held,
  ]);
  render(
    <WorkflowRecoveryConcept
      {...props}
      onRun={vi.fn()}
      onOpenFile={onOpenFile}
    />,
  );
  await waitFor(() =>
    expect(
      screen.getByTestId("workflow-recovery-run-details-toggle"),
    ).toHaveTextContent("Output held for correction"),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-run-details-toggle"));
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
    "The result did not pass its checks",
  );
  fireEvent.click(screen.getByTestId("workflow-open-check-report"));
  expect(onOpenFile).toHaveBeenCalledWith("validation/assessment-held.json");
});

it("keeps the owned POST and richer result ahead of older observed history", async () => {
  const get = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockResolvedValue([]);
  let options!: WorkflowRunOptions;
  let finish!: (r: WorkflowRecoveryRunResult) => void;
  const onRun = vi.fn((value?: WorkflowRunOptions) => {
    options = value!;
    return new Promise<WorkflowRecoveryRunResult>((resolve) => {
      finish = resolve;
    });
  });
  render(<WorkflowRecoveryConcept {...props} onRun={onRun} />);
  await waitFor(() =>
    expect(
      screen.getByTestId("workflow-recovery-run-start"),
    ).not.toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-run-start"));
  await waitFor(() => expect(onRun).toHaveBeenCalledOnce());
  await act(async () => {
    options.onEvent?.({
      kind: "run_started",
      run_log_path: "runs/owned/current.json",
      at: new Date().toISOString(),
      task_id: "",
      task_title: "Owned",
    });
    options.onEvent?.({
      kind: "step_started",
      at: new Date().toISOString(),
      task_id: "document_1",
      task_title: "Owned first step",
      execution_kind: "ai",
    });
  });
  get.mockResolvedValue([
    { ...snapshot("completed"), started_at: "2000-01-01T00:00:00Z" },
  ]);
  await focus();
  expect(
    screen.getByTestId("workflow-recovery-block-block.document-1"),
  ).toHaveAttribute("data-run-state", "running");
  expect(screen.getByTestId("workflow-recovery-run-cancel")).toBeVisible();
  await act(async () => {
    finish({
      outputPath: "owned.html",
      outputBytes: 22,
      taskTitle: "Owned",
      runLogPath: "runs/owned/current.json",
    });
  });
  expect(screen.getByTestId("workflow-native-run-summary")).toHaveTextContent(
    "Workflow completed",
  );
  expect(
    screen.getByTestId("workflow-recovery-run-details-toggle"),
  ).toHaveTextContent("owned.html");
  expect(onRun).toHaveBeenCalledOnce();
});

// A different existing workflow proves exact read-only evidence projection and
// source invalidation without any model, provider, approval, or execution calls.
it("attaches Robot Tracking Diagnosis evidence without a runner and retains real edited-source mismatch checks", async () => {
  const readLatest = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowRuns")
    .mockResolvedValue([]);
  const record = snapshot("completed");
  record.execution!.outputs = [
    {
      task_id: "align_and_measure_acceptance",
      task_title: "Align samples and calculate tracking metrics",
      output_path: "results/tracking-metrics.csv",
      output_format: "csv",
      output_bytes: 123,
    },
  ];
  const shared = {
    ...props,
    workflowSource: robotSource,
    workflowFilePath: "workflows/robot-tracking-diagnosis.workflow.wflow",
  };
  const { rerender } = render(
    <WorkflowRecoveryConcept {...shared} readOnlyRun={record} />,
  );
  fireEvent.click(
    screen.getByTestId(
      "workflow-recovery-block-block.align-and-measure-acceptance",
    ),
  );
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).toHaveTextContent("tracking-metrics.csv");
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).not.toHaveTextContent("different saved workflow");
  expect(screen.getByTestId("workflow-results-toggle")).toHaveTextContent(
    "1/1 available",
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-view-code"));
  const editor = screen.getByTestId("workflow-recovery-source-editor");
  fireEvent.change(editor, {
    target: {
      value: robotSource.replace(
        'name: "Robot Tracking Diagnosis"',
        'name: "Edited diagnosis"',
      ),
    },
  });
  fireEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
  fireEvent.click(screen.getByTestId("workflow-recovery-view-diagram"));
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).toHaveTextContent("different saved workflow");
  expect(screen.queryByText("Files produced in this run")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).not.toHaveTextContent("different saved workflow");
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).toHaveTextContent("tracking-metrics.csv");
  rerender(
    <WorkflowRecoveryConcept
      {...shared}
      readOnlyRun={{ ...record, source_digest: "f".repeat(64) }}
    />,
  );
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).toHaveTextContent("different saved workflow");
  rerender(<WorkflowRecoveryConcept {...shared} />);
  expect(
    screen.getByTestId("workflow-engineering-step-context"),
  ).not.toHaveTextContent("different saved workflow");
  expect(screen.queryByText("Files produced in this run")).toBeNull();
  expect(screen.getByTestId("workflow-results-toggle")).toHaveTextContent(
    "0/0 available",
  );
  expect(readLatest).not.toHaveBeenCalled();
  expect(screen.queryByTestId("workflow-recovery-run")).toBeNull();
});
