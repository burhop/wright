import { useCallback, useEffect, useRef, useState } from "react";

import { workspaceService } from "../../services/workspace-service";
import { hostAdapter } from "../../services/host-adapter";

interface DirectBrepSurfaceProps {
  readonly sessionId: string;
}

export function DirectBrepSurface({ sessionId }: DirectBrepSurfaceProps) {
  const [controlUrl, setControlUrl] = useState<string | null>(null);
  const [status, setStatus] = useState(
    "Starting BREP on its dedicated port...",
  );
  const [error, setError] = useState<string | null>(null);
  const [generation, setGeneration] = useState(0);
  const connectionRef = useRef<{
    sessionId: string;
    promise: ReturnType<typeof workspaceService.openBrepPanel>;
  } | null>(null);

  const connect = useCallback(async () => {
    setControlUrl(null);
    setError(null);
    setStatus("Starting BREP on its dedicated port...");
    const existingConnection = connectionRef.current;
    const connection =
      existingConnection?.sessionId === sessionId
        ? existingConnection.promise
        : workspaceService.openBrepPanel(sessionId);
    connectionRef.current = { sessionId, promise: connection };
    try {
      const panel = await connection;
      setControlUrl(panel.control_url);
      setStatus(
        panel.connected
          ? "BREP is connected to Wright AI tools."
          : "BREP is ready; connecting its canvas to Wright AI tools...",
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "BREP is unavailable");
    } finally {
      if (connectionRef.current?.promise === connection) {
        connectionRef.current = null;
      }
    }
  }, [sessionId]);

  useEffect(() => {
    void connect();
  }, [connect, generation]);

  return (
    <section
      data-testid="direct-brep-surface"
      aria-label="BREP application panel"
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: "var(--color-neutral, #111827)",
      }}
    >
      <div
        style={{
          minHeight: 34,
          padding: "0 var(--space-sm, 8px)",
          display: "flex",
          alignItems: "center",
          gap: "var(--space-sm, 8px)",
          borderBottom: "1px solid var(--color-border, #2d3748)",
          color: error
            ? "var(--color-error, #ef4444)"
            : "var(--color-secondary, #a0aec0)",
          fontSize: "0.72rem",
        }}
      >
        <span role={error ? "alert" : "status"} style={{ flex: 1 }}>
          {error ?? status}
        </span>
        {error && (
          <button
            type="button"
            onClick={() => setGeneration((value) => value + 1)}
            style={{ cursor: "pointer" }}
          >
            Retry
          </button>
        )}
        {controlUrl && (
          <button
            type="button"
            aria-label="Open BREP in browser"
            title="Open BREP in browser"
            onClick={() =>
              void hostAdapter.openExternal(controlUrl, {
                approvedDirectUrl: true,
              })
            }
            style={{ cursor: "pointer" }}
          >
            Open in browser
          </button>
        )}
      </div>
      {controlUrl ? (
        <iframe
          key={controlUrl}
          data-testid="brep-application-frame"
          title="BREP canvas"
          src={controlUrl}
          onLoad={() => setStatus("BREP is connected to Wright AI tools.")}
          allow="clipboard-read; clipboard-write; fullscreen"
          style={{ width: "100%", flex: 1, border: 0, background: "#111827" }}
        />
      ) : (
        <div
          data-testid="brep-panel-loading"
          style={{
            flex: 1,
            display: "grid",
            placeItems: "center",
            color: "var(--color-secondary, #a0aec0)",
          }}
        >
          {error ? "BREP did not start." : "Preparing the BREP canvas..."}
        </div>
      )}
    </section>
  );
}
