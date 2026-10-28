import { createRoot } from "react-dom/client";
import {
  App,
  applyDocumentTheme,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";
import {
  EmptyResultSchema,
  type CallToolResult,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { openNativeWorkspaceFile } from "./native-file-client";
import "@wright/ui-kit/styles.css";
import { FileDownloadProvider } from "@wright/ui-kit";
import { downloadNativeFile } from "./native-download";
import type { InteractionSnapshot, ProcessRef } from "@wright/process-client";
import { NativePanelContent } from "./NativePanelContent";
import { NativeSourceClient } from "./native-source-client";
import { NativeEditorDraftClient } from "./native-editor-draft-client";
import { NativeUiReview } from "./NativeUiReview";
import { captureUiReview, captureUiObservation, type ReviewEvent } from "./native-ui-review";
import type { NativeProcessCall } from "./native-process-client";
import type { NativeTransferCall } from "./native-transfer-client";
import {
  NativeHomePanel,
  type HomeCall,
  type DesktopWorkspace,
} from "./NativeHomePanel";
import {
  readNavigationState,
  rememberNavigationState,
  navigationState,
  type NativeNavigationState,
  type HomeView,
  type NativeWorkflowLocation,
} from "./native-navigation-state";

const root = createRoot(document.getElementById("editor")!);
const notice = document.getElementById("notice")!;
const pendingNavigationNotice =
  "Your draft is kept. Save it before changing workspace.";
const app = new App(
  { name: "wright-native-workflow-editor", version: "0.1.0" },
  { tools: { listChanged: false } },
  { autoResize: false },
);
const requestDownload = (blob: Blob, name: string) => downloadNativeFile(app, blob, name);
let args: Record<string, unknown> = {};
let pending: CallToolResult | undefined;
let generation = 0;
let dirty = false;
let selectedWorkspace: DesktopWorkspace | undefined;
let navigation: NativeNavigationState | undefined;
let homeView: HomeView = "workflows";
let restorationNotice = "";
let contextGeneration = 0;
let contextWrite: Promise<unknown> = Promise.resolve();
let contextTimer: ReturnType<typeof setTimeout> | undefined;
let lastContextSignature = "";
let widgetAccepted = false;
let homeGeneration = 0;
let openedWorkflow: NativeWorkflowLocation | undefined;
let activeSurface: "home" | "workflow" = "home";
// Opt-in native-file proof. Each host document owns its existing Wright editor.
// Source saves and drafts still use the normal scoped Wright clients below.
let connected = false;
let fileInput: { name: string; resourceUri: string } | undefined;
let fileLoading = false;
let fileBound = false;
let nativeWorkspaceFiles = false;
let nativeFileNotice = "";
function setNativeFilesMode(enabled: boolean) {
  const available = !!app.getHostCapabilities()?.experimental?.["openai/files"];
  nativeWorkspaceFiles = enabled && available;
  nativeFileNotice =
    enabled && !available
      ? "This host does not support native file tabs. Wright's existing editor and previews remain available."
      : "";
}
let reopenCurrentFile = false;
const fileInstanceId = crypto.randomUUID();
async function fileObservation(
  stage: "opened" | "rendered" | "activated" | "draft-changed",
) {
  const experimental = app.getHostCapabilities()?.experimental;
  const remembered = navigation ?? readNavigationState();
  const location = openedWorkflow ?? remembered?.workflow;
  const workspace = selectedWorkspace ?? remembered;
  return app.callServerTool({
    name: "wright_workflow_file_context",
    arguments: {
      request: {
        instance_id: fileInstanceId,
        stage,
        capabilities: {
          files: !!experimental?.["openai/files"],
          resources: !!experimental?.["openai/resource"],
        },
        ...(openedWorkflow
          ? { observed_source_digest: openedWorkflow.source_digest }
          : {}),
        editor_has_unsaved_changes: dirty,
        ...(workspace &&
        location &&
        location.path.split("/").at(-1) === fileInput?.name
          ? {
              resume: {
                workspace_id: workspace.workspace_id,
                session_id: workspace.session_id,
                path: location.path,
                ...(!reopenCurrentFile
                  ? { expected_sha256: location.source_digest }
                  : {}),
              },
            }
          : {}),
      },
    },
  });
}
async function openNativeFile() {
  if (!connected || !fileInput || fileLoading || fileBound) return;
  if (!app.getHostCapabilities()?.experimental?.["openai/resource"]) {
    notice.textContent =
      "This host did not advertise native file-viewer support.";
    return;
  }
  fileLoading = true;
  try {
    const result = await fileObservation("opened");
    const data = result.structuredContent;
    if (data?.native_workspace_files_enabled === true) setNativeFilesMode(true);
    const binding = data?.native_file as Record<string, unknown> | undefined;
    if (
      result.isError ||
      !binding ||
      typeof binding.path !== "string" ||
      binding.path.split("/").at(-1) !== fileInput.name
    )
      throw new Error("Native file binding unavailable");
    args = {
      workspace_id: binding.workspace_id,
      session_id: binding.session_id,
      path: binding.path,
    };
    pending = result;
    const remembered = readNavigationState();
    const previous =
      remembered &&
      remembered.workspace_id === binding.workspace_id &&
      remembered.session_id === binding.session_id &&
      remembered.workflow?.path === binding.path &&
      remembered.workflow.source_digest === binding.source_sha256
        ? remembered.workflow
        : undefined;
    const runId =
      typeof binding.run_id === "string" ? binding.run_id : previous?.run_id;
    if (runId || previous?.view === "working") {
      const request = {
        ...args,
        operation: "snapshot",
        expected_storage_digest: binding.source_sha256,
        ...(runId ? { run_id: runId } : {}),
      };
      pending = await app.callServerTool({
        name: "wright_process_view",
        arguments: { request },
      });
      args = {
        ...request,
        ...(previous
          ? {
              restored_view: previous.view,
              restored_source_digest: previous.source_digest,
            }
          : {}),
      };
    }
    fileBound = true;
    reopenCurrentFile = false;
    await open();
  } catch {
    fileBound = false;
    notice.textContent =
      "Wright could not confirm this file's saved context. No file or draft was changed.";
    if (readNavigationState()?.workflow) {
      const retry = document.createElement("button");
      retry.textContent = "Open current saved revision";
      retry.onclick = () => {
        reopenCurrentFile = true;
        void openNativeFile();
      };
      notice.append(" ", retry);
    }
  } finally {
    fileLoading = false;
  }
}
window.addEventListener("focus", () => {
  if (fileBound) void fileObservation("activated").catch(() => {});
});
document.addEventListener("visibilitychange", () => {
  if (fileBound && document.visibilityState === "visible")
    void fileObservation("activated").catch(() => {});
});
const reviewEvents: ReviewEvent[] = [];
let latestUiReport:
  { workspace_id: string; session_id: string; path: string } | undefined;
const reviewLocation = () => ({
  ...(navigation ? { navigation } : {}),
  active_surface: activeSurface,
  editor_has_unsaved_changes: dirty,
});
function recordReviewEvent(kind: ReviewEvent["kind"]) {
  const event: ReviewEvent = {
    kind,
    elapsed_ms: Math.round(performance.now()),
    ...(kind === "navigation"
      ? { location: structuredClone(reviewLocation()) }
      : {}),
  };
  reviewEvents.push(event);
  if (reviewEvents.length > 20) reviewEvents.shift();
  scheduleContext();
}
window.addEventListener("resize", () => recordReviewEvent("resize"));
window.addEventListener("error", () => recordReviewEvent("error"));
window.addEventListener("unhandledrejection", () =>
  recordReviewEvent("unhandled-rejection"),
);
// Observe only our iframe. Coalesce normal interactions and sample after paint;
// no polling, saved reports, model turns, or workflow actions are introduced.
function scheduleContext() {
  contextGeneration++;
  clearTimeout(contextTimer);
  contextTimer = setTimeout(() => {
    requestAnimationFrame(() => requestAnimationFrame(publishContext));
  }, 250);
}
document.getElementById("editor")!.addEventListener("click", scheduleContext);
document.getElementById("editor")!.addEventListener("load", scheduleContext, true);
document.getElementById("editor")!.addEventListener("error", scheduleContext, true);
document.addEventListener("visibilitychange", scheduleContext);
function rememberLocation() {
  if (!selectedWorkspace) return;
  navigation = {
    schema_version: "wright.native-navigation/1",
    workspace_id: selectedWorkspace.workspace_id,
    session_id: selectedWorkspace.session_id,
    view: homeView,
    ...(openedWorkflow ? { workflow: openedWorkflow } : {}),
  };
  recordReviewEvent("navigation");
  widgetAccepted = rememberNavigationState(navigation);
}
function publishContext() {
  if (!selectedWorkspace || !navigation) return;
  const version = contextGeneration;
  const context = {
    ...navigation,
    workspace_name: selectedWorkspace.workspace_name,
    active_surface: activeSurface,
    ui_observation: captureUiObservation(
      document.getElementById("editor")!, app.getHostContext(), reviewLocation(),
      reviewEvents, fileInstanceId,
    ),
    ...(latestUiReport ? { ui_problem_report: latestUiReport } : {}),
    ...(openedWorkflow
      ? { workflow: { ...openedWorkflow, editor_has_unsaved_changes: dirty } }
      : {}),
  };
  const signature = JSON.stringify(context);
  if (signature === lastContextSignature) return;
  contextWrite = contextWrite
    .catch(() => {})
    .then(async () => {
      if (version !== contextGeneration || signature === lastContextSignature) return;
      try {
        await app.updateModelContext(
          { structuredContent: {
            ...context,
            ui_observation: { ...context.ui_observation, observed_at: new Date().toISOString() },
          } },
          { timeout: 5000 },
        );
        lastContextSignature = signature;
        if (version === contextGeneration) {
          const nextNotice = widgetAccepted
            ? ""
            : "Workspace context is available to this conversation, but this host does not save panel navigation. Ask the conversation to reopen this workspace.";
          if (restorationNotice !== nextNotice) {
            restorationNotice = nextNotice;
            renderCurrent?.(app.getHostContext());
          }
        }
      } catch {
        if (version === contextGeneration) {
          restorationNotice = widgetAccepted
            ? "The panel location is saved here, but chat context could not be updated. Name the workspace when asking the conversation."
            : "This host could not retain panel navigation. Reopen Wright with the workspace name; saved workflows are unchanged.";
          renderCurrent?.(app.getHostContext());
        }
      }
    });
}
const rememberWorkspace = (workspace: DesktopWorkspace) => {
  const previous = selectedWorkspace ?? navigation;
  if (
    previous?.workspace_id !== workspace.workspace_id ||
    previous.session_id !== workspace.session_id
  )
    openedWorkflow = undefined;
  selectedWorkspace = workspace;
  rememberLocation();
};
const rememberView = (view: HomeView) => {
  homeView = view;
  rememberLocation();
};
const rememberWorkflow = (location: NativeWorkflowLocation) => {
  if (
    openedWorkflow?.path === location.path &&
    openedWorkflow.source_digest === location.source_digest &&
    openedWorkflow.run_id === location.run_id &&
    openedWorkflow.view === location.view
  )
    return;
  openedWorkflow = location;
  rememberLocation();
};
let renderCurrent: ((context?: McpUiHostContext) => void) | undefined;
const processCall: NativeProcessCall = async (name, request) => {
  try {
    return await app.callServerTool({ name, arguments: { request } });
  } finally {
    scheduleContext();
  }
};
const transferCall: NativeTransferCall = (name, arguments_) =>
  app.callServerTool({ name, arguments: arguments_ });

async function openSavedWorkflow(
  workspaceId: string,
  sessionId: string,
  path: string,
) {
  if (fileBound && path !== openedWorkflow?.path)
    throw new Error("Open the other document in its own desktop tab.");
  if (dirty)
    throw new Error("Save or reconcile the current change before navigating.");
  const request = ++generation;
  const scope = { workspace_id: workspaceId, session_id: sessionId, path };
  const result = await app.callServerTool({
    name: "wright_workflow_open",
    arguments: scope,
  });
  if (request !== generation || dirty) return;
  if (result.isError)
    throw new Error(
      "The saved destination is unavailable. No import was repeated.",
    );
  args = scope;
  pending = result;
  await open();
}
const homeCall: HomeCall = (name, arguments_) =>
  app.callServerTool(
    { name, arguments: arguments_ },
    name === "wright_connection_validate" ? { timeout: 360_000 } : undefined,
  );
async function openWorkspaceFile(
  workspace: Pick<DesktopWorkspace, "workspace_id" | "session_id">,
  path: string,
) {
  if (!app.getHostCapabilities()?.experimental?.["openai/files"])
    throw new Error("Native file tabs are unavailable in this host.");
  return openNativeWorkspaceFile(
    {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      path,
    },
    (name, arguments_) => app.callServerTool({ name, arguments: arguments_ }),
    async (absolutePath) => {
      // Public extension, matching @openai/mcp-extensions 0.2.1 createFiles.
      // The base MCP Apps request union does not yet include this extension.
      await app.request(
        {
          method: "openai/files/open",
          params: { path: absolutePath },
        } as unknown as Parameters<typeof app.request>[0],
        EmptyResultSchema,
        { timeout: 10000 },
      );
    },
  );
}
app.registerTool(
  "wright_ui_inspect",
  {
    title: "Inspect Wright view",
    description:
      "Read bounded layout, build and navigation observations from this Wright iframe. No DOM text, form/source values, native screenshot, host-shell access or workflow actions.",
    inputSchema: z.object({}).strict(),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  () => {
    const report = captureUiReview(
      document.body,
      app.getHostContext(),
      reviewLocation(),
      reviewEvents,
      document.querySelector('[data-testid="wright-ui-review-open"]') ??
        undefined,
    );
    return {
      content: [{ type: "text", text: JSON.stringify(report) }],
      structuredContent: report,
    };
  },
);
createRoot(document.getElementById("ui-review")!).render(
  <NativeUiReview
    root={() => document.getElementById("editor")!}
    host={() => app.getHostContext()}
    location={reviewLocation}
    workspace={() => selectedWorkspace}
    events={reviewEvents}
    call={homeCall}
    onSaved={(workspace, path) => {
      latestUiReport = {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        path,
      };
      rememberLocation();
    }}
    requestReview={async (workspace, path) => {
      if (!app.getHostCapabilities()?.message?.text) return "unsupported";
      const response = await app.sendMessage(
        {
          role: "user",
          content: [
            {
              type: "text",
              text:
                "Please review this saved Wright UI problem report. No engineering workflow should run.\n" +
                JSON.stringify({
                  workspace_id: workspace.workspace_id,
                  session_id: workspace.session_id,
                  path,
                }),
            },
          ],
        },
        { timeout: 5000 },
      );
      if (response.isError)
        throw Error("Host did not confirm message delivery");
      return "sent";
    }}
  />,
);
function home() {
  if (fileBound) return;
  if (dirty) {
    notice.textContent = pendingNavigationNotice;
    return;
  }
  generation++;
  activeSurface = "home";
  if (selectedWorkspace) rememberLocation();
  const homeKey = ++homeGeneration;
  notice.textContent = "";
  renderCurrent = () =>
    root.render(
      <FileDownloadProvider request={requestDownload}>
      <NativeHomePanel
        key={homeKey}
        call={homeCall}
        initialSelection={selectedWorkspace ?? navigation}
        initialView={homeView}
        onOpenFile={nativeWorkspaceFiles ? openWorkspaceFile : undefined}
        nativeFileNotice={nativeFileNotice}
        onNavigate={rememberView}
        restorationNotice={restorationNotice}
        lastLocation={navigation}
        onReopen={async (workspace, location) => {
          const request = ++generation;
          const scope = {
            workspace_id: workspace.workspace_id,
            session_id: workspace.session_id,
            path: location.path,
          };
          const needsProcess = location.view === "working" || !!location.run_id;
          const target = needsProcess
            ? {
                ...scope,
                operation: "snapshot",
                expected_storage_digest: location.source_digest,
                ...(location.run_id ? { run_id: location.run_id } : {}),
              }
            : scope;
          const result = await app.callServerTool({
            name: needsProcess ? "wright_process_view" : "wright_workflow_open",
            arguments: needsProcess ? { request: target } : target,
          });
          if (request !== generation || dirty) return;
          if (result.isError) throw new Error("Saved location is unavailable");
          args = {
            ...target,
            restored_source_digest: location.source_digest,
            restored_view: location.view,
          };
          pending = result;
          await open();
        }}
        onDirty={(pending) => {
          dirty = pending;
        }}
        onSelect={rememberWorkspace}
        onOpenRun={async (workspace, path, run) => {
          const request = ++generation;
          const scope = {
            operation: "snapshot",
            workspace_id: workspace.workspace_id,
            session_id: workspace.session_id,
            path,
            expected_storage_digest: run.source_digest,
            run_id: run.run_id,
          };
          const result = await app.callServerTool({
            name: "wright_process_view",
            arguments: { request: scope },
          });
          if (request !== generation || dirty) return;
          if (result.isError || !result.structuredContent?.snapshot)
            throw new Error("Exact run unavailable");
          args = scope;
          pending = result;
          await open();
        }}
        openLink={async (url) => {
          const result = await app.openLink({ url });
          if (result.isError)
            throw new Error("Host declined sign-in navigation");
        }}
        onOpen={async (workspace, path) => {
          if (nativeWorkspaceFiles) {
            if (!(await openWorkspaceFile(workspace, path)))
              throw new Error("No qualified native viewer for the saved file.");
            return;
          }
          await openSavedWorkflow(
            workspace.workspace_id,
            workspace.session_id,
            path,
          );
        }}
      />
      </FileDownloadProvider>,
    );
  renderCurrent(app.getHostContext());
}
function theme(ctx?: McpUiHostContext) {
  if (!ctx) return;
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  const mapping: Record<string, string> = {
    "--color-background-primary": "--native-host-bg",
    "--color-text-primary": "--native-host-fg",
    "--color-text-secondary": "--native-host-muted",
    "--color-border-primary": "--native-host-border",
    "--font-sans": "--native-host-font",
  };
  const container = document.getElementById("editor")!;
  for (const [key, target] of Object.entries(mapping)) {
    const value =
      ctx.styles?.variables?.[
        key as keyof NonNullable<typeof ctx.styles.variables>
      ];
    if (
      typeof value === "string" &&
      value.length < 160 &&
      !/[;{}@]|url\s*\(/i.test(value)
    )
      container.style.setProperty(target, value);
    if (
      typeof value === "string" &&
      value.length < 160 &&
      !/[;{}@]|url\s*\(/i.test(value)
    )
      document.getElementById("ui-review")?.style.setProperty(target, value);
  }
}
async function open() {
  const openGeneration = ++generation;
  if (pending?.structuredContent?.native_workspace_files_enabled === true)
    setNativeFilesMode(true);
  const input = {
    ...(args.request && typeof args.request === "object"
      ? (args.request as Record<string, unknown>)
      : args),
  };
  if (
    typeof input.path === "string" &&
    /^\/workflows\/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$/.test(input.path)
  )
    input.path = input.path.slice(1);
  if (
    pending?.structuredContent?.view === "home" &&
    !pending.isError &&
    typeof input.path !== "string"
  ) {
    setNativeFilesMode(
      pending.structuredContent.native_workspace_files_enabled === true,
    );
    if (dirty) {
      notice.textContent =
        "Your draft is kept. Save it before changing workspace.";
      return;
    }
    const requested =
      typeof input.workspace_id === "string" ||
      typeof input.session_id === "string";
    const explicit = navigationState({
      schema_version: "wright.native-navigation/1",
      workspace_id: input.workspace_id,
      session_id: input.session_id,
      view: "workflows",
    });
    const acknowledged = pending.structuredContent.selection as
      Record<string, unknown> | undefined;
    if (
      requested &&
      (!explicit ||
        acknowledged?.workspace_id !== explicit.workspace_id ||
        acknowledged.session_id !== explicit.session_id)
    ) {
      notice.textContent =
        "The requested workspace was not confirmed. No other workspace was opened.";
      return;
    }
    const remembered = navigation ?? readNavigationState();
    const restored = explicit
      ? {
          ...explicit,
          ...(remembered?.workspace_id === explicit.workspace_id &&
          remembered.session_id === explicit.session_id &&
          remembered.workflow
            ? { workflow: remembered.workflow }
            : {}),
        }
      : remembered;
    if (
      explicit &&
      (selectedWorkspace?.workspace_id !== explicit.workspace_id ||
        selectedWorkspace.session_id !== explicit.session_id)
    )
      selectedWorkspace = undefined;
    navigation = restored;
    openedWorkflow = restored?.workflow;
    homeView = restored?.view ?? "workflows";
    if (nativeWorkspaceFiles && homeView === "workflows") homeView = "files";
    home();
    return;
  }
  if (
    !pending ||
    typeof input.workspace_id !== "string" ||
    typeof input.session_id !== "string" ||
    typeof input.path !== "string"
  ) {
    notice.textContent =
      "Ask the desktop conversation to open a saved workflow in this workspace.";
    return;
  }
  if (dirty) {
    notice.textContent =
      "Your draft is kept. Save it before opening another workflow.";
    return;
  }
  const data = pending.structuredContent as
    | {
        workspace?: {
          workspace_id?: string;
          session_id?: string;
          workspace_name?: string;
        };
        working_view_enabled?: boolean;
        snapshot?: InteractionSnapshot;
      }
    | undefined;
  if (
    pending.isError ||
    data?.workspace?.workspace_id !== input.workspace_id ||
    data.workspace.session_id !== input.session_id
  ) {
    notice.textContent =
      "Workspace context is unavailable. Your current draft is unchanged.";
    return;
  }
  const working = typeof input.expected_storage_digest === "string";
  const process: ProcessRef | undefined = working
    ? {
        workspace_id: input.workspace_id,
        source_path: input.path,
        source_digest: String(input.expected_storage_digest),
      }
    : undefined;
  const observed = data.snapshot?.context;
  if (
    working &&
    (data.working_view_enabled !== true ||
      !observed ||
      observed.process.workspace_id !== process!.workspace_id ||
      observed.process.source_path !== process!.source_path ||
      observed.process.source_digest !== process!.source_digest ||
      (observed.run_id ?? undefined) !== input.run_id)
  ) {
    notice.textContent =
      "The exact run or process context is unavailable. No work was started or repeated.";
    return;
  }
  const client = new NativeSourceClient(
    {
      workspaceId: input.workspace_id,
      sessionId: input.session_id,
      path: input.path,
    },
    async (name, arguments_) =>
      app.callServerTool({ name, arguments: arguments_ }),
  );
  const draftClient = new NativeEditorDraftClient(
    {
      workspaceId: input.workspace_id,
      sessionId: input.session_id,
      path: input.path,
    },
    async (name, arguments_) =>
      app.callServerTool({ name, arguments: arguments_ }),
  );
  notice.textContent = "Opening the accepted workflow…";
  try {
    const document = await client.read(); // Cached tool results are not durable restoration authority.
    if (openGeneration !== generation || dirty) return;
    if (process && document.storage_digest !== process.source_digest) {
      notice.textContent =
        "This run's source changed. Reopen its exact accepted workflow; no action was repeated.";
      return;
    }
    if (
      typeof input.restored_source_digest === "string" &&
      document.storage_digest !== input.restored_source_digest
    ) {
      notice.textContent =
        "The workflow changed since this view was saved. Open it from Workflows to inspect the current source. No run was started or resumed.";
      return;
    }
    selectedWorkspace = {
      workspace_id: input.workspace_id,
      session_id: input.session_id,
      workspace_name: data.workspace?.workspace_name ?? "Workspace",
      available: true,
      reason: null,
    };
    homeView = "workflows";
    activeSurface = "workflow";
    openedWorkflow = {
      path: input.path,
      source_digest: document.storage_digest,
      view:
        input.restored_view === "editor"
          ? "editor"
          : process
            ? "working"
            : "editor",
      ...(typeof input.run_id === "string" ? { run_id: input.run_id } : {}),
    };
    rememberLocation();
    renderCurrent = (context) =>
      root.render(
        <FileDownloadProvider request={requestDownload}>
        <div className="native-workspace-frame" data-native-file={fileBound}>
          {!fileBound && (
            <nav aria-label="Wright navigation">
              <button onClick={home}>← Workspace home</button>
            </nav>
          )}
          <NativePanelContent
            key={`${input.workspace_id}:${input.path}:${document.storage_digest}:${document.layout_revision}:${input.run_id ?? "editor"}`}
            initial={document}
            sourceClient={client}
            draftClient={draftClient}
            call={processCall}
            readEvidence={homeCall}
            transferCall={transferCall}
            onOpenTransferred={async (path) => {
              if (nativeWorkspaceFiles) {
                if (
                  !(await openWorkspaceFile(
                    {
                      workspace_id: String(input.workspace_id),
                      session_id: String(input.session_id),
                    },
                    path,
                  ))
                )
                  throw new Error(
                    "The imported file has no qualified native viewer.",
                  );
                return;
              }
              await openSavedWorkflow(
                String(input.workspace_id),
                String(input.session_id),
                path,
              );
            }}
            sessionId={String(input.session_id)}
            workspaceName={data.workspace?.workspace_name ?? "Workspace"}
            initialProcess={process}
            initialView={
              input.restored_view === "editor" ? "editor" : undefined
            }
            initialRunId={
              typeof input.run_id === "string" ? input.run_id : undefined
            }
            workingViewEnabled={data.working_view_enabled === true}
            onLocationChange={rememberWorkflow}
            theme={context?.theme}
            onDirty={(value) => {
              const changed = dirty !== value;
              dirty = value;
              if (!value && notice.textContent === pendingNavigationNotice)
                notice.textContent = "";
              if (changed) {
                rememberLocation();
                if (fileBound)
                  void fileObservation("draft-changed").catch(() => {});
              }
            }}
            onAcceptedSource={(saved) => {
              openedWorkflow = {
                path: saved.path,
                source_digest: saved.storage_digest,
                view: openedWorkflow?.view ?? "editor",
                ...(openedWorkflow?.source_digest === saved.storage_digest &&
                openedWorkflow.run_id
                  ? { run_id: openedWorkflow.run_id }
                  : {}),
              };
              rememberLocation();
            }}
          />
        </div>
        </FileDownloadProvider>,
      );
    renderCurrent(app.getHostContext());
    requestAnimationFrame(() => theme(app.getHostContext()));
    if (fileBound)
      requestAnimationFrame(() => {
        void fileObservation("rendered").catch(() => {});
      });
    notice.textContent = nativeFileNotice;
  } catch {
    if (openGeneration === generation)
      notice.textContent =
        "Wright could not open this workflow. Your saved work is unchanged; no operation was repeated.";
  }
}
app.ontoolinput = (params) => {
  const candidate = params.arguments?.file as
    Record<string, unknown> | undefined;
  if (
    candidate &&
    typeof candidate.name === "string" &&
    typeof candidate.resourceUri === "string"
  ) {
    if (
      fileInput &&
      (candidate.name !== fileInput.name ||
        candidate.resourceUri !== fileInput.resourceUri)
    ) {
      notice.textContent =
        "The host replaced this tab's document identity. Its current editor has been retained.";
      return;
    }
    fileInput = { name: candidate.name, resourceUri: candidate.resourceUri };
    void openNativeFile();
    return;
  }
  if (fileInput) return;
  args = params.arguments ?? {};
  void open();
};
app.ontoolresult = (result) => {
  if (fileInput || result.structuredContent?.view === "native-workflow-file") {
    if (result.structuredContent?.view === "native-workflow-file") {
      nativeWorkspaceFiles =
        result.structuredContent.native_workspace_files_enabled === true;
    }
    void openNativeFile();
    return;
  }
  pending = result;
  void open();
};
app.onhostcontextchanged = (context) => {
  recordReviewEvent("host-context");
  theme(context);
  renderCurrent?.(context);
};
app
  .connect()
  .then(() => {
    connected = true;
    theme(app.getHostContext());
    if (fileInput) void openNativeFile();
    else void open();
  })
  .catch(() => {
    notice.textContent =
      "Native host connection unavailable. Open this editor through the Wright plugin.";
  });
