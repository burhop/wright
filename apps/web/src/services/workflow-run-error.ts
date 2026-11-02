/** Shared run error; the three-argument form preserves existing callers. */
export class WorkspaceWorkflowRunError extends Error {
  readonly description: string;
  readonly code: string;
  readonly correction: string | null;
  readonly phase: "request" | "execution";
  readonly traceId: string;

  constructor(
    first: string,
    second: string,
    correction?: string | null,
    phase?: "request" | "execution",
    traceId = "",
  ) {
    const description = phase === undefined ? second : first;
    super(
      phase === undefined
        ? description
        : [description, correction].filter(Boolean).join(" "),
    );
    this.name = "WorkspaceWorkflowRunError";
    this.description = description;
    this.code = phase === undefined ? first : second;
    this.correction = correction || null;
    this.phase = phase ?? "execution";
    this.traceId = traceId;
  }
}

export function workflowRunErrorFromPayload(
  payload: unknown,
  phase: "request" | "execution",
): WorkspaceWorkflowRunError {
  const object = (value: unknown): Record<string, unknown> =>
    value !== null && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  const text = (value: unknown) => (typeof value === "string" ? value : "");
  const envelope = object(payload);
  const detail = object(envelope.detail);
  return new WorkspaceWorkflowRunError(
    text(detail.message) ||
      text(envelope.message) ||
      text(envelope.detail) ||
      "The workflow could not run.",
    (
      text(detail.code) ||
      text(envelope.error_code) ||
      text(envelope.code)
    ).toLowerCase(),
    text(detail.correction) ||
      text(object(envelope.details).correction) ||
      text(envelope.correction),
    phase,
    text(envelope.trace_id),
  );
}
