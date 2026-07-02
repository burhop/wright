import { BrowserHostAdapter } from "./browser-adapter";
import { DesktopHostAdapter } from "./desktop-adapter";
import { isDesktop } from "./detect";
import type { HostAdapter } from "./host-adapter";

export type { HostAdapter };
export { isDesktop };

export const hostAdapter: HostAdapter = isDesktop()
  ? new DesktopHostAdapter()
  : new BrowserHostAdapter();

// Inject monkey patch for global fetch in desktop mode to route API calls via IPC
if (typeof window !== "undefined" && isDesktop()) {
  const originalFetch = window.fetch;
  if (!(window as any).__wright_fetch_patched) {
    (window as any).__wright_fetch_patched = true;
    (window as any)._originalFetch = originalFetch;

    window.fetch = async (
      input: RequestInfo | URL,
      init?: RequestInit,
    ): Promise<Response> => {
      let urlString = "";
      if (typeof input === "string") {
        urlString = input;
      } else if (input instanceof URL) {
        urlString = input.toString();
      } else if (input && typeof input === "object" && "url" in input) {
        urlString = (input as Request).url;
      }

      const isApi =
        urlString.includes("/api/") ||
        urlString.startsWith("/api/") ||
        urlString.includes("localhost:8000") ||
        urlString.includes("127.0.0.1:8000");

      if (isApi) {
        return hostAdapter.fetch(input, init);
      }

      return originalFetch(input, init);
    };
  }
}
