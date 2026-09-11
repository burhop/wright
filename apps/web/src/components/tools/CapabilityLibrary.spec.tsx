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
  field_provenance: {
    catalog_metadata: "active_catalog_snapshot",
    compatibility: "current_machine_observation",
    user_state: "local_registry_and_workspace_state",
  },
  data_touched: ["FeatureScript source"],
  examples: ["Generate a mounting bracket"],
  validation_history: [
    {
      status: "not_tested",
      message: "Wright has not contacted the endpoint.",
      missing_dependencies: [],
    },
  ],
  lifecycle_stage: "verified_mcp",
  maturity: "official",
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
    supported_platforms: {
      windows_11_x64: {
        status: "likely",
        tested: false,
        notes: "Remote preview should be platform neutral.",
      },
    },
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
    enabled_workspaces: [
      { workspace_id: "workspace-a", label: "Bracket workspace" },
    ],
  },
  local_validation: {
    evidence_id: "validation-1",
    state: "passed",
    observed_at: "2026-08-12T12:30:00Z",
    reason_codes: [],
    limitation: "Read-only probe only; no tool-call approval was granted.",
  },
  windows_qualification: {
    observed_at: "2026-08-13T12:00:00Z",
    evidence_path:
      "docs/mcp-catalog/evidence/windows-qualification-2026-08-13/onshape-labs-featurescript-mcp-windows-qualification.json",
    evidence_digest: "a".repeat(64),
    current: true,
    stale_reasons: [],
    source: {
      result: "passed",
      label: "Publisher source verified",
      reason_code: "source_verified",
    },
    package_or_registration: {
      result: "partial",
      label: "Registration not completed",
      reason_code: "publisher_terms_required",
    },
    startup: {
      result: "not_applicable",
      label: "Remote service",
      reason_code: "remote_service",
    },
    protocol: {
      result: "not_tested",
      label: "Protocol check not run",
      reason_code: "terms_not_completed",
    },
    host_or_backend: {
      result: "partial",
      label: "Onshape account needed",
      reason_code: "account_required",
    },
    wright_setup: {
      result: "not_tested",
      label: "Wright setup not run",
      reason_code: "terms_not_completed",
    },
    gateway: {
      result: "not_tested",
      label: "Gateway check not run",
      reason_code: "terms_not_completed",
    },
    cleanup: {
      result: "passed",
      label: "No local residue",
      reason_code: "no_local_changes",
    },
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

  it("shows cost, login, location, and installation details", async () => {
    const user = userEvent.setup();
    render(<CapabilityLibrary />);

    expect(await screen.findByText(capability.name)).toBeInTheDocument();
    expect(screen.getByText("Subscription required")).toBeInTheDocument();
    expect(
      screen.queryByText("What do the setup labels mean?"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("capability-next-action"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("evidence-badge-official_preview"),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /view MCP server details/i }),
    );
    const dialog = screen.getByRole("dialog");
    expect(screen.getByTestId("capability-details-backdrop")).toBeVisible();
    expect(dialog).toHaveClass("capability-dialog");
    expect(dialog.querySelector(".capability-dialog__content")).toBeTruthy();
    expect(dialog.querySelector(".capability-dialog__footer")).toBeTruthy();
    expect(dialog).toHaveTextContent("Network access was not confirmed");
    expect(dialog).toHaveTextContent("App Store subscription");
    expect(dialog).toHaveTextContent("FeatureScript source");
    expect(dialog).toHaveTextContent("Generate a mounting bracket");
    expect(dialog).toHaveTextContent("network_access_approval");
    expect(dialog).toHaveTextContent("windows_11_x64: likely");
    expect(dialog).toHaveTextContent("active catalog snapshot");
    expect(dialog).toHaveTextContent("Wright has not contacted the endpoint");
    expect(dialog).toHaveTextContent("jarvis-onshape-mcp");
    expect(dialog).toHaveTextContent("Local validation: passed");
    expect(dialog).toHaveTextContent("Windows qualification");
    expect(dialog).toHaveTextContent("Registration not completed");
    expect(dialog).toHaveTextContent("Onshape account needed");
    expect(dialog).toHaveTextContent("No local residue");
    expect(dialog).toHaveTextContent("Bracket workspace");
    expect(dialog).toHaveTextContent(
      "does not approve individual tool calls or destructive actions",
    );
  });

  it("filters immediately without another request and keeps the URL focused", async () => {
    render(<CapabilityLibrary />);
    await screen.findByText(capability.name);
    fireEvent.change(screen.getByLabelText("Search MCP servers"), {
      target: { value: "missing tool" },
    });
    expect(screen.getByTestId("capability-empty-state")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Search MCP servers"), {
      target: { value: "FeatureScript" },
    });
    fireEvent.change(screen.getByLabelText("Operating system"), {
      target: { value: "windows" },
    });
    fireEvent.change(screen.getByLabelText("Installed"), {
      target: { value: "false" },
    });
    expect(screen.getByText(capability.name)).toBeInTheDocument();
    expect(mcpService.getCapabilities).toHaveBeenCalledTimes(1);
    expect(window.location.search).toContain("search=FeatureScript");
    expect(window.location.search).toContain("platform=windows");
    expect(window.location.search).toContain("installed=false");
    expect(screen.getAllByRole("combobox")).toHaveLength(2);
    expect(screen.getAllByRole("checkbox")).toHaveLength(2);
  });

  it("keeps existing cards usable when a refresh fails", async () => {
    const rendered = render(<CapabilityLibrary />);
    await screen.findByText(capability.name);
    vi.mocked(mcpService.getCapabilities).mockRejectedValueOnce(
      new Error("offline"),
    );
    rendered.rerender(<CapabilityLibrary refreshToken={1} />);
    expect(screen.getByText(capability.name)).toBeInTheDocument();
    await screen.findByRole("alert");
    expect(
      screen.getByRole("button", { name: /view MCP server details/i }),
    ).toBeEnabled();
  });

  it("loads fresh state when an install completes during an older request", async () => {
    let finishOld!: (value: CapabilityListResponse) => void;
    vi.mocked(mcpService.getCapabilities).mockReturnValueOnce(
      new Promise((resolve) => {
        finishOld = resolve;
      }),
    );
    const rendered = render(<CapabilityLibrary />);
    vi.mocked(mcpService.getCapabilities).mockResolvedValueOnce({
      ...result,
      capabilities: [{ ...capability, name: "Updated installation" }],
    });
    rendered.rerender(<CapabilityLibrary refreshToken={1} />);
    await screen.findByText("Updated installation");
    finishOld(result);
    await waitFor(() =>
      expect(screen.queryByText(capability.name)).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Updated installation")).toBeInTheDocument();
  });

  it("loads all pages so filtering covers the complete catalog", async () => {
    vi.mocked(mcpService.getCapabilities)
      .mockResolvedValueOnce({ ...result, next_cursor: "page-2" })
      .mockResolvedValueOnce({
        ...result,
        capabilities: [
          { ...capability, capability_id: "second", name: "Second server" },
        ],
        next_cursor: null,
      });
    render(<CapabilityLibrary />);
    await screen.findByText("Second server");
    expect(mcpService.getCapabilities).toHaveBeenCalledWith({
      limit: 200,
      cursor: "page-2",
    });
  });

  it("offers installation directly on a card", async () => {
    const onPlanOnboarding = vi.fn();
    render(<CapabilityLibrary onPlanOnboarding={onPlanOnboarding} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Install " + capability.name }),
    );
    expect(onPlanOnboarding).toHaveBeenCalledWith(capability.capability_id);
  });

  it("supports keyboard detail opening and local observation", async () => {
    const user = userEvent.setup();
    render(<CapabilityLibrary />);
    const button = await screen.findByRole("button", {
      name: /view MCP server details/i,
    });
    button.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByTestId("capability-details-close")).toHaveFocus();
    await user.click(screen.getByText("Technical details"));
    await user.click(
      screen.getByRole("button", { name: /check this computer/i }),
    );
    expect(mcpService.observeCapability).toHaveBeenCalledWith(
      "onshape-labs-featurescript-mcp",
    );
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(button).toHaveFocus();
  });

  it("closes capability details before handing off to setup", async () => {
    const user = userEvent.setup();
    const onPlanOnboarding = vi.fn();
    render(<CapabilityLibrary onPlanOnboarding={onPlanOnboarding} />);

    await user.click(
      await screen.findByRole("button", { name: /view MCP server details/i }),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Install MCP server" }),
    );

    expect(onPlanOnboarding).toHaveBeenCalledWith(capability.capability_id);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
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
      "bundled MCP Server Library could not be loaded",
    );
    expect(
      screen.getByRole("button", { name: "Try loading again" }),
    ).toBeEnabled();
  });
});
