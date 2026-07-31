import { useCallback, useEffect, useMemo, useReducer } from "react";

import {
  restoreWorkspaceLayout,
  serializeWorkspaceLayout,
  workspaceLayoutReducer,
  type WorkspaceLayoutAction,
  type WorkspaceLayoutState,
} from "../components/workspace/workspace-layout";

export function surfaceLayoutStorageKey(
  userId: string,
  workspaceId: string,
): string {
  return `wright.workspaceSurfaces.layout.v2.${encodeURIComponent(userId)}.${encodeURIComponent(workspaceId)}`;
}

export function loadSurfaceLayout(
  storage: Pick<Storage, "getItem"> | null,
  key: string,
  containerWidth: number,
): WorkspaceLayoutState {
  if (!storage) return restoreWorkspaceLayout(null, containerWidth);
  try {
    return restoreWorkspaceLayout(storage.getItem(key), containerWidth);
  } catch {
    return restoreWorkspaceLayout(null, containerWidth);
  }
}

export function saveSurfaceLayout(
  storage: Pick<Storage, "setItem"> | null,
  key: string,
  state: WorkspaceLayoutState,
): void {
  if (!storage) return;
  try {
    storage.setItem(key, serializeWorkspaceLayout(state));
  } catch {
    // Layout persistence is a convenience and never runtime authority.
  }
}

function browserLocalStorage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function usePersistentSurfaceLayout(
  workspaceId: string,
  containerWidth: number,
  userId = "local-user",
): readonly [WorkspaceLayoutState, React.Dispatch<WorkspaceLayoutAction>] {
  const key = useMemo(
    () => surfaceLayoutStorageKey(userId, workspaceId),
    [userId, workspaceId],
  );
  type KeyedState = { readonly key: string; readonly layout: WorkspaceLayoutState };
  type KeyedAction =
    | { readonly type: "layout"; readonly action: WorkspaceLayoutAction }
    | { readonly type: "hydrate"; readonly key: string; readonly layout: WorkspaceLayoutState };
  const [record, keyedDispatch] = useReducer(
    (current: KeyedState, action: KeyedAction): KeyedState =>
      action.type === "hydrate"
        ? { key: action.key, layout: action.layout }
        : { key: current.key, layout: workspaceLayoutReducer(current.layout, action.action) },
    undefined,
    (): KeyedState => ({
      key,
      layout: loadSurfaceLayout(browserLocalStorage(), key, containerWidth),
    }),
  );
  const dispatch = useCallback(
    (action: WorkspaceLayoutAction) => keyedDispatch({ type: "layout", action }),
    [],
  );

  useEffect(() => {
    if (record.key === key) return;
    keyedDispatch({
      type: "hydrate",
      key,
      layout: loadSurfaceLayout(browserLocalStorage(), key, containerWidth),
    });
  }, [containerWidth, key, record.key]);
  useEffect(() => {
    if (record.key !== key) return;
    saveSurfaceLayout(browserLocalStorage(), key, record.layout);
  }, [key, record]);
  return [record.layout, dispatch] as const;
}
