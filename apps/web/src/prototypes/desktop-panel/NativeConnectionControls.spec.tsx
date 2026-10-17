import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeConnectionControls } from "./NativeConnectionControls";

afterEach(cleanup);
const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "A",
  available: true,
  reason: null,
};
const scope = {
  workspace_id: "a",
  session_id: "chat-a",
  capability_id: "provider",
  server_id: "registered",
};
const state = {
  capability_id: "provider",
  server_id: "registered",
  shared_scope: "wright-host",
  control_digest: "a".repeat(64),
  installed: true,
  active: true,
  status: "active",
  bound_workspace_id: "a",
  tools: [
    {
      tool_id: "registered:inspect",
      name: "inspect",
      enabled: true,
      reported_read_only: true,
    },
  ],
};
const read = (extra = {}) => ({
  content: [],
  structuredContent: { ...scope, state: { ...state, ...extra } },
});
const changed = (
  operation: string,
  extra = {},
  toolId: string | null = null,
) => ({
  content: [],
  structuredContent: {
    ok: true,
    document: {
      ...scope,
      operation,
      tool_id: toolId,
      state: { ...state, control_digest: "b".repeat(64), ...extra },
    },
  },
});
function show(call = vi.fn().mockResolvedValue(read())) {
  const onChanged = vi.fn();
  const view = render(
    <NativeConnectionControls
      call={call}
      workspace={workspace}
      capabilityId="provider"
      serverId="registered"
      onChanged={onChanged}
    />,
  );
  fireEvent.click(screen.getByText("Provider controls"));
  return { call, onChanged, ...view };
}

it("reads exact scoped state on opening and marks the shared scope", async () => {
  const { call } = show();
  await screen.findByText(/Process: active/);
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_connection_controls",
    scope,
  );
  expect(screen.getByText(/shared across Wright workspaces/)).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Start for this workspace" }),
  ).toBeDisabled();
});

it("switches an exact tool once using the observed subject and refreshes its owner", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(read())
    .mockResolvedValue(
      changed(
        "tool-disable",
        { tools: [{ ...state.tools[0], enabled: false }] },
        "registered:inspect",
      ),
    );
  const { onChanged } = show(call);
  const checkbox = await screen.findByRole("checkbox", { name: /inspect/ });
  onChanged.mockClear();
  fireEvent.click(checkbox);
  fireEvent.click(checkbox);
  await screen.findByText(/Shared provider state updated/);
  expect(checkbox).not.toBeChecked();
  expect(call).toHaveBeenLastCalledWith("wright_connection_control", {
    request: {
      ...scope,
      shared_scope: "wright-host",
      control_digest: state.control_digest,
      operation: "tool-disable",
      tool_id: "registered:inspect",
    },
  });
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_control"),
  ).toHaveLength(1);
  expect(onChanged).toHaveBeenCalledOnce();
});

it.each(["lost reply", "wrong subject", "target not reached"])(
  "requires readback after %s and never repeats stop",
  async (failure) => {
    const call = vi
      .fn()
      .mockResolvedValueOnce(read())
      .mockImplementationOnce(() =>
        failure === "lost reply"
          ? Promise.reject(Error("lost"))
          : Promise.resolve(
              changed(
                "stop",
                failure === "wrong subject" ? { server_id: "other" } : {},
              ),
            ),
      )
      .mockResolvedValue(read({ active: false, status: "inactive" }));
    const { onChanged } = show(call);
    fireEvent.click(
      await screen.findByRole("button", { name: "Stop provider (shared)" }),
    );
    await screen.findByText(/Control outcome is not confirmed/);
    expect(
      screen.getByRole("button", { name: "Stop provider (shared)" }),
    ).toBeDisabled();
    expect(onChanged).toHaveBeenCalledTimes(1); // Initial authoritative read only.
    fireEvent.click(
      screen.getByRole("button", { name: "Refresh provider state" }),
    );
    await screen.findByText(/Process: inactive/);
    expect(
      screen.getByRole("button", { name: "Start for this workspace" }),
    ).toBeEnabled();
    expect(
      call.mock.calls.filter(([name]) => name === "wright_connection_control"),
    ).toHaveLength(1);
  },
);

