import React from "react";
import { useViewerPanel } from "../../store/viewer";
import type { FileDescriptor } from "../../services/viewer-panel/types";

interface ViewerInspectorProps {
  onClose: () => void;
  isResponsive: boolean;
}

export const ViewerInspector: React.FC<ViewerInspectorProps> = ({
  onClose,
  isResponsive,
}) => {
  const {
    activeTabPath,
    getProvider,
    openTabs,
    reloadDocument,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useViewerPanel();

  const activeTab = openTabs.find((t) => t.path === activeTabPath);

  const activeProvider = activeTabPath ? getProvider(activeTabPath) : null;

  // Resolve file details for capabilities lookup
  const ext = activeTabPath
    ? activeTabPath.split(".").pop()?.toLowerCase() || ""
    : "";
  const name = activeTabPath
    ? activeTabPath.split("/").pop() || activeTabPath
    : "";
  const file: FileDescriptor | null = activeTabPath
    ? {
        id: activeTabPath,
        uri: activeTabPath,
        name,
        extension: ext,
        mimeType: ext === "pdf" ? "application/pdf" : "text/plain",
      }
    : null;

  const capabilities =
    file && activeProvider
      ? activeProvider.getCapabilities(file, "preview")
      : null;

  const handleForcePing = () => {
    // Dispatch custom event to simulate pinging
    const event = new CustomEvent("viewer:force-ping", {
      detail: { path: activeTabPath },
    });
    window.dispatchEvent(event);
    alert("Forced watchdog heartbeat ping to panel host.");
  };

  const handleReload = async () => {
    if (file) {
      await reloadDocument(file);
    }
  };

  return (
    <div
      data-testid="viewer-inspector-panel"
      style={{
        width: "320px",
        backgroundColor: "var(--color-surface, #1e1e1e)",
        borderLeft: "1px solid var(--color-border, #2e2e2e)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        fontFamily: "var(--font-ui, system-ui, sans-serif)",
        fontSize: "0.8rem",
        color: "var(--color-primary, #ffffff)",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "var(--space-md, 12px)",
          borderBottom: "1px solid var(--color-border, #2e2e2e)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "var(--color-surface-subtle, #151515)",
        }}
      >
        <span
          style={{
            fontWeight: "600",
            letterSpacing: "0.5px",
            textTransform: "uppercase",
            fontSize: "0.75rem",
            color: "var(--color-secondary, #aaaaaa)",
          }}
        >
          Viewer Diagnostics
        </span>
        <button
          data-testid="viewer-inspector-close"
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            color: "var(--color-secondary, #aaaaaa)",
            cursor: "pointer",
            fontSize: "0.9rem",
            padding: "2px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          title="Close Diagnostics"
        ></button>
      </div>

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "var(--space-md, 12px)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-md, 12px)",
        }}
      >
        {activeTabPath ? (
          <>
            {/* General Info */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs, 6px)",
              }}
            >
              <div
                style={{
                  fontWeight: "600",
                  color: "var(--color-secondary, #aaaaaa)",
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                }}
              >
                Document Details
              </div>
              <div
                style={{
                  backgroundColor: "var(--color-surface-subtle, #151515)",
                  padding: "var(--space-sm, 8px)",
                  borderRadius: "var(--radius-sm, 4px)",
                  border: "1px solid var(--color-border, #2e2e2e)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "4px",
                  }}
                >
                  <span style={{ color: "var(--color-secondary, #aaaaaa)" }}>
                    File Name:
                  </span>
                  <span style={{ fontWeight: "500" }}>{activeTab?.name}</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "4px",
                  }}
                >
                  <span style={{ color: "var(--color-secondary, #aaaaaa)" }}>
                    URI / Path:
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono, monospace)",
                      fontSize: "0.7rem",
                      textOverflow: "ellipsis",
                      overflow: "hidden",
                      whiteSpace: "nowrap",
                      maxWidth: "160px",
                    }}
                    title={activeTabPath}
                  >
                    {activeTabPath}
                  </span>
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "4px",
                  }}
                >
                  <span style={{ color: "var(--color-secondary, #aaaaaa)" }}>
                    MIME Type:
                  </span>
                  <span>{file?.mimeType}</span>
                </div>
                <div
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <span style={{ color: "var(--color-secondary, #aaaaaa)" }}>
                    Is Dirty:
                  </span>
                  <span
                    style={{
                      color: activeTab?.isDirty
                        ? "var(--color-warning, #ffb000)"
                        : "var(--color-success, #10b981)",
                      fontWeight: "600",
                    }}
                  >
                    {activeTab?.isDirty ? "Yes " : "No"}
                  </span>
                </div>
              </div>
            </div>

            {/* Provider and Capabilities */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs, 6px)",
              }}
            >
              <div
                style={{
                  fontWeight: "600",
                  color: "var(--color-secondary, #aaaaaa)",
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                }}
              >
                Viewer Adapter
              </div>
              <div
                style={{
                  backgroundColor: "var(--color-surface-subtle, #151515)",
                  padding: "var(--space-sm, 8px)",
                  borderRadius: "var(--radius-sm, 4px)",
                  border: "1px solid var(--color-border, #2e2e2e)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "6px",
                  }}
                >
                  <span style={{ color: "var(--color-secondary, #aaaaaa)" }}>
                    Provider ID:
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono, monospace)",
                      fontSize: "0.75rem",
                    }}
                  >
                    {activeProvider?.id || "None"}
                  </span>
                </div>

                <div
                  style={{
                    borderTop: "1px solid var(--color-border, #2e2e2e)",
                    paddingTop: "6px",
                    marginTop: "6px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "500",
                      marginBottom: "6px",
                      fontSize: "0.75rem",
                      color: "var(--color-secondary, #aaaaaa)",
                    }}
                  >
                    Resolved Capabilities:
                  </div>
                  {capabilities ? (
                    <div
                      style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}
                    >
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "10px",
                          backgroundColor: capabilities.canEdit
                            ? "rgba(16, 185, 129, 0.15)"
                            : "rgba(255, 255, 255, 0.05)",
                          color: capabilities.canEdit ? "#10b981" : "#888888",
                          fontSize: "0.65rem",
                        }}
                      >
                        Editable: {capabilities.canEdit ? "Yes" : "No"}
                      </span>
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "10px",
                          backgroundColor: capabilities.canAnnotate
                            ? "rgba(16, 185, 129, 0.15)"
                            : "rgba(255, 255, 255, 0.05)",
                          color: capabilities.canAnnotate
                            ? "#10b981"
                            : "#888888",
                          fontSize: "0.65rem",
                        }}
                      >
                        Annotate: {capabilities.canAnnotate ? "Yes" : "No"}
                      </span>
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "10px",
                          backgroundColor: capabilities.supports3DControls
                            ? "rgba(16, 185, 129, 0.15)"
                            : "rgba(255, 255, 255, 0.05)",
                          color: capabilities.supports3DControls
                            ? "#10b981"
                            : "#888888",
                          fontSize: "0.65rem",
                        }}
                      >
                        3D Controls:{" "}
                        {capabilities.supports3DControls ? "Yes" : "No"}
                      </span>
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: "10px",
                          backgroundColor: capabilities.prefersIsolation
                            ? "rgba(239, 68, 68, 0.15)"
                            : "rgba(255, 255, 255, 0.05)",
                          color: capabilities.prefersIsolation
                            ? "#ef4444"
                            : "#888888",
                          fontSize: "0.65rem",
                        }}
                      >
                        Isolated: {capabilities.prefersIsolation ? "Yes" : "No"}
                      </span>
                    </div>
                  ) : (
                    <span style={{ fontStyle: "italic", color: "#888888" }}>
                      No capabilities registered
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Watchdog Heartbeat Diagnostics */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs, 6px)",
              }}
            >
              <div
                style={{
                  fontWeight: "600",
                  color: "var(--color-secondary, #aaaaaa)",
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                }}
              >
                Watchdog Status
              </div>
              <div
                style={{
                  backgroundColor: "var(--color-surface-subtle, #151515)",
                  padding: "var(--space-sm, 8px)",
                  borderRadius: "var(--radius-sm, 4px)",
                  border: "1px solid var(--color-border, #2e2e2e)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>Watchdog State:</span>
                <span
                  data-testid="inspector-watchdog-state"
                  style={{
                    fontWeight: "700",
                    color: isResponsive
                      ? "var(--color-success, #10b981)"
                      : "var(--color-error, #ef4444)",
                    backgroundColor: isResponsive
                      ? "rgba(16, 185, 129, 0.15)"
                      : "rgba(239, 68, 68, 0.15)",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    fontSize: "0.7rem",
                  }}
                >
                  {isResponsive ? "RESPONSIVE" : "UNRESPONSIVE"}
                </span>
              </div>
            </div>

            {/* Actions / Troubleshooting */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs, 6px)",
              }}
            >
              <div
                style={{
                  fontWeight: "600",
                  color: "var(--color-secondary, #aaaaaa)",
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                }}
              >
                Troubleshooting Tools
              </div>
              <div
                style={{ display: "flex", flexDirection: "column", gap: "6px" }}
              >
                <button
                  data-testid="inspector-force-ping"
                  onClick={handleForcePing}
                  style={{
                    backgroundColor: "var(--color-surface-subtle, #151515)",
                    color: "var(--color-primary, #ffffff)",
                    border: "1px solid var(--color-border, #2e2e2e)",
                    borderRadius: "var(--radius-sm, 4px)",
                    padding: "var(--space-sm, 8px)",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "0.75rem",
                    textAlign: "left",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor =
                      "rgba(255, 255, 255, 0.05)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor =
                      "var(--color-surface-subtle)")
                  }
                >
                  Trigger Watchdog Heartbeat Ping
                </button>

                <button
                  data-testid="inspector-reload-tab"
                  onClick={handleReload}
                  style={{
                    backgroundColor: "var(--color-surface-subtle, #151515)",
                    color: "var(--color-primary, #ffffff)",
                    border: "1px solid var(--color-border, #2e2e2e)",
                    borderRadius: "var(--radius-sm, 4px)",
                    padding: "var(--space-sm, 8px)",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "0.75rem",
                    textAlign: "left",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor =
                      "rgba(255, 255, 255, 0.05)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor =
                      "var(--color-surface-subtle)")
                  }
                >
                  Force Reload Viewer Document
                </button>

                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    data-testid="inspector-undo"
                    onClick={() => undo(activeTabPath)}
                    disabled={!canUndo(activeTabPath)}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface-subtle, #151515)",
                      color: "var(--color-primary, #ffffff)",
                      border: "1px solid var(--color-border, #2e2e2e)",
                      borderRadius: "var(--radius-sm, 4px)",
                      padding: "6px",
                      cursor: canUndo(activeTabPath)
                        ? "pointer"
                        : "not-allowed",
                      opacity: canUndo(activeTabPath) ? 1 : 0.45,
                      fontWeight: "600",
                      fontSize: "0.7rem",
                    }}
                  >
                    Undo Edit
                  </button>
                  <button
                    data-testid="inspector-redo"
                    onClick={() => redo(activeTabPath)}
                    disabled={!canRedo(activeTabPath)}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface-subtle, #151515)",
                      color: "var(--color-primary, #ffffff)",
                      border: "1px solid var(--color-border, #2e2e2e)",
                      borderRadius: "var(--radius-sm, 4px)",
                      padding: "6px",
                      cursor: canRedo(activeTabPath)
                        ? "pointer"
                        : "not-allowed",
                      opacity: canRedo(activeTabPath) ? 1 : 0.45,
                      fontWeight: "600",
                      fontSize: "0.7rem",
                    }}
                  >
                    Redo Edit
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "var(--color-secondary, #aaaaaa)",
              textAlign: "center",
              gap: "var(--space-sm)",
            }}
          >
            <span style={{ fontSize: "2rem" }}></span>
            <span>
              Select any active tab in the editor to inspect diagnostic
              attributes and capabilities.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViewerInspector;
