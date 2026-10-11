import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App, { createAppRouter } from "../src/App";
import Sidebar from "../src/components/layout/Sidebar";
import { hostAdapter } from "../src/services/host-adapter";

const { featureFlags, processPageRender } = vi.hoisted(() => ({
  featureFlags: { processDefinitionEnabled: false },
  processPageRender: vi.fn(),
}));

vi.mock("../src/services/surfaces/feature-flags", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("../src/services/surfaces/feature-flags")
    >();
  return {
    ...actual,
    processDefinitionViewEnabled: () => featureFlags.processDefinitionEnabled,
  };
});

vi.mock("../src/components/pages/ProcessDefinitionPage", () => {
  const ProcessDefinitionPage = () => {
    processPageRender();
    return <div data-testid="page-process-definition">Process definition</div>;
  };
  return { default: ProcessDefinitionPage, ProcessDefinitionPage };
});

vi.mock("../src/components/layout/AppShell", () => ({
  default: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("../src/components/pages/DashboardPage", () => ({
  default: () => <div data-testid="page-dashboard">Wright dashboard</div>,
}));
vi.mock("../src/components/pages/EngineeringModelLibraryPage", () => ({
  default: () => (
    <div data-testid="page-engineering-models">Engineering Models</div>
  ),
}));
vi.mock("../src/components/pages/ModelSetupPage", () => ({
  default: () => <div data-testid="page-model-setup">Model Setup</div>,
}));

vi.mock("../src/store/sessions", () => ({
  ChatProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));
vi.mock("../src/store/tools", () => ({
  ToolsProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));
vi.mock("../src/store/viewer", () => ({
  useViewerPanel: () => ({ openTabs: [], setTabDirty: vi.fn() }),
  ViewerPanelProvider: ({ children }: { children: ReactNode }) => (
    <>{children}</>
  ),
}));

describe("App startup", () => {
  const routers: ReturnType<typeof createAppRouter>[] = [];
  const renderApp = () => {
    const router = createAppRouter();
    routers.push(router);
    return render(<App router={router} />);
  };
  beforeEach(() => {
    featureFlags.processDefinitionEnabled = false;
    processPageRender.mockReset();
    window.history.replaceState({}, "", "/");
  });

  afterEach(() => {
    routers.splice(0).forEach((router) => router.dispose());
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

    renderApp();

    expect(await screen.findByTestId("page-dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Welcome to Wright")).not.toBeInTheDocument();
  });

  it.each([
    ["/engineering-models", "page-engineering-models"],
    ["/setup/model", "page-model-setup"],
  ])("preserves the distinct %s route", async (path, testId) => {
    window.history.replaceState({}, "", path);
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
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ theme: "dark" }), { status: 200 }),
    );

    renderApp();

    expect(await screen.findByTestId(testId)).toBeInTheDocument();
  });

  it("falls through to bounded dashboard recovery when the process route is disabled", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/processes/product-definition-v1");
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
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ theme: "dark" }), { status: 200 }),
    );

    const app = renderApp();

    expect(await screen.findByTestId("page-not-found")).toBeInTheDocument();
    expect(processPageRender).not.toHaveBeenCalled();
    const recovery = screen.getByTestId("back-to-dashboard-btn");
    expect(recovery).toHaveAttribute("href", "/");
    await user.click(recovery);
    expect(await screen.findByTestId("page-dashboard")).toBeInTheDocument();

    app.unmount();
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId("nav-process-definition")).toBeNull();
  });

  it("preserves hash routing for the desktop host", async () => {
    vi.spyOn(hostAdapter, "getRouterType").mockReturnValue("hash");
    window.history.replaceState({}, "", "/#/engineering-models");
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
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ theme: "dark" }), { status: 200 }),
    );
    renderApp();
    expect(
      await screen.findByTestId("page-engineering-models"),
    ).toBeInTheDocument();
  });
});
