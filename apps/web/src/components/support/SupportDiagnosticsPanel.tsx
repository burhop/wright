import { useEffect, useId, useState } from "react";
import type { NavigationTarget } from "@wright/process-client";
import { NavigationButton } from "@wright/ui-kit";

import {
  workspaceService,
  type SupportDiagnosticPreview,
} from "../../services/workspace-service";

type PanelState =
  "idle" | "previewing" | "previewed" | "exporting" | "exported" | "error";

function humanize(value: string): string {
  return value.replaceAll(/[-_]/g, " ").toLowerCase();
}

interface SupportDiagnosticsPanelProps {
  workspaceId: string;
  sessionId?: string;
  scenarioRunId?: string;
  sourceRunId?: string;
  onNavigate?: (target: NavigationTarget) => void;
}

export function SupportDiagnosticsPanel(props: SupportDiagnosticsPanelProps) {
  // A confirmation belongs to one exact scope, including after pending reads.
  const key = JSON.stringify([
    props.workspaceId,
    props.sessionId,
    props.scenarioRunId,
    props.sourceRunId,
  ]);
  return <SupportDiagnosticsController key={key} {...props} />;
}

function SupportDiagnosticsController({
  workspaceId,
  sessionId,
  scenarioRunId,
  sourceRunId,
  onNavigate,
}: SupportDiagnosticsPanelProps) {
  const titleId = useId();
  const [preview, setPreview] = useState<SupportDiagnosticPreview | null>(null);
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [confirmed, setConfirmed] = useState(false);
  const [message, setMessage] = useState(
    "Preview a local support file before choosing whether to export it.",
  );

  const [now, setNow] = useState(Date.now);
  const expired = Boolean(preview && Date.parse(preview.expires_at) <= now);
  useEffect(() => {
    if (!preview) return;
    const delay = Date.parse(preview.expires_at) - Date.now();
    if (delay <= 0) {
      setNow(Date.now());
      return;
    }
    const timeout = window.setTimeout(
      () => setNow(Date.now()),
      Math.min(delay, 2_147_483_647),
    );
    return () => window.clearTimeout(timeout);
  }, [preview]);

  const createPreview = async () => {
    setPanelState("previewing");
    setPreview(null);
    setConfirmed(false);
    setMessage("Preparing a private local preview...");
    try {
      const next = await workspaceService.previewSupportDiagnostics(
        workspaceId,
        {
          ...(sourceRunId
            ? { source_run_id: sourceRunId }
            : {
                ...(sessionId ? { session_id: sessionId } : {}),
                ...(scenarioRunId ? { scenario_run_id: scenarioRunId } : {}),
              }),
        },
      );
      if (
        next.snapshot.workspace_id !== workspaceId ||
        (next.snapshot.scope.source_run_id ?? undefined) !== sourceRunId ||
        (next.snapshot.scope.session_id ?? undefined) !==
          (sourceRunId ? undefined : sessionId) ||
        (next.snapshot.scope.scenario_run_id ?? undefined) !==
          (sourceRunId ? undefined : scenarioRunId) ||
        (sourceRunId && next.snapshot.source_run?.run_id !== sourceRunId)
      )
        throw new Error(
          "The preview belongs to a different diagnostic scope. Create a fresh preview.",
        );
      setNow(Date.now());
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
      aria-labelledby={titleId}
      className="support-diagnostics"
      data-testid="support-diagnostics-panel"
    >
      <h5 id={titleId}>Local support diagnostics</h5>
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
            <strong>Diagnostic summary:</strong>{" "}
            {humanize(preview.snapshot.summary.reason)}
            .
            <br />
            <strong>Next action:</strong>{" "}
            {humanize(preview.snapshot.summary.next_action)}.
          </p>
          {preview.snapshot.source_run ? (
            <div data-testid="support-diagnostics-source-run">
              <h6>Recorded run evidence</h6>
              <p>
                Run <code>{preview.snapshot.source_run.run_id}</code>; recorded
                status: {humanize(preview.snapshot.source_run.recorded_status)}.
                These are saved observations, not a live progress estimate.
                Current state and recovery stay in the working view.
              </p>
              <details>
                <summary>Evidence identities and recorded times</summary>
                <p>
                  Source digest:{" "}
                  <code>{preview.snapshot.source_run.source_digest}</code>
                </p>
                <p>
                  Canonical record digest:{" "}
                  <code>{preview.snapshot.source_run.record_digest}</code>
                </p>
                {preview.snapshot.source_run.started_at && (
                  <p>
                    Recorded start:{" "}
                    <time>{preview.snapshot.source_run.started_at}</time>
                  </p>
                )}
                {preview.snapshot.source_run.ended_at && (
                  <p>
                    Recorded execution end:{" "}
                    <time>{preview.snapshot.source_run.ended_at}</time>
                  </p>
                )}
                <p>
                  {preview.snapshot.source_run.event_count} total recorded
                  events. Engineering payloads are omitted.
                </p>
              </details>
              {preview.snapshot.source_run.events_truncated && (
                <p>
                  Only the latest 100 relevant timing events are included.
                  Earlier events remain in the local run evidence.
                </p>
              )}
              {preview.snapshot.source_run.metadata_omitted && (
                <p>Some unverified event metadata was omitted.</p>
              )}
              <ol aria-label="Recorded run timing events">
                {preview.snapshot.source_run.events.map((event) => (
                  <li key={event.sequence}>
                    Event {event.sequence}: {humanize(event.kind)}
                    {event.step_id && (
                      <>
                        {" "}
                        — <code>{event.step_id}</code>
                      </>
                    )}
                    {event.at && (
                      <>
                        {" "}
                        at <time>{event.at}</time>
                      </>
                    )}
                    {event.elapsed_ms != null && (
                      <>
                        ; recorded duration {event.elapsed_ms} ms from event{" "}
                        {event.start_sequence}
                      </>
                    )}
                    {event.reason && <>; {humanize(event.reason)}</>}
                    {onNavigate && event.step_id && (
                      <NavigationButton
                        title={`Inspect step ${event.step_id}`}
                        target={{
                          kind: "block",
                          block_id: event.step_id,
                          run_id: preview.snapshot.source_run!.run_id,
                        }}
                        onNavigate={onNavigate}
                      />
                    )}
                  </li>
                ))}
              </ol>
              {onNavigate && (
                <NavigationButton
                  title="Inspect recorded run"
                  target={{
                    kind: "run",
                    run_id: preview.snapshot.source_run.run_id,
                  }}
                  onNavigate={onNavigate}
                />
              )}
            </div>
          ) : null}
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
