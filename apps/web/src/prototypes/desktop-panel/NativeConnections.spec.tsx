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
