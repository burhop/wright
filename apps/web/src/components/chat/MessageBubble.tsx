import type { ChatMessage } from "../../store/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageBubbleProps {
  message: ChatMessage;
  onOpenFile?: (path: string) => void;
  activeSessionId?: string;
  workspacePath?: string;
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

/**
 * Preprocesses message content by isolating code blocks and wrapping URLs
 * and file paths in the non-code segments with markdown link syntax.
 */
function preprocessContent(
  content: string,
  activeSessionId?: string,
  workspacePath?: string,
): string {
  if (!content) return "";

  // 1. Split content by markdown code blocks (fenced and inline) to preserve literal code
  const parts = content.split(/(```[\s\S]*?```|`[^`\n]+`)/g);

  const processedParts = parts.map((part, index) => {
    if (index % 2 !== 0) {
      // Odd index is a code block. Keep it exactly as-is.
      return part;
    }

    // Combined regex:
    // Group 1: MEDIA:path token: (MEDIA:[^\s\)\],<]+)
    // Group 2: Existing markdown link: (\[.*?\]\(.*?\))
    // Group 3: URL (http/https): (https?:\/\/[^\s\)\],<]+)
    // Group 4: Absolute path starting with /home/ or /tmp/: (\/(?:home|tmp)\/[^\s\)\],<]+)
    // Group 5: Relative path starting with /: (\/[a-zA-Z0-9_\-\.\/]+\.(?:stl|py|scad|json|md|txt|png|jpg|jpeg|gif|svg))
    // Group 6: Relative path not starting with /: (\b[a-zA-Z0-9_\-\.\/]+\.(?:stl|py|scad|json|md|txt|png|jpg|jpeg|gif|svg)\b)
    const regex =
      /(MEDIA:[^\s\)\],<]+)|(\[.*?\]\(.*?\))|(https?:\/\/[^\s\)\],<]+)|(\/(?:home|tmp)\/[^\s\)\],<]+)|(\/[a-zA-Z0-9_\-\.\/]+\.(?:stl|py|scad|json|md|txt|png|jpg|jpeg|gif|svg))|(\b[a-zA-Z0-9_\-\.\/]+\.(?:stl|py|scad|json|md|txt|png|jpg|jpeg|gif|svg)\b)/g;

    return part.replace(
      regex,
      (match, mediaToken, markdownLink, url, absPath, relPathWithSlash, relPathNoSlash) => {
        if (mediaToken) {
          const mediaPath = mediaToken.substring(6); // Strip "MEDIA:"
          let cleanPath = mediaPath;
          if (workspacePath && mediaPath.startsWith(workspacePath)) {
            cleanPath = mediaPath.slice(workspacePath.length);
          } else if (activeSessionId) {
            const idx = mediaPath.indexOf(activeSessionId);
            if (idx !== -1) {
              cleanPath = mediaPath.slice(idx + activeSessionId.length);
            }
          }
          if (!cleanPath.startsWith("/")) {
            cleanPath = "/" + cleanPath;
          }
          const apiBase = getApiBase();
          const encodedPath = encodeURIComponent(cleanPath);
          const imageUrl = `${apiBase}/api/workspace/files/content?session_id=${activeSessionId || ""}&path=${encodedPath}`;
          return `![Rendered Image](${imageUrl})`;
        }

        if (markdownLink) {
          return match;
        }

        if (url) {
          return `[${url}](${url})`;
        }

        if (absPath) {
          let cleanPath = absPath;
          if (workspacePath && absPath.startsWith(workspacePath)) {
            cleanPath = absPath.slice(workspacePath.length);
          } else if (activeSessionId) {
            const idx = absPath.indexOf(activeSessionId);
            if (idx !== -1) {
              cleanPath = absPath.slice(idx + activeSessionId.length);
            }
          }

          // Ensure path starts with a single slash
          if (!cleanPath.startsWith("/")) {
            cleanPath = "/" + cleanPath;
          }
          return `[${absPath}](file://${cleanPath})`;
        }

        if (relPathWithSlash) {
          return `[${relPathWithSlash}](file://${relPathWithSlash})`;
        }

        if (relPathNoSlash) {
          // Prepend leading slash to match tree path format
          return `[${relPathNoSlash}](file:///${relPathNoSlash})`;
        }

        return match;
      },
    );
  });

  return processedParts.join("");
}

export function MessageBubble({
  message,
  onOpenFile,
  activeSessionId,
  workspacePath,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const processedContent = isUser
    ? message.content
    : preprocessContent(message.content, activeSessionId, workspacePath);

  return (
    <div
      data-testid={`message-${message.id}`}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        gap: "var(--space-xs)",
        width: "100%",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "var(--space-md) var(--space-lg)",
          borderRadius: "var(--radius-lg)",
          backgroundColor: isUser
            ? "var(--color-surface)"
            : "var(--color-surface-subtle)",
          border: "1px solid var(--color-border)",
          color: "var(--color-primary)",
          textAlign: "left",
          boxShadow:
            "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
          transition: "all 0.2s ease",
        }}
      >
        <div
          className="message-content"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "0.8rem",
            lineHeight: "1.4",
          }}
        >
          {isUser ? (
            <div style={{ whiteSpace: "pre-wrap" }}>{processedContent}</div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              urlTransform={(url) => {
                // Allow file:// URLs to pass through so we can capture and render them as click buttons
                if (url.startsWith("file://")) {
                  return url;
                }
                const isSafe =
                  url.startsWith("http://") ||
                  url.startsWith("https://") ||
                  url.startsWith("mailto:") ||
                  url.startsWith("tel:");
                return isSafe ? url : "#";
              }}
              components={{
                a: ({ href, children, ...props }) => {
                  if (href && href.startsWith("file://")) {
                    let filePath = href.substring(7);
                    if (filePath.startsWith("//")) {
                      filePath = filePath.substring(1);
                    }
                    if (!filePath.startsWith("/")) {
                      filePath = "/" + filePath;
                    }
                    return (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          if (onOpenFile) {
                            onOpenFile(filePath);
                          }
                        }}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#58a6ff",
                          textDecoration: "underline",
                          cursor: "pointer",
                          padding: 0,
                          font: "inherit",
                          display: "inline",
                        }}
                        title={`Open ${filePath}`}
                      >
                        {children}
                      </button>
                    );
                  }

                  // Explicitly validate protocol to prevent javascript: or vbscript: XSS vectors
                  const isSafe =
                    href &&
                    (href.startsWith("http://") ||
                      href.startsWith("https://") ||
                      href.startsWith("mailto:") ||
                      href.startsWith("tel:"));
                  return (
                    <a
                      href={isSafe ? href : "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {processedContent}
            </ReactMarkdown>
          )}
        </div>

        <div
          style={{
            marginTop: "var(--space-xs)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-md)",
            fontSize: "0.75rem",
            color: "var(--color-secondary)",
            fontFamily: "var(--font-mono)",
          }}
        >
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          {message.traceId && (
            <span style={{ opacity: 0.7 }}>
              ID: {message.traceId.slice(0, 8)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
