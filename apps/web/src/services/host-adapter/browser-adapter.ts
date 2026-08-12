import {
  SurfaceHostAdapterError,
  validateApprovedDirectSurfaceUrl,
  validateIssuedSurfacePreviewUrl,
  type ExternalOpenOptions,
  type HostAdapter,
} from "./host-adapter";
import type { FileEntry, SelectOptions } from "./wright-desktop";
import { createBrowserSession, readStoredAccessToken } from "../auth-session";

export { SurfaceHostAdapterError } from "./host-adapter";

interface BrowserHostAdapterOptions {
  readonly controlUrl?: string;
  readonly openWindow?: (
    url: string,
    target: string,
    features: string,
  ) => Window | null;
}

function devSurfaceProxyUrl(value: string, control: URL): string {
  const preview = new URL(value);
  if (!["5173", "5174"].includes(control.port)) return value;
  if (preview.origin === control.origin) return value;
  const path = `/__wright-surface/${encodeURIComponent(preview.host)}${preview.pathname}${preview.search}${preview.hash}`;
  const proxyOrigin = `${control.protocol}//${preview.hostname}:${control.port}`;
  return new URL(path, proxyOrigin).toString();
}

function existingDevSurfaceProxyUrl(
  value: string,
  control: URL,
): { readonly proxyUrl: string; readonly issuedUrl: string } | null {
  if (!["5173", "5174"].includes(control.port)) return null;
  const proxy = new URL(value);
  if (
    proxy.protocol !== control.protocol ||
    proxy.port !== control.port ||
    proxy.search !== ""
  )
    return null;
  const match = proxy.pathname.match(
    /^\/__wright-surface\/([^/]+)\/__wright\/bootstrap$/,
  );
  if (!match) return null;
  const upstreamHost = decodeURIComponent(match[1]);
  const issuedUrl = validateIssuedSurfacePreviewUrl(
    `${control.protocol}//${upstreamHost}/__wright/bootstrap${proxy.hash}`,
    control.origin,
  );
  const issued = new URL(issuedUrl);
  if (proxy.origin !== control.origin && proxy.hostname !== issued.hostname)
    return null;
  return { proxyUrl: devSurfaceProxyUrl(issuedUrl, control), issuedUrl };
}

export class BrowserHostAdapter implements HostAdapter {
  readonly mode = "browser";
  readonly surfaceCapabilities = {
    absolutePreviewUrls: true,
    externalOpen: true,
  } as const;
  private readonly configuredControlUrl?: string;
  private readonly configuredOpenWindow?: BrowserHostAdapterOptions["openWindow"];

  constructor(options: BrowserHostAdapterOptions = {}) {
    this.configuredControlUrl = options.controlUrl;
    this.configuredOpenWindow = options.openWindow;
  }

  private controlUrl(): URL {
    if (this.configuredControlUrl) return new URL(this.configuredControlUrl);
    if (typeof window === "undefined") return new URL("http://127.0.0.1:8000/");
    const location = window.location;
    if (typeof location.href === "string" && location.href) {
      return new URL(location.href);
    }
    const port = location.port ? `:${location.port}` : "";
    return new URL(`${location.protocol}//${location.hostname}${port}/`);
  }

  getApiBaseUrl(): string {
    const control = this.controlUrl();
    const host = control.hostname;
    const port = control.port;
    if (port === "5173" || port === "5174") {
      return "";
    }
    return `${control.protocol}//${host}${port ? `:${port}` : ""}`;
  }

