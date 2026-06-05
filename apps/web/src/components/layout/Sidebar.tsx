import NavItem from "../common/NavItem";
import type { NavigationSection } from "../../store/types";

const SECTIONS: NavigationSection[] = [
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
    id: "file-vault",
    label: "File Vault",
    path: "/file-vault",
    icon: "folder",
    order: 3,
  },
];

export function Sidebar() {
  return (
    <aside
      data-testid="sidebar"
      style={{
        width: "240px",
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
        {SECTIONS.map((sec) => (
          <NavItem
            key={sec.id}
            id={sec.id}
            label={sec.label}
            path={sec.path}
            icon={sec.icon}
          />
        ))}
      </div>
    </aside>
  );
}

export default Sidebar;
