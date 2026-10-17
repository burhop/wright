import { createRoot } from "react-dom/client";
import {
  App,
  applyDocumentTheme,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import "@wright/ui-kit/styles.css";
import type { InteractionSnapshot, ProcessRef } from "@wright/process-client";
import { NativePanelContent } from "./NativePanelContent";
import { NativeSourceClient } from "./native-source-client";
import { NativeEditorDraftClient } from "./native-editor-draft-client";
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
} from "./native-navigation-state";

const root = createRoot(document.getElementById("editor")!);
const notice = document.getElementById("notice")!;
const app = new App(
  { name: "wright-native-workflow-editor", version: "0.1.0" },
  {},
  { autoResize: false },
);
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
let homeGeneration = 0;
let openedWorkflow:
  { path: string; source_digest: string; run_id?: string } | undefined;
function rememberLocation() {
  if (!selectedWorkspace) return;
  navigation = {
    schema_version: "wright.native-navigation/1",
    workspace_id: selectedWorkspace.workspace_id,
    session_id: selectedWorkspace.session_id,
    view: homeView,
  };
  const widgetAccepted = rememberNavigationState(navigation);
  const version = ++contextGeneration;
  const context = {
    ...navigation,
    workspace_name: selectedWorkspace.workspace_name,
    ...(openedWorkflow
      ? { workflow: { ...openedWorkflow, editor_has_unsaved_changes: dirty } }
      : {}),
  };
  contextWrite = contextWrite
    .catch(() => {})
    .then(async () => {
      if (version !== contextGeneration) return;
      try {
        await app.updateModelContext(
          { structuredContent: context },
          { timeout: 5000 },
        );
        if (version === contextGeneration) {
          restorationNotice = widgetAccepted
            ? ""
            : "Workspace context is available to this conversation, but this host does not save panel navigation. Ask the conversation to reopen this workspace.";
          renderCurrent?.(app.getHostContext());
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
  if (
    selectedWorkspace?.workspace_id !== workspace.workspace_id ||
    selectedWorkspace.session_id !== workspace.session_id
  )
    openedWorkflow = undefined;
  selectedWorkspace = workspace;
  rememberLocation();
};
const rememberView = (view: HomeView) => {
  homeView = view;
  openedWorkflow = undefined;
  rememberLocation();
};
let renderCurrent: ((context?: McpUiHostContext) => void) | undefined;
const processCall: NativeProcessCall = (name, request) =>
  app.callServerTool({ name, arguments: { request } });
const transferCall: NativeTransferCall = (name, arguments_) =>
  app.callServerTool({ name, arguments: arguments_ });

async function openSavedWorkflow(
  workspaceId: string,
  sessionId: string,
  path: string,
) {
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
function home() {
  if (dirty) {
    notice.textContent =
      "Your draft is kept. Save it before changing workspace.";
    return;
  }
  generation++;
  openedWorkflow = undefined;
  const homeKey = ++homeGeneration;
  notice.textContent = "";
  renderCurrent = () =>
    root.render(
      <NativeHomePanel
        key={homeKey}
        call={homeCall}
        initialSelection={selectedWorkspace ?? navigation}
        initialView={homeView}
        onNavigate={rememberView}
        restorationNotice={restorationNotice}
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
          await openSavedWorkflow(
            workspace.workspace_id,
            workspace.session_id,
            path,
          );
        }}
      />,
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
  }
}
async function open() {
  const openGeneration = ++generation;
  const input = {
    ...(args.request && typeof args.request === "object"
      ? (args.request as Record<string, unknown>)
      : args),
  };
  if (
    pending?.structuredContent?.view === "home" &&
    !pending.isError &&
    typeof input.path !== "string"
  ) {
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
    const restored = explicit ?? navigation ?? readNavigationState();
    if (
      explicit &&
      (selectedWorkspace?.workspace_id !== explicit.workspace_id ||
        selectedWorkspace.session_id !== explicit.session_id)
    )
      selectedWorkspace = undefined;
    navigation = restored;
    homeView = restored?.view ?? "workflows";
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
  const draftClient = new NativeEditorDraftClient({
    workspaceId: input.workspace_id, sessionId: input.session_id, path: input.path,
  }, async (name, arguments_) => app.callServerTool({name, arguments: arguments_}));
  notice.textContent = "Opening the accepted workflow…";
  try {
    const document = await client.read(); // Cached tool results are not durable restoration authority.
    if (openGeneration !== generation || dirty) return;
    if (process && document.storage_digest !== process.source_digest) {
      notice.textContent =
        "This run's source changed. Reopen its exact accepted workflow; no action was repeated.";
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
    openedWorkflow = {
      path: input.path,
      source_digest: document.storage_digest,
      ...(typeof input.run_id === "string" ? { run_id: input.run_id } : {}),
    };
    rememberLocation();
    renderCurrent = (context) =>
      root.render(
        <div className="native-workspace-frame">
          <nav aria-label="Wright navigation">
            <button onClick={home}>Workspaces</button>
          </nav>
          <NativePanelContent
            key={`${input.workspace_id}:${input.path}:${document.storage_digest}:${document.layout_revision}:${input.run_id ?? "editor"}`}
            initial={document}
            sourceClient={client}
            draftClient={draftClient}
            call={processCall}
            transferCall={transferCall}
            onOpenTransferred={(path) =>
              openSavedWorkflow(
                String(input.workspace_id),
                String(input.session_id),
                path,
              )
            }
            sessionId={String(input.session_id)}
            workspaceName={data.workspace?.workspace_name ?? "Workspace"}
            initialProcess={process}
            initialRunId={
              typeof input.run_id === "string" ? input.run_id : undefined
            }
            workingViewEnabled={data.working_view_enabled === true}
            theme={context?.theme}
            onDirty={(value) => {
              const changed = dirty !== value;
              dirty = value;
              if (changed) rememberLocation();
            }}
            onAcceptedSource={(saved) => {
              openedWorkflow = {
                path: saved.path,
                source_digest: saved.storage_digest,
                ...(openedWorkflow?.source_digest === saved.storage_digest &&
                openedWorkflow.run_id
                  ? { run_id: openedWorkflow.run_id }
                  : {}),
              };
              rememberLocation();
            }}
          />
        </div>,
      );
    renderCurrent(app.getHostContext());
    requestAnimationFrame(() => theme(app.getHostContext()));
    notice.textContent = "";
  } catch {
    if (openGeneration === generation)
      notice.textContent =
        "Wright could not open this workflow. Your saved work is unchanged; no operation was repeated.";
  }
}
app.ontoolinput = (params) => {
  args = params.arguments ?? {};
  void open();
};
app.ontoolresult = (result) => {
  pending = result;
  void open();
};
app.onhostcontextchanged = (context) => {
  theme(context);
  renderCurrent?.(context);
};
app
  .connect()
  .then(() => {
    theme(app.getHostContext());
    void open();
  })
  .catch(() => {
    notice.textContent =
      "Native host connection unavailable. Open this editor through the Wright plugin.";
  });
