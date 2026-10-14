import { lazy, Suspense, useEffect } from "react";
import {
  createBrowserRouter,
  createHashRouter,
  createRoutesFromElements,
  RouterProvider,
  Outlet,
  Route,
  Navigate,
  useLocation,
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
import ProgramStatusPage from "./components/pages/ProgramStatusPage";
import ProcessDefinitionPage from "./components/pages/ProcessDefinitionPage";
import { AuthGate } from "./components/common/AuthGate";

import { ToolsProvider } from "./store/tools";
import { ChatProvider } from "./store/sessions";
import { ViewerPanelProvider } from "./store/viewer";
import { SurfaceStateProvider } from "./store/surfaces";
import { hostAdapter } from "./services/host-adapter";
import {
  processDefinitionViewEnabled,
  workspaceSurfacesEnabled,
} from "./services/surfaces/feature-flags";
import { useDesktopIntegration } from "./hooks/useDesktopIntegration";
import { initializeSavedTheme } from "./services/ui-preferences";
import { WorkspaceNavigationGuard } from "./components/chat/WorkspaceNavigationGuard";

const NativeProcessPage = lazy(
  () => import("./components/pages/NativeProcessPage"),
);

function AppContent() {
  const location = useLocation();
  const desktopConversation =
    new URLSearchParams(location.search).get("host") === "openai-desktop";
  const content = (
    <ViewerPanelProvider>
      <ToolsProvider>
        <AuthGate>
          <AppShell>
            <WorkspaceNavigationGuard />
            <Outlet />
          </AppShell>
        </AuthGate>
      </ToolsProvider>
    </ViewerPanelProvider>
  );
  return (
    <ChatProvider desktopConversation={desktopConversation}>
      {workspaceSurfacesEnabled() ? (
        <SurfaceStateProvider>{content}</SurfaceStateProvider>
      ) : (
        content
      )}
    </ChatProvider>
  );
}

// Created once by the entry point, outside React rendering and StrictMode.
// The data router supplies navigation blocking for links and browser history.
export function createAppRouter() {
  const createRouter =
    hostAdapter.getRouterType() === "hash"
      ? createHashRouter
      : createBrowserRouter;
  return createRouter(
    createRoutesFromElements(
      <Route element={<AppContent />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        <Route path="/tool-registry" element={<ToolRegistryPage />} />
        <Route path="/file-vault" element={<FileVaultPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/setup/model" element={<ModelSetupPage />} />
        <Route
          path="/engineering-models"
          element={<EngineeringModelLibraryPage />}
        />
        <Route path="/program-status" element={<ProgramStatusPage />} />
        <Route
          path="/native-processes"
          element={
            <Suspense fallback={<p role="status">Loading native processes…</p>}>
              <NativeProcessPage />
            </Suspense>
          }
        />
        {processDefinitionViewEnabled() && (
          <Route
            path="/processes/product-definition-v1"
            element={<ProcessDefinitionPage />}
          />
        )}
        <Route path="/settings" element={<SettingsPage />} />
        {/* Backward compatibility: redirect old /agent-chat route to dashboard */}
        <Route path="/agent-chat" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>,
    ),
  );
}

function App({ router }: { router: ReturnType<typeof createAppRouter> }) {
  useDesktopIntegration();
  useEffect(() => initializeSavedTheme(), []);
  return <RouterProvider router={router} />;
}

export default App;
