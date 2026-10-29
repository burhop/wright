import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NativePendingWork } from "./NativePendingWork";

afterEach(cleanup);
const workspace = {
  workspace_id: "w",
  session_id: "s",
  workspace_name: "Handle",
  available: true,
  reason: null,
};
const item = {
  checkpoint_id: "c1",
  workflow_path: "workflows/handle.wflow",
  run_id: "r1",
  path: "runs/r1.json",
  source_digest: "a".repeat(64),
  step_title: "Review dimensions",
  state: "pending",
  action_kind: "local_review",
};
const response = (
  items: Record<string, unknown>[] = [item],
  id = "w",
  next: string | null = null,
) => ({
  content: [],
  structuredContent: {
    workspace_id: id,
    session_id: "s",
    checkpoints: { items, next_cursor: next },
    reviews: { items: [] as Record<string, unknown>[], next_cursor: null },
  },
});

it("shows the engineer's title and opens exactly the recorded run without a resume call", async () => {
  const call = vi.fn().mockResolvedValue(response());
  const onOpen = vi.fn().mockResolvedValue(undefined);
  render(
    <NativePendingWork
      workspace={workspace}
      call={call}
      titles={{ [item.workflow_path]: "Replacement handle" }}
      onOpen={onOpen}
    />,
  );
  await screen.findByText("Replacement handle");
  expect(screen.getByText("Review results · Review dimensions")).toBeVisible();
  expect(onOpen).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Open run" }));
  await waitFor(() =>
    expect(onOpen).toHaveBeenCalledExactlyOnceWith(item.workflow_path, {
      run_id: "r1",
      path: "runs/r1.json",
      source_digest: "a".repeat(64),
      status: "pending",
      started_at: null,
    }),
  );
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workspace_pending", {
    workspace_id: "w",
    session_id: "s",
    checkpoint_after: "",
    review_after: "",
  });
});

it("suppresses delayed responses from the previous workspace", async () => {
  let finish!: (value: ReturnType<typeof response>) => void;
  const call = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    )
    .mockResolvedValue(response([], "new"));
  const props = { call, titles: {}, onOpen: vi.fn() };
  const view = render(<NativePendingWork workspace={workspace} {...props} />);
  view.rerender(
    <NativePendingWork
      workspace={{ ...workspace, workspace_id: "new" }}
      {...props}
    />,
  );
  await waitFor(() =>
    expect(screen.queryByRole("status")).not.toBeInTheDocument(),
  );
  finish(response());
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(screen.queryByText(/Review dimensions/)).not.toBeInTheDocument();
  expect(props.onOpen).not.toHaveBeenCalled();
});

it("does not disguise a failed read as an empty queue", async () => {
  render(
    <NativePendingWork
      workspace={workspace}
      call={vi.fn().mockResolvedValue({ isError: true })}
      titles={{}}
      onOpen={vi.fn()}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not check");
  expect(
    screen.getByRole("button", { name: "Refresh attention list" }),
  ).toBeEnabled();
});

it("labels approval as ready but keeps the button navigation-only", async () => {
  const call = vi
    .fn()
    .mockResolvedValue(
      response([
        { ...item, state: "approved", action_kind: "printer_transfer" },
      ]),
    );
  const onOpen = vi
    .fn()
    .mockRejectedValue(new Error("Subject changed elsewhere"));
  render(
    <NativePendingWork
      workspace={workspace}
      call={call}
      titles={{}}
      onOpen={onOpen}
    />,
  );
  await screen.findByText("Ready to continue · Review dimensions");
  fireEvent.click(screen.getByRole("button", { name: "Open run" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "This run could not be opened",
  );
  expect(call).toHaveBeenCalledTimes(1);
});

it("keeps the entry compact and reveals other waits only on request", async () => {
  const items = Array.from({ length: 5 }, (_, i) => ({
    ...item,
    checkpoint_id: `c${i}`,
    step_title: `Decision ${i}`,
  }));
  render(
    <NativePendingWork
      workspace={workspace}
      call={vi.fn().mockResolvedValue(response(items))}
      titles={{}}
      onOpen={vi.fn()}
    />,
  );
  await screen.findByText("Review results · Decision 0");
  expect(screen.getAllByRole("button", { name: "Open run" })).toHaveLength(3);
  fireEvent.click(screen.getByRole("button", { name: "Show more" }));
  expect(screen.getAllByRole("button", { name: "Open run" })).toHaveLength(5);
});

it("advances exhausted owner cursors rather than repeating the first page", async () => {
  const first = response([item], "w", "c1");
  first.structuredContent.reviews.items = [
    { ...item, checkpoint_id: undefined, review_id: "review1" },
  ];
  const call = vi
    .fn()
    .mockResolvedValueOnce(first)
    .mockResolvedValue(response([{ ...item, checkpoint_id: "c2" }]));
  render(
    <NativePendingWork
      workspace={workspace}
      call={call}
      titles={{}}
      onOpen={vi.fn()}
    />,
  );
  fireEvent.click(await screen.findByRole("button", { name: "Next page" }));
  await waitFor(() =>
    expect(call).toHaveBeenLastCalledWith("wright_workspace_pending", {
      workspace_id: "w",
      session_id: "s",
      checkpoint_after: "c1",
      review_after: "review1",
    }),
  );
});

it("does not display records returned for another workspace", async () => {
  render(
    <NativePendingWork
      workspace={workspace}
      call={vi.fn().mockResolvedValue(response([item], "foreign"))}
      titles={{}}
      onOpen={vi.fn()}
    />,
  );
  await screen.findByRole("alert");
  expect(
    screen.queryByRole("button", { name: "Open run" }),
  ).not.toBeInTheDocument();
});

it("distinguishes an unanswered input from an expired review", async () => {
  const questions = [
    {
      ...item,
      checkpoint_id: "input",
      checkpoint_kind: "input",
      action_kind: "human_input",
      step_title: "Supply load",
    },
    { ...item, checkpoint_id: "expired", expires_at: 1 },
  ];
  render(
    <NativePendingWork
      workspace={workspace}
      call={vi.fn().mockResolvedValue(response(questions))}
      titles={{}}
      onOpen={vi.fn()}
    />,
  );
  await screen.findByText("Provide information · Supply load");
  expect(
    screen.getByText(
      "Review expired — open run for next steps · Review dimensions",
    ),
  ).toBeVisible();
  expect(screen.getAllByRole("button", { name: "Open run" })).toHaveLength(2);
});
