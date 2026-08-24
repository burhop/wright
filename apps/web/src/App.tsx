import { lazy, Suspense, useEffect } from "react";
import {
  BrowserRouter,
  HashRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./components/pages/DashboardPage";
import WorkspacePage from "./components/pages/WorkspacePage";
import ToolRegistryPage from "./components/pages/ToolRegistryPage";
import FileVaultPage from "./components/pages/FileVaultPage";
import NotFoundPage from "./components/pages/NotFoundPage";
import LogsPage from "./components/pages/LogsPage";
import SettingsPage from "./components/pages/SettingsPage";
import ModelSetupPage from "./components/pages/ModelSetupPage";
import EngineeringModelLibraryPage from "./components/pages/EngineeringModelLibraryPage";
import { AuthGate } from "./components/common/AuthGate";

import { ToolsProvider } from "./store/tools";
import { ChatProvider } from "./store/sessions";
import { ViewerPanelProvider } from "./store/viewer";
import { SurfaceStateProvider } from "./store/surfaces";
import { hostAdapter } from "./services/host-adapter";
import {
  engineeringWorkflowPrototypeEnabled,
  workspaceSurfacesEnabled,
} from "./services/surfaces/feature-flags";
import { useDesktopIntegration } from "./hooks/useDesktopIntegration";

const EngineeringWorkflowVisualSlice = lazy(
  () =>
    import("./prototypes/engineering-workflow/EngineeringWorkflowVisualSlice"),
);
const ReactFlowBakeoffHarness = lazy(
  () =>
    import("./prototypes/engineering-workflow/canvas/react-flow/ReactFlowBakeoffHarness"),
);

function App() {
  useDesktopIntegration();

  useEffect(() => {
    hostAdapter
      .fetch(`${hostAdapter.getApiBaseUrl()}/api/setup/status`)
      .then((res) => res.json())
      .then((data) => {
        const activeTheme = data.theme || "dark";
        document.documentElement.setAttribute("data-theme", activeTheme);
      })
      .catch(() => {
        document.documentElement.setAttribute("data-theme", "dark");
      });
  }, []);

  const Router =
    hostAdapter.getRouterType() === "hash" ? HashRouter : BrowserRouter;

  const prototypeElement = engineeringWorkflowPrototypeEnabled() ? (
    <Suspense fallback={<p role="status">Loading visual prototype.</p>}>
      <EngineeringWorkflowVisualSlice />
    </Suspense>
  ) : (
    <NotFoundPage />
  );

  const reactFlowBakeoffElement = engineeringWorkflowPrototypeEnabled() ? (
    <Suspense fallback={<p role="status">Loading React Flow bakeoff.</p>}>
      <ReactFlowBakeoffHarness />
    </Suspense>
  ) : (
    <NotFoundPage />
  );

  const securedContent = (
    <ViewerPanelProvider>
      <ToolsProvider>
        <AuthGate>
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
              <Route path="/setup/model" element={<ModelSetupPage />} />
              <Route
                path="/engineering-models"
                element={<EngineeringModelLibraryPage />}
              />
              <Route path="/settings" element={<SettingsPage />} />
              {/* Backward compatibility: redirect old /agent-chat route to dashboard */}
              <Route path="/agent-chat" element={<Navigate to="/" replace />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AppShell>
        </AuthGate>
      </ToolsProvider>
    </ViewerPanelProvider>
  );

  const applicationContent = workspaceSurfacesEnabled() ? (
    <SurfaceStateProvider>{securedContent}</SurfaceStateProvider>
  ) : (
    securedContent
  );

  return (
    <Router>
      <Routes>
        <Route
          path="/prototype/engineering-workflow"
          element={prototypeElement}
        />
        <Route
          path="/prototype/engineering-workflow/bakeoff/react-flow"
          element={reactFlowBakeoffElement}
        />
        <Route
          path="*"
          element={<ChatProvider>{applicationContent}</ChatProvider>}
        />
      </Routes>
    </Router>
  );
}

export default App;
