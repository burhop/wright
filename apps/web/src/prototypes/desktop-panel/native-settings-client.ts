import { z } from "zod";
import type { HomeCall, DesktopWorkspace } from "./NativeHomePanel";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

const settingsSchema = z.object({
  workspace_id: z.string(),
  revision: z.string().regex(/^[a-f0-9]{64}$/),
  workspace_prompt: z.string().max(131072).nullable(),
  git_remote_url: z.string().max(2048).nullable(),
  git_username: z.string().max(256).nullable(),
  git_large_file_threshold: z.number().int().positive().max(Number.MAX_SAFE_INTEGER).nullable(),
  remote_hidden: z.boolean(),
}).strict();
export type WorkspaceSettings = z.infer<typeof settingsSchema>;
export type WorkspaceSettingsChanges = Partial<Pick<WorkspaceSettings,
  "workspace_prompt" | "git_remote_url" | "git_username" | "git_large_file_threshold">>;

function payload(result: CallToolResult): Record<string, unknown> {
  if (result.isError) throw new Error("Wright did not confirm the settings request.");
  if (result.structuredContent) return result.structuredContent;
  const text = result.content.find((item) => item.type === "text");
  if (!text || text.type !== "text") throw new Error("No settings record was returned.");
  return JSON.parse(text.text);
}

export function publicGitRemote(value: string): boolean {
  if (value.length > 2048 || /\s/.test(value) || [...value].some((char) => char.charCodeAt(0) < 32)) return false;
  if (/^[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+$/.test(value)) return true;
  try {
    const parsed = new URL(value);
    return ["https:", "ssh:"].includes(parsed.protocol) && !!parsed.hostname &&
      !parsed.password && !parsed.search && !parsed.hash &&
      (parsed.protocol !== "https:" || !parsed.username);
  } catch { return false; }
}

/** Exact existing settings only. No credential channel, Git action or agent switch. */
export class NativeSettingsClient {
  private head?: WorkspaceSettings;
  private pending?: WorkspaceSettingsChanges;
  private readonly scope: {workspace_id: string; session_id: string};
  private readonly call: HomeCall;
  constructor(workspace: Pick<DesktopWorkspace, "workspace_id" | "session_id">, call: HomeCall) {
    this.scope = Object.freeze({workspace_id: workspace.workspace_id, session_id: workspace.session_id});
    this.call = call;
  }
  get requiresRead(): boolean { return !!this.pending; }
  private record(value: Record<string, unknown>): WorkspaceSettings {
    const saved = settingsSchema.parse(value.settings);
    if (value.workspace_id !== this.scope.workspace_id || value.session_id !== this.scope.session_id || saved.workspace_id !== this.scope.workspace_id)
      throw new Error("Saved settings belong to a different workspace or session.");
    return saved;
  }
  private matches(saved: WorkspaceSettings, changes: WorkspaceSettingsChanges): boolean {
    return Object.entries(changes).every(([key, value]) => saved[key as keyof WorkspaceSettings] === value) &&
      (!("git_remote_url" in changes) || !saved.remote_hidden);
  }
  async read(): Promise<WorkspaceSettings> {
    const saved = this.record(payload(await this.call("wright_workspace_settings_read", {request: this.scope})));
    if (!this.head) this.head = saved;
    if (this.pending && this.matches(saved, this.pending)) {
      this.pending = undefined;
      this.head = saved;
    }
    return saved;
  }
  accept(saved: WorkspaceSettings): void {
    if (this.pending) throw new Error("Read the unconfirmed save before replacing your settings edit.");
    if (saved.workspace_id !== this.scope.workspace_id) throw new Error("Workspace identity differs.");
    this.head = saved;
  }
  async save(changes: WorkspaceSettingsChanges): Promise<WorkspaceSettings> {
    if (!this.head || this.pending) throw new Error("Read saved settings before another write; no save was repeated.");
    if (changes.git_remote_url && !publicGitRemote(changes.git_remote_url))
      throw new Error("Use HTTPS or SSH without passwords, tokens, query or fragment.");
    this.pending = {...changes};
    const value = payload(await this.call("wright_workspace_settings_save", {request: {
      ...this.scope, expected_revision: this.head.revision, changes,
    }}));
    if (value.ok !== true) {
      const error = value.error as {outcome_known?: boolean; message?: string} | undefined;
      if (error?.outcome_known) this.pending = undefined;
      throw new Error(error?.message ?? "Settings save is unconfirmed. Read saved state before continuing.");
    }
    const saved = this.record(value);
    if (!this.matches(saved, changes)) throw new Error("The intended settings were not confirmed. Read saved state.");
    this.pending = undefined;
    this.head = saved;
    return saved;
  }
}
