import { hostAdapter } from "../host-adapter";
import {
  parseSurfaceDescriptor,
  type SurfaceDescriptor,
} from "./surface-contract";
import type { SafeDisplayRepresentation } from "./renderers/safe-renderers";

export interface DisplayProjection {
  readonly artifactId: string;
  readonly surfaceId: string;
  readonly displayId: string;
  readonly revision: number;
  readonly title: string;
  readonly accessibilityDescription: string;
  readonly durability: "durable" | "session" | "ephemeral";
  readonly representations: readonly SafeDisplayRepresentation[];
}

export interface DisplayHistoryItem {
  readonly artifactId: string;
  readonly revision: number;
  readonly current: boolean;
  readonly createdAt: string;
}

export interface PresentationLaunch {
  readonly presentationId: string;
  readonly instanceId: string;
  readonly generation: number;
  readonly kind: "panel" | "browser";
  readonly absoluteBootstrapUrl: string;
  readonly expiresAt: string;
}

export interface PresentationPreference {
  readonly kind: "panel" | "browser";
  readonly remembered: boolean;
  readonly reason: string;
}

export type LiveAppOperation = "start" | "retry" | "restart" | "stop";

export interface LiveAppRuntime {
  readonly surfaceId: string;
  readonly instanceId: string;
  readonly generation: number;
  readonly state: SurfaceDescriptor["lifecycle"];
  readonly sharing: string;
  readonly ownership: string;
  readonly platform: string | null;
  readonly lifetimePolicy: string;
  readonly failure: {
    readonly code: string;
    readonly message: string;
    readonly retryable: boolean;
  } | null;
  readonly actions: readonly {
    readonly operation: LiveAppOperation;
    readonly label: string;
  }[];
}

export interface LiveAppHealth {
  readonly instanceId: string;
  readonly generation: number;
  readonly state: string;
  readonly ok: boolean | null;
  readonly diagnosticCode: string | null;
  readonly message: string;
  readonly observedStatus: number | null;
  readonly attempts: number;
}

export interface LiveAppLogs {
  readonly entries: readonly {
    readonly sequence: number;
    readonly stream: string;
    readonly message: string;
    readonly capturedAt: string;
    readonly byteCount: number;
  }[];
  readonly rotated: boolean;
  readonly droppedBytes: number;
  readonly nextSequence: number;
}

