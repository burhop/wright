import { hostAdapter } from "./host-adapter";

export interface WorkflowReasoningWait {
  readonly runId: string;
  readonly requestId: string;
  readonly queuedAt: string;
  readonly label: string;
  readonly detail: string;
}

export type WorkflowReasoningStatusReader = (
  runId: string,
  signal: AbortSignal,
) => Promise<WorkflowReasoningWait | null>;

/** Read the existing durable handoff owner; never answer or execute from the UI. */
export async function readDesktopReasoningWait(
  scope: {
    workspaceId: string;
    sessionId: string;
    runId: string;
    workspaceName: string;
  },
  signal: AbortSignal,
): Promise<WorkflowReasoningWait | null> {
  const query = new URLSearchParams({
    workspace_id: scope.workspaceId,
    session_id: scope.sessionId,
  });
  const response = await hostAdapter.fetch(
    `${hostAdapter.getApiBaseUrl()}/api/desktop/reasoning?${query}`,
    { method: "GET", signal },
  );
  if (!response.ok)
    throw new Error(
      `AI handoff status could not be read (HTTP ${response.status}).`,
    );
  return desktopReasoningWait(await response.json(), scope);
}

/** Shared bounded status interpretation; transports never answer the task. */
export function desktopReasoningWait(
  rows: unknown,
  scope: {
    workspaceId: string;
    sessionId: string;
    runId: string;
    workspaceName: string;
  },
): WorkflowReasoningWait | null {
  if (!Array.isArray(rows))
    throw new Error("Wright returned invalid AI handoff status.");
  const matches: WorkflowReasoningWait[] = [];
  for (const row of rows) {
    const request = row?.request;
    if (
      !request ||
      request.workspace_id !== scope.workspaceId ||
      request.session_id !== scope.sessionId
    )
      throw new Error(
        "Wright returned AI handoff status for another workspace or session.",
      );
    if (request.run_id !== scope.runId) continue;
    if (
      request.schema_version !== "wright.desktop-reasoning/1" ||
      request.binding?.adapter !== "openai-desktop-harness" ||
      !["response", "action"].includes(request.kind) ||
      typeof request.request_id !== "string" ||
      !request.request_id ||
      typeof request.created_at !== "string" ||
      !Number.isFinite(Date.parse(request.created_at))
    )
      throw new Error("Wright returned invalid AI handoff identity.");
    matches.push({
      runId: scope.runId,
      requestId: request.request_id,
      queuedAt: request.created_at,
      label: "Waiting for desktop chat",
      detail: `The AI task is queued for this conversation. This prototype does not automatically start a chat turn. Send “Continue the workflow in ${scope.workspaceName}” in the desktop chat to continue this same run.`,
    });
  }
  if (matches.length > 1)
    throw new Error(
      "Wright returned more than one pending AI task for this run.",
    );
  return matches[0] ?? null;
}
