import React, { useEffect, useState, useRef } from "react";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";
import { agentService } from "../../services/agent-service";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  logger: string;
  workspace_id?: string;
  trace_id: string;
  span_id?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function LogsPage() {
  // Filters & Logs state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);

  const [selectedWorkspace, setSelectedWorkspace] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [limit] = useState(100);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Right-click context menu state
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    visible: boolean;
    selectedText: string;
  }>({ x: 0, y: 0, visible: false, selectedText: "" });

  // Floating Chat Drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState("");

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Helper to construct API URL
  const getApiUrl = (path: string) => {
    const host = window.location.hostname;
    const port = window.location.port;
    const base =
      port === "5173" || port === "5174" ? `http://${host}:8000` : "";
    return `${base}${path}`;
  };

  // Fetch workspaces for filter dropdown
  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const list = await workspaceService.getAllWorkspaces();
        setWorkspaces(list);
      } catch (err) {
        console.error("Failed to load workspaces", err);
      }
    };
    fetchWorkspaces();
  }, []);

  // Fetch logs based on filter settings
  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedWorkspace) params.append("workspace_id", selectedWorkspace);
      if (selectedLevel) params.append("level", selectedLevel);
      if (searchQuery) params.append("search", searchQuery);
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());

      const res = await fetch(getApiUrl(`/api/logs?${params.toString()}`));
      if (!res.ok) throw new Error("Failed to fetch logs from backend");

      const data = await res.json();
      setLogs(data.logs || []);
      setTotalLogs(data.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load logs");
    } finally {
      setIsLoading(false);
    }
  };

  // Re-fetch when filter options change
  useEffect(() => {
    setOffset(0);
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkspace, selectedLevel, limit, offset]);

  // Scroll to bottom of chat drawer on message changes
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, streamedResponse]);

  // Context menu handling
  const handleContextMenu = (e: React.MouseEvent) => {
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString().trim() : "";

    if (selectedText) {
      e.preventDefault();
      setContextMenu({
        x: e.clientX,
        y: e.clientY,
        visible: true,
        selectedText,
      });
    } else {
      setContextMenu((prev) => ({ ...prev, visible: false }));
    }
  };

  // Close context menu on click elsewhere
  useEffect(() => {
    const closeMenu = () => {
      setContextMenu((prev) => ({ ...prev, visible: false }));
    };
    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);

  // Initialize and launch debug chat
  const handleSendToHermes = async () => {
    setContextMenu((prev) => ({ ...prev, visible: false }));
    setIsDrawerOpen(true);
    setChatMessages([]);
    setStreamedResponse("");
    setIsSending(true);

    try {
      // 1. Create a session on the backend
      const session = await agentService.createSession(
        selectedWorkspace || undefined,
      );
      setChatSessionId(session.sessionId);

      // 2. Format the diagnostic log message
      const initialPrompt = `The following log output was selected for debugging:\n\n\`\`\`json\n${contextMenu.selectedText}\n\`\`\`\n\nPlease analyze this log for issues and offer troubleshooting solutions.`;

      setChatMessages([{ role: "user", content: initialPrompt }]);

      // 3. Send to agent
      let responseText = "";
      for await (const event of agentService.sendMessage(
        session.sessionId,
        initialPrompt,
      )) {
        if (event.type === "token") {
          responseText += event.text;
          setStreamedResponse(responseText);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: responseText },
      ]);
      setStreamedResponse("");
    } catch (err: any) {
      console.error(err);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Failed to communicate with Hermes: ${err.message || "Unknown error"}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // Send subsequent messages in chat drawer
  const handleSendChatMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !chatSessionId || isSending) return;

    const userMsg = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setIsSending(true);
    setStreamedResponse("");

    try {
      let responseText = "";
      for await (const event of agentService.sendMessage(
        chatSessionId,
        userMsg,
      )) {
        if (event.type === "token") {
          responseText += event.text;
          setStreamedResponse(responseText);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: responseText },
      ]);
      setStreamedResponse("");
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.message || "Failed to send message."}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div
      data-testid="page-logs"
      onContextMenu={handleContextMenu}
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        gap: "var(--space-md)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Title & Stats */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h2 style={{ fontFamily: "var(--font-ui)", fontWeight: 600 }}>
          Application Logs
        </h2>
        <span style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
          Total logs found: <strong>{totalLogs}</strong>
        </span>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-md)",
          alignItems: "center",
          flexWrap: "wrap",
          padding: "var(--space-sm)",
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
        }}
      >
        {/* Workspace Dropdown */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "180px",
            textAlign: "left",
          }}
        >
          <label
            style={{
              fontSize: "0.7rem",
              color: "var(--color-secondary)",
              fontWeight: 600,
            }}
          >
            FILTER WORKSPACE
          </label>
          <select
            data-testid="logs-filter-workspace"
            value={selectedWorkspace}
            onChange={(e) => setSelectedWorkspace(e.target.value)}
            style={{
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "4px var(--space-sm)",
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            <option value="">All Workspaces</option>
            {workspaces.map((w) => (
              <option key={w.workspace_id} value={w.workspace_id}>
                {w.workspace_name || w.local_path.split("/").pop()}
              </option>
            ))}
          </select>
        </div>

        {/* Severity Level Dropdown */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            minWidth: "120px",
            textAlign: "left",
          }}
        >
          <label
            style={{
              fontSize: "0.7rem",
              color: "var(--color-secondary)",
              fontWeight: 600,
            }}
          >
            SEVERITY LEVEL
          </label>
          <select
            data-testid="logs-filter-level"
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            style={{
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "4px var(--space-sm)",
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            <option value="">All Levels</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        {/* Search Query Input */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "2px",
            flex: 1,
            minWidth: "200px",
            textAlign: "left",
          }}
        >
          <label
            style={{
              fontSize: "0.7rem",
              color: "var(--color-secondary)",
              fontWeight: 600,
            }}
          >
            KEYWORD SEARCH
          </label>
          <input
            data-testid="logs-filter-search"
            type="text"
            placeholder="Search events, messages, logger names..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchLogs()}
            style={{
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "4px var(--space-sm)",
              fontSize: "0.85rem",
              outline: "none",
            }}
          />
        </div>

        {/* Action Buttons */}
        <div
          style={{
            display: "flex",
            gap: "var(--space-sm)",
            alignSelf: "flex-end",
          }}
        >
          <button
            data-testid="logs-refresh-btn"
            onClick={fetchLogs}
            style={{
              padding: "5px var(--space-md)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              fontSize: "0.8rem",
              fontWeight: 600,
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Logs Table Area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          backgroundColor: "var(--color-surface)",
        }}
      >
        {isLoading ? (
          <div
            style={{
              padding: "var(--space-2xl)",
              color: "var(--color-secondary)",
              fontSize: "0.9rem",
            }}
          >
            Loading system logs...
          </div>
        ) : error ? (
          <div
            style={{
              padding: "var(--space-2xl)",
              color: "var(--color-error)",
              fontSize: "0.9rem",
            }}
          >
            {error}
          </div>
        ) : logs.length === 0 ? (
          <div
            style={{
              padding: "var(--space-2xl)",
              color: "var(--color-secondary)",
              fontSize: "0.9rem",
            }}
          >
            No logs matched the selected filters.
          </div>
        ) : (
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "0.8rem",
              textAlign: "left",
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--color-border)",
                  backgroundColor: "var(--color-surface-subtle)",
                }}
              >
                <th
                  style={{
                    padding: "8px",
                    width: "80px",
                    color: "var(--color-secondary)",
                  }}
                >
                  TIME
                </th>
                <th
                  style={{
                    padding: "8px",
                    width: "80px",
                    color: "var(--color-secondary)",
                  }}
                >
                  LEVEL
                </th>
                <th
                  style={{
                    padding: "8px",
                    width: "150px",
                    color: "var(--color-secondary)",
                  }}
                >
                  LOGGER
                </th>
                <th style={{ padding: "8px", color: "var(--color-secondary)" }}>
                  MESSAGE
                </th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: "1px solid var(--color-border)",
                    backgroundColor:
                      log.level === "error"
                        ? "rgba(239, 68, 68, 0.02)"
                        : "transparent",
                  }}
                >
                  <td
                    style={{
                      padding: "6px 8px",
                      fontFamily: "var(--font-mono)",
                      color: "var(--color-secondary)",
                    }}
                  >
                    {log.timestamp.includes("T")
                      ? log.timestamp.split("T")[1].substring(0, 8)
                      : log.timestamp.substring(11, 19)}
                  </td>
                  <td style={{ padding: "6px 8px" }}>
                    <span
                      style={{
                        padding: "2px 6px",
                        borderRadius: "var(--radius-sm)",
                        fontSize: "0.65rem",
                        fontWeight: "bold",
                        textTransform: "uppercase",
                        backgroundColor:
                          log.level === "error"
                            ? "rgba(239, 68, 68, 0.15)"
                            : log.level === "warning"
                              ? "rgba(245, 158, 11, 0.15)"
                              : "rgba(34, 197, 94, 0.15)",
                        color:
                          log.level === "error"
                            ? "var(--color-error, #ef4444)"
                            : log.level === "warning"
                              ? "#f59e0b"
                              : "var(--color-success, #22c55e)",
                      }}
                    >
                      {log.level}
                    </span>
                  </td>
                  <td
                    style={{
                      padding: "6px 8px",
                      color: "var(--color-secondary)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {log.logger}
                  </td>
                  <td
                    style={{
                      padding: "6px 8px",
                      fontFamily: "var(--font-mono)",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-all",
                    }}
                  >
                    {log.message}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination (Simple) */}
      {logs.length > 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "0.8rem",
          }}
        >
          <button
            disabled={offset === 0}
            onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
            style={{
              padding: "4px 8px",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              opacity: offset === 0 ? 0.4 : 1,
            }}
          >
            Previous
          </button>
          <span>
            Showing logs {offset + 1} -{" "}
            {Math.min(offset + logs.length, totalLogs)} of {totalLogs}
          </span>
          <button
            disabled={offset + logs.length >= totalLogs}
            onClick={() => setOffset((prev) => prev + limit)}
            style={{
              padding: "4px 8px",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              opacity: offset + logs.length >= totalLogs ? 0.4 : 1,
            }}
          >
            Next
          </button>
        </div>
      )}

      {/* Right-click Context Menu */}
      {contextMenu.visible && (
        <div
          data-testid="logs-context-menu"
          style={{
            position: "fixed",
            left: contextMenu.x,
            top: contextMenu.y,
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-glow)",
            zIndex: 100,
            padding: "4px 0",
          }}
        >
          <button
            data-testid="logs-context-send-btn"
            onClick={handleSendToHermes}
            style={{
              display: "block",
              width: "100%",
              padding: "var(--space-xs) var(--space-md)",
              fontSize: "0.85rem",
              textAlign: "left",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor =
                "rgba(56, 189, 248, 0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            Send selection to Hermes for help
          </button>
        </div>
      )}

      {/* 4. Sliding Debugger Drawer (Hermes Chat) */}
      {isDrawerOpen && (
        <div
          data-testid="logs-debug-drawer"
          style={{
            position: "fixed",
            top: 0,
            right: 0,
            bottom: 0,
            width: "420px",
            backgroundColor: "var(--color-surface)",
            borderLeft: "1px solid var(--color-border)",
            boxShadow: "-4px 0 24px rgba(0, 0, 0, 0.3)",
            zIndex: 200,
            display: "flex",
            flexDirection: "column",
            textAlign: "left",
            animation: "slideIn 0.2s ease-out forwards",
          }}
        >
          {/* Drawer Header */}
          <div
            style={{
              padding: "var(--space-md)",
              borderBottom: "1px solid var(--color-border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              backgroundColor: "var(--color-surface-subtle)",
            }}
          >
            <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>
              Hermes Diagnostic Debugger
            </h3>
            <button
              data-testid="logs-drawer-close"
              onClick={() => setIsDrawerOpen(false)}
              style={{
                fontSize: "1.2rem",
                color: "var(--color-secondary)",
                padding: "2px var(--space-xs)",
              }}
            ></button>
          </div>

          {/* Chat Transcript */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "var(--space-md)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-md)",
            }}
          >
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  backgroundColor:
                    msg.role === "user"
                      ? "rgba(56, 189, 248, 0.08)"
                      : "var(--color-surface-subtle)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-sm) var(--space-md)",
                  maxWidth: "85%",
                  fontSize: "0.8rem",
                }}
              >
                <div
                  style={{
                    fontWeight: "bold",
                    fontSize: "0.7rem",
                    marginBottom: "2px",
                    color: "var(--color-secondary)",
                  }}
                >
                  {msg.role === "user" ? "YOU" : "HERMES"}
                </div>
                <div
                  style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Streamed token placeholder */}
            {streamedResponse && (
              <div
                style={{
                  alignSelf: "flex-start",
                  backgroundColor: "var(--color-surface-subtle)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-sm) var(--space-md)",
                  maxWidth: "85%",
                  fontSize: "0.8rem",
                }}
              >
                <div
                  style={{
                    fontWeight: "bold",
                    fontSize: "0.7rem",
                    marginBottom: "2px",
                    color: "var(--color-secondary)",
                  }}
                >
                  HERMES
                </div>
                <div
                  style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
                >
                  {streamedResponse}
                  <span className="thinking-dot" />
                </div>
              </div>
            )}

            {isSending && !streamedResponse && (
              <div
                style={{
                  display: "flex",
                  gap: "4px",
                  paddingLeft: "var(--space-xs)",
                }}
              >
                <span className="thinking-dot" />
                <span className="thinking-dot" />
                <span className="thinking-dot" />
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Composer Form */}
          <form
            onSubmit={handleSendChatMessage}
            style={{
              padding: "var(--space-md)",
              borderTop: "1px solid var(--color-border)",
              display: "flex",
              gap: "var(--space-sm)",
              backgroundColor: "var(--color-surface-subtle)",
            }}
          >
            <input
              data-testid="logs-drawer-input"
              type="text"
              placeholder="Ask Hermes about the error..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={isSending}
              style={{
                flex: 1,
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-sm)",
                fontSize: "0.85rem",
                outline: "none",
              }}
            />
            <button
              data-testid="logs-drawer-send"
              type="submit"
              disabled={isSending || !chatInput.trim()}
              style={{
                padding: "0 var(--space-md)",
                backgroundColor: "var(--color-secondary)",
                color: "var(--color-surface-subtle)",
                fontSize: "0.85rem",
                fontWeight: 600,
                borderRadius: "var(--radius-md)",
                opacity: isSending || !chatInput.trim() ? 0.5 : 1,
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}

      {/* Slide in styles */}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}

export default LogsPage;
