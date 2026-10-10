import { useCallback, useEffect } from "react";
import { matchPath, useBlocker, type BlockerFunction } from "react-router-dom";
import { useViewerPanel } from "../../store/viewer";
import { NativeConfirmDialog } from "../native-process/NativeConfirmDialog";
import "../native-process/native-process.css";

/** Keep the mounted editors intact until the user resolves a workspace departure. */
export function WorkspaceNavigationGuard() {
  const { openTabs, setTabDirty } = useViewerPanel();
  const dirtyWorkflows = openTabs.filter(
    (tab) => tab.type === "workflow" && (tab.isDirty || tab.isSaving),
  );
  const saving = dirtyWorkflows.some((tab) => tab.isSaving);
  const hasUnsavedWorkflow = dirtyWorkflows.length > 0;
  const shouldBlock = useCallback<BlockerFunction>(
    ({ currentLocation, nextLocation }) => {
      const current = matchPath(
        "/workspace/:workspaceId",
        currentLocation.pathname,
      );
      const next = matchPath("/workspace/:workspaceId", nextLocation.pathname);
      // Tab, result and working-view links within this workspace retain the editors.
      return (
        hasUnsavedWorkflow &&
        Boolean(current) &&
        current?.params.workspaceId !== next?.params.workspaceId
      );
    },
    [hasUnsavedWorkflow],
  );
  const blocker = useBlocker(shouldBlock);
  const reset = blocker.reset;
  const keepEditing = useCallback(() => reset?.(), [reset]);

  useEffect(() => {
    // A pending save can finish while the choice is open. Clear the stale choice;
    // completing a save never initiates navigation on the user's behalf.
    if (!hasUnsavedWorkflow && blocker.state === "blocked") reset?.();
  }, [hasUnsavedWorkflow, blocker.state, reset]);

  if (blocker.state !== "blocked" || !hasUnsavedWorkflow) return null;
  return (
    <NativeConfirmDialog
      title="Leave workspace with unsaved changes?"
      stayLabel="Keep editing"
      proceedLabel="Discard changes and leave"
      proceedDisabled={saving}
      stay={keepEditing}
      proceed={() => {
        if (saving) return;
        for (const tab of dirtyWorkflows) setTabDirty(tab.path, false);
        blocker.proceed();
      }}
    >
      {saving && (
        <p role="status">
          Wait for saving to finish before leaving. Discarding edits cannot
          cancel a save already in progress.
        </p>
      )}
      <p>
        These workflows have unsaved changes. Keep editing to save them, or
        discard the changes and leave this workspace.
      </p>
      <ul>
        {dirtyWorkflows.map((tab) => (
          <li key={tab.path}>{tab.path.replace(/^\//, "")}</li>
        ))}
      </ul>
    </NativeConfirmDialog>
  );
}
