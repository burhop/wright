import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";
import { ToolRegistryPage } from "../components/pages/ToolRegistryPage";
import { mcpService } from "../services/mcp-service";
import { useTools } from "../store/tools";

vi.mock("../store/tools", () => ({ useTools: vi.fn() }));
vi.mock("../services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      ...original.mcpService,
      getCapabilities: vi.fn(),
      getCatalogState: vi.fn(),
      previewCatalogUpdate: vi.fn(),
      activateCatalogUpdate: vi.fn(),
      rollbackCatalog: vi.fn(),
      reportMissingMcp: vi.fn(),
      reportMissingCapability: vi.fn(),
    },
  };
});
vi.mock("../hooks/useLogger", () => ({
  default: () => ({ info: vi.fn(), error: vi.fn(), warn: vi.fn() }),
}));

describe("ToolRegistryPage capability layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useTools as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      fetchServersAndTools: vi.fn(),
    });
    vi.mocked(mcpService.getCapabilities).mockResolvedValue({
      snapshot: {
        snapshot_id: "bundled",
        channel: "bundled",
        sequence: 1,
        offline: true,
        updated_at: "2026-08-12T00:00:00Z",
      },
      capabilities: [],
      next_cursor: null,
      total: 0,
    });
    vi.mocked(mcpService.getCatalogState).mockResolvedValue({
      bundled_snapshot_id: "bundled",
      active_snapshot_id: "bundled",
      previous_snapshot_id: null,
      active_sequence: 1,
      active_channel: "bundled",
      active_generation: 1,
      updated_at: "2026-08-12T00:00:00Z",
      updated_by: "wright-bootstrap",
      configured_channels: [],
      diagnostic: null,
      history: [],
    });
  });

  it("renders the MCP Server Library information architecture", async () => {
    render(<ToolRegistryPage />);

    expect(screen.getByTestId("page-tool-registry")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Engineering MCP Server Library" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("MCP server filters")).toBeInTheDocument();
    expect(screen.getByTestId("tool-registry-register-btn")).toHaveTextContent(
      "Add custom MCP server",
    );
    expect(
      await screen.findByTestId("capability-empty-state"),
    ).toBeInTheDocument();
    expect(mcpService.getCatalogState).not.toHaveBeenCalled();
  });

  it("does not advertise the raw catalog size as the registry count", () => {
    vi.mocked(useTools).mockReturnValue({
      servers: Array.from({ length: 82 }),
    } as unknown as ReturnType<typeof useTools>);
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("nav-tool-registry")).toHaveTextContent(
      /^Tool Registry$/,
    );
  });
});
