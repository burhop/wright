import { useState, useRef, useEffect } from "react";
import type {
  KeyboardEvent,
  ChangeEvent,
  DragEvent,
  ClipboardEvent,
} from "react";
import { agentService } from "../../services/agent-service";
import type { AgentCommand, VaultFile } from "../../services/agent-service";
import { CommandMenu } from "./CommandMenu";
import { AttachmentPill } from "./AttachmentPill";
import { workspaceService } from "../../services/workspace-service";

interface MessageComposerProps {
  onSend: (message: string, attachments?: string[]) => void;
  disabled?: boolean;
  isStreaming?: boolean;
  onCancel?: () => void;
  sessionId?: string;
}

function getMcpStatusTone(status: string): { label: string; color: string } {
  if (status === "ok") return { label: "Active", color: "#22c55e" };
  if (status === "warning" || status === "mismatch") {
    return {
      label: status === "mismatch" ? "Mismatch" : "Needs attention",
      color: "#f59e0b",
    };
  }
  return { label: "Error", color: "#ef4444" };
}

export function MessageComposer({
  onSend,
  disabled = false,
  isStreaming = false,
  onCancel,
  sessionId,
}: MessageComposerProps) {
  const [text, setText] = useState("");
  const [attachments, setAttachments] = useState<VaultFile[]>([]);
  const [commands, setCommands] = useState<AgentCommand[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [showMenu, setShowMenu] = useState(false);
  const [menuFilter, setMenuFilter] = useState("");
  const [menuPrefix, setMenuPrefix] = useState("/");
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const [showPlusMenu, setShowPlusMenu] = useState(false);
  const [mcpStatus, setMcpStatus] = useState<{
    status: string;
    message: string;
    running_mcps?: {
      name: string;
      status: string;
      error_message?: string | null;
    }[];
  } | null>(null);
  const [showStatusPopup, setShowStatusPopup] = useState(false);
  const [workspaceFiles, setWorkspaceFiles] = useState<
    { name: string; path: string }[]
  >([]);

  const fetchWorkspaceFiles = async () => {
    if (!sessionId) return;
    try {
      const tree = await workspaceService.getWorkspaceFiles(sessionId);
      const getFilesFromTree = (
        node: any,
      ): { name: string; path: string }[] => {
        let list: { name: string; path: string }[] = [];
        if (node.type === "file") {
          list.push({ name: node.name, path: node.path });
        }
        if (node.children) {
          for (const child of node.children) {
            list = list.concat(getFilesFromTree(child));
          }
        }
        return list;
      };
      setWorkspaceFiles(getFilesFromTree(tree));
    } catch (err) {
      console.error("Failed to fetch workspace files for autocomplete", err);
    }
  };

  useEffect(() => {
    // Fetch available commands on mount
    agentService
      .getCommands()
      .then((cmds) => setCommands(cmds))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [text]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowPlusMenu(false);
      }
    };
    if (showPlusMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showPlusMenu]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowStatusPopup(false);
      }
    };
    if (showStatusPopup) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showStatusPopup]);

  useEffect(() => {
    if (!sessionId) {
      setMcpStatus(null);
      return;
    }

    let isMounted = true;
    const fetchStatus = async () => {
      try {
        const status = await workspaceService.getMcpStatus(sessionId);
        if (isMounted) {
          setMcpStatus(status);
        }
      } catch (err) {
        console.error("Failed to fetch MCP status in composer", err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId]);

  const handleSend = () => {
    if ((text.trim() || attachments.length > 0) && !disabled) {
      onSend(
        text.trim(),
        attachments.map((a) => a.file_id),
      );
      setText("");
      setAttachments([]);
      setShowMenu(false);
      setShowPlusMenu(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showMenu) {
      if (["ArrowUp", "ArrowDown", "Enter"].includes(e.key)) {
        // Handled by CommandMenu global listener
        return;
      }
      if (e.key === "Escape") {
        setShowMenu(false);
      }
    } else {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    }
  };

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setText(val);

    const cursorPosition = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursorPosition);

    // Check for "@file " followed by search filter
    const fileMatch = textBeforeCursor.match(/(?:^|\s)(@file\s)(\S*)$/);
    if (fileMatch) {
      setMenuPrefix(fileMatch[1]); // "@file "
      setMenuFilter(fileMatch[2]);
      if (workspaceFiles.length === 0) {
        fetchWorkspaceFiles();
      }
      if (textareaRef.current) {
        const rect = textareaRef.current.getBoundingClientRect();
        setMenuPosition({
          top: rect.top - 10,
          left: rect.left + 20,
        });
      }
      setShowMenu(true);
      return;
    }

    // Check for "@" followed by search filter (can contain slashes, dots, hyphens)
    const atMatch = textBeforeCursor.match(/(?:^|\s)(@)(\S*)$/);
    if (atMatch) {
      setMenuPrefix(atMatch[1]); // "@"
      setMenuFilter(atMatch[2]);
      if (workspaceFiles.length === 0) {
        fetchWorkspaceFiles();
      }
      if (textareaRef.current) {
        const rect = textareaRef.current.getBoundingClientRect();
        setMenuPosition({
          top: rect.top - 10,
          left: rect.left + 20,
        });
      }
      setShowMenu(true);
      return;
    }

    // Check for "/" typed at the beginning of a word
    const match = textBeforeCursor.match(/(?:^|\s)(\/)(\w*)$/);
    if (match) {
      setMenuPrefix(match[1]); // "/"
      setMenuFilter(match[2]);

      if (textareaRef.current) {
        const rect = textareaRef.current.getBoundingClientRect();
        // Approximate position
        setMenuPosition({
          top: rect.top - 10,
          left: rect.left + 20,
        });
      }
      setShowMenu(true);
    } else {
      setShowMenu(false);
    }
  };

  const handleCommandSelect = (cmd: AgentCommand) => {
    // Replace the prefix and filter with the full command
    const cursorPosition = textareaRef.current?.selectionStart || text.length;
    const textBeforeCursor = text.slice(0, cursorPosition);
    const textAfterCursor = text.slice(cursorPosition);

    const newTextBeforeCursor = textBeforeCursor.replace(
      /(?:^|\s)([@\/]|@file\s)(\S*)$/,
      `$1${cmd.name} `,
    );
    const updatedText = newTextBeforeCursor.trimStart() + textAfterCursor;
    setText(updatedText);

    if (cmd.name === "file" && cmd.prefix === "@") {
      setMenuPrefix("@file ");
      setMenuFilter("");
      fetchWorkspaceFiles();
      setShowMenu(true);
    } else {
      setShowMenu(false);
    }
    textareaRef.current?.focus();
  };

  const openCommandMenu = (prefix: "/" | "@") => {
    const rect = containerRef.current?.getBoundingClientRect();
    setMenuPrefix(prefix);
    setMenuFilter("");
    setMenuPosition({
      top: (rect?.top ?? 0) - 20,
      left: (rect?.left ?? 0) + 40,
    });

    if (prefix === "@" && workspaceFiles.length === 0) {
      void fetchWorkspaceFiles();
    }

    setShowMenu(true);
    setShowPlusMenu(false);
    textareaRef.current?.focus();
  };

  const uploadFile = async (file: File) => {
    try {
      const uploaded = await agentService.uploadFile(file);
      setAttachments((prev) => [...prev, uploaded]);
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload file. Please try again.");
    }
  };

  const handlePaste = async (e: ClipboardEvent<HTMLTextAreaElement>) => {
    if (e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile();
          if (file) {
            e.preventDefault();
            await uploadFile(file);
          }
        }
      }
    }
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i];
        if (file.type.startsWith("image/")) {
          await uploadFile(file);
        }
      }
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const mcpTone = mcpStatus ? getMcpStatusTone(mcpStatus.status) : null;

  return (
    <div
      ref={containerRef}
      data-testid="message-composer"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "4px",
        backgroundColor: "var(--color-surface-subtle)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "2px",
        width: "100%",
        minWidth: 0,
        boxSizing: "border-box",
        boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {showMenu && (
        <CommandMenu
          commands={
            menuPrefix === "@" || menuPrefix === "@file "
              ? workspaceFiles.map((f) => ({
                  name: f.path,
                  description: "",
                  prefix: menuPrefix,
                }))
              : commands
          }
          filter={menuFilter}
          prefix={menuPrefix}
          onSelect={handleCommandSelect}
          position={menuPosition}
        />
      )}

      {attachments.length > 0 && (
        <div
          style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-xs)" }}
        >
          {attachments.map((file) => (
            <AttachmentPill
              key={file.file_id}
              file={file}
              onRemove={(id) =>
                setAttachments((prev) => prev.filter((a) => a.file_id !== id))
              }
            />
          ))}
        </div>
      )}

      <textarea
        ref={textareaRef}
        data-testid="composer-input"
        rows={1}
        value={text}
        onChange={handleTextChange}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        placeholder="Type your engineering query... (or paste an image)"
        style={{
          width: "100%",
          minWidth: 0,
          boxSizing: "border-box",
          display: "block",
          resize: "none",
          backgroundColor: "transparent",
          color: "var(--color-primary)",
          fontSize: "0.875rem",
          lineHeight: "1.4",
          fontFamily: "var(--font-ui)",
          minHeight: "24px",
          maxHeight: "300px",
          overflowY: "auto",
          border: "none",
          outline: "none",
          padding: "6px 8px",
        }}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-xs)",
          padding: "0 2px 2px 2px",
          minWidth: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-xs)",
          }}
        >
          <div style={{ position: "relative" }}>
            <button
              type="button"
              aria-label="Add context"
              aria-expanded={showPlusMenu}
              onClick={() => setShowPlusMenu(!showPlusMenu)}
              title="Add context"
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "50%",
                border: "1px solid var(--color-border)",
                backgroundColor: "var(--color-surface)",
                color: "var(--color-secondary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              +
            </button>

            {showPlusMenu && (
              <div
                role="menu"
                aria-label="Add context menu"
                data-testid="composer-plus-menu"
                style={{
                  position: "absolute",
                  bottom: "36px",
                  left: "0",
                  backgroundColor: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "6px",
                  boxShadow: "0 8px 24px rgba(0, 0, 0, 0.28)",
                  zIndex: 1000,
                  minWidth: "250px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                }}
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => openCommandMenu("/")}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "28px 1fr",
                    gap: "8px",
                    alignItems: "center",
                    padding: "8px",
                    textAlign: "left",
                    background: "transparent",
                    border: "none",
                    color: "var(--color-text)",
                    cursor: "pointer",
                    borderRadius: "6px",
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{ color: "var(--color-primary)", fontWeight: 700 }}
                  >
                    /
                  </span>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: "block", fontWeight: 600 }}>
                      Command
                    </span>
                    <span
                      style={{
                        display: "block",
                        color: "var(--color-text-muted)",
                        fontSize: "0.75rem",
                      }}
                    >
                      Run a Hermes or Wright slash command
                    </span>
                  </span>
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => openCommandMenu("@")}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "28px 1fr",
                    gap: "8px",
                    alignItems: "center",
                    padding: "8px",
                    textAlign: "left",
                    background: "transparent",
                    border: "none",
                    color: "var(--color-text)",
                    cursor: "pointer",
                    borderRadius: "6px",
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{ color: "var(--color-primary)", fontWeight: 700 }}
                  >
                    @
                  </span>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: "block", fontWeight: 600 }}>
                      Workspace File
                    </span>
                    <span
                      style={{
                        display: "block",
                        color: "var(--color-text-muted)",
                        fontSize: "0.75rem",
                      }}
                    >
                      Reference a file from this workspace
                    </span>
                  </span>
                </button>
                <label
                  role="menuitem"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "28px 1fr",
                    gap: "8px",
                    alignItems: "center",
                    padding: "8px",
                    textAlign: "left",
                    color: "var(--color-text)",
                    cursor: "pointer",
                    borderRadius: "6px",
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{ color: "var(--color-primary)", fontWeight: 700 }}
                  >
                    img
                  </span>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: "block", fontWeight: 600 }}>
                      Image Upload
                    </span>
                    <span
                      style={{
                        display: "block",
                        color: "var(--color-text-muted)",
                        fontSize: "0.75rem",
                      }}
                    >
                      Attach screenshots or other image files
                    </span>
                  </span>
                  <input
                    aria-label="Upload image"
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    multiple
                    onChange={async (e) => {
                      if (e.target.files) {
                        for (let i = 0; i < e.target.files.length; i++) {
                          await uploadFile(e.target.files[i]);
                        }
                      }
                      setShowPlusMenu(false);
                    }}
                  />
                </label>
              </div>
            )}
          </div>

          {mcpStatus && (
            <div style={{ position: "relative" }}>
              <button
                data-testid="mcp-status-indicator"
                onClick={() => setShowStatusPopup(!showStatusPopup)}
                style={{
                  height: "20px",
                  padding: "0 8px",
                  borderRadius: "10px",
                  border: "none",
                  backgroundColor: mcpTone?.color || "#ef4444",
                  color: "#ffffff",
                  fontSize: "0.65rem",
                  fontWeight: "bold",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  transition: "background-color 0.2s",
                }}
                title={mcpStatus.message}
              >
                MCP
              </button>

              {showStatusPopup && (
                <div
                  data-testid="mcp-status-popup"
                  style={{
                    position: "absolute",
                    bottom: "28px",
                    left: "0",
                    backgroundColor: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-sm)",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                    zIndex: 1001,
                    minWidth: "200px",
                    maxWidth: "300px",
                    fontSize: "0.75rem",
                    color: "var(--color-primary)",
                    textAlign: "left",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "4px",
                    }}
                  >
                    <strong
                      style={{
                        color: mcpTone?.color || "#ef4444",
                      }}
                    >
                      MCP Status: {mcpTone?.label || "Unknown"}
                    </strong>
                    <button
                      onClick={() => setShowStatusPopup(false)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--color-text-dim)",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                        padding: 0,
                      }}
                    ></button>
                  </div>
                  <div
                    style={{
                      lineHeight: "1.4",
                      color: "var(--color-secondary)",
                    }}
                  >
                    {mcpStatus.message}
                  </div>
                  {mcpStatus.running_mcps &&
                    mcpStatus.running_mcps.length > 0 && (
                      <div
                        style={{
                          marginTop: "12px",
                          borderTop: "1px solid var(--color-border)",
                          paddingTop: "8px",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: "bold",
                            marginBottom: "6px",
                            fontSize: "0.7rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            color: "var(--color-text-dim)",
                          }}
                        >
                          Running MCP Servers ({mcpStatus.running_mcps.length})
                        </div>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "6px",
                          }}
                        >
                          {mcpStatus.running_mcps.map((mcp, idx) => (
                            <div
                              key={idx}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                gap: "8px",
                              }}
                            >
                              <span
                                style={{
                                  fontWeight: 500,
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                  flex: 1,
                                }}
                                title={mcp.name}
                              >
                                {mcp.name}
                              </span>
                              <span
                                style={{
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  fontSize: "0.6rem",
                                  fontWeight: "bold",
                                  textTransform: "uppercase",
                                  backgroundColor:
                                    mcp.status === "active"
                                      ? "rgba(34, 197, 94, 0.1)"
                                      : mcp.status === "error"
                                        ? "rgba(239, 68, 68, 0.1)"
                                        : "rgba(245, 158, 11, 0.12)",
                                  color:
                                    mcp.status === "active"
                                      ? "#22c55e"
                                      : mcp.status === "error"
                                        ? "#ef4444"
                                        : "#f59e0b",
                                }}
                              >
                                {mcp.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              )}
            </div>
          )}
        </div>

        <div
          style={{
            display: "flex",
            gap: "var(--space-xs)",
            alignItems: "center",
          }}
        >
          {isStreaming && onCancel && (
            <button
              data-testid="composer-cancel"
              onClick={onCancel}
              title="Cancel execution"
              style={{
                width: "28px",
                height: "28px",
                flexShrink: 0,
                borderRadius: "50%",
                backgroundColor: "var(--color-surface)",
                color: "#ef4444",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.2s ease",
                cursor: "pointer",
                border: "1px solid var(--color-border)",
              }}
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              </svg>
            </button>
          )}

          <button
            data-testid="composer-send"
            onClick={handleSend}
            disabled={!text.trim() && attachments.length === 0}
            style={{
              width: "28px",
              height: "28px",
              flexShrink: 0,
              borderRadius: "50%",
              backgroundColor:
                text.trim() || attachments.length > 0
                  ? "var(--color-secondary)"
                  : "var(--color-surface)",
              color:
                text.trim() || attachments.length > 0
                  ? "var(--color-neutral)"
                  : "var(--color-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              cursor:
                text.trim() || attachments.length > 0 ? "pointer" : "default",
              border: "1px solid var(--color-border)",
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ marginLeft: "-2px" }}
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default MessageComposer;
