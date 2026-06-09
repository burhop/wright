import type { VaultFile } from "../../services/agent-service";

interface AttachmentPillProps {
  file: VaultFile;
  onRemove: (fileId: string) => void;
}

export function AttachmentPill({ file, onRemove }: AttachmentPillProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-xs)",
        padding: "var(--space-xs) var(--space-sm)",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        fontSize: "0.75rem",
        color: "var(--color-primary)",
      }}
    >
      <div
        style={{
          width: "24px",
          height: "24px",
          borderRadius: "var(--radius-sm)",
          overflow: "hidden",
          backgroundColor: "var(--color-surface-subtle)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {file.mime_type.startsWith("image/") ? (
          <img
            src={file.url}
            alt={file.filename}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <span style={{ fontSize: "10px" }}>📄</span>
        )}
      </div>
      <span
        style={{
          maxWidth: "100px",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {file.filename}
      </span>
      <button
        onClick={() => onRemove(file.file_id)}
        style={{
          background: "none",
          border: "none",
          color: "var(--color-secondary)",
          cursor: "pointer",
          padding: "2px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        title="Remove attachment"
      >
        ×
      </button>
    </div>
  );
}
