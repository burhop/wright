import type { ChatSession, ChatSessionCompact } from '../store/types';
import { logger } from './logger';

const agentLogger = logger.child('HermesAgentService');


export type AgentEvent =
  | { type: 'token'; text: string }
  | { type: 'tool'; name: string; preview: string }
  | { type: 'done'; session: ChatSession }
  | { type: 'error'; message: string };

export interface ServiceHealthResult {
  state: 'connected' | 'disconnected' | 'unknown';
  latencyMs?: number;
}

const API_BASE = 'http://127.0.0.1:8000';

export class HermesAgentService {
  async checkHealth(): Promise<ServiceHealthResult> {
    try {
      const response = await fetch(`${API_BASE}/api/agent/health`);
      if (response.ok) {
        const data = await response.json();
        return {
          state: data.state as 'connected' | 'disconnected',
          latencyMs: data.latencyMs,
        };
      }
    } catch (err) {
      console.error('Agent health check failed', err);
    }
    return { state: 'disconnected', latencyMs: 0 };
  }

  async createSession(workspace?: string): Promise<ChatSession> {
    agentLogger.info('Creating session', { workspace });
    const response = await fetch(`${API_BASE}/api/agent/sessions/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ workspace }),
    });

    if (!response.ok) {
      agentLogger.error('Failed to create session', { statusText: response.statusText, status: response.status });
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
    agentLogger.info('Deleting session', { sessionId });
    const response = await fetch(`${API_BASE}/api/agent/sessions/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      agentLogger.error('Failed to delete session', { sessionId, statusText: response.statusText });
      throw new Error(`Failed to delete session: ${response.statusText}`);
    }
    agentLogger.info('Session deleted successfully', { sessionId });
  }

  async *sendMessage(sessionId: string, message: string): AsyncIterable<AgentEvent> {
    agentLogger.info('Sending message', { sessionId, messageLength: message.length });
    // 1. Initiate chat start
    const response = await fetch(`${API_BASE}/api/agent/chat/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      agentLogger.error('Failed to initiate chat', { sessionId, error: errData.detail });
      yield { type: 'error', message: errData.detail || 'Hermes agent is not available.' };
      return;
    }

    const { stream_id } = await response.json();
    agentLogger.info('Chat stream started', { sessionId, streamId: stream_id });

    // 2. Consume SSE stream via browser Native EventSource
    const eventQueue: AgentEvent[] = [];
    let isDone = false;
    let resolveQueue: (() => void) | null = null;

    const eventSource = new EventSource(`${API_BASE}/api/agent/chat/stream?stream_id=${stream_id}`);

    const pushEvent = (evt: AgentEvent) => {
      eventQueue.push(evt);
      if (resolveQueue) {
        resolveQueue();
        resolveQueue = null;
      }
    };

    eventSource.addEventListener('token', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        agentLogger.debug('Stream token received', { sessionId, tokenLength: data.text?.length });
        pushEvent({ type: 'token', text: data.text });
      } catch (err) {
        agentLogger.debug('Stream token received (raw)', { sessionId, tokenLength: e.data?.length });
        pushEvent({ type: 'token', text: e.data });
      }
    });

    eventSource.addEventListener('tool', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        agentLogger.info('Stream tool invoke received', { sessionId, toolName: data.name, preview: data.preview });
        pushEvent({ type: 'tool', name: data.name, preview: data.preview || '' });
      } catch (err) {
        // ignore
      }
    });

    eventSource.addEventListener('stream_end', (_e: MessageEvent) => {
      agentLogger.info('Stream completed', { sessionId });
      eventSource.close();
      pushEvent({
        type: 'done',
        session: {
          sessionId,
          title: '', // filled dynamically in reducer
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

    eventSource.addEventListener('error', (e: any) => {
      const errMsg = e.data ? (typeof e.data === 'string' ? e.data : JSON.stringify(e.data)) : 'Hermes response stream failed.';
      agentLogger.error('Stream error encountered', { sessionId, error: errMsg });
      eventSource.close();
      pushEvent({ type: 'error', message: e.data ? JSON.parse(e.data).message : 'Hermes response stream failed.' });
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
}

export const agentService = new HermesAgentService();
export default agentService;
