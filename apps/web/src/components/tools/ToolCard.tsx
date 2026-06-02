import { useState } from 'react';
import type { McpServer, McpTool } from '../../services/mcp-service';

interface ToolCardProps {
  server: McpServer;
  tools: McpTool[];
  onToggleActive: (serverId: string, active: boolean) => Promise<void>;
  onDelete: (serverId: string) => Promise<void>;
  onToggleTool: (toolId: string, enabled: boolean) => Promise<void>;
}

export function ToolCard({
  server,
  tools,
  onToggleActive,
  onDelete,
  onToggleTool,
}: ToolCardProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showTools, setShowTools] = useState(false);

  const handleActiveToggle = async () => {
    setIsToggling(true);
    try {
      await onToggleActive(server.server_id, !server.is_active);
    } catch (err) {
      console.error(err);
    } finally {
      setIsToggling(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to remove the MCP server "${server.name}"?`)) {
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(server.server_id);
    } catch (err) {
      console.error(err);
      setIsDeleting(false);
    }
  };

  // Determine status color dot
  const getStatusColor = () => {
    if (server.status === 'active') return 'var(--color-success)';
    if (server.status === 'error') return 'var(--color-error)';
    return 'var(--color-secondary)';
  };

  return (
    <div
      data-testid={`server-card-${server.server_id}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--color-surface-subtle)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-lg)',
        gap: 'var(--space-md)',
        transition: 'all 0.2s ease',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        position: 'relative',
        opacity: isDeleting ? 0.5 : 1,
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-ui)', color: 'var(--color-primary)', fontWeight: 600 }}>
            {server.name}
          </h3>
          <span
            style={{
              display: 'inline-block',
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-secondary)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              marginTop: 'var(--space-xs)',
              border: '1px solid var(--color-border)',
            }}
          >
            {server.category}
          </span>
        </div>

        {/* Server Toggle Button */}
        <button
          onClick={handleActiveToggle}
          disabled={isToggling || isDeleting}
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 500,
            border: '1px solid var(--color-border)',
            backgroundColor: server.is_active ? 'var(--color-surface)' : 'var(--color-primary)',
            color: server.is_active ? 'var(--color-primary)' : 'var(--color-neutral)',
            cursor: isToggling ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          {isToggling ? 'Connecting...' : server.is_active ? 'Disable' : 'Enable'}
        </button>
      </div>

      {/* Connection Info / Code Command */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--color-neutral)',
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: 'var(--color-secondary)',
          wordBreak: 'break-all',
          gap: 'var(--space-xs)',
        }}
      >
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <span style={{ color: 'var(--color-primary)' }}>Transport:</span>
          <span>{server.type}</span>
        </div>
        {server.command && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-primary)' }}>Endpoint/Command:</span>
            <span style={{ whiteSpace: 'pre-wrap', marginTop: '2px' }}>
              {Array.isArray(server.command) ? server.command.join(' ') : server.command}
            </span>
          </div>
        )}
      </div>

      {/* Status Indicators */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: getStatusColor(),
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--color-primary)', textTransform: 'capitalize' }}>
            {server.status}
          </span>
        </div>

        {/* Delete Custom Server Button */}
        {server.name !== 'CalculiX Simulation' && (
          <button
            onClick={handleDelete}
            disabled={isDeleting || isToggling}
            style={{
              color: 'var(--color-error)',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: '2px 6px',
            }}
          >
            Remove
          </button>
        )}
      </div>

      {/* Error block if any */}
      {server.error_message && (
        <div
          style={{
            backgroundColor: 'rgba(248, 113, 113, 0.1)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-md)',
            fontSize: '0.8rem',
            color: 'var(--color-error)',
            wordBreak: 'break-word',
          }}
        >
          <strong>Connection Error:</strong> {server.error_message}
        </div>
      )}

      {/* Discovered Tools Dropdown */}
      {tools.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-md)', marginTop: 'var(--space-xs)' }}>
          <button
            onClick={() => setShowTools(!showTools)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              width: '100%',
              fontSize: '0.9rem',
              color: 'var(--color-secondary)',
              cursor: 'pointer',
              textAlign: 'left',
              fontWeight: 500,
            }}
          >
            <span>Exposed Tools ({tools.length})</span>
            <span>{showTools ? '▲' : '▼'}</span>
          </button>

          {showTools && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', marginTop: 'var(--space-md)' }}>
              {tools.map((tool) => (
                <div
                  key={tool.tool_id}
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-xs)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                      {tool.name}
                    </span>
                    
                    {/* Tool Toggle Checkbox */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--color-secondary)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={tool.is_enabled}
                        onChange={(e) => onToggleTool(tool.tool_id, e.target.checked)}
                        style={{ cursor: 'pointer' }}
                      />
                      {tool.is_enabled ? 'Enabled' : 'Disabled'}
                    </label>
                  </div>
                  {tool.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--color-secondary)', fontStyle: 'italic' }}>
                      {tool.description}
                    </p>
                  )}
                  {tool.input_schema && Object.keys(tool.input_schema).length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-secondary)', marginTop: '4px' }}>
                      <span style={{ fontWeight: 600 }}>Schema keys:</span>{' '}
                      {Object.keys(tool.input_schema.properties || {}).join(', ') || 'none'}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
