import { useState } from "react";
import type {
  McpServer,
  McpTool,
  EnvVarDefinition,
} from "../../services/mcp-service";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";
import { ServerTypeBadge } from "./ServerTypeBadge";
import { useTools } from "../../store/tools";
import { WorkspaceEnablement } from "./WorkspaceEnablement";

interface ToolCardProps {
  server: McpServer;
  tools: McpTool[];
  onInstall: (serverId: string, sessionId?: string | null) => Promise<void>;
  onUninstall: (serverId: string, sessionId?: string | null) => Promise<void>;
  onDelete: (serverId: string) => Promise<void>;
  onToggleTool: (toolId: string, enabled: boolean) => Promise<void>;
  workspaces: WorkspaceInfo[];
  activeSessionId: string | null;
  onRefreshWorkspaces: () => Promise<void>;
}

export function ToolCard({
  server,
  tools,
  onInstall,
  onUninstall,
  onDelete,
  onToggleTool,
  workspaces,
  activeSessionId,
  onRefreshWorkspaces,
}: ToolCardProps) {
  const [isInstalling, setIsInstalling] = useState(false);
  const [isUninstalling, setIsUninstalling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showWorkspaces, setShowWorkspaces] = useState(false);
  const [togglingWorkspaceId, setTogglingWorkspaceId] = useState<string | null>(
    null,
  );

  const [imgError, setImgError] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState<{
    installed: string;
    latest: string;
  } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [upToDateMessage, setUpToDateMessage] = useState(false);
  const [cardNotice, setCardNotice] = useState<string | null>(null);

  const {
    checkServerVersion,
    updateServerState,
    saveCredentials,
    deleteCredentials,
  } = useTools();
  const isLocalServer = server.type === "stdio";

  // Credential configuration state
  const hasEnvVarDefs =
    Array.isArray(server.env_vars) && server.env_vars.length > 0;
  const [showCredentials, setShowCredentials] = useState(false);
  const [credentialValues, setCredentialValues] = useState<
    Record<string, string>
  >({});
  const [isSavingCreds, setIsSavingCreds] = useState(false);
  const [credentialSaved, setCredentialSaved] = useState(false);
  const credentialDefs = hasEnvVarDefs
    ? (server.env_vars as EnvVarDefinition[])
    : [];
  const configuredCredentials = server.credentials_configured || {};
  const missingRequiredCredentialDefs = credentialDefs.filter(
    (v) => v.required && !configuredCredentials[v.name],
  );
  const requiredCredsMissing = () => missingRequiredCredentialDefs.length > 0;
  const hasUnsavedCredentialValues = Object.values(credentialValues).some(
    (value) => value.trim().length > 0,
  );
  const hasValuesForMissingRequiredCredentials =
    missingRequiredCredentialDefs.every(
      (varDef) => (credentialValues[varDef.name] || "").trim().length > 0,
    );

  const isInstallBlocked =
    server.installability_tier === "blocked" ||
    server.installability_tier === "non_working";
  const currentPlatform =
    server.platform_support?.linux_x64 ||
    server.platform_support?.windows_11_x64 ||
    Object.values(server.platform_support || {})[0];

  const titleCase = (value: string) =>
    value
      .split(/[_-]/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

  const verificationMeta: Record<
    McpServer["verification_state"],
    { label: string; tooltip: string }
  > = {
    verified_mcp: {
      label: "Verified MCP",
      tooltip:
        "Catalog evidence indicates this is an MCP server, but this is not a security review.",
    },
    verified_docs_mcp: {
      label: "Docs verified MCP",
      tooltip:
        "Project documentation describes MCP support; this is not a security review.",
    },
    community_mcp: {
      label: "Community MCP",
      tooltip:
        "Community or public catalog entry; review the source before installing.",
    },
    user_reported_url_needed: {
      label: "Needs source URL",
      tooltip:
        "User-reported candidate that needs a source URL before validation.",
    },
    verified_api_wrapper_candidate: {
      label: "API wrapper candidate",
      tooltip:
        "Likely wraps an API as MCP, but the exact server implementation needs review.",
    },
    capability_alias: {
      label: "Capability alias",
      tooltip:
        "Represents a capability area rather than a directly installable MCP server.",
    },
    ui_or_web_standard: {
      label: "UI/web standard",
      tooltip:
        "Represents a UI or web standard integration, not a normal MCP server package.",
    },
    watchlist: {
      label: "Watchlist",
      tooltip:
        "Tracked as a possible future MCP entry; not ready for normal install.",
    },
    excluded: {
      label: "Excluded",
      tooltip: "Intentionally excluded from normal MCP installation workflows.",
    },
  };

  const installabilityMeta: Record<
    McpServer["installability_tier"],
    { label: string; tooltip: string }
  > = {
    tested: {
      label: "Launch tested",
      tooltip:
        "Wright ran the MCP server in the validation environment. This is not a security review and does not guarantee bug-free behavior.",
    },
    might_work: {
      label: "Needs validation",
      tooltip:
        "The catalog entry looks plausible but has not passed Wright's MCP launch validation.",
    },
    blocked: {
      label: "Blocked",
      tooltip:
        server.install_blocked_reason ||
        "Automated install is blocked until the catalog entry is corrected.",
    },
    non_working: {
      label: "Not working",
      tooltip:
        "Validation found this MCP server does not currently work in the supported environment.",
    },
  };

  const riskTooltip =
    server.risk_level === "read-only"
      ? "Expected to read data only. Review permissions and source before installing."
      : server.risk_level === "safety-critical"
        ? "Could affect safety-critical workflows. Requires careful human review before use."
        : `${titleCase(server.risk_level)} risk classification from catalog metadata. Review source and permissions before installing.`;

  const verification = verificationMeta[server.verification_state] || {
    label: titleCase(server.verification_state),
    tooltip: "Catalog verification status.",
  };
  const installability = installabilityMeta[server.installability_tier] || {
    label: titleCase(server.installability_tier),
    tooltip: "Catalog installability status.",
  };

  const badgeStyle = (
    color: string,
    backgroundColor = "var(--color-surface-subtle)",
  ) => ({
    display: "inline-flex",
    alignItems: "center",
    fontSize: "0.65rem",
    textTransform: "uppercase" as const,
    backgroundColor,
    color,
    padding: "2px 6px",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--color-border)",
    fontWeight: 700,
    letterSpacing: 0,
    maxWidth: "100%",
  });

  const persistCredentialValues = async () => {
    const valuesToSave = Object.fromEntries(
      Object.entries(credentialValues).filter(
        ([, value]) => value.trim().length > 0,
      ),
    );
    if (Object.keys(valuesToSave).length === 0) {
      return false;
    }
    setIsSavingCreds(true);
    setCardError(null);
    await saveCredentials(server.server_id, valuesToSave);
    setCredentialSaved(true);
    setCredentialValues({});
    setTimeout(() => setCredentialSaved(false), 3000);
    setIsSavingCreds(false);
    return true;
  };

  const handleSaveCredentials = async () => {
    setCardNotice(null);
    try {
      await persistCredentialValues();
    } catch (err: any) {
      setCardError(err.message || "Failed to save credentials");
    } finally {
      setIsSavingCreds(false);
    }
  };

  const performInstall = async () => {
    await onInstall(server.server_id, activeSessionId);
    await onRefreshWorkspaces();
  };

  const revealCredentialForm = (notice: string) => {
    setShowDetails(true);
    setShowCredentials(true);
    setCardNotice(notice);
  };

  const handleInstall = async () => {
    setCardError(null);
    setCardNotice(null);

    if (requiredCredsMissing() && !hasValuesForMissingRequiredCredentials) {
      revealCredentialForm("Enter the required credentials to continue.");
      return;
    }

    setIsInstalling(true);
    try {
      if (requiredCredsMissing() || hasUnsavedCredentialValues) {
        await persistCredentialValues();
      }
      await performInstall();
    } catch (err: any) {
      console.error(err);
      setCardError(err.message || "Failed to install server");
    } finally {
      setIsInstalling(false);
      setIsSavingCreds(false);
    }
  };

  const handleClearCredentials = async () => {
    setCardError(null);
    try {
      await deleteCredentials(server.server_id);
      setCredentialValues({});
    } catch (err: any) {
      setCardError(err.message || "Failed to clear credentials");
    }
  };

  const handleUninstall = async () => {
    if (
      !window.confirm(`Are you sure you want to uninstall "${server.name}"?`)
    ) {
      return;
    }
    setIsUninstalling(true);
    setCardError(null);
    try {
      await onUninstall(server.server_id, activeSessionId);
      await onRefreshWorkspaces();
    } catch (err: any) {
      console.error(err);
      setCardError(err.message || "Failed to uninstall server");
    } finally {
      setIsUninstalling(false);
    }
  };

  const handleDelete = async () => {
    if (
      !window.confirm(
        `Are you sure you want to remove the MCP server "${server.name}"?`,
      )
    ) {
      return;
    }
    setIsDeleting(true);
    setCardError(null);
    try {
      await onDelete(server.server_id);
    } catch (err: any) {
      console.error(err);
      setCardError(err.message || "Failed to delete server");
      setIsDeleting(false);
    }
  };

  const handleCheckForUpdates = async () => {
    setIsCheckingUpdate(true);
    setCardError(null);
    setUpToDateMessage(false);
    try {
      const result = await checkServerVersion(server.server_id);
      if (result.error) {
        setCardError(result.error);
      } else if (result.update_available) {
        setUpdateAvailable({
          installed: result.installed || server.installed_version || "unknown",
          latest: result.latest || "unknown",
        });
      } else {
        setUpToDateMessage(true);
        setTimeout(() => setUpToDateMessage(false), 3000);
      }
    } catch (err: any) {
      setCardError(err.message || "Failed to check for updates");
    } finally {
      setIsCheckingUpdate(false);
    }
  };

  const handleUpdate = async () => {
    setIsUpdating(true);
    setCardError(null);
    try {
      await updateServerState(server.server_id);
      setUpdateAvailable(null);
    } catch (err: any) {
      setCardError(err.message || "Failed to update server");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleToggleWorkspace = async (
    w: WorkspaceInfo,
    isEnabled: boolean,
  ) => {
    setTogglingWorkspaceId(w.workspace_id);
    try {
      await workspaceService.toggleWorkspaceTool(
        w.session_id,
        server.server_id,
        isEnabled,
      );
      await onRefreshWorkspaces();
    } catch (err) {
      console.error(err);
    } finally {
      setTogglingWorkspaceId(null);
    }
  };

  const getStatusColor = () => {
    if (!server.is_installed) return "var(--color-text-dim)";
    if (server.status === "active") return "var(--color-success)";
    if (server.status === "error") return "var(--color-error)";
    return "var(--color-secondary)";
  };

  const renderLogo = () => {
    if (server.image_url && !imgError) {
      return (
        <img
          src={server.image_url}
          onError={() => setImgError(true)}
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            objectFit: "cover",
            border: "1px solid var(--color-border)",
          }}
          data-testid={`server-card-logo-${server.server_id}`}
          alt={server.name}
        />
      );
    }
    const firstLetter = server.name.charAt(0).toUpperCase();
    return (
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "50%",
          background:
            "linear-gradient(135deg, var(--color-surface-hover), var(--color-border))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "1.05rem",
          fontWeight: 700,
          color: "var(--color-secondary)",
          border: "1px solid var(--color-border)",
        }}
        data-testid={`server-card-logo-${server.server_id}`}
      >
        {firstLetter}
      </div>
    );
  };

  return (
    <div
      data-testid={`server-card-${server.server_id}`}
      style={{
        display: "flex",
        flexDirection: "column",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-lg)",
        gap: "var(--space-sm)",
        transition: "all var(--transition-smooth)",
        boxShadow: "var(--shadow-md)",
        position: "relative",
        opacity: isDeleting || isUninstalling ? 0.5 : 1,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--color-secondary)";
        e.currentTarget.style.boxShadow = "var(--shadow-glow)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--color-border)";
        e.currentTarget.style.boxShadow = "var(--shadow-md)";
      }}
    >
      {/* Top Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "var(--space-sm)",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "var(--space-sm)",
            alignItems: "center",
          }}
        >
          {renderLogo()}
          <div style={{ textAlign: "left" }}>
            <h3
              style={{
                fontSize: "0.95rem",
                fontFamily: "var(--font-ui)",
                color: "var(--color-primary)",
                fontWeight: 600,
                margin: 0,
                display: "flex",
                alignItems: "center",
                gap: "var(--space-xs)",
              }}
            >
              {server.name}
              {server.installed_version && (
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 500,
                    color: "var(--color-success)",
                    marginLeft: "4px",
                  }}
                >
                  v{server.installed_version}
                </span>
              )}
            </h3>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-xs)",
                marginTop: "2px",
                flexWrap: "wrap",
              }}
            >
              <ServerTypeBadge type={server.type} />
              <span
                title={`Category: ${titleCase(server.category)}`}
                style={{
                  display: "inline-block",
                  fontSize: "0.65rem",
                  textTransform: "uppercase",
                  backgroundColor: "var(--color-surface-subtle)",
                  color: "var(--color-secondary)",
                  padding: "2px 6px",
                  borderRadius: "20px",
                  border: "1px solid rgba(56, 189, 248, 0.2)",
                  fontWeight: 600,
                  letterSpacing: "0.5px",
                }}
              >
                {server.category}
              </span>
              <span
                data-testid={`server-card-verification-${server.server_id}`}
                title={verification.tooltip}
                aria-label={verification.tooltip}
                style={badgeStyle("var(--color-secondary)")}
              >
                {verification.label}
              </span>
              <span
                data-testid={`server-card-installability-${server.server_id}`}
                title={installability.tooltip}
                aria-label={installability.tooltip}
                style={badgeStyle(
                  server.installability_tier === "tested"
                    ? "var(--color-success)"
                    : server.installability_tier === "might_work"
                      ? "var(--color-warning)"
                      : "var(--color-error)",
                )}
              >
                {installability.label}
              </span>
              <span
                data-testid={`server-card-risk-${server.server_id}`}
                title={riskTooltip}
                aria-label={riskTooltip}
                style={badgeStyle(
                  server.risk_level === "high" ||
                    server.risk_level === "safety-critical"
                    ? "var(--color-error)"
                    : "var(--color-text-muted)",
                )}
              >
                {server.risk_level === "read-only"
                  ? "Read only"
                  : `${titleCase(server.risk_level)} risk`}
              </span>
            </div>
          </div>
        </div>

        {/* Global Install Button / Status Badge */}
        <div>
          {!server.is_installed ? (
            <button
              onClick={handleInstall}
              disabled={
                isInstalling || isSavingCreds || isDeleting || isInstallBlocked
              }
              data-testid={
                isLocalServer
                  ? `server-card-install-btn-${server.server_id}`
                  : `server-card-connect-btn-${server.server_id}`
              }
              title={
                isInstallBlocked
                  ? server.install_blocked_reason ||
                    "This entry is blocked from automated install"
                  : requiredCredsMissing()
                    ? "Enter the required credentials to install"
                    : undefined
              }
              style={{
                padding: "var(--space-xs) var(--space-md)",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8rem",
                fontWeight: 600,
                border: "none",
                backgroundColor: "var(--color-secondary)",
                color: "#ffffff",
                cursor:
                  isInstalling || isSavingCreds || isInstallBlocked
                    ? "not-allowed"
                    : "pointer",
                transition: "all var(--transition-smooth)",
                boxShadow: "var(--shadow-glow)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = "var(--shadow-glow-active)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = "var(--shadow-glow)";
              }}
            >
              {isInstalling || isSavingCreds
                ? isLocalServer
                  ? requiredCredsMissing()
                    ? "Saving..."
                    : "Installing..."
                  : requiredCredsMissing()
                    ? "Saving..."
                    : "Connecting..."
                : isLocalServer
                  ? requiredCredsMissing() && showCredentials
                    ? "Save & Install"
                    : "Install"
                  : requiredCredsMissing() && showCredentials
                    ? "Save & Connect"
                    : "Connect"}
            </button>
          ) : requiredCredsMissing() ? (
            <div
              style={{
                display: "flex",
                gap: "var(--space-xs)",
                alignItems: "center",
                flexWrap: "wrap",
                justifyContent: "flex-end",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setCardError(null);
                  revealCredentialForm(
                    "Enter the required credentials before using this server.",
                  );
                }}
                disabled={isSavingCreds || isDeleting}
                data-testid={`server-card-add-credentials-btn-${server.server_id}`}
                title="Required credentials are missing"
                style={{
                  padding: "var(--space-xs) var(--space-md)",
                  borderRadius: "var(--radius-md)",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  border: "none",
                  backgroundColor: "var(--color-warning)",
                  color: "var(--color-surface)",
                  cursor:
                    isSavingCreds || isDeleting ? "not-allowed" : "pointer",
                  transition: "all var(--transition-smooth)",
                }}
              >
                Add Credentials
              </button>
              <button
                onClick={handleUninstall}
                disabled={isUninstalling}
                data-testid={
                  isLocalServer
                    ? `server-card-uninstall-btn-${server.server_id}`
                    : `server-card-disconnect-btn-${server.server_id}`
                }
                style={{
                  padding: "var(--space-xs) var(--space-sm)",
                  borderRadius: "var(--radius-md)",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  border: "1px solid rgba(239, 68, 68, 0.35)",
                  backgroundColor: "transparent",
                  color: "var(--color-error)",
                  cursor: isUninstalling ? "not-allowed" : "pointer",
                  transition: "all var(--transition-smooth)",
                }}
              >
                {isUninstalling
                  ? isLocalServer
                    ? "Uninstalling..."
                    : "Disconnecting..."
                  : isLocalServer
                    ? "Uninstall"
                    : "Disconnect"}
              </button>
            </div>
          ) : (
            <button
              onClick={handleUninstall}
              disabled={isUninstalling}
              data-testid={
                isLocalServer
                  ? `server-card-uninstall-btn-${server.server_id}`
                  : `server-card-disconnect-btn-${server.server_id}`
              }
              style={{
                padding: "var(--space-xs) var(--space-md)",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8rem",
                fontWeight: 600,
                border: "none",
                backgroundColor: "var(--color-error)",
                color: "#ffffff",
                cursor: isUninstalling ? "not-allowed" : "pointer",
                transition: "all var(--transition-smooth)",
                boxShadow: "0 0 10px rgba(239, 68, 68, 0.15)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow =
                  "0 0 15px rgba(239, 68, 68, 0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow =
                  "0 0 10px rgba(239, 68, 68, 0.15)";
              }}
            >
              {isUninstalling
                ? isLocalServer
                  ? "Uninstalling..."
                  : "Disconnecting..."
                : isLocalServer
                  ? "Uninstall"
                  : "Disconnect"}
            </button>
          )}
        </div>
      </div>

      {/* Description Block */}
      {server.description && (
        <div
          data-testid={`server-card-description-${server.server_id}`}
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-xs)",
          }}
        >
          <p
            style={{
              fontSize: "0.8rem",
              color: "var(--color-text-muted)",
              lineHeight: 1.5,
              margin: "0",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              textOverflow: "ellipsis",
              textAlign: "left",
            }}
          >
            {server.description.split("⚠️")[0].trim()}
          </p>
          {server.description.includes("⚠️") && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                fontSize: "0.7rem",
                fontWeight: 600,
                color: "var(--color-warning)",
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.2)",
                padding: "2px 6px",
                borderRadius: "6px",
                width: "fit-content",
              }}
            >
              ⚠️ {server.description.split("⚠️")[1].trim()}
            </span>
          )}
          {server.source_url && (
            <a
              href={server.source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: "0.7rem",
                color: "var(--color-secondary)",
                opacity: 0.7,
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                width: "fit-content",
                transition: "opacity var(--transition-fast)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.7")}
            >
              ↗ View Source
            </a>
          )}
        </div>
      )}

      <button
        type="button"
        onClick={() => setShowDetails(!showDetails)}
        data-testid={`server-card-details-toggle-${server.server_id}`}
        aria-expanded={showDetails}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-sm)",
          width: "100%",
          padding: "var(--space-xs) 0 0",
          color: "var(--color-secondary)",
          background: "none",
          border: "none",
          borderTop: "1px solid var(--color-border)",
          cursor: "pointer",
          fontSize: "0.78rem",
          fontWeight: 700,
          textAlign: "left",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          transition: "color var(--transition-fast)",
        }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.color = "var(--color-primary)")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.color = "var(--color-secondary)")
        }
      >
        <span>{showDetails ? "Hide details" : "Show details"}</span>
        <span>{showDetails ? "Collapse" : "Expand"}</span>
      </button>

      {showDetails && (
        <>
          <div
            data-testid={`server-card-platform-${server.server_id}`}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
              padding: "var(--space-sm)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--color-surface-subtle)",
              textAlign: "left",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "var(--space-sm)",
                fontSize: "0.76rem",
              }}
            >
              <span style={{ color: "var(--color-primary)", fontWeight: 700 }}>
                Linux x64
              </span>
              <span
                style={{ color: "var(--color-secondary)", fontWeight: 700 }}
              >
                {currentPlatform?.status || "unknown"}
                {currentPlatform?.tested ? " · tested" : ""}
              </span>
            </div>
            {currentPlatform?.notes && (
              <span
                style={{
                  fontSize: "0.72rem",
                  color: "var(--color-text-muted)",
                }}
              >
                {currentPlatform.notes}
              </span>
            )}
            {(server.host_software_required.length > 0 ||
              server.credentials_required.length > 0) && (
              <span
                style={{
                  fontSize: "0.72rem",
                  color: "var(--color-text-muted)",
                }}
              >
                Requires:{" "}
                {[
                  ...server.host_software_required,
                  ...server.credentials_required,
                ].join(", ")}
              </span>
            )}
            {server.validation_result?.message && (
              <span
                style={{
                  fontSize: "0.72rem",
                  color: "var(--color-text-muted)",
                }}
              >
                {server.validation_result.message}
              </span>
            )}
            {server.install_blocked_reason && (
              <span
                style={{ fontSize: "0.72rem", color: "var(--color-warning)" }}
              >
                {server.install_blocked_reason}
              </span>
            )}
            {server.follow_up_url && (
              <a
                href={server.follow_up_url}
                data-testid={`server-card-followup-${server.server_id}`}
                style={{
                  fontSize: "0.72rem",
                  color: "var(--color-secondary)",
                  textDecoration: "none",
                  fontWeight: 700,
                }}
              >
                Follow-up record
              </a>
            )}
          </div>

          {/* Credential Configuration Panel */}
          {hasEnvVarDefs && (
            <div
              data-testid={`server-card-credentials-section-${server.server_id}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs)",
              }}
            >
              {/* Requires Configuration badge */}
              {requiredCredsMissing() && !showCredentials && (
                <span
                  data-testid={`server-card-credentials-badge-${server.server_id}`}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "0.7rem",
                    fontWeight: 600,
                    color: "var(--color-warning)",
                    backgroundColor: "rgba(245, 158, 11, 0.08)",
                    border: "1px solid rgba(245, 158, 11, 0.2)",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    width: "fit-content",
                  }}
                >
                  🔑 Requires Configuration
                </span>
              )}

              <button
                type="button"
                onClick={() => setShowCredentials(!showCredentials)}
                data-testid={`server-card-credentials-toggle-${server.server_id}`}
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
                  {showCredentials
                    ? "▼ Hide Credentials"
                    : "▶ Configure Credentials"}
                </span>
              </button>

              {showCredentials && (
                <div
                  data-testid={`server-card-credentials-form-${server.server_id}`}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-sm)",
                    padding: "var(--space-md)",
                    backgroundColor: "var(--color-surface-subtle)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-lg)",
                    marginTop: "var(--space-xs)",
                  }}
                >
                  {(server.env_vars as EnvVarDefinition[]).map((varDef) => {
                    const isConfigured =
                      server.credentials_configured?.[varDef.name] || false;
                    return (
                      <div
                        key={varDef.name}
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "var(--space-xs)",
                          }}
                        >
                          <label
                            style={{
                              fontSize: "0.78rem",
                              fontWeight: 600,
                              color: "var(--color-primary)",
                            }}
                          >
                            {varDef.label}
                          </label>
                          {varDef.required && (
                            <span
                              style={{
                                fontSize: "0.65rem",
                                color: "var(--color-error)",
                                fontWeight: 700,
                              }}
                            >
                              *
                            </span>
                          )}
                          <span
                            data-testid={`server-card-credential-status-${varDef.name}`}
                            style={{
                              fontSize: "0.7rem",
                              marginLeft: "auto",
                              color: isConfigured
                                ? "var(--color-success)"
                                : "var(--color-text-dim)",
                            }}
                          >
                            {isConfigured ? "✓ Saved" : "✗ Not set"}
                          </span>
                        </div>
                        {varDef.description && (
                          <span
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--color-text-muted)",
                              fontStyle: "italic",
                            }}
                          >
                            {varDef.description}
                          </span>
                        )}
                        <input
                          type={varDef.secret ? "password" : "text"}
                          placeholder={
                            isConfigured
                              ? "••••••••  (already configured)"
                              : `Enter ${varDef.label}`
                          }
                          value={credentialValues[varDef.name] || ""}
                          onChange={(e) =>
                            setCredentialValues((prev) => ({
                              ...prev,
                              [varDef.name]: e.target.value,
                            }))
                          }
                          data-testid={`server-card-credential-input-${varDef.name}`}
                          style={{
                            padding: "6px 10px",
                            backgroundColor: "var(--color-surface)",
                            border: "1px solid var(--color-border)",
                            borderRadius: "var(--radius-md)",
                            color: "var(--color-primary)",
                            fontSize: "0.8rem",
                            fontFamily: "var(--font-mono)",
                            outline: "none",
                            transition: "border-color var(--transition-fast)",
                          }}
                          onFocus={(e) =>
                            (e.currentTarget.style.borderColor =
                              "var(--color-secondary)")
                          }
                          onBlur={(e) =>
                            (e.currentTarget.style.borderColor =
                              "var(--color-border)")
                          }
                        />
                      </div>
                    );
                  })}

                  {/* Save / Clear buttons */}
                  <div
                    style={{
                      display: "flex",
                      gap: "var(--space-sm)",
                      marginTop: "var(--space-xs)",
                    }}
                  >
                    <button
                      onClick={handleSaveCredentials}
                      disabled={
                        isSavingCreds ||
                        Object.values(credentialValues).every((v) => !v)
                      }
                      data-testid={`server-card-credentials-save-btn-${server.server_id}`}
                      style={{
                        padding: "var(--space-xs) var(--space-md)",
                        borderRadius: "var(--radius-md)",
                        fontSize: "0.78rem",
                        fontWeight: 600,
                        border: "none",
                        backgroundColor: "var(--color-secondary)",
                        color: "#ffffff",
                        cursor:
                          isSavingCreds ||
                          Object.values(credentialValues).every((v) => !v)
                            ? "not-allowed"
                            : "pointer",
                        transition: "all var(--transition-smooth)",
                      }}
                    >
                      {isSavingCreds ? "Saving..." : "Save Credentials"}
                    </button>
                    <button
                      onClick={handleClearCredentials}
                      data-testid={`server-card-credentials-clear-btn-${server.server_id}`}
                      style={{
                        padding: "var(--space-xs) var(--space-md)",
                        borderRadius: "var(--radius-md)",
                        fontSize: "0.78rem",
                        fontWeight: 600,
                        border: "1px solid var(--color-border)",
                        backgroundColor: "transparent",
                        color: "var(--color-text-muted)",
                        cursor: "pointer",
                        transition: "all var(--transition-fast)",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.borderColor =
                          "var(--color-error)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.borderColor =
                          "var(--color-border)")
                      }
                    >
                      Clear Credentials
                    </button>
                    {credentialSaved && (
                      <span
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--color-success)",
                          fontWeight: 500,
                          alignSelf: "center",
                        }}
                      >
                        ✓ Saved successfully
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Update Available Banner */}
          {updateAvailable && (
            <div
              data-testid={`server-card-update-banner-${server.server_id}`}
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid var(--color-warning)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-md)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: "0.85rem",
                color: "var(--color-warning)",
                textAlign: "left",
              }}
            >
              <span>
                <strong>Update available:</strong> v{updateAvailable.installed}{" "}
                → v{updateAvailable.latest}
              </span>
              <button
                onClick={handleUpdate}
                disabled={isUpdating}
                data-testid={`server-card-update-btn-${server.server_id}`}
                style={{
                  backgroundColor: "var(--color-warning)",
                  color: "var(--color-surface)",
                  border: "none",
                  padding: "var(--space-xs) var(--space-md)",
                  borderRadius: "var(--radius-md)",
                  fontWeight: 600,
                  cursor: isUpdating ? "not-allowed" : "pointer",
                }}
              >
                {isUpdating ? "Updating..." : "Update Now"}
              </button>
            </div>
          )}

          {/* Connection Info / Code Command */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              backgroundColor: "var(--color-surface-subtle)",
              padding: "var(--space-md)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--color-border)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
              color: "var(--color-text-muted)",
              wordBreak: "break-all",
              gap: "var(--space-xs)",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", gap: "var(--space-sm)" }}>
              <span style={{ color: "var(--color-primary)", fontWeight: 500 }}>
                Transport:
              </span>
              <span style={{ color: "var(--color-secondary)" }}>
                {server.type}
              </span>
            </div>
            {server.command && (
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span
                  style={{ color: "var(--color-primary)", fontWeight: 500 }}
                >
                  Endpoint/Command:
                </span>
                <span
                  style={{
                    whiteSpace: "pre-wrap",
                    marginTop: "2px",
                    color: "var(--color-secondary)",
                    fontSize: "0.75rem",
                  }}
                >
                  {Array.isArray(server.command)
                    ? server.command.join(" ")
                    : server.command}
                </span>
              </div>
            )}
          </div>
          <WorkspaceEnablement
            serverId={server.server_id}
            serverName={server.name}
            isInstalled={server.is_installed}
            workspaces={workspaces}
            showWorkspaces={showWorkspaces}
            togglingWorkspaceId={togglingWorkspaceId}
            onToggleVisible={() => setShowWorkspaces((visible) => !visible)}
            onToggleWorkspace={handleToggleWorkspace}
          />

          {/* Status Indicators & Control Buttons */}
          {(server.is_installed ||
            (!server.is_installed && !server.source_url)) && (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: "0.8rem",
                borderTop: "1px solid var(--color-border)",
                paddingTop: "var(--space-sm)",
                marginTop: "var(--space-xs)",
              }}
            >
              {server.is_installed ? (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--space-sm)",
                  }}
                >
                  <span
                    className={
                      server.status === "active"
                        ? "pulse-success-glow"
                        : undefined
                    }
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: getStatusColor(),
                      boxShadow: `0 0 8px ${getStatusColor()}`,
                      display: "inline-block",
                    }}
                  />
                  <span
                    style={{
                      color: "var(--color-primary)",
                      textTransform: "capitalize",
                      fontWeight: 500,
                    }}
                  >
                    {server.status}
                  </span>
                </div>
              ) : (
                <div />
              )}

              {/* Action Controls */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-md)",
                }}
              >
                {server.is_installed && isLocalServer && (
                  <button
                    onClick={handleCheckForUpdates}
                    disabled={isCheckingUpdate || isUpdating}
                    data-testid={`server-card-check-update-btn-${server.server_id}`}
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--color-secondary)",
                      backgroundColor: "transparent",
                      border: "none",
                      cursor: isCheckingUpdate ? "not-allowed" : "pointer",
                      transition: "all var(--transition-fast)",
                      padding: "0",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.color = "var(--color-primary)")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.color = "var(--color-secondary)")
                    }
                  >
                    {isCheckingUpdate ? "Checking..." : "↻ Check for Updates"}
                  </button>
                )}
                {upToDateMessage && (
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--color-success)",
                      fontWeight: 500,
                    }}
                  >
                    ✓ Up to date
                  </span>
                )}
                {!server.is_installed && !server.source_url && (
                  <button
                    onClick={handleDelete}
                    disabled={isDeleting || isInstalling}
                    data-testid={`server-card-remove-btn-${server.server_id}`}
                    style={{
                      color: "var(--color-text-dim)",
                      fontSize: "0.8rem",
                      fontWeight: 500,
                      cursor: "pointer",
                      border: "none",
                      background: "none",
                      transition: "color var(--transition-fast)",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.color = "#ef4444")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.color = "var(--color-text-dim)")
                    }
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Card-local dismissible notice block */}
          {cardNotice && (
            <div
              data-testid={`server-card-notice-${server.server_id}`}
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid var(--color-warning)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-md)",
                fontSize: "0.8rem",
                color: "var(--color-warning)",
                wordBreak: "break-word",
                textAlign: "left",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "var(--space-sm)",
              }}
            >
              <span>{cardNotice}</span>
              <button
                onClick={() => setCardNotice(null)}
                style={{
                  color: "var(--color-warning)",
                  cursor: "pointer",
                  fontWeight: "bold",
                  padding: "0 4px",
                  background: "none",
                  border: "none",
                }}
              >
                âœ•
              </button>
            </div>
          )}

          {/* Card-local dismissible error block */}
          {cardError && (
            <div
              data-testid={`server-card-error-${server.server_id}`}
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.08)",
                border: "1px solid var(--color-error)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-md)",
                fontSize: "0.8rem",
                color: "var(--color-error)",
                wordBreak: "break-word",
                textAlign: "left",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "var(--space-sm)",
              }}
            >
              <span>
                <strong>Error:</strong> {cardError}
              </span>
              <button
                onClick={() => setCardError(null)}
                style={{
                  color: "var(--color-error)",
                  cursor: "pointer",
                  fontWeight: "bold",
                  padding: "0 4px",
                  background: "none",
                  border: "none",
                }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Backend connection error message */}
          {server.error_message && (
            <div
              data-testid={`server-card-error-${server.server_id}`}
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.08)",
                border: "1px solid var(--color-error)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-md)",
                fontSize: "0.8rem",
                color: "var(--color-error)",
                wordBreak: "break-word",
                textAlign: "left",
              }}
            >
              <strong>Connection Error:</strong> {server.error_message}
            </div>
          )}

          {/* Discovered Tools Dropdown */}
          {server.is_installed && tools.length > 0 && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                borderTop: "1px solid var(--color-border)",
                paddingTop: "var(--space-md)",
                marginTop: "var(--space-xs)",
              }}
            >
              <button
                onClick={() => setShowTools(!showTools)}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  width: "100%",
                  fontSize: "0.85rem",
                  color: "var(--color-secondary)",
                  cursor: "pointer",
                  textAlign: "left",
                  fontWeight: 600,
                  border: "none",
                  background: "none",
                }}
              >
                <span>Exposed Tools ({tools.length})</span>
                <span>{showTools ? "▲" : "▼"}</span>
              </button>

              {showTools && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-md)",
                    marginTop: "var(--space-md)",
                  }}
                >
                  {tools.map((tool) => (
                    <div
                      key={tool.tool_id}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-lg)",
                        padding: "var(--space-md)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "var(--space-xs)",
                        textAlign: "left",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.8rem",
                            color: "var(--color-primary)",
                            fontWeight: 600,
                          }}
                        >
                          {tool.name}
                        </span>

                        {/* Tool Toggle Checkbox */}
                        <label
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            fontSize: "0.8rem",
                            color: "var(--color-text-muted)",
                            cursor: "pointer",
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={tool.is_enabled}
                            onChange={(e) =>
                              onToggleTool(tool.tool_id, e.target.checked)
                            }
                            style={{
                              cursor: "pointer",
                              accentColor: "var(--color-secondary)",
                            }}
                          />
                          {tool.is_enabled ? "Enabled" : "Disabled"}
                        </label>
                      </div>
                      {tool.description && (
                        <p
                          style={{
                            fontSize: "0.8rem",
                            color: "var(--color-secondary)",
                            fontStyle: "italic",
                            lineHeight: 1.4,
                          }}
                        >
                          {tool.description}
                        </p>
                      )}
                      {tool.input_schema &&
                        Object.keys(tool.input_schema).length > 0 && (
                          <div
                            style={{
                              fontSize: "0.75rem",
                              color: "var(--color-text-dim)",
                              marginTop: "4px",
                            }}
                          >
                            <span style={{ fontWeight: 600 }}>
                              Schema keys:
                            </span>{" "}
                            {Object.keys(
                              tool.input_schema.properties || {},
                            ).join(", ") || "none"}
                          </div>
                        )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
