import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import AppShell from "../src/components/layout/AppShell";

describe("AppShell", () => {
  it("renders header, sidebar, and children content", () => {
    render(
      <MemoryRouter>
        <AppShell>
          <div data-testid="test-child">Dashboard Content</div>
        </AppShell>
      </MemoryRouter>,
    );

    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
    expect(screen.getByTestId("header")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("test-child")).toHaveTextContent(
      "Dashboard Content",
    );
  });
  it("does not render the obsolete Split Onshape control", () => {
    render(
      <MemoryRouter initialEntries={["/workspace/demo-session"]}>
        <AppShell>
          <div data-testid="test-child">Workspace Content</div>
        </AppShell>
      </MemoryRouter>,
    );

    expect(screen.queryByTestId("split-view-toggle")).not.toBeInTheDocument();
    expect(screen.queryByText("Split Onshape")).not.toBeInTheDocument();
    expect(screen.queryByTestId("split-resizer")).not.toBeInTheDocument();
    expect(screen.getByTestId("test-child")).toHaveTextContent(
      "Workspace Content",
    );
  });

});
