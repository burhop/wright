import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceActivityBar } from "./WorkspaceActivityBar";

describe("WorkspaceActivityBar", () => {
  it("announces the selected navigation panel visibility", () => {
    const props = {
      activeSidebar: "files" as const,
      onBack: vi.fn(),
      onSelectSidebar: vi.fn(),
    };
    const { rerender } = render(
      <WorkspaceActivityBar {...props} isSidebarCollapsed />,
    );
    expect(screen.getByTestId("activity-bar-explorer-btn")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    rerender(<WorkspaceActivityBar {...props} isSidebarCollapsed={false} />);
    expect(screen.getByTestId("activity-bar-explorer-btn")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByTestId("activity-bar-explorer-btn")).toHaveAttribute(
      "aria-controls",
      "workspace-navigation-panel",
    );
    expect(screen.getByTestId("activity-bar-mcp-btn")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });
  it("uses generic MCP navigation without a dedicated BREP launcher", () => {
    const onSelectSidebar = vi.fn();

    render(
      <WorkspaceActivityBar
        activeSidebar="files"
        isSidebarCollapsed={false}
        onBack={vi.fn()}
        onSelectSidebar={onSelectSidebar}
        onOpenWorkflows={vi.fn()}
        workflowsEnabled
      />,
    );

    expect(
      screen.queryByTestId("activity-bar-brep-btn"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("activity-bar-mcp-btn")).toBeInTheDocument();
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
