import {
  SurfaceHostAdapterError,
  validateApprovedDirectSurfaceUrl,
  validateIssuedSurfacePreviewUrl,
  type ExternalOpenOptions,
  type HostAdapter,
} from "./host-adapter";
import type {
  FileEntry,
  SelectOptions,
  WrightApiResponse,
} from "./wright-desktop";

function requestHeaders(
  headers: HeadersInit | undefined,
): Record<string, string> {
  return Object.fromEntries(new Headers(headers).entries());
}

function isMetadataResponse(value: unknown): value is WrightApiResponse {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    return false;
  const row = value as Record<string, unknown>;
  return (
    Number.isInteger(row.status) &&
    typeof row.statusText === "string" &&
    typeof row.headers === "object" &&
    row.headers !== null &&
    "body" in row
  );
}

function responseBody(value: unknown, headers: Headers): BodyInit | null {
  if (value === null || value === undefined) return null;
  const mediaType = headers.get("content-type")?.toLowerCase() ?? "";
  if (mediaType.includes("application/json")) return JSON.stringify(value);
  if (typeof value === "string") return value;
  if (!headers.has("content-type"))
    headers.set("content-type", "application/json");
  return JSON.stringify(value);
}

export class DesktopHostAdapter implements HostAdapter {
  readonly mode = "desktop";
  readonly surfaceCapabilities = {
    absolutePreviewUrls: true,
    externalOpen: true,
  } as const;
  private apiPort = 8000;
  private workspacePath: string | null = null;
  private configPromise: Promise<void>;

  constructor() {
    this.configPromise = this.initConfig();
  }

  private async initConfig() {
    if (typeof window !== "undefined" && window.wrightDesktop) {
      try {
        const config = await window.wrightDesktop.getConfig();
        this.apiPort = config.apiPort;
        this.workspacePath = config.workspacePath;
        console.debug(
          "[DesktopHostAdapter] Configured workspace path:",
          this.workspacePath,
        );
      } catch (e) {
        console.error("Failed to load desktop config", e);
      }
    }
  }

  getApiBaseUrl(): string {
    return `http://localhost:${this.apiPort}`;
  }

  resolveBackendUrl(path: string): string {
    if (!path.startsWith("/")) {
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_URL_REJECTED",
        "Backend path must be absolute.",
      );
    }
    return new URL(path, this.getApiBaseUrl()).toString();
  }

  validateIssuedPreviewUrl(value: string): string {
    return validateIssuedSurfacePreviewUrl(value);
  }

  async openExternal(
    value: string,
    options: ExternalOpenOptions = {},
  ): Promise<void> {
    if (typeof window === "undefined" || !window.wrightDesktop?.openExternal) {
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_EXTERNAL_OPEN_UNAVAILABLE",
        "Desktop external-open integration is unavailable.",
      );
    }
    const validated = options.approvedDirectUrl
      ? validateApprovedDirectSurfaceUrl(value)
      : this.validateIssuedPreviewUrl(value);
    const opened = await window.wrightDesktop.openExternal(validated, {
      approvedDirectUrl: options.approvedDirectUrl === true,
    });
    if (!opened) {
      throw new SurfaceHostAdapterError(
        "SURFACE_HOST_EXTERNAL_OPEN_FAILED",
        "The system browser refused to open the surface.",
      );
    }
  }

  getRouterType(): "browser" | "hash" {
    return "hash";
  }

  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      throw new Error("wrightDesktop bridge not found on window");
    }

    // Parse the URL to get the path
    let urlString = "";
    if (typeof input === "string") {
      urlString = input;
    } else if (input instanceof URL) {
      urlString = input.toString();
    } else if (input && typeof input === "object" && "url" in input) {
      urlString = (input as Request).url;
    }

    // Extract path starting with /api/
    let apiPath = urlString;
    try {
      if (urlString.startsWith("http://") || urlString.startsWith("https://")) {
        const parsedUrl = new URL(urlString);
        apiPath = parsedUrl.pathname + parsedUrl.search;
      } else if (urlString.startsWith("file://")) {
        const match = urlString.match(/file:\/\/[^\/]*(\/api\/.*)/);
        if (match) {
          apiPath = match[1];
        }
      }
    } catch (e) {
      // Fallback to urlString as is
    }

    // Ensure apiPort config is initialized if possible
    await this.configPromise.catch(() => {});

    const method = init?.method || "GET";
    let bodyObj: any = undefined;
    if (init?.body) {
      if (typeof init.body === "string") {
        try {
          bodyObj = JSON.parse(init.body);
        } catch (e) {
          bodyObj = init.body;
        }
      } else {
        bodyObj = init.body;
      }
    }

    try {
      const result = await window.wrightDesktop.api({
        path: apiPath,
        method,
        body: bodyObj,
        headers: requestHeaders(init?.headers),
        includeResponseMetadata: true,
      });
      if (!isMetadataResponse(result)) {
        throw new Error(
          "wrightDesktop bridge returned an invalid response envelope",
        );
      }
      const headers = new Headers(result.headers);
      return new Response(responseBody(result.body, headers), {
        status: result.status,
        statusText: result.statusText,
        headers,
      });
    } catch (err: any) {
      const statusCode = err.status || 500;
      const statusText = err.message || "Internal Server Error";
      return new Response(
        JSON.stringify({
          error_code: err.code || "API_ERROR",
          message: err.message || "API request failed",
          trace_id: "unknown",
          details: err.details,
        }),
        {
          status: statusCode,
          statusText,
          headers: { "content-type": "application/json" },
        },
      );
    }
  }

  async readFile(path: string): Promise<string> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      throw new Error("wrightDesktop bridge not found");
    }
    return window.wrightDesktop.readFile(path);
  }

  async writeFile(path: string, content: string): Promise<void> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      throw new Error("wrightDesktop bridge not found");
    }
    return window.wrightDesktop.writeFile(path, content);
  }

  async listDirectory(path: string): Promise<FileEntry[]> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      throw new Error("wrightDesktop bridge not found");
    }
    return window.wrightDesktop.listDirectory(path);
  }

  async selectFiles(options?: SelectOptions): Promise<string[]> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      throw new Error("wrightDesktop bridge not found");
    }
    return window.wrightDesktop.selectFiles(options);
  }

  async notify(title: string, body: string): Promise<boolean> {
    if (typeof window === "undefined" || !window.wrightDesktop) {
      return false;
    }
    return window.wrightDesktop.notify({ title, body });
  }

  hasTerminal(): boolean {
    return true;
  }

  dispose(): void {}
}
