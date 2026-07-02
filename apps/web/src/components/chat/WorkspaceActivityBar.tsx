import {
  FolderIcon,
  GitIcon,
  SettingsIcon,
  BackIcon,
  MCPIcon,
  BookOpenIcon,
} from "../common/Icons";

export type WorkspaceSidebarId =
  | "marketplace"
  | "files"
  | "git"
  | "settings"
  | "docs";

interface WorkspaceActivityBarProps {
  activeSidebar: WorkspaceSidebarId;
  isSidebarCollapsed: boolean;
  onBack: () => void;
  onSelectSidebar: (sidebar: WorkspaceSidebarId) => void;
}

const items: Array<{
  id: WorkspaceSidebarId;
  testId: string;
  title: string;
  icon: (size: number) => JSX.Element;
}> = [
  {
    id: "files",
    testId: "activity-bar-explorer-btn",
    title: "Workspace Files",
    icon: (size) => <FolderIcon size={size} />,
  },
  {
    id: "marketplace",
    testId: "activity-bar-mcp-btn",
    title: "MCP Tools",
    icon: (size) => <MCPIcon size={size} />,
  },
  {
    id: "git",
    testId: "activity-bar-git-btn",
    title: "Git Version Control",
    icon: (size) => <GitIcon size={size} />,
  },
  {
    id: "settings",
    testId: "activity-bar-settings-btn",
    title: "Workspace Settings",
    icon: (size) => <SettingsIcon size={size} />,
  },
  {
    id: "docs",
    testId: "activity-bar-docs-btn",
    title: "Docs & Tutorials",
    icon: (size) => <BookOpenIcon size={size} />,
  },
];

function iconButtonStyle(isActive = false) {
  return {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "var(--space-xs)",
    opacity: isActive ? 1 : 0.45,
    color: isActive ? "var(--color-secondary)" : "var(--color-primary)",
  };
}

export function WorkspaceActivityBar({
  activeSidebar,
  isSidebarCollapsed,
  onBack,
  onSelectSidebar,
}: WorkspaceActivityBarProps) {
  return (
    <div
      style={{
        backgroundColor: "var(--color-surface-elevated)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: "var(--space-md)",
        gap: "var(--space-md)",
        zIndex: 5,
      }}
    >
      <button
        data-testid="activity-bar-back-btn"
        onClick={onBack}
        style={iconButtonStyle(false)}
        title="Back to Dashboard"
        className="activity-bar-icon"
      >
        <BackIcon size={20} />
      </button>
      {items.map((item) => {
        const isActive = !isSidebarCollapsed && activeSidebar === item.id;
        return (
          <button
            key={item.id}
            data-testid={item.testId}
            onClick={() => onSelectSidebar(item.id)}
            style={iconButtonStyle(isActive)}
            title={item.title}
            className="activity-bar-icon"
          >
            {item.icon(20)}
          </button>
        );
      })}
    </div>
  );
}
