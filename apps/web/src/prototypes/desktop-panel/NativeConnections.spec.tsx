import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeConnections } from "./NativeConnections";
const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const reply = (scope = "a") => ({
  content: [],
  structuredContent: {
    workspace_id: scope,
    session_id: "chat-a",
    next_cursor: null,
    connections: [
      {
        capability_id: "cad",
        server_id: "registered-cad",
        name: "CAD",
        description: "Design",
        installed: true,
        active: true,
        enabled_here: false,
        credentials_missing: false,
        process_status: "stopped",
        installed_version: null,
        compatibility: { status: "uncertain", reasons: [] },
      },
    ],
  },
});
afterEach(cleanup);

function enabledReply(enabled = true) {
  const result = reply();
  result.structuredContent.connections[0].enabled_here = enabled;
  return result;
}
function disabledReceipt(workspaceId = "a") {
  return {
    content: [],
    structuredContent: {
      workspace_id: workspaceId,
      session_id: "chat-a",
      availability: {
        workspace_id: workspaceId,
        capability_id: "cad",
        server_id: "registered-cad",
        enabled: false,
      },
    },
  };
}

it("disables the exact workspace connection once and retains provider setup", async () => {
  let finish!: (value: ReturnType<typeof disabledReceipt>) => void;
  const pending = new Promise<ReturnType<typeof disabledReceipt>>((resolve) => {
    finish = resolve;
  });
  const call = vi
    .fn()
    .mockResolvedValueOnce(enabledReply())
    .mockReturnValueOnce(pending);
  render(<NativeConnections workspace={workspace} call={call} />);
  const disable = await screen.findByRole("button", {
    name: "Disable CAD in this workspace",
  });
  fireEvent.click(disable);
  fireEvent.click(disable);
  expect(
    call.mock.calls.filter(([name]) => name === "wright_connection_disable"),
  ).toHaveLength(1);
  expect(call).toHaveBeenLastCalledWith("wright_connection_disable", {
    workspace_id: "a",
    session_id: "chat-a",
    capability_id: "cad",
    server_id: "registered-cad",
  });
  finish(disabledReceipt());
  expect(
    await screen.findByText("CAD is disabled in this workspace."),
  ).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "Disable CAD in this workspace" }),
  ).toBeNull();
  expect(
    screen.getByRole("button", { name: "Review setup for CAD" }),
  ).toBeVisible();
  expect(
    call.mock.calls.every(([name]) =>
      ["wright_connections_list", "wright_connection_disable"].includes(name),
    ),
  ).toBe(true);
});

it.each(["lost reply", "wrong scope"])(
  "reconciles %s through a read without repeating disable",
  async (failure) => {
    const call = vi
      .fn()
      .mockResolvedValueOnce(enabledReply())
      .mockImplementationOnce(() =>
        failure === "lost reply"
          ? Promise.reject(Error("Lost acknowledgement"))
          : Promise.resolve(disabledReceipt("other")),
      )
      .mockResolvedValue(enabledReply(false));
    render(<NativeConnections workspace={workspace} call={call} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Disable CAD in this workspace",
      }),
    );
    expect(
      await screen.findByText(/Disable outcome is not confirmed/),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Disable CAD in this workspace" }),
    ).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Search / refresh" }));
    expect(
      await screen.findByText(
        /Saved availability is confirmed: this connection is disabled/,
      ),
    ).toBeVisible();
    expect(
      call.mock.calls.filter(([name]) => name === "wright_connection_disable"),
    ).toHaveLength(1);
  },
);

it("shows catalog state without implying workspace grant or live health", async () => {
  const call = vi.fn().mockResolvedValue(reply());
  render(<NativeConnections workspace={workspace} call={call} />);
  expect(
    await screen.findByText("Not enabled in this workspace"),
  ).toBeVisible();
  fireEvent.click(screen.getByText("Readiness details"));
  expect(screen.getByText(/Process: stopped/)).toBeVisible();
  expect(
    screen.getByText(/never approves individual tool actions/),
  ).toBeVisible();
  expect(call).toHaveBeenCalledWith("wright_connections_list", {
    workspace_id: "a",
    session_id: "chat-a",
    search: "",
  });
});

