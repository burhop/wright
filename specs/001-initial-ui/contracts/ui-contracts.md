# UI Contracts: Initial UI Foundation

**Feature**: 001-initial-ui | **Date**: 2026-06-02

## 1. Service Abstractions

### AgentService

The agent communication layer. In v1, all methods return stub data. When the Hermes Agent backend is available, these methods will issue real HTTP requests.

```typescript
interface AgentService {
  /** Send a message to the agent and receive a response stream */
  sendMessage(sessionId: string, message: string): AsyncIterable<AgentEvent>;
  
  /** Check if the agent backend is reachable */
  checkHealth(): Promise<ServiceHealthResult>;
  
  /** Create a new chat session */
  createSession(workspace?: string): Promise<ChatSession>;
  
  /** List all sessions (compact metadata only, no messages) */
  listSessions(): Promise<ChatSessionCompact[]>;
  
  /** Load a full session with messages */
  loadSession(sessionId: string): Promise<ChatSession>;
  
  /** Delete a session */
  deleteSession(sessionId: string): Promise<void>;
}

type AgentEvent =
  | { type: "token"; text: string }
  | { type: "tool"; name: string; preview: string }
  | { type: "done"; session: ChatSession }
  | { type: "error"; message: string };

type ServiceHealthResult = {
  state: "connected" | "disconnected" | "unknown";
  latencyMs?: number;
};
```

### HealthService

Polls backend services for connectivity status.

```typescript
interface HealthService {
  /** Start periodic health checks (interval in ms) */
  startPolling(intervalMs: number): void;
  
  /** Stop all health checks */
  stopPolling(): void;
  
  /** Get current status of all services */
  getStatuses(): ServiceStatus[];
  
  /** Subscribe to status changes */
  onStatusChange(callback: (statuses: ServiceStatus[]) => void): () => void;
}
```

### Logger

Structured JSON logger contract.

```typescript
interface Logger {
  debug(message: string, metadata?: Record<string, unknown>): void;
  info(message: string, metadata?: Record<string, unknown>): void;
  warn(message: string, metadata?: Record<string, unknown>): void;
  error(message: string, metadata?: Record<string, unknown>): void;
  
  /** Create a child logger scoped to a component */
  child(component: string): Logger;
}
```

### Telemetry

OpenTelemetry trace management contract.

```typescript
interface TelemetryService {
  /** Start a new span for an action */
  startSpan(actionName: string): SpanHandle;
  
  /** Get the current active trace ID (for display in UI) */
  getActiveTraceId(): string | null;
  
  /** Get recent traces for the status area */
  getRecentTraces(limit: number): TraceContext[];
}

interface SpanHandle {
  /** End the span successfully */
  end(): void;
  
  /** End the span with an error */
  error(err: Error): void;
  
  /** Get the trace ID for this span */
  traceId: string;
}
```

## 2. Component Contracts

### AppShell

Top-level layout component. Renders header, sidebar, and content area.

```
Props: { children: ReactNode }
Renders: Header + Sidebar + <main>{children}</main>
data-testid: "app-shell"
```

### Sidebar

Navigation sidebar with links to all sections.

```
Props: { sections: NavigationSection[], activePath: string }
Renders: List of NavItem components
data-testid: "sidebar", each item: "nav-{section.id}"
```

### ChatLayout

Three-panel Hermes-style layout for the Agent Chat page.

```
Props: none (manages own state via ChatContext)
Renders: SessionsSidebar | ChatTranscript + MessageComposer | WorkspacePanel
data-testid: "chat-layout"
Layout: CSS Grid — 260px | 1fr | 280px (right panel collapsible)
```

### SessionsSidebar

Left panel of the chat layout. Lists sessions and provides CRUD controls.

```
Props: { sessions: ChatSessionCompact[], activeId: string | null, onSelect, onCreate, onDelete }
Renders: Session list with action buttons
data-testid: "sessions-sidebar", each session: "session-{sessionId}"
```

### MessageComposer

Text input with send button at the bottom of the chat transcript.

```
Props: { onSend: (message: string) => void, disabled: boolean }
Renders: Textarea + Send button
data-testid: "message-composer", "composer-input", "composer-send"
```

### StatusBar

Service health indicator area in the header.

```
Props: { statuses: ServiceStatus[], latestTrace: TraceContext | null }
Renders: StatusDot per service + latest trace ID
data-testid: "status-bar", each dot: "status-{serviceId}"
```

## 3. Routing Contract

| Path | Component | data-testid |
|------|-----------|-------------|
| `/` | DashboardPage | `"page-dashboard"` |
| `/agent-chat` | AgentChatPage | `"page-agent-chat"` |
| `/tool-registry` | ToolRegistryPage | `"page-tool-registry"` |
| `/file-vault` | FileVaultPage | `"page-file-vault"` |
| `*` | NotFoundPage | `"page-not-found"` |

## 4. Design Token Contract

All components MUST reference CSS custom properties from `tokens/design-tokens.css`. Direct color values, font sizes, and spacing values in component CSS are forbidden.

```css
/* Hermes Calm-Console palette */
--color-primary:       #EAE0D5;  /* main text on dark surfaces */
--color-secondary:     #C6AC8F;  /* secondary text, tool metadata */
--color-neutral:       #0A0908;  /* app shell background */
--color-surface:       #22333B;  /* panel backgrounds */
--color-surface-subtle: #11100E; /* card backgrounds */
--color-border:        #3B4A50;  /* subtle borders */
--color-success:       #86C08B;  /* connected, success states */
--color-warning:       #E0B15D;  /* degraded, warning states */
--color-error:         #F87171;  /* disconnected, error states */

/* Typography */
--font-body:    Georgia, 'Times New Roman', serif;
--font-ui:      -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
--font-mono:    'SF Mono', ui-monospace, monospace;

/* Spacing */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 12px;
--space-lg: 16px;

/* Radii */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
```
