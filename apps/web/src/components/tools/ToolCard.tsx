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
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-xl)',
        gap: 'var(--space-md)',
        transition: 'all var(--transition-smooth)',
        boxShadow: 'var(--shadow-md)',
        position: 'relative',
        opacity: isDeleting ? 0.5 : 1,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-secondary)';
        e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-border)';
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-ui)', color: 'var(--color-primary)', fontWeight: 600 }}>
            {server.name}
          </h3>
          <span
            style={{
              display: 'inline-block',
              fontSize: '0.7rem',
              textTransform: 'uppercase',
              backgroundColor: 'var(--color-surface-subtle)',
              color: 'var(--color-secondary)',
              padding: '2px 8px',
              borderRadius: '20px',
              marginTop: 'var(--space-xs)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              fontWeight: 600,
              letterSpacing: '0.5px',
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
            padding: 'var(--space-sm) var(--space-lg)',
            borderRadius: 'var(--radius-lg)',
            fontSize: '0.85rem',
            fontWeight: 600,
            border: server.is_active ? '1px solid var(--color-border)' : 'none',
            backgroundColor: server.is_active ? 'transparent' : 'var(--color-secondary)',
            color: server.is_active ? 'var(--color-primary)' : 'var(--color-surface-subtle)',
            cursor: isToggling ? 'not-allowed' : 'pointer',
            transition: 'all var(--transition-smooth)',
            boxShadow: server.is_active ? 'none' : 'var(--shadow-glow)',
          }}
          onMouseEnter={(e) => {
            if (!server.is_active) {
              e.currentTarget.style.boxShadow = 'var(--shadow-glow-active)';
            } else {
              e.currentTarget.style.borderColor = 'var(--color-secondary)';
              e.currentTarget.style.color = 'var(--color-secondary)';
            }
          }}
          onMouseLeave={(e) => {
            if (!server.is_active) {
              e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
            } else {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.color = 'var(--color-primary)';
            }
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
          backgroundColor: 'var(--color-surface-subtle)',
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: 'rgba(255, 255, 255, 0.7)',
          wordBreak: 'break-all',
          gap: 'var(--space-xs)',
        }}
      >
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <span style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Transport:</span>
          <span style={{ color: 'var(--color-secondary)' }}>{server.type}</span>
        </div>
        {server.command && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Endpoint/Command:</span>
            <span style={{ whiteSpace: 'pre-wrap', marginTop: '2px', color: 'var(--color-secondary)', fontSize: '0.75rem' }}>
              {Array.isArray(server.command) ? server.command.join(' ') : server.command}
            </span>
          </div>
        )}
      </div>

      {/* Status Indicators */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <span
            className={server.status === 'active' ? 'pulse-success-glow' : undefined}
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: getStatusColor(),
              boxShadow: `0 0 8px ${getStatusColor()}`,
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--color-primary)', textTransform: 'capitalize', fontWeight: 500 }}>
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
              border: 'none',
              background: 'none',
              transition: 'color var(--transition-fast)',
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-error)'}
          >
            Remove
          </button>
        )}
      </div>

      {/* Error block if any */}
      {server.error_message && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-lg)',
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
              fontSize: '0.85rem',
              color: 'var(--color-secondary)',
              cursor: 'pointer',
              textAlign: 'left',
              fontWeight: 600,
              border: 'none',
              background: 'none',
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
                    backgroundColor: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--space-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-xs)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                      {tool.name}
                    </span>
                    
                    {/* Tool Toggle Checkbox */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.6)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={tool.is_enabled}
                        onChange={(e) => onToggleTool(tool.tool_id, e.target.checked)}
                        style={{ cursor: 'pointer', accentColor: 'var(--color-secondary)' }}
                      />
                      {tool.is_enabled ? 'Enabled' : 'Disabled'}
                    </label>
                  </div>
                  {tool.description && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-secondary)', fontStyle: 'italic', lineHeight: 1.4 }}>
                      {tool.description}
                    </p>
                  )}
                  {tool.input_schema && Object.keys(tool.input_schema).length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.4)', marginTop: '4px' }}>
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
