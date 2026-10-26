import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import "./native-panel.css";
import { NativeSourceClient } from "./native-source-client";
import { recoveryWorkflowSourceSummary } from "../workflow-recovery/recovery-authoring";
import { NativeFilePreview } from "./NativeFilePreview";
import { NativeFileUpload } from "./NativeFileUpload";
import { NativeWorkspaceSettings } from "./NativeWorkspaceSettings";
import { NativeConnections } from "./NativeConnections";
import { NativeNewWorkflow } from "./NativeNewWorkflow";
import { EngineeringTemplateDialog } from "../workflow-recovery/EngineeringTemplateDialog";
import { nativeTemplateClient } from "./native-template-client";
import { NativeRecentRuns, type RecordedRun } from "./NativeRecentRuns";
import type {
  HomeView,
  NativeNavigationState,
  NativeWorkflowLocation,
} from "./native-navigation-state";

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
    | "wright_workspace_create"
    | "wright_workspace_settings_read"
    | "wright_workspace_settings_save"
    | "wright_workflow_read"
    | "wright_workflow_create"
    | "wright_workflow_templates"
    | "wright_workflow_template_create"
    | "wright_workspace_files"
    | "wright_workspace_file_preview"
    | "wright_workspace_file_download"
    | "wright_workspace_file_upload"
    | "wright_workflow_history"
    | "wright_recorded_run_read"
    | "wright_connection_replacement"
    | "wright_connection_configuration_preview"
    | "wright_connection_credentials"
    | "wright_connection_credentials_form"
    | "wright_connection_credentials_save"
    | "wright_connections_list"
    | "wright_connection_plans"
    | "wright_connection_plan"
    | "wright_connection_preview"
    | "wright_connection_command_preview"
    | "wright_connection_import_plan"
    | "wright_connection_plan_read"
    | "wright_connection_plan_update"
    | "wright_connection_signin"
    | "wright_connection_validate"
    | "wright_connection_enable"
    | "wright_connection_disable"
    | "wright_connection_controls"
    | "wright_connection_control",
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
  initialView = "workflows",
  onNavigate,
  restorationNotice,
  onDirty,
  lastLocation,
  onReopen,
}: {
  readonly call: HomeCall;
  readonly initialView?: HomeView;
  readonly onNavigate?: (view: HomeView) => void;
  readonly restorationNotice?: string;
  readonly onDirty?: (dirty: boolean) => void;
  readonly lastLocation?: NativeNavigationState;
  readonly onReopen?: (
    workspace: DesktopWorkspace,
    location: NativeWorkflowLocation,
  ) => Promise<void>;
  readonly initialSelection?: Pick<
    DesktopWorkspace,
    "workspace_id" | "session_id"
  >;
  readonly onSelect?: (workspace: DesktopWorkspace) => void;
  readonly onOpenRun?: (
    workspace: DesktopWorkspace,
    path: string,
    run: RecordedRun,
  ) => Promise<void>;
  readonly onOpen: (workspace: DesktopWorkspace, path: string) => Promise<void>;
  readonly openLink?: (url: string) => Promise<void>;
}) {
  const [items, setItems] = useState<DesktopWorkspace[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsDirty, setSettingsDirty] = useState(false);
  const settingsChanged = useCallback(
    (pending: boolean) => {
      setSettingsDirty(pending);
      onDirty?.(pending);
    },
    [onDirty],
  );
  const [selected, setSelected] = useState<DesktopWorkspace>();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [purposes, setPurposes] = useState<Record<string, string>>({});
  const [readingWorkflowNames, setReadingWorkflowNames] = useState(false);
  const previewOpener = useRef<HTMLButtonElement | null>(null);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [createNotice, setCreateNotice] = useState("");
  const [createUncertain, setCreateUncertain] = useState(false);
  const createFlight = useRef(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [view, setView] = useState<HomeView>(initialView);
  function navigate(next: HomeView) {
    setView(next);
    onNavigate?.(next);
  }
  const [fileQuery, setFileQuery] = useState("");
  const [workflowQuery, setWorkflowQuery] = useState("");
  const [previewPath, setPreviewPath] = useState<string>();
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const templateService = useMemo(
    () => (selected ? nativeTemplateClient(call, selected) : undefined),
    [call, selected],
  );
  const workflowFiles = files.filter(
    (file) =>
      file.path.replace(/^\//, "").startsWith("workflows/") &&
      file.path.endsWith(".wflow"),
  );
  const normalized = (text: string) =>
    text.toLocaleLowerCase().replace(/[-_]+/g, " ").replace(/\s+/g, " ").trim();
  const workflowName = (file: FileNode) =>
    titles[file.path] ??
    file.name.replace(/(?:\.workflow)?\.wflow$/, "").replace(/[-_]+/g, " ");
  const matchingWorkflows = workflowFiles.filter((file) =>
    normalized(
      `${workflowName(file)} ${file.path} ${purposes[file.path] ?? ""}`,
    ).includes(normalized(workflowQuery)),
  );
  const matchingFiles = files.filter((file) =>
    file.path.toLowerCase().includes(fileQuery.toLowerCase()),
  );
  useEffect(() => {
    if (!selected) return;
    let active = true;
    const workflows = files.filter(
      (file) =>
        file.path.replace(/^\//, "").startsWith("workflows/") &&
        file.path.endsWith(".wflow"),
    );
    void (async () => {
      const savedTitles: Record<string, string> = {};
      const savedPurposes: Record<string, string> = {};
      for (let offset = 0; active && offset < workflows.length; offset += 4) {
        await Promise.all(
          workflows.slice(offset, offset + 4).map(async (file) => {
            try {
              const client = new NativeSourceClient(
                {
                  workspaceId: selected.workspace_id,
                  sessionId: selected.session_id,
                  path: file.path.replace(/^\//, ""),
                },
                (name, args) => {
                  if (name !== "wright_workflow_read")
                    throw Error("Title lookup is read only");
                  return call(name, args);
                },
              );
              const summary = recoveryWorkflowSourceSummary(
                (await client.read()).source,
              );
              if (active && summary) {
                const { title, purpose } = summary;
                if (title) savedTitles[file.path] = title;
                if (purpose) savedPurposes[file.path] = purpose;
              }
            } catch {
              /* An unavailable source keeps its exact filename fallback. */
            }
          }),
        );
      }
      if (active) {
        setTitles(savedTitles);
        setPurposes(savedPurposes);
        setReadingWorkflowNames(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [files, selected, call]);
  const recentWorkflow =
    selected?.workspace_id === lastLocation?.workspace_id &&
    selected?.session_id === lastLocation?.session_id
      ? lastLocation?.workflow
      : undefined;
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
      if (settingsDirty) return;
      const request = ++generation.current;
      setSelected(workspace);
      onSelect?.(workspace);
      setFiles([]);
      setTitles({});
      setPurposes({});
      setReadingWorkflowNames(false);
      setPreviewPath(undefined);
      setFileQuery("");
      setWorkflowQuery("");
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
        const visibleFiles = workspaceFiles(data.tree as FileNode);
        setReadingWorkflowNames(
          visibleFiles.some(
            (file) =>
              file.path.replace(/^\//, "").startsWith("workflows/") &&
              file.path.endsWith(".wflow"),
          ),
        );
        setFiles(visibleFiles);
      } catch {
        if (request === generation.current)
          setError(
            "This workspace could not be read. Refresh to retry; no workflow was opened or run.",
          );
      } finally {
        if (request === generation.current) setLoading(false);
      }
    },
    [call, onSelect, settingsDirty],
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
    else
      setError(
        "The selected workspace or session is no longer available. Choose a workspace to continue.",
      );
  }, [items, loading, error, select]);

  const createWorkspace = async () => {
    const name = workspaceName.trim();
    if (!name || createFlight.current || createUncertain || settingsDirty)
      return;
    createFlight.current = true;
    setCreating(true);
    setCreateNotice("");
    try {
      const created = payload(await call("wright_workspace_create", { name }));
      if (
        typeof created.workspace_id !== "string" ||
        typeof created.session_id !== "string"
      )
        throw new Error("Creation receipt unavailable");
      // Reconcile the recorded identity through discovery before selecting it.
      const discovered = payload(await call("wright_workspace_list", {}));
      if (!Array.isArray(discovered.workspaces))
        throw new Error("Discovery unavailable");
      const workspaces = discovered.workspaces as DesktopWorkspace[];
      const workspace = workspaces.find(
        (item) =>
          item.available &&
          item.workspace_id === created.workspace_id &&
          item.session_id === created.session_id,
      );
      if (!workspace) throw new Error("Created workspace unavailable");
      setItems(workspaces);
      setWorkspaceName("");
      setCreateVisible(false);
      navigate("workflows");
      await select(workspace);
    } catch {
      setCreateUncertain(true);
      setCreateNotice(
        "Workspace creation was not fully confirmed. Refresh the workspace list and check for the new workspace; this form will not repeat the request.",
      );
    } finally {
      setCreating(false);
      createFlight.current = false;
    }
  };

  return (
    <main className="native-home" data-control-style="neutral">
      <header className="native-home__workspace-bar">
        <h1>Wright</h1>
        <div className="native-home__workspace-picker">
          <label htmlFor="wright-workspace">Workspace</label>
          <select
            id="wright-workspace"
            disabled={opening || creating || settingsDirty}
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
        </div>
        <button
          disabled={opening || creating || settingsDirty}
          onClick={() => {
            restore.current = selected ?? restore.current;
            setRefresh((value) => value + 1);
          }}
        >
          Refresh
        </button>
      </header>
      {restorationNotice && <p role="status">{restorationNotice}</p>}
      <div className="native-home__workspace-actions">
        <button
          disabled={
            opening || creating || loading || createUncertain || settingsDirty
          }
          onClick={() => setCreateVisible((value) => !value)}
        >
          New workspace
        </button>
        {selected && (
          <button
            disabled={opening || creating || settingsDirty}
            onClick={() => setSettingsOpen((current) => !current)}
            aria-expanded={settingsOpen}
          >
            {settingsOpen ? "Close workspace settings" : "Workspace settings"}
          </button>
        )}
      </div>
      {createVisible && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void createWorkspace();
          }}
        >
          <label htmlFor="wright-new-workspace">Workspace name</label>
          <input
            id="wright-new-workspace"
            value={workspaceName}
            disabled={creating || createUncertain || settingsDirty}
            onChange={(event) => setWorkspaceName(event.target.value)}
            required
          />
          <button
            type="submit"
            disabled={
              creating ||
              createUncertain ||
              settingsDirty ||
              !workspaceName.trim()
            }
          >
            {creating ? "Creating workspace…" : "Create workspace"}
          </button>
        </form>
      )}
      {createNotice && <p role="alert">{createNotice}</p>}
      {error && <p role="alert">{error}</p>}
      {loading && <p role="status">Loading…</p>}
      {!loading && !error && items.length === 0 && (
        <p>No Wright workspaces yet. Choose New workspace to get started.</p>
      )}
      {selected && (
        <>
          {settingsOpen && (
            <NativeWorkspaceSettings
              key={`${selected.workspace_id}:${selected.session_id}`}
              workspace={selected}
              call={call}
              onDirty={settingsChanged}
            />
          )}
        </>
      )}
      <div inert={settingsDirty}>
        {recentWorkflow && selected && onReopen && (
          <div className="native-home__return">
            <span>Last viewed</span>
            <button
              disabled={loading || opening || creating}
              onClick={() => {
                setOpening(true);
                setError("");
                void onReopen(selected, recentWorkflow)
                  .catch(() =>
                    setError(
                      "This saved location could not be reopened. Open the workflow from the list to inspect its current source. No run was started or resumed.",
                    ),
                  )
                  .finally(() => setOpening(false));
              }}
            >
              Reopen{" "}
              {titles["/" + recentWorkflow.path] ??
                titles[recentWorkflow.path] ??
                recentWorkflow.path
                  .split("/")
                  .at(-1)
                  ?.replace(/(?:\.workflow)?\.wflow$/, "")
                  .replace(/[-_]+/g, " ")}
              {recentWorkflow.view === "working" ? " · Run and results" : ""}
            </button>
            {recentWorkflow.run_id && (
              <small>Run {recentWorkflow.run_id}</small>
            )}
          </div>
        )}
        {selected && (
          <nav aria-label="Workspace views">
            <button
              aria-current={view === "workflows" ? "page" : undefined}
              onClick={() => navigate("workflows")}
              disabled={opening || creating}
            >
              Workflows
            </button>
            <button
              aria-current={view === "connections" ? "page" : undefined}
              onClick={() => navigate("connections")}
              disabled={opening || creating}
            >
              Connections
            </button>
            <button
              aria-current={view === "files" ? "page" : undefined}
              onClick={() => navigate("files")}
              disabled={opening || creating}
            >
              Files
            </button>
            <button
              aria-current={view === "runs" ? "page" : undefined}
              onClick={() => navigate("runs")}
              disabled={opening || creating}
            >
              Recent runs
            </button>
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
        {selected && view === "runs" && (
          <NativeRecentRuns
            key={`${selected.workspace_id}:${selected.session_id}`}
            workspace={selected}
            paths={workflowFiles.map((file) => file.path.replace(/^\//, ""))}
            initialPath={recentWorkflow?.path}
            titles={titles}
            call={call}
            onOpen={
              onOpenRun
                ? async (path, run) => {
                    setOpening(true);
                    try {
                      await onOpenRun(selected, path, run);
                    } finally {
                      setOpening(false);
                    }
                  }
                : undefined
            }
          />
        )}
        {selected && view === "files" && (
          <section aria-label="Files">
            <h2>Files</h2>
            <label htmlFor="wright-file-search">Find a file</label>
            <input
              id="wright-file-search"
              type="search"
              value={fileQuery}
              onChange={(event) => setFileQuery(event.target.value)}
            />
            {!loading && !error && files.length === 0 && (
              <p>No saved files here yet.</p>
            )}
            {!loading &&
              !error &&
              files.length > 0 &&
              matchingFiles.length === 0 && <p>No files match this search.</p>}
            <p className="native-home__list-count" role="status">
              {matchingFiles.length} of {files.length} files
            </p>
            <ul
              className="native-home__files"
              aria-label="Workspace files"
              tabIndex={0}
            >
              {matchingFiles.map((file) => (
                <li key={file.path}>
                  <button
                    type="button"
                    onClick={(event) => {
                      previewOpener.current = event.currentTarget;
                      setPreviewPath(file.path.replace(/^\//, ""));
                    }}
                  >
                    {file.name}
                  </button>
                  <small title={file.path}>{file.path}</small>
                </li>
              ))}
            </ul>
            <details className="native-home__file-options">
              <summary>Upload a file</summary>
              <NativeFileUpload
                key={`${selected.workspace_id}:${selected.session_id}`}
                call={call}
                workspace={selected}
                onUploaded={(path) => {
                  void select(selected);
                  setFileQuery(path.split("/").at(-1) ?? "");
                }}
              />
            </details>
            <details className="native-home__file-options">
              <summary>Preview and download details</summary>
              <p>
                Text previews support files up to 64 KiB; downloads support
                visible files up to 16 MiB. Other previews are unavailable here.
                Inspect run outputs and their evidence in the workflow’s
                working view.
              </p>
            </details>
            {previewPath && (
              <NativeFilePreview
                key={`${selected.workspace_id}:${selected.session_id}:${previewPath}`}
                call={call}
                workspace={selected}
                path={previewPath}
                onClose={() => {
                  setPreviewPath(undefined);
                  previewOpener.current?.focus();
                }}
              />
            )}
          </section>
        )}
        {selected && view === "workflows" && (
          <section aria-label="Workflows">
            <div className="native-home__section-heading">
              <h2>Workflows</h2>
              <div className="native-home__workflow-actions">
                <NativeNewWorkflow
                  key={`${selected.workspace_id}:${selected.session_id}`}
                  workspace={selected}
                  call={call}
                  onOpen={onOpen}
                  onBusy={setCreating}
                  disabled={loading || opening || creating}
                />
                <button
                  disabled={loading || creating || opening}
                  onClick={() => setTemplatesOpen(true)}
                >
                  Use a template
                </button>
              </div>
            </div>
            {templateService && (
              <EngineeringTemplateDialog
                key={`${selected.workspace_id}:${selected.session_id}`}
                open={templatesOpen}
                workspaceId={selected.workspace_id}
                sessionId={selected.session_id}
                workspaceName={selected.workspace_name}
                service={templateService}
                previewUrl={() => null}
                onClose={() => setTemplatesOpen(false)}
                onCreated={(path) => {
                  setOpening(true);
                  void onOpen(selected, path)
                    .catch(() =>
                      setError(
                        "The template was saved, but its editor could not be opened. Refresh and open the saved workflow.",
                      ),
                    )
                    .finally(() => setOpening(false));
                }}
              />
            )}
            {workflowFiles.length > 0 && (
              <input
                type="search"
                aria-label="Find a workflow"
                placeholder="Find a workflow…"
                value={workflowQuery}
                onChange={(event) => setWorkflowQuery(event.target.value)}
              />
            )}
            {!loading && !error && workflowFiles.length === 0 && (
              <p>
                No saved workflows here yet. Choose New workflow or ask this
                conversation to create one.
              </p>
            )}
            {!loading &&
              !readingWorkflowNames &&
              workflowFiles.length > 0 &&
              matchingWorkflows.length === 0 && (
                <p>No workflows match this search.</p>
              )}
            {readingWorkflowNames && (
              <p role="status">Reading saved workflow names…</p>
            )}
            {!readingWorkflowNames &&
              workflowFiles.length > Object.keys(titles).length && (
                <p role="status">
                  Some saved names are unavailable. Filenames are shown; Refresh
                  to retry.
                </p>
              )}
            <ul
              className="native-home__workflows"
              aria-label="Workspace workflows"
              tabIndex={0}
              hidden={readingWorkflowNames}
            >
              {matchingWorkflows.map((file) => (
                <li key={file.path}>
                  <button
                    aria-label={titles[file.path] ?? file.name}
                    disabled={loading || creating}
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
                    {workflowName(file)}
                    <span aria-hidden="true" className="native-home__open-hint">
                      Open →
                    </span>
                  </button>
                  {purposes[file.path] && (
                    <p className="native-home__workflow-purpose">
                      {purposes[file.path]}
                    </p>
                  )}
                  <details className="native-home__file-location">
                    <summary>File location</summary>
                    <small>{file.path}</small>
                  </details>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
