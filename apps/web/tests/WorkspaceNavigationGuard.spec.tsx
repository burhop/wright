import { useReducer } from "react";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  createMemoryRouter,
  Link,
  Outlet,
  RouterProvider,
  useLocation,
} from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspaceNavigationGuard } from "../src/components/chat/WorkspaceNavigationGuard";
import type { EditorTab } from "../src/store/viewer";

const viewer = vi.hoisted(() => ({
  openTabs: [] as EditorTab[],
  setTabDirty: vi.fn(),
}));
vi.mock("../src/store/viewer", () => ({ useViewerPanel: () => viewer }));

function Layout() {
  const [, update] = useReducer((n) => n + 1, 0);
  return (
    <>
      <WorkspaceNavigationGuard />
      <button
        onClick={() => {
          viewer.openTabs = viewer.openTabs.map((tab) => ({
            ...tab,
            isDirty: false,
          }));
          update();
        }}
      >
        Finish pending save
      </button>
      <Outlet />
    </>
  );
}
function Workspace() {
  const location = useLocation();
  return (
    <>
      <div data-testid="location">
        {location.pathname}
        {location.search}
      </div>
      <input aria-label="Draft" defaultValue="Retained unsaved text" />
      <Link to="/">Back to Dashboard</Link>
      <Link to="/workspace/two?workflow=canonical">Other workspace</Link>
      <Link to="/workspace/one?workflow=canonical&workflowPath=other.wflow">
        Other workflow tab
      </Link>
      <Link to="/settings">Settings</Link>
    </>
  );
}

describe("Workspace navigation protection", () => {
  let router: ReturnType<typeof createMemoryRouter>;
  const start = (entries = ["/workspace/one?workflow=canonical"]) => {
    router = createMemoryRouter(
      [
        {
          element: <Layout />,
          children: [
            { path: "/", element: <p>Dashboard destination</p> },
            { path: "/workspace/:workspaceId", element: <Workspace /> },
            { path: "/settings", element: <p>Settings destination</p> },
          ],
        },
      ],
      { initialEntries: entries, initialIndex: entries.length - 1 },
    );
    return render(<RouterProvider router={router} />);
  };
  beforeEach(() => {
    viewer.openTabs = [
      {
        path: "/workflows/design.wflow",
        name: "design.wflow",
        type: "workflow",
        isDirty: true,
      },
    ];
    viewer.setTabDirty.mockReset().mockImplementation((path, isDirty) => {
      viewer.openTabs = viewer.openTabs.map((tab) =>
        tab.path === path ? { ...tab, isDirty } : tab,
      );
    });
  });
  afterEach(() => {
    cleanup();
    router?.dispose();
  });

  it("keeps the exact editor mounted on cancelled dashboard navigation", async () => {
    start();
    const user = userEvent.setup();
    const draft = screen.getByLabelText("Draft");
    await user.type(draft, " with edits");
    await user.click(screen.getByRole("link", { name: "Back to Dashboard" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent(
      "workflows/design.wflow",
    );
    expect(screen.getByRole("button", { name: "Keep editing" })).toHaveFocus();
    expect(router.state.location.pathname).toBe("/workspace/one");
    await user.click(screen.getByRole("button", { name: "Keep editing" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByLabelText("Draft")).toBe(draft);
    expect(draft).toHaveValue("Retained unsaved text with edits");
    expect(viewer.setTabDirty).not.toHaveBeenCalled();
  });

  it("protects background drafts when switching workspace and follows the exact destination only after discard", async () => {
    viewer.openTabs.push({
      path: "/workflows/background.wflow",
      name: "background.wflow",
      type: "workflow",
      isDirty: true,
    });
    viewer.openTabs.push({
      path: "/notes.txt",
      name: "notes.txt",
      type: "code",
      isDirty: true,
    });
    start();
    const user = userEvent.setup();
    await user.click(screen.getByRole("link", { name: "Other workspace" }));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("workflows/background.wflow");
    expect(dialog).not.toHaveTextContent("notes.txt");
    await user.keyboard("{Escape}");
    expect(router.state.location.pathname).toBe("/workspace/one");
    await user.click(screen.getByRole("link", { name: "Other workspace" }));
    await user.click(
      screen.getByRole("button", { name: "Discard changes and leave" }),
    );
    await waitFor(() =>
      expect(router.state.location.pathname).toBe("/workspace/two"),
    );
    expect(router.state.location.search).toBe("?workflow=canonical");
    expect(viewer.setTabDirty.mock.calls).toEqual([
      ["/workflows/design.wflow", false],
      ["/workflows/background.wflow", false],
    ]);
  });

  it("allows tab and working-view query navigation in the same workspace", async () => {
    start();
    await userEvent.click(
      screen.getByRole("link", { name: "Other workflow tab" }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(router.state.location.search).toContain("workflowPath=other.wflow");
    await act(() =>
      router.navigate("/workspace/one?processView=common#result"),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(viewer.setTabDirty).not.toHaveBeenCalled();
  });

  it("blocks browser Back and supports cancelling then explicitly continuing it", async () => {
    start(["/", "/workspace/one"]);
    await act(() => router.navigate(-1));
    expect(await screen.findByRole("dialog")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Keep editing" }));
    expect(router.state.location.pathname).toBe("/workspace/one");
    await act(() => router.navigate(-1));
    await userEvent.click(
      screen.getByRole("button", { name: "Discard changes and leave" }),
    );
    expect(await screen.findByText("Dashboard destination")).toBeVisible();
  });

  it("does not prompt for clean workflow tabs", async () => {
    viewer.openTabs[0].isDirty = false;
    start();
    await userEvent.click(screen.getByRole("link", { name: "Settings" }));
    expect(await screen.findByText("Settings destination")).toBeVisible();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("holds departure while a save is pending even if the dirty flag cleared", async () => {
    viewer.openTabs[0].isDirty = false;
    viewer.openTabs[0].isSaving = true;
    start();
    const user = userEvent.setup();
    await user.click(screen.getByRole("link", { name: "Back to Dashboard" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent(
      "Wait for saving to finish",
    );
    expect(
      screen.getByRole("button", { name: "Discard changes and leave" }),
    ).toBeDisabled();
    const keep = screen.getByRole("button", { name: "Keep editing" });
    expect(keep).toHaveFocus();
    await user.tab();
    expect(keep).toHaveFocus();
    expect(router.state.location.pathname).toBe("/workspace/one");
    await user.click(keep);
    expect(viewer.setTabDirty).not.toHaveBeenCalled();
  });

  it("clears a stale choice if a pending save completes without navigating automatically", async () => {
    start();
    const user = userEvent.setup();
    await user.click(screen.getByRole("link", { name: "Back to Dashboard" }));
    expect(await screen.findByRole("dialog")).toBeVisible();
    // Emulates the already-running save completing, not an action behind the modal.
    await user.click(
      screen.getByRole("button", { name: "Finish pending save" }),
    );
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(router.state.location.pathname).toBe("/workspace/one");
    await user.click(screen.getByRole("link", { name: "Back to Dashboard" }));
    expect(await screen.findByText("Dashboard destination")).toBeVisible();
  });
});
