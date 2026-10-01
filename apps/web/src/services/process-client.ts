import {
  createNativeProcessClient,
  type NativeProcessClientOptions,
  type ProcessClient,
} from "@wright/process-client";
import { hostAdapter } from "./host-adapter";

/** Keep shell authentication and desktop URL handling out of the public SDK. */
export function createWorkspaceProcessClient(
  options: Omit<NativeProcessClientOptions, "fetch" | "baseUrl">,
): ProcessClient {
  return createNativeProcessClient({
    ...options,
    fetch: (input, init) => hostAdapter.fetch(input, init),
    baseUrl: hostAdapter.resolveBackendUrl("/api/workspace/process-interfaces"),
  });
}
