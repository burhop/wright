import { useState, useEffect } from 'react';
import { useTools } from '../../store/tools';
import { ToolCard } from '../tools/ToolCard';
import { AddToolModal } from '../tools/AddToolModal';
import useLogger from '../../hooks/useLogger';

export function ToolRegistryPage() {
  const logger = useLogger('ToolRegistryPage');
  const {
    servers,
    tools,
    isLoading,
    error,
    registerCustomServer,
    toggleServerState,
    deleteServerState,
    toggleToolState,
  } = useTools();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    logger.info('Tool Registry Page loaded');
  }, [logger]);

  // Categories present in servers
  const categories = ['all', 'simulation', 'cad', 'analysis', 'utilities'];

  // Filtering servers
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
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-neutral)',
            fontWeight: 600,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
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
          <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 600, color: 'var(--color-secondary)' }}>
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
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.9rem',
                  textTransform: 'capitalize',
                  fontWeight: selectedCategory === cat ? 600 : 400,
                  backgroundColor: selectedCategory === cat ? 'var(--color-surface)' : 'transparent',
                  color: selectedCategory === cat ? 'var(--color-primary)' : 'var(--color-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
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
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-primary)',
                fontSize: '0.95rem',
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
                backgroundColor: 'rgba(248, 113, 113, 0.1)',
                border: '1px solid var(--color-error)',
                borderRadius: 'var(--radius-md)',
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
                      onToggleActive={toggleServerState}
                      onDelete={deleteServerState}
                      onToggleTool={toggleToolState}
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
