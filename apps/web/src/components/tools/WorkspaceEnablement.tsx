import type { WorkspaceInfo } from "../../services/workspace-service";

interface WorkspaceEnablementProps {
  serverId: string;
  serverName: string;
  isInstalled: boolean;
  workspaces: WorkspaceInfo[];
  showWorkspaces: boolean;
  togglingWorkspaceId: string | null;
  onToggleVisible: () => void;
  onToggleWorkspace: (workspace: WorkspaceInfo, isEnabled: boolean) => void;
}

function workspaceDisplayName(path: string) {
  const parts = path.split("/");
  return parts[parts.length - 1] || path;
}

function workspaceHasServer(
  workspace: WorkspaceInfo,
  serverId: string,
  serverName: string,
) {
  return (
    workspace.enabled_tools?.includes(serverId) ||
    workspace.enabled_tools?.includes(serverName) ||
    false
  );
}

export function WorkspaceEnablement({
  serverId,
  serverName,
  isInstalled,
  workspaces,
  showWorkspaces,
  togglingWorkspaceId,
  onToggleVisible,
  onToggleWorkspace,
}: WorkspaceEnablementProps) {
  if (!isInstalled) {
    return null;
  }

  const enabledCount = workspaces.filter((workspace) =>
    workspaceHasServer(workspace, serverId, serverName),
  ).length;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-xs)",
        borderTop: "1px solid var(--color-border)",
        paddingTop: "var(--space-sm)",
        marginTop: "var(--space-xs)",
        textAlign: "left",
      }}
    >
      <button
        type="button"
        onClick={onToggleVisible}
        data-testid={`server-card-workspaces-toggle-${serverId}`}
        style={{
          fontSize: "0.72rem",
          color: "var(--color-secondary)",
          cursor: "pointer",
          border: "none",
          background: "none",
          textAlign: "left",
          padding: "0",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.5px",
          transition: "color var(--transition-fast)",
        }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.color = "var(--color-primary)")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.color = "var(--color-secondary)")
        }
      >
        <span>
          {showWorkspaces
            ? "Hide Workspaces"
            : `Configure Workspaces (${enabledCount}/${workspaces.length})`}
        </span>
      </button>

      {showWorkspaces && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-xs)",
            maxHeight: "120px",
            overflowY: "auto",
            paddingRight: "4px",
            marginTop: "var(--space-xs)",
          }}
        >
          {workspaces.length === 0 ? (
            <span
              style={{
                fontSize: "0.8rem",
                color: "var(--color-secondary)",
                fontStyle: "italic",
              }}
            >
              No workspaces available.
            </span>
          ) : (
            workspaces.map((workspace) => {
              const isEnabled = workspaceHasServer(
                workspace,
                serverId,
                serverName,
              );
              const isToggling = togglingWorkspaceId === workspace.workspace_id;

              return (
                <label
                  key={workspace.workspace_id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "4px var(--space-md)",
                    backgroundColor: isEnabled
                      ? "rgba(56, 189, 248, 0.04)"
                      : "var(--color-surface-card-subtle)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.78rem",
                    cursor: isToggling ? "not-allowed" : "pointer",
                    transition: "all var(--transition-fast)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-sm)",
                      overflow: "hidden",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      disabled={isToggling}
                      onChange={(event) =>
                        onToggleWorkspace(workspace, event.target.checked)
                      }
                      style={{
                        accentColor: "var(--color-secondary)",
                        cursor: "pointer",
                      }}
                    />
                    <span
                      style={{
                        fontWeight: 500,
                        color: isEnabled
                          ? "var(--color-primary)"
                          : "var(--color-secondary)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {workspaceDisplayName(workspace.local_path)}
                    </span>
                  </div>
                  {isToggling && (
                    <span
                      style={{
                        fontSize: "0.7rem",
                        color: "var(--color-secondary)",
                      }}
                    >
                      Updating...
                    </span>
                  )}
                </label>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
