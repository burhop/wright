import { hostAdapter } from "./host-adapter";

type RivetEditorLocation = Pick<Location, "hostname" | "protocol">;

// Change this with each pinned editor artifact so an already-open Wright
// workspace reloads its isolated Rivet iframe instead of retaining old code.
const RIVET_EDITOR_ARTIFACT_REVISION = "db4d86e7";

export function directRivetEditorUrl(
  environment: Record<string, unknown> = import.meta.env,
  location: RivetEditorLocation | null =
    typeof window !== "undefined" ? window.location : null,
): string | null {
  const configured = environment.VITE_RIVET_DIRECT_EDITOR_URL;
  if (typeof configured === "string" && configured.trim()) return configured;
  if (!location) return null;
  const hostname = location.hostname.toLowerCase();
  if (!["localhost", "127.0.0.1", "::1", "[::1]"].includes(hostname)) return null;
  return `${location.protocol}//${location.hostname}:9180/`;
}

export function directRivetCanvasFrameUrl(
  editorUrl: string,
  parentOrigin: string,
): string {
  const frameUrl = new URL(editorUrl);
  const trustedParent = new URL(parentOrigin).origin;
  frameUrl.searchParams.set("parentOrigin", trustedParent);
  frameUrl.searchParams.set("artifactRevision", RIVET_EDITOR_ARTIFACT_REVISION);
  return frameUrl.toString();
}

export function directRivetWorkflowUrl(slug: string): string | null {
  const base = directRivetEditorUrl();
  if (!base) return null;
  const url = new URL(base);
  url.searchParams.set("workflow", slug);
  return url.toString();
}

export async function openDirectRivetEditor(): Promise<boolean> {
  const url = directRivetEditorUrl();
  if (!url) return false;
  await hostAdapter.openExternal(url, { approvedDirectUrl: true });
  return true;
}
