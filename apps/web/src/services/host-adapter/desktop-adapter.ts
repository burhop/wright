import type { HostAdapter } from "./host-adapter";
import type { FileEntry, SelectOptions } from "./wright-desktop";

export class DesktopHostAdapter implements HostAdapter {
  readonly mode = "desktop";
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
        headers: init?.headers as Record<string, string>,
      });

      return {
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => result,
        text: async () =>
          typeof result === "string" ? result : JSON.stringify(result),
        arrayBuffer: async () =>
          new TextEncoder().encode(
            typeof result === "string" ? result : JSON.stringify(result),
          ).buffer,
      } as Response;
    } catch (err: any) {
      const statusCode = err.status || 500;
      const statusText = err.message || "Internal Server Error";
      return {
        ok: false,
        status: statusCode,
        statusText: statusText,
        json: async () => ({
          error_code: err.code || "API_ERROR",
          message: err.message || "API request failed",
          trace_id: "unknown",
          details: err.details,
        }),
        text: async () => JSON.stringify(err),
      } as Response;
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
