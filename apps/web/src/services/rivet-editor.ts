import { hostAdapter } from "./host-adapter";

// Change this with each pinned editor artifact so an already-open Wright
// workspace reloads its isolated Rivet iframe instead of retaining old code.
const RIVET_EDITOR_ARTIFACT_REVISION = "6b12fce1";

export function directRivetEditorUrl(
  environment: Record<string, unknown> = import.meta.env,
): string | null {
  const configured = environment.VITE_RIVET_DIRECT_EDITOR_URL;
  if (typeof configured === "string" && configured.trim()) return configured;
  return null;
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
