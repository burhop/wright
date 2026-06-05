export interface NavigationSection {
  id: string;
  label: string;
  path: string;
  icon: string;
  order: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
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

export type ChatSessionCompact = Omit<ChatSession, "messages" | "isActive">;

export interface ServiceStatus {
  serviceId: string;
  name: string;
  endpoint: string;
  state: "connected" | "disconnected" | "unknown";
  lastChecked: number | null;
}

export interface WorkspaceFile {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  last_modified: number;
  git_status: "Clean" | "M" | "U" | "A" | "D";
  children: WorkspaceFile[] | null;
}

export interface TraceContext {
  traceId: string;
  spanId: string;
  actionName: string;
  startTime: number;
  duration: number | null;
  status: "ok" | "error" | "in-progress";
}

export interface LogEntry {
  timestamp: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
  component: string;
  traceId: string | null;
  metadata: Record<string, unknown>;
}

export interface EditorTab {
  path: string; // Workspace-relative path to the file (e.g. "/designs/gearbox.stl")
  name: string; // Filename (e.g. "gearbox.stl")
  type: "stl" | "image" | "code" | "text"; // File categorization type
  isDirty: boolean; // True if there are unsaved text edits
  last_modified: number; // Epoch timestamp when file was opened/last modified
}

export interface WorkspaceLayoutState {
  activeSidebarTab: "marketplace" | "files" | "git" | "settings"; // Active pane inside Left Sidebar
  isSidebarCollapsed: boolean; // True if Left Sidebar is collapsed
  isAgentCollapsed: boolean; // True if Right Agent Sidebar is collapsed
  openTabs: EditorTab[]; // List of open file tabs
  activeTabPath: string | null; // Path of the currently focused file tab
  leftSidebarWidth: number; // Width of Left Sidebar in px
  rightSidebarWidth: number; // Width of Right Sidebar in px
}
