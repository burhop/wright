import type {
  ChatSession,
  ChatSessionCompact,
  ChatMessage,
} from "../store/types";
import { logger } from "./logger";

const agentLogger = logger.child("HermesAgentService");

export type AgentEvent =
  | { type: "token"; text: string }
  | { type: "tool"; name: string; preview: string; percentage?: number }
  | { type: "progress"; percentage: number; message: string }
  | { type: "done"; session: ChatSession }
  | { type: "error"; message: string };

interface ServiceHealthResult {
  state: "connected" | "disconnected" | "unknown";
  latencyMs?: number;
}

export interface AgentCommand {
  name: string;
  description: string;
  prefix: string;
}

export interface VaultFile {
  file_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  url: string;
}

const getApiBase = () => {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }
  const host = window.location.hostname;
  const port = window.location.port;
  if (port === "5173" || port === "5174") {
    return `http://${host}:8000`;
  }
  return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
};
const API_BASE = getApiBase();

export class HermesAgentService {
  async checkHealth(): Promise<ServiceHealthResult> {
    try {
      const response = await fetch(`${API_BASE}/api/agent/health`);
      if (response.ok) {
        const data = await response.json();
        return {
          state: data.state as "connected" | "disconnected",
          latencyMs: data.latencyMs,
        };
      }
    } catch (err) {
      console.error("Agent health check failed", err);
    }
    return { state: "disconnected", latencyMs: 0 };
  }

