import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  CapabilityListResponse,
  CapabilityView,
} from "../../services/mcp-service";
import { mcpService } from "../../services/mcp-service";
import { CapabilityLibrary } from "./CapabilityLibrary";

vi.mock("../../services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      getCapabilities: vi.fn(),
      observeCapability: vi.fn(),
    },
  };
});

const capability: CapabilityView = {
  capability_id: "onshape-labs-featurescript-mcp",
  canonical_id: "onshape-labs-featurescript-mcp",
  name: "Onshape Labs FeatureScript MCP",
  vendor: "Onshape / PTC",
  description: "Generate and refine FeatureScript from engineering intent.",
  domains: ["cad", "cloud-cad"],
  tags: ["onshape", "featurescript"],
  aliases: ["onshape-featurescript-mcp-official"],
  capability_summary: ["Generate FeatureScript", "Test and refine code"],
  evidence_class: "official_preview",
  transport: "streamable_http",
  locality: "remote",
  risk_level: "medium",
  installability_tier: "might_work",
  compatibility: {
    status: "uncertain",
    platform_key: "windows_11_x64",
    reasons: [
      {
        code: "network_access_unconfirmed",
        message: "Network access was not confirmed.",
        recovery: "Review and approve the endpoint during onboarding.",
        source: "machine.network_policy",
      },
    ],
  },
  source_records: [
    {
      url: "https://www.onshape.com/en/blog/featurescript-mcp-server-enables-text-code-cad",
      kind: "vendor_docs",
      primary: true,
      authority: "vendor",
      notes: "Official announcement.",
    },
  ],
  requirements: {
    host_software: [],
    credentials: [],
    license: "App Store subscription completed independently.",
    approval_gates: ["network_access_approval"],
  },
  validation_result: {
    status: "not_tested",
    message: "Wright has not contacted the endpoint.",
    missing_dependencies: [],
  },
  user_state: {
    installed: false,
    active: false,
    process_status: "inactive",
    explicit_disabled: false,
    credentials_configured: {},
    enabled_workspaces: [],
  },
  custom: false,
  available_actions: ["view_details", "observe", "plan_onboarding"],
  alternatives: ["jarvis-onshape-mcp"],
};

const result: CapabilityListResponse = {
  snapshot: {
    snapshot_id: "bundled-fixture",
    channel: "bundled",
    sequence: 1,
    offline: true,
    updated_at: "2026-08-12T00:00:00Z",
  },
  capabilities: [capability],
  next_cursor: null,
  total: 70,
};

describe("CapabilityLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, "", "/tool-registry");
    vi.mocked(mcpService.getCapabilities).mockResolvedValue(result);
    vi.mocked(mcpService.observeCapability).mockResolvedValue({
      observation: {
        observation_id: "machine-1",
        observed_at: "2026-08-12T12:00:00Z",
        expires_at: "2026-08-12T12:15:00Z",
        platform_key: "windows_11_x64",
        os_name: "Windows",
        os_version: "11",
        architecture: "AMD64",
        distribution_mode: "native",
        runtimes: {},
        package_managers: {},
        network_policy: "unknown",
        host_observations: {},
        digest: "a".repeat(64),
      },
      compatibility: capability.compatibility,
    });
  });

  it("shows offline provenance, evidence, compatibility, and details", async () => {
    const user = userEvent.setup();
    render(<CapabilityLibrary />);

    expect(await screen.findByText(capability.name)).toBeInTheDocument();
    expect(screen.getByTestId("capability-offline-source")).toHaveTextContent(
      "complete bundled catalog",
    );
    expect(
      screen.getByTestId("evidence-badge-official_preview"),
    ).toHaveTextContent("Official preview");
    expect(
      screen.getByTestId("compatibility-badge-uncertain"),
    ).toHaveTextContent("Compatibility uncertain");

    await user.click(screen.getByRole("button", { name: /view details/i }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent("Network access was not confirmed");
    expect(dialog).toHaveTextContent("App Store subscription");
    expect(dialog).toHaveTextContent("Wright has not contacted the endpoint");
    expect(dialog).toHaveTextContent("jarvis-onshape-mcp");
  });

  it("keeps filter state in the URL and sends each dimension", async () => {
    render(<CapabilityLibrary />);
    await screen.findByText(capability.name);

    fireEvent.change(screen.getByLabelText("Search capabilities"), {
      target: { value: "bracket" },
    });
    fireEvent.change(screen.getByLabelText("Engineering domain"), {
      target: { value: "cad" },
    });
    fireEvent.change(screen.getByLabelText("Evidence class"), {
      target: { value: "official_preview" },
    });

    await waitFor(() =>
      expect(mcpService.getCapabilities).toHaveBeenLastCalledWith(
        expect.objectContaining({
          search: "bracket",
          domain: ["cad"],
          evidence_class: ["official_preview"],
        }),
      ),
    );
    expect(window.location.search).toContain("search=bracket");
    expect(window.location.search).toContain("domain=cad");
  });

  it("supports keyboard detail opening and local observation", async () => {
    const user = userEvent.setup();
    render(<CapabilityLibrary />);
    const button = await screen.findByRole("button", { name: /view details/i });
    button.focus();
    await user.keyboard("{Enter}");
    await user.click(
      screen.getByRole("button", { name: /check this machine again/i }),
    );
    expect(mcpService.observeCapability).toHaveBeenCalledWith(
      "onshape-labs-featurescript-mcp",
    );
  });

  it("renders honest empty and unavailable states", async () => {
    vi.mocked(mcpService.getCapabilities).mockResolvedValueOnce({
      ...result,
      capabilities: [],
      total: 0,
    });
    const rendered = render(<CapabilityLibrary />);
    expect(
      await screen.findByTestId("capability-empty-state"),
    ).toBeInTheDocument();

    rendered.unmount();
    vi.mocked(mcpService.getCapabilities).mockRejectedValueOnce(
      new Error("offline"),
    );
    render(<CapabilityLibrary />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "bundled Capability Library could not be loaded",
    );
  });
});
