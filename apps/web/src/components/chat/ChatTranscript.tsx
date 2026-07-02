import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import type {
  ChatMessage,
  ChatSession,
  StreamActivityEntry,
} from "../../store/types";

interface ChatTranscriptProps {
  session: ChatSession | null;
  isStreaming?: boolean;
  streamedText?: string;
  activeTool?: { name: string; preview: string; percentage?: number } | null;
  streamActivity?: StreamActivityEntry[];
  onOpenFile?: (path: string) => void;
  activeSessionId?: string;
  workspacePath?: string;
}

function formatActivityTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function ActivityPanel({
  isStreaming,
  activeTool,
  entries,
}: {
  isStreaming: boolean;
  activeTool: { name: string; preview: string; percentage?: number } | null;
  entries: StreamActivityEntry[];
}) {
  const [expanded, setExpanded] = useState(false);
  const latestEntry = entries[entries.length - 1];
  const summary = activeTool
    ? activeTool.name
      ? `Using ${activeTool.name}`
      : "Using a tool"
    : latestEntry?.title || (isStreaming ? "Waiting for Hermes" : "Activity");
  const detail = activeTool?.preview || latestEntry?.detail;
  const percentage = activeTool?.percentage ?? latestEntry?.percentage;

  return (
    <div
      data-testid="stream-activity-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        alignSelf: "flex-start",
        padding: "var(--space-md)",
        backgroundColor: "var(--color-surface-subtle)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        color: "var(--color-secondary)",
        fontFamily: "var(--font-ui)",
        fontSize: "0.8rem",
        width: "100%",
        minWidth: 0,
        boxSizing: "border-box",
        gap: "var(--space-sm)",
      }}
    >
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-sm)",
          width: "100%",
          minWidth: 0,
          padding: 0,
          border: "none",
          background: "transparent",
          color: "inherit",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <span
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-sm)",
            minWidth: 0,
          }}
        >
          <span
            className={isStreaming ? "thinking-dot" : undefined}
            style={
              isStreaming
                ? undefined
                : {
                    display: "inline-block",
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    backgroundColor: "var(--color-secondary)",
                    flex: "0 0 auto",
                  }
            }
          />
          <span style={{ minWidth: 0 }}>
            <strong style={{ color: "var(--color-primary)" }}>
              {isStreaming ? "Working" : "Activity"}
            </strong>
            <span style={{ marginLeft: "0.35rem" }}>{summary}</span>
          </span>
        </span>
        <span
          style={{
            color: "var(--color-secondary)",
            flex: "0 0 auto",
            fontSize: "0.75rem",
          }}
        >
          {expanded ? "Hide" : "Show"}
        </span>
      </button>

      {detail && (
        <div
          style={{
            color: "var(--color-primary)",
            fontSize: "0.75rem",
            lineHeight: 1.35,
            overflowWrap: "anywhere",
            wordBreak: "break-word",
          }}
        >
          {detail}
        </div>
      )}

      {percentage !== undefined && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "0.75rem",
            }}
          >
            <span>Progress</span>
            <span data-testid="progress-percentage">{percentage}%</span>
          </div>
          <div
            style={{
              height: "6px",
              width: "100%",
              backgroundColor: "var(--color-neutral)",
              borderRadius: "3px",
              overflow: "hidden",
              border: "1px solid var(--color-border)",
            }}
          >
            <div
              data-testid="progress-bar"
              style={{
                height: "100%",
                width: `${Math.max(0, Math.min(100, percentage))}%`,
                backgroundColor: "var(--color-success)",
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      )}

      {expanded && (
        <div
          data-testid="stream-activity-details"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-xs)",
            borderTop: "1px solid var(--color-border)",
            paddingTop: "var(--space-sm)",
          }}
        >
          {entries.length === 0 ? (
            <div>Waiting for stream activity.</div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto minmax(0, 1fr)",
                  gap: "var(--space-xs)",
                  alignItems: "baseline",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.7rem",
                    opacity: 0.75,
                  }}
                >
                  {formatActivityTime(entry.timestamp)}
                </span>
                <span style={{ minWidth: 0 }}>
                  <span style={{ color: "var(--color-primary)" }}>
                    {entry.title}
                  </span>
                  {entry.detail && (
                    <span
                      style={{
                        display: "block",
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {entry.detail}
                    </span>
                  )}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export function ChatTranscript({
  session,
  isStreaming = false,
  streamedText = "",
  activeTool = null,
  streamActivity = [],
  onOpenFile,
  activeSessionId,
  workspacePath,
}: ChatTranscriptProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    const container = containerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [
    session?.messages?.length,
    streamedText,
    activeTool,
    streamActivity.length,
  ]);

  if (!session) {
    return (
      <div
        data-testid="chat-transcript"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--color-secondary)",
          fontFamily: "var(--font-ui)",
          fontSize: "0.8rem",
        }}
      >
        <span>Select or create a session to start chatting.</span>
      </div>
    );
  }

  const mockStreamingMessage: ChatMessage | null =
    isStreaming && streamedText.trim()
      ? {
          id: "streaming-msg",
          role: "assistant",
          content: streamedText,
          timestamp: Date.now(),
          traceId: null,
        }
      : null;

  return (
    <div
      ref={containerRef}
      data-testid="chat-transcript"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-lg)",
        padding: "var(--space-lg)",
        height: "100%",
        overflowY: "auto",
        scrollBehavior: "smooth",
      }}
    >
      {session.messages.length === 0 && !isStreaming && (
        <div
          style={{
            margin: "auto",
            textAlign: "center",
            color: "var(--color-secondary)",
            fontFamily: "var(--font-body)",
          }}
        >
          <p style={{ fontSize: "0.9rem" }}>No messages yet.</p>
          <p style={{ fontSize: "0.78rem", marginTop: "4px" }}>
            Send a message to start conversing with the Hermes Agent.
          </p>
        </div>
      )}

      {session.messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          onOpenFile={onOpenFile}
          activeSessionId={activeSessionId}
          workspacePath={workspacePath}
        />
      ))}

      {(isStreaming || streamActivity.length > 0 || activeTool) && (
        <ActivityPanel
          isStreaming={isStreaming}
          activeTool={activeTool}
          entries={streamActivity}
        />
      )}

      {mockStreamingMessage && (
        <MessageBubble
          message={mockStreamingMessage}
          onOpenFile={onOpenFile}
          activeSessionId={activeSessionId}
          workspacePath={workspacePath}
        />
      )}

      {isStreaming && !streamedText.trim() && (
        <div
          data-testid="thinking-indicator"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: "var(--space-xs)",
            width: "100%",
          }}
        >
          <div
            style={{
              maxWidth: "80%",
              padding: "var(--space-md) var(--space-lg)",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "var(--color-surface-subtle)",
              border: "1px solid var(--color-border)",
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                height: "1.5rem",
              }}
            >
              <span className="thinking-dot"></span>
              <span className="thinking-dot"></span>
              <span className="thinking-dot"></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatTranscript;
