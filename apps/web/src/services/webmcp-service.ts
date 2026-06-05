import { logger } from "./logger";

const webMcpLogger = logger.child("WebMcpService");

export class WebMcpService {
  private socket: WebSocket | null = null;
  private get wsUrl() {
    if (typeof window === "undefined") {
      return "ws://127.0.0.1:8000/api/webmcp/ws";
    }
    const host = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    if (port === "5173" || port === "5174") {
      return `${protocol}//${host}:8000/api/webmcp/ws`;
    }
    return `${protocol}//${host}${port ? `:${port}` : ""}/api/webmcp/ws`;
  }
  private reconnectTimer: any = null;

  constructor() {
    // Listen for response dispatches from browser viewport components
    window.addEventListener("webmcp:response", (e: Event) => {
      const customEvent = e as CustomEvent;
      const { callId, result, error } = customEvent.detail || {};

      if (!callId) return;

      webMcpLogger.info("Received local response event, sending to agent", {
        callId,
      });

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(
          JSON.stringify({
            jsonrpc: "2.0",
            id: callId,
            result,
            error,
          }),
        );
      } else {
        webMcpLogger.warn("WebSocket not open, cannot send response", {
          callId,
        });
      }
    });
  }

  connect() {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.CONNECTING ||
        this.socket.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    webMcpLogger.info("Connecting to WebMCP host socket", { url: this.wsUrl });
    try {
      this.socket = new WebSocket(this.wsUrl);

      this.socket.onopen = () => {
        webMcpLogger.info("WebMCP host socket connected");
        if (this.reconnectTimer) {
          clearInterval(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const { id: callId, method, params } = payload;

          if (callId && method) {
            webMcpLogger.info("Forwarding WebMCP request event to window", {
              callId,
              method,
            });
            window.dispatchEvent(
              new CustomEvent("webmcp:request", {
                detail: { callId, method, params },
              }),
            );
          }
        } catch (err) {
          webMcpLogger.error("Failed to parse WebMCP message", {
            data: event.data,
          });
        }
      };

      this.socket.onclose = () => {
        webMcpLogger.warn(
          "WebMCP host socket closed. Attempting reconnect in 5 seconds.",
        );
        this.socket = null;
        this.startReconnect();
      };

      this.socket.onerror = (err) => {
        webMcpLogger.error("WebMCP socket error occurred", { err });
      };
    } catch (e) {
      webMcpLogger.error("Failed to instantiate WebSocket", { error: e });
      this.startReconnect();
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearInterval(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  private startReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setInterval(() => {
        this.connect();
      }, 5000);
    }
  }
}

export const webMcpService = new WebMcpService();
export default webMcpService;