it("shows workspace permission even when an enabled provider needs credentials", async () => {
  const data = enabledReply();
  data.structuredContent.connections[0].active = false;
  data.structuredContent.connections[0].credentials_missing = true;
  const call = vi.fn().mockResolvedValue(data);
  render(<NativeConnections workspace={workspace} call={call} />);
  expect(
    await screen.findByText("Sign-in or credentials needed"),
  ).toBeVisible();
  expect(screen.getByText("Enabled in this workspace")).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Disable CAD in this workspace" }),
  ).toBeEnabled();
});
it("rejects mismatched scope and permits an explicit search retry", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply("other"))
    .mockResolvedValue(reply());
  render(<NativeConnections workspace={workspace} call={call} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "could not be read",
  );
  expect(screen.queryByText("CAD")).toBeNull();
  expect(screen.queryByText("No matching connections.")).toBeNull();
  fireEvent.change(screen.getByLabelText("Find an MCP"), {
    target: { value: "CAD" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Search / refresh" }));
  expect(await screen.findByText("CAD")).toBeVisible();
  expect(call).toHaveBeenLastCalledWith("wright_connections_list", {
    workspace_id: "a",
    session_id: "chat-a",
    search: "CAD",
  });
});

it("prepares a workspace plan only after an explicit click without applying it", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply())
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        plan: {
          plan_id: "plan",
          capability_id: "cad",
          workspace_id: "a",
          requested_scope: "workspace",
          state: "blocked",
          effects: [],
          blocking_reasons: [
            {
              code: "login",
              message: "Account sign-in required",
              recovery: "Use the account setup",
            },
          ],
        },
      },
    });
  render(<NativeConnections workspace={workspace} call={call} />);
  const button = await screen.findByRole("button", {
    name: "Review setup for CAD",
  });
  expect(call).toHaveBeenCalledTimes(1);
  fireEvent.click(button);
  expect(
    await screen.findByText(/Nothing has been installed or approved/),
  ).toBeVisible();
  expect(screen.getByText(/Account sign-in required/)).toBeVisible();
  expect(call).toHaveBeenLastCalledWith("wright_connection_plan", {
    workspace_id: "a",
    session_id: "chat-a",
    capability_id: "cad",
    independently_completed_license: false,
  });
  expect(call).toHaveBeenCalledTimes(2);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Review setup for CAD" }));
  expect(call).toHaveBeenLastCalledWith("wright_connection_plan", {
    workspace_id: "a",
    session_id: "chat-a",
    capability_id: "cad",
    independently_completed_license: true,
  });
  await screen.findByRole("alert");
});

it("reconciles a lost apply acknowledgement with reads only", async () => {
  const plan = {
    plan_id: "p",
    plan_digest: "a".repeat(64),
    capability_id: "cad",
    workspace_id: "a",
    requested_scope: "workspace",
    state: "approved",
    effects: [],
    blocking_reasons: [],
  };
  const scoped = (value: typeof plan) => ({
    content: [],
    structuredContent: { workspace_id: "a", session_id: "chat-a", plan: value },
  });
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply())
    .mockResolvedValueOnce(scoped(plan))
    .mockRejectedValueOnce(Error("acknowledgement lost"))
    .mockResolvedValueOnce(scoped({ ...plan, state: "completed" }))
    .mockResolvedValue(reply());
  render(<NativeConnections workspace={workspace} call={call} />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Review setup for CAD" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Apply approved setup" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "outcome is not confirmed",
  );
  expect(
    screen.getByRole("button", { name: "Apply approved setup" }),
  ).toBeDisabled();
  expect(
    call.mock.calls.filter(
      (args) => args[0] === "wright_connection_plan_update",
    ),
  ).toHaveLength(1);
  fireEvent.click(
    screen.getByRole("button", { name: "Check saved setup status" }),
  );
  expect(await screen.findByText(/Registration completed/)).toBeVisible();
  expect(
    call.mock.calls.filter(
      (args) => args[0] === "wright_connection_plan_update",
    ),
  ).toHaveLength(1);
  expect(call).toHaveBeenCalledWith("wright_connection_plan_read", {
    workspace_id: "a",
    session_id: "chat-a",
    plan_id: "p",
  });
});

