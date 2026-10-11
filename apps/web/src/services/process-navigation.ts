import {
  ProcessClientError,
  type NavigationResolution,
  type NavigationTarget,
  type ProcessRef,
} from "@wright/process-client";

/** Transient host focus, never persisted run state or execution authority. */
export interface ProcessNavigationRequest {
  readonly requestId: string;
  readonly resolution: NavigationResolution;
}

export function createProcessNavigationDispatcher() {
  let host:
    | ((process: ProcessRef, resolution: NavigationResolution) => Promise<void>)
    | undefined;
  return Object.freeze({
    setHost(value: typeof host) {
      host = value;
    },
    async navigate(
      process: ProcessRef,
      _target: NavigationTarget,
      resolution: NavigationResolution,
    ) {
      if (!host)
        throw new ProcessClientError({
          code: "CAPABILITY_UNAVAILABLE",
          message: "This view has no workspace navigation host.",
          correction: "Open the process in its Wright workspace.",
        });
      await host(process, resolution);
    },
  });
}

export function sameProcessReference(
  left: ProcessRef,
  right: ProcessRef,
): boolean {
  return (
    left.workspace_id === right.workspace_id &&
    left.source_path === right.source_path &&
    left.source_digest === right.source_digest
  );
}
