import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import { isDesktop } from "../../services/host-adapter";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isWorkspaceView = location.pathname.startsWith("/workspace/");

  const desktop = isDesktop();

  return (
    <div
      data-testid="app-shell"
      data-desktop={desktop}
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100svh",
        width: "100vw",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
        paddingTop: desktop ? "var(--titlebar-height, 34px)" : "0px",
      }}
    >
      <Header />

      <div
        className={`app-shell__body${
          isWorkspaceView ? " app-shell__body--workspace" : ""
        }`}
      >
        {!isWorkspaceView && <Sidebar />}

        <main className="app-shell__main">{children}</main>
      </div>
    </div>
  );
}

export default AppShell;
