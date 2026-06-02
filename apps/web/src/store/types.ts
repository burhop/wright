export interface NavigationSection {
  id: string;
  label: string;
  path: string;
  icon: string;
  order: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  traceId: string | null;
}

export interface ChatSession {
  sessionId: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  isActive: boolean;
}

export type ChatSessionCompact = Omit<ChatSession, 'messages' | 'isActive'>;

export interface ServiceStatus {
  serviceId: string;
  name: string;
  endpoint: string;
  state: 'connected' | 'disconnected' | 'unknown';
  lastChecked: number | null;
}

export interface WorkspaceFile {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number | null;
  children: WorkspaceFile[] | null;
}

export interface TraceContext {
  traceId: string;
  spanId: string;
  actionName: string;
  startTime: number;
  duration: number | null;
  status: 'ok' | 'error' | 'in-progress';
}

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  component: string;
  traceId: string | null;
  metadata: Record<string, unknown>;
}
