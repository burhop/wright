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
