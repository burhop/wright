import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { canonicalLayoutBytes } from "../workflow-recovery/canonical-wire";
import type { RecoveryLayout } from "../workflow-recovery/model";
import {
  WorkspaceWorkflowSourceConflictError,
  type WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";

export interface NativeSourceScope {
  readonly workspaceId: string;
  readonly sessionId: string;
  readonly path: string;
}
export type NativeSourceCall = (
  tool: "wright_workflow_read" | "wright_workflow_save",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;

function payload(result: CallToolResult): unknown {
  if (result.isError) throw new Error("Wright did not confirm this request.");
  if (result.structuredContent) return result.structuredContent;
  const text = result.content.find((item) => item.type === "text");
  if (!text || text.type !== "text") throw new Error("Wright returned no source record.");
  return JSON.parse(text.text);
}

function sameLayout(intended: RecoveryLayout, observed: RecoveryLayout): boolean {
  // Revision fields are assigned by Wright; compare the requested presentation.
  return canonicalLayoutBytes({ ...intended, semanticRevision: observed.semanticRevision, layoutRevision: observed.layoutRevision }) === canonicalLayoutBytes(observed);
}

/** Exact source operations only. Never a fetch proxy, executor, or model route. */
export class NativeSourceClient {
  private head?: WorkspaceWorkflowSourceDocument;
  private pending?: { source: string; layout: RecoveryLayout };
  private readonly scope: NativeSourceScope;
  private readonly call: NativeSourceCall;
  constructor(scope: NativeSourceScope, call: NativeSourceCall) {
    this.scope = Object.freeze({ ...scope });
    this.call = call;
  }

  private document(value: unknown): WorkspaceWorkflowSourceDocument {
    const doc = value as Partial<WorkspaceWorkflowSourceDocument> | null;
    if (!doc || doc.workspace_id !== this.scope.workspaceId || doc.path !== this.scope.path ||
        doc.metadata_authority !== "wright_host" || typeof doc.source !== "string" ||
        !Number.isInteger(doc.storage_revision) || doc.storage_revision! < 1 ||
        !Number.isInteger(doc.definition_revision) || doc.definition_revision! < 1 ||
        !/^[a-f0-9]{64}$/.test(String(doc.storage_digest)))
      throw new Error("Wright did not return the exact accepted workflow identity.");
    return doc as WorkspaceWorkflowSourceDocument;
  }
  private args() {
    return { workspace_id: this.scope.workspaceId, session_id: this.scope.sessionId, path: this.scope.path };
  }

  async read(): Promise<WorkspaceWorkflowSourceDocument> {
    const doc = this.document(payload(await this.call("wright_workflow_read", this.args())));
    if (!this.head) this.head = doc;
    // An uncertain write is reconciled only by observing its exact intended state.
    if (this.pending && doc.source === this.pending.source && doc.layout &&
        sameLayout(this.pending.layout, doc.layout))
      {
        this.pending = undefined;
        this.head = doc;
      }
    return doc;
  }

  /** Rebase only after the user explicitly reloads the accepted document. */
  accept(doc: WorkspaceWorkflowSourceDocument): void {
    if (this.pending) throw new Error("Save outcome is still unknown; preserve the draft until it is reconciled.");
    this.head = this.document(doc);
  }

  async save(source: string, layout: RecoveryLayout): Promise<WorkspaceWorkflowSourceDocument> {
    if (this.pending) throw new Error("Save outcome is still unknown. Read the accepted source; no save was repeated.");
    if (!this.head) throw new Error("Open the accepted workflow before saving.");
    const expected = this.head;
    this.pending = { source, layout: structuredClone(layout) };
    const value = payload(await this.call("wright_workflow_save", {
      ...this.args(), source, layout,
      expected_storage_revision: expected.storage_revision,
      expected_storage_digest: expected.storage_digest,
      expected_layout_revision: expected.layout_revision ?? 0,
      semantic_change_validated: true,
    })) as { ok?: boolean; document?: unknown; error?: { code?: string; outcome_known?: boolean; message?: string } };
    if (value.ok === false) {
      if (value.error?.outcome_known === true) this.pending = undefined;
      if (value.error?.code === "WORKFLOW_SOURCE_CONFLICT")
        throw new WorkspaceWorkflowSourceConflictError(null, null);
      throw new Error(value.error?.message ?? "Wright did not confirm this save.");
    }
    if (value.ok !== true) throw new Error("Wright did not confirm this save.");
    const doc = this.document(value.document);
    if (doc.source !== source || !doc.layout || !sameLayout(layout, doc.layout))
      throw new Error("Wright did not confirm the intended source and layout. Read accepted state before another save.");
    this.head = doc;
    this.pending = undefined;
    return doc;
  }
}
