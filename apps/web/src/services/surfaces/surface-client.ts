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

function responseRecord(value: unknown, label: string): Record<string, unknown> {
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
  if (!Number.isSafeInteger(launch.generation) || Number(launch.generation) < 1) {
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
    throw new TypeError("presentation preference remembered state is malformed");
  }
  return Object.freeze({
    kind: preference.kind,
    remembered: preference.remembered,
    reason: responseString(preference.reason, "presentation preference reason"),
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
    throw new Error(`Workspace Surface request failed with HTTP ${response.status}`);
  }
  return response.json();
}

const base = () => `${hostAdapter.getApiBaseUrl()}/api/workspace/surfaces`;

export async function listSurfaces(
  workspaceId: string,
  sessionId: string,
): Promise<SurfaceDescriptor[]> {
  const value = (await checked(
    await hostAdapter.fetch(base(), { headers: headers(workspaceId, sessionId) }),
  )) as { items?: unknown[] };
  if (!Array.isArray(value.items)) throw new TypeError("surface list is malformed");
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
    await hostAdapter.fetch(`${base()}/${encodeURIComponent(surfaceId)}/history`, {
      headers: headers(workspaceId, sessionId),
    }),
  )) as { items?: DisplayHistoryItem[] };
  if (!Array.isArray(value.items)) throw new TypeError("display history is malformed");
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
): Promise<{ deleted: boolean; recoverable: boolean; retentionStatus: string }> {
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
