import { createRoot } from "react-dom/client";
import { App, applyDocumentTheme, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import "@wright/ui-kit/styles.css";
import { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import { NativeSourceClient } from "./native-source-client";

const root = createRoot(document.getElementById("editor")!);
const notice = document.getElementById("notice")!;
const app = new App({name:"wright-native-workflow-editor",version:"0.1.0"},{},{autoResize:false});
let args: Record<string, unknown> = {};
let pending: CallToolResult | undefined;
let generation = 0;
let dirty = false;
function theme(ctx?: McpUiHostContext) {
  if (!ctx) return;
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  const mapping: Record<string,string> = {"--color-background-primary":"--color-neutral","--color-text-primary":"--color-primary","--color-text-secondary":"--color-text-muted","--color-border-primary":"--color-border","--font-sans":"--font-ui"};
  const container = document.querySelector<HTMLElement>(".native-workflow-panel") ?? document.getElementById("editor")!;
  for (const [key,target] of Object.entries(mapping)) {
    const value = ctx.styles?.variables?.[key as keyof NonNullable<typeof ctx.styles.variables>];
    if (typeof value === "string" && value.length < 160 && !/[;{}@]|url\s*\(/i.test(value)) container.style.setProperty(target,value);
  }
}
async function open() {
  const token = ++generation;
  const input = { ...args };
  if (!pending || typeof input.workspace_id !== "string" || typeof input.session_id !== "string" || typeof input.path !== "string") {
    notice.textContent = "Ask the desktop conversation to open a saved workflow in this workspace.";
    return;
  }
  if (dirty) { notice.textContent = "Your draft is kept. Save it before opening another workflow."; return; }
  const data = pending.structuredContent as {workspace?: {workspace_id?: string; session_id?: string; workspace_name?: string}} | undefined;
  if (pending.isError || data?.workspace?.workspace_id !== input.workspace_id || data.workspace.session_id !== input.session_id) { notice.textContent = "Workspace context is unavailable. Your current draft is unchanged."; return; }
  const client = new NativeSourceClient({workspaceId:input.workspace_id,sessionId:input.session_id,path:input.path},async (name,arguments_) => app.callServerTool({name,arguments:arguments_}));
  notice.textContent = "Opening the accepted workflow…";
  try {
    const document = await client.read(); // Cached tool results are not durable restoration authority.
    if (token !== generation || dirty) return;
    root.render(<NativeWorkflowPanel key={`${input.workspace_id}:${input.path}:${document.storage_digest}:${document.layout_revision}`} initial={document} client={client} workspaceName={data?.workspace?.workspace_name ?? "Workspace"} onDirty={value => { dirty = value; }} />);
    requestAnimationFrame(() => theme(app.getHostContext()));
    notice.textContent = "";
  } catch { if (token === generation) notice.textContent = "Wright could not open this workflow. Your saved work is unchanged; no operation was repeated."; }
}
app.ontoolinput = params => { args = params.arguments ?? {}; void open(); };
app.ontoolresult = result => { pending = result; void open(); };
app.onhostcontextchanged = theme;
app.connect().then(() => { theme(app.getHostContext()); void open(); }).catch(() => { notice.textContent = "Native host connection unavailable. Open this editor through the Wright plugin."; });
