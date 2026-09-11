import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspacePage } from "../src/components/pages/WorkspacePage";

const getWorkspace = vi.fn();
const activateWorkspace = vi.fn();
const logger = vi.hoisted(() => ({ info: vi.fn(), error: vi.fn() }));
let activationQueue = Promise.resolve<void>(undefined);

vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getWorkspace: (...args: unknown[]) => getWorkspace(...args),
    activateWorkspace: (...args: unknown[]) => {
      const request = activationQueue.then(() => activateWorkspace(...args));
      activationQueue = request.then(
        () => undefined,
        () => undefined,
      );
      return request;
    },
  },
}));

vi.mock("../src/hooks/useLogger", () => ({
  default: () => logger,
}));

vi.mock("../src/components/chat/WorkspacePanel", () => ({
  default: ({
    workspace,
  }: {
    workspace: { workspace_id: string; local_path: string };
  }) => (
    <div
      data-testid="workspace-panel-stub"
      data-workspace-id={workspace.workspace_id}
    >
      {workspace.local_path}
    </div>
  ),
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

function WorkspaceRouteHarness() {
  const navigate = useNavigate();
  return (
    <>
      <button
        type="button"
        data-testid="go-workspace-b"
        onClick={() => navigate("/workspace/workspace-b")}
      >
        Open B
      </button>
      <Routes>
        <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
      </Routes>
    </>
  );
}

function WorkspaceUnmountHarness() {
  const navigate = useNavigate();
  return (
    <>
      <button
        type="button"
        data-testid="leave-workspace"
        onClick={() => navigate("/")}
      >
        Leave workspace
      </button>
      <button
        type="button"
        data-testid="open-workspace-b"
        onClick={() => navigate("/workspace/workspace-b")}
      >
        Open B
      </button>
      <Routes>
        <Route
          path="/"
          element={<div data-testid="dashboard-stub">Dashboard</div>}
        />
        <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
      </Routes>
    </>
  );
}

describe("WorkspacePage", () => {
  beforeEach(() => {
    getWorkspace.mockReset();
    activateWorkspace.mockReset();
    activationQueue = Promise.resolve();
  });

  it("does not reload the workspace after activation", async () => {
    getWorkspace.mockResolvedValue({
      workspace_id: "workspace-1",
      session_id: "session-1",
      local_path: "C:/workspaces/demo",
    });
    activateWorkspace.mockResolvedValue(true);

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("workspace-panel-stub")).toHaveTextContent(
      "C:/workspaces/demo",
    );
    // Depending on the suite renderer, React may exercise a development
    // remount. Every activation must reuse the workspace from its matching
    // read; the old implementation issued one additional read per activation.
    expect(getWorkspace.mock.calls.length).toBe(
      activateWorkspace.mock.calls.length,
    );
    expect(getWorkspace.mock.calls.length).toBeGreaterThan(0);
    expect(getWorkspace.mock.calls.length).toBeLessThanOrEqual(2);
  });

  it("explains when a legacy workspace is blocked for application safety", async () => {
    getWorkspace.mockRejectedValue(
      new Error(
        "Workspace access blocked because its path overlaps Wright application files.",
      ),
    );

    render(
      <MemoryRouter initialEntries={["/workspace/unsafe-workspace"]}>
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Workspace Blocked")).toBeInTheDocument();
    expect(
      screen.getByText(/overlaps Wright application files/i),
    ).toBeVisible();
    expect(activateWorkspace).not.toHaveBeenCalled();
  });

  it("never exposes the prior workspace while a reused route loads a missing workspace", async () => {
    const workspaceB = deferred<never>();
    getWorkspace.mockImplementation((workspaceId: string) =>
      workspaceId === "workspace-a"
        ? Promise.resolve({
            workspace_id: "workspace-a",
            session_id: "session-a",
            local_path: "C:/workspaces/a",
          })
        : workspaceB.promise,
    );
    activateWorkspace.mockResolvedValue(true);

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-a"]}>
        <WorkspaceRouteHarness />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("workspace-panel-stub")).toHaveAttribute(
      "data-workspace-id",
      "workspace-a",
    );

    fireEvent.click(screen.getByTestId("go-workspace-b"));
    expect(
      screen.queryByTestId("workspace-panel-stub"),
    ).not.toBeInTheDocument();
    await act(async () => {
      workspaceB.reject(new Error("Workspace B does not exist."));
    });
    expect(await screen.findByText("Workspace Not Found")).toBeVisible();
    expect(
      screen.queryByTestId("workspace-panel-stub"),
    ).not.toBeInTheDocument();
  });

  it("ignores a late response from the prior workspace after a valid route transition", async () => {
    const workspaceA = deferred<{
      workspace_id: string;
      session_id: string;
      local_path: string;
    }>();
    const workspaceB = deferred<{
      workspace_id: string;
      session_id: string;
      local_path: string;
    }>();
    getWorkspace.mockImplementation((workspaceId: string) =>
      workspaceId === "workspace-a" ? workspaceA.promise : workspaceB.promise,
    );
    activateWorkspace.mockResolvedValue(true);

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-a"]}>
        <WorkspaceRouteHarness />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(getWorkspace).toHaveBeenCalledWith("workspace-a"),
    );
    fireEvent.click(screen.getByTestId("go-workspace-b"));
    await waitFor(() =>
      expect(getWorkspace).toHaveBeenCalledWith("workspace-b"),
    );

    await act(async () => {
      workspaceB.resolve({
        workspace_id: "workspace-b",
        session_id: "session-b",
        local_path: "C:/workspaces/b",
      });
    });
    expect(await screen.findByTestId("workspace-panel-stub")).toHaveAttribute(
      "data-workspace-id",
      "workspace-b",
    );

    await act(async () => {
      workspaceA.resolve({
        workspace_id: "workspace-a",
        session_id: "session-a",
        local_path: "C:/workspaces/a",
      });
    });
    expect(screen.getByTestId("workspace-panel-stub")).toHaveAttribute(
      "data-workspace-id",
      "workspace-b",
    );
    expect(activateWorkspace).not.toHaveBeenCalledWith("session-a");
  });

  it("serializes in-flight activation so the latest workspace owns runtime context", async () => {
    const activationA = deferred<boolean>();
    const activationB = deferred<boolean>();
    const completedActivations: string[] = [];
    getWorkspace.mockImplementation((workspaceId: string) =>
      Promise.resolve(
        workspaceId === "workspace-a"
          ? {
              workspace_id: "workspace-a",
              session_id: "session-a",
              local_path: "C:/workspaces/a",
            }
          : {
              workspace_id: "workspace-b",
              session_id: "session-b",
              local_path: "C:/workspaces/b",
            },
      ),
    );
    activateWorkspace.mockImplementation((sessionId: string) => {
      const pending =
        sessionId === "session-a" ? activationA.promise : activationB.promise;
      return pending.then((result) => {
        completedActivations.push(sessionId);
        return result;
      });
    });

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-a"]}>
        <WorkspaceRouteHarness />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(activateWorkspace).toHaveBeenCalledWith("session-a"),
    );

    fireEvent.click(screen.getByTestId("go-workspace-b"));
    await waitFor(() =>
      expect(getWorkspace).toHaveBeenCalledWith("workspace-b"),
    );
    expect(activateWorkspace).not.toHaveBeenCalledWith("session-b");
    expect(
      screen.queryByTestId("workspace-panel-stub"),
    ).not.toBeInTheDocument();

    await act(async () => {
      activationA.resolve(true);
    });
    await waitFor(() =>
      expect(activateWorkspace).toHaveBeenCalledWith("session-b"),
    );
    expect(completedActivations).toEqual(["session-a"]);
    expect(
      screen.queryByTestId("workspace-panel-stub"),
    ).not.toBeInTheDocument();

    await act(async () => {
      activationB.resolve(true);
    });
    expect(await screen.findByTestId("workspace-panel-stub")).toHaveAttribute(
      "data-workspace-id",
      "workspace-b",
    );
    expect(completedActivations).toEqual(["session-a", "session-b"]);
  });

  it("keeps activation ordered across workspace page unmount and remount", async () => {
    const activationA = deferred<boolean>();
    const activationB = deferred<boolean>();
    const completedActivations: string[] = [];
    getWorkspace.mockImplementation((workspaceId: string) =>
      Promise.resolve(
        workspaceId === "workspace-a"
          ? {
              workspace_id: "workspace-a",
              session_id: "session-a",
              local_path: "C:/workspaces/a",
            }
          : {
              workspace_id: "workspace-b",
              session_id: "session-b",
              local_path: "C:/workspaces/b",
            },
      ),
    );
    activateWorkspace.mockImplementation((sessionId: string) => {
      const pending =
        sessionId === "session-a" ? activationA.promise : activationB.promise;
      return pending.then((result) => {
        completedActivations.push(sessionId);
        return result;
      });
    });

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-a"]}>
        <WorkspaceUnmountHarness />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(activateWorkspace).toHaveBeenCalledWith("session-a"),
    );

    fireEvent.click(screen.getByTestId("leave-workspace"));
    expect(await screen.findByTestId("dashboard-stub")).toBeVisible();
    fireEvent.click(screen.getByTestId("open-workspace-b"));
    await waitFor(() =>
      expect(getWorkspace).toHaveBeenCalledWith("workspace-b"),
    );
    expect(activateWorkspace).not.toHaveBeenCalledWith("session-b");

    await act(async () => {
      activationA.resolve(true);
    });
    await waitFor(() =>
      expect(activateWorkspace).toHaveBeenCalledWith("session-b"),
    );
    expect(completedActivations).toEqual(["session-a"]);

    await act(async () => {
      activationB.resolve(true);
    });
    expect(await screen.findByTestId("workspace-panel-stub")).toHaveAttribute(
      "data-workspace-id",
      "workspace-b",
    );
    expect(completedActivations).toEqual(["session-a", "session-b"]);
  });

  it("rejects a mismatched workspace identity before activation", async () => {
    getWorkspace.mockResolvedValue({
      workspace_id: "workspace-elsewhere",
      session_id: "session-elsewhere",
      local_path: "C:/workspaces/elsewhere",
    });

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Workspace Not Found")).toBeVisible();
    expect(
      screen.getByText(/different workspace than the one requested/i),
    ).toBeVisible();
    expect(activateWorkspace).not.toHaveBeenCalled();
  });

  it("fails closed when the backend declines workspace activation", async () => {
    getWorkspace.mockResolvedValue({
      workspace_id: "workspace-1",
      session_id: "session-1",
      local_path: "C:/workspaces/demo",
    });
    activateWorkspace.mockResolvedValue(false);

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Workspace Not Found")).toBeVisible();
    expect(
      screen.getByText(/could not activate this workspace session/i),
    ).toBeVisible();
    expect(
      screen.queryByTestId("workspace-panel-stub"),
    ).not.toBeInTheDocument();
  });
});
