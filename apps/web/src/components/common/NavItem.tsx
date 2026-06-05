import { NavLink } from "react-router-dom";
import {
  DashboardIcon,
  AgentChatIcon,
  ToolRegistryIcon,
  FileVaultIcon,
} from "./Icons";

interface NavItemProps {
  label: string;
  path: string;
  id: string;
  icon: string;
}

const renderIcon = (iconName: string) => {
  switch (iconName) {
    case "layout-dashboard":
      return <DashboardIcon size={18} />;
    case "message-square":
      return <AgentChatIcon size={18} />;
    case "wrench":
      return <ToolRegistryIcon size={18} />;
    case "folder":
      return <FileVaultIcon size={18} />;
    default:
      return null;
  }
};

export function NavItem({ label, path, id, icon }: NavItemProps) {
  return (
    <NavLink
      to={path}
      data-testid={`nav-${id}`}
      style={({ isActive }) => ({
        display: "block",
        padding: "var(--space-md) var(--space-lg)",
        color: isActive ? "var(--color-primary)" : "var(--color-secondary)",
        backgroundColor: isActive ? "rgba(56, 189, 248, 0.08)" : "transparent",
        borderRadius: "var(--radius-lg)",
        fontSize: "0.95rem",
        fontWeight: isActive ? "600" : "500",
        fontFamily: "var(--font-ui)",
        borderLeft: isActive
          ? "3px solid var(--color-secondary)"
          : "3px solid transparent",
        transition: "all var(--transition-smooth)",
        cursor: "pointer",
        boxShadow: isActive ? "var(--shadow-glow)" : "none",
      })}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-md)",
        }}
      >
        {renderIcon(icon)}
        <span>{label}</span>
      </div>
    </NavLink>
  );
}

export default NavItem;
