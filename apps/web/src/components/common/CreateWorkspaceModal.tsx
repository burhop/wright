import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";

interface CreateWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (workspace: WorkspaceInfo) => void;
}

export function CreateWorkspaceModal({
  isOpen,
  onClose,
  onCreated,
}: CreateWorkspaceModalProps) {
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log("[DEBUG] CreateWorkspaceModal useEffect, isOpen:", isOpen);
    if (isOpen) {
      setName("");
      setError(null);
    }
  }, [isOpen]);

  const handleNameChange = (val: string) => {
    setName(val);
  };

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setError(null);

    if (!name.trim()) {
      setError("Workspace name is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const workspace = await workspaceService.createWorkspace(
        name.trim(),
      );
      setName("");
      onCreated(workspace);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create workspace";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setName("");
    setError(null);
    onClose();
  };

  return createPortal(
    <div
      data-testid="create-workspace-modal"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(4px)",
      }}
      onClick={handleClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "500px",
          maxWidth: "90vw",
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-xl)",
          padding: "var(--space-2xl)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-xl)",
        }}
        className="animate-fade-in-up"
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.4rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            Create Workspace
          </h2>
          <button
            onClick={handleClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--color-secondary)",
              fontSize: "1.2rem",
              cursor: "pointer",
              padding: "var(--space-xs)",
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-lg)",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
            }}
          >
            <label
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Workspace Name
            </label>
            <input
              id="workspace-name-input"
              type="text"
              placeholder="e.g., Turbine Blade FEA"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              autoFocus
              maxLength={100}
              style={{
                width: "100%",
                padding: "var(--space-md) var(--space-lg)",
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                color: "var(--color-primary)",
                fontSize: "0.95rem",
                outline: "none",
                transition: "border-color var(--transition-fast)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-secondary)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              padding: "var(--space-md) var(--space-lg)",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              border: "1px solid var(--color-error)",
              borderRadius: "var(--radius-md)",
              color: "var(--color-error)",
              fontSize: "0.85rem",
            }}
          >
            {error}
          </div>
        )}

        {/* Actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "var(--space-md)",
          }}
        >
          <button
            onClick={handleClose}
            style={{
              padding: "var(--space-md) var(--space-xl)",
              backgroundColor: "transparent",
              color: "var(--color-secondary)",
              fontWeight: 500,
              fontSize: "0.9rem",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-border)",
              cursor: "pointer",
              transition: "all var(--transition-fast)",
            }}
          >
            Cancel
          </button>
          <button
            id="workspace-create-submit"
            onClick={handleSubmit}
            disabled={isSubmitting}
            style={{
              padding: "var(--space-md) var(--space-xl)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              fontWeight: 600,
              fontSize: "0.9rem",
              borderRadius: "var(--radius-md)",
              border: "none",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              transition: "all var(--transition-smooth)",
              boxShadow: "var(--shadow-glow)",
              opacity: isSubmitting ? 0.7 : 1,
            }}
            onMouseEnter={(e) => {
              if (!isSubmitting)
                e.currentTarget.style.boxShadow = "var(--shadow-glow-active)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "var(--shadow-glow)";
            }}
          >
            {isSubmitting ? "Creating..." : "Create"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
