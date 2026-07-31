import type { FileEntry, SelectOptions } from "./wright-desktop";

export interface SurfaceHostCapabilities {
  readonly absolutePreviewUrls: true;
  readonly externalOpen: boolean;
}

export interface ExternalOpenOptions {
  readonly approvedDirectUrl?: boolean;
}

export class SurfaceHostAdapterError extends Error {
  readonly code:
    | "SURFACE_HOST_URL_REJECTED"
    | "SURFACE_HOST_EXTERNAL_OPEN_FAILED"
    | "SURFACE_HOST_EXTERNAL_OPEN_UNAVAILABLE";

  constructor(
    code:
      | "SURFACE_HOST_URL_REJECTED"
      | "SURFACE_HOST_EXTERNAL_OPEN_FAILED"
      | "SURFACE_HOST_EXTERNAL_OPEN_UNAVAILABLE",
    message: string,
  ) {
    super(message);
    this.name = "SurfaceHostAdapterError";
    this.code = code;
  }
}

function absoluteHttpUrl(value: string): URL {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new SurfaceHostAdapterError(
      "SURFACE_HOST_URL_REJECTED",
      "Surface URL must be absolute.",
    );
  }
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username !== "" ||
    url.password !== ""
  ) {
    throw new SurfaceHostAdapterError(
      "SURFACE_HOST_URL_REJECTED",
      "Surface URL must use HTTP(S) without credentials.",
    );
  }
  return url;
}

export function validateIssuedSurfacePreviewUrl(
  value: string,
  controlOrigin?: string,
): string {
  const url = absoluteHttpUrl(value);
  if (
    url.pathname !== "/__wright/bootstrap" ||
    url.search !== "" ||
    url.hash.slice(1).length < 32 ||
    (controlOrigin !== undefined && url.origin === controlOrigin)
  ) {
    throw new SurfaceHostAdapterError(
      "SURFACE_HOST_URL_REJECTED",
      "Surface preview URL is not a distinct issued bootstrap URL.",
    );
  }
  return url.toString();
}

export function validateApprovedDirectSurfaceUrl(value: string): string {
  return absoluteHttpUrl(value).toString();
}

export interface HostAdapter {
  readonly mode: "browser" | "desktop";
  readonly surfaceCapabilities: SurfaceHostCapabilities;
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;
  listDirectory(path: string): Promise<FileEntry[]>;
  selectFiles(options?: SelectOptions): Promise<string[]>;
  getApiBaseUrl(): string;
  resolveBackendUrl(path: string): string;
  validateIssuedPreviewUrl(value: string): string;
  openExternal(value: string, options?: ExternalOpenOptions): Promise<void>;
  getRouterType(): "browser" | "hash";
  notify(title: string, body: string): Promise<boolean>;
  hasTerminal(): boolean;
  dispose(): void;
}
