import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useLogger from "../../hooks/useLogger";
import { ToolRegistryIcon, FileVaultIcon } from "../common/Icons";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";
import { CreateWorkspaceModal } from "../common/CreateWorkspaceModal";

export function DashboardPage() {
  const logger = useLogger("DashboardPage");
  const navigate = useNavigate();

  const [recentWorkspaces, setRecentWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [showAllWorkspaces, setShowAllWorkspaces] = useState(false);
  const [allWorkspaces, setAllWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    logger.info("Dashboard Page loaded");
    const fetchWorkspaces = async () => {
      try {
        const recent = await workspaceService.getRecentWorkspaces();
        setRecentWorkspaces(recent);
      } catch (err) {
        logger.error("Failed to load workspaces", { err });
      }
    };
    fetchWorkspaces();
  }, [logger]);

  const getWorkspaceName = (w: WorkspaceInfo) => {
    if (w.workspace_name) return w.workspace_name;
    const parts = w.local_path.split("/");
    return parts[parts.length - 1] || w.local_path;
  };

  const formatTimeAgo = (ts: number) => {
    const diffSec = Math.floor(Date.now() / 1000) - ts;
    if (diffSec < 60) return "just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
  };

  const handleSelectWorkspace = async (w: WorkspaceInfo) => {
    console.log("[DEBUG] handleSelectWorkspace clicked:", w);
    try {
      console.log(
        "[DEBUG] calling workspaceService.activateWorkspace for session:",
        w.session_id,
      );
      await workspaceService.activateWorkspace(w.session_id);
      console.log(
        "[DEBUG] activateWorkspace returned. Navigating to:",
        `/workspace/${w.workspace_id}`,
      );
      navigate(`/workspace/${w.workspace_id}`);
    } catch (err) {
      console.error("[DEBUG] Failed to switch workspace:", err);
      logger.error("Failed to switch workspace", { err });
    }
  };

  const handleViewAllWorkspaces = async () => {
    if (!showAllWorkspaces) {
      try {
        const all = await workspaceService.getAllWorkspaces();
        setAllWorkspaces(all);
      } catch (err) {
        logger.error("Failed to load all workspaces", { err });
      }
    }
    setShowAllWorkspaces(!showAllWorkspaces);
  };

  const handleWorkspaceCreated = async (workspace: WorkspaceInfo) => {
    setIsCreateModalOpen(false);
    try {
      await workspaceService.activateWorkspace(workspace.session_id);
      navigate(`/workspace/${workspace.workspace_id}`);
    } catch (err) {
      logger.error("Failed to activate new workspace", { err });
      navigate(`/workspace/${workspace.workspace_id}`);
    }
  };

  return (
    <div
      data-testid="page-dashboard"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-2xl)",
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "var(--space-2xl) var(--space-xl)",
      }}
      className="animate-fade-in-up"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-sm)",
        }}
      >
        <h1
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: "2.8rem",
            fontWeight: 700,
            color: "var(--color-primary)",
            textAlign: "left",
            letterSpacing: "-0.75px",
          }}
        >
          Welcome to Wright
        </h1>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "1.2rem",
            color: "var(--color-secondary)",
            textAlign: "left",
            maxWidth: "800px",
            lineHeight: 1.7,
          }}
        >
          A local-first multi-agent mechanical engineering appliance. Wright
          runs locally to orchestrate, analyze, and document your mechanical
          designs under complete privacy.
        </p>
      </div>

      {/* Workspace Panel */}
      <div
        className="glow-card"
        style={{
          padding: "var(--space-2xl)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-lg)",
          textAlign: "left",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          backgroundColor: "var(--color-surface)",
          boxShadow: "var(--shadow-lg)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h2
              style={{
                fontFamily: "var(--font-ui)",
                fontSize: "1.5rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Engineering Workspaces
            </h2>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.9rem",
                color: "var(--color-secondary)",
                marginTop: "2px",
              }}
            >
              Your project directories. Each workspace scopes tools, files, and
              agent conversations.
            </p>
          </div>

          {/* Create Workspace Button */}
          <button
            id="create-workspace-btn"
            onClick={() => {
              console.log(
                "[DEBUG] Create Workspace button clicked, setting isCreateModalOpen to true",
              );
              setIsCreateModalOpen(true);
            }}
            style={{
              padding: "var(--space-md) var(--space-xl)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              fontWeight: 600,
              fontSize: "0.9rem",
              borderRadius: "var(--radius-lg)",
              border: "none",
              cursor: "pointer",
              transition: "all var(--transition-smooth)",
              boxShadow: "var(--shadow-glow)",
              whiteSpace: "nowrap",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = "var(--shadow-glow-active)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "var(--shadow-glow)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            + Create Workspace
          </button>
        </div>

        {/* Recent Workspaces List */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
            marginTop: "var(--space-xs)",
          }}
        >
          <span
            style={{
              fontSize: "0.75rem",
              textTransform: "uppercase",
              fontWeight: 600,
              color: "var(--color-secondary)",
              letterSpacing: "1px",
            }}
          >
            Recently Opened
          </span>

          {recentWorkspaces.length === 0 ? (
            <div
              style={{
                padding: "var(--space-xl)",
                backgroundColor: "var(--color-surface-subtle)",
                borderRadius: "var(--radius-lg)",
                textAlign: "center",
                border: "1px dashed var(--color-border)",
              }}
            >
              <span
                style={{ fontSize: "0.95rem", color: "var(--color-secondary)" }}
              >
                No workspaces yet. Click{" "}
                <strong style={{ color: "var(--color-primary)" }}>
                  + Create Workspace
                </strong>{" "}
                above to get started.
              </span>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs)",
              }}
            >
              {recentWorkspaces.map((w) => (
                <div
                  key={w.workspace_id}
                  onClick={() => handleSelectWorkspace(w)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "var(--space-lg) var(--space-xl)",
                    backgroundColor: "var(--color-surface-subtle)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-lg)",
                    cursor: "pointer",
                    transition: "all var(--transition-smooth)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor =
                      "var(--color-secondary)";
                    e.currentTarget.style.boxShadow = "var(--shadow-glow)";
                    e.currentTarget.style.transform = "translateX(2px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-border)";
                    e.currentTarget.style.boxShadow = "none";
                    e.currentTarget.style.transform = "translateX(0)";
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-md)",
                    }}
                  >
                    <div style={{ color: "var(--color-secondary)" }}>
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                      </svg>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "2px",
                        textAlign: "left",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "1rem",
                          fontWeight: 600,
                          color: "var(--color-primary)",
                        }}
                      >
                        {getWorkspaceName(w)}
                      </span>
                      <span
                        style={{
                          fontSize: "0.8rem",
                          color: "var(--color-secondary)",
                        }}
                      >
                        {w.local_path}
                      </span>
                    </div>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-md)",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.8rem",
                        color: "var(--color-secondary)",
                      }}
                    >
                      {formatTimeAgo(w.updated_at)}
                    </span>
                    <span
                      style={{
                        color: "var(--color-secondary)",
                        fontSize: "0.9rem",
                      }}
                    >
                      →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* View All Workspaces */}
        {recentWorkspaces.length > 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-md)",
            }}
          >
            <button
              id="view-all-workspaces-btn"
              onClick={handleViewAllWorkspaces}
              style={{
                alignSelf: "flex-start",
                padding: "var(--space-sm) var(--space-lg)",
                backgroundColor: "transparent",
                color: "var(--color-secondary)",
                fontWeight: 500,
                fontSize: "0.85rem",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--color-border)",
                cursor: "pointer",
                transition: "all var(--transition-fast)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--color-secondary)";
                e.currentTarget.style.color = "var(--color-primary)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.color = "var(--color-secondary)";
              }}
            >
              {showAllWorkspaces
                ? "▲ Hide all workspaces"
                : "▼ View all workspaces"}
            </button>

            {showAllWorkspaces && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-xs)",
                  paddingLeft: "var(--space-md)",
                }}
              >
                {allWorkspaces.length === 0 ? (
                  <span
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--color-secondary)",
                      fontStyle: "italic",
                    }}
                  >
                    No workspaces found.
                  </span>
                ) : (
                  allWorkspaces.map((w) => (
                    <div
                      key={w.workspace_id}
                      onClick={() => handleSelectWorkspace(w)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "var(--space-md) var(--space-lg)",
                        backgroundColor: "rgba(255, 255, 255, 0.01)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-md)",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        transition: "all var(--transition-fast)",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor =
                          "var(--color-secondary)";
                        e.currentTarget.style.backgroundColor =
                          "rgba(56, 189, 248, 0.04)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor =
                          "var(--color-border)";
                        e.currentTarget.style.backgroundColor =
                          "rgba(255, 255, 255, 0.01)";
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "var(--space-sm)",
                        }}
                      >
                        <span
                          style={{
                            fontWeight: 600,
                            color: "var(--color-primary)",
                          }}
                        >
                          {getWorkspaceName(w)}
                        </span>
                        <span
                          style={{
                            color: "var(--color-secondary)",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            maxWidth: "400px",
                          }}
                        >
                          {w.local_path}
                        </span>
                      </div>
                      <span
                        style={{
                          color: "var(--color-secondary)",
                          fontSize: "0.75rem",
                        }}
                      >
                        {formatTimeAgo(w.updated_at)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feature Cards Grid — Tool Registry & File Vault only */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "var(--space-xl)",
        }}
      >
        <Link
          to="/tool-registry"
          className="glow-card"
          style={{
            padding: "var(--space-2xl)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
            textAlign: "left",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "rgba(56, 189, 248, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--color-secondary)",
              boxShadow: "var(--shadow-glow)",
            }}
          >
            <ToolRegistryIcon size={24} />
          </div>
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.4rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            Tool Registry
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.95rem",
              color: "var(--color-secondary)",
              lineHeight: 1.5,
            }}
          >
            Explore available system tools, solvers, and analytical adapters.
            Wright exposes CAD parsers, finite element solvers, and data
            formatters to agents.
          </p>
        </Link>

        <Link
          to="/file-vault"
          className="glow-card"
          style={{
            padding: "var(--space-2xl)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
            textAlign: "left",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "rgba(56, 189, 248, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--color-secondary)",
              boxShadow: "var(--shadow-glow)",
            }}
          >
            <FileVaultIcon size={24} />
          </div>
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.4rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            File Vault
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.95rem",
              color: "var(--color-secondary)",
              lineHeight: 1.5,
            }}
          >
            Manage engineering artifacts, design specs, and simulation outputs.
            The vault operates entirely offline, keeping your raw files secure
            in your workspace.
          </p>
        </Link>
      </div>

      {/* Create Workspace Modal */}
      <CreateWorkspaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={handleWorkspaceCreated}
      />
    </div>
  );
}

export default DashboardPage;
