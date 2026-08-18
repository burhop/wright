import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CapabilityApiError,
  mcpService,
  type ImportPreview,
  type InstallPlan,
  type OnboardingRun,
  type CapabilityValidationEvidence,
} from "../../services/mcp-service";
import { workspaceService } from "../../services/workspace-service";
import { OnboardingWizard } from "./OnboardingWizard";

vi.mock("../../services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      previewImport: vi.fn(),
      createInstallPlan: vi.fn(),
      approveInstallPlan: vi.fn(),
      applyInstallPlan: vi.fn(),
      getCredentialStatus: vi.fn(),
      runCapabilityValidation: vi.fn(),
      enableCapabilityForWorkspace: vi.fn(),
    },
  };
});

vi.mock("../../services/workspace-service", () => ({
  workspaceService: { getAllWorkspaces: vi.fn() },
}));

const preview: ImportPreview = {
  preview_id: "import-1",
  detected_format: "plain_server",
  drafts: [
    {
      draft_id: "draft-1",
      name: "Fixture MCP",
      source_format: "plain_server",
      transport: "stdio",
      command: "python",
      arguments: ["server.py"],
      environment_requirements: [],
      header_requirements: [],
      warnings: [],
      errors: [],
      redacted_preview: {},
      draft_digest: "a".repeat(64),
    },
  ],
  document_errors: [],
  created_at: "2026-08-12T12:00:00Z",
  expires_at: "2026-08-12T12:15:00Z",
  source_discarded: true,
};

const plan: InstallPlan = {
  plan_id: "plan-1",
  plan_version: 1,
  state: "reviewable",
  capability_id: "import:draft-1",
  snapshot_id: "bundled-70",
  machine_observation_id: "machine-1",
  backend_kind: "local_command",
  requested_scope: "global_registered",
  source: { command: "python", arguments: ["server.py"] },
  requirements: {
    platform: ["windows_11_x64"],
    runtimes: ["python"],
    license: {
      state: "known",
      reference: "MIT",
      independent_completion_required: false,
    },
    credentials: ["API_TOKEN"],
    network: [],
    storage: ["wright-managed:draft-1"],
    host: [],
  },
  effects: [
    {
      step_id: "effect-register",
      kind: "write_config",
      description: "Register the reviewed literal command.",
      reversible: true,
    },
  ],
  steps: [],
  validation_steps: [],
  rollback_steps: [],
  approval_gates: ["advanced_local_command_approval"],
  blocking_reasons: [],
  expires_at: "2026-08-12T12:30:00Z",
  plan_digest: "b".repeat(64),
};

const run: OnboardingRun = {
  run_id: "run-1",
  plan_id: plan.plan_id,
  plan_digest: plan.plan_digest,
  state: "completed",
  adapter_kind: "local_command",
  adapter_version: "test",
  started_at: "2026-08-12T12:00:00Z",
  completed_at: "2026-08-12T12:00:01Z",
  effects: [],
  trace_id: "trace-1",
};