  async createSession(workspace?: string): Promise<ChatSession> {
    agentLogger.info("Creating session", { workspace });
    const response = await fetch(`${API_BASE}/api/agent/sessions/new`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ workspace }),
    });

    if (!response.ok) {
      agentLogger.error("Failed to create session", {
        statusText: response.statusText,
        status: response.status,
      });
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      sessionId: data.session_id,
      title: data.title,
      messages: [],
      createdAt: data.created_at,
      updatedAt: data.created_at,
      isActive: true,
    };
  }

  async listSessions(): Promise<ChatSessionCompact[]> {
    const response = await fetch(`${API_BASE}/api/agent/sessions`);
    if (!response.ok) {
      throw new Error(`Failed to list sessions: ${response.statusText}`);
    }

    const data = await response.json();
    return data.sessions.map((s: any) => ({
      sessionId: s.session_id,
      title: s.title,
      createdAt: s.created_at,
      updatedAt: s.updated_at,
    }));
  }

  async deleteSession(sessionId: string): Promise<void> {
    agentLogger.info("Deleting session", { sessionId });
    const response = await fetch(
      `${API_BASE}/api/agent/sessions/${sessionId}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      agentLogger.error("Failed to delete session", {
        sessionId,
        statusText: response.statusText,
      });
      throw new Error(`Failed to delete session: ${response.statusText}`);
    }
    agentLogger.info("Session deleted successfully", { sessionId });
  }

  async *sendMessage(
    sessionId: string,
    message: string,
    attachments?: string[],
  ): AsyncIterable<AgentEvent> {
    agentLogger.info("Sending message", {
      sessionId,
      messageLength: message.length,
      attachmentsCount: attachments?.length || 0,
    });
    // 1. Initiate chat start
    const response = await fetch(`${API_BASE}/api/agent/chat/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId, message, attachments }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      agentLogger.error("Failed to initiate chat", {
        sessionId,
        error: errData.detail,
      });
      yield {
        type: "error",
        message: errData.detail || "Hermes agent is not available.",
      };
      return;
    }

    const { stream_id } = await response.json();
    agentLogger.info("Chat stream started", { sessionId, streamId: stream_id });

    // 2. Consume SSE stream via browser Native EventSource
    const eventQueue: AgentEvent[] = [];
    let isDone = false;
    let resolveQueue: (() => void) | null = null;

    const eventSource = new EventSource(
      `${API_BASE}/api/agent/chat/stream?stream_id=${stream_id}`,
    );

    const pushEvent = (evt: AgentEvent) => {
      eventQueue.push(evt);
      if (resolveQueue) {
        resolveQueue();
        resolveQueue = null;
      }
    };

    eventSource.addEventListener("token", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        agentLogger.debug("Stream token received", {
          sessionId,
          tokenLength: data.text?.length,
        });
        pushEvent({ type: "token", text: data.text });
      } catch (err) {
        agentLogger.debug("Stream token received (raw)", {
          sessionId,
          tokenLength: e.data?.length,
        });
        pushEvent({ type: "token", text: e.data });
      }
    });

    eventSource.addEventListener("tool", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        agentLogger.info("Stream tool invoke received", {
          sessionId,
          toolName: data.name,
          preview: data.preview,
        });
        pushEvent({
          type: "tool",
          name: data.name,
          preview: data.preview || "",
          percentage: data.percentage,
        });
      } catch (err) {
        // ignore
      }
    });

    eventSource.addEventListener("progress", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        agentLogger.info("Stream tool progress received", {
          sessionId,
          percentage: data.percentage,
          message: data.message,
        });
        pushEvent({
          type: "progress",
          percentage: data.percentage,
          message: data.message || "",
        });
      } catch (err) {
        // ignore
      }
    });

    eventSource.addEventListener("stream_end", (_e: MessageEvent) => {
      agentLogger.info("Stream completed", { sessionId });
      eventSource.close();
      pushEvent({
        type: "done",
        session: {
          sessionId,
          title: "", // filled dynamically in reducer
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          isActive: true,
        },
      });
      isDone = true;
      if (resolveQueue) {
        resolveQueue();
      }
    });

    eventSource.addEventListener("error", (e: any) => {
      const errMsg = e.data
        ? typeof e.data === "string"
          ? e.data
          : JSON.stringify(e.data)
        : "Hermes response stream failed.";
      agentLogger.error("Stream error encountered", {
        sessionId,
        error: errMsg,
      });
      eventSource.close();
      pushEvent({
        type: "error",
        message: e.data
          ? JSON.parse(e.data).message
          : "Hermes response stream failed.",
      });
      isDone = true;
      if (resolveQueue) {
        resolveQueue();
      }
    });

    while (!isDone || eventQueue.length > 0) {
      if (eventQueue.length === 0) {
        await new Promise<void>((resolve) => {
          resolveQueue = resolve;
        });
      }
      while (eventQueue.length > 0) {
        const evt = eventQueue.shift();
        if (evt) {
          yield evt;
        }
      }
    }
  }

  async getActiveAgent(): Promise<string> {
    const response = await fetch(`${API_BASE}/api/agent/active`);
    if (!response.ok) {
      throw new Error(`Failed to get active agent: ${response.statusText}`);
    }
    const data = await response.json();
    return data.agent;
  }

  async setActiveAgent(
    agentName: string,
    sessionId?: string | null,
  ): Promise<string> {
    const url = sessionId
      ? `${API_BASE}/api/agent/active?session_id=${sessionId}`
      : `${API_BASE}/api/agent/active`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ agent: agentName }),
    });
    if (!response.ok) {
      throw new Error(`Failed to set active agent: ${response.statusText}`);
    }
    const data = await response.json();
    return data.agent;
  }

  async saveContext(
    workspaceId: string,
    contextData: Record<string, unknown>,
  ): Promise<boolean> {
    agentLogger.info("Saving workspace context", { workspaceId });
    const response = await fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/context/save`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context_data: contextData }),
      },
    );
    if (!response.ok) {
      agentLogger.warn("Failed to save context", { status: response.status });
      return false;
    }
    return true;
  }

  async loadContext(
    workspaceId: string,
  ): Promise<Record<string, unknown> | null> {
    agentLogger.info("Loading workspace context", { workspaceId });
    const response = await fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/context/load`,
    );
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      agentLogger.warn("Failed to load context", { status: response.status });
      return null;
    }
    const data = await response.json();
    return data.context_data ?? null;
  }

  async getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
    agentLogger.info("Fetching session history", { sessionId });
    const response = await fetch(
      `${API_BASE}/api/agent/sessions/${sessionId}/history`,
    );
    if (!response.ok) {
      agentLogger.error("Failed to fetch session history", {
        sessionId,
        statusText: response.statusText,
      });
      throw new Error(
        `Failed to fetch session history: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.messages.map((m: any) => ({
      id: m.id,
      role: m.role as "user" | "assistant",
      content: m.content,
      timestamp: m.timestamp,
      traceId: m.trace_id ?? null,
    }));
  }

  async getCommands(): Promise<AgentCommand[]> {
    agentLogger.info("Fetching commands");
    const response = await fetch(`${API_BASE}/api/agent/commands`);
    if (!response.ok) {
      agentLogger.error("Failed to fetch commands", {
        statusText: response.statusText,
      });
      throw new Error(`Failed to fetch commands: ${response.statusText}`);
    }
    const data = await response.json();
    return data.commands;
  }

  async uploadFile(file: File): Promise<VaultFile> {
    agentLogger.info("Uploading file", { name: file.name, size: file.size });
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/vault/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      agentLogger.error("Failed to upload file", {
        statusText: response.statusText,
      });
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }
    return await response.json();
  }
}

export const agentService = new HermesAgentService();
export default agentService;
