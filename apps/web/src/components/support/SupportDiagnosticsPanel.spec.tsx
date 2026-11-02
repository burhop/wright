import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type SupportDiagnosticPreview,
} from "../../services/workspace-service";
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
    scope: {},
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
    const scopedPreview = {
      ...preview,
      snapshot: {
        ...preview.snapshot,
        scope: { session_id: "session-1", scenario_run_id: "scenario-run" },
      },
    };
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValue(
      scopedPreview,
    );
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
      scopedPreview,
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

  const sourcePreview = (runId = "source-run"): SupportDiagnosticPreview => ({
    ...preview,
    snapshot: {
      ...preview.snapshot,
      scope: { source_run_id: runId },
      source_run: {
        run_id: runId,
        source_digest: `sha256:${"1".repeat(64)}`,
        record_digest: `sha256:${"2".repeat(64)}`,
        recorded_status: "failed",
        started_at: "2026-10-23T12:00:00Z",
        ended_at: "2026-10-23T12:00:05Z",
        event_count: 102,
        events_truncated: true,
        metadata_omitted: true,
        events: [
          {
            sequence: 102,
            kind: "step_completed",
            step_id: "create_mesh",
            at: "2026-10-23T12:00:05Z",
            start_sequence: 101,
            elapsed_ms: 2000,
          },
        ],
      },
    },
  });

  it("previews the exact source run without claiming session scope or automatically exporting", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValue(
      sourcePreview(),
    );
    render(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sessionId="unrelated-session"
        sourceRunId="source-run"
        onNavigate={onNavigate}
      />,
    );
    expect(workspaceService.previewSupportDiagnostics).not.toHaveBeenCalled();
    await user.click(screen.getByTestId("support-diagnostics-preview"));
    expect(
      await screen.findByTestId("support-diagnostics-source-run"),
    ).toHaveTextContent("recorded duration 2000 ms from event 101");
    expect(screen.getByText(/only the latest 100/i)).toBeVisible();
    expect(
      screen.getByText(/unverified event metadata was omitted/i),
    ).toBeVisible();
    expect(workspaceService.previewSupportDiagnostics).toHaveBeenCalledWith(
      "workspace-1",
      { source_run_id: "source-run" },
    );
    expect(workspaceService.exportSupportDiagnostics).not.toHaveBeenCalled();
    await user.click(
      screen.getByRole("button", { name: "Inspect step create_mesh" }),
    );
    expect(onNavigate).toHaveBeenCalledWith({
      kind: "block",
      block_id: "create_mesh",
      run_id: "source-run",
    });
    expect(screen.getByTestId("support-diagnostics-export")).toBeDisabled();
  });

  it("resets a reviewed confirmation when the run changes", async () => {
    const user = userEvent.setup();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValue(
      sourcePreview(),
    );
    const rendered = render(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sourceRunId="source-run"
      />,
    );
    await user.click(screen.getByTestId("support-diagnostics-preview"));
    await user.click(await screen.findByTestId("support-diagnostics-confirm"));
    expect(screen.getByTestId("support-diagnostics-export")).toBeEnabled();
    rendered.rerender(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sourceRunId="next-run"
      />,
    );
    expect(screen.queryByTestId("support-diagnostics-confirm")).toBeNull();
    expect(screen.queryByTestId("support-diagnostics-source-run")).toBeNull();
    expect(workspaceService.exportSupportDiagnostics).not.toHaveBeenCalled();
  });

  it("ignores a late preview for the previous run and rejects a mismatched response", async () => {
    const user = userEvent.setup();
    let resolve!: (value: SupportDiagnosticPreview) => void;
    vi.mocked(workspaceService.previewSupportDiagnostics).mockReturnValueOnce(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const rendered = render(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sourceRunId="source-run"
      />,
    );
    await user.click(screen.getByTestId("support-diagnostics-preview"));
    rendered.rerender(
      <SupportDiagnosticsPanel
        workspaceId="workspace-1"
        sourceRunId="next-run"
      />,
    );
    await act(async () => resolve(sourcePreview()));
    expect(screen.queryByTestId("support-diagnostics-source-run")).toBeNull();
    vi.mocked(workspaceService.previewSupportDiagnostics).mockResolvedValueOnce(
      sourcePreview(),
    );
    await user.click(screen.getByTestId("support-diagnostics-preview"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "different diagnostic scope",
    );
    expect(screen.queryByTestId("support-diagnostics-confirm")).toBeNull();
  });

  it("expires a visible confirmation when the preview lifetime ends", async () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(new Date("2026-10-23T12:00:00Z"));
      const result = { ...preview, expires_at: "2026-10-23T12:00:01Z" };
      vi.mocked(
        workspaceService.previewSupportDiagnostics,
      ).mockResolvedValueOnce(result);
      render(<SupportDiagnosticsPanel workspaceId="workspace-1" />);
      await act(async () => {
        screen.getByTestId("support-diagnostics-preview").click();
      });
      await act(async () => {
        screen.getByTestId("support-diagnostics-confirm").click();
      });
      expect(screen.getByTestId("support-diagnostics-export")).toBeEnabled();
      await act(async () => {
        vi.advanceTimersByTime(1001);
      });
      expect(screen.getByRole("alert")).toHaveTextContent("Preview expired");
      expect(screen.getByTestId("support-diagnostics-export")).toBeDisabled();
    } finally {
      vi.useRealTimers();
    }
  });
});
