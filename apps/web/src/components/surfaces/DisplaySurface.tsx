import { useEffect, useMemo, useState } from "react";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import {
  deleteDisplay,
  getDisplayHistory,
  getDisplayProjection,
  getDisplayVerification,
  type DisplayHistoryItem,
  type DisplayProjection,
} from "../../services/surfaces/surface-client";
import { PlotlyRenderer } from "../../services/surfaces/renderers/plotly-renderer";
import {
  SafeRepresentationRenderer,
  type SafeDisplayRepresentation,
} from "../../services/surfaces/renderers/safe-renderers";

interface Props {
  readonly descriptor: SurfaceDescriptor;
  readonly sessionId: string;
  readonly onDeleted: (retentionStatus: string) => void;
}

function safeFallback(
  projection: DisplayProjection,
  representation: SafeDisplayRepresentation | undefined,
) {
  return representation ? (
    <SafeRepresentationRenderer
      representation={representation}
      description={projection.accessibilityDescription}
    />
  ) : (
    <p>{projection.accessibilityDescription}</p>
  );
}

export function DisplaySurface({ descriptor, sessionId, onDeleted }: Props) {
  const [projection, setProjection] = useState<DisplayProjection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<DisplayHistoryItem[] | null>(null);
  const [verification, setVerification] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [retentionStatus, setRetentionStatus] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    getDisplayProjection(
      descriptor.surfaceId,
      descriptor.workspaceId,
      sessionId,
      descriptor.revision,
    )
      .then((value) => {
        if (active) setProjection(value);
      })
      .catch((reason: unknown) => {
        if (active)
          setError(reason instanceof Error ? reason.message : String(reason));
      });
    return () => {
      active = false;
    };
  }, [
    descriptor.revision,
    descriptor.surfaceId,
    descriptor.workspaceId,
    sessionId,
  ]);

  const ordered = useMemo(
    () =>
      [...(projection?.representations ?? [])].sort(
        (left, right) =>
          Number(left.fallbackRank ?? 0) - Number(right.fallbackRank ?? 0),
      ),
    [projection],
  );

  if (error || (projection && ordered.length === 0)) {
    return (
      <div
        role="alert"
        data-testid="surface-display-error"
        style={{ padding: 24 }}
      >
        This display is unavailable.{" "}
        {error ?? "No safe representation was provided."}
        <button data-testid="surface-diagnostics" type="button">
          Open diagnostics
        </button>
      </div>
    );
  }
  if (!projection) return <div role="status">Loading display…</div>;

  const primary = ordered[0];
  const fallback = ordered.find(
    (item) => item.mediaType !== "application/vnd.plotly.v1+json",
  );

  return (
    <section
      data-testid="display-surface"
      aria-label={projection.title}
      style={{ height: "100%", overflow: "auto", padding: 16 }}
    >
      <header style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <h2 style={{ marginRight: "auto" }}>{projection.title}</h2>
        <span>Revision {projection.revision}</span>
        <button
          data-testid="surface-history"
          type="button"
          onClick={() =>
            void getDisplayHistory(
              descriptor.surfaceId,
              descriptor.workspaceId,
              sessionId,
            ).then(setHistory)
          }
        >
          History
        </button>
        <button
          data-testid="surface-verification"
          type="button"
          onClick={() =>
            void getDisplayVerification(
              descriptor.surfaceId,
              descriptor.workspaceId,
              sessionId,
            ).then(setVerification)
          }
        >
          Verify
        </button>
        <button
          data-testid="surface-delete-output"
          type="button"
          onClick={() => {
            setHistory(null);
            setVerification(null);
            setConfirmDelete(true);
          }}
        >
          Delete…
        </button>
      </header>
      {primary.mediaType === "application/vnd.plotly.v1+json" ? (
        <PlotlyRenderer
          representation={{
            mediaType: "application/vnd.plotly.v1+json",
            encoding: "json",
            data: primary.data,
          }}
          description={projection.accessibilityDescription}
          fallback={safeFallback(projection, fallback)}
        />
      ) : (
        <SafeRepresentationRenderer
          representation={primary}
          description={projection.accessibilityDescription}
        />
      )}
      {history && (
        <div role="dialog" aria-label="Display revision history">
          <h3>Revision history</h3>
          <ol>
            {history.map((item) => (
              <li key={item.artifactId}>
                Revision {item.revision}
                {item.current ? " (current)" : ""}
              </li>
            ))}
          </ol>
          <button type="button" onClick={() => setHistory(null)}>
            Close history
          </button>
        </div>
      )}
      {verification && (
        <div role="dialog" aria-label="Artifact verification">
          <h3>Artifact verification</h3>
          <p>
            {verification.prompt
              ? String(verification.prompt)
              : "Direct execution (no prompt)"}
          </p>
          <pre>
            {JSON.stringify(verification.effective_constraints, null, 2)}
          </pre>
          <pre>{String(verification.script ?? "")}</pre>
          <p>Script revision {String(verification.script_revision)}</p>
          <button type="button" onClick={() => setVerification(null)}>
            Close verification
          </button>
        </div>
      )}
      {confirmDelete && (
        <div role="dialog" aria-label="Delete durable output">
          <p>
            This durable output and its history will be removed and cannot be
            recovered. Content-addressed payload cleanup is scheduled by
            retention policy.
          </p>
          <button
            type="button"
            onClick={() =>
              void deleteDisplay(
                descriptor.surfaceId,
                descriptor.workspaceId,
                sessionId,
              ).then((result) => {
                setConfirmDelete(false);
                setRetentionStatus(result.retentionStatus);
                onDeleted(result.retentionStatus);
              })
            }
          >
            Delete output
          </button>
          <button type="button" onClick={() => setConfirmDelete(false)}>
            Cancel
          </button>
        </div>
      )}
      {retentionStatus && (
        <p role="status">{retentionStatus.replaceAll("_", " ")}</p>
      )}
    </section>
  );
}
