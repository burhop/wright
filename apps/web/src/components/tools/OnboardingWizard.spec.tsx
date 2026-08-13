import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CapabilityApiError,
  mcpService,
  type ImportPreview,
  type InstallPlan,
  type OnboardingRun,
} from "../../services/mcp-service";
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
    },
  };
});

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
  });

  it("starts with all supported sources and makes no request", () => {
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    expect(screen.getByRole("dialog")).toBeVisible();
    expect(
      screen.getByRole("option", { name: "Capability Library" }),
    ).toBeVisible();
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
      screen.getByRole("button", { name: "Create read-only plan" }),
    );
    expect(
      screen.getByText(/Normalizing the source and checking this machine/),
    ).toBeVisible();
    pending.resolve(preview);

    expect(await screen.findByText("Review exact plan")).toBeVisible();
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
        screen.getByRole("button", { name: "Create read-only plan" }),
      );
      await screen.findByText("Review exact plan");
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
          message: "Solid Edge was not found.",
          recovery: "Install or start Solid Edge, then check again.",
        },
      ],
    });
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    await user.selectOptions(screen.getByLabelText("Source"), "host");
    await user.type(screen.getByLabelText("Capability ID"), "solid-edge-mcp");
    await user.click(
      screen.getByRole("button", { name: "Create read-only plan" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Solid Edge was not found",
    );
    expect(
      screen.getByRole("button", { name: "Continue to credentials" }),
    ).toBeDisabled();
    expect(mcpService.previewImport).not.toHaveBeenCalled();
  });

  it("moves through credentials, approval, apply progress, and completion", async () => {
    const user = userEvent.setup();
    const pending = deferred<OnboardingRun>();
    const completed = vi.fn();
    vi.mocked(mcpService.applyInstallPlan).mockReturnValue(pending.promise);
    render(
      <OnboardingWizard isOpen onClose={vi.fn()} onCompleted={completed} />,
    );
    await user.type(screen.getByLabelText("Capability ID"), "fixture");
    await user.click(
      screen.getByRole("button", { name: "Create read-only plan" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Continue to credentials" }),
    );
    expect(screen.getByText(/API_TOKEN/)).toHaveTextContent(
      "secure credential flow",
    );
    await user.click(
      screen.getByRole("button", { name: "Approve and apply exact plan" }),
    );
    expect(screen.getByText(/Applying the approved plan/)).toBeVisible();
    pending.resolve(run);

    expect(await screen.findByText("Onboarding completed")).toBeVisible();
    expect(completed).toHaveBeenCalledOnce();
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
    render(<OnboardingWizard isOpen onClose={vi.fn()} />);
    await user.type(screen.getByLabelText("Capability ID"), "fixture");
    await user.click(
      screen.getByRole("button", { name: "Create read-only plan" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Continue to credentials" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Approve and apply exact plan" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "install_plan_invalidated",
      ),
    );
    expect(screen.getByText("Review exact plan")).toBeVisible();
  });
});
