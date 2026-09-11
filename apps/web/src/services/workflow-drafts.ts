import { z } from "zod";

import { hostAdapter } from "./host-adapter";

export const MAX_WORKFLOW_DRAFT_BYTES = 1024 * 1024;
const identifier = z
  .string()
  .regex(/^[a-z0-9][a-z0-9._-]*$/)
  .max(96);
const text = z.string().min(1).max(500);
const digest = z.string().regex(/^[0-9a-f]{64}$/);
const ids = z.array(identifier).max(64);

const phase = z
  .object({
    id: identifier,
    name: text,
    purpose: text,
    order: z.number().int().min(0).max(15),
    block_ids: ids,
  })
  .strict();
const block = z
  .object({
    id: identifier,
    title: text,
    purpose: text,
    role: z.enum(["input", "work", "review", "release"]),
    phase_id: identifier,
    input_port_ids: ids,
    output_port_ids: ids,
    gate_ids: ids,
    intended_artifact_ids: ids,
  })
  .strict();
const port = z
  .object({
    id: identifier,
    owner_block_id: identifier,
    direction: z.enum(["input", "output"]),
    name: text,
    value_type_id: identifier,
    required: z.boolean(),
    cardinality: z.enum(["one", "many"]),
  })
  .strict();
const connection = z
  .object({
    id: identifier,
    source_port_id: identifier,
    target_port_id: identifier,
  })
  .strict();
const gate = z
  .object({
    id: identifier,
    owner_block_id: identifier,
    condition: text,
    proceed_target_block_id: identifier,
    revise_target_block_id: identifier,
    feedback_path_id: identifier,
  })
  .strict();
const feedbackPath = z
  .object({
    id: identifier,
    from_gate_id: identifier,
    to_block_id: identifier,
    reason: text,
  })
  .strict();
const intendedArtifact = z
  .object({
    id: identifier,
    title: text,
    artifact_type_id: identifier,
    description: text,
    produced_by_block_id: identifier,
  })
  .strict();
const semantic = z
  .object({
    title: text,
    purpose: text,
    phases: z.array(phase).min(1).max(16),
    blocks: z.array(block).max(100),
    ports: z.array(port).max(400),
    connections: z.array(connection).max(400),
    gates: z.array(gate).max(100),
    feedback_paths: z.array(feedbackPath).max(100),
    intended_artifacts: z.array(intendedArtifact).max(200),
  })
  .strict();
const layout = z
  .object({
    schema_version: z.literal("1.0.0"),
    positions: z
      .array(
        z
          .object({
            semantic_id: identifier,
            x: z.number().int().min(-10_000).max(10_000),
            y: z.number().int().min(-10_000).max(10_000),
          })
          .strict(),
      )
      .max(100),
  })
  .strict();
const workflowDraft = z
  .object({
    document_kind: z.literal("workflow-draft"),
    schema_version: z.literal("1.0.0-draft.1"),
    draft_id: identifier,
    revision: z.number().int().min(1),
    semantic_sha256: digest,
    layout_sha256: digest,
    semantic,
    layout,
  })
  .strict();
const diagnostic = z
  .object({
    code: z
      .string()
      .regex(/^[A-Z][A-Z0-9_]*$/)
      .max(96),
    path: z.string().min(1).max(300),
    affected_semantic_ids: z.array(identifier).max(64),
    explanation: text,
    correction: text,
  })
  .strict();
const validationResult = z
  .object({
    valid: z.boolean(),
    semantic_sha256: digest,
    layout_sha256: digest,
    diagnostics: z.array(diagnostic).max(256),
  })
  .strict();
const errorResult = z
  .object({
    error_code: z
      .string()
      .regex(/^[A-Z][A-Z0-9_]*$/)
      .max(96),
    message: text,
    recovery_class: identifier,
    trace_id: z.string().min(1).max(200),
    diagnostics: z.array(diagnostic).max(256).optional(),
  })
  .strict();

export type WorkflowDraft = z.infer<typeof workflowDraft>;
export type WorkflowDraftValidation = z.infer<typeof validationResult>;

export interface WorkflowDraftResult {
  draft: WorkflowDraft;
  etag: string;
}

