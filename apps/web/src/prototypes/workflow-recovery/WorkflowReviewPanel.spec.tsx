import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  workspaceService,
  type WorkspaceWorkflowReview,
} from "../../services/workspace-service";
import { WorkflowReviewPanel, useWorkflowReviews } from "./WorkflowReviewPanel";
import { AUTHORING_TEMPLATES } from "./authoring-objects";

const review: WorkspaceWorkflowReview = {
  review_id: "review-1",
  package_digest: "package-sha",
  state: "pending",
  run_id: "run-1",
  workflow_path: "workflows/review.wflow",
  source_digest: "source-sha",
  task_id: "review",
  task_title: "Engineer review",
  instructions: "Check all dimensions and unresolved assumptions.",
  artifacts: [
    {
      output_path: "reports/brief-001.html",
      sha256: "artifact-sha",
      output_bytes: 128,
      output_format: "html",
      task_id: "draft",
      task_title: "Draft",
    },
  ],
  created_at: "2026-09-08T10:00:00Z",
  decided_at: null,
  actor: null,
  reason: null,
};
afterEach(() => vi.restoreAllMocks());

it("opens the exact indexed output in the existing viewer and shows evidence identity", () => {
  const open = vi.fn();
  render(
    <WorkflowReviewPanel
      review={review}
      sessionId="session"
      onOpenFile={open}
      onUpdate={vi.fn()}
      onRefresh={vi.fn()}
    />,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Open reports/brief-001.html" }),
  );
  expect(open).toHaveBeenCalledWith("reports/brief-001.html");
  expect(screen.getByText(review.instructions)).toBeVisible();
  fireEvent.click(screen.getByText("Reviewed package identity"));
  expect(screen.getByText("artifact-sha")).toBeVisible();
  expect(screen.getByText(/identity is not authenticated/)).toBeVisible();
});

it("requires change notes and sends only the chosen review and decision", async () => {
  const decide = vi
    .spyOn(workspaceService, "decideWorkspaceWorkflowReview")
    .mockResolvedValue({
      ...review,
      state: "changes_requested",
      reason: "Missing tolerance",
    });
  const update = vi.fn();
  render(
    <WorkflowReviewPanel
      review={review}
      sessionId="session"
      onUpdate={update}
      onRefresh={vi.fn()}
    />,
  );
  expect(
    screen.getByRole("button", { name: "Request changes" }),
  ).toBeDisabled();
  fireEvent.change(
    screen.getByLabelText("Review notes (required for changes)"),
    { target: { value: " Missing tolerance " } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Request changes" }));
  await waitFor(() => expect(update).toHaveBeenCalled());
  expect(decide).toHaveBeenCalledExactlyOnceWith(
    "session",
    review,
    "changes_requested",
    "Missing tolerance",
  );
});

it("keeps stale package feedback and disables repeated decisions until refresh", async () => {
  vi.spyOn(workspaceService, "decideWorkspaceWorkflowReview").mockRejectedValue(
    new Error("Reviewed file changed. Run again to create a new review."),
  );
  const refresh = vi.fn();
  render(
    <WorkflowReviewPanel
      review={review}
      sessionId="session"
      onUpdate={vi.fn()}
      onRefresh={refresh}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Approve" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Run again to create a new review",
  );
  expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Refresh reviews" }));
  expect(refresh).toHaveBeenCalledOnce();
});

it("shows a recorded decision without offering a second approval", () => {
  render(
    <WorkflowReviewPanel
      review={{ ...review, state: "approved", reason: "Checked" }}
      sessionId="session"
      onUpdate={vi.fn()}
      onRefresh={vi.fn()}
    />,
  );
  expect(screen.getByText(/Review approved/)).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "Approve" }),
  ).not.toBeInTheDocument();
});

it("shows persisted stale evidence and disables both decisions before submission", () => {
  const decide = vi.spyOn(workspaceService, "decideWorkspaceWorkflowReview");
  render(
    <WorkflowReviewPanel
      review={{
        ...review,
        evidence_status: "stale",
        evidence_message: "The reviewed output changed.",
      }}
      sessionId="session"
      onUpdate={vi.fn()}
      onRefresh={vi.fn()}
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent(
    "The reviewed output changed.",
  );
  fireEvent.change(
    screen.getByLabelText("Review notes (required for changes)"),
    { target: { value: "Fix dimensions" } },
  );
  expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Request changes" }),
  ).toBeDisabled();
  expect(decide).not.toHaveBeenCalled();
});

it("rehydrates reviews on reopen and ignores late results from another workflow", async () => {
  let finishOld!: (value: WorkspaceWorkflowReview[]) => void;
  const fetch = vi
    .spyOn(workspaceService, "getWorkspaceWorkflowReviews")
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishOld = resolve;
        }),
    )
    .mockResolvedValue([review]);
  function Harness({ path }: { path: string }) {
    const state = useWorkflowReviews("session", path, "reopen");
    return (
      <div>
        {state.reviews.map((item) => (
          <span key={item.review_id}>{item.review_id}</span>
        ))}
      </div>
    );
  }
  const { rerender } = render(<Harness path="workflows/old.wflow" />);
  rerender(<Harness path={review.workflow_path} />);
  expect(await screen.findByText("review-1")).toBeVisible();
  await act(async () => finishOld([{ ...review, review_id: "old-review" }]));
  expect(screen.queryByText("old-review")).not.toBeInTheDocument();
  expect(fetch).toHaveBeenLastCalledWith("session", review.workflow_path);
});

it("authors Engineer review as a terminal one-document step", () => {
  const template = AUTHORING_TEMPLATES.find(
    (item) => item.id === "manual-review",
  )!;
  expect(template.executionKind).toBe("human");
  expect(template.ports).toHaveLength(1);
  expect(template.ports[0]).toMatchObject({
    direction: "input",
    typeId: "type.document.engineering",
  });
});