  resolveBackendUrl(path: string): string {
    if (!path.startsWith("/")) {
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_URL_REJECTED",
        "Backend path must be absolute.",
      );
    }
    return new URL(path, this.controlUrl().origin).toString();
  }

  validateIssuedPreviewUrl(value: string): string {
    const control = this.controlUrl();
    const existingProxy = existingDevSurfaceProxyUrl(value, control);
    if (existingProxy) return existingProxy.proxyUrl;
    const validated = validateIssuedSurfacePreviewUrl(value, control.origin);
    return devSurfaceProxyUrl(validated, control);
  }

  async openExternal(
    value: string,
    options: ExternalOpenOptions = {},
  ): Promise<void> {
    const control = this.controlUrl();
    const existingProxy = existingDevSurfaceProxyUrl(value, control);
    const validated = options.approvedDirectUrl
      ? validateApprovedDirectSurfaceUrl(value)
      : (existingProxy?.issuedUrl ??
        validateIssuedSurfacePreviewUrl(value, control.origin));
    const openWindow =
      this.configuredOpenWindow ??
      ((url: string, target: string, features: string) =>
        window.open(url, target, features));
    // Browsers may return null for a successful `window.open` when the
    // `noopener` feature is used, making that indistinguishable from a popup
    // blocker. Open a same-origin blank window first, sever its opener before
    // any remote content loads, install a no-referrer policy, then navigate.
    const opened = openWindow("about:blank", "_blank", "popup");
    if (!opened) {
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_EXTERNAL_OPEN_FAILED",
        "The system browser refused to open the surface.",
      );
    }
    try {
      opened.opener = null;
      const referrerPolicy = opened.document.createElement("meta");
      referrerPolicy.name = "referrer";
      referrerPolicy.content = "no-referrer";
      opened.document.head.append(referrerPolicy);
      opened.location.replace(validated);
    } catch {
      opened.close();
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_EXTERNAL_OPEN_FAILED",
        "The system browser could not navigate to the surface.",
      );
    }
  }

  getRouterType(): "browser" | "hash" {
    return "browser";
  }

  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const requestInit: RequestInit = {
      ...init,
      credentials: init?.credentials ?? "same-origin",
    };
    const response = await fetch(input, requestInit);
    if (response.status !== 401 || this.isAuthSessionRequest(input)) {
      return response;
    }

    const token = readStoredAccessToken();
    if (!token) return response;

    try {
      await createBrowserSession(token);
    } catch {
      return response;
    }
    return fetch(input, requestInit);
  }

  private isAuthSessionRequest(input: RequestInfo | URL): boolean {
    const value =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : "url" in input
            ? input.url
            : "";
    return value.includes("/api/auth/session");
  }

  async readFile(
    path: string,
    options?: { sessionId?: string },
  ): Promise<string> {
    const sessionId = options?.sessionId || "";
    const url = `${this.getApiBaseUrl()}/api/workspace/files/content?session_id=${sessionId}&path=${encodeURIComponent(path)}`;
    const response = await this.fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to read file: ${response.statusText}`);
    }
    return response.text();
  }

  async writeFile(
    path: string,
    content: string,
    options?: { sessionId?: string },
  ): Promise<void> {
    const sessionId = options?.sessionId || "";
    const url = `${this.getApiBaseUrl()}/api/workspace/files/content`;
    const response = await this.fetch(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        path,
        content,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to write file: ${response.statusText}`);
    }
  }

  async listDirectory(
    _path: string,
    _options?: { sessionId?: string },
  ): Promise<FileEntry[]> {
    throw new Error("listDirectory is not supported in browser mode");
  }

  async selectFiles(options?: SelectOptions): Promise<string[]> {
    return new Promise((resolve) => {
      if (typeof document === "undefined") {
        resolve([]);
        return;
      }
      const input = document.createElement("input");
      input.type = "file";
      if (options?.multiple) input.multiple = true;
      if (options?.directory) {
        input.setAttribute("webkitdirectory", "");
        input.setAttribute("directory", "");
      }
      if (options?.filters) {
        const accept = options.filters
          .flatMap((f) => f.extensions.map((ext) => `.${ext}`))
          .join(",");
        input.accept = accept;
      }

      input.onchange = () => {
        const files = Array.from(input.files || []);
        resolve(files.map((f) => (f as any).webkitRelativePath || f.name));
      };

      input.oncancel = () => {
        resolve([]);
      };

      input.click();
    });
  }

  async notify(title: string, body: string): Promise<boolean> {
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission === "granted") {
        new Notification(title, { body });
        return true;
      } else if (Notification.permission !== "denied") {
        const permission = await Notification.requestPermission();
        if (permission === "granted") {
          new Notification(title, { body });
          return true;
        }
      }
    }
    return false;
  }

  hasTerminal(): boolean {
    return false;
  }

  dispose(): void {}
}
