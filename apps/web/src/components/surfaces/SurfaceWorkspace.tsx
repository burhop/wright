import { useEffect, useState } from "react";

import { listSurfaces } from "../../services/surfaces/surface-client";
import { useSurfaces, useSurfaceUpdates } from "../../store/surfaces";
import { DisplaySurface } from "./DisplaySurface";

interface Props {
  readonly workspaceId: string;
  readonly sessionId: string;
}

export function SurfaceWorkspace({ workspaceId, sessionId }: Props) {
  const { state, dispatch } = useSurfaces();
  const [notice, setNotice] = useState<string | null>(null);
  useSurfaceUpdates(workspaceId, sessionId);

  useEffect(() => {
    let active = true;
    void listSurfaces(workspaceId, sessionId)
      .then((items) => {
        if (!active) return;
        for (const descriptor of items) dispatch({ type: "upsert", descriptor });
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [dispatch, sessionId, workspaceId]);

  if (state.tabs.length === 0 || !state.activeSurfaceId) {
    return notice ? (
      <div role="status" style={{ position: "absolute", inset: 16, zIndex: 20 }}>
        {notice.replaceAll("_", " ")}
      </div>
    ) : null;
  }
  const descriptor = state.byId[state.activeSurfaceId];
  if (!descriptor) return null;

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
      <div role="tabpanel" style={{ flex: 1, minHeight: 0 }}>
        {descriptor.source.kind === "display" ? (
          <DisplaySurface
            descriptor={descriptor}
            sessionId={sessionId}
            onDeleted={(retentionStatus) => {
              setNotice(retentionStatus);
              dispatch({ type: "remove", surfaceId: descriptor.surfaceId });
            }}
          />
        ) : (
          <div role="status">This surface presenter is not enabled yet.</div>
        )}
      </div>
    </div>
  );
}
