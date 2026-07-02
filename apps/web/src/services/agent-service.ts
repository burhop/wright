import type {
  ChatSession,
  ChatSessionCompact,
  ChatMessage,
} from "../store/types";
import { logger } from "./logger";
import { hostAdapter } from "./host-adapter";

const agentLogger = logger.child("HermesAgentService");

export type AgentEvent =
  | { type: "stream_start"; streamId: string }
  | { type: "token"; text: string }
  | { type: "tool"; name: string; preview: string; percentage?: number }
  | {
      type: "progress";
      percentage?: number;
      message: string;
      title: string;
      detail?: string;
    }
  | { type: "done"; session: ChatSession }
  | { type: "error"; message: string };

interface ServiceHealthResult {
  state: "connected" | "disconnected" | "unknown";
  latencyMs?: number;
  baseUrl?: string | null;
  error?: string | null;
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
    return "";
  }
  return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
};
const API_BASE = getApiBase();

function summarizeToolCallPayload(data: any): {
  name: string;
  preview: string;
} {
  const toolCalls = Array.isArray(data?.tool_calls) ? data.tool_calls : [];
  const firstCall = toolCalls[0] || {};
  const fn = firstCall.function || {};
  const name = data?.name || fn.name || firstCall.name || "Tool call";
  const rawPreview = data?.preview || fn.arguments || firstCall.arguments || "";
  const preview =
    typeof rawPreview === "string"
      ? rawPreview
      : JSON.stringify(rawPreview ?? "");

  return {
    name,
    preview: preview.length > 220 ? `${preview.slice(0, 217)}...` : preview,
  };
}

function formatProgressStatus(value: unknown): string {
  if (typeof value !== "string" || value.length === 0) return "";
  return value.replace(/[_-]+/g, " ").replace(/^./, (c) => c.toUpperCase());
}

function summarizeProgressPayload(data: any): {
  title: string;
  detail?: string;
  message: string;
  percentage?: number;
} {
  const tool = data?.tool || data?.tool_name || data?.name || data?.server;
  const status = data?.status || data?.state || data?.phase;
  const label = data?.label || data?.title || data?.step || data?.operation;
  const message = data?.message || data?.detail || data?.description || "";
  const percentage =
    typeof data?.percentage === "number"
      ? data.percentage
      : typeof data?.progress === "number"
        ? data.progress
        : undefined;

  const statusText = formatProgressStatus(status);
  let title = "Tool progress";
  if (tool && statusText) {
    title = `${tool}: ${statusText}`;
  } else if (tool) {
    title = `${tool}`;
  } else if (label) {
    title = `${label}`;
  } else if (statusText) {
    title = statusText;
  }

  const details = [label, message]
    .filter((part) => typeof part === "string" && part.trim().length > 0)
    .map((part) => String(part).trim());
  const uniqueDetails = Array.from(new Set(details));
  const detail = uniqueDetails.length > 0 ? uniqueDetails.join(" - ") : undefined;

  return {
    title,
    detail,
    message: detail || title,
    percentage,
  };
}

export class HermesAgentService {
  private activeStreams = new Map<
    string,
    { abortController: AbortController; abort: () => void }
  >();

  async checkHealth(): Promise<ServiceHealthResult> {
    try {
      const response = await fetch(`${API_BASE}/api/agent/health`);
      if (response.ok) {
        const data = await response.json();
        return {
          state: data.state as "connected" | "disconnected",
          latencyMs: data.latencyMs,
          baseUrl: data.baseUrl ?? null,
          error: data.error ?? null,
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

  async listSessions(workspaceId?: string): Promise<ChatSessionCompact[]> {
    const url = workspaceId
      ? `${API_BASE}/api/agent/sessions?workspace_id=${encodeURIComponent(workspaceId)}`
      : `${API_BASE}/api/agent/sessions`;
    const response = await fetch(url);
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

    const abortController = new AbortController();
    const abort = () => {
      abortController.abort();
    };
    this.activeStreams.set(sessionId, { abortController, abort });

    try {
      const response = await fetch(`${API_BASE}/api/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, message, attachments }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        agentLogger.error("Failed to initiate chat", {
          sessionId,
          error: errData.message || errData.detail,
        });
        yield {
          type: "error",
          message:
            errData.message || errData.detail || "Agent is not available.",
        };
        return;
      }

      if (!response.body) {
        yield { type: "error", message: "Response body is empty." };
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last partial line in the buffer
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.substring(6).trim();
          } else if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.substring(5).trim();
            if (currentEvent) {
              const eventYield = this.parseSSEEvent(
                currentEvent,
                dataStr,
                sessionId,
              );
              if (eventYield) {
                yield eventYield;
              }
              currentEvent = "";
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        yield { type: "error", message: "Stream cancelled by user." };
      } else {
        agentLogger.error("Stream error encountered", {
          sessionId,
          error: err.message || String(err),
        });
        yield {
          type: "error",
          message: err.message || "Agent response stream failed.",
        };
      }
    } finally {
      this.activeStreams.delete(sessionId);
    }
  }

  private parseSSEEvent(
    event: string,
    dataStr: string,
    sessionId: string,
  ): AgentEvent | null {
    if (event === "token") {
      try {
        const data = JSON.parse(dataStr);
        return { type: "token", text: data.text };
      } catch (err) {
        return { type: "token", text: dataStr };
      }
    } else if (event === "tool") {
      try {
        const data = JSON.parse(dataStr);
        const summary = summarizeToolCallPayload(data);
        return {
          type: "tool",
          name: summary.name,
          preview: summary.preview,
          percentage: data.percentage,
        };
      } catch (err) {
        return null;
      }
    } else if (event === "progress") {
      try {
        const data = JSON.parse(dataStr);
        const summary = summarizeProgressPayload(data);
        return {
          type: "progress",
          percentage: summary.percentage,
          message: summary.message,
          title: summary.title,
          detail: summary.detail,
        };
      } catch (err) {
        return null;
      }
    } else if (event === "stream_end") {
      hostAdapter.notify(
        "Agent Task Finished",
        "The agent has completed your request.",
      );
      return {
        type: "done",
        session: {
          sessionId,
          title: "",
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          isActive: true,
        },
      };
    } else if (event === "error") {
      try {
        const data = JSON.parse(dataStr);
        return {
          type: "error",
          message: data.message || "Agent response stream failed.",
        };
      } catch (err) {
        return {
          type: "error",
          message: dataStr || "Agent response stream failed.",
        };
      }
    }
    return null;
  }

  async cancelStream(sessionId: string, _streamId?: string): Promise<boolean> {
    const key = sessionId;
    const active = this.activeStreams.get(key);
    if (active) {
      active.abort();
      this.activeStreams.delete(key);
    }
    try {
      const response = await fetch(
        `${API_BASE}/api/agent/chat/cancel?session_id=${encodeURIComponent(sessionId)}`,
        {
          method: "POST",
        },
      );
      if (response.ok) {
        const data = await response.json();
        return data.success;
      }
    } catch (err) {
      agentLogger.error(
        "Failed to cancel stream on backend",
        err instanceof Error ? { error: err.message } : { error: String(err) },
      );
    }
    return false;
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
