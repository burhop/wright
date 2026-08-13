import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ToolRegistryPage } from "../src/components/pages/ToolRegistryPage";
import { mcpService } from "../src/services/mcp-service";
import { useTools } from "../src/store/tools";

vi.mock("../src/store/tools", () => ({ useTools: vi.fn() }));
vi.mock("../src/services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../src/services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      ...original.mcpService,
      getCapabilities: vi.fn(),
      observeCapability: vi.fn(),
      reportMissingMcp: vi.fn(),
    },
  };
});
vi.mock("../src/hooks/useLogger", () => ({
  default: () => ({ info: vi.fn(), error: vi.fn(), warn: vi.fn() }),
}));

const baseCapability = {
  capability_id: "cad-extractor",
  canonical_id: "cad-extractor",
  name: "CAD Extractor",
  vendor: "Fixture vendor",
  description: "Extract geometry for engineering review.",
  domains: ["cad"],
  tags: ["geometry"],
  aliases: [],
  capability_summary: ["Extract geometry"],
  field_provenance: {},
  data_touched: [],
  examples: [],
  validation_history: [],
  lifecycle_stage: "community_mcp",
  maturity: "community",
  evidence_class: "verified_community" as const,
  transport: "stdio" as const,
  locality: "local" as const,
  risk_level: "low" as const,
  installability_tier: "tested" as const,
  compatibility: {
    status: "compatible" as const,
    platform_key: "linux_x64",
    reasons: [],
  },
  source_records: [],
  requirements: {},
  validation_result: {
    status: "passed" as const,
    message: "Validated in a deterministic fixture.",
    missing_dependencies: [],
  },
  user_state: {
    installed: true,
    active: false,
    process_status: "inactive",
    explicit_disabled: true,
    credentials_configured: {},
    enabled_workspaces: [],
  },
  custom: false,
  available_actions: ["view_details", "observe", "manage_installation"],
  alternatives: [],
};

describe("ToolRegistryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, "", "/tool-registry");
    (useTools as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      registerCustomServer: vi.fn(),
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
      capabilities: [baseCapability],
      next_cursor: null,
      total: 1,
    });
  });

  it("renders the merged capability projection", async () => {
    render(<ToolRegistryPage />);

    expect(await screen.findByText("CAD Extractor")).toBeInTheDocument();
    expect(
      screen.getByTestId("evidence-badge-verified_community"),
    ).toHaveTextContent("Verified community");
    expect(
      screen.getByTestId("compatibility-badge-compatible"),
    ).toHaveTextContent("Compatible");
    expect(
      screen.getByTestId("capability-card-cad-extractor"),
    ).toHaveTextContent("Installed");
  });

  it("sends search and domain filters to the capability endpoint", async () => {
    render(<ToolRegistryPage />);
    await screen.findByText("CAD Extractor");

    fireEvent.change(screen.getByLabelText("Search capabilities"), {
      target: { value: "geometry" },
    });
    fireEvent.change(screen.getByLabelText("Engineering domain"), {
      target: { value: "cad" },
    });

    await waitFor(() =>
      expect(mcpService.getCapabilities).toHaveBeenLastCalledWith(
        expect.objectContaining({ search: "geometry", domain: ["cad"] }),
      ),
    );
  });

  it("opens progressive details without exposing a launch command", async () => {
    render(<ToolRegistryPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /view details for cad extractor/i,
      }),
    );

    expect(screen.getByRole("dialog")).toHaveTextContent(
      "Validated in a deterministic fixture",
    );
    expect(screen.queryByText(/uv run/i)).not.toBeInTheDocument();
  });
});
