import React, { useEffect, useRef } from "react";
import type { EditorTab } from "../../store/viewer";
import { CloseIcon } from "../common/Icons";

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
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const reveal = () => container.current?.querySelector<HTMLElement>('[aria-selected="true"]')?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    reveal();
    if (typeof ResizeObserver === "undefined" || !container.current) return;
    const observer = new ResizeObserver(reveal);
    observer.observe(container.current);
    return () => observer.disconnect();
  }, [activeTabPath, tabs.length]);
  return (
    <div
      ref={container}
      className="editor-tabs-container"
      data-testid="editor-tabs-container"
      role="tablist"
      aria-label="Open documents"
      style={{
        display: "flex",
        backgroundColor: "var(--color-surface-subtle)",
        borderBottom: "1px solid var(--color-border, #2e2e2e)",
        overflowX: "auto",
        whiteSpace: "nowrap",
        height: "32px",
        alignItems: "center",
        paddingLeft: "0",
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab.path === activeTabPath;
        return (
          <div
            key={tab.path}
            onClick={() => onSelectTab(tab.path)}
            data-testid={`editor-tab-${tab.path}`}
            title={tab.path}
            role="tab"
            aria-label={tab.name.replace(/\.workflow\.wflow$/i, ".wflow")}
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            onKeyDown={e => {
              if (e.target !== e.currentTarget) return;
              const index = tabs.indexOf(tab);
              const next = e.key === "ArrowRight" ? (index + 1) % tabs.length : e.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length : e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : -1;
              if (next >= 0) { e.preventDefault(); onSelectTab(tabs[next]!.path); (e.currentTarget.parentElement?.children[next] as HTMLElement)?.focus(); }
              if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelectTab(tab.path); }
            }}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0 8px",
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
              flexShrink: 0,
              transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
              position: "relative",
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.backgroundColor =
                  "var(--color-surface-hover)";
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
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: "180px",
                marginRight: "var(--space-sm, 6px)",
              }}
            >
              {tab.name.replace(/\.workflow\.wflow$/i, ".wflow")}
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
              type="button"
              aria-label={`Close ${tab.name}`}
              title={`Close ${tab.name}`}
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
                opacity: isActive ? 0.85 : 0.65,
                padding: "2px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "50%",
                width: "24px",
                height: "24px",
                flexShrink: 0,
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.backgroundColor =
                  "rgba(255, 255, 255, 0.12)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = isActive ? "0.85" : "0.65";
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              <CloseIcon size={13} aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default EditorTabs;