it("distinguishes a rejected control and waits for explicit fresh state", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(read())
    .mockResolvedValue({
      content: [],
      structuredContent: { ok: false, error: { outcome_known: true } },
    });
  show(call);
  fireEvent.click(
    await screen.findByRole("button", { name: "Stop provider (shared)" }),
  );
  await screen.findByText(/Wright rejected this control/);
  expect(
    screen.getByRole("button", { name: "Stop provider (shared)" }),
  ).toBeDisabled();
});

it("does not accept another workspace's snapshot", async () => {
  show(
    vi.fn().mockResolvedValue({
      content: [],
      structuredContent: {
        ...read().structuredContent,
        workspace_id: "other",
      },
    }),
  );
  await screen.findByText(/Provider state could not be read/);
  expect(
    screen.queryByRole("button", { name: "Stop provider (shared)" }),
  ).toBeNull();
});

it("ignores late control replies after leaving the scoped panel", async () => {
  let finish!: (value: ReturnType<typeof changed>) => void;
  const call = vi
    .fn()
    .mockResolvedValueOnce(read())
    .mockReturnValueOnce(
      new Promise((resolve) => {
        finish = resolve;
      }),
    );
  const { onChanged, unmount } = show(call);
  fireEvent.click(
    await screen.findByRole("button", { name: "Stop provider (shared)" }),
  );
  await waitFor(() => expect(call).toHaveBeenCalledTimes(2));
  onChanged.mockClear();
  unmount();
  finish(changed("stop", { active: false, status: "inactive" }));
  await Promise.resolve();
  expect(onChanged).not.toHaveBeenCalled();
});

it("reviews shared uninstall before sending exactly one observed-subject operation", async () => {
  const call = vi.fn().mockResolvedValueOnce(read()).mockResolvedValue(changed("uninstall", {installed: false, active: false, status: "inactive"}));
  show(call);
  fireEvent.click(await screen.findByRole("button", {name: "Uninstall provider (shared)"}));
  expect(call).toHaveBeenCalledOnce();
  expect(screen.getByLabelText("Confirm provider uninstall")).toHaveTextContent(/Saved setup, credentials and downloaded packages are retained/);
  fireEvent.click(screen.getByRole("button", {name: "Keep provider"}));
  expect(call).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", {name: "Uninstall provider (shared)"}));
  fireEvent.click(screen.getByRole("button", {name: "Uninstall for all workspaces"}));
  await screen.findByText(/Shared provider state updated/);
  expect(call).toHaveBeenLastCalledWith("wright_connection_control", {request: {...scope, operation: "uninstall", shared_scope: "wright-host", control_digest: state.control_digest}});
  expect(call.mock.calls.filter(([name]) => name === "wright_connection_control")).toHaveLength(1);
  expect(screen.getByRole("button", {name: "Start for this workspace"})).toBeDisabled();
  expect(screen.getByRole("button", {name: "Uninstall provider (shared)"})).toBeDisabled();
});

it("an uncertain uninstall requires readback, never a second uninstall", async () => {
  const call = vi.fn().mockResolvedValueOnce(read()).mockRejectedValueOnce(new Error("lost reply")).mockResolvedValue(read({installed: false, active: false, status: "inactive"}));
  show(call);
  fireEvent.click(await screen.findByRole("button", {name: "Uninstall provider (shared)"}));
  fireEvent.click(screen.getByRole("button", {name: "Uninstall for all workspaces"}));
  await screen.findByText(/Control outcome is not confirmed/);
  expect(screen.getByRole("button", {name: "Uninstall provider (shared)"})).toBeDisabled();
  fireEvent.click(screen.getByRole("button", {name: "Refresh provider state"}));
  await screen.findByText(/Process: inactive/);
  expect(call.mock.calls.filter(([name]) => name === "wright_connection_control")).toHaveLength(1);
  expect(screen.getByRole("button", {name: "Start for this workspace"})).toBeDisabled();
});
