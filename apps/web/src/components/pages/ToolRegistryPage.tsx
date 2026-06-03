import { useState, useEffect } from 'react';
import { useTools } from '../../store/tools';
import { useChat } from '../../store/sessions';
import { ToolCard } from '../tools/ToolCard';
import { AddToolModal } from '../tools/AddToolModal';
import useLogger from '../../hooks/useLogger';
import { workspaceService, type WorkspaceInfo } from '../../services/workspace-service';

export function ToolRegistryPage() {
  const logger = useLogger('ToolRegistryPage');
  const { state: chatState } = useChat();
  const activeSessionId = chatState.activeSessionId;

  const {
    servers,
    tools,
    isLoading,
    error,
    registerCustomServer,
    installServerState,
    uninstallServerState,
    deleteServerState,
    toggleToolState,
  } = useTools();

  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const list = await workspaceService.getAllWorkspaces();
        setWorkspaces(list);
      } catch (err) {
        console.error('Failed to load workspaces in ToolRegistryPage', err);
      }
    };
    fetchWorkspaces();
  }, []);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    logger.info('Tool Registry Page loaded');
  }, [logger]);

  const categories = ['all', 'simulation', 'cad', 'analysis', 'utilities'];

  const filteredServers = servers.filter((server) => {
    const matchesSearch = server.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === 'all' || server.category.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  return (
    <div
      data-testid="page-tool-registry"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--color-neutral)',
        color: 'var(--color-primary)',
        overflow: 'hidden',
      }}
      className="animate-fade-in-up"
    >
      {/* Top Title Section */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: 'var(--space-xl)',
          borderBottom: '1px solid var(--color-border)',
          backgroundColor: 'var(--color-surface-subtle)',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.8rem', fontFamily: 'var(--font-ui)', fontWeight: 700, color: 'var(--color-primary)' }}>
            Engineering Tool Registry
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-secondary)', marginTop: 'var(--space-xs)' }}>
            Configure solver subprocesses, monitor custom schema configurations, and toggle agent-exposed capabilities.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          style={{
            padding: 'var(--space-md) var(--space-lg)',
            backgroundColor: 'var(--color-secondary)',
            color: 'var(--color-surface-subtle)',
            fontWeight: 600,
            borderRadius: 'var(--radius-lg)',
            border: 'none',
            cursor: 'pointer',
            transition: 'all var(--transition-smooth)',
            boxShadow: 'var(--shadow-glow)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = 'var(--shadow-glow-active)';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          + Register Custom Tool
        </button>
      </div>

      {/* Main Page Layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar Categories */}
        <div
          style={{
            width: '240px',
            borderRight: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface-subtle)',
            padding: 'var(--space-xl) var(--space-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
          }}
        >
          <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 600, color: 'var(--color-secondary)', letterSpacing: '1px', paddingLeft: 'var(--space-md)' }}>
            Categories
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  textAlign: 'left',
                  padding: 'var(--space-md)',
                  borderRadius: 'var(--radius-lg)',
                  fontSize: '0.9rem',
                  textTransform: 'capitalize',
                  fontWeight: selectedCategory === cat ? 600 : 500,
                  backgroundColor: selectedCategory === cat ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
                  color: selectedCategory === cat ? 'var(--color-secondary)' : 'rgba(255, 255, 255, 0.6)',
                  cursor: 'pointer',
                  borderLeft: selectedCategory === cat ? '3px solid var(--color-secondary)' : '3px solid transparent',
                  transition: 'all var(--transition-smooth)',
                }}
                onMouseEnter={(e) => {
                  if (selectedCategory !== cat) {
                    e.currentTarget.style.color = 'var(--color-primary)';
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedCategory !== cat) {
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.6)';
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Directory Grid */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 'var(--space-xl)' }}>
          {/* Search bar */}
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <input
              type="text"
              placeholder="Search MCP servers by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-md) var(--space-lg)',
                backgroundColor: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--color-primary)',
                fontSize: '0.95rem',
                outline: 'none',
                transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-secondary)';
                e.currentTarget.style.boxShadow = '0 0 10px rgba(56, 189, 248, 0.15)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Loading or Error states */}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
              <div className="thinking-dot" />
              <div className="thinking-dot" />
              <div className="thinking-dot" />
            </div>
          )}

          {!isLoading && error && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--color-error)',
                borderRadius: 'var(--radius-lg)',
                padding: 'var(--space-lg)',
                color: 'var(--color-error)',
                marginBottom: 'var(--space-xl)',
              }}
            >
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Grid Render */}
          {!isLoading && (
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
              {filteredServers.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-secondary)' }}>
                  No MCP servers found matching the selected query or filters.
                </div>
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                    gap: 'var(--space-xl)',
                  }}
                >
                  {filteredServers.map((server) => (
                    <ToolCard
                      key={server.server_id}
                      server={server}
                      tools={tools.filter((t) => t.server_id === server.server_id)}
                      onInstall={installServerState}
                      onUninstall={uninstallServerState}
                      onDelete={deleteServerState}
                      onToggleTool={toggleToolState}
                      workspaces={workspaces}
                      activeSessionId={activeSessionId}
                      onRefreshWorkspaces={async () => {
                        try {
                          const list = await workspaceService.getAllWorkspaces();
                          setWorkspaces(list);
                        } catch (err) {
                          console.error(err);
                        }
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal Dialog Form */}
      <AddToolModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={registerCustomServer}
      />
    </div>
  );
}

export default ToolRegistryPage;