function responseRecord(
  value: unknown,
  label: string,
): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${label} response is malformed`);
  }
  return value as Record<string, unknown>;
}

function responseString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new TypeError(`${label} is malformed`);
  }
  return value;
}

function parsePresentationLaunch(
  value: unknown,
  requestedKind: "panel" | "browser",
): PresentationLaunch {
  const launch = responseRecord(value, "presentation launch");
  if (launch.kind !== requestedKind) {
    throw new TypeError("presentation launch kind does not match the request");
  }
  if (
    !Number.isSafeInteger(launch.generation) ||
    Number(launch.generation) < 1
  ) {
    throw new TypeError("presentation launch generation is malformed");
  }
  const expiresAt = responseString(launch.expiresAt, "presentation expiresAt");
  if (Number.isNaN(Date.parse(expiresAt))) {
    throw new TypeError("presentation expiresAt is malformed");
  }
  return Object.freeze({
    presentationId: responseString(
      launch.presentationId,
      "presentation presentationId",
    ),
    instanceId: responseString(launch.instanceId, "presentation instanceId"),
    generation: Number(launch.generation),
    kind: requestedKind,
    absoluteBootstrapUrl: hostAdapter.validateIssuedPreviewUrl(
      responseString(
        launch.absoluteBootstrapUrl,
        "presentation absoluteBootstrapUrl",
      ),
    ),
    expiresAt,
  });
}

function parsePresentationPreference(value: unknown): PresentationPreference {
  const preference = responseRecord(value, "presentation preference");
  if (preference.kind !== "panel" && preference.kind !== "browser") {
    throw new TypeError("presentation preference kind is malformed");
  }
  if (typeof preference.remembered !== "boolean") {
    throw new TypeError(
      "presentation preference remembered state is malformed",
    );
  }
  return Object.freeze({
    kind: preference.kind,
    remembered: preference.remembered,
    reason: responseString(preference.reason, "presentation preference reason"),
  });
}

function parseLiveAppRuntime(value: unknown): LiveAppRuntime {
  const runtime = responseRecord(value, "live app");
  const states = new Set([
    "declared",
    "starting",
    "ready",
    "unhealthy",
    "stopping",
    "stopped",
    "failed",
  ]);
  if (!states.has(String(runtime.state))) {
    throw new TypeError("live app state is malformed");
  }
  if (
    !Number.isSafeInteger(runtime.generation) ||
    Number(runtime.generation) < 1
  ) {
    throw new TypeError("live app generation is malformed");
  }
  if (!Array.isArray(runtime.actions)) {
    throw new TypeError("live app actions are malformed");
  }
  const actions = runtime.actions.map((item) => {
    const action = responseRecord(item, "live app action");
    if (
      !["start", "retry", "restart", "stop"].includes(String(action.operation))
    ) {
      throw new TypeError("live app action operation is malformed");
    }
    return Object.freeze({
      operation: action.operation as LiveAppOperation,
      label: responseString(action.label, "live app action label"),
    });
  });
  return Object.freeze({
    surfaceId: responseString(runtime.surfaceId, "live app surfaceId"),
    instanceId: responseString(runtime.instanceId, "live app instanceId"),
    generation: Number(runtime.generation),
    state: runtime.state as SurfaceDescriptor["lifecycle"],
    sharing: responseString(runtime.sharing, "live app sharing"),
    ownership: responseString(runtime.ownership, "live app ownership"),
    platform:
      runtime.platform === null
        ? null
        : responseString(runtime.platform, "live app platform"),
    lifetimePolicy: responseString(
      runtime.lifetimePolicy,
      "live app lifetimePolicy",
    ),
    failure: runtime.failure as LiveAppRuntime["failure"],
    actions,
  });
}

function headers(workspaceId: string, sessionId: string): HeadersInit {
  return {
    "X-Wright-Workspace-ID": workspaceId,
    "X-Wright-Session-ID": sessionId,
  };
}

async function checked(response: Response): Promise<unknown> {
  if (!response.ok) {
    throw new Error(
      `Workspace Surface request failed with HTTP ${response.status}`,
    );
  }
  return response.json();
}

const base = () => `${hostAdapter.getApiBaseUrl()}/api/workspace/surfaces`;

export async function declareLiveApp(
  manifest: Record<string, unknown>,
  workspaceId: string,
  sessionId: string,
): Promise<SurfaceDescriptor> {
  return parseSurfaceDescriptor(await checked(await hostAdapter.fetch(base(), {
    method: "POST",
    headers: { ...headers(workspaceId, sessionId), "Content-Type": "application/json", "Idempotency-Key": `rivet-editor-${crypto.randomUUID()}` },
    body: JSON.stringify({ schemaVersion: 1, kind: "live_app", manifest }),
  })));
}

export async function listSurfaces(
  workspaceId: string,
  sessionId: string,
): Promise<SurfaceDescriptor[]> {
  const value = (await checked(
    await hostAdapter.fetch(base(), {
      headers: headers(workspaceId, sessionId),
    }),
  )) as { items?: unknown[] };
  if (!Array.isArray(value.items))
    throw new TypeError("surface list is malformed");
  return value.items.map(parseSurfaceDescriptor);
}

export async function getDisplayProjection(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
  surfaceRevision?: number,
): Promise<DisplayProjection> {
  const revisionQuery = surfaceRevision
    ? `?surfaceRevision=${encodeURIComponent(surfaceRevision)}`
    : "";
  return (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/display${revisionQuery}`,
      { headers: headers(workspaceId, sessionId) },
    ),
  )) as DisplayProjection;
}

