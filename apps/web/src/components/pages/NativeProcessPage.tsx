import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";
import { NativeEditor } from "../native-process/NativeEditor";
import { NativeConfirmDialog } from "../native-process/NativeConfirmDialog";
import "../native-process/native-process.css";

export default function NativeProcessPage() {
  const [chosen, setChosen] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [pendingWorkspace, setPendingWorkspace] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [workspaceError, setWorkspaceError] = useState("");
  useEffect(() => {
    let active = true;
    void workspaceService
      .getAllWorkspaces()
      .then((items) => {
        if (active) {
          setWorkspaces(items);
          setChosen(
            (previous) =>
              previous ??
              items.find((workspace) => workspace.session_id)?.session_id ??
              null,
          );
        }
      })
      .catch(() => {
        if (active)
          setWorkspaceError(
            "Workspace discovery failed. Check the service and reopen this page.",
          );
      });
    return () => {
      active = false;
    };
  }, []);
  const managed = workspaces
    .filter((workspace) => workspace.session_id)
    .map((workspace) => ({
      sessionId: workspace.session_id,
      title: workspace.workspace_name || workspace.workspace_id,
    }));
  const sessionId = chosen;
  return (
    <section
      className="native-process"
      data-testid="page-native-process"
      aria-labelledby="native-process-heading"
    >
      <header>
        <p>Engineering processes</p>
        <h1 id="native-process-heading">Build a native process</h1>
        <p>
          Define inputs, connect exact ports and preserve your work in Wright’s
          process language.
        </p>
      </header>
      {workspaceError && <p role="alert">{workspaceError}</p>}
      {managed.length ? (
        <>
          <label className="native-workspace">
            Workspace
            <select
              data-testid="native-workspace"
              value={sessionId ?? ""}
              onChange={(event) => {
                if (dirty) setPendingWorkspace(event.target.value);
                else setChosen(event.target.value);
              }}
            >
              {managed.map((session) => (
                <option key={session.sessionId} value={session.sessionId}>
                  {session.title}
                </option>
              ))}
            </select>
          </label>
          {sessionId && (
            <NativeEditor
              key={sessionId}
              sessionId={sessionId}
              onDirtyChange={setDirty}
            />
          )}
          {pendingWorkspace && (
            <NativeConfirmDialog
              title="Switch workspace"
              stay={() => setPendingWorkspace(null)}
              proceed={() => {
                setChosen(pendingWorkspace);
                setPendingWorkspace(null);
              }}
            >
              <p>
                This workspace has unsaved changes. A recovery draft is retained
                in this tab when browser storage is available. Stay to save your
                work first.
              </p>
            </NativeConfirmDialog>
          )}
        </>
      ) : (
        <p data-testid="native-no-workspace">
          Open or create a managed workspace from the{" "}
          <Link to="/">Dashboard</Link> to save a process.
        </p>
      )}
    </section>
  );
}
