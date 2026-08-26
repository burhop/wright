export type WorkflowOutputKind =
  "document" | "model" | "file" | "dataset" | "link" | "message" | "other";

export type WorkflowOutputDurability = "durable" | "session" | "ephemeral";

export type WorkflowOutputActionKind =
  "view" | "open" | "download" | "open-in-application";

export interface WorkflowOutputAction {
  actionId: string;
  kind: WorkflowOutputActionKind;
  label: string;
  available: boolean;
  unavailableReason?: string;
}

/**
 * Serializable reference stored in a run record. The action implementation is
 * resolved separately by the runtime that produced the output.
 */
export interface WorkflowOutputReference {
  outputId: string;
  title: string;
  kind: WorkflowOutputKind;
  description: string;
  format?: string;
  sizeBytes?: number;
  durability: WorkflowOutputDurability;
  producer: {
    block: string;
    serverId?: string;
    toolName?: string;
  };
  actions: readonly WorkflowOutputAction[];
}

function isOutputReference(value: unknown): value is WorkflowOutputReference {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const candidate = value as Partial<WorkflowOutputReference>;
  return (
    typeof candidate.outputId === "string" &&
    typeof candidate.title === "string" &&
    typeof candidate.kind === "string" &&
    typeof candidate.description === "string" &&
    typeof candidate.durability === "string" &&
    Boolean(candidate.producer) &&
    Array.isArray(candidate.actions)
  );
}

export function workflowOutputsFrom(value: unknown): WorkflowOutputReference[] {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  const outputs = (value as { outputs?: unknown }).outputs;
  return Array.isArray(outputs) ? outputs.filter(isOutputReference) : [];
}
