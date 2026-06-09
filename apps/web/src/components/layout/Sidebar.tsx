import NavItem from "../common/NavItem";
import type { NavigationSection } from "../../store/types";
import { useTools } from "../../store/tools";

export function Sidebar() {
  let servers = [];
  try {
    const toolsContext = useTools();
    servers = toolsContext.servers || [];
  } catch (e) {
    // Fallback when rendered outside ToolsProvider (e.g. in isolated tests)
  }

  const sections: NavigationSection[] = [
    {
      id: "dashboard",
      label: "Dashboard",
      path: "/",
      icon: "layout-dashboard",
      order: 1,
    },
    {
      id: "tool-registry",
      label: "Tool Registry",
      path: "/tool-registry",
      icon: "wrench",
      order: 2,
    },
    {
      id: "logs",
      label: "Logs",
      path: "/logs",
      icon: "logs",
      order: 3,
    },
    {
      id: "settings",
      label: "Settings",
      path: "/settings",
      icon: "settings",
      order: 4,
    },
  ];

  return (
    <aside
      data-testid="sidebar"
      style={{
        width: "180px",
        backgroundColor: "var(--color-surface-subtle)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        padding: "var(--space-lg) var(--space-md)",
        gap: "var(--space-sm)",
        height: "100%",
        overflowY: "auto",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-xs)",
        }}
      >
        {sections.map((sec) => (
          <NavItem
            key={sec.id}
            id={sec.id}
            label={sec.label}
            path={sec.path}
            icon={sec.icon}
            badge={sec.id === "tool-registry" ? servers.length : undefined}
          />
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;
