import { z } from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import type { WorkflowEditorDraftSnapshot } from "../workflow-recovery/WorkflowRecoveryConcept";
import type { NativeSourceScope } from "./native-source-client";

export type NativeEditorDraftCall = (
  name: "wright_editor_drafts_read" | "wright_editor_draft_save",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;
const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const metadata = z
  .object({
    schema_version: z.literal("wright.workflow-editor-draft/1"),
    path: z.string(),
    draft_id: id,
    request_id: id,
    base_storage_revision: z.number().int().positive(),
    base_storage_digest: digest,
    draft_revision: z.number().int().positive(),
    draft_digest: digest,
    updated_at: z.number().int().positive(),
    view: z.enum(["diagram", "code", "split"]),
    base_matches_current: z.boolean(),
    matches_accepted: z.boolean(),
    accepted_checkpoint: z.boolean(),
  })
  .strict();
const record = metadata
  .extend({
    source: z.string().max(1048576),
    applied_source: z.string().max(1048576),
    // Presentation is validated again against the recovered diagram by the shared editor.
    layout: z.record(z.string(), z.unknown()).nullable(),
  })
  .strict();
export type EditorDraftMetadata = z.infer<typeof metadata>;
export type EditorDraftRecord = Omit<z.infer<typeof record>, "layout"> &
  WorkflowEditorDraftSnapshot;
type Snapshot = WorkflowEditorDraftSnapshot & {
  base_storage_revision: number;
  base_storage_digest: string;
};
function body(result: CallToolResult): Record<string, unknown> {
  if (result.isError)
    throw new Error("Wright did not confirm the draft request.");
  if (result.structuredContent) return result.structuredContent;
  const text = result.content.find((item) => item.type === "text");
  if (!text || text.type !== "text")
    throw new Error("No draft record was returned.");
  return JSON.parse(text.text);
}
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonical(row[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

/** CAS on inert editor state only. A lost response requires an explicit read. */
export class NativeEditorDraftClient {
  private readonly scope: NativeSourceScope;
  private readonly call: NativeEditorDraftCall;
  private stream?: { id: string; digest: string };
  private pending?: { id: string; requestId: string; snapshot: Snapshot };
  private denied = false;
  constructor(scope: NativeSourceScope, call: NativeEditorDraftCall) {
    this.scope = Object.freeze({ ...scope });
    this.call = call;
  }
  get requiresRead(): boolean {
    return !!this.pending || this.denied;
  }
  private args() {
    return {
      workspace_id: this.scope.workspaceId,
      session_id: this.scope.sessionId,
      path: this.scope.path,
    };
  }
  private scoped(result: CallToolResult): Record<string, unknown> {
    const value = body(result);
    if (
      value.workspace_id !== this.scope.workspaceId ||
      value.session_id !== this.scope.sessionId ||
      value.path !== this.scope.path
    )
      throw new Error(
        "Saved draft belongs to a different workspace or source.",
      );
    return value;
  }
  async list(): Promise<EditorDraftMetadata[]> {
    const value = this.scoped(
      await this.call("wright_editor_drafts_read", {
        request: { ...this.args(), draft_id: null },
      }),
    );
    const rows = z.array(metadata).max(64).parse(value.drafts);
    if (rows.some((row) => row.path !== this.scope.path))
      throw new Error("Draft source differs.");
    return rows;
  }
  async read(draftId: string): Promise<EditorDraftRecord> {
    const value = this.scoped(
      await this.call("wright_editor_drafts_read", {
        request: { ...this.args(), draft_id: draftId },
      }),
    );
    const saved = record.parse(value.draft) as EditorDraftRecord;
    if (saved.draft_id !== draftId || saved.path !== this.scope.path)
      throw new Error("Draft identity differs.");
    if (
      this.pending?.id === draftId &&
      this.pending.requestId === saved.request_id &&
      this.same(saved, this.pending.snapshot)
    ) {
      this.stream = { id: draftId, digest: saved.draft_digest };
      this.pending = undefined;
      this.denied = false;
    }
    return saved;
  }
  /** Explicit user recovery only; never silently rebase a draft from an older source. */
  resume(
    saved: EditorDraftRecord,
    accepted: WorkspaceWorkflowSourceDocument,
  ): void {
    if (this.requiresRead)
      throw new Error("Resolve the previous draft save first.");
    if (
      !saved.base_matches_current ||
      saved.path !== this.scope.path ||
      saved.base_storage_revision !== accepted.storage_revision ||
      saved.base_storage_digest !== accepted.storage_digest
    )
      throw new Error(
        "This draft is based on an older workflow. Inspect and copy it instead.",
      );
    this.stream = { id: saved.draft_id, digest: saved.draft_digest };
  }
  private same(saved: EditorDraftRecord, snapshot: Snapshot): boolean {
    return Object.entries(snapshot).every(
      ([key, value]) =>
        canonical(saved[key as keyof EditorDraftRecord]) === canonical(value),
    );
  }
  async save(
    snapshot: WorkflowEditorDraftSnapshot,
    accepted: WorkspaceWorkflowSourceDocument,
    dirty: boolean,
  ): Promise<EditorDraftMetadata | undefined> {
    if (this.requiresRead)
      throw new Error("Draft save needs inspection; no write was repeated.");
    if (!dirty && !this.stream) return;
    const intended: Snapshot = dirty
      ? {
          ...snapshot,
          base_storage_revision: accepted.storage_revision,
          base_storage_digest: accepted.storage_digest,
        }
      : {
          source: accepted.source,
          applied_source: accepted.source,
          layout: accepted.layout ?? null,
          view: snapshot.view,
          base_storage_revision: accepted.storage_revision,
          base_storage_digest: accepted.storage_digest,
        };
    const draftId = this.stream?.id ?? crypto.randomUUID();
    const requestId = crypto.randomUUID();
    this.pending = {
      id: draftId,
      requestId,
      snapshot: structuredClone(intended),
    };
    const value = body(
      await this.call("wright_editor_draft_save", {
        request: {
          ...this.args(),
          draft_id: draftId,
          request_id: requestId,
          expected_draft_digest: this.stream?.digest ?? null,
          snapshot: intended,
        },
      }),
    );
    if (value.ok !== true) {
      const error = value.error as { outcome_known?: boolean } | undefined;
      if (error?.outcome_known === true) {
        this.pending = undefined;
        this.denied = true;
      }
      throw new Error(
        error?.outcome_known === true
          ? "Draft was not saved. Inspect saved drafts; your open edits are preserved."
          : "Draft save is unconfirmed. Read its saved state before continuing.",
      );
    }
    // Scope, request, and exact intended content must all be acknowledged.
    this.scoped({ content: [], structuredContent: value });
    const saved = record.parse(value.draft) as EditorDraftRecord;
    if (
      saved.draft_id !== draftId ||
      saved.request_id !== requestId ||
      saved.path !== this.scope.path ||
      !this.same(saved, intended)
    )
      throw new Error(
        "The intended draft was not confirmed. Read saved state before continuing.",
      );
    this.stream = { id: draftId, digest: saved.draft_digest };
    this.pending = undefined;
    return metadata.parse(
      Object.fromEntries(
        Object.entries(saved).filter(
          ([key]) => !["source", "applied_source", "layout"].includes(key),
        ),
      ),
    );
  }
  async inspectPending(): Promise<boolean> {
    if (!this.pending) return false;
    await this.read(this.pending.id);
    return !this.pending;
  }
  startSeparateDraft(): void {
    if (this.pending)
      throw new Error("The previous draft outcome is still unconfirmed.");
    this.stream = undefined;
    this.denied = false;
  }
}
