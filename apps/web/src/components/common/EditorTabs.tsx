import React from "react";
import type { EditorTab } from "../../store/types";

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
      style={{
        display: "flex",
        backgroundColor: "var(--color-neutral, #1e1e1e)",
        borderBottom: "1px solid var(--color-border)",
        overflowX: "auto",
        whiteSpace: "nowrap",
        height: "35px",
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab.path === activeTabPath;
        return (
          <div
            key={tab.path}
            onClick={() => onSelectTab(tab.path)}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0 var(--space-md)",
              borderRight: "1px solid var(--color-border)",
              backgroundColor: isActive
                ? "var(--color-surface)"
                : "var(--color-neutral)",
              color: isActive
                ? "var(--color-primary)"
                : "var(--color-secondary)",
              cursor: "pointer",
              fontSize: "0.75rem",
              fontWeight: isActive ? "600" : "400",
              fontFamily: "var(--font-ui)",
              height: "100%",
              userSelect: "none",
              transition: "background-color 0.2s",
            }}
          >
            <span style={{ marginRight: "var(--space-sm)" }}>
              {tab.type === "stl" ? "🧊" : tab.type === "image" ? "🖼️" : "📄"}
            </span>
            <span
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: "120px",
              }}
            >
              {tab.name}
              {tab.isDirty && " *"}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCloseTab(tab.path);
              }}
              style={{
                marginLeft: "var(--space-md)",
                background: "none",
                border: "none",
                color: "inherit",
                cursor: "pointer",
                opacity: 0.6,
                fontSize: "0.75rem",
                padding: "2px",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default EditorTabs;
