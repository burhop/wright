import { useEffect, useId, useRef, useState } from "react";

interface WorkspaceWorkflowDialogProps {
  workspaceName: string;
  loadWorkflows: () => Promise<Array<{ path: string; name: string }>>;
  onOpen: (path: string) => void;
  onNew: () => Promise<void>;
  onClose: () => void;
}

/** A workspace file chooser; source storage and the existing editor own edits. */
export function WorkspaceWorkflowDialog({
  workspaceName,
  loadWorkflows,
  onOpen,
  onNew,
  onClose,
}: WorkspaceWorkflowDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const mounted = useRef(false);
  const titleId = useId();
  const [files, setFiles] = useState<Array<{ path: string; name: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    mounted.current = true;
    const element = dialog.current;
    element?.showModal();
    return () => {
      mounted.current = false;
      element?.close();
    };
  }, []);

  useEffect(() => {
    let current = true;
    setLoading(true);
    setError("");
    loadWorkflows()
      .then((choices) => {
        if (current) setFiles(choices);
      })
      .catch((failure: unknown) => {
        if (current)
          setError(
            failure instanceof Error
              ? failure.message
              : "Unable to list saved workflows. Close and reopen to retry.",
          );
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [loadWorkflows]);

  const create = async () => {
    setCreating(true);
    setError("");
    try {
      await onNew();
      if (mounted.current) onClose();
    } catch (failure) {
      if (mounted.current)
        setError(
          failure instanceof Error
            ? failure.message
            : "Could not create a workflow.",
        );
    } finally {
      if (mounted.current) setCreating(false);
    }
  };

  return (
    <dialog
      ref={dialog}
      className="native-workflow-dialog"
      aria-labelledby={titleId}
      data-testid="workspace-workflow-picker"
      onCancel={onClose}
      style={{
        color: "var(--color-primary)",
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md, 12px)",
        padding: 24,
        width: "min(480px, 90vw)",
        maxHeight: "80vh",
        margin: "auto",
      }}
    >
      <h2 id={titleId}>Workflows</h2>
      <p>{workspaceName}</p>
      {loading && <p role="status">Loading saved workflows…</p>}
      {!loading && !error && files.length === 0 && <p>No saved workflows yet.</p>}
      <div style={{ display: "grid", gap: 8, maxHeight: "45vh", overflow: "auto" }}>
        {files.map((file) => (
          <button
            type="button"
            key={file.path}
            className="recovery-button recovery-button--secondary"
            disabled={creating}
            onClick={() => {
              onOpen(file.path);
              onClose();
            }}
          >
            {file.name.replace(/\.workflow\.wflow$/i, "")}
          </button>
        ))}
      </div>
      {error && <p role="alert">{error}</p>}
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button
          type="button"
          className="recovery-button"
          disabled={creating}
          onClick={() => void create()}
        >
          {creating ? "Creating…" : "New workflow"}
        </button>
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </dialog>
  );
}