const validation: CapabilityValidationEvidence = {
  evidence_id: "validation-1",
  capability_id: plan.capability_id,
  server_id: plan.capability_id,
  snapshot_id: plan.snapshot_id,
  capability_digest: "c".repeat(64),
  observation_id: plan.machine_observation_id,
  platform_key: "windows_11_x64",
  architecture: "amd64",
  server_revision: "1.0.0",
  credential_binding_digest: "d".repeat(64),
  state: "passed",
  protocol_steps: {
    initialize: "passed",
    "notifications/initialized": "passed",
    "tools/list": "passed",
  },
  schema_digest: "e".repeat(64),
  tool_count: 1,
  read_only_probe: {
    name: "health",
    argument_digest: "f".repeat(64),
    result_digest: "1".repeat(64),
    status: "passed",
    limitation: "Fixture health only",
  },
  observed_at: "2026-08-12T12:00:01Z",
  reason_codes: [],
  missing_requirements: [],
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("OnboardingWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(mcpService.previewImport).mockResolvedValue(preview);
    vi.mocked(mcpService.createInstallPlan).mockResolvedValue(plan);
    vi.mocked(mcpService.approveInstallPlan).mockResolvedValue({
      ...plan,
      state: "approved",
    });
    vi.mocked(mcpService.applyInstallPlan).mockResolvedValue(run);
    vi.mocked(mcpService.getCredentialStatus).mockResolvedValue({
      server_id: plan.capability_id,
      env_vars: [],
      configured: { API_TOKEN: true },
    });
    vi.mocked(mcpService.runCapabilityValidation).mockResolvedValue(validation);
    vi.mocked(workspaceService.getAllWorkspaces).mockResolvedValue([
      {
        workspace_id: "workspace-a",
        session_id: "session-a",
        workspace_name: "Bracket project",
        local_path: "D:/workspace/a",
        git_remote_url: null,
        git_username: null,
        enabled_tools: [],
        updated_at: 1,
      },
      {
        workspace_id: "workspace-b",
        session_id: "session-b",
        workspace_name: "Pump project",
        local_path: "D:/workspace/b",
        git_remote_url: null,
        git_username: null,
        enabled_tools: [],
        updated_at: 1,
      },
    ]);
    vi.mocked(mcpService.enableCapabilityForWorkspace).mockResolvedValue({
      workspace_id: "workspace-a",
      capability_id: plan.capability_id,
      server_id: plan.capability_id,
      enabled: true,
      validation_evidence_id: validation.evidence_id,
      invocation_approved: false,
      message:
        "Available in this workspace. Individual tool invocation remains separate.",
    });
  });

  it("starts with custom MCP sources and makes no request", () => {
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    expect(screen.getByRole("dialog")).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Add custom MCP server" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("option", { name: "Capability Library" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Paste MCP configuration" }),
    ).toBeVisible();
    expect(
      screen.getByRole("option", { name: "Remote MCP endpoint" }),
    ).toBeVisible();
    expect(
      screen.getByRole("option", { name: "Advanced local command" }),
    ).toBeVisible();
    expect(
      screen.getByRole("option", { name: "Engineering host bridge" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        "This check is read-only. It does not install software, connect an account, or enable tools.",
      ),
    ).toBeVisible();
    expect(mcpService.previewImport).not.toHaveBeenCalled();
  });

  it("normalizes pasted configuration and creates a read-only plan", async () => {
    const user = userEvent.setup();
    const pending = deferred<ImportPreview>();
    vi.mocked(mcpService.previewImport).mockReturnValue(pending.promise);
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    await user.selectOptions(screen.getByLabelText("Source"), "import");
    fireEvent.change(screen.getByLabelText("MCP configuration JSON"), {
      target: { value: '{"command":"python"}' },
    });
    await user.click(
      screen.getByRole("button", { name: "Review install plan" }),
    );
    expect(
      screen.getByText(/Normalizing the source and checking this machine/),
    ).toBeVisible();
    pending.resolve(preview);

    expect(await screen.findByText("Confirm this installation")).toBeVisible();
    expect(screen.getByTestId("onboarding-plan-review")).toHaveTextContent(
      "Register the reviewed literal command",
    );
    expect(mcpService.createInstallPlan).toHaveBeenCalledWith(
      expect.objectContaining({
        import_preview_id: "import-1",
        draft_id: "draft-1",
        draft_digest: "a".repeat(64),
      }),
    );
  });

  it("uses the shared Wright form treatment for native controls", () => {
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);

    const source = screen.getByLabelText("Source");
    expect(source.closest("section")).toHaveClass("wright-form");
    expect(
      screen.getByRole("button", { name: "Review install plan" }),
    ).toHaveClass("wright-form__primary");
  });

  it.each([
    ["remote", "HTTPS MCP endpoint"],
    ["local", "Literal executable"],
  ])(
    "normalizes the %s source through the import boundary",
    async (value, field) => {
      const user = userEvent.setup();
      render(<OnboardingWizard isOpen onClose={vi.fn()} />);
      await user.selectOptions(screen.getByLabelText("Source"), value);
      expect(screen.getByLabelText("Source")).toHaveValue(value);
      await user.type(
        screen.getByLabelText(field),
        value === "remote" ? "https://example.invalid/mcp" : "python",
      );
      await user.click(
        screen.getByRole("button", { name: "Review install plan" }),
      );
      await screen.findByText("Confirm this installation");
      expect(mcpService.previewImport).toHaveBeenCalledOnce();
    },
  );

  it("uses catalog identity for library and host plans and shows blockers", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.createInstallPlan).mockResolvedValue({
      ...plan,
      state: "blocked",
      backend_kind: "host_bridge",
      blocking_reasons: [
        {
          code: "host_software_missing",
          message: "Desktop CAD was not found.",
          recovery: "Install or start Desktop CAD, then check again.",
        },
      ],
    });
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    await user.selectOptions(screen.getByLabelText("Source"), "host");
    await user.type(screen.getByLabelText("MCP server ID"), "desktop-cad-mcp");
    await user.click(
      screen.getByRole("button", { name: "Review install plan" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Desktop CAD was not found",
    );
    expect(
      screen.getByRole("button", { name: "Return to requirements" }),
    ).toBeVisible();
    expect(mcpService.previewImport).not.toHaveBeenCalled();
  });

  it("moves through credentials, approval, apply progress, and completion", async () => {
    const user = userEvent.setup();
    const pending = deferred<OnboardingRun>();
    const completed = vi.fn();
    vi.mocked(mcpService.applyInstallPlan).mockReturnValue(pending.promise);
    render(
      <OnboardingWizard
        isOpen
        initialCapabilityId="fixture"
        onClose={vi.fn()}
        onCompleted={completed}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Review install plan" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Continue to installation" }),
    );
    expect(screen.getByText(/secure credential flow/)).toHaveTextContent(
      "API_TOKEN",
    );
    expect(
      screen.getByTestId("credential-configuration-status"),
    ).toHaveTextContent("API_TOKEN: configured");
    await user.click(
      screen.getByRole("button", { name: "Install MCP server" }),
    );
    expect(screen.getByText(/Applying the approved plan/)).toBeVisible();
    pending.resolve(run);
    expect(await screen.findByText("Choose one workspace")).toBeVisible();
    expect(screen.getByLabelText("Workspace")).toHaveValue("workspace-a");
    expect(screen.getByText(/does not mean approved/)).toBeVisible();
    await user.click(
      screen.getByRole("button", {
        name: "Make available in this workspace",
      }),
    );
    expect(await screen.findByText("Onboarding completed")).toBeVisible();
    expect(screen.getByText(/Fixture health only/)).toBeVisible();
    expect(
      screen.getByText(/Individual tool invocation remains separate/),
    ).toBeVisible();
    expect(completed).toHaveBeenCalledOnce();
  });

  it("shows failed validation and does not offer workspace enablement", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.runCapabilityValidation).mockResolvedValue({
      ...validation,
      state: "failed",
      schema_digest: undefined,
      tool_count: undefined,
      read_only_probe: undefined,
      reason_codes: ["validation_tools_list_failed"],
    });
    render(
      <OnboardingWizard
        isOpen
        initialCapabilityId="fixture"
        onClose={vi.fn()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Review install plan" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Continue to installation" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Install MCP server" }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Installation completed; validation failed",
      }),
    ).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "registered the MCP server",
    );
    expect(screen.getByText("Validation: failed")).toBeVisible();
    expect(screen.queryByTestId("workspace-selection")).not.toBeInTheDocument();
    expect(mcpService.enableCapabilityForWorkspace).not.toHaveBeenCalled();
  });

  it("returns to exact review on a changed-plan failure", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.approveInstallPlan).mockRejectedValue(
      new CapabilityApiError(
        "Catalog or machine evidence changed.",
        "install_plan_invalidated",
        "trace-changed",
        "Create a fresh plan.",
      ),
    );
    render(
      <OnboardingWizard
        isOpen
        initialCapabilityId="fixture"
        onClose={vi.fn()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Review install plan" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Continue to installation" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Install MCP server" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "install_plan_invalidated",
      ),
    );
    expect(screen.getByText("Confirm this installation")).toBeVisible();
  });

  it("traps keyboard focus, closes with Escape, and restores the trigger", async () => {
    const user = userEvent.setup();
    const trigger = document.createElement("button");
    trigger.textContent = "Open onboarding";
    document.body.appendChild(trigger);
    trigger.focus();
    const close = vi.fn();
    render(<OnboardingWizard isOpen onClose={close} />);

    const closeButton = screen.getByRole("button", {
      name: "Close onboarding",
    });
    expect(closeButton).toHaveFocus();
    await user.tab({ shift: true });
    expect(
      screen.getByRole("button", { name: "Review install plan" }),
    ).toHaveFocus();
    await user.tab();
    expect(closeButton).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(close).toHaveBeenCalledOnce();
    await waitFor(() => expect(trigger).toHaveFocus());
    trigger.remove();
  });
});
it("uses a simplified setup entry when a listed MCP server is selected", () => {
  render(
    <OnboardingWizard
      isOpen
      initialCapabilityId="fixture-mcp"
      onClose={vi.fn()}
    />,
  );

  expect(
    screen.getByRole("heading", {
      name: "Install MCP server",
    }),
  ).toBeVisible();
  expect(screen.queryByLabelText("Source")).not.toBeInTheDocument();
  expect(screen.getByTestId("onboarding-selected-server")).toHaveTextContent(
    "fixture-mcp",
  );
  expect(
    screen.getByRole("button", { name: "Review install plan" }),
  ).toBeEnabled();
  expect(
    screen.queryByText(
      "I reviewed and completed any publisher requirements shown for this server.",
    ),
  ).not.toBeInTheDocument();
});
