import { useState, useEffect } from "react";
import { useTools } from "../../store/tools";
import { useChat } from "../../store/sessions";
import { ToolCard } from "../tools/ToolCard";
import { AddToolModal } from "../tools/AddToolModal";
import useLogger from "../../hooks/useLogger";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";

const CATEGORY_META: Record<string, { icon: string; label: string }> = {
  all: { icon: "🔧", label: "All Tools" },
  local: { icon: "💻", label: "Local Servers" },
  network: { icon: "🌐", label: "Network / Cloud" },
  cad: { icon: "📐", label: "CAD & Modeling" },
  simulation: { icon: "🔬", label: "Simulation / FEA" },
  manufacturing: { icon: "🏭", label: "Manufacturing" },
  plm: { icon: "☁️", label: "PLM / Enterprise" },
  utilities: { icon: "⚡", label: "Web & Utilities" },
  analysis: { icon: "📊", label: "Analysis" },
};

export function ToolRegistryPage() {
  const logger = useLogger("ToolRegistryPage");
  const { state: chatState } = useChat();
  const activeSessionId = chatState.activeSessionId;

  const {
    servers,
    tools,
    isLoading,
    error,
    registerCustomServer,
    installServerState,
    uninstallServerState,
    deleteServerState,
    toggleToolState,
  } = useTools();

  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const list = await workspaceService.getAllWorkspaces();
        setWorkspaces(list);
      } catch (err) {
        console.error("Failed to load workspaces in ToolRegistryPage", err);
      }
    };
    fetchWorkspaces();
  }, []);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    logger.info("Tool Registry Page loaded");
  }, [logger]);

  const categories = [
    "all",
    "local",
    "network",
    "cad",
    "simulation",
    "manufacturing",
    "plm",
    "utilities",
  ];

  const filteredServers = servers.filter((server) => {
    const matchesSearch =
      server.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (server.description || "")
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
    let matchesCategory = false;
    if (selectedCategory === "all") {
      matchesCategory = true;
    } else if (selectedCategory === "local") {
      matchesCategory = server.type === "stdio";
    } else if (selectedCategory === "network") {
      matchesCategory = ["sse", "webmcp"].includes(server.type);
    } else {
      matchesCategory =
        server.category.toLowerCase() === selectedCategory.toLowerCase();
    }
    return matchesSearch && matchesCategory;
  });

  // Sort: installed first, then by name
  const sortedServers = [...filteredServers].sort((a, b) => {
    if (a.is_installed && !b.is_installed) return -1;
    if (!a.is_installed && b.is_installed) return 1;
    return a.name.localeCompare(b.name);
  });

  // Category counts for sidebar
  const getCategoryCount = (cat: string) => {
    if (cat === "all") return servers.length;
    if (cat === "local")
      return servers.filter((s) => s.type === "stdio").length;
    if (cat === "network")
      return servers.filter((s) => ["sse", "webmcp"].includes(s.type)).length;
    return servers.filter((s) => s.category.toLowerCase() === cat).length;
  };

  const installedCount = servers.filter((s) => s.is_installed).length;

  return (
    <div
      data-testid="page-tool-registry"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
      }}
      className="animate-fade-in-up"
    >
      {/* Top Title Section */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "var(--space-xl) var(--space-xxl)",
          borderBottom: "1px solid var(--color-border)",
          background:
            "linear-gradient(180deg, var(--color-surface-subtle) 0%, var(--color-neutral) 100%)",
        }}
      >
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-md)",
            }}
          >
            <h1
              style={{
                fontSize: "1.8rem",
                fontFamily: "var(--font-ui)",
                fontWeight: 700,
                color: "var(--color-primary)",
                margin: 0,
              }}
            >
              Engineering Tool Registry
            </h1>
            <span
              style={{
                fontSize: "0.7rem",
                fontWeight: 700,
                letterSpacing: "1px",
                padding: "4px 10px",
                borderRadius: "20px",
                background:
                  "linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(168, 85, 247, 0.15))",
                border: "1px solid rgba(56, 189, 248, 0.25)",
                color: "var(--color-secondary)",
                textTransform: "uppercase",
              }}
            >
              {servers.length} Tools · {installedCount} Active
            </span>
          </div>
          <p
            style={{
              fontSize: "0.9rem",
              color: "var(--color-secondary)",
              marginTop: "var(--space-xs)",
              margin: 0,
            }}
          >
            Discover, install, and manage MCP servers for CAD, FEA, CAM, and PLM
            workflows.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          data-testid="tool-registry-register-btn"
          style={{
            padding: "var(--space-md) var(--space-lg)",
            backgroundColor: "var(--color-secondary)",
            color: "var(--color-surface-subtle)",
            fontWeight: 600,
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
          + Register Custom Tool
        </button>
      </div>

      {/* Main Page Layout */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Sidebar Categories */}
        <div
          style={{
            width: "260px",
            minWidth: "260px",
            borderRight: "1px solid var(--color-border)",
            backgroundColor: "var(--color-surface-subtle)",
            padding: "var(--space-xl) var(--space-lg)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
          }}
        >
          <span
            style={{
              fontSize: "0.75rem",
              textTransform: "uppercase",
              fontWeight: 700,
              color: "var(--color-secondary)",
              letterSpacing: "1.5px",
              paddingLeft: "var(--space-md)",
            }}
          >
            Categories
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {categories.map((cat) => {
              const meta = CATEGORY_META[cat] || { icon: "🔧", label: cat };
              const count = getCategoryCount(cat);
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  data-testid={`tool-registry-category-${cat}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    textAlign: "left",
                    padding: "10px var(--space-md)",
                    borderRadius: "var(--radius-lg)",
                    fontSize: "0.88rem",
                    fontWeight: selectedCategory === cat ? 600 : 500,
                    backgroundColor:
                      selectedCategory === cat
                        ? "rgba(56, 189, 248, 0.08)"
                        : "transparent",
                    color:
                      selectedCategory === cat
                        ? "var(--color-secondary)"
                        : "var(--color-text-muted)",
                    cursor: "pointer",
                    borderLeft:
                      selectedCategory === cat
                        ? "3px solid var(--color-secondary)"
                        : "3px solid transparent",
                    transition: "all var(--transition-smooth)",
                    border: "none",
                    borderBottom: "none",
                  }}
                  onMouseEnter={(e) => {
                    if (selectedCategory !== cat) {
                      e.currentTarget.style.color = "var(--color-primary)";
                      e.currentTarget.style.backgroundColor =
                        "var(--color-surface-hover)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedCategory !== cat) {
                      e.currentTarget.style.color = "var(--color-text-muted)";
                      e.currentTarget.style.backgroundColor = "transparent";
                    }
                  }}
                >
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-sm)",
                    }}
                  >
                    <span style={{ fontSize: "1rem" }}>{meta.icon}</span>
                    <span>{meta.label}</span>
                  </span>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      minWidth: "24px",
                      textAlign: "center",
                      padding: "2px 6px",
                      borderRadius: "10px",
                      backgroundColor:
                        selectedCategory === cat
                          ? "rgba(56, 189, 248, 0.15)"
                          : "var(--color-surface-hover)",
                      color:
                        selectedCategory === cat
                          ? "var(--color-secondary)"
                          : "var(--color-text-dim)",
                    }}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Sidebar Footer Stats */}
          <div
            style={{
              marginTop: "auto",
              padding: "var(--space-md)",
              borderTop: "1px solid var(--color-border)",
            }}
          >
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--color-text-dim)",
                lineHeight: 1.8,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Total Servers</span>
                <span
                  style={{ fontWeight: 600, color: "var(--color-primary)" }}
                >
                  {servers.length}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Installed</span>
                <span
                  style={{ fontWeight: 600, color: "var(--color-success)" }}
                >
                  {installedCount}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Available</span>
                <span
                  style={{ fontWeight: 600, color: "var(--color-secondary)" }}
                >
                  {servers.length - installedCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Directory Grid */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            padding: "var(--space-xl)",
          }}
        >
          {/* Search bar */}
          <div
            style={{
              marginBottom: "var(--space-xl)",
              position: "relative",
              maxWidth: "600px",
            }}
          >
            <span
              style={{
                position: "absolute",
                left: "14px",
                top: "50%",
                transform: "translateY(-50%)",
                fontSize: "1rem",
                color: "var(--color-text-dim)",
                pointerEvents: "none",
              }}
            >
              🔍
            </span>
            <input
              type="text"
              placeholder="Search by name, description, or platform..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="tool-registry-search-input"
              style={{
                width: "100%",
                padding: "var(--space-md) var(--space-lg)",
                paddingLeft: "42px",
                backgroundColor: "var(--color-surface-subtle)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-lg)",
                color: "var(--color-primary)",
                fontSize: "0.95rem",
                outline: "none",
                transition:
                  "border-color var(--transition-fast), box-shadow var(--transition-fast)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-secondary)";
                e.currentTarget.style.boxShadow =
                  "0 0 10px var(--color-border-glow)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Results header */}
          {!isLoading && (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "var(--space-lg)",
                fontSize: "0.8rem",
                color: "var(--color-text-dim)",
              }}
            >
              <span>
                Showing{" "}
                <strong style={{ color: "var(--color-primary)" }}>
                  {sortedServers.length}
                </strong>{" "}
                of {servers.length} servers
                {searchQuery && (
                  <>
                    {" "}
                    matching &ldquo;<em>{searchQuery}</em>&rdquo;
                  </>
                )}
              </span>
            </div>
          )}

          {/* Loading or Error states */}
          {isLoading && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                flex: 1,
              }}
            >
              <div className="thinking-dot" />
              <div className="thinking-dot" />
              <div className="thinking-dot" />
            </div>
          )}

          {!isLoading && error && (
            <div
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                border: "1px solid var(--color-error)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-lg)",
                color: "var(--color-error)",
                marginBottom: "var(--space-xl)",
              }}
            >
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Grid Render */}
          {!isLoading && (
            <div style={{ flex: 1, overflowY: "auto", paddingRight: "4px" }}>
              {sortedServers.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    padding: "60px 40px",
                    color: "var(--color-secondary)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "3rem",
                      marginBottom: "var(--space-lg)",
                    }}
                  >
                    🔍
                  </div>
                  <h3
                    style={{
                      fontFamily: "var(--font-ui)",
                      fontWeight: 600,
                      fontSize: "1.2rem",
                      color: "var(--color-primary)",
                      marginBottom: "var(--space-sm)",
                    }}
                  >
                    No MCP Servers Found
                  </h3>
                  <p
                    style={{
                      fontSize: "0.9rem",
                      maxWidth: "400px",
                      margin: "0 auto",
                      lineHeight: 1.6,
                    }}
                  >
                    Try adjusting your search query or selecting a different
                    category filter.
                  </p>
                </div>
              ) : (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(auto-fill, minmax(340px, 1fr))",
                    gap: "var(--space-lg)",
                  }}
                >
                  {sortedServers.map((server) => (
                    <ToolCard
                      key={server.server_id}
                      server={server}
                      tools={tools.filter(
                        (t) => t.server_id === server.server_id,
                      )}
                      onInstall={installServerState}
                      onUninstall={uninstallServerState}
                      onDelete={deleteServerState}
                      onToggleTool={toggleToolState}
                      workspaces={workspaces}
                      activeSessionId={activeSessionId}
                      onRefreshWorkspaces={async () => {
                        try {
                          const list =
                            await workspaceService.getAllWorkspaces();
                          setWorkspaces(list);
                        } catch (err) {
                          console.error(err);
                        }
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal Dialog Form */}
      <AddToolModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={registerCustomServer}
      />
    </div>
  );
}

export default ToolRegistryPage;
