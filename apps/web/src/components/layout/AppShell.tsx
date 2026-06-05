import { useEffect, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import { webMcpService } from "../../services/webmcp-service";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isWorkspaceView = location.pathname.startsWith("/workspace/");

  useEffect(() => {
    webMcpService.connect();
    return () => {
      webMcpService.disconnect();
    };
  }, []);

  return (
    <div
      data-testid="app-shell"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100svh",
        width: "100vw",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
      }}
    >
      <Header />

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {!isWorkspaceView && <Sidebar />}

        <main
          style={{
            flex: 1,
            overflowY: "auto",
            padding: isWorkspaceView ? "0" : "var(--space-xl)",
            backgroundColor: "var(--color-neutral)",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppShell;
