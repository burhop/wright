import React, { useState, useEffect } from "react";
import workspaceService from "../../services/workspace-service";

interface FileEditorProps {
  sessionId: string;
  filePath: string;
  initialContent: string;
  onSaveStatusChange?: (isDirty: boolean) => void;
}

export const FileEditor: React.FC<FileEditorProps> = ({
  sessionId,
  filePath,
  initialContent,
  onSaveStatusChange,
}) => {
  const [content, setContent] = useState(initialContent);
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    setContent(initialContent);
    setIsDirty(false);
    onSaveStatusChange?.(false);
  }, [initialContent, filePath]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setContent(val);
    if (val !== initialContent) {
      setIsDirty(true);
      onSaveStatusChange?.(true);
    } else {
      setIsDirty(false);
      onSaveStatusChange?.(false);
    }
  };

  const handleSave = async () => {
    if (!isDirty || saving) return;
    setSaving(true);
    setSaveError(null);
    try {
      await workspaceService.saveFileContent(sessionId, filePath, content);
      setIsDirty(false);
      onSaveStatusChange?.(false);
    } catch (err: unknown) {
      console.error("Failed to save file content:", err);
      setSaveError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const lineCount = content.split("\n").length;
  const lineNumbers = Array.from(
    { length: Math.max(lineCount, 1) },
    (_, i) => i + 1,
  ).join("\n");

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#1e1e1e",
      }}
    >
      {/* Editor status bar / controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "var(--space-xs) var(--space-md)",
          backgroundColor: "#252526",
          borderBottom: "1px solid var(--color-border)",
          fontFamily: "var(--font-ui)",
          fontSize: "0.75rem",
          color: "var(--color-secondary)",
        }}
      >
        <span>{filePath}</span>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-md)",
          }}
        >
          {saveError && (
            <span style={{ color: "var(--color-error)" }}>⚠️ {saveError}</span>
          )}
          {saving ? (
            <span>Saving...</span>
          ) : isDirty ? (
            <button
              onClick={handleSave}
              style={{
                backgroundColor: "var(--color-accent, #4f46e5)",
                color: "white",
                border: "none",
                borderRadius: "var(--radius-xs)",
                padding: "2px 8px",
                cursor: "pointer",
                fontWeight: "600",
              }}
            >
              Save Changes
            </button>
          ) : (
            <span style={{ opacity: 0.6 }}>Saved</span>
          )}
        </div>
      </div>

      {/* Editor Body */}
      <div
        style={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
          padding: "var(--space-sm) 0",
        }}
      >
        {/* Line Numbers */}
        <pre
          style={{
            margin: 0,
            padding: "0 var(--space-sm)",
            width: "40px",
            textAlign: "right",
            color: "#858585",
            fontSize: "0.85rem",
            fontFamily: "var(--font-code)",
            lineHeight: "1.5",
            borderRight: "1px solid #3c3c3c",
            userSelect: "none",
            overflow: "hidden",
          }}
        >
          {lineNumbers}
        </pre>

        {/* Text Area Editor */}
        <textarea
          value={content}
          onChange={handleContentChange}
          onBlur={handleSave}
          style={{
            flex: 1,
            margin: 0,
            padding: "0 var(--space-md)",
            backgroundColor: "transparent",
            color: "#d4d4d4",
            border: "none",
            outline: "none",
            fontSize: "0.85rem",
            fontFamily: "var(--font-code)",
            lineHeight: "1.5",
            resize: "none",
            whiteSpace: "pre",
            overflow: "auto",
          }}
        />
      </div>
    </div>
  );
};

export default FileEditor;
