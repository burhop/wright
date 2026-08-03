import { useEffect, useMemo, useRef, useState } from "react";

import {
  createPresentation,
  listSurfaces,
} from "../../services/surfaces/surface-client";
import { hostAdapter } from "../../services/host-adapter";
import {
  createSurfaceState,
  restoreSurfaceState,
  serializeSurfaceState,
  useSurfaces,
  useSurfaceUpdates,
} from "../../store/surfaces";
import { DisplaySurface } from "./DisplaySurface";
import { LiveAppSurface } from "./LiveAppSurface";
import { McpAppSurface } from "./McpAppSurface";
import { SurfaceDeck } from "./SurfaceDeck";
import { SurfaceTabs } from "./SurfaceTabs";

interface Props {
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly focusMode?: boolean;
  readonly onEnterFocus?: () => void;
  readonly onExitFocus?: () => void;
}

export function SurfaceWorkspace({
  workspaceId,
  sessionId,
  focusMode = false,
  onEnterFocus,
  onExitFocus,
}: Props) {
  const { state, dispatch } = useSurfaces();
  const headingRef = useRef<HTMLHeadingElement>(null);
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
    const reconcile = () => {
      void listSurfaces(workspaceId, sessionId).then((items) => {
        dispatch({ type: "reconcile", descriptors: items });
      });
    };
    window.addEventListener("wright-surfaces-changed", reconcile);
    return () => window.removeEventListener("wright-surfaces-changed", reconcile);
  }, [dispatch, sessionId, workspaceId]);

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
      <div
        role="status"
        style={{ position: "absolute", inset: 16, zIndex: 20 }}
      >
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
      <div style={{ display: "flex", alignItems: "center" }}>
        <h2
          ref={headingRef}
          id="workspace-surfaces-heading"
          tabIndex={-1}
          className="sr-only"
        >
          Workspace surfaces
        </h2>
        <div style={{ flex: 1, minWidth: 0 }} data-focus-region="tabs">
          <SurfaceTabs
            tabs={descriptors.map((descriptor) => ({
              id: descriptor.surfaceId,
              label: descriptor.title,
              closable: true,
              status: descriptor.lifecycle,
            }))}
            selectedId={state.activeSurfaceId}
            onSelect={(surfaceId) => dispatch({ type: "activate", surfaceId })}
            onClose={(surfaceId) => dispatch({ type: "remove", surfaceId })}
            emptyFocusRef={headingRef}
          />
        </div>
        {focusMode && (
          <button
            type="button"
            className="workspace-surface-control"
            data-testid="surface-exit-focus"
            onClick={onExitFocus}
          >
            Restore workspace layout
          </button>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <SurfaceDeck
          descriptors={descriptors}
          activeSurfaceId={state.activeSurfaceId}
          onOpenInBrowser={async (descriptor) => {
            try {
              const launch = await createPresentation(
                descriptor.surfaceId,
                workspaceId,
                sessionId,
                "browser",
                {
                  rememberPreference: false,
                  isolatedAcknowledged:
                    descriptor.instance?.sharing === "isolated",
                },
              );
              await hostAdapter.openExternal(launch.absoluteBootstrapUrl);
            } catch (reason) {
              setNotice(
                reason instanceof Error ? reason.message : String(reason),
              );
            }
          }}
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
                onFocusMode={() => onEnterFocus?.()}
              />
            ) : descriptor.source.kind === "mcp_app" ? (
              <McpAppSurface
                descriptor={descriptor}
                sessionId={sessionId}
                onFocusMode={onEnterFocus}
              />
            ) : (
              <div role="status">
                This surface presenter is not enabled yet.
              </div>
            )
          }
        />
      </div>
    </div>
  );
}
