import type { HostAdapter } from "./host-adapter";
import type { FileEntry, SelectOptions } from "./wright-desktop";

export class BrowserHostAdapter implements HostAdapter {
  readonly mode = "browser";

  getApiBaseUrl(): string {
    if (typeof window === "undefined") return "http://127.0.0.1:8000";
    const host = window.location.hostname;
    const port = window.location.port;
    if (port === "5173" || port === "5174") {
      return "";
    }
    return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
  }

  getRouterType(): "browser" | "hash" {
    return "browser";
  }

  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    return fetch(input, init);
  }

  async readFile(
    path: string,
    options?: { sessionId?: string },
  ): Promise<string> {
    const sessionId = options?.sessionId || "";
    const url = `${this.getApiBaseUrl()}/api/workspace/files/content?session_id=${sessionId}&path=${encodeURIComponent(path)}`;
    const response = await fetch(url);
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
    const response = await fetch(url, {
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
