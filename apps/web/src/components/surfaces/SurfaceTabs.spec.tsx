import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SurfaceTabs } from "./SurfaceTabs";

const tabs = [
  { id: "graph", label: "Graph", closable: true },
  { id: "brep", label: "BREP", closable: true },
  { id: "webmcp", label: "WebMCP", closable: false },
] as const;

describe("SurfaceTabs", () => {
  it("provides a semantic tablist with roving focus and explicit selection", async () => {
    const user = userEvent.setup();
    const select = vi.fn();
    render(<SurfaceTabs tabs={tabs} selectedId="graph" onSelect={select} />);

    const graph = screen.getByTestId("surface-tab-graph");
    const brep = screen.getByTestId("surface-tab-brep");
    expect(
      screen.getByRole("tablist", { name: "Workspace surfaces" }),
    ).toBeVisible();
    expect(graph).toHaveAttribute("aria-selected", "true");
    expect(graph).toHaveAttribute("tabindex", "0");
    expect(brep).toHaveAttribute("tabindex", "-1");

    graph.focus();
    await user.keyboard("{ArrowRight}");
    expect(brep).toHaveFocus();
    expect(select).not.toHaveBeenCalled();
    await user.keyboard("{Enter}");
    expect(select).toHaveBeenCalledWith("brep");
    await user.keyboard("{End}");
    expect(screen.getByTestId("surface-tab-webmcp")).toHaveFocus();
    await user.keyboard("{Home}");
    expect(graph).toHaveFocus();
  });

  it("closes with Delete, restores focus, and exposes no reorder affordance", async () => {
    const user = userEvent.setup();
    const close = vi.fn();
    const headingRef = { current: document.createElement("h2") };
    document.body.append(headingRef.current);
    render(
      <SurfaceTabs
        tabs={tabs}
        selectedId="brep"
        onSelect={vi.fn()}
        onClose={close}
        emptyFocusRef={headingRef}
      />,
    );

    const brep = screen.getByTestId("surface-tab-brep");
    brep.focus();
    await user.keyboard("{Delete}");
    expect(close).toHaveBeenCalledWith("brep");
    expect(screen.getByTestId("surface-tab-webmcp")).toHaveFocus();
    expect(
      screen.queryByRole("button", { name: /reorder/i }),
    ).not.toBeInTheDocument();
    expect(brep).not.toHaveAttribute("draggable", "true");

    headingRef.current.remove();
  });

  it("restores focus to the surfaces heading after the final tab closes", async () => {
    const user = userEvent.setup();
    const heading = document.createElement("h2");
    heading.tabIndex = -1;
    document.body.append(heading);
    render(
      <SurfaceTabs
        tabs={[{ id: "only", label: "Only surface", closable: true }]}
        selectedId="only"
        onSelect={vi.fn()}
        onClose={vi.fn()}
        emptyFocusRef={{ current: heading }}
      />,
    );

    screen.getByTestId("surface-tab-only").focus();
    await user.keyboard("{Delete}");
    expect(heading).toHaveFocus();
    heading.remove();
  });
});
