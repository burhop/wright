import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import useLogger from "../../hooks/useLogger";
import useHealthStatus from "../../hooks/useHealthStatus";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";
import {
  mcpService,
  type BillingSubscription,
} from "../../services/mcp-service";
import { CreateWorkspaceModal } from "../common/CreateWorkspaceModal";

const getApiUrl = (path: string) => {
  if (typeof window === "undefined") return `http://127.0.0.1:8000${path}`;
  const host = window.location.hostname;
  const port = window.location.port;
  const base =
    port === "5173" || port === "5174" ? `http://${host}:8000` : "";
  return `${base}${path}`;
};

export function DashboardPage() {
  const logger = useLogger("DashboardPage");
  const navigate = useNavigate();

  // Health and Agent Connection state
  const statuses = useHealthStatus(10000); // Poll health status every 10s
  const apiState = statuses.find((s) => s.serviceId === "wright-api")?.state || "unknown";
  const hermesState = statuses.find((s) => s.serviceId === "hermes-agent")?.state || "unknown";
  const inferenceLabel = "Nemotron-Nano-30B";

  const [recentWorkspaces, setRecentWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [showAllWorkspaces, setShowAllWorkspaces] = useState(false);
  const [allWorkspaces, setAllWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [activeSessionsCount, setActiveSessionsCount] = useState<number>(0);
  const [subscriptions, setSubscriptions] = useState<BillingSubscription[]>([]);

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

    const fetchRecentLogs = async () => {
      try {
        const res = await fetch(getApiUrl("/api/logs?limit=3"));
        if (res.ok) {
          const data = await res.json();
          setRecentLogs(data.logs || []);
        }
      } catch (err) {
        console.error("Failed to fetch recent logs", err);
      }
    };

    const fetchSessions = async () => {
      try {
        const res = await fetch(getApiUrl("/api/agent/sessions"));
        if (res.ok) {
          const data = await res.json();
          setActiveSessionsCount(data.sessions?.length || 0);
        }
      } catch (err) {
        console.error("Failed to fetch sessions count", err);
      }
    };

    const fetchSubscriptions = async () => {
      try {
        const activeSubscriptions = await mcpService.getBillingSubscriptions();
        setSubscriptions(activeSubscriptions);
      } catch (err) {
        logger.error("Failed to fetch billing subscriptions", { err });
      }
    };

    fetchWorkspaces();
    fetchRecentLogs();
    fetchSessions();
    fetchSubscriptions();

    const subscriptionsRefresh = window.setInterval(fetchSubscriptions, 5000);
    window.addEventListener("focus", fetchSubscriptions);
    return () => {
      window.clearInterval(subscriptionsRefresh);
      window.removeEventListener("focus", fetchSubscriptions);
    };
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

  const formatBillingAmount = (subscription: BillingSubscription) => {
    const currency = subscription.currency.toUpperCase();
    const amount = new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(subscription.amount_cents / 100);
    return subscription.interval ? `${amount} / ${subscription.interval}` : amount;
  };

  const formatPaymentDate = (paymentDate: number) =>
    new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(paymentDate * 1000));

  const handleSelectWorkspace = async (w: WorkspaceInfo) => {
    try {
      await workspaceService.activateWorkspace(w.session_id);
      navigate(`/workspace/${w.workspace_id}`);
    } catch (err) {
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
        gap: "var(--space-md)",
        maxWidth: "1280px",
        margin: "0 auto",
        padding: "var(--space-md) var(--space-lg)",
      }}
      className="animate-fade-in-up"
    >
      {/* Title section (compact) */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid var(--color-border)",
          paddingBottom: "var(--space-sm)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          <h1
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.8rem",
              fontWeight: 700,
              color: "var(--color-primary)",
              letterSpacing: "-0.5px",
            }}
          >
            Wright Design Hub
          </h1>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.85rem",
              color: "var(--color-secondary)",
            }}
          >
            Local-first multi-agent engineering workspace orchestrator.
          </p>
        </div>

        <button
          data-testid="create-workspace-btn"
          id="create-workspace-btn"
          onClick={() => setIsCreateModalOpen(true)}
          style={{
            padding: "var(--space-sm) var(--space-md)",
            backgroundColor: "var(--color-secondary)",
            color: "var(--color-surface-subtle)",
            fontWeight: 600,
            fontSize: "0.85rem",
            borderRadius: "var(--radius-md)",
            border: "none",
            cursor: "pointer",
            transition: "all var(--transition-smooth)",
            boxShadow: "var(--shadow-glow)",
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

      {/* Grid Layout (Condensed margin & padding, fits on 1080p screen) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-md)",
          width: "100%",
        }}
      >
        {/* Box 1: Engineering Workspaces (1/2 Width) */}
        <div
          data-testid="card-workspaces"
          className="glow-card"
          style={{
            padding: "var(--space-md)",
            backgroundColor: "var(--color-surface)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--color-border)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
          }}
        >
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
                fontSize: "1.1rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              🛠️ Engineering Workspaces
            </h2>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              maxHeight: "240px",
              overflowY: "auto",
            }}
          >
            {recentWorkspaces.length === 0 ? (
              <div
                style={{
                  padding: "var(--space-md)",
                  backgroundColor: "var(--color-surface-subtle)",
                  borderRadius: "var(--radius-md)",
                  textAlign: "center",
                  border: "1px dashed var(--color-border)",
                  fontSize: "0.8rem",
                  color: "var(--color-secondary)",
                }}
              >
                No active workspaces yet. Create one above to begin.
              </div>
            ) : (
              recentWorkspaces.map((w) => (
                <div
                  key={w.workspace_id}
                  data-testid={`card-workspace-${w.workspace_id}`}
                  onClick={() => handleSelectWorkspace(w)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "6px var(--space-sm)",
                    backgroundColor: "var(--color-surface-subtle)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    transition: "all var(--transition-smooth)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-secondary)";
                    e.currentTarget.style.transform = "translateX(2px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-border)";
                    e.currentTarget.style.transform = "translateX(0)";
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
                    <div style={{ color: "var(--color-secondary)", flexShrink: 0 }}>
                      📁
                    </div>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        textAlign: "left",
                        overflow: "hidden",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "0.85rem",
                          fontWeight: 600,
                          color: "var(--color-primary)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {getWorkspaceName(w)}
                      </span>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--color-secondary)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          maxWidth: "340px",
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
                      gap: "var(--space-sm)",
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.7rem",
                        color: "var(--color-secondary)",
                      }}
                    >
                      {formatTimeAgo(w.updated_at)}
                    </span>
                    <span style={{ color: "var(--color-secondary)", fontSize: "0.8rem" }}>
                      →
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {recentWorkspaces.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <button
                data-testid="view-all-workspaces-btn"
                id="view-all-workspaces-btn"
                onClick={handleViewAllWorkspaces}
                style={{
                  alignSelf: "flex-start",
                  padding: "4px var(--space-sm)",
                  backgroundColor: "transparent",
                  color: "var(--color-secondary)",
                  fontWeight: 500,
                  fontSize: "0.75rem",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--color-border)",
                  cursor: "pointer",
                  transition: "all var(--transition-fast)",
                }}
              >
                {showAllWorkspaces ? "▲ Hide all workspaces" : "▼ View all workspaces"}
              </button>

              {showAllWorkspaces && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "2px",
                    maxHeight: "100px",
                    overflowY: "auto",
                    paddingLeft: "var(--space-xs)",
                    borderLeft: "2px solid var(--color-border)",
                  }}
                >
                  {allWorkspaces.map((w) => (
                    <div
                      key={w.workspace_id}
                      onClick={() => handleSelectWorkspace(w)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "4px var(--space-xs)",
                        cursor: "pointer",
                        fontSize: "0.75rem",
                        borderRadius: "var(--radius-sm)",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = "rgba(56, 189, 248, 0.04)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "transparent";
                      }}
                    >
                      <span style={{ fontWeight: 600, color: "var(--color-primary)" }}>
                        {getWorkspaceName(w)}
                      </span>
                      <span style={{ color: "var(--color-secondary)", fontSize: "0.7rem" }}>
                        {formatTimeAgo(w.updated_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Box 2: Agent Status (1/2 Width) */}
        <div
          data-testid="card-agent-status"
          className="glow-card"
          style={{
            padding: "var(--space-md)",
            backgroundColor: "var(--color-surface)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--color-border)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            🤖 Agent Status (Hermes)
          </h2>

          {/* Connection Indicators */}
          <div style={{ display: "flex", gap: "var(--space-md)", flexWrap: "wrap", fontSize: "0.8rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: apiState === "connected" ? "var(--color-success, #22c55e)" : "var(--color-error, #ef4444)",
                }}
              />
              <span>Wright API: <strong>{apiState}</strong></span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: hermesState === "connected" ? "var(--color-success, #22c55e)" : "var(--color-error, #ef4444)",
                }}
              />
              <span>Hermes: <strong>{hermesState}</strong></span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: "var(--color-success, #22c55e)",
                }}
              />
              <span>Inference Engine: <strong>{inferenceLabel}</strong></span>
            </div>
          </div>

          {/* Running Tasks status */}
          <div
            style={{
              padding: "var(--space-xs) var(--space-sm)",
              backgroundColor: "var(--color-surface-subtle)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-border)",
              fontSize: "0.8rem",
              textAlign: "left",
            }}
          >
            <div style={{ color: "var(--color-secondary)", fontSize: "0.75rem", fontWeight: "bold" }}>
              CURRENT AGENT RUNNING STATE
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "2px" }}>
              <span className="thinking-dot" />
              <span>Idle (Awaiting task request)</span>
            </div>
          </div>

          {/* Recent System Health Logs */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2px", textAlign: "left" }}>
            <div style={{ color: "var(--color-secondary)", fontSize: "0.75rem", fontWeight: "bold" }}>
              RECENT SYSTEM HEALTH LOGS
            </div>
            {recentLogs.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "2px", maxHeight: "100px", overflowY: "auto" }}>
                {recentLogs.map((entry, idx) => (
                  <div
                    key={idx}
                    style={{
                      fontSize: "0.7rem",
                      backgroundColor: "var(--color-surface-subtle)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "var(--radius-xs)",
                      padding: "4px var(--space-xs)",
                      color: "var(--color-text-muted)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                    title={entry.message}
                  >
                    [{entry.timestamp.substring(11, 19)}] {entry.logger}: {entry.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Box 3: Stripe Billing Subscriptions (1/2 Width) */}
        <div
          data-testid="card-subscriptions"
          className="glow-card"
          style={{
            padding: "var(--space-md)",
            backgroundColor: "var(--color-surface)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--color-border)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            Stripe Billing Subscriptions
          </h2>

          <div
            data-testid="subscriptions-count"
            style={{
              alignSelf: "flex-start",
              fontSize: "0.75rem",
              color: "var(--color-secondary)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              padding: "3px var(--space-sm)",
              textTransform: "uppercase",
              fontWeight: 700,
            }}
          >
            {subscriptions.length} active
          </div>

          {subscriptions.length === 0 ? (
            <div
              data-testid="subscriptions-empty"
              style={{
                minHeight: "124px",
                borderRadius: "var(--radius-md)",
                border: "1px solid transparent",
              }}
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {subscriptions.map((subscription) => (
                <div
                  key={subscription.subscription_id}
                  data-testid={`subscription-row-${subscription.server_id}`}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    padding: "var(--space-sm)",
                    backgroundColor: "var(--color-surface-subtle)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    textAlign: "left",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.88rem",
                      fontWeight: 700,
                      color: "var(--color-primary)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {subscription.server_name}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: "var(--space-sm)",
                      fontSize: "0.76rem",
                      color: "var(--color-secondary)",
                    }}
                  >
                    <span>{formatPaymentDate(subscription.payment_date)}</span>
                    <strong style={{ color: "var(--color-primary)" }}>
                      {formatBillingAmount(subscription)}
                    </strong>
                  </div>
                  <div
                    data-testid={`subscription-mcp-status-${subscription.server_id}`}
                    style={{
                      alignSelf: "flex-start",
                      color: subscription.mcp_enabled
                        ? "var(--color-success, #22c55e)"
                        : "var(--color-warning, #f59e0b)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "var(--radius-sm)",
                      padding: "4px var(--space-sm)",
                      fontSize: "0.72rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    {subscription.mcp_enabled ? "MCP Server enabled" : "Provisioning"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Box 4: System Activity & Telemetry (1/2 Width) */}
        <div
          data-testid="card-telemetry"
          className="glow-card"
          style={{
            padding: "var(--space-md)",
            backgroundColor: "var(--color-surface)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--color-border)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "var(--color-primary)",
            }}
          >
            📊 System Telemetry
          </h2>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              textAlign: "left",
              fontSize: "0.8rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-secondary)" }}>SQLite DB Location:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>state.db</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-secondary)" }}>Total Workspaces Indexed:</span>
              <span><strong>{recentWorkspaces.length}</strong></span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-secondary)" }}>Active Agent Chat Sessions:</span>
              <span><strong>{activeSessionsCount}</strong></span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-secondary)" }}>Offline-First Mode:</span>
              <span style={{ color: "var(--color-success, #22c55e)" }}>Enabled (100% Local)</span>
            </div>
          </div>
        </div>

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
