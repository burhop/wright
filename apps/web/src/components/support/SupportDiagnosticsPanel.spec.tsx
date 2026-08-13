import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workspaceService } from "../../services/workspace-service";
import { SupportDiagnosticsPanel } from "./SupportDiagnosticsPanel";

vi.mock("../../services/workspace-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...original,
    workspaceService: {
      previewSupportDiagnostics: vi.fn(),
      exportSupportDiagnostics: vi.fn(),
    },
  };
});

const preview = {
  snapshot: {
    schema_version: "1.0" as const,
    snapshot_id: "snapshot_12345678",
    created_at: "2026-08-13T12:00:00Z",
    expires_at: "2099-08-13T12:05:00Z",
    workspace_id: "workspace-1",
    principal_digest: `sha256:${"a".repeat(64)}`,
    scope: { session_id: "session-1", scenario_run_id: "scenario-run" },
    summary: {
      status: "degraded" as const,
      reason: "FAILURES_RECORDED",
      next_action: "INSPECT_RECOVERY",
    },
    providers: [
      {
        kind: "rivet" as const,
        provider_id: "wright-rivet",
        status: "failed" as const,
        identity_digest: `sha256:${"b".repeat(64)}`,
      },
    ],
    state_inventory: {
      schema_version: "1.0" as const,
      data_schema: 16,
      catalog_snapshot: {
        channel: "stable",
        sequence: 1,
        digest: `sha256:${"c".repeat(64)}`,
        state: "active" as const,
      },
      counts: { scenario_reports: 1 },
      digests: { program_material: `sha256:${"d".repeat(64)}` },
      storage: [],
    },
    failures: [
      {
        stage: "engineering-scenario",
        provider_kind: "rivet" as const,
        reason: "SCENARIO_FAILED",
        cleanup: "residue-possible" as const,
        recovery: "INSPECT_BEFORE_RETRY",
      },
    ],
    categories: [
      {
        name: "provider-status",
        disposition: "included" as const,
        item_count: 1,
        reason: "INCLUDED",
      },
      {
        name: "raw-engineering-payloads",
        disposition: "omitted" as const,
        item_count: 0,
        reason: "PROPRIETARY_CONTENT_FORBIDDEN",
      },
      {
        name: "private-paths",
        disposition: "redacted" as const,
        item_count: 0,
        reason: "PRIVATE_PATHS_FORBIDDEN",
      },
    ],
    snapshot_digest: `sha256:${"e".repeat(64)}`,
  },
  snapshot_digest: `sha256:${"e".repeat(64)}`,
  confirmation_token: "confirmation-token",
  expires_at: "2099-08-13T12:05:00Z",
  filename: "wright-support-workspace-1.json",
};

describe("SupportDiagnosticsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValue(
      preview,
    );
    vi.mocked(workspaceService.exportSupportDiagnostics).mockResolvedValue();
  });

  it("requires preview and an explicit current confirmation before one export", async () => {
    const user = userEvent.setup();
    render(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sessionId="session-1"
        scenarioRunId="scenario-run"
      />,
    );

    expect(
      screen.getByText(/nothing is uploaded automatically/i),
    ).toBeVisible();
    expect(screen.queryByRole("checkbox")).toBeNull();
    await user.click(screen.getByTestId("support-diagnostics-preview"));

    expect(await screen.findByText(/Preview is ready/i)).toBeVisible();
    expect(screen.getByText(/raw engineering payloads/i)).toBeVisible();
    expect(screen.getByText(/omitted/i)).toBeVisible();
    expect(screen.getByText(/private paths/i)).toBeVisible();
    expect(screen.getByText(/redacted/i)).toBeVisible();
    expect(screen.getByText(/inspect before retry/i)).toBeVisible();
    const exportButton = screen.getByTestId("support-diagnostics-export");
    expect(exportButton).toBeDisabled();

    await user.click(screen.getByTestId("support-diagnostics-confirm"));
    expect(exportButton).toBeEnabled();
    await user.click(exportButton);

    expect(workspaceService.previewSupportDiagnostics).toHaveBeenCalledWith(
      "workspace-1",
      { session_id: "session-1", scenario_run_id: "scenario-run" },
    );
    expect(workspaceService.exportSupportDiagnostics).toHaveBeenCalledWith(
      preview,
    );
    expect(await screen.findByText(/Exported once/i)).toBeVisible();
    expect(exportButton).toBeDisabled();
  });

  it("keeps a safe actionable error and allows a fresh preview", async () => {
    const user = userEvent.setup();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockRejectedValueOnce(
      new Error("Preview expired. Create a fresh preview."),
    );
    render(<SupportDiagnosticsPanel workspaceId="workspace-1" />);

    await user.click(screen.getByTestId("support-diagnostics-preview"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Preview expired. Create a fresh preview.",
    );
    expect(screen.getByTestId("support-diagnostics-preview")).toBeEnabled();
  });

  it("supports keyboard confirmation, honest expiry, and no replay after remount", async () => {
    const user = userEvent.setup();
    const rendered = render(
      <SupportDiagnosticsPanel workspaceId="workspace-1" />,
    );
    const previewButton = screen.getByTestId("support-diagnostics-preview");
    previewButton.focus();
    await user.keyboard("{Enter}");
    const confirmation = await screen.findByTestId(
      "support-diagnostics-confirm",
    );
    confirmation.focus();
    await user.keyboard(" ");
    expect(screen.getByTestId("support-diagnostics-export")).toBeEnabled();

    rendered.unmount();
    render(<SupportDiagnosticsPanel workspaceId="workspace-1" />);
    expect(screen.queryByRole("checkbox")).toBeNull();
    expect(workspaceService.exportSupportDiagnostics).not.toHaveBeenCalled();
  });

  it("disables export for an expired preview and names the recovery", async () => {
    const user = userEvent.setup();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValueOnce(
      {
        ...preview,
        expires_at: "2000-01-01T00:00:00Z",
        snapshot: { ...preview.snapshot, expires_at: "2000-01-01T00:00:00Z" },
      },
    );
    render(<SupportDiagnosticsPanel workspaceId="workspace-1" />);
    await user.click(screen.getByTestId("support-diagnostics-preview"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Preview expired. Create a fresh preview.",
    );
    expect(screen.getByTestId("support-diagnostics-confirm")).toBeDisabled();
    expect(screen.getByTestId("support-diagnostics-export")).toBeDisabled();
  });
});
