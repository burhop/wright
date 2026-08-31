import NavItem from "../common/NavItem";
import type { NavigationSection } from "../../store/types";
import { useTools } from "../../store/tools";
import { processDefinitionViewEnabled } from "../../services/surfaces/feature-flags";

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
      id: "program-status",
      label: "Program Status",
      path: "/program-status",
      icon: "layout-dashboard",
      order: 2,
    },
    {
      id: "tool-registry",
      label: "Tool Registry",
      path: "/tool-registry",
      icon: "wrench",
      order: 3,
    },
    {
      id: "logs",
      label: "Logs",
      path: "/logs",
      icon: "logs",
      order: 4,
    },
    {
      id: "model-setup",
      label: "Model Setup",
      path: "/setup/model",
      icon: "settings",
      order: 5,
    },
    {
      id: "engineering-models",
      label: "Engineering Models",
      path: "/engineering-models",
      icon: "wrench",
      order: 6,
    },
    {
      id: "settings",
      label: "Settings",
      path: "/settings",
      icon: "settings",
      order: 7,
    },
    ...(processDefinitionViewEnabled()
      ? [
          {
            id: "process-definition",
            label: "Process Definition",
            path: "/processes/product-definition-v1",
            icon: "layout-dashboard",
            order: 8,
          },
        ]
      : []),
  ];

  return (
    <aside data-testid="sidebar" className="app-sidebar">
      <div className="app-sidebar__navigation">
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
