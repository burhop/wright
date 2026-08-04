import { hostAdapter } from "./host-adapter";

export function directRivetEditorUrl(): string | null {
  const configured = import.meta.env.VITE_RIVET_DIRECT_EDITOR_URL;
  if (typeof configured === "string" && configured.trim()) return configured;
  if (
    import.meta.env.DEV &&
    typeof window !== "undefined" &&
    ["5173", "5174"].includes(window.location.port)
  ) {
    return `${window.location.protocol}//${window.location.hostname}:9180/`;
  }
  return null;
}

export function directRivetWorkflowUrl(slug: string): string | null {
  const base = directRivetEditorUrl();
  if (!base) return null;
  const url = new URL(base);
  url.searchParams.set("wrightMinimal", "1");
  url.searchParams.set("workflow", slug);
  url.searchParams.set(
    "title",
    slug
      .split("-")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ") || "Rivet",
  );
  return url.toString();
}

export async function openDirectRivetEditor(): Promise<boolean> {
  const url = directRivetEditorUrl();
  if (!url) return false;
  await hostAdapter.openExternal(url, { approvedDirectUrl: true });
  return true;
}
