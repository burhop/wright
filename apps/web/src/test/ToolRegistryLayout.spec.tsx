import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
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
      getEngineeringStatus: vi.fn(),
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
    vi.mocked(mcpService.getEngineeringStatus).mockResolvedValue({
      schema_version: 1,
      generated_at: "2026-09-09T00:00:00Z",
      as_of: "2026-09-09",
      policy_version: "2026-09-08.1",
      counts: { curated: 10, follow_up: 56, removed: 12 },
      qualification_counts: { passing: 10, failing: 10, blocked: 32, stale: 0, untested: 25 },
      target: { minimum: 10, ideal: 15, maximum: 20, curated: 10, minimum_met: true, ideal_met: false },
      breakdowns: { disciplines: [], protocols: [], transports: [], platforms: [], dependencies: [] },
      protocol_status: [],
      changes: {
        previous_as_of: "2026-09-08",
        count: 0,
        summary: { promotion: 0, demotion: 0, new: 0, failure: 0, recovery: 0, removal: 0 },
        items: [],
      },
      chains: [],
      records: [],
      limitations: [],
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
    expect(await screen.findByTestId("engineering-mcp-status")).toHaveTextContent(
      "10 of 15 preferred integrations",
    );
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
  });
});
