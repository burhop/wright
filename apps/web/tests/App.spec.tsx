import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { hostAdapter } from "../src/services/host-adapter";

vi.mock("../src/components/layout/AppShell", () => ({
  default: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("../src/components/pages/DashboardPage", () => ({
  default: () => <div data-testid="page-dashboard">Wright dashboard</div>,
}));

vi.mock("../src/store/sessions", () => ({
  ChatProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));
vi.mock("../src/store/tools", () => ({
  ToolsProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));
vi.mock("../src/store/viewer", () => ({
  ViewerPanelProvider: ({ children }: { children: ReactNode }) => (
    <>{children}</>
  ),
}));

describe("App startup", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the Wright dashboard without waiting for setup status", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ auth_required: false, authenticated: true }),
            { status: 200 },
          ),
        ),
    );
    vi.spyOn(hostAdapter, "fetch").mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(await screen.findByTestId("page-dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Welcome to Wright")).not.toBeInTheDocument();
  });
});
