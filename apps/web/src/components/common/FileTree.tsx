import { useState } from "react";
import type { WorkspaceFile } from "../../store/types";

interface FileTreeProps {
  node: WorkspaceFile;
  onFileClick?: (path: string) => void;
  onCreate?: (
    parentPath: string,
    name: string,
    type: "file" | "directory",
  ) => Promise<void>;
  onDelete?: (path: string) => Promise<void>;
  onRename?: (path: string, newPath: string) => Promise<void>;
  onMove?: (sourcePath: string, destPath: string) => Promise<void>;
  /** Set of expanded directory paths — when provided, tree expansion is controlled by parent */
  expandedPaths?: Set<string>;
  /** Called when a directory is toggled — required when expandedPaths is provided */
  onToggleExpand?: (path: string) => void;
}

export function FileTree({
  node,
  onFileClick,
  onCreate,
  onDelete,
  onRename,
  onMove,
  expandedPaths,
  onToggleExpand,
}: FileTreeProps) {
  // If expandedPaths is provided, use controlled expansion; otherwise use local state
  const isControlled = expandedPaths !== undefined;
  const [localIsOpen, setLocalIsOpen] = useState(false);
  const isOpen = isControlled ? expandedPaths.has(node.path) : localIsOpen;
  const [isHovered, setIsHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState<"file" | "directory" | null>(
    null,
  );
  const [inputValue, setInputValue] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isDir = node.type === "directory";

  const handleClick = () => {
    if (isDir) {
      if (isControlled && onToggleExpand) {
        onToggleExpand(node.path);
      } else {
        setLocalIsOpen(!isOpen);
      }
    } else if (onFileClick) {
      onFileClick(node.path);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) {
      setIsCreating(null);
      return;
    }
    setErrorMsg(null);
    try {
      if (onCreate && isCreating) {
        await onCreate(node.path, inputValue.trim(), isCreating);
        if (isControlled && onToggleExpand && !isOpen) {
          onToggleExpand(node.path);
        } else {
          setLocalIsOpen(true);
        }
      }
      setInputValue("");
      setIsCreating(null);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Creation failed");
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || inputValue.trim() === node.name) {
      setIsEditing(false);
      return;
    }
    setErrorMsg(null);
    try {
      if (onRename) {
        const parts = node.path.split("/");
        parts.pop();
        const parentDir = parts.join("/");
        const newPath =
          parentDir === ""
            ? `/${inputValue.trim()}`
            : `${parentDir}/${inputValue.trim()}`;
        await onRename(node.path, newPath);
      }
      setIsEditing(false);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Rename failed");
    }
  };

  // Git Status Styling
  const getStatusColor = () => {
    switch (node.git_status) {
      case "U":
        return "var(--color-success, #22c55e)";
      case "M":
        return "var(--color-warning, #eab308)";
      case "A":
        return "var(--color-accent, #3b82f6)";
      case "D":
        return "var(--color-error, #ef4444)";
      default:
        return "var(--color-primary)";
    }
  };

  const getStatusBadge = () => {
    if (node.git_status === "Clean") return null;
    return (
      <span
        style={{
          fontSize: "0.7rem",
          fontWeight: "bold",
          color: getStatusColor(),
          marginLeft: "var(--space-xs)",
          opacity: 0.8,
        }}
      >
        {node.git_status}
      </span>
    );
  };

  // Drag and Drop handlers
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", node.path);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    if (isDir) {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    if (!isDir) return;
    e.preventDefault();
    const sourcePath = e.dataTransfer.getData("text/plain");
    if (sourcePath && sourcePath !== node.path) {
      const fileName = sourcePath.split("/").pop() || "";
      const destPath =
        node.path === "/" ? `/${fileName}` : `${node.path}/${fileName}`;
      if (sourcePath !== destPath && onMove) {
        try {
          await onMove(sourcePath, destPath);
        } catch (err: unknown) {
          console.error("Drag and drop move failed:", err);
        }
      }
    }
  };

  return (
    <div
      style={{
        fontFamily: "var(--font-ui)",
        fontSize: "0.85rem",
        color: getStatusColor(),
        textAlign: "left",
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Node row */}
      <div
        draggable={node.path !== "/"}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "var(--space-xs) var(--space-sm)",
          cursor: "pointer",
          borderRadius: "var(--radius-sm)",
          backgroundColor: isHovered
            ? "rgba(255, 255, 255, 0.05)"
            : "transparent",
          transition: "background-color 0.15s ease",
          userSelect: "none",
          textDecoration: node.git_status === "D" ? "line-through" : "none",
        }}
      >
        {isEditing ? (
          <form
            onSubmit={handleRenameSubmit}
            style={{ display: "flex", width: "100%" }}
          >
            <input
              autoFocus
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onBlur={() => setIsEditing(false)}
              onClick={(e) => e.stopPropagation()}
              style={{
                flex: 1,
                backgroundColor: "var(--color-surface-subtle)",
                color: "var(--color-primary)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-xs)",
                padding: "1px var(--space-xs)",
                fontSize: "0.8rem",
                outline: "none",
              }}
            />
          </form>
        ) : (
          <div
            data-testid={`file-node-${node.path}`}
            onClick={handleClick}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xs)",
              flex: 1,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            <span style={{ fontSize: "0.75rem", opacity: 0.7 }}>
              {isDir ? (isOpen ? "▼" : "▶") : "📄"}
            </span>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
              {node.name}
            </span>
            {getStatusBadge()}
          </div>
        )}

        {/* Hover action toolbar */}
        {isHovered && !isEditing && node.path !== "/" && (
          <div
            style={{
              display: "flex",
              gap: "var(--space-xs)",
              alignItems: "center",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {isDir && (
              <>
                <button
                  title="New File"
                  onClick={() => {
                    setIsCreating("file");
                    setInputValue("");
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--color-secondary)",
                    cursor: "pointer",
                    padding: "2px",
                    fontSize: "0.8rem",
                  }}
                >
                  📄+
                </button>
                <button
                  title="New Folder"
                  onClick={() => {
                    setIsCreating("directory");
                    setInputValue("");
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--color-secondary)",
                    cursor: "pointer",
                    padding: "2px",
                    fontSize: "0.8rem",
                  }}
                >
                  📁+
                </button>
              </>
            )}
            <button
              title="Rename"
              onClick={() => {
                setInputValue(node.name);
                setIsEditing(true);
              }}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-secondary)",
                cursor: "pointer",
                padding: "2px",
                fontSize: "0.8rem",
              }}
            >
              ✏️
            </button>
            <button
              title="Delete"
              onClick={async () => {
                if (
                  onDelete &&
                  confirm(`Are you sure you want to delete ${node.name}?`)
                ) {
                  await onDelete(node.path);
                }
              }}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-error, #ef4444)",
                cursor: "pointer",
                padding: "2px",
                fontSize: "0.8rem",
              }}
            >
              🗑️
            </button>
          </div>
        )}
      </div>

      {errorMsg && (
        <div
          style={{
            color: "var(--color-error, #ef4444)",
            fontSize: "0.7rem",
            paddingLeft: "var(--space-md)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Creation form */}
      {isCreating && (
        <div style={{ paddingLeft: "var(--space-lg)" }}>
          <form
            onSubmit={handleCreateSubmit}
            style={{ display: "flex", padding: "var(--space-xs) 0" }}
          >
            <span
              style={{ fontSize: "0.8rem", marginRight: "var(--space-xs)" }}
            >
              {isCreating === "directory" ? "📁" : "📄"}
            </span>
            <input
              autoFocus
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onBlur={() => setIsCreating(null)}
              style={{
                flex: 1,
                backgroundColor: "var(--color-surface-subtle)",
                color: "var(--color-primary)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-xs)",
                padding: "1px var(--space-xs)",
                fontSize: "0.8rem",
                outline: "none",
              }}
            />
          </form>
        </div>
      )}

      {/* Child directories/files */}
      {isDir && isOpen && node.children && (
        <div
          style={{
            paddingLeft: "var(--space-md)",
            borderLeft: "1px solid var(--color-border)",
            marginLeft: "var(--space-sm)",
          }}
        >
          {node.children.map((child) => (
            <FileTree
              key={child.path}
              node={child}
              onFileClick={onFileClick}
              onCreate={onCreate}
              onDelete={onDelete}
              onRename={onRename}
              onMove={onMove}
              expandedPaths={expandedPaths}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default FileTree;
