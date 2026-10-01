import type { Reason } from "./contracts.generated";

/** Safe user-facing reasons; raw provider/HTTP payloads stay in their owner. */
export class ProcessClientError extends Error {
  readonly reason: Reason;
  readonly httpStatus?: number;
  readonly requestId?: string;
  readonly uncertain: boolean;

  constructor(
    reason: Reason,
    options: {
      httpStatus?: number;
      requestId?: string;
      uncertain?: boolean;
    } = {},
  ) {
    super(reason.message);
    this.name = "ProcessClientError";
    this.reason = Object.freeze({ ...reason });
    this.httpStatus = options.httpStatus;
    this.requestId = options.requestId;
    this.uncertain = options.uncertain ?? reason.code === "OUTCOME_UNKNOWN";
  }
}

export function clientError(
  code: string,
  message: string,
  correction: string,
): ProcessClientError {
  return new ProcessClientError({ code, message, correction });
}

export function unknownOutcome(requestId: string): ProcessClientError {
  return new ProcessClientError(
    {
      code: "OUTCOME_UNKNOWN",
      message: "Wright could not confirm whether the request was accepted.",
      correction:
        "Reconcile the saved run or retry this exact request with the same request ID. Do not create a new request.",
    },
    { requestId, uncertain: true },
  );
}