it("shows saved validation as historical evidence without retrying validation", async () => {
  const data = reply();
  Object.assign(data.structuredContent.connections[0], {
    local_validation: {
      evidence_id: "v1",
      state: "passed",
      observed_at: "2026-10-14T00:00:00Z",
      reason_codes: [],
    },
  });
  const call = vi.fn().mockResolvedValue(data);
  render(<NativeConnections workspace={workspace} call={call} />);
  await screen.findByText("CAD");
  fireEvent.click(screen.getByText("Readiness details"));
  expect(
    screen.getByText("Last recorded protocol validation: passed."),
  ).toBeVisible();
  expect(screen.getByText(/does not confirm current readiness/)).toBeVisible();
  expect(call).toHaveBeenCalledTimes(1);
  expect(call.mock.calls[0][0]).toBe("wright_connections_list");
});

it("reopens an existing setup through reads only", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply())
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        capability_id: "cad",
        plans: [
          {
            plan_id: "saved",
            capability_id: "cad",
            workspace_id: "a",
            state: "completed",
            created_at: "2026-10-14",
          },
        ],
      },
    })
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        plan: {
          plan_id: "saved",
          plan_digest: "a".repeat(64),
          capability_id: "cad",
          workspace_id: "a",
          requested_scope: "workspace",
          state: "completed",
          effects: [],
          blocking_reasons: [],
        },
      },
    });
  render(<NativeConnections workspace={workspace} call={call} />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Saved setup for CAD" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: /Open completed setup/ }),
  );
  expect(await screen.findByText("Plan state: completed.")).toBeVisible();
  expect(call.mock.calls.map(([name]) => name)).toEqual([
    "wright_connections_list",
    "wright_connection_plans",
    "wright_connection_plan_read",
  ]);
});

it("recovers an imported setup without its provider identity and opens the exact saved plan", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply())
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        capability_id: null,
        plans: [
          {
            plan_id: "imported",
            capability_id: "import:custom",
            workspace_id: "a",
            state: "blocked",
            created_at: "2026-10-15",
          },
        ],
      },
    })
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        plan: {
          plan_id: "imported",
          plan_digest: "b".repeat(64),
          capability_id: "import:custom",
          workspace_id: "a",
          requested_scope: "workspace",
          state: "blocked",
          effects: [],
          blocking_reasons: [],
        },
      },
    });
  render(<NativeConnections workspace={workspace} call={call} />);
  await screen.findByText("CAD");
  fireEvent.click(
    screen.getByRole("button", { name: "Saved setup in this workspace" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: /Open blocked setup/ }),
  );
  expect(await screen.findByText("Plan state: blocked.")).toBeVisible();
  expect(call.mock.calls.slice(1)).toEqual([
    ["wright_connection_plans", { workspace_id: "a", session_id: "chat-a" }],
    [
      "wright_connection_plan_read",
      { workspace_id: "a", session_id: "chat-a", plan_id: "imported" },
    ],
  ]);
});

it("rejects another workspace in an unfiltered saved-plan response", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(reply())
    .mockResolvedValueOnce({
      content: [],
      structuredContent: {
        workspace_id: "a",
        session_id: "chat-a",
        capability_id: null,
        plans: [
          {
            plan_id: "private",
            capability_id: "import:custom",
            workspace_id: "b",
            state: "completed",
            created_at: "2026-10-15",
          },
        ],
      },
    });
  render(<NativeConnections workspace={workspace} call={call} />);
  await screen.findByText("CAD");
  fireEvent.click(
    screen.getByRole("button", { name: "Saved setup in this workspace" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Saved setup could not be read",
  );
  expect(
    screen.queryByRole("button", { name: /Open completed setup/ }),
  ).toBeNull();
});
