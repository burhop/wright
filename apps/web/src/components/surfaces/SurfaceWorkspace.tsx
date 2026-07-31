import { useEffect, useMemo, useState } from "react";

import { listSurfaces } from "../../services/surfaces/surface-client";
import {
  createSurfaceState,
  restoreSurfaceState,
  serializeSurfaceState,
  useSurfaces,
  useSurfaceUpdates,
} from "../../store/surfaces";
import { DisplaySurface } from "./DisplaySurface";
import { LiveAppSurface } from "./LiveAppSurface";
import { SurfaceDeck } from "./SurfaceDeck";

interface Props {
  readonly workspaceId: string;
  readonly sessionId: string;
}

export function SurfaceWorkspace({ workspaceId, sessionId }: Props) {
  const { state, dispatch } = useSurfaces();
  const [notice, setNotice] = useState<string | null>(null);
  const [restoredStorageKey, setRestoredStorageKey] = useState<string | null>(
    null,
  );
  const [reconciledStorageKey, setReconciledStorageKey] = useState<
    string | null
  >(null);
  const storageKey = useMemo(
    () => `wright.workspaceSurfaces.state.${workspaceId}.${sessionId}`,
    [sessionId, workspaceId],
  );
  useSurfaceUpdates(workspaceId, sessionId);

  useEffect(() => {
    setRestoredStorageKey(null);
    let nextState = createSurfaceState();
    try {
      const serialized = window.localStorage.getItem(storageKey);
      if (serialized) {
        nextState = restoreSurfaceState(serialized);
      }
    } catch {
      // Sandboxed/opaque documents may deny storage; server reconciliation remains.
    } finally {
      dispatch({ type: "restore", state: nextState });
      setRestoredStorageKey(storageKey);
    }
  }, [dispatch, storageKey]);

  useEffect(() => {
    if (restoredStorageKey !== storageKey) return;
    try {
      window.localStorage.setItem(storageKey, serializeSurfaceState(state));
    } catch {
      // Persistence is a hint and never required for runtime authority.
    }
  }, [restoredStorageKey, state, storageKey]);

  useEffect(() => {
    let active = true;
    setReconciledStorageKey(null);
    setNotice(null);
    void listSurfaces(workspaceId, sessionId)
      .then((items) => {
        if (!active) return;
        dispatch({ type: "reconcile", descriptors: items });
        setReconciledStorageKey(storageKey);
      })
      .catch(() => {
        if (!active) return;
        setNotice(
          "Unable to reconcile restored surfaces. Retry after the workspace service reconnects.",
        );
      });
    return () => {
      active = false;
    };
  }, [dispatch, sessionId, storageKey, workspaceId]);

  if (reconciledStorageKey !== storageKey) {
    return (
      <div role="status" data-testid="surface-restore-status">
        {notice ?? "Restoring workspace surfaces…"}
      </div>
    );
  }

  if (state.tabs.length === 0 || !state.activeSurfaceId) {
    return notice ? (
      <div role="status" style={{ position: "absolute", inset: 16, zIndex: 20 }}>
        {notice.replaceAll("_", " ")}
      </div>
    ) : null;
  }
  if (!state.byId[state.activeSurfaceId]) return null;
  const descriptors = state.tabs.map((surfaceId) => state.byId[surfaceId]);

  return (
    <div
      data-testid="surface-deck"
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 20,
        display: "flex",
        flexDirection: "column",
        background: "var(--color-neutral)",
      }}
    >
      <div role="tablist" aria-label="Workspace surfaces" style={{ display: "flex" }}>
        {state.tabs.map((surfaceId) => {
          const item = state.byId[surfaceId];
          return (
            <button
              key={surfaceId}
              role="tab"
              aria-selected={surfaceId === state.activeSurfaceId}
              data-testid={`surface-tab-${surfaceId}`}
              type="button"
              onClick={() => dispatch({ type: "activate", surfaceId })}
            >
              {item.title}
            </button>
          );
        })}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <SurfaceDeck
          descriptors={descriptors}
          activeSurfaceId={state.activeSurfaceId}
          renderSurface={(descriptor) =>
            descriptor.source.kind === "display" ? (
              <DisplaySurface
                descriptor={descriptor}
                sessionId={sessionId}
                onDeleted={(retentionStatus) => {
                  setNotice(retentionStatus);
                  dispatch({ type: "remove", surfaceId: descriptor.surfaceId });
                }}
              />
            ) : descriptor.source.kind === "live_app" ? (
              <LiveAppSurface
                descriptor={descriptor}
                sessionId={sessionId}
                onFocusMode={() =>
                  dispatch({
                    type: "layout",
                    layout: {
                      mode: "focus",
                      chatSize: state.layout.chatSize,
                    },
                  })
                }
              />
            ) : (
              <div role="status">This surface presenter is not enabled yet.</div>
            )
          }
        />
      </div>
    </div>
  );
}
