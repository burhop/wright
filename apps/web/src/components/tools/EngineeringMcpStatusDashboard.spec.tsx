import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { mcpService, type EngineeringMcpStatus } from "../../services/mcp-service";
import { EngineeringMcpStatusDashboard } from "./EngineeringMcpStatusDashboard";

vi.mock("../../services/mcp-service", async (loadOriginal) => {
  const original = await loadOriginal<typeof import("../../services/mcp-service")>();
  return { ...original, mcpService: { ...original.mcpService, getEngineeringStatus: vi.fn() } };
});

const status: EngineeringMcpStatus = {
  schema_version: 1,
  generated_at: "2026-09-09T12:00:00Z",
  as_of: "2026-09-09",
  policy_version: "2026-09-08.1",
  counts: { curated: 10, follow_up: 56, removed: 12 },
  qualification_counts: { passing: 10, failing: 10, blocked: 32, stale: 0, untested: 25 },
  target: { minimum: 10, ideal: 15, maximum: 20, curated: 10, minimum_met: true, ideal_met: false },
  breakdowns: {
    disciplines: [{ key: "cad", passing: 1, failing: 0, blocked: 0, stale: 0, untested: 0, total: 1 }],
    protocols: [], transports: [], platforms: [], dependencies: [],
  },
  protocol_status: [
    { protocol: "mcp", label: "MCP", known: 75, curated: 10, passing: 10, status: "implemented", physical_operation_qualified: null },
    { protocol: "webmcp", label: "WebMCP", known: 1, curated: 0, passing: 0, status: "implemented", physical_operation_qualified: null },
    { protocol: "hardware_mcp", label: "Hardware MCP", known: 2, curated: 0, passing: 0, status: "qualification_required", physical_operation_qualified: false },
    { protocol: "mhs", label: "Anthropic Model Hardware Standard", known: 0, curated: 0, passing: 0, status: "research_preview", physical_operation_qualified: false },
  ],
  changes: {
    previous_as_of: "2026-09-08",
    count: 1,
    summary: { promotion: 0, demotion: 0, new: 0, failure: 0, recovery: 0, removal: 0 },
    items: [{ server_id: "openscad-mcp", change: "qualification_refreshed" }],
  },
  chains: [{ chain_id: "mechanical-cad-fea-review", name: "Mechanical CAD → structural screening → DXF review", status: "passed", call_count: 8, handoffs_accepted: 2, corrupt_handoffs_rejected: 2, artifact_checks: 8, cleanup: "passed", last_run: "2026-09-09T01:00:00Z", evidence_href: "/api/mcp/status/evidence/process-chains", scenario_kind: "synthetic_qualification_fixture" }],
  records: [{ server_id: "openscad-mcp", name: "OpenSCAD Rendering Engine", vendor: "quellant", source_url: "https://github.com/quellant/openscad-mcp", source_revision: "d438b84", scope: "Cube export", implementation_mode: "wrapper", disposition: "curated", qualification_status: "passing", protocol_family: "mcp", transport: "stdio", disciplines: ["cad"], engineering_stages: ["design"], platforms: ["linux_x64"], dependency_groups: ["system"], prerequisites: ["OpenSCAD"], credentials: [], last_qualified_at: "2026-09-09", expires_at: "2026-10-09", evidence_age_days: 0, latest_result: "passed", latest_message: "passed", failure: null, evidence_href: "/api/mcp/status/evidence/server-openscad-mcp", evidence_sha256: "a".repeat(64), owner: "Wright catalog maintainers", review_due: "2026-10-09", next_action: "Renew the workflow." }],
  limitations: [],
};

describe("EngineeringMcpStatusDashboard", () => {
  beforeEach(() => vi.mocked(mcpService.getEngineeringStatus).mockResolvedValue(status));

  it("shows evidence-backed counts, protocol boundaries, chains, and server details", async () => {
    render(<EngineeringMcpStatusDashboard />);
    expect(await screen.findByText("Engineering MCP Status")).toBeInTheDocument();
    expect(screen.getByTestId("engineering-count-curated")).toHaveTextContent("10");
    expect(screen.getByTestId("engineering-status-passing")).toHaveTextContent("10 Passing");
    expect(screen.getByTestId("engineering-protocol-mhs")).toHaveTextContent("has not qualified physical operation");
    expect(screen.getByTestId("engineering-chain-mechanical-cad-fea-review")).toHaveTextContent("8 calls");
    expect(screen.getByTestId("engineering-status-records")).toHaveTextContent("OpenSCAD Rendering Engine");
    expect(screen.getByRole("link", { name: "Open evidence" })).toHaveAttribute("href", "/api/mcp/status/evidence/server-openscad-mcp");
  });

  it("filters the evidence table without changing portfolio totals", async () => {
    render(<EngineeringMcpStatusDashboard />);
    await screen.findByText("OpenSCAD Rendering Engine");
    fireEvent.change(screen.getByLabelText("Search"), { target: { value: "no-match" } });
    expect(screen.getByText("Server evidence (0 shown)")).toBeInTheDocument();
    expect(screen.getByTestId("engineering-count-curated")).toHaveTextContent("10");
  });
});