export async function getDisplayHistory(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<DisplayHistoryItem[]> {
  const value = (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/history`,
      {
        headers: headers(workspaceId, sessionId),
      },
    ),
  )) as { items?: DisplayHistoryItem[] };
  if (!Array.isArray(value.items))
    throw new TypeError("display history is malformed");
  return value.items;
}

export async function getDisplayVerification(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<Record<string, unknown>> {
  return (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/verification`,
      { headers: headers(workspaceId, sessionId) },
    ),
  )) as Record<string, unknown>;
}

export async function deleteDisplay(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<{
  deleted: boolean;
  recoverable: boolean;
  retentionStatus: string;
}> {
  return (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/display?retentionDisclosureConfirmed=true`,
      { method: "DELETE", headers: headers(workspaceId, sessionId) },
    ),
  )) as { deleted: boolean; recoverable: boolean; retentionStatus: string };
}

export async function createPresentation(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
  kind: "panel" | "browser",
  options: {
    readonly rememberPreference?: boolean;
    readonly isolatedAcknowledged?: boolean;
    readonly idempotencyKey?: string;
  } = {},
): Promise<PresentationLaunch> {
  const idempotencyKey =
    options.idempotencyKey ??
    `presentation-${surfaceId}-${kind}-${crypto.randomUUID()}`;
  return parsePresentationLaunch(
    await checked(
      await hostAdapter.fetch(
        `${base()}/${encodeURIComponent(surfaceId)}/presentations`,
        {
          method: "POST",
          headers: {
            ...headers(workspaceId, sessionId),
            "Content-Type": "application/json",
            "Idempotency-Key": idempotencyKey,
          },
          body: JSON.stringify({
            kind,
            rememberPreference: options.rememberPreference ?? false,
            isolatedAcknowledged: options.isolatedAcknowledged ?? false,
          }),
        },
      ),
    ),
    kind,
  );
}

export async function closePresentation(
  surfaceId: string,
  presentationId: string,
  workspaceId: string,
  sessionId: string,
): Promise<void> {
  const response = await hostAdapter.fetch(
    `${base()}/${encodeURIComponent(surfaceId)}/presentations/${encodeURIComponent(presentationId)}`,
    { method: "DELETE", headers: headers(workspaceId, sessionId) },
  );
  if (!response.ok) {
    throw new Error(
      `Workspace Surface presentation close failed with HTTP ${response.status}`,
    );
  }
}

export async function getPresentationPreference(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<PresentationPreference> {
  return parsePresentationPreference(
    await checked(
      await hostAdapter.fetch(
        `${base()}/${encodeURIComponent(surfaceId)}/presentation-preference`,
        { headers: headers(workspaceId, sessionId) },
      ),
    ),
  );
}

export async function operateLiveApp(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
  operation: LiveAppOperation,
): Promise<LiveAppRuntime> {
  return parseLiveAppRuntime(
    await checked(
      await hostAdapter.fetch(
        `${base()}/${encodeURIComponent(surfaceId)}/${operation}`,
        {
          method: "POST",
          headers: {
            ...headers(workspaceId, sessionId),
            "Idempotency-Key": `live-app-${operation}-${surfaceId}-${crypto.randomUUID()}`,
          },
        },
      ),
    ),
  );
}

export async function getLiveApp(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<LiveAppRuntime> {
  return parseLiveAppRuntime(
    await checked(
      await hostAdapter.fetch(
        `${base()}/${encodeURIComponent(surfaceId)}/live-app`,
        { headers: headers(workspaceId, sessionId) },
      ),
    ),
  );
}

export async function getLiveAppHealth(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<LiveAppHealth> {
  return (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/live-app/health`,
      { headers: headers(workspaceId, sessionId) },
    ),
  )) as LiveAppHealth;
}

export async function getLiveAppLogs(
  surfaceId: string,
  workspaceId: string,
  sessionId: string,
): Promise<LiveAppLogs> {
  return (await checked(
    await hostAdapter.fetch(
      `${base()}/${encodeURIComponent(surfaceId)}/live-app/logs?limit=100`,
      { headers: headers(workspaceId, sessionId) },
    ),
  )) as LiveAppLogs;
}
