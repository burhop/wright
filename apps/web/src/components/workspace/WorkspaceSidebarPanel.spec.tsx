import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { WorkspaceSidebarPanel } from "./WorkspaceSidebarPanel";
import { WorkspaceLayout } from "./WorkspaceLayout";
import { createWorkspaceLayout } from "./workspace-layout";

describe("workspace compact navigation", () => {
  it("keeps desktop navigation docked without drawer controls", () => {
    render(<WorkspaceSidebarPanel compact={false} open width={260} onClose={vi.fn()}>
      <button>Existing file</button>
    </WorkspaceSidebarPanel>);
    expect(screen.getByTestId("workspace-sidebar")).toHaveStyle({ display: "flex", gridColumn: "2" });
    expect(screen.queryByRole("button", { name: "Close workspace navigation" })).toBeNull();
    expect(screen.queryByTestId("workspace-sidebar-backdrop")).toBeNull();
  });

  it("overlays compact navigation and closes through Escape with focus restored", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const initiator = document.createElement("button");
    initiator.textContent = "Files";
    document.body.append(initiator);
    initiator.focus();
    const { rerender } = render(<WorkspaceSidebarPanel compact open width={260} onClose={onClose}>
      <button>Existing file</button>
    </WorkspaceSidebarPanel>);
    expect(screen.getByTestId("workspace-sidebar")).toHaveStyle({ position: "absolute", left: "48px" });
    expect(screen.getByRole("button", { name: "Close workspace navigation" })).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
    rerender(<WorkspaceSidebarPanel compact open={false} width={260} onClose={onClose}>
      <button>Existing file</button>
    </WorkspaceSidebarPanel>);
    expect(initiator).toHaveFocus();
    expect(screen.getByTestId("workspace-sidebar")).not.toBeVisible();
    expect(screen.queryByTestId("workspace-sidebar-backdrop")).toBeNull();
    initiator.remove();
  });

  it("offers both an explicit close control and return-to-workspace backdrop", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<WorkspaceSidebarPanel compact open width={420} onClose={onClose}>
      <span>Contents</span>
    </WorkspaceSidebarPanel>);
    await user.click(screen.getByRole("button", { name: "Close workspace navigation" }));
    await user.click(screen.getByRole("button", { name: "Return to workspace" }));
    expect(onClose).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId("workspace-sidebar")).toHaveStyle({ width: "420px", maxWidth: "calc(100% - 48px)" });
  });

  it("keeps the same document and file controls mounted across drawer changes", () => {
    const { rerender } = render(<WorkspaceSidebarPanel compact open={false} width={260} onClose={vi.fn()}>
      <input aria-label="File search" defaultValue="original" />
    </WorkspaceSidebarPanel>);
    const control = screen.getByLabelText("File search");
    rerender(<WorkspaceSidebarPanel compact open width={260} onClose={vi.fn()}>
      <input aria-label="File search" defaultValue="original" />
    </WorkspaceSidebarPanel>);
    expect(screen.getByRole("textbox", { name: "File search" })).toBe(control);
    rerender(<WorkspaceSidebarPanel compact={false} open width={260} onClose={vi.fn()}>
      <input aria-label="File search" defaultValue="original" />
    </WorkspaceSidebarPanel>);
    expect(screen.getByRole("textbox", { name: "File search" })).toBe(control);
  });

  it("allows the legacy document column to fit the available compact width", () => {
    const { container } = render(<WorkspaceLayout layout={createWorkspaceLayout(432)}
      paneContainerWidth={432} leftSidebarWidth={260} leftSidebarCollapsed chatCollapsed adaptive={false}>
      <section>Document</section>
    </WorkspaceLayout>);
    expect((container.firstElementChild as HTMLElement).style.gridTemplateColumns)
      .toBe("48px 0px 0px minmax(0, 1fr) 0px 0px");
  });
});
