import { useCallback, useEffect, useState } from "react";
import {
  CapabilityApiError,
  mcpService,
  type CatalogStateResponse,
  type CatalogUpdatePreview,
} from "../../services/mcp-service";

interface CatalogPanelError {
  message: string;
  code?: string;
  traceId?: string;
  recovery?: string;
}

function displayError(error: unknown): CatalogPanelError {
  if (error instanceof CapabilityApiError) {
    return {
      message: error.message,
      code: error.errorCode,
      traceId: error.traceId,
      recovery: error.recovery,
    };
  }
  return { message: "The catalog operation could not be completed." };
}

export function CatalogUpdatePanel({
  onCatalogChanged,
}: {
  onCatalogChanged?: () => void;
}) {
  const [state, setState] = useState<CatalogStateResponse | null>(null);
  const [preview, setPreview] = useState<CatalogUpdatePreview | null>(null);
  const [operation, setOperation] = useState<
    "loading" | "idle" | "checking" | "activating" | "rolling-back"
  >("loading");
  const [error, setError] = useState<CatalogPanelError | null>(null);

  const loadState = useCallback(async () => {
    try {
      setState(await mcpService.getCatalogState());
      setError(null);
    } catch (caught) {
      setError(displayError(caught));
    } finally {
      setOperation("idle");
    }
  }, []);

  useEffect(() => {
    void loadState();
  }, [loadState]);

  const checkForUpdates = async () => {
    setOperation("checking");
    setError(null);
    setPreview(null);
    try {
      setPreview(
        await mcpService.previewCatalogUpdate({ configured_channel: true }),
      );
    } catch (caught) {
      setError(displayError(caught));
    } finally {
      setOperation("idle");
    }
  };

  const activate = async () => {
    if (!preview) return;
    setOperation("activating");
    setError(null);
    try {
      await mcpService.activateCatalogUpdate(
        preview.preview_id,
        preview.preview_digest,
      );
      await loadState();
      setPreview(null);
      onCatalogChanged?.();
    } catch (caught) {
      setError(displayError(caught));
    } finally {
      setOperation("idle");
    }
  };

  const rollback = async () => {
    if (!state?.previous_snapshot_id) return;
    setOperation("rolling-back");
    setError(null);
    try {
      await mcpService.rollbackCatalog(
        state.active_snapshot_id,
        state.previous_snapshot_id,
      );
      await loadState();
      setPreview(null);
      onCatalogChanged?.();
    } catch (caught) {
      setError(displayError(caught));
    } finally {
      setOperation("idle");
    }
  };

  const hasChannel = Boolean(state?.configured_channels.length);
  const busy = operation !== "idle";

  return (
    <section
      aria-labelledby="catalog-update-title"
      data-testid="catalog-update-panel"
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-lg)",
        background: "var(--color-surface-subtle)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: "var(--space-lg)",
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 id="catalog-update-title" style={{ margin: 0 }}>
            Capability catalog
          </h2>
          {state && (
            <p data-testid="catalog-active-source" style={{ marginBottom: 0 }}>
              Active source: <strong>{state.active_channel}</strong>, sequence{" "}
              {state.active_sequence}
            </p>
          )}
          {!hasChannel && state && (
            <p style={{ color: "var(--color-text-muted)", marginBottom: 0 }}>
              No signed update channel is configured. The bundled catalog stays
              available offline.
            </p>
          )}
        </div>
        <div
          style={{ display: "flex", gap: "var(--space-sm)", flexWrap: "wrap" }}
        >
          <button
            type="button"
            disabled={!hasChannel || busy}
            onClick={checkForUpdates}
          >
            {operation === "checking" ? "Checking…" : "Check for updates"}
          </button>
          <button
            type="button"
            disabled={!state?.previous_snapshot_id || busy}
            onClick={rollback}
          >
            {operation === "rolling-back" ? "Rolling back…" : "Roll back"}
          </button>
        </div>
      </div>

      {operation === "loading" && <p role="status">Loading catalog state…</p>}
      {state?.diagnostic && (
        <p role="status">
          {state.diagnostic.message} {state.diagnostic.recovery}
        </p>
      )}
      {error && (
        <div role="alert" style={{ marginTop: "var(--space-md)" }}>
          <strong>{error.message}</strong>
          {error.recovery && <div>{error.recovery}</div>}
          {error.code && <div>Error code: {error.code}</div>}
          {error.traceId && <div>Trace: {error.traceId}</div>}
        </div>
      )}

      {preview && (
        <div
          data-testid="catalog-update-preview"
          style={{ marginTop: "var(--space-lg)" }}
        >
          <h3>Verified signed update</h3>
          <p>
            {preview.diff.summary.added} added · {preview.diff.summary.changed}{" "}
            changed · {preview.diff.summary.removed} removed
          </p>
          <p>{preview.risk_summary.note}</p>
          <button type="button" disabled={busy} onClick={activate}>
            {operation === "activating" ? "Activating…" : "Activate update"}
          </button>
        </div>
      )}

      {state && state.history.length > 0 && (
        <details style={{ marginTop: "var(--space-lg)" }}>
          <summary>Catalog history</summary>
          <ol aria-label="Catalog history">
            {state.history.map((item) => (
              <li key={item.activation_id}>
                {item.kind} · {item.result} · {item.actor}
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
