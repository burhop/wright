import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { NativeNewWorkflow } from "./NativeNewWorkflow";

afterEach(cleanup);
const workspace = {
  workspace_id: "one",
  session_id: "one-chat",
  workspace_name: "One",
  available: true,
  reason: null,
};
const receipt = (args: Record<string, unknown>) => ({
  content: [],
  structuredContent: {
    ...args,
    source: String(args.source) + "# owner materialized defaults\n",
    storage_digest: "a".repeat(64),
  },
});
function setup(call = vi.fn(), onOpen = vi.fn().mockResolvedValue(undefined)) {
  const onBusy = vi.fn();
  render(
    <NativeNewWorkflow
      workspace={workspace}
      call={call}
      onOpen={onOpen}
      onBusy={onBusy}
      disabled={false}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "New workflow" }));
  fireEvent.change(screen.getByLabelText("Workflow name"), {
    target: { value: 'Robot "review"' },
  });
  return { call, onOpen, onBusy };
}
it("creates an empty shared definition and opens its exact saved scope without execution", async () => {
  const call = vi.fn().mockImplementation(async (_name, args) => receipt(args));
  const { onOpen, onBusy } = setup(call);
  fireEvent.click(screen.getByRole("button", { name: "Create workflow" }));
  await waitFor(() => expect(onOpen).toHaveBeenCalledTimes(1));
  expect(call).toHaveBeenCalledTimes(1);
  const [name, args] = call.mock.calls[0];
  expect(name).toBe("wright_workflow_create");
  expect(args).toMatchObject({ workspace_id: "one", session_id: "one-chat" });
  expect(args.path).toMatch(
    /^workflows\/untitled-workflow-[\da-f-]+\.workflow\.wflow$/,
  );
  expect(args.source).toContain('name: "Robot \\"review\\""');
  expect(args.source).not.toContain("block ");
  expect(onOpen).toHaveBeenCalledWith(workspace, args.path);
  expect(onBusy).toHaveBeenLastCalledWith(false);
});
it("does not duplicate creation while pending or after a lost acknowledgement", async () => {
  let reject!: (reason: Error) => void;
  const call = vi.fn().mockReturnValue(
    new Promise((_resolve, no) => {
      reject = no;
    }),
  );
  const { onOpen } = setup(call);
  const button = screen.getByRole("button", { name: "Create workflow" });
  fireEvent.click(button);
  fireEvent.click(button);
  expect(call).toHaveBeenCalledTimes(1);
  reject(new Error("connection lost"));
  await screen.findByRole("alert");
  expect(button).toBeDisabled();
  expect(onOpen).not.toHaveBeenCalled();
});
it("reopens a confirmed saved workflow after navigation fails without creating it again", async () => {
  const call = vi.fn().mockImplementation(async (_name, args) => receipt(args));
  const onOpen = vi
    .fn()
    .mockRejectedValueOnce(new Error("read failed"))
    .mockResolvedValue(undefined);
  setup(call, onOpen);
  fireEvent.click(screen.getByRole("button", { name: "Create workflow" }));
  await screen.findByText(/Your workflow was saved/);
  fireEvent.click(screen.getByRole("button", { name: "Open saved workflow" }));
  await waitFor(() => expect(onOpen).toHaveBeenCalledTimes(2));
  expect(call).toHaveBeenCalledTimes(1);
  expect(onOpen.mock.calls[1]).toEqual(onOpen.mock.calls[0]);
});
it("rejects a receipt for another workspace", async () => {
  const call = vi
    .fn()
    .mockImplementation(async (_name, args) =>
      receipt({ ...args, workspace_id: "other" }),
    );
  const { onOpen } = setup(call);
  fireEvent.click(screen.getByRole("button", { name: "Create workflow" }));
  await screen.findByText(/Creation was not confirmed/);
  expect(onOpen).not.toHaveBeenCalled();
});

it.each(["sent", "unsupported", "uncertain"] as const)(
  "makes %s chat handoff visible without creating or running work",
  async (outcome) => {
    const onPlanInChat =
      outcome === "uncertain"
        ? vi.fn().mockRejectedValue(new Error("lost"))
        : vi.fn().mockResolvedValue(outcome);
    const call = vi.fn();
    const onOpen = vi.fn();
    render(
      <NativeNewWorkflow
        workspace={workspace}
        call={call}
        onOpen={onOpen}
        onBusy={vi.fn()}
        disabled={false}
        onPlanInChat={onPlanInChat}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "New workflow" }));
    const plan = screen.getByRole("button", { name: "Plan in Codex chat" });
    fireEvent.click(plan);
    fireEvent.click(plan);
    const message = await screen.findByRole(
      outcome === "uncertain" ? "alert" : "status",
    );
    expect(message).toHaveTextContent(
      outcome === "sent"
        ? "Continue in the Codex chat"
        : outcome === "unsupported"
          ? "cannot send"
          : "Delivery was not confirmed",
    );
    expect(onPlanInChat).toHaveBeenCalledExactlyOnceWith(workspace);
    expect(plan).toBeDisabled();
    expect(call).not.toHaveBeenCalled();
    expect(onOpen).not.toHaveBeenCalled();
  },
);
