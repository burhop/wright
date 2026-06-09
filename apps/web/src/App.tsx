import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./components/pages/DashboardPage";
import WorkspacePage from "./components/pages/WorkspacePage";
import ToolRegistryPage from "./components/pages/ToolRegistryPage";
import FileVaultPage from "./components/pages/FileVaultPage";
import NotFoundPage from "./components/pages/NotFoundPage";
import SetupPage from "./components/pages/SetupPage";
import LogsPage from "./components/pages/LogsPage";
import SettingsPage from "./components/pages/SettingsPage";

import { ToolsProvider } from "./store/tools";
import { ChatProvider } from "./store/sessions";
import { ViewerPanelProvider } from "./store/viewer";

const getApiUrl = (path: string) => {
  if (typeof window === "undefined") return `http://127.0.0.1:8000${path}`;
  const host = window.location.hostname;
  const port = window.location.port;
  const base =
    port === "5173" || port === "5174" ? `http://${host}:8000` : "";
  return `${base}${path}`;
};

function App() {
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(getApiUrl("/api/setup/status"))
      .then((res) => res.json())
      .then((data) => {
        setIsConfigured(data.is_configured);
        const activeTheme = data.theme || "dark";
        document.documentElement.setAttribute("data-theme", activeTheme);
      })
      .catch(() => {
        // Fallback to true on errors to avoid blocking in purely static/offline environments
        setIsConfigured(true);
        document.documentElement.setAttribute("data-theme", "dark");
      });
  }, []);

  if (isConfigured === null) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          backgroundColor: "var(--color-neutral)",
          color: "var(--color-primary)",
          fontFamily: "var(--font-ui)",
        }}
      >
        <div style={{ display: "flex", gap: "4px" }}>
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
        </div>
      </div>
    );
  }

  if (!isConfigured) {
    return <SetupPage onConfigured={() => setIsConfigured(true)} />;
  }

  return (
    <BrowserRouter>
      <ChatProvider>
        <ViewerPanelProvider>
          <ToolsProvider>
            <AppShell>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route
                path="/workspace/:workspaceId"
                element={<WorkspacePage />}
              />
              <Route path="/tool-registry" element={<ToolRegistryPage />} />
              <Route path="/file-vault" element={<FileVaultPage />} />
              <Route path="/logs" element={<LogsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              {/* Backward compatibility: redirect old /agent-chat route to dashboard */}
              <Route path="/agent-chat" element={<Navigate to="/" replace />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
            </AppShell>
          </ToolsProvider>
        </ViewerPanelProvider>
      </ChatProvider>
    </BrowserRouter>
  );
}

export default App;
