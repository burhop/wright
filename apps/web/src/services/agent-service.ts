import type {
  ChatSession,
  ChatSessionCompact,
  ChatMessage,
} from "../store/types";
import { logger } from "./logger";
import { hostAdapter } from "./host-adapter";

const agentLogger = logger.child("HermesAgentService");

export type AgentEvent =
  | { type: "stream_start"; streamId: string; startedAt?: number }
  | { type: "token"; text: string }
  | { type: "tool"; name: string; preview: string; percentage?: number }
  | {
      type: "progress";
      percentage?: number;
      message: string;
      title: string;
      detail?: string;
      server?: string;
      tool?: string;
      status?: string;
      progress?: number;
      total?: number;
      correlationId?: string;
      heartbeat?: boolean;
    }
  | { type: "done"; session: ChatSession }
  | { type: "error"; message: string };

export interface AgentUiContext {
  activeRivetSlug?: string | null;
}

export interface AgentStreamStatus {
  active: boolean;
  sessionId: string;
  streamId?: string;
  message?: string;
  startedAt?: number;
  eventCount?: number;
}

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

export interface HermesModelOption {
  value: string;
  label: string;
  provider: string;
  model: string;
  is_current: boolean;
}

export interface HermesModelOptionGroup {
  provider: string;
  label: string;
  options: HermesModelOption[];
}

export interface HermesModelOptionsResponse {
  current_value?: string | null;
  current_provider?: string | null;
  current_model?: string | null;
  groups: HermesModelOptionGroup[];
}

export interface SetHermesModelResponse {
  ok: boolean;
  provider: string;
  model: string;
  session_locked: boolean;
  confirm_required: boolean;
  confirm_message?: string | null;
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

export function summarizeProgressPayload(data: any): {
  title: string;
  detail?: string;
  message: string;
  percentage?: number;
  server?: string;
  tool?: string;
  status?: string;
  progress?: number;
  total?: number;
  correlationId?: string;
  heartbeat?: boolean;
} {
  const server = data?.server || data?.server_id;
  const tool = data?.tool || data?.tool_name || data?.name;
  const status = data?.status || data?.state || data?.phase;
  const label = data?.title || data?.label || data?.step || data?.operation;
  const message = data?.message || data?.detail || data?.description || "";
  const progress =
    typeof data?.progress === "number" ? data.progress : undefined;
  const total = typeof data?.total === "number" ? data.total : undefined;
  const percentage =
    typeof data?.percentage === "number"
      ? data.percentage
      : progress !== undefined && total !== undefined && total > 0
        ? Math.round((progress / total) * 100)
        : undefined;

  const statusText = formatProgressStatus(status);
  let title = "Tool progress";
  if (label) {
    title = `${label}`;
  } else if (tool && statusText) {
    title = `${tool}: ${statusText}`;
  } else if (tool) {
    title = `${tool}`;
  } else if (statusText) {
    title = statusText;
  }

  const identity = [server, tool]
    .filter((part) => typeof part === "string" && part.trim().length > 0)
    .join(" / ");
  const details = [identity, message]
    .filter((part) => typeof part === "string" && part.trim().length > 0)
    .map((part) => String(part).trim());
  const uniqueDetails = Array.from(new Set(details));
  const detail =
    uniqueDetails.length > 0 ? uniqueDetails.join(" - ") : undefined;

  return {
    title,
    detail,
    message: detail || title,
    percentage,
    server: typeof server === "string" ? server : undefined,
    tool: typeof tool === "string" ? tool : undefined,
    status: typeof status === "string" ? status : undefined,
    progress,
    total,
    correlationId:
      typeof data?.correlationId === "string"
        ? data.correlationId
        : typeof data?.correlation_id === "string"
          ? data.correlation_id
          : undefined,
    heartbeat: data?.heartbeat === true || undefined,
  };
}

export class HermesAgentService {
  private activeStreams = new Map<
    string,
    { abortController: AbortController; abort: () => void }
  >();
  private activeAgentRequest: Promise<string> | null = null;
  private modelOptionsRequest: Promise<HermesModelOptionsResponse> | null = null;
  private modelOptionsCache: HermesModelOptionsResponse | null = null;
  private commandsRequest: Promise<AgentCommand[]> | null = null;
  private commandsCache: AgentCommand[] | null = null;

