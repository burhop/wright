import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import DashboardPage from './components/pages/DashboardPage';
import WorkspacePage from './components/pages/WorkspacePage';
import ToolRegistryPage from './components/pages/ToolRegistryPage';
import FileVaultPage from './components/pages/FileVaultPage';
import NotFoundPage from './components/pages/NotFoundPage';

import { ToolsProvider } from './store/tools';
import { ChatProvider } from './store/sessions';

function App() {
  return (
    <BrowserRouter>
      <ChatProvider>
        <ToolsProvider>
          <AppShell>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
              <Route path="/tool-registry" element={<ToolRegistryPage />} />
              <Route path="/file-vault" element={<FileVaultPage />} />
              {/* Backward compatibility: redirect old /agent-chat route to dashboard */}
              <Route path="/agent-chat" element={<Navigate to="/" replace />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AppShell>
        </ToolsProvider>
      </ChatProvider>
    </BrowserRouter>
  );
}

export default App;
