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

interface MessageComposerProps {
  onSend: (message: string, attachments?: string[]) => void;
  disabled?: boolean;
  isStreaming?: boolean;
  onCancel?: () => void;
}

export function MessageComposer({
  onSend,
  disabled = false,
  isStreaming = false,
  onCancel,
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

    // Check for "/" or "@" typed at the beginning of a word
    const match = textBeforeCursor.match(/(?:^|\s)([@\/])(\w*)$/);
    if (match) {
      setMenuPrefix(match[1]);
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
      /(?:^|\s)([@\/])(\w*)$/,
      ` $1${cmd.name} `,
    );
    setText(newTextBeforeCursor.trimStart() + textAfterCursor);
    setShowMenu(false);
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
        boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
        position: "relative",
      }}
    >
      {showMenu && (
        <CommandMenu
          commands={commands}
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
          boxSizing: "border-box",
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
          padding: "0 2px 2px 2px",
        }}
      >
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setShowPlusMenu(!showPlusMenu)}
            title="Add Context or Media"
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
              style={{
                position: "absolute",
                bottom: "36px",
                left: "0",
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-xs)",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                zIndex: 1000,
                minWidth: "150px",
                display: "flex",
                flexDirection: "column",
                gap: "2px",
              }}
            >
              <button
                onClick={() => {
                  setMenuPrefix("/");
                  setMenuFilter("");
                  setMenuPosition({
                    top:
                      containerRef.current?.getBoundingClientRect().top ||
                      0 - 20,
                    left:
                      containerRef.current?.getBoundingClientRect().left ||
                      0 + 40,
                  });
                  setShowMenu(true);
                  setShowPlusMenu(false);
                }}
                style={{
                  padding: "8px",
                  textAlign: "left",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  borderRadius: "4px",
                }}
              >
                ⚡ Actions
              </button>
              <button
                onClick={() => {
                  setMenuPrefix("@");
                  setMenuFilter("");
                  setMenuPosition({
                    top:
                      containerRef.current?.getBoundingClientRect().top ||
                      0 - 20,
                    left:
                      containerRef.current?.getBoundingClientRect().left ||
                      0 + 40,
                  });
                  setShowMenu(true);
                  setShowPlusMenu(false);
                }}
                style={{
                  padding: "8px",
                  textAlign: "left",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  borderRadius: "4px",
                }}
              >
                👤 @ Mentions
              </button>
              <label
                style={{
                  padding: "8px",
                  textAlign: "left",
                  cursor: "pointer",
                  borderRadius: "4px",
                  display: "block",
                }}
              >
                🖼️ Media
                <input
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

        <div style={{ display: "flex", gap: "var(--space-xs)", alignItems: "center" }}>
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
                (text.trim() || attachments.length > 0)
                  ? "var(--color-secondary)"
                  : "var(--color-surface)",
              color:
                (text.trim() || attachments.length > 0)
                  ? "var(--color-neutral)"
                  : "var(--color-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              cursor:
                (text.trim() || attachments.length > 0)
                  ? "pointer"
                  : "default",
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
