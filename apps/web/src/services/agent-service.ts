import type { ChatSession, ChatSessionCompact } from '../store/types';

export type AgentEvent =
  | { type: 'token'; text: string }
  | { type: 'tool'; name: string; preview: string }
  | { type: 'done'; session: ChatSession }
  | { type: 'error'; message: string };

export interface ServiceHealthResult {
  state: 'connected' | 'disconnected' | 'unknown';
  latencyMs?: number;
}

export class StubAgentService {
  private sessions: Map<string, ChatSession> = new Map();

  async checkHealth(): Promise<ServiceHealthResult> {
    return { state: 'connected', latencyMs: 15 };
  }

  async createSession(workspace?: string): Promise<ChatSession> {
    const sessionId = Math.random().toString(16).substring(2, 14);
    const session: ChatSession = {
      sessionId,
      title: workspace ? `Session on ${workspace}` : 'New Engineering Session',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isActive: true,
    };
    this.sessions.set(sessionId, session);
    return session;
  }

  async listSessions(): Promise<ChatSessionCompact[]> {
    return Array.from(this.sessions.values()).map(({ sessionId, title, createdAt, updatedAt }) => ({
      sessionId,
      title,
      createdAt,
      updatedAt,
    }));
  }

  async loadSession(sessionId: string): Promise<ChatSession> {
    let session = this.sessions.get(sessionId);
    if (!session) {
      // Auto create if requested but not in memory (for easy hydration)
      session = {
        sessionId,
        title: 'Engineering Session',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        isActive: true,
      };
      this.sessions.set(sessionId, session);
    }
    return session;
  }

  async deleteSession(sessionId: string): Promise<void> {
    this.sessions.delete(sessionId);
  }

  async *sendMessage(sessionId: string, message: string): AsyncIterable<AgentEvent> {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = await this.loadSession(sessionId);
    }

    yield { type: 'tool', name: 'calculate_stress', preview: 'Analyzing stress fields on component...' };
    await new Promise((resolve) => setTimeout(resolve, 600));

    const responseText = `I have received your request: "${message}". As a local offline assistant in v1, I am processing your mechanical designs. Let me know if you need to inspect workspace files or check specific calculations.`;
    
    const words = responseText.split(' ');
    for (const word of words) {
      yield { type: 'token', text: word + ' ' };
      await new Promise((resolve) => setTimeout(resolve, 30));
    }

    // Add assistant message
    const assistantMsg = {
      id: Math.random().toString(36).substring(7),
      role: 'assistant' as const,
      content: responseText.trim(),
      timestamp: Date.now(),
      traceId: 'tr-' + Math.random().toString(36).substring(7),
    };
    session.messages.push(assistantMsg);
    session.updatedAt = Date.now();

    yield { type: 'done', session };
  }
}

export const agentService = new StubAgentService();
export default agentService;
