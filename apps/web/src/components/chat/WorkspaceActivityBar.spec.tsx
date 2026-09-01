import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceActivityBar } from "./WorkspaceActivityBar";

describe("WorkspaceActivityBar", () => {
  it("opens BREP without selecting a sidebar", async () => {
    const user = userEvent.setup();
    const onOpenBrepPanel = vi.fn();
    const onSelectSidebar = vi.fn();

    render(
      <WorkspaceActivityBar
        activeSidebar="files"
        isSidebarCollapsed={false}
        onBack={vi.fn()}
        onSelectSidebar={onSelectSidebar}
        onOpenWorkflows={vi.fn()}
        onOpenBrepPanel={onOpenBrepPanel}
        workflowsEnabled
      />,
    );

    await user.click(screen.getByTestId("activity-bar-brep-btn"));

    expect(onOpenBrepPanel).toHaveBeenCalledOnce();
    expect(onSelectSidebar).not.toHaveBeenCalled();
  });

  it("opens workspace workflows without selecting a sidebar", async () => {
    const user = userEvent.setup();
    const onOpenWorkflows = vi.fn();
    const onSelectSidebar = vi.fn();
    render(
      <WorkspaceActivityBar
        activeSidebar="files"
        isSidebarCollapsed={false}
        onBack={vi.fn()}
        onSelectSidebar={onSelectSidebar}
        onOpenWorkflows={onOpenWorkflows}
        onOpenBrepPanel={vi.fn()}
        workflowsEnabled
      />,
    );
    expect(screen.getByTestId("activity-bar-workflows-btn")).toHaveAttribute(
      "title",
      "Workflows",
    );
    await user.click(screen.getByTestId("activity-bar-workflows-btn"));
    expect(onOpenWorkflows).toHaveBeenCalledOnce();
    expect(onSelectSidebar).not.toHaveBeenCalled();
  });
});
