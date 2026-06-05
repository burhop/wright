import { useState, useRef, useEffect } from "react";
import type { KeyboardEvent } from "react";

interface MessageComposerProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageComposer({
  onSend,
  disabled = false,
}: MessageComposerProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      data-testid="message-composer"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-sm)",
        backgroundColor: "var(--color-surface-subtle)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-md)",
        width: "100%",
        boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
      }}
    >
      <textarea
        ref={textareaRef}
        data-testid="composer-input"
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          disabled ? "Streaming response..." : "Type your engineering query..."
        }
        disabled={disabled}
        style={{
          width: "100%",
          resize: "none",
          backgroundColor: "transparent",
          color: "var(--color-primary)",
          fontSize: "1rem",
          lineHeight: "1.5",
          fontFamily: "var(--font-ui)",
          minHeight: "24px",
          maxHeight: "200px",
          overflowY: "auto",
        }}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
        }}
      >
        <button
          data-testid="composer-send"
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          style={{
            padding: "var(--space-sm) var(--space-lg)",
            borderRadius: "var(--radius-md)",
            backgroundColor:
              text.trim() && !disabled
                ? "var(--color-secondary)"
                : "var(--color-surface)",
            color:
              text.trim() && !disabled
                ? "var(--color-neutral)"
                : "var(--color-secondary)",
            fontWeight: "600",
            fontFamily: "var(--font-ui)",
            fontSize: "0.875rem",
            transition: "all 0.2s ease",
            cursor: text.trim() && !disabled ? "pointer" : "default",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default MessageComposer;
