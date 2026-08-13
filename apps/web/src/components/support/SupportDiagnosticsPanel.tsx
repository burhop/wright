import { useMemo, useState } from "react";

import {
  workspaceService,
  type SupportDiagnosticPreview,
} from "../../services/workspace-service";

type PanelState =
  "idle" | "previewing" | "previewed" | "exporting" | "exported" | "error";

function humanize(value: string): string {
  return value.replaceAll(/[-_]/g, " ").toLowerCase();
}

export function SupportDiagnosticsPanel({
  workspaceId,
  sessionId,
  scenarioRunId,
}: {
  workspaceId: string;
  sessionId?: string;
  scenarioRunId?: string;
}) {
  const [preview, setPreview] = useState<SupportDiagnosticPreview | null>(null);
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [confirmed, setConfirmed] = useState(false);
  const [message, setMessage] = useState(
    "Preview a local support file before choosing whether to export it.",
  );

  const expired = useMemo(
    () => Boolean(preview && Date.parse(preview.expires_at) <= Date.now()),
    [preview],
  );

  const createPreview = async () => {
    setPanelState("previewing");
    setPreview(null);
    setConfirmed(false);
    setMessage("Preparing a private local preview...");
    try {
      const next = await workspaceService.previewSupportDiagnostics(
        workspaceId,
        {
          ...(sessionId ? { session_id: sessionId } : {}),
          ...(scenarioRunId ? { scenario_run_id: scenarioRunId } : {}),
        },
      );
      setPreview(next);
      setPanelState("previewed");
      setMessage(
        "Preview is ready. Review every category before confirming export.",
      );
    } catch (error) {
      setPanelState("error");
      setMessage(
        error instanceof Error
          ? error.message
          : "Support preview is unavailable. Create a fresh preview.",
      );
    }
  };

  const exportPreview = async () => {
    if (!preview || !confirmed || expired || panelState === "exported") return;
    setPanelState("exporting");
    setMessage("Exporting the reviewed support file...");
    try {
      await workspaceService.exportSupportDiagnostics(preview);
      setPanelState("exported");
      setConfirmed(false);
      setMessage(
        "Exported once. Create a fresh preview if you need another support file.",
      );
    } catch (error) {
      setPanelState("error");
      setConfirmed(false);
      setMessage(
        error instanceof Error
          ? error.message
          : "Support file export was denied. Create a fresh preview.",
      );
    }
  };

  return (
    <section
      aria-labelledby="support-diagnostics-title"
      className="support-diagnostics"
      data-testid="support-diagnostics-panel"
    >
      <h5 id="support-diagnostics-title">Local support diagnostics</h5>
      <p>
        Build a small, privacy-filtered support file for this engineering run.
        Nothing is uploaded automatically.
      </p>
      <p
        aria-live="polite"
        role={panelState === "error" || expired ? "alert" : "status"}
      >
        {expired ? "Preview expired. Create a fresh preview." : message}
      </p>
      <div className="support-diagnostics__actions">
        <button
          data-testid="support-diagnostics-preview"
          disabled={panelState === "previewing" || panelState === "exporting"}
          onClick={() => void createPreview()}
          type="button"
        >
          {preview ? "Create a fresh preview" : "Preview support file"}
        </button>
      </div>
      {preview ? (
        <div className="support-diagnostics__preview">
          <p>
            <strong>Status:</strong> {humanize(preview.snapshot.summary.status)}
            .
            <br />
            <strong>Next action:</strong>{" "}
            {humanize(preview.snapshot.summary.next_action)}.
          </p>
          <h6>Preview contents</h6>
          <ul>
            {preview.snapshot.categories.map((category) => (
              <li key={category.name}>
                {humanize(category.name)}: {category.disposition}
                {category.item_count ? ` (${category.item_count})` : ""} —{" "}
                {humanize(category.reason)}
              </li>
            ))}
          </ul>
          {preview.snapshot.failures.length ? (
            <>
              <h6>Recorded failures and recovery</h6>
              <ul>
                {preview.snapshot.failures.map((failure, index) => (
                  <li key={`${failure.stage}-${failure.reason}-${index}`}>
                    <strong>{humanize(failure.stage)}</strong>:{" "}
                    {humanize(failure.reason)}; cleanup{" "}
                    {humanize(failure.cleanup)}; recovery{" "}
                    {humanize(failure.recovery)}.
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          <label className="support-diagnostics__confirmation">
            <input
              checked={confirmed}
              data-testid="support-diagnostics-confirm"
              disabled={
                expired ||
                panelState === "exporting" ||
                panelState === "exported"
              }
              onChange={(event) => setConfirmed(event.target.checked)}
              type="checkbox"
            />
            I reviewed this current preview and want to export it locally.
          </label>
          <div className="support-diagnostics__actions">
            <button
              data-testid="support-diagnostics-export"
              disabled={
                !confirmed ||
                expired ||
                panelState === "exporting" ||
                panelState === "exported"
              }
              onClick={() => void exportPreview()}
              type="button"
            >
              {panelState === "exporting"
                ? "Exporting..."
                : "Export reviewed support file"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
