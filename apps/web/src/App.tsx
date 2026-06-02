import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import DashboardPage from './components/pages/DashboardPage';
import AgentChatPage from './components/pages/AgentChatPage';
import ToolRegistryPage from './components/pages/ToolRegistryPage';
import FileVaultPage from './components/pages/FileVaultPage';
import NotFoundPage from './components/pages/NotFoundPage';

import { ToolsProvider } from './store/tools';

function App() {
  return (
    <BrowserRouter>
      <ToolsProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/agent-chat" element={<AgentChatPage />} />
            <Route path="/tool-registry" element={<ToolRegistryPage />} />
            <Route path="/file-vault" element={<FileVaultPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppShell>
      </ToolsProvider>
    </BrowserRouter>
  );
}

export default App;
