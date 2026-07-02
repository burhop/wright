import React from "react";
import type { EditorTab } from "../../store/viewer";

interface EditorTabsProps {
  tabs: EditorTab[];
  activeTabPath: string | null;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string) => void;
}

export const EditorTabs: React.FC<EditorTabsProps> = ({
  tabs,
  activeTabPath,
  onSelectTab,
  onCloseTab,
}) => {
  return (
    <div
      className="editor-tabs-container"
      data-testid="editor-tabs-container"
      style={{
        display: "flex",
        backgroundColor: "var(--color-neutral-dark, #121212)",
        borderBottom: "1px solid var(--color-border, #2e2e2e)",
        overflowX: "auto",
        whiteSpace: "nowrap",
        height: "38px",
        alignItems: "center",
        paddingLeft: "var(--space-xs, 4px)",
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab.path === activeTabPath;
        const ext = tab.path.split(".").pop()?.toLowerCase() || "";

        // Premium type icons
        let icon = "";
        if (ext === "stl" || ext === "step" || ext === "iges") icon = "";
        else if (
          ["png", "jpg", "jpeg", "svg", "gif", "webp", "bmp"].includes(ext)
        )
          icon = "";
        else if (ext === "pdf") icon = "";
        else if (ext === "md") icon = "";
        else if (["py", "js", "ts", "tsx", "json", "scad"].includes(ext))
          icon = "";

        return (
          <div
            key={tab.path}
            onClick={() => onSelectTab(tab.path)}
            data-testid={`editor-tab-${tab.path}`}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0 var(--space-md, 12px)",
              borderRight: "1px solid var(--color-border, #2e2e2e)",
              borderTop: isActive
                ? "2px solid var(--color-primary-active, #007acc)"
                : "2px solid transparent",
              backgroundColor: isActive
                ? "var(--color-surface, #1e1e1e)"
                : "transparent",
              color: isActive
                ? "var(--color-primary, #ffffff)"
                : "var(--color-secondary, #aaaaaa)",
              cursor: "pointer",
              fontSize: "0.75rem",
              fontWeight: isActive ? "600" : "400",
              fontFamily: "var(--font-ui, system-ui, sans-serif)",
              height: "100%",
              userSelect: "none",
              transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
              position: "relative",
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.backgroundColor =
                  "var(--color-neutral-hover, rgba(255, 255, 255, 0.05))";
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.backgroundColor = "transparent";
              }
            }}
          >
            <span
              style={{
                marginRight: "var(--space-sm, 6px)",
                fontSize: "0.9rem",
              }}
            >
              {icon}
            </span>
            <span
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: "140px",
                marginRight: "var(--space-sm, 6px)",
              }}
            >
              {tab.name}
            </span>

            {/* Dirty Indicator */}
            {tab.isDirty && (
              <span
                data-testid={`editor-tab-dirty-${tab.path}`}
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "var(--color-warning, #ffb000)",
                  marginRight: "var(--space-xs, 4px)",
                  display: "inline-block",
                }}
                title="Unsaved changes"
              />
            )}

            <button
              onClick={(e) => {
                e.stopPropagation();
                onCloseTab(tab.path);
              }}
              data-testid={`editor-tab-close-${tab.path}`}
              style={{
                background: "none",
                border: "none",
                color: "inherit",
                cursor: "pointer",
                opacity: 0.5,
                fontSize: "0.7rem",
                padding: "2px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "50%",
                width: "16px",
                height: "16px",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.backgroundColor =
                  "rgba(255, 255, 255, 0.1)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "0.5";
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            ></button>
          </div>
        );
      })}
    </div>
  );
};

export default EditorTabs;
