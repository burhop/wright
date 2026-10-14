import { useCallback, useEffect, useRef, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import "./native-panel.css";
import { NativeConnections } from "./NativeConnections";
import { NativeRecentRuns, type RecordedRun } from "./NativeRecentRuns";

export interface DesktopWorkspace {
  workspace_id: string;
  session_id: string;
  workspace_name: string;
  available: boolean;
  reason: string | null;
}
interface FileNode {
  name: string;
  path: string;
  type: string;
  children?: FileNode[];
}
export type HomeCall = (
  name:
    | "wright_workspace_list"
    | "wright_workspace_files"
    | "wright_workflow_history"
    | "wright_connections_list"
    | "wright_connection_plans"
    | "wright_connection_plan"
    | "wright_connection_plan_read"
    | "wright_connection_plan_update"
    | "wright_connection_signin"
    | "wright_connection_validate"
    | "wright_connection_enable",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;

function payload(result: CallToolResult): Record<string, unknown> {
  if (result.isError) throw new Error("Wright did not confirm this read.");
  if (result.structuredContent) return result.structuredContent;
  const text = result.content.find((item) => item.type === "text");
  if (!text || text.type !== "text") throw new Error("No workspace record.");
  return JSON.parse(text.text);
}
function workspaceFiles(node: FileNode): FileNode[] {
  if (node.type === "file") return [node];
  return (node.children ?? []).flatMap(workspaceFiles);
}

/** Navigation only: backend reads establish scope; choosing a view never starts work. */
export function NativeHomePanel({
  call,
  onOpen,
  openLink,
  initialSelection,
  onSelect,
  onOpenRun,
}: {
  readonly call: HomeCall;
  readonly initialSelection?: Pick<
    DesktopWorkspace,
    "workspace_id" | "session_id"
  >;
  readonly onSelect?: (workspace: DesktopWorkspace) => void;
  readonly onOpenRun?: (workspace: DesktopWorkspace, path: string, run: RecordedRun) => Promise<void>;
  readonly onOpen: (workspace: DesktopWorkspace, path: string) => Promise<void>;
  readonly openLink?: (url: string) => Promise<void>;
}) {
  const [items, setItems] = useState<DesktopWorkspace[]>([]);
  const [selected, setSelected] = useState<DesktopWorkspace>();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [view, setView] = useState<"workflows" | "connections" | "files" | "runs">("workflows");
  const [fileQuery, setFileQuery] = useState("");
  const workflowFiles = files.filter((file) => file.path.endsWith(".wflow"));
  const generation = useRef(0);
  const restore = useRef(initialSelection);
  const invalidate = useCallback(() => {
    generation.current++;
  }, []);
  useEffect(() => {
    let active = true;
    invalidate();
    setLoading(true);
    setError("");
    setSelected(undefined);
    setFiles([]);
    void call("wright_workspace_list", {})
      .then((result) => {
        const data = payload(result);
        if (!Array.isArray(data.workspaces))
          throw new Error("No workspace list.");
        if (active) setItems(data.workspaces as DesktopWorkspace[]);
      })
      .catch(() => {
        if (active)
          setError(
            "Workspaces could not be refreshed. Try Refresh; your saved work is unchanged.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      invalidate();
    };
  }, [call, refresh, invalidate]);

  const select = useCallback(
    async (workspace: DesktopWorkspace) => {
      const request = ++generation.current;
      setSelected(workspace);
      onSelect?.(workspace);
      setFiles([]);
      setFileQuery("");
      setError("");
      setLoading(true);
      try {
        const data = payload(
          await call("wright_workspace_files", {
            workspace_id: workspace.workspace_id,
            session_id: workspace.session_id,
          }),
        );
        if (request !== generation.current) return;
        if (
          data.workspace_id !== workspace.workspace_id ||
          data.session_id !== workspace.session_id ||
          !data.tree
        )
          throw new Error("Workspace scope differs.");
        setFiles(workspaceFiles(data.tree as FileNode));
      } catch {
        if (request === generation.current)
          setError(
            "This workspace could not be read. Refresh to retry; no workflow was opened or run.",
          );
      } finally {
        if (request === generation.current) setLoading(false);
      }
    },
    [call, onSelect],
  );

  useEffect(() => {
    if (loading || !restore.current || error) return;
    const saved = restore.current;
    restore.current = undefined;
    const workspace = items.find(
      (item) =>
        item.available &&
        item.workspace_id === saved.workspace_id &&
        item.session_id === saved.session_id,
    );
    if (workspace) void select(workspace);
  }, [items, loading, error, select]);

  return (
    <main className="native-home" data-control-style="neutral">
      <header>
        <h1>Wright</h1>
        <button
          disabled={opening}
          onClick={() => setRefresh((value) => value + 1)}
        >
          Refresh
        </button>
      </header>
      <p>Engineering workflows, alongside this conversation.</p>
      <label htmlFor="wright-workspace">Workspace</label>
      <select
        id="wright-workspace"
        disabled={opening}
        value={selected?.workspace_id ?? ""}
        onChange={(event) => {
          const workspace = items.find(
            (item) => item.workspace_id === event.target.value,
          );
          if (workspace) void select(workspace);
        }}
      >
        <option value="" disabled>
          Choose a workspace
        </option>
        {items.map((workspace) => (
          <option
            key={workspace.workspace_id}
            value={workspace.workspace_id}
            disabled={!workspace.available}
          >
            {workspace.workspace_name}
            {workspace.available ? "" : " — unavailable"}
          </option>
        ))}
      </select>
      {error && <p role="alert">{error}</p>}
      {loading && <p role="status">Loading…</p>}
      {!loading && !error && items.length === 0 && (
        <p>
          No Wright workspaces yet. Ask this conversation to create one, then
          refresh.
        </p>
      )}
      {selected && (
        <nav aria-label="Workspace views">
          <button onClick={() => setView("workflows")} disabled={opening}>
            Workflows
          </button>
          <button onClick={() => setView("connections")} disabled={opening}>
            Connections
          </button>
          <button onClick={() => setView("files")} disabled={opening}>
            Files
          </button>
          <button onClick={() => setView("runs")} disabled={opening}>Recent runs</button>
        </nav>
      )}
      {selected && view === "connections" && (
        <NativeConnections
          key={selected.workspace_id}
          workspace={selected}
          call={call}
          openLink={openLink}
        />
      )}
      {selected && view === "runs" && <NativeRecentRuns
        key={`${selected.workspace_id}:${selected.session_id}`}
        workspace={selected} paths={workflowFiles.map((file) => file.path.replace(/^\//, ""))}
        call={call} onOpen={onOpenRun ? async (path, run) => {
          setOpening(true);
          try { await onOpenRun(selected, path, run); } finally { setOpening(false); }
        } : undefined} />}
      {selected && view === "files" && (
        <section aria-label="Files">
          <h2>Files</h2>
          <p>Saved workspace files. Inspect run outputs and their evidence in the workflow’s working view.</p>
          <label htmlFor="wright-file-search">Find a file</label>
          <input id="wright-file-search" type="search" value={fileQuery}
            onChange={(event) => setFileQuery(event.target.value)} />
          {!loading && !error && files.length === 0 && <p>No saved files here yet.</p>}
          {!loading && !error && files.length > 0 &&
            !files.some((file) => file.path.toLowerCase().includes(fileQuery.toLowerCase())) &&
            <p>No files match this search.</p>}
          <ul>
            {files.filter((file) => file.path.toLowerCase().includes(fileQuery.toLowerCase())).map((file) => (
              <li key={file.path}>
                <span>{file.name}</span>
                <small>{file.path}</small>
              </li>
            ))}
          </ul>
          <p>File preview, upload and download are not available in this panel yet.</p>
        </section>
      )}
      {selected && view === "workflows" && (
        <section aria-label="Workflows">
          <h2>Workflows</h2>
          {!loading && !error && workflowFiles.length === 0 && (
            <p>
              No saved workflows here yet. Ask this conversation to create one.
            </p>
          )}
          <ul>
            {workflowFiles.map((file) => (
              <li key={file.path}>
                <button
                  disabled={loading}
                  onClick={() => {
                    setLoading(true);
                    setOpening(true);
                    // File-tree paths start at the workspace root; source identities
                    // are relative to it. Preserve every other character exactly.
                    void onOpen(selected, file.path.replace(/^\//, ""))
                      .catch(() =>
                        setError(
                          "The workflow could not be opened. Your saved source is unchanged.",
                        ),
                      )
                      .finally(() => {
                        setLoading(false);
                        setOpening(false);
                      });
                  }}
                >
                  {file.name}
                </button>
                <small>{file.path}</small>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