export class WorkflowDraftClientError extends Error {
  readonly status: number;
  readonly errorCode: string;

  constructor(status: number, errorCode: string) {
    super("Workflow draft request failed.");
    this.name = "WorkflowDraftClientError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonical(row[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

async function sha256(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonical(value));
  const result = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(result)]
    .map((item) => item.toString(16).padStart(2, "0"))
    .join("");
}

export async function bindWorkflowDraftIdentities(
  draft: WorkflowDraft,
): Promise<WorkflowDraft> {
  return {
    ...draft,
    semantic_sha256: await sha256(draft.semantic),
    layout_sha256: await sha256(draft.layout),
  };
}

export function decodeWorkflowDraft(value: unknown): WorkflowDraft {
  return workflowDraft.parse(value);
}

export async function verifyWorkflowDraftIdentity(
  draft: WorkflowDraft,
): Promise<void> {
  if ((await sha256(draft.semantic)) !== draft.semantic_sha256) {
    throw new Error("WORKFLOW_DRAFT_SEMANTIC_IDENTITY_MISMATCH");
  }
  if ((await sha256(draft.layout)) !== draft.layout_sha256) {
    throw new Error("WORKFLOW_DRAFT_LAYOUT_IDENTITY_MISMATCH");
  }
}

async function decodeResponse(
  response: Response,
): Promise<WorkflowDraftResult> {
  if (!response.ok) {
    let code = "WORKFLOW_DRAFT_STORAGE_FAILED";
    try {
      const body = await response.text();
      if (new TextEncoder().encode(body).byteLength > 16 * 1024)
        throw new Error();
      const error = errorResult.parse(JSON.parse(body));
      code = error.error_code;
    } catch {
      /* use support-safe fallback */
    }
    throw new WorkflowDraftClientError(response.status, code);
  }
  const body = await response.text();
  if (new TextEncoder().encode(body).byteLength > MAX_WORKFLOW_DRAFT_BYTES) {
    throw new Error("WORKFLOW_DRAFT_RESPONSE_TOO_LARGE");
  }
  const draft = decodeWorkflowDraft(JSON.parse(body));
  await verifyWorkflowDraftIdentity(draft);
  const etag = response.headers.get("etag");
  if (etag !== `"${await sha256(draft)}"`)
    throw new Error("WORKFLOW_DRAFT_ETAG_MISMATCH");
  return { draft, etag };
}

function url(path = ""): string {
  return `${hostAdapter.getApiBaseUrl()}/api/workflow-drafts${path}`;
}

export async function createWorkflowDraft(
  title: string,
  purpose: string,
): Promise<WorkflowDraftResult> {
  return decodeResponse(
    await hostAdapter.fetch(url(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, purpose }),
    }),
  );
}

export async function readWorkflowDraft(
  draftId: string,
): Promise<WorkflowDraftResult> {
  return decodeResponse(
    await hostAdapter.fetch(url(`/${encodeURIComponent(draftId)}`), {
      cache: "no-cache",
    }),
  );
}

export async function validateWorkflowDraft(
  draft: WorkflowDraft,
): Promise<WorkflowDraftValidation> {
  const response = await hostAdapter.fetch(
    url(`/${encodeURIComponent(draft.draft_id)}/validate`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: canonical(draft),
    },
  );
  if (!response.ok)
    throw new WorkflowDraftClientError(
      response.status,
      "WORKFLOW_DRAFT_INVALID",
    );
  const body = await response.text();
  if (new TextEncoder().encode(body).byteLength > MAX_WORKFLOW_DRAFT_BYTES) {
    throw new Error("WORKFLOW_DRAFT_RESPONSE_TOO_LARGE");
  }
  return validationResult.parse(JSON.parse(body));
}

export async function saveWorkflowDraft(
  draft: WorkflowDraft,
  etag: string,
): Promise<WorkflowDraftResult> {
  return decodeResponse(
    await hostAdapter.fetch(url(`/${encodeURIComponent(draft.draft_id)}`), {
      method: "PUT",
      headers: { "Content-Type": "application/json", "If-Match": etag },
      body: canonical(draft),
    }),
  );
}