  async checkHealth(): Promise<ServiceHealthResult> {
    try {
      const response = await fetch(`${API_BASE}/api/agent/health`);
      if (response.ok) {
        const data = await response.json();
        return {
          state: data.state as "connected" | "disconnected" | "unknown",
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
      ? `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/sessions?refresh=false`
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
    uiContext?: AgentUiContext,
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
        body: JSON.stringify({
          session_id: sessionId,
          message,
          attachments,
          active_rivet_slug: uiContext?.activeRivetSlug ?? null,
        }),
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

      for await (const eventYield of this.readSSEEvents(response, sessionId)) {
        yield eventYield;
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

  private async *readSSEEvents(
    response: Response,
    sessionId: string,
  ): AsyncIterable<AgentEvent> {
    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
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
  }

  async *attachStream(sessionId: string, after = 0): AsyncIterable<AgentEvent> {
    try {
      const response = await fetch(
        `${API_BASE}/api/agent/chat/stream?session_id=${encodeURIComponent(sessionId)}&after=${after}`,
      );
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        yield {
          type: "error",
          message:
            errData.message || errData.detail || "No stream is available.",
        };
        return;
      }
      for await (const eventYield of this.readSSEEvents(response, sessionId)) {
        yield eventYield;
      }
    } catch (err) {
      yield {
        type: "error",
        message:
          err instanceof Error
            ? err.message
            : "The agent response could not be reconnected.",
      };
    }
  }

  async getStreamStatus(sessionId: string): Promise<AgentStreamStatus> {
    const response = await fetch(
      `${API_BASE}/api/agent/chat/stream/status?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to check agent work: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      active: data.active === true,
      sessionId: data.session_id || sessionId,
      streamId: data.stream_id || undefined,
      message: data.message || undefined,
      startedAt:
        typeof data.started_at === "number" ? data.started_at : undefined,
      eventCount:
        typeof data.event_count === "number" ? data.event_count : undefined,
    };
  }

  private parseSSEEvent(
    event: string,
    dataStr: string,
    sessionId: string,
  ): AgentEvent | null {
    if (event === "stream_start") {
      try {
        const data = JSON.parse(dataStr);
        return {
          type: "stream_start",
          streamId: data.streamId || data.stream_id || data.id || "",
          startedAt:
            typeof data.startedAt === "number"
              ? data.startedAt
              : typeof data.started_at === "number"
                ? data.started_at
                : undefined,
        };
      } catch (err) {
        return { type: "stream_start", streamId: dataStr };
      }
    } else if (event === "token") {
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
          server: summary.server,
          tool: summary.tool,
          status: summary.status,
          progress: summary.progress,
          total: summary.total,
          correlationId: summary.correlationId,
          heartbeat: summary.heartbeat,
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
    if (this.activeAgentRequest) return this.activeAgentRequest;
    this.activeAgentRequest = (async () => {
      const response = await fetch(`${API_BASE}/api/agent/active`);
      if (!response.ok) {
        throw new Error(`Failed to get active agent: ${response.statusText}`);
      }
      const data = await response.json();
      return data.agent;
    })();
    try {
      return await this.activeAgentRequest;
    } finally {
      this.activeAgentRequest = null;
    }
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

  async listHermesModels(refresh = false): Promise<HermesModelOptionsResponse> {
    if (!refresh && this.modelOptionsCache) return this.modelOptionsCache;
    if (!refresh && this.modelOptionsRequest) return this.modelOptionsRequest;
    const request = (async () => {
      const response = await fetch(
        `${API_BASE}/api/agent/models${refresh ? "?refresh=true" : ""}`,
      );
      if (!response.ok) {
        throw new Error(`Failed to list Hermes models: ${response.statusText}`);
      }
      const options = (await response.json()) as HermesModelOptionsResponse;
      this.modelOptionsCache = options;
      return options;
    })();
    if (!refresh) this.modelOptionsRequest = request;
    try {
      return await request;
    } finally {
      if (!refresh) this.modelOptionsRequest = null;
    }
  }

  async setHermesModel(
    provider: string,
    model: string,
    sessionId?: string | null,
  ): Promise<SetHermesModelResponse> {
    const response = await fetch(`${API_BASE}/api/agent/model`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider,
        model,
        session_id: sessionId || null,
      }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Failed to set Hermes model: ${response.statusText}`,
      );
    }
    this.modelOptionsCache = null;
    return response.json();
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
    if (this.commandsCache) return this.commandsCache;
    if (this.commandsRequest) return this.commandsRequest;
    agentLogger.info("Fetching commands");
    this.commandsRequest = (async () => {
      const response = await fetch(`${API_BASE}/api/agent/commands`);
      if (!response.ok) {
        agentLogger.error("Failed to fetch commands", {
          statusText: response.statusText,
        });
        throw new Error(`Failed to fetch commands: ${response.statusText}`);
      }
      const data = await response.json();
      this.commandsCache = data.commands;
      return data.commands;
    })();
    try {
      return await this.commandsRequest;
    } finally {
      this.commandsRequest = null;
    }
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
