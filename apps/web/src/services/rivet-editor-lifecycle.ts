import { workspaceService } from "./workspace-service";
import type { SurfaceDescriptor } from "./surfaces/surface-contract";
import {
  declareLiveApp,
  listSurfaces,
  operateLiveApp,
  type LiveAppOperation,
} from "./surfaces/surface-client";

const startupRequests = new Map<string, Promise<string>>();
const RIVET_SOURCE_ID = "wright.rivet-editor";

function recoveryOperation(
  lifecycle: SurfaceDescriptor["lifecycle"],
): LiveAppOperation | null {
  if (lifecycle === "declared") return "start";
  if (lifecycle === "stopped") return "restart";
  if (lifecycle === "failed") return "retry";
  return null;
}

function matchingRivetSurface(
  descriptors: readonly SurfaceDescriptor[],
  surfaceId: string,
): SurfaceDescriptor | null {
  return (
    descriptors.find(
      (descriptor) =>
        descriptor.surfaceId === surfaceId &&
        descriptor.source.kind === "live_app" &&
        descriptor.source.sourceId === RIVET_SOURCE_ID,
    ) ?? null
  );
}

async function waitForRunnableSurface(
  workspaceId: string,
  sessionId: string,
  surfaceId: string,
): Promise<SurfaceDescriptor> {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    const descriptor = matchingRivetSurface(
      await listSurfaces(workspaceId, sessionId),
      surfaceId,
    );
    if (!descriptor) {
      throw new Error("The managed Rivet editor surface disappeared.");
    }
    if (
      descriptor.lifecycle !== "starting" &&
      descriptor.lifecycle !== "stopping"
    ) {
      return descriptor;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 100));
  }
  throw new Error("The managed Rivet editor did not become ready in time.");
}

async function startRivetEditor(
  workspaceId: string,
  sessionId: string,
): Promise<string> {
  const surface = await workspaceService.getRivetEditorSurface(sessionId);
  if (!surface.manifest) {
    throw new Error(surface.detail || "Rivet editor is unavailable.");
  }

  let descriptor = await declareLiveApp(
    surface.manifest,
    workspaceId,
    sessionId,
  );

  for (let attempt = 0; attempt < 3; attempt += 1) {
    if (
      descriptor.lifecycle === "ready" ||
      descriptor.lifecycle === "unhealthy"
    ) {
      window.dispatchEvent(new Event("wright-surfaces-changed"));
      return descriptor.surfaceId;
    }

    if (
      descriptor.lifecycle === "starting" ||
      descriptor.lifecycle === "stopping"
    ) {
      descriptor = await waitForRunnableSurface(
        workspaceId,
        sessionId,
        descriptor.surfaceId,
      );
      continue;
    }

    const operation = recoveryOperation(descriptor.lifecycle);
    if (!operation) {
      throw new Error(
        `Rivet editor cannot start from ${descriptor.lifecycle}.`,
      );
    }

    try {
      const runtime = await operateLiveApp(
        descriptor.surfaceId,
        workspaceId,
        sessionId,
        operation,
      );
      if (runtime.state === "ready" || runtime.state === "unhealthy") {
        window.dispatchEvent(new Event("wright-surfaces-changed"));
        return descriptor.surfaceId;
      }
    } catch (error) {
      // Another Wright window may have won the same idempotent start. Re-read
      // the authoritative descriptor before deciding that startup failed.
      descriptor = await waitForRunnableSurface(
        workspaceId,
        sessionId,
        descriptor.surfaceId,
      );
      if (
        descriptor.lifecycle === "ready" ||
        descriptor.lifecycle === "unhealthy"
      ) {
        window.dispatchEvent(new Event("wright-surfaces-changed"));
        return descriptor.surfaceId;
      }
      if (attempt === 2) throw error;
      continue;
    }

    descriptor = await waitForRunnableSurface(
      workspaceId,
      sessionId,
      descriptor.surfaceId,
    );
  }

  throw new Error("The managed Rivet editor did not start.");
}

export function ensureRivetEditorRunning(
  workspaceId: string,
  sessionId: string,
): Promise<string> {
  const key = `${workspaceId}:${sessionId}`;
  const existing = startupRequests.get(key);
  if (existing) return existing;

  const request = startRivetEditor(workspaceId, sessionId).finally(() => {
    if (startupRequests.get(key) === request) startupRequests.delete(key);
  });
  startupRequests.set(key, request);
  return request;
}
